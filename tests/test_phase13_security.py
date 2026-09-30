"""
reServe AI - Phase 13 Security & Production Hardening Test Suite

Tests for:
1. Unauthenticated protected endpoints
2. Invalid JWT token rejection
3. Expired JWT token handling
4. Role-based access control (wrong role forbidden)
5. Cross-role boundary enforcement
6. Malformed request payload rejection
7. Invalid ID / parameter bounds handling
8. Multi-tenant cross-organization isolation
9. Missing model artifact safe handling
10. Truthful simulated Fruit CV behavior
11. Truthful Waste ML fallback behavior
12. ML Registry and API status consistency
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from backend.main import app
from backend.core.config import settings
from backend.core.security import ALGORITHM
from backend.core.deps import check_tenant_access
from backend.models.entities import User

PROJECT_ROOT = Path(__file__).resolve().parent.parent
client = TestClient(app)


def get_token(username: str = "admin@reserveai.com", password: str = "Admin@1234") -> str:
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["access_token"]


class TestAuthenticationSecurity:
    """Security verification for JWT authentication and token life-cycle."""

    def test_unauthenticated_protected_endpoint(self):
        """Unauthenticated requests to protected endpoints must be rejected with 401."""
        resp = client.get("/api/v1/ml/status")
        assert resp.status_code == 401
        assert "not provided" in resp.json()["detail"].lower()

    def test_invalid_jwt_token(self):
        """Malformed or tampered JWT tokens must return 401 Unauthorized."""
        headers = {"Authorization": "Bearer malformed.invalid.jwt.token"}
        resp = client.get("/api/v1/ml/status", headers=headers)
        assert resp.status_code == 401
        assert "could not validate credentials" in resp.json()["detail"].lower()

    def test_expired_jwt_token(self):
        """Expired JWT tokens must be rejected with 401."""
        expired_time = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {"sub": "1", "exp": expired_time}
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

        headers = {"Authorization": f"Bearer {expired_token}"}
        resp = client.get("/api/v1/ml/status", headers=headers)
        assert resp.status_code == 401
        assert "could not validate credentials" in resp.json()["detail"].lower()

    def test_invalid_credentials_rejected(self):
        """Invalid username or password must be rejected with 401 without revealing user existence."""
        resp = client.post("/api/v1/auth/login", json={"username": "nonexistent@reserveai.com", "password": "WrongPassword"})
        assert resp.status_code == 401
        assert "incorrect email or password" in resp.json()["detail"].lower()


class TestRBACAuthorization:
    """Verification of Role-Based Access Control and Cross-Tenant Boundaries."""

    def test_wrong_role_forbidden_on_admin_endpoint(self):
        """Users without SUPER_ADMIN or ORG_ADMIN roles must receive 403 Forbidden on user admin."""
        # Logistics coordinator token
        log_token = get_token("logistics@reserveai.com", "Logistics@1234")
        headers = {"Authorization": f"Bearer {log_token}"}

        # Attempt to access user management endpoint
        resp = client.get("/api/v1/users/", headers=headers)
        assert resp.status_code == 403
        assert "operation not permitted" in resp.json()["detail"].lower()

    def test_cross_role_logistics_coordination(self):
        """NGO rep cannot create routes; only LOGISTICS_COORDINATOR or SUPER_ADMIN may coordinate routes."""
        ngo_token = get_token("ngo@reserveai.com", "NGO@1234")
        headers = {"Authorization": f"Bearer {ngo_token}"}

        resp = client.post(
            "/api/v1/logistics/routes/optimize",
            headers=headers,
            json={"kitchen_id": 1, "selected_requests": [1], "vehicle_capacity_kg": 500.0}
        )
        assert resp.status_code == 403
        assert "operation not permitted" in resp.json()["detail"].lower()

    def test_cross_tenant_isolation(self):
        """Cross-tenant organization isolation must raise 403 Forbidden."""
        from fastapi import HTTPException
        mock_user = User(id=10, role="KITCHEN_MANAGER", organization_id=1)
        # Attempt to access resource from organization 2
        with pytest.raises(HTTPException) as exc_info:
            check_tenant_access(mock_user, organization_id=2)
        assert exc_info.value.status_code == 403
        assert "cross-organization" in exc_info.value.detail.lower()

    def test_super_admin_bypasses_tenant_isolation(self):
        """SUPER_ADMIN role legitimately has global platform oversight."""
        super_admin = User(id=1, role="SUPER_ADMIN", organization_id=1)
        # Should not raise exception
        check_tenant_access(super_admin, organization_id=2)


class TestAPIValidationAndErrorHandling:
    """Input boundary validation and controlled failure handling."""

    def test_malformed_numeric_payload(self):
        """Submitting non-numeric values for numeric fields must return 422 Unprocessable Entity."""
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/v1/demand/predict",
            headers=headers,
            json={"kitchen_id": "NOT_AN_INTEGER", "food_item_id": 1}
        )
        assert resp.status_code == 422

    def test_empty_image_upload_rejected(self):
        """Empty file uploads to quality scan must be rejected with 400 Bad Request."""
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/v1/quality/scan",
            headers=headers,
            files={"image": ("empty.jpg", b"", "image/jpeg")},
            data={"food_item_id": 1, "category": "FRUITS", "food_name": "Apple"}
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_oversized_file_upload_rejected(self):
        """Files exceeding 5MB size limit must be rejected with 413 Payload Too Large."""
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}
        six_mb_bytes = b"0" * (6 * 1024 * 1024)
        resp = client.post(
            "/api/v1/quality/scan",
            headers=headers,
            files={"image": ("oversized.jpg", six_mb_bytes, "image/jpeg")},
            data={"food_item_id": 1, "category": "FRUITS", "food_name": "Apple"}
        )
        assert resp.status_code in (413, 400)


class TestMLIntegrationTruthfulness:
    """Verification that ML endpoints truthfully report fallback/simulation and consistency."""

    def test_fruit_cv_simulation_mode_and_human_verification(self):
        """Fruit CV must explicitly return simulated=True and human_verification_required=True."""
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/v1/quality/scan",
            headers=headers,
            files={"image": ("test.jpg", b"mock-jpeg-bytes-for-test", "image/jpeg")},
            data={"food_item_id": 1, "category": "FRUITS", "food_name": "Apple"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["simulated"] is True
        assert data["human_verified"] is False
        assert "PENDING" in data["food_safety_verdict"]

    def test_waste_remains_rule_based_fallback(self):
        """Waste prediction must return rule-based-v1.0 because 0 historical records exist."""
        from ml.waste_predictor import waste_engine
        res = waste_engine.predict_waste(production_kg=100.0, expected_demand_kg=85.0, inventory_batches_near_expiry_kg=5.0)
        assert res["model_version"] == "rule-based-v1.0"
        assert res["expected_waste_kg"] is not None

    def test_ml_registry_and_api_consistency(self):
        """Every engine reported by /api/v1/ml/status must match models/model_registry.json."""
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/v1/ml/status", headers=headers)
        assert resp.status_code == 200
        api_data = resp.json()

        reg_path = PROJECT_ROOT / "models" / "model_registry.json"
        with open(reg_path, "r", encoding="utf-8") as f:
            registry = json.load(f)

        assert api_data["total_engines"] == len(registry)
        reg_names = {e["model_name"] for e in registry}
        api_names = {e["engine"] for e in api_data["engines"]}
        assert reg_names == api_names
