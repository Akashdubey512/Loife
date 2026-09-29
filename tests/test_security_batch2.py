import os
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.security import hash_password, verify_password
from backend.core.database import SessionLocal, Base, engine
from backend.models.entities import User
from backend.services.seed_service import seed_database
from backend.core.config import settings

client = TestClient(app)

# -------------------------------------------------------------
# SEC-HIGH-01: Password Security Tests
# -------------------------------------------------------------

def test_correct_password_against_valid_hash_succeeds():
    raw_pwd = "SuperSecretPassword@2026"
    valid_hash = hash_password(raw_pwd)
    assert verify_password(raw_pwd, valid_hash) is True

def test_incorrect_password_against_valid_hash_fails():
    raw_pwd = "SuperSecretPassword@2026"
    valid_hash = hash_password(raw_pwd)
    assert verify_password("WrongPassword!123", valid_hash) is False

def test_malformed_hash_fails_securely():
    raw_pwd = "Password@123"
    # No dollar sign delimiter
    assert verify_password(raw_pwd, "malformednohashhere") is False
    # Empty string
    assert verify_password(raw_pwd, "") is False
    # Multiple dollar signs
    assert verify_password(raw_pwd, "salt$part1$part2") is False
    # Non-hex salt/key
    assert verify_password(raw_pwd, "nothex$nothex") is False
    # Non-string input
    assert verify_password(raw_pwd, None) is False

def test_plaintext_stored_password_rejected():
    raw_pwd = "PlaintextPassword123"
    # Even if stored password equals raw password, plaintext comparison must NEVER succeed
    assert verify_password(raw_pwd, raw_pwd) is False

def test_password_verification_errors_do_not_bypass_login():
    response = client.post("/api/v1/auth/login", json={
        "username": "kitchen@reserveai.com",
        "password": "IncorrectPassword!999"
    })
    assert response.status_code == 401
    assert "access_token" not in response.json()

def test_existing_login_remains_functional():
    response = client.post("/api/v1/auth/login", json={
        "username": "kitchen@reserveai.com",
        "password": "Kitchen@1234"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "kitchen@reserveai.com"


# -------------------------------------------------------------
# SEC-HIGH-03: Database Seeding Safety Tests
# -------------------------------------------------------------

def test_production_environment_rejects_automatic_seeding(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="strictly prohibited in production"):
        seed_database()

def test_development_seeding_works_when_explicitly_invoked():
    # Explicit invocation should complete without error
    seed_database(force=True)
    db: Session = SessionLocal()
    try:
        user_count = db.query(User).count()
        assert user_count >= 5
    finally:
        db.close()

def test_repeated_seeding_is_idempotent_and_does_not_duplicate_users():
    db: Session = SessionLocal()
    try:
        count_before = db.query(User).count()
    finally:
        db.close()

    # Re-run explicit seeding
    seed_database(force=True)

    db = SessionLocal()
    try:
        count_after = db.query(User).count()
        assert count_after == count_before
    finally:
        db.close()

def test_existing_user_credentials_and_roles_not_overwritten():
    db: Session = SessionLocal()
    try:
        # Check kitchen user
        user = db.query(User).filter(User.email == "kitchen@reserveai.com").first()
        assert user is not None
        assert user.role == "KITCHEN_MANAGER"
        original_hash = user.hashed_password
    finally:
        db.close()

    # Re-run explicit seeding
    seed_database(force=True)

    db = SessionLocal()
    try:
        user_recheck = db.query(User).filter(User.email == "kitchen@reserveai.com").first()
        assert user_recheck.role == "KITCHEN_MANAGER"
        assert user_recheck.hashed_password == original_hash
    finally:
        db.close()
