import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.core.database import SessionLocal
from backend.models.entities import Inventory, InventoryBatch, FoodItem, QualityResult

client = TestClient(app)

def get_auth_token(email: str = "quality@reserveai.com", password: str = "Quality@1234") -> str:
    response = client.post("/api/v1/auth/login", json={
        "username": email,
        "password": password
    })
    assert response.status_code == 200, f"Login failed for {email}: {response.text}"
    return response.json()["access_token"]

# Synthetic minimal valid JPEG bytes (JFIF header, >= 32 bytes)
VALID_JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00" + (b"\x01" * 64) + b"\xff\xd9"
)

# Synthetic minimal valid PNG header (8-byte signature + 13-byte IHDR + dimension bytes 100x100)
VALID_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    + (100).to_bytes(4, "big")
    + (100).to_bytes(4, "big")
    + b"\x08\x02\x00\x00\x00"
    + b"\x00" * 32
)

# 1. Valid supported image is accepted (JPEG and PNG)
def test_valid_supported_jpeg_accepted():
    token = get_auth_token()
    file_payload = ("fresh_produce.jpg", VALID_JPEG_BYTES, "image/jpeg")
    response = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1, "category": "VEGETABLES", "food_name": "Fresh Spinach"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "freshness_score" in data
    assert "freshness_level" in data
    assert data["human_verified"] is False
    assert "/uploads/scans/" in data["image_url"]

def test_valid_supported_png_accepted():
    token = get_auth_token()
    file_payload = ("sample_item.png", VALID_PNG_BYTES, "image/png")
    response = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1, "category": "FRUITS", "food_name": "Organic Apples"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["food_name"] == "Organic Apples"
    assert "freshness_level" in data

# 2. Oversized image is rejected with HTTP 413
def test_oversized_image_rejected_with_413():
    token = get_auth_token()
    # 5 MB + 1024 bytes
    oversized_bytes = b"\xff\xd8\xff" + (b"\x00" * (5 * 1024 * 1024 + 1024))
    file_payload = ("oversized.jpg", oversized_bytes, "image/jpeg")
    response = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1}
    )
    assert response.status_code == 413
    assert "exceeds maximum allowable size" in response.json()["detail"]

# 3. Invalid image bytes are rejected with controlled HTTP 400
def test_invalid_image_bytes_rejected():
    token = get_auth_token()
    garbage_bytes = b"Hello, this is just plain text content, not an image format!"
    file_payload = ("test.jpg", garbage_bytes, "image/jpeg")
    response = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1}
    )
    assert response.status_code == 400
    assert "Unsupported or invalid image content" in response.json()["detail"]

# 4. Misleading MIME type is rejected when content is invalid
def test_misleading_mime_type_rejected():
    token = get_auth_token()
    # Claims to be image/jpeg, but is actually an HTML snippet
    html_bytes = b"<!DOCTYPE html><html><body>Fake JPEG</body></html>"
    file_payload = ("fake_photo.jpg", html_bytes, "image/jpeg")
    response = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1}
    )
    assert response.status_code == 400
    assert "Unsupported or invalid image content" in response.json()["detail"]

# 5. Unsupported file formats are rejected
def test_unsupported_file_formats_rejected():
    token = get_auth_token()
    # PDF document
    pdf_bytes = b"%PDF-1.4\n%Fake PDF content for test"
    file_payload = ("document.pdf", pdf_bytes, "application/pdf")
    res_pdf = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1}
    )
    assert res_pdf.status_code == 400

    # Windows PE executable
    exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00Fake executable content"
    file_payload_exe = ("script.exe", exe_bytes, "application/octet-stream")
    res_exe = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload_exe},
        data={"food_item_id": 1}
    )
    assert res_exe.status_code == 400

# 6. Filename keywords cannot force a freshness or spoilage classification
def test_filename_keywords_cannot_override_classification():
    token = get_auth_token()
    # Valid JPEG image, but filename contains hostile/spoofed keywords
    file_payload = ("decay_rotten_bad_spoiled.jpg", VALID_JPEG_BYTES, "image/jpeg")
    response = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1, "food_name": "Crisp Celery"}
    )
    assert response.status_code == 200
    data = response.json()
    # Previously, "decay" or "rotten" in filename hardcoded freshness_score = 32.0 and level = ROTTEN
    assert data["freshness_score"] != 32.0, "Filename keyword must not force hardcoded freshness score 32.0"
    assert data["freshness_level"] != "ROTTEN", "Filename keyword must not force ROTTEN classification"
    assert data["redistribution_status"] != "HAZARD_DISCARD"

