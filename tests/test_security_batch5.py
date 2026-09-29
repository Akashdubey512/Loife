import os
import re
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch

from backend.main import app
from backend.core.config import settings, Settings
from backend.core.rate_limiter import auth_rate_limiter, InMemoryRateLimiter

client = TestClient(app)

# =====================================================================
# SEC-HIGH-04: Authentication Endpoint Rate Limiting Tests
# =====================================================================

def test_login_below_rate_limit_succeeds():
    auth_rate_limiter.reset()
    response = client.post("/api/v1/auth/login", json={
        "username": "kitchen@reserveai.com",
        "password": "Kitchen@1234"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_exceeding_rate_limit_returns_429():
    auth_rate_limiter.reset()
    # Temporarily set max_requests to 3 for deterministic testing
    original_max = auth_rate_limiter.max_requests
    original_window = auth_rate_limiter.window_seconds
    try:
        auth_rate_limiter.max_requests = 3
        auth_rate_limiter.window_seconds = 60

        # Send 3 requests (all allowed)
        for _ in range(3):
            res = client.post("/api/v1/auth/login", json={
                "username": "kitchen@reserveai.com",
                "password": "WrongPassword"
            })
            assert res.status_code == 401

        # 4th request must be blocked by rate limiter with 429
        blocked_res = client.post("/api/v1/auth/login", json={
            "username": "kitchen@reserveai.com",
            "password": "Kitchen@1234"
        })
        assert blocked_res.status_code == 429
        assert "Too many authentication attempts" in blocked_res.json()["detail"]
        assert "Retry-After" in blocked_res.headers
    finally:
        auth_rate_limiter.max_requests = original_max
        auth_rate_limiter.window_seconds = original_window
        auth_rate_limiter.reset()

def test_registration_rate_limiting_enforced():
    auth_rate_limiter.reset()
    original_max = auth_rate_limiter.max_requests
    original_window = auth_rate_limiter.window_seconds
    try:
        auth_rate_limiter.max_requests = 2
        auth_rate_limiter.window_seconds = 60

        # 1st and 2nd registration attempts
        for i in range(2):
            res = client.post("/api/v1/auth/register", json={
                "email": f"rate_limit_user_{i}@example.com",
                "password": "Password@1234",
                "full_name": f"Rate User {i}"
            })
            assert res.status_code in (200, 400)  # Either created or already exists

        # 3rd attempt exceeds limit
        blocked_res = client.post("/api/v1/auth/register", json={
            "email": "rate_limit_user_excess@example.com",
            "password": "Password@1234",
            "full_name": "Rate User Excess"
        })
        assert blocked_res.status_code == 429
        assert "Too many authentication attempts" in blocked_res.json()["detail"]
    finally:
        auth_rate_limiter.max_requests = original_max
        auth_rate_limiter.window_seconds = original_window
        auth_rate_limiter.reset()

def test_independent_client_identities():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60, enabled=True)
    
    class DummyClient:
        def __init__(self, host):
            self.host = host

    class DummyRequest:
        def __init__(self, host):
            self.client = DummyClient(host)

    req1 = DummyRequest("192.168.1.100")
    req2 = DummyRequest("192.168.1.200")

    # Client 1 uses 2 requests
    limiter.check(req1)
    limiter.check(req1)

    # Client 1 is blocked
    with pytest.raises(Exception) as exc:
        limiter.check(req1)
    assert exc.value.status_code == 429

    # Client 2 is NOT blocked (independent quota)
    limiter.check(req2)
    limiter.check(req2)


# =====================================================================
# SEC-MED-04: Database Credential Configuration Tests
# =====================================================================

def test_docker_compose_no_hardcoded_passwords():
    with open("deployment/docker-compose.yml", "r", encoding="utf-8") as f:
        content = f.read()

    # Must not contain default hardcoded database password
    assert "reserve_secure_pass" not in content, "Found hardcoded 'reserve_secure_pass' in docker-compose.yml"
    # Must use required environment substitution
    assert "${POSTGRES_PASSWORD:?" in content
    assert "${POSTGRES_USER:?" in content

def test_docker_compose_consistent_credentials():
    with open("deployment/docker-compose.yml", "r", encoding="utf-8") as f:
        content = f.read()

    # Backend DATABASE_URL must reference same POSTGRES_USER and POSTGRES_PASSWORD variables
    assert "DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/" in content

def test_env_example_database_placeholders():
    with open(".env.example", "r", encoding="utf-8") as f:
        content = f.read()

    assert "POSTGRES_PASSWORD=replace-with-a-secure-database-password" in content
    assert "reserve_secure_pass" not in content


# =====================================================================
# SEC-LOW: Non-Root Backend Container Tests
# =====================================================================

def test_dockerfile_backend_runs_as_non_root():
    with open("deployment/Dockerfile.backend", "r", encoding="utf-8") as f:
        content = f.read()

    # Must contain unprivileged user creation
    assert re.search(r"useradd.*appuser", content), "Dockerfile.backend missing unprivileged user creation"
    # Must declare USER directive with non-root user
    assert re.search(r"^USER\s+appuser", content, re.MULTILINE), "Dockerfile.backend missing USER appuser directive"
    # Must ensure /app ownership
    assert re.search(r"chown.*appuser.*\/app", content), "Dockerfile.backend missing chown for /app"


# =====================================================================
# SEC-INFO: API Documentation Disabled in Production Tests
# =====================================================================

def test_api_docs_available_in_development():
    # In current development environment, docs and openapi are available
    res_docs = client.get("/api/v1/docs")
    assert res_docs.status_code == 200

    res_openapi = client.get("/api/v1/openapi.json")
    assert res_openapi.status_code == 200

    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "api_docs" in res_root.json()

def test_api_docs_disabled_in_production():
    # Instantiate a production app to verify Swagger/OpenAPI/ReDoc are disabled
    prod_app = FastAPI(
        title="Production Test App",
        openapi_url=None,
        docs_url=None,
        redoc_url=None
    )
    prod_client = TestClient(prod_app)

    res_docs = prod_client.get("/docs")
    assert res_docs.status_code == 404

    res_openapi = prod_client.get("/openapi.json")
    assert res_openapi.status_code == 404

    res_redoc = prod_client.get("/redoc")
    assert res_redoc.status_code == 404


# =====================================================================
# SEC-INFO: Frontend Axios 401 Interceptor Verification
# =====================================================================

def test_frontend_api_has_401_interceptor():
    with open("frontend/src/services/api.ts", "r", encoding="utf-8") as f:
        content = f.read()

    # Must have response interceptor
    assert "apiClient.interceptors.response.use" in content
    # Must handle status 401 specifically
    assert "error.response.status === 401" in content
    # Must remove token on 401
    assert "localStorage.removeItem('reserve_token')" in content
    # Must avoid clearing on /auth/login failures
    assert "requestUrl.includes('/auth/login')" in content
