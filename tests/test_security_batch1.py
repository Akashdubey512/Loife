import pytest
import uuid
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.config import Settings

client = TestClient(app)

def get_auth_token(email: str = "admin@reserveai.com", password: str = "Admin@1234") -> str:
    response = client.post("/api/v1/auth/login", json={
        "username": email,
        "password": password
    })
    assert response.status_code == 200
    return response.json()["access_token"]

# 1. Protected endpoint without token returns 401
def test_protected_endpoint_without_token():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Bearer"

# 2. Protected endpoint with invalid token returns 401
def test_protected_endpoint_with_invalid_token():
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.malformed.token"}
    )
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"

# 3. Protected endpoint with valid token works
def test_protected_endpoint_with_valid_token():
    token = get_auth_token("kitchen@reserveai.com", "Kitchen@1234")
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "kitchen@reserveai.com"
    assert user_data["role"] == "KITCHEN_MANAGER"

# 4. Public registration cannot assign privileged roles
def test_public_registration_cannot_assign_privileged_roles():
    response = client.post("/api/v1/auth/register", json={
        "email": f"attacker_{uuid.uuid4().hex[:6]}@example.com",
        "password": "Attacker@1234",
        "full_name": "Privilege Escalation Attempt",
        "role": "SUPER_ADMIN"
    })
    assert response.status_code == 403
    assert "privileged roles" in response.json()["detail"].lower()

# 5. Public registration cannot assign arbitrary organizations
def test_public_registration_cannot_assign_arbitrary_organizations():
    response = client.post("/api/v1/auth/register", json={
        "email": f"attacker_org_{uuid.uuid4().hex[:6]}@example.com",
        "password": "Attacker@1234",
        "full_name": "Org Hijack Attempt",
        "organization_id": 1
    })
    assert response.status_code == 403
    assert "organization membership" in response.json()["detail"].lower()

# 6. Legitimate registration remains functional
def test_legitimate_registration_remains_functional():
    test_email = f"community_{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/api/v1/auth/register", json={
        "email": test_email,
        "password": "SecurePassword@1234",
        "full_name": "Community Member"
    })
    assert response.status_code == 200
    created = response.json()
    assert created["email"] == test_email
    assert created["role"] == "PUBLIC_USER"
    assert created["organization_id"] is None

# 7. Production configuration rejects missing or insecure JWT secrets
def test_production_configuration_rejects_missing_or_insecure_jwt_secrets():
    # Missing / empty
    with pytest.raises(ValueError, match="Production configuration error"):
        Settings(ENVIRONMENT="production", SECRET_KEY="")

    # Known insecure default secret
    with pytest.raises(ValueError, match="Production configuration error"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="reserve-ai-super-secure-production-ready-jwt-secret-key-2026"
        )

    # Too short (< 32 chars)
    with pytest.raises(ValueError, match="Production configuration error"):
        Settings(ENVIRONMENT="production", SECRET_KEY="short-secret-key")

# 8. Valid configured secrets are accepted
def test_valid_configured_secrets_are_accepted():
    strong_key = "a-secure-production-key-with-over-32-characters-1234567890"
    cfg = Settings(ENVIRONMENT="production", SECRET_KEY=strong_key)
    assert cfg.SECRET_KEY == strong_key

# 9. Administrative user creation remains functional for privileged staff
def test_administrative_user_creation_with_role():
    admin_token = get_auth_token("admin@reserveai.com", "Admin@1234")
    new_staff_email = f"staff_{uuid.uuid4().hex[:8]}@reserveai.com"
    response = client.post(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": new_staff_email,
            "password": "StaffPassword@1234",
            "full_name": "Authorized Staff Member",
            "role": "KITCHEN_MANAGER",
            "organization_id": 1
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_staff_email
    assert data["role"] == "KITCHEN_MANAGER"
    assert data["organization_id"] == 1
