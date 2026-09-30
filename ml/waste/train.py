"""
reServe AI - Waste ML Training Pipeline

Phase 9E: This module defines the training contract for the waste prediction model.

IMPORTANT: The waste model should ONLY be trained on legitimate food waste data.
Do NOT use unrelated datasets (energy, maintenance, sensor) as fake waste labels.

Current Status: NO LEGITIMATE LABELED WASTE DATA AVAILABLE.
The production engine remains rule-based (rule-based-v1.0).
"""


# ============================================================
# REQUIRED FIELDS FOR WASTE MODEL TRAINING
# ============================================================
# When legitimate waste data becomes available (e.g., from the
# platform's own operational logs), the following schema should
# be used.

WASTE_TRAINING_SCHEMA = {
    "required_features": [
        "food_category",          # e.g., COOKED_MEALS, FRESH_PRODUCE
        "quantity_prepared_kg",    # Amount prepared
        "quantity_served_kg",     # Amount actually served
        "day_of_week",            # 0=Monday, 6=Sunday
        "meal_type",              # BREAKFAST, LUNCH, DINNER
        "kitchen_id",             # Kitchen identifier
    ],
    "optional_features": [
        "quantity_returned_kg",   # Plate returns
        "storage_duration_hours", # Time in storage
        "storage_temperature_c",  # Average storage temp
        "event_size",             # Number of diners
        "weather_temperature_c",  # External temperature
        "is_holiday",             # Boolean
        "menu_item_id",           # Specific dish
    ],
    "target": "waste_kg",         # Actual waste in kg (continuous)
    "alternative_target": "waste_fraction",  # waste_kg / quantity_prepared_kg
    "minimum_training_rows": 500,
    "recommended_training_rows": 5000,
}


def check_waste_data_availability():
    """
    Check if the platform's database contains sufficient labeled waste records
    for supervised model training.

    Returns a dict with availability status.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

    try:
        from backend.core.database import SessionLocal
        from backend.models.entities import WasteEvent
        db = SessionLocal()
        count = db.query(WasteEvent).count()
        db.close()

        if count >= WASTE_TRAINING_SCHEMA["minimum_training_rows"]:
            return {
                "available": True,
                "row_count": count,
                "status": f"Found {count} waste records — sufficient for training",
            }
        elif count > 0:
            return {
                "available": False,
                "row_count": count,
                "status": f"Found {count} waste records — insufficient (need >= {WASTE_TRAINING_SCHEMA['minimum_training_rows']})",
            }
        else:
            return {
                "available": False,
                "row_count": 0,
                "status": "No waste event records found in database",
            }
    except Exception as e:
        return {
            "available": False,
            "row_count": 0,
            "status": f"Cannot check database: {e}",
        }


def extract_training_data():
    """
    Extract waste training data from the platform's own database.
    Only call this if check_waste_data_availability() returns available=True.
    """
    raise NotImplementedError(
        "Waste training data extraction is not yet implemented. "
        "Requires sufficient labeled waste records in the database."
    )


def train_waste_model():
    """
    Train a supervised waste prediction model.
    Only call this if extract_training_data() succeeds.
    """
    raise NotImplementedError(
        "Waste model training requires legitimate labeled waste data. "
        "Current status: NO LEGITIMATE LABELED WASTE DATA AVAILABLE. "
        "The production engine will remain rule-based-v1.0."
    )


if __name__ == "__main__":
    print("=" * 60)
    print("reServe AI — Waste ML Data Availability Check")
    print("=" * 60)

    result = check_waste_data_availability()
    print(f"\nStatus: {result['status']}")
    print(f"Records found: {result['row_count']}")
    print(f"Training possible: {result['available']}")

    if not result["available"]:
        print("\n[INFO] Waste ML model NOT trained — insufficient legitimate labeled data.")
        print("[INFO] Production engine remains: rule-based-v1.0")
        print("[INFO] This is an honest outcome, not a failure.")
    print()
    print("Required training schema:")
    for field in WASTE_TRAINING_SCHEMA["required_features"]:
        print(f"  - {field}")
    print(f"  Target: {WASTE_TRAINING_SCHEMA['target']}")
    print(f"  Minimum rows: {WASTE_TRAINING_SCHEMA['minimum_training_rows']}")
