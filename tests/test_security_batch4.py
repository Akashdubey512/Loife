import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from backend.main import app
from backend.core.config import Settings
from backend.core.database import SessionLocal
from backend.core.security import hash_password
from backend.models.entities import Organization, User, Kitchen, RedistributionRequest, NGOPartner

client = TestClient(app)

def get_auth_token(email: str = "kitchen@reserveai.com", password: str = "Kitchen@1234") -> str:
    response = client.post("/api/v1/auth/login", json={
        "username": email,
        "password": password
    })
    assert response.status_code == 200, f"Login failed for {email}: {response.text}"
    return response.json()["access_token"]


# =====================================================================
# SEC-MED-01: CORS Configuration Tests
# =====================================================================

def test_cors_trusted_origin_granted_access():
    response = client.options(
        "/api/v1/redistribution/surplus",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"

def test_cors_untrusted_origin_denied():
    response = client.options(
        "/api/v1/redistribution/surplus",
        headers={
            "Origin": "http://malicious-site.attacker.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    # Untrusted origin must NOT receive an Access-Control-Allow-Origin matching its origin
    allowed_origin = response.headers.get("access-control-allow-origin")
    assert allowed_origin != "http://malicious-site.attacker.com"
    assert allowed_origin != "*"

def test_cors_production_rejects_wildcard():
    # Production with wildcard CORS must raise ValueError
    with pytest.raises(ValueError, match="Wildcard CORS origin.*strictly prohibited"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 32,
            BACKEND_CORS_ORIGINS=["*"]
        )

def test_cors_production_rejects_empty_origins():
    # Production with empty CORS origins must raise ValueError
    with pytest.raises(ValueError, match="BACKEND_CORS_ORIGINS must be configured"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 32,
            BACKEND_CORS_ORIGINS=[]
        )

def test_cors_comma_separated_env_parsing():
    s = Settings(
        ENVIRONMENT="development",
        SECRET_KEY="a" * 32,
        BACKEND_CORS_ORIGINS="https://app.reserveai.com, https://admin.reserveai.com"
    )
    assert s.BACKEND_CORS_ORIGINS == ["https://app.reserveai.com", "https://admin.reserveai.com"]

def test_cors_wildcard_stripped_in_development():
    # If wildcard is supplied alongside credentials, it is stripped
    s = Settings(
        ENVIRONMENT="development",
        SECRET_KEY="a" * 32,
        BACKEND_CORS_ORIGINS=["http://localhost:3000", "*"]
    )
    assert "*" not in s.BACKEND_CORS_ORIGINS
    assert "http://localhost:3000" in s.BACKEND_CORS_ORIGINS


# =====================================================================
# SEC-MED-02: Surplus Claim Authorization & Tenant Isolation Tests
# =====================================================================

def test_unauthenticated_surplus_claim_rejected():
    response = client.post("/api/v1/redistribution/requests/1/claim?ngo_id=1")
    assert response.status_code == 401
    assert "detail" in response.json()

def test_unauthorized_role_cannot_claim_surplus():
    # Quality inspector attempting to claim surplus must receive 403 Forbidden
    inspector_token = get_auth_token("quality@reserveai.com", "Quality@1234")
    response = client.post(
        "/api/v1/redistribution/requests/1/claim?ngo_id=1",
        headers={"Authorization": f"Bearer {inspector_token}"}
    )
    assert response.status_code == 403
    assert "Operation not permitted" in response.json()["detail"]

def test_authorized_ngo_rep_can_claim_eligible_surplus():
    # Create fresh surplus item in organization 1
    db: Session = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        surplus = RedistributionRequest(
            kitchen_id=1,
            food_item_id=1,
            quantity_kg=30.0,
            estimated_meals=60,
            available_from=now_utc,
            expires_at=now_utc + timedelta(hours=8),
            status="POSTED"
        )
        db.add(surplus)
        db.commit()
        db.refresh(surplus)
        req_id = surplus.id
    finally:
        db.close()

    ngo_token = get_auth_token("ngo@reserveai.com", "NGO@1234")
    response = client.post(
        f"/api/v1/redistribution/requests/{req_id}/claim?ngo_id=1",
        headers={"Authorization": f"Bearer {ngo_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "MATCHED"
    assert data["ngo_id"] == 1

def test_cross_organization_claim_rejected():
    db: Session = SessionLocal()
    try:
        # Ensure Organization 2 and User in Org 2 exist
        org2 = db.query(Organization).filter(Organization.id == 2).first()
        if not org2:
            org2 = Organization(name="Org 2 Humanitarian Hub", org_type="NGO", contact_email="hub@org2.org")
            db.add(org2)
            db.commit()
            db.refresh(org2)

        user_org2 = db.query(User).filter(User.email == "ngo_org2@example.com").first()
        if not user_org2:
            user_org2 = User(
                email="ngo_org2@example.com",
                hashed_password=hash_password("Pass@1234"),
                full_name="External NGO Operator",
                role="NGO_REP",
                organization_id=org2.id
            )
            db.add(user_org2)
            db.commit()

        # Create surplus item in Organization 1's kitchen
        now_utc = datetime.now(timezone.utc)
        surplus_org1 = RedistributionRequest(
            kitchen_id=1,
            food_item_id=1,
            quantity_kg=20.0,
            estimated_meals=40,
            available_from=now_utc,
            expires_at=now_utc + timedelta(hours=6),
            status="POSTED"
        )
        db.add(surplus_org1)
        db.commit()
        db.refresh(surplus_org1)
        req_id = surplus_org1.id
    finally:
        db.close()

    org2_token = get_auth_token("ngo_org2@example.com", "Pass@1234")

    # Attempt cross-organization claim: Org 2 claimant on Org 1 surplus
    response = client.post(
        f"/api/v1/redistribution/requests/{req_id}/claim?ngo_id=1",
        headers={"Authorization": f"Bearer {org2_token}"}
    )
    assert response.status_code == 403
    assert "Cross-organization surplus claim is forbidden" in response.json()["detail"]

def test_client_supplied_org_id_cannot_bypass_tenant_check():
    # Attempt to spoof tenant by injecting organization_id parameter into query
    org2_token = get_auth_token("ngo_org2@example.com", "Pass@1234")

    db: Session = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        surplus = RedistributionRequest(
            kitchen_id=1,
            food_item_id=1,
            quantity_kg=15.0,
            estimated_meals=30,
            available_from=now_utc,
            expires_at=now_utc + timedelta(hours=6),
            status="POSTED"
        )
        db.add(surplus)
        db.commit()
        db.refresh(surplus)
        req_id = surplus.id
    finally:
        db.close()

    # Pass spoofed organization_id=1 in query string
    response = client.post(
        f"/api/v1/redistribution/requests/{req_id}/claim?ngo_id=1&organization_id=1",
        headers={"Authorization": f"Bearer {org2_token}"}
    )
    assert response.status_code == 403

def test_duplicate_claim_prevention_remains_intact():
    db: Session = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        surplus = RedistributionRequest(
            kitchen_id=1,
            food_item_id=1,
            quantity_kg=18.0,
            estimated_meals=36,
            available_from=now_utc,
            expires_at=now_utc + timedelta(hours=6),
            status="POSTED"
        )
        db.add(surplus)
        db.commit()
        db.refresh(surplus)
        req_id = surplus.id
    finally:
        db.close()

    token = get_auth_token("kitchen@reserveai.com", "Kitchen@1234")

    # 1. First claim succeeds
    first = client.post(
        f"/api/v1/redistribution/requests/{req_id}/claim?ngo_id=1",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert first.status_code == 200

    # 2. Duplicate claim fails with 409 Conflict
    second = client.post(
        f"/api/v1/redistribution/requests/{req_id}/claim?ngo_id=2",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert second.status_code == 409
    assert "already in" in second.json()["detail"].lower()


# =====================================================================
# SEC-MED-05: Health Check Endpoint Tests
# =====================================================================

def test_health_check_returns_success_without_auth():
    # Must be unauthenticated and return 200
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["database"] == "connected"
    assert "environment" in data

def test_health_check_does_not_expose_secrets():
    response = client.get("/health")
    assert response.status_code == 200
    raw_text = response.text.lower()
    # Confirm no credentials or internal config leaked
    assert "secret" not in raw_text
    assert "password" not in raw_text
    assert "database_url" not in raw_text
    assert "postgres" not in raw_text
    assert "sqlite" not in raw_text

def test_health_check_database_failure_returns_503():
    # Simulate DB execution failure
    with patch("sqlalchemy.orm.Session.execute", side_effect=OperationalError("connection refused", {}, None)):
        response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "UNHEALTHY"
        assert data["detail"]["database"] == "unavailable"

def test_docker_compose_healthcheck_target_exists():
    # Read docker-compose.yml and verify healthcheck command targets /health
    with open("deployment/docker-compose.yml", "r", encoding="utf-8") as f:
        compose_text = f.read()
    assert "http://localhost:8000/health" in compose_text
