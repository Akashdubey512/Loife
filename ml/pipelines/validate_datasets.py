"""
reServe AI - Phase 8D: Data Validation Pipeline

Validates all acquired datasets against expected schemas and constraints.
Run: python -m ml.pipelines.validate_datasets
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MANIFEST_PATH = DATA_DIR / "manifests" / "dataset_manifest.json"
REPORTS_DIR = PROJECT_ROOT / "reports" / "data"


def count_csv_rows(filepath: Path) -> int:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            next(reader, None)
            return sum(1 for _ in reader)
    except Exception:
        return -1


def get_csv_columns(filepath: Path) -> list:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            return next(reader, [])
    except Exception:
        return []


def count_images(dirpath: Path) -> int:
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    return sum(1 for p in dirpath.rglob("*") if p.suffix.lower() in extensions)


def validate_ai4i():
    print("\n--- AI4I 2020 Predictive Maintenance ---")
    csv_files = list((RAW_DIR / "ai4i").rglob("*.csv"))
    if not csv_files:
        print("  [SKIP] No data files found")
        return {"status": "missing", "checks": 0, "passed": 0}

    csv_path = csv_files[0]
    rows = count_csv_rows(csv_path)
    cols = get_csv_columns(csv_path)

    checks = []
    checks.append(("row_count >= 9000", rows >= 9000))
    checks.append(("has_14_columns", len(cols) >= 14))
    checks.append(("has_machine_failure_col", any("failure" in c.lower() for c in cols)))
    checks.append(("has_temperature_col", any("temp" in c.lower() for c in cols)))
    checks.append(("has_torque_col", any("torque" in c.lower() for c in cols)))
    checks.append(("has_tool_wear_col", any("tool" in c.lower() for c in cols)))

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {name}")
    print(f"  Result: {passed}/{len(checks)} passed ({rows} rows, {len(cols)} cols)")

    return {"status": "valid" if passed == len(checks) else "partial", "checks": len(checks), "passed": passed, "rows": rows, "columns": len(cols)}


def validate_appliances_energy():
    print("\n--- Appliances Energy Prediction ---")
    csv_files = list((RAW_DIR / "appliances_energy").rglob("*.csv"))
    if not csv_files:
        print("  [SKIP] No data files found")
        return {"status": "missing", "checks": 0, "passed": 0}

    csv_path = csv_files[0]
    rows = count_csv_rows(csv_path)
    cols = get_csv_columns(csv_path)

    checks = []
    checks.append(("row_count >= 19000", rows >= 19000))
    checks.append(("has_25+_columns", len(cols) >= 25))
    checks.append(("has_appliances_col", any("appliances" in c.lower() for c in cols)))
    checks.append(("has_lights_col", any("lights" in c.lower() for c in cols)))
    checks.append(("has_temperature_cols", sum(1 for c in cols if c.startswith("T")) >= 5))

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {name}")
    print(f"  Result: {passed}/{len(checks)} passed ({rows} rows, {len(cols)} cols)")

    return {"status": "valid" if passed == len(checks) else "partial", "checks": len(checks), "passed": passed, "rows": rows, "columns": len(cols)}


def validate_poore_nemecek():
    print("\n--- Poore & Nemecek / OWID LCA ---")
    csv_path = RAW_DIR / "poore_nemecek" / "poore_nemecek_consolidated.csv"
    if not csv_path.exists():
        print("  [SKIP] Consolidated CSV not found")
        return {"status": "missing", "checks": 0, "passed": 0}

    rows = count_csv_rows(csv_path)
    cols = get_csv_columns(csv_path)

    checks = []
    checks.append(("row_count >= 40", rows >= 40))
    checks.append(("has_food_product_col", "food_product" in cols))
    checks.append(("has_ghg_col", any("ghg" in c.lower() for c in cols)))
    checks.append(("has_land_use_col", any("land" in c.lower() for c in cols)))
    checks.append(("has_water_col", any("water" in c.lower() or "freshwater" in c.lower() for c in cols)))
    checks.append(("has_source_col", "source" in cols))

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {name}")
    print(f"  Result: {passed}/{len(checks)} passed ({rows} products)")

    return {"status": "valid" if passed == len(checks) else "partial", "checks": len(checks), "passed": passed, "rows": rows}


def validate_genpact():
    print("\n--- Genpact Food Demand ---")
    train_path = RAW_DIR / "genpact" / "train.csv"
    if not train_path.exists():
        print("  [SKIP] train.csv not found")
        return {"status": "missing", "checks": 0, "passed": 0}

    rows = count_csv_rows(train_path)
    cols = get_csv_columns(train_path)

    checks = []
    checks.append(("row_count >= 10000", rows >= 10000))
    checks.append(("has_center_id", "center_id" in cols))
    checks.append(("has_meal_id", "meal_id" in cols))
    checks.append(("has_checkout_price", "checkout_price" in cols))
    checks.append(("has_base_price", "base_price" in cols))
    checks.append(("has_num_orders", "num_orders" in cols))
    checks.append(("has_week", "week" in cols))

    # Check supplementary files
    meal_path = RAW_DIR / "genpact" / "meal_info.csv"
    fc_path = RAW_DIR / "genpact" / "fulfilment_center_info.csv"
    checks.append(("meal_info_exists", meal_path.exists()))
    checks.append(("fulfilment_center_info_exists", fc_path.exists()))

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {name}")
    print(f"  Result: {passed}/{len(checks)} passed ({rows} rows)")

    return {"status": "valid" if passed == len(checks) else "partial", "checks": len(checks), "passed": passed, "rows": rows}


def validate_enose():
    print("\n--- E-nose Beef Quality Dataset (Mendeley) ---")
    csv_files = list((RAW_DIR / "enose").rglob("*.csv"))
    if not csv_files:
        print("  [SKIP] No enose data files found")
        return {"status": "missing", "checks": 0, "passed": 0}

    csv_path = csv_files[0]
    rows = count_csv_rows(csv_path)
    cols = [c.strip().lower() for c in get_csv_columns(csv_path)]

    checks = []
    checks.append(("row_count >= 20000", rows >= 20000))
    checks.append(("has_13+_columns", len(cols) >= 13))
    checks.append(("has_class_col", any("class" in c or "label" in c for c in cols)))
    checks.append(("has_temperature_col", any("temp" in c for c in cols)))
    checks.append(("has_humidity_col", any("humid" in c for c in cols)))
    checks.append(("has_mq_sensors", sum(1 for c in cols if "mq" in c) >= 6))
    checks.append(("has_tvc_col", any("tvc" in c for c in cols)))

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {name}")
    print(f"  Result: {passed}/{len(checks)} passed ({rows} rows, {len(cols)} cols)")

    return {"status": "valid" if passed == len(checks) else "partial", "checks": len(checks), "passed": passed, "rows": rows, "columns": len(cols)}


def validate_models():
    print("\n--- Trained Model Artifacts ---")
    models_dir = PROJECT_ROOT / "models"

    checks = []
    for model_name in ["demand", "maintenance", "energy", "enose"]:
        model_path = models_dir / model_name / f"{model_name}_model.joblib"
        meta_path = models_dir / model_name / f"{model_name}_model_metadata.json"
        checks.append((f"{model_name}_model_exists", model_path.exists()))
        checks.append((f"{model_name}_metadata_exists", meta_path.exists()))

        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            checks.append((f"{model_name}_has_metrics", "metrics" in meta))
            checks.append((f"{model_name}_has_version", "model_version" in meta))
            checks.append((f"{model_name}_has_limitations", "limitations" in meta and len(meta["limitations"]) > 0))

    registry_path = models_dir / "model_registry.json"
    checks.append(("model_registry_exists", registry_path.exists()))

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {name}")
    print(f"  Result: {passed}/{len(checks)} passed")

    return {"status": "valid" if passed == len(checks) else "partial", "checks": len(checks), "passed": passed}


def validate_vrplib():
    print("\n--- CVRPLIB Benchmark Instances (PUC-Rio) ---")
    vrp_files = list((RAW_DIR / "vrplib").glob("*.vrp"))
    sol_files = list((RAW_DIR / "vrplib").glob("*.sol"))
    json_report = REPORTS_DIR.parent / "models" / "vrp_benchmark.json"

    checks = []
    checks.append(("vrp_instances >= 9", len(vrp_files) >= 9))
    checks.append(("sol_files >= 9", len(sol_files) >= 9))
    checks.append(("benchmark_report_exists", json_report.exists()))

    if json_report.exists():
        with open(json_report, "r", encoding="utf-8") as f:
            bench_data = json.load(f)
        checks.append(("all_benchmark_instances_feasible", bench_data.get("all_feasible", False) is True))
        checks.append(("solution_gap_calculated", bench_data.get("average_solution_gap_pct") is not None))

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {name}")
    print(f"  Result: {passed}/{len(checks)} passed ({len(vrp_files)} instances, {len(sol_files)} solutions)")

    return {"status": "valid" if passed == len(checks) else "partial", "checks": len(checks), "passed": passed, "instances": len(vrp_files)}


def main():
    print("=" * 60)
    print("reServe AI - Phase 8D/9/10B: Data & Model Validation")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    results = {}
    results["ai4i_2020"] = validate_ai4i()
    results["appliances_energy"] = validate_appliances_energy()
    results["poore_nemecek"] = validate_poore_nemecek()
    results["genpact_demand"] = validate_genpact()
    results["enose_beef"] = validate_enose()
    results["cvrplib_benchmark"] = validate_vrplib()
    results["trained_models"] = validate_models()

    # Summary
    total_checks = sum(r["checks"] for r in results.values())
    total_passed = sum(r["passed"] for r in results.values())

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    for name, r in results.items():
        status = "[OK]" if r["passed"] == r["checks"] else "[WARN]" if r["passed"] > 0 else "[FAIL]"
        print(f"  {status} {name}: {r['passed']}/{r['checks']} checks")

    print(f"\n  TOTAL: {total_passed}/{total_checks} checks passed")

    # Save report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "validation_report.json"
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_checks": total_checks,
        "total_passed": total_passed,
        "results": results,
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Report saved: {report_path}")


if __name__ == "__main__":
    main()