# 7. Excessive / decompression-bomb image dimensions rejected
def test_excessive_dimensions_rejected():
    token = get_auth_token()
    # PNG with width 10,000 and height 10,000 (> 8192 safety bound)
    bomb_png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        + (10000).to_bytes(4, "big")
        + (10000).to_bytes(4, "big")
        + b"\x08\x02\x00\x00\x00"
        + b"\x00" * 32
    )
    file_payload = ("bomb.png", bomb_png, "image/png")
    response = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1}
    )
    assert response.status_code == 400
    assert "exceed maximum allowed safety bounds" in response.json()["detail"]

# 8. Truncated or corrupted image headers rejected cleanly
def test_truncated_image_rejected():
    token = get_auth_token()
    # Starts with JPEG marker but only 10 bytes long (< 32 required for JPEG integrity)
    truncated_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 6
    file_payload = ("truncated.jpg", truncated_jpeg, "image/jpeg")
    response = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1}
    )
    assert response.status_code == 400
    assert "Corrupted or truncated JPEG" in response.json()["detail"]

def test_corrupted_png_missing_ihdr_rejected():
    token = get_auth_token()
    # PNG signature present, but missing IHDR chunk
    corrupted_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    file_payload = ("corrupt.png", corrupted_png, "image/png")
    response = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1}
    )
    assert response.status_code == 400
    assert "missing IHDR" in response.json()["detail"]

# 9. Existing expiry safety gate remains effective
def test_expired_batch_triggers_hazard_discard():
    token = get_auth_token()
    db: Session = SessionLocal()
    try:
        # Create an expired batch
        now_utc = datetime.now(timezone.utc)
        test_batch = InventoryBatch(
            inventory_id=1,
            batch_number=f"EXP-TEST-{int(now_utc.timestamp())}",
            initial_quantity_kg=25.0,
            remaining_quantity_kg=25.0,
            procured_at=now_utc - timedelta(days=10),
            expiry_date=now_utc - timedelta(days=2),
            status="EXPIRED"
        )
        db.add(test_batch)
        db.commit()
        db.refresh(test_batch)
        batch_id = test_batch.id
    finally:
        db.close()

    file_payload = ("fresh_looking.jpg", VALID_JPEG_BYTES, "image/jpeg")
    response = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1, "batch_id": batch_id, "food_name": "Perishable Batch Item"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["redistribution_status"] == "HAZARD_DISCARD"
    assert data["freshness_level"] == "ROTTEN"
    assert data["food_safety_verdict"] == "REJECTED_EXPIRED_BATCH"
    assert any("Batch Expiration Passed" in d for d in data["defects_detected"])

# 10. Human verification remains functional
def test_human_verification_workflow_functional():
    token = get_auth_token("quality@reserveai.com", "Quality@1234")
    file_payload = ("verify_test.jpg", VALID_JPEG_BYTES, "image/jpeg")
    scan_res = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1, "food_name": "Tomatoes for Sign-off"}
    )
    assert scan_res.status_code == 200
    scan_id = scan_res.json()["id"]

    # Sign off with QUALITY_INSPECTOR role
    verify_res = client.post(
        f"/api/v1/quality/scans/{scan_id}/verify",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "verdict": "APPROVED_FOR_REDISTRIBUTION",
            "inspector_notes": "Visually certified clean and safe by certified officer."
        }
    )
    assert verify_res.status_code == 200
    vdata = verify_res.json()
    assert vdata["human_verified"] is True
    assert vdata["food_safety_verdict"] == "APPROVED_FOR_REDISTRIBUTION"
    assert vdata["status"] == "SAFE_FOR_REDISTRIBUTION"
    assert vdata["inspector_name"] is not None

# 11. Empty upload rejected with HTTP 400
def test_empty_upload_rejected():
    token = get_auth_token()
    file_payload = ("empty.jpg", b"", "image/jpeg")
    response = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
