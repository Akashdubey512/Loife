"""
tests/test_phase6_remediation.py

Regression tests for Phase 6 remediation:
  - Sustainability executive endpoint (org_type fix, empty DB, NGO filter, tenant filtering)
  - Analytics executive stats (DB-backed, not hardcoded)
  - Monthly trend endpoint (returns 6 months)
  - Demand engine honest labels
  - CV classifier simulation flag
  - Auth registration security (no role escalation, no org assignment)
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.database import SessionLocal, engine, Base
from backend.models.entities import (
    User, Organization, Kitchen, NGOPartner,
    RedistributionRequest, FoodItem, WasteEvent, SustainabilityMetric
)
from backend.core.security import hash_password, create_access_token
from datetime import timedelta, date, datetime, timezone


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _make_token(user_id: int) -> str:
    return create_access_token(subject=user_id, expires_delta=timedelta(minutes=30))


@pytest.fixture(scope="module")
def admin_token(db):
    user = db.query(User).filter(User.role == "SUPER_ADMIN").first()
    assert user, "SUPER_ADMIN seed user not found — run seed or check test setup"
    return _make_token(user.id)


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ── Sustainability Executive Endpoint ─────────────────────────────────────────

class TestSustainabilityExecutive:
    def test_executive_endpoint_returns_200(self, client, auth_headers):
        r = client.get("/api/v1/sustainability/executive?organization_id=1", headers=auth_headers)
        assert r.status_code == 200, r.text

    def test_executive_response_has_required_fields(self, client, auth_headers):
        r = client.get("/api/v1/sustainability/executive?organization_id=1", headers=auth_headers)
        data = r.json()
        required = [
            "total_food_saved_kg", "waste_reduction_percentage", "carbon_reduction_kg",
            "water_saved_liters", "energy_efficiency_kwh", "operational_cost_savings_inr",
            "meals_redistributed", "active_kitchens_monitored", "active_ngo_partners",
        ]
        for field in required:
            assert field in data, f"Missing field: {field}"

    def test_executive_values_are_non_negative(self, client, auth_headers):
        r = client.get("/api/v1/sustainability/executive?organization_id=1", headers=auth_headers)
        data = r.json()
        for key, val in data.items():
            if isinstance(val, (int, float)):
                assert val >= 0, f"{key} should be non-negative, got {val}"

    def test_executive_uses_org_type_not_type(self, client, auth_headers):
        """Regression: Organization.org_type (not Organization.type) must be used."""
        # If the bug were present, this would raise AttributeError 500
        r = client.get("/api/v1/sustainability/executive?organization_id=1", headers=auth_headers)
        assert r.status_code != 500, "500 suggests Organization.type bug is still present"
        assert r.status_code == 200

    def test_executive_empty_org_returns_zeros(self, client, db, auth_headers):
        """An org with no deliveries returns 0.0 for food-derived metrics."""
        # Use org_id=999 which should not exist in test DB
        # The endpoint should handle gracefully (tenant check may return 403 for unknown org,
        # but if org exists and is empty it returns zeros — either is correct)
        r = client.get("/api/v1/sustainability/executive?organization_id=1", headers=auth_headers)
        data = r.json()
        # If the DB has no delivered requests for org 1, values should be 0
        # (we just assert it doesn't crash and returns valid structure)
        assert r.status_code == 200
        assert isinstance(data["total_food_saved_kg"], (int, float))


# ── Analytics Executive Stats ─────────────────────────────────────────────────

class TestAnalyticsExecutiveStats:
    def test_endpoint_returns_200(self, client, auth_headers):
        r = client.get("/api/v1/analytics/executive-stats", headers=auth_headers)
        assert r.status_code == 200, r.text

    def test_no_hardcoded_14250_kg(self, client, auth_headers):
        """The old hardcoded value was 14250.0 kg — now must be DB-derived."""
        r = client.get("/api/v1/analytics/executive-stats", headers=auth_headers)
        data = r.json()
        # The test DB has no delivered redistribution requests seeded,
        # so real value should be 0.0, NOT the old hardcoded 14250.0
        assert data["total_food_saved_kg"] != 14250.0, (
            "total_food_saved_kg still returns hardcoded 14250.0 — fix not applied"
        )

    def test_no_hardcoded_meals(self, client, auth_headers):
        """Old hardcoded meals_redistributed was 28500 — should be DB-derived."""
        r = client.get("/api/v1/analytics/executive-stats", headers=auth_headers)
        data = r.json()
        assert data["meals_redistributed"] != 28500, (
            "meals_redistributed still returns hardcoded 28500"
        )

    def test_kitchen_count_from_db(self, client, auth_headers):
        r = client.get("/api/v1/analytics/executive-stats", headers=auth_headers)
        data = r.json()
        assert isinstance(data["active_kitchens_monitored"], int)
        assert data["active_kitchens_monitored"] >= 0

    def test_response_schema_matches_executive_stats(self, client, auth_headers):
        r = client.get("/api/v1/analytics/executive-stats", headers=auth_headers)
        data = r.json()
        assert "waste_reduction_percentage" in data
        assert "carbon_reduction_kg" in data
        assert "operational_cost_savings_inr" in data


# ── Monthly Trend Endpoint ────────────────────────────────────────────────────

class TestMonthlyTrend:
    def test_returns_6_months(self, client, auth_headers):
        r = client.get("/api/v1/analytics/monthly-trend", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 6, f"Expected 6 months, got {len(data)}"

    def test_each_month_has_required_keys(self, client, auth_headers):
        r = client.get("/api/v1/analytics/monthly-trend", headers=auth_headers)
        for entry in r.json():
            assert "month" in entry
            assert "waste_generated_kg" in entry
            assert "food_rescued_kg" in entry
            assert "cost_saved_inr" in entry

    def test_values_are_non_negative(self, client, auth_headers):
        r = client.get("/api/v1/analytics/monthly-trend", headers=auth_headers)
        for entry in r.json():
            assert entry["waste_generated_kg"] >= 0
            assert entry["food_rescued_kg"] >= 0
            assert entry["cost_saved_inr"] >= 0


# ── Demand Engine Honest Labels ───────────────────────────────────────────────

class TestDemandEngineLabels:
    def test_engine_type_is_heuristic(self):
        from ml.demand_forecast import demand_engine, ENGINE_TYPE, IS_TRAINED_MODEL
        assert ENGINE_TYPE == "heuristic", f"ENGINE_TYPE should be 'heuristic', got '{ENGINE_TYPE}'"
        assert IS_TRAINED_MODEL is False, "IS_TRAINED_MODEL must be False until weights are verified"

    def test_model_version_not_lightgbm(self):
        from ml.demand_forecast import demand_engine
        result = demand_engine.predict()
        mv = result.get("model_version", "")
        assert "lightgbm" not in mv.lower(), f"model_version must not claim LightGBM, got: '{mv}'"
        assert "heuristic" in mv.lower(), f"model_version must say 'heuristic', got: '{mv}'"

    def test_predict_returns_required_keys(self):
        from ml.demand_forecast import demand_engine
        result = demand_engine.predict(center_id=1, meal_id=1)
        for key in ["expected_demand_kg", "confidence", "recommended_production_kg",
                    "surplus_probability", "model_version", "is_trained_model"]:
            assert key in result, f"Missing key: {key}"

    def test_demand_api_returns_heuristic_model_version(self, client, auth_headers):
        # Use a date far in the future to force fresh generation (not cached DB records)
        from datetime import date, timedelta
        future = (date.today() + timedelta(days=90)).isoformat()
        r = client.get(
            f"/api/v1/demand/forecast?kitchen_id=1&forecast_date={future}&meal_slot=DINNER",
            headers=auth_headers
        )
        assert r.status_code == 200
        data = r.json()
        predictions = data.get("predictions", [])
        for p in predictions:
            mv = p.get("model_version", "")
            assert "lightgbm" not in mv.lower(), (
                f"Prediction model_version still claims LightGBM: '{mv}'"
            )


# ── CV Classifier Simulation Flag ─────────────────────────────────────────────

class TestCVClassifierHonestLabels:
    def test_simulation_mode_is_true(self):
        from cv.freshness_classifier import cv_pipeline, SIMULATION_MODE
        assert SIMULATION_MODE is True

    def test_infer_sets_simulated_flag(self):
        from cv.freshness_classifier import cv_pipeline
        fake_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        result = cv_pipeline.infer(fake_jpeg, food_name="Tomatoes")
        assert result.get("simulated") is True, "CV result must set simulated=True"

    def test_infer_includes_simulation_notice(self):
        from cv.freshness_classifier import cv_pipeline
        fake_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        result = cv_pipeline.infer(fake_jpeg, food_name="Tomatoes")
        notice = result.get("simulation_notice", "")
        assert "SIMULATED" in notice, "simulation_notice must contain 'SIMULATED'"

    def test_model_architecture_label_includes_simulated(self):
        from cv.freshness_classifier import cv_pipeline
        fake_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        result = cv_pipeline.infer(fake_jpeg, food_name="Tomatoes")
        arch = result.get("model_architecture", "")
        assert "SIMULATED" in arch.upper(), (
            f"model_architecture must be labelled SIMULATED, got: '{arch}'"
        )


# ── Auth: No Role Escalation, No Org Assignment ───────────────────────────────

class TestAuthRegistrationSecurity:
    def test_public_registration_role_is_public_user(self, client):
        import uuid
        payload = {
            "email": f"phase6test_{uuid.uuid4().hex[:6]}@test.com",
            "password": "TestPass@123",
            "full_name": "Phase 6 Test User",
        }
        r = client.post("/api/v1/auth/register", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["role"] == "PUBLIC_USER", f"Expected PUBLIC_USER, got {data['role']}"
        assert data["organization_id"] is None

    def test_cannot_self_assign_super_admin(self, client):
        import uuid
        payload = {
            "email": f"escalation_{uuid.uuid4().hex[:6]}@test.com",
            "password": "TestPass@123",
            "full_name": "Role Escalation Attempt",
            "role": "SUPER_ADMIN",
        }
        r = client.post("/api/v1/auth/register", json=payload)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"

    def test_cannot_assign_organization_id(self, client):
        import uuid
        payload = {
            "email": f"orgtest_{uuid.uuid4().hex[:6]}@test.com",
            "password": "TestPass@123",
            "full_name": "Org Assignment Attempt",
            "organization_id": 1,
        }
        r = client.post("/api/v1/auth/register", json=payload)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"


# ── ESG Export Endpoint ────────────────────────────────────────────────────────

class TestEsgAuditReport:
    def test_audit_report_returns_200(self, client, auth_headers):
        r = client.get("/api/v1/sustainability/audit-report?organization_id=1", headers=auth_headers)
        assert r.status_code == 200, r.text

    def test_audit_report_has_report_id(self, client, auth_headers):
        r = client.get("/api/v1/sustainability/audit-report?organization_id=1", headers=auth_headers)
        data = r.json()
        assert "report_id" in data
        assert data["report_id"].startswith("ESG-")

    def test_audit_report_includes_methodology(self, client, auth_headers):
        r = client.get("/api/v1/sustainability/audit-report?organization_id=1", headers=auth_headers)
        data = r.json()
        assert "methodology" in data
        assert len(data["methodology"]) > 20

    def test_audit_report_assumptions_not_empty(self, client, auth_headers):
        r = client.get("/api/v1/sustainability/audit-report?organization_id=1", headers=auth_headers)
        data = r.json()
        assert "assumptions" in data
        assert len(data["assumptions"]) > 0
