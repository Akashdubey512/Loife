"""
reServe AI - Phase 11 Test Suite
Tests for:
1. CV Freshness Classifier dynamic model status, fallback, and scope
2. VRP Clarke-Wright + 2-Opt solver feasibility and distance improvement
3. Backend routing engine module integration (backend.routing.engine)
4. Waste ML continuous zero-record audit and honest fallback
5. Model registry and /ml/status accuracy
6. Reproducible CV training definitions
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent
client = TestClient(app)


class TestCVFreshnessClassifierPhase11:
    def test_cv_scope_and_status(self):
        from cv.freshness_classifier import cv_pipeline, SIMULATION_MODE
        assert cv_pipeline.scope == "FRUIT_IMAGERY_ONLY"
        assert SIMULATION_MODE is True  # Preserved honest simulation until weights exist
        assert cv_pipeline.model_status == "simulated"

    def test_cv_inference_contract(self):
        from cv.freshness_classifier import cv_pipeline
        # Create a tiny 10x10 mock image
        import io
        from PIL import Image
        img = Image.new("RGB", (30, 30), color=(200, 100, 50))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        res = cv_pipeline.infer(buf.getvalue(), food_name="Apple")

        assert res["food_type"] == "Apple"
        assert res["freshness_level"] in ["FRESH", "MODERATE", "DEGRADING", "ROTTEN"]
        assert 0 <= res["quality_score"] <= 100
        assert res["simulated"] is True
        assert res["human_verification_required"] is True
        assert res["model_status"] == "simulated"
        assert res["scope"] == "FRUIT_IMAGERY_ONLY"

    def test_training_scripts_exist(self):
        req_file = PROJECT_ROOT / "ml" / "cv" / "requirements-training.txt"
        train_script = PROJECT_ROOT / "ml" / "cv" / "train_fruit_classifier.py"
        audit_report = PROJECT_ROOT / "reports" / "models" / "cv_training_environment.md"
        assert req_file.exists(), "ml/cv/requirements-training.txt must exist"
        assert train_script.exists(), "ml/cv/train_fruit_classifier.py must exist"
        assert audit_report.exists(), "reports/models/cv_training_environment.md must exist"

        content = audit_report.read_text(encoding="utf-8")
        assert "FRUIT IMAGERY ONLY" in content
        assert "Source-Aware" in content or "source-aware" in content


class TestVRPOptimizationPhase11:
    def setup_method(self):
        self.vrp_dir = PROJECT_ROOT / "data" / "raw" / "vrplib"
        self.comp_report = PROJECT_ROOT / "reports" / "models" / "vrp_optimization_comparison.md"
        self.json_report = PROJECT_ROOT / "reports" / "models" / "vrp_benchmark.json"

    def test_backend_routing_engine_exports(self):
        from backend.routing.engine import (
            VehicleRoutingEngine,
            solve_cvrp_greedy,
            solve_cvrp_clarke_wright_2opt,
            solve_cvrp,
        )
        assert callable(solve_cvrp_greedy)
        assert callable(solve_cvrp_clarke_wright_2opt)
        assert callable(solve_cvrp)

    def test_clarke_wright_2opt_feasibility_and_quality(self):
        from backend.routing.engine import solve_cvrp_clarke_wright_2opt
        import vrplib
        sample_path = self.vrp_dir / "A-n32-k5.vrp"
        inst = vrplib.read_instance(str(sample_path))
        sol_path = self.vrp_dir / "A-n32-k5.sol"
        bks = vrplib.read_solution(str(sol_path))["cost"]

        res = solve_cvrp_clarke_wright_2opt(inst)
        assert res["is_feasible"] is True
        assert res["capacity_violations"] == 0
        assert res["vehicle_count"] == 5
        # Gap must be less than 10% on A-n32-k5 (BKS 784, CW+2opt 829 = 5.7%)
        gap = ((res["total_distance"] - bks) / bks) * 100.0
        assert 0 < gap < 10.0

    def test_vrp_optimization_comparison_report(self):
        assert self.comp_report.exists(), "reports/models/vrp_optimization_comparison.md must exist"
        content = self.comp_report.read_text(encoding="utf-8")
        assert "Clarke-Wright" in content
        assert "2-Opt" in content
        assert "Feasibility" in content

    def test_logistics_optimizer_2opt_integration(self):
        from logistics.optimizer import VehicleRoutingOptimizer
        opt = VehicleRoutingOptimizer(vehicle_capacity_kg=500.0)
        depot = {"lat": 28.6139, "lng": 77.2090, "name": "Central Kitchen"}
        stops = [
            {"lat": 28.6200, "lng": 77.2150, "name": "Shelter A", "quantity_kg": 50, "urgency_hours": 2},
            {"lat": 28.6300, "lng": 77.2250, "name": "Food Bank B", "quantity_kg": 80, "urgency_hours": 5},
            {"lat": 28.6250, "lng": 77.2200, "name": "Pantry C", "quantity_kg": 60, "urgency_hours": 4},
        ]
        route = opt.optimize_route(depot=depot, delivery_stops=stops)
        assert route["stops_count"] == 5
        assert route["routing_engine"] == "clarke-wright-2opt-v2.0"
        assert route["total_distance_km"] > 0


class TestModelRegistryAndStatusPhase11:
    def test_model_registry_contains_phase11_vrp(self):
        reg_path = PROJECT_ROOT / "models" / "model_registry.json"
        with open(reg_path, "r", encoding="utf-8") as f:
            registry = json.load(f)

        vrp_entry = next((e for e in registry if e.get("model_name") == "route_optimization"), None)
        assert vrp_entry is not None
        assert vrp_entry["model_version"] == "clarke-wright-2opt-v2.0"
        assert vrp_entry["metrics"]["improved_average_gap_pct"] < 10.0
        assert vrp_entry["metrics"]["feasibility"] == "100%"

    def test_ml_status_endpoint(self):
        token_resp = client.post("/api/v1/auth/login", json={"username": "admin@reserveai.com", "password": "Admin@1234"})
        assert token_resp.status_code == 200
        token = token_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/v1/ml/status", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_engines"] == 8
        vrp = next((e for e in data["engines"] if e["engine"] == "route_optimization"), None)
        assert vrp is not None
        assert vrp["model_version"] == "clarke-wright-2opt-v2.0"
        assert vrp["average_gap_pct"] < 10.0

    def test_waste_remains_fallback_no_fake_data(self):
        token_resp = client.post("/api/v1/auth/login", json={"username": "admin@reserveai.com", "password": "Admin@1234"})
        token = token_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/v1/ml/status", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        waste = next((e for e in data["engines"] if e["engine"] == "waste_prediction"), None)
        assert waste is not None
        assert waste["model_version"] == "rule-based-v1.0"
        assert waste["status"] == "fallback"
