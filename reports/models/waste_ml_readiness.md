# Food Waste ML Readiness Assessment

**Assessment Date:** 2026-10-01  
**Auditor:** reServe AI Engineering & ML Data Quality  
**Status:** **NOT READY FOR SUPERVISED ML TRAINING (HONEST FALLBACK ACTIVE)**  
**Active Production Model:** `rule-based-v1.0` (Heuristic Baseline)

---

## 1. Executive Summary

A comprehensive database audit of the production database (`reserve_ai.db`) reveals **0 historical `WasteEvent` records**.

In strict adherence to the project's data integrity rules:
- **No synthetic labels** will be generated to simulate training success.
- **No unrelated datasets** (such as AI4I maintenance, Appliances Energy, or E-Nose sensors) will be misattributed as food waste records.
- Supervised ML training is **suspended** until legitimate operational data accumulates.
- The production engine remains on the validated heuristic fallback: `rule-based-v1.0`.

---

## 2. Database Audit Findings

| Table / Entity | Row Count | Labeled Waste Observations | Training Readiness |
|---|---|---|---|
| `waste_events` (`WasteEvent`) | **0** | 0 | ❌ Insufficient (Min required: 500) |
| `kitchens` (`Kitchen`) | Seed data only | 0 | Contextual reference |
| `food_items` (`FoodItem`) | Seed data only | 0 | Contextual reference |
| `inventory_batches` (`InventoryBatch`) | Dynamic test/seed data | 0 | Contextual reference |

---

## 3. Data Accumulation Requirements for Supervised Training

To transition from the rule-based fallback to an active trained model (e.g., LightGBM / XGBoost Regressor), the platform requires operational logging across institutional kitchens:

### Required Training Feature Schema

```json
{
  "required_features": [
    "kitchen_id",
    "food_category",
    "meal_slot",
    "day_of_week",
    "quantity_prepared_kg",
    "quantity_served_kg",
    "inventory_batches_near_expiry_kg"
  ],
  "optional_features": [
    "plate_waste_returned_kg",
    "diner_headcount",
    "storage_duration_hours",
    "ambient_temperature_c",
    "is_holiday_or_special_event"
  ],
  "target": "actual_waste_kg",
  "minimum_rows_threshold": 500,
  "recommended_rows_threshold": 5000
}
```

### Operational Milestone Roadmap
1. **Milestone 1 (0 – 100 Waste Events):** Run on `rule-based-v1.0`. Collect baseline error between rule-based prediction and logged waste.
2. **Milestone 2 (500 Waste Events):** Train first candidate ML model using a strict **time-aware chronological split** (e.g. first 400 events train, final 100 events test).
3. **Milestone 3 (Evaluation Gate):** Promote candidate ML model to production *only if* Test MAE is lower than the rule-based heuristic MAE by at least 15%.

---

## 4. Production Integrity

- Endpoint `/api/v1/waste/predictions` correctly reports:
  - `model_version: "rule-based-v1.0"`
  - `is_trained_model: false`
  - `root_cause` decomposition for proactive kitchen action.
- Unified model registry (`models/model_registry.json`) accurately reflects:
  - `status: "fallback"`
  - `algorithm: "Rule-based heuristic"`
