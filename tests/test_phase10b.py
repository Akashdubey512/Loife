"""
reServe AI - Phase 10B Test Suite

Tests for:
1. E-Nose validation audit & leakage-safe metrics
2. CVRPLIB acquisition, VRP benchmark execution, and feasibility
3. Food waste ML readiness assessment and honest fallback
4. CV freshness simulation transparency and fallback integrity
5. Unified model registry integrity (8 engines)
6. Backend ML status live reporting
"""

import json
import os
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 1. E-Nose Audited Validation Tests
# ============================================================

class TestEnoseAuditedValidation:
    def setup_method(self):
        self.meta_path = PROJECT_ROOT / "models" / "enose" / "enose_model_metadata.json"
        self.audit_path = PROJECT_ROOT / "reports" / "models" / "enose_validation_audit.md"

    def test_enose_metadata_has_audit_fields(self):
        assert self.meta_path.exists(), "enose_model_metadata.json must exist"
        with open(self.meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        metrics = data.get("metrics", {})
        assert "leakage_safe_accuracy" in metrics, "Must report leakage_safe_accuracy"
        assert "leakage_safe_macro_f1" in metrics, "Must report leakage_safe_macro_f1"
        assert metrics["leakage_safe_accuracy"] == 0.9310
        assert metrics["leakage_safe_macro_f1"] == 0.8718
        assert "naive_random_split_accuracy" in metrics, "Must also document naive random split baseline"

    def test_enose_audit_report_exists(self):
        assert self.audit_path.exists(), "reports/models/enose_validation_audit.md must exist"
        content = self.audit_path.read_text(encoding="utf-8")
        assert "autocorrelation" in content.lower()
        assert "15-minute block holdout" in content.lower()
        assert "BEEF QUALITY ONLY" in content

    def test_enose_scope_strict_beef(self):
        from ml.sensor.enose_classifier import enose_engine
        res = enose_engine.evaluate({
            "Temperature": 29.0, "Humidity": 60.0,
            "Mq-2": 500, "Mq-3": 400, "Mq-4": 300, "Mq-5": 300,
            "Mq-135": 450, "Mq-136": 400, "Mq-137": 750, "Mq-138": 60
        })
        assert res["scope"] == "BEEF_QUALITY_ONLY"
        assert "BEEF" in res["notice"].upper()


# ============================================================
# 2. CVRPLIB & VRP Benchmark Tests
# ============================================================

class TestVrpBenchmark:
    def setup_method(self):
        self.vrp_dir = PROJECT_ROOT / "data" / "raw" / "vrplib"
        self.json_report = PROJECT_ROOT / "reports" / "models" / "vrp_benchmark.json"
        self.md_report = PROJECT_ROOT / "reports" / "models" / "vrp_benchmark.md"

    def test_cvrplib_instances_downloaded(self):
        vrp_files = list(self.vrp_dir.glob("*.vrp"))
        sol_files = list(self.vrp_dir.glob("*.sol"))
        assert len(vrp_files) >= 9, f"Expected at least 9 .vrp files, got {len(vrp_files)}"
        assert len(sol_files) >= 9, f"Expected at least 9 .sol files, got {len(sol_files)}"

    def test_vrp_benchmark_reports_exist(self):
        assert self.json_report.exists(), "vrp_benchmark.json must exist"
        assert self.md_report.exists(), "vrp_benchmark.md must exist"

    def test_vrp_benchmark_feasibility_and_metrics(self):
        with open(self.json_report, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["all_feasible"] is True, "All benchmark instances must be 100% feasible"
        assert data["total_instances_evaluated"] >= 9
        assert data["average_solution_gap_pct"] is not None
        assert 0 < data["average_solution_gap_pct"] < 60

    def test_vrp_solver_execution(self):
        from ml.pipelines.benchmark_vrp import solve_cvrp_greedy
        import vrplib
        sample_path = self.vrp_dir / "A-n32-k5.vrp"
        inst = vrplib.read_instance(str(sample_path))
        res = solve_cvrp_greedy(inst)
        assert res["is_feasible"] is True
        assert res["capacity_violations"] == 0
        assert res["vehicle_count"] == 5
        assert res["total_distance"] > 0


# ============================================================
# 3. Waste ML Readiness Tests
# ============================================================

class TestWasteReadiness:
    def setup_method(self):
        self.report_path = PROJECT_ROOT / "reports" / "models" / "waste_ml_readiness.md"

    def test_waste_readiness_report_exists(self):
        assert self.report_path.exists(), "waste_ml_readiness.md must exist"
        content = self.report_path.read_text(encoding="utf-8")
        assert "rule-based-v1.0" in content
        assert "0 historical" in content or "insufficient" in content.lower()

    def test_waste_engine_honest_fallback(self):
        from ml.waste_predictor import waste_engine
        res = waste_engine.predict_waste(
            production_kg=120.0,
            expected_demand_kg=100.0,
            inventory_batches_near_expiry_kg=5.0
        )
        assert res["model_version"] == "rule-based-v1.0"
        assert "trained" not in res["model_version"].lower()


# ============================================================
# 4. CV Freshness Simulation Honesty Tests
# ============================================================

class TestCvFreshnessHonesty:
    def setup_method(self):
        self.report_path = PROJECT_ROOT / "reports" / "models" / "cv_freshness_status.md"

    def test_cv_status_audit_exists(self):
        assert self.report_path.exists(), "cv_freshness_status.md must exist"
        content = self.report_path.read_text(encoding="utf-8")
        assert "3,200" in content
        assert "SIMULATION_MODE = True" in content
        assert "PyTorch" in content

    def test_cv_simulation_mode_is_true(self):
        from cv.freshness_classifier import SIMULATION_MODE
        assert SIMULATION_MODE is True, "Must remain simulated until genuine trained weights exist"

    def test_cv_infer_invalid_image_fallback(self):
        from cv.freshness_classifier import cv_pipeline
        res = cv_pipeline.infer(b"corrupted-invalid-bytes", food_name="Banana")
        assert res["simulated"] is True
        assert res["freshness_level"] in ["FRESH", "MODERATE", "DEGRADING", "ROTTEN"]
        assert "simulation_notice" in res or "simulated" in res


# ============================================================
# 5. Model Registry & ML Status Tests (Phase 10B)
# ============================================================

class TestModelRegistryAndStatusPhase10B:
    def setup_method(self):
        self.registry_path = PROJECT_ROOT / "models" / "model_registry.json"

    def test_registry_contains_8_engines(self):
        with open(self.registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
        names = {e["model_name"] for e in registry}
        expected = {
            "demand_forecasting",
            "predictive_maintenance",
            "energy_forecasting",
            "waste_prediction",
            "cv_freshness_classifier",
            "enose_beef_quality",
            "sustainability_lca",
            "route_optimization",
        }
        assert expected.issubset(names), f"Missing engines: {expected - names}"

    def test_ml_status_reports_route_optimization(self):
        from backend.ml_status import _load_registry
        reg = _load_registry()
        route_entry = next((e for e in reg if e.get("model_name") == "route_optimization"), None)
        assert route_entry is not None
        assert route_entry["status"] == "active"
        assert "cvrplib" in route_entry.get("dataset_source", "").lower()
