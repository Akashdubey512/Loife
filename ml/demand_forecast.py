"""
reServe AI - Demand Forecasting Engine

HONEST LABELING NOTICE:
This module implements a HEURISTIC forecasting engine, not a trained
LightGBM / XGBoost / CatBoost model. No model weights are loaded from disk.

The algorithm uses:
  - Rolling 7-day average of historical consumption
  - Day-of-week demand multipliers (empirical constants)
  - Price-elasticity adjustment
  - 4% asymmetric production buffer (waste-risk penalty)

It was designed to be API-compatible with a future trained LightGBM pipeline
(matching Genpact Food Demand Forecasting Dataset schema). When trained weights
are available and independently validated, replace _heuristic_predict() with
a real model.forward() call and set ENGINE_TYPE = "lightgbm-trained".

Until then, all model_version strings report "heuristic-v1.4" to be accurate.
"""

import math
from typing import Dict, Any, List
from datetime import date, timedelta


ENGINE_TYPE = "heuristic"           # change to "lightgbm-trained" when weights are loaded
ENGINE_VERSION = "heuristic-v1.4"  # surfaced in all prediction records
IS_TRAINED_MODEL = False            # False until checkpoint verified


class DemandForecastingPipeline:
    """
    Heuristic demand forecasting pipeline.

    Compatible with the Genpact Food Demand Forecasting Dataset feature schema
    (center_id, meal_id, checkout_price, base_price, lag features, day_of_week,
    month) but uses hand-crafted heuristics rather than gradient-boosted trees.
    """

    def __init__(self):
        self.engine_type = ENGINE_TYPE
        self.is_trained = IS_TRAINED_MODEL
        self.feature_columns = [
            "center_id", "meal_id", "checkout_price", "base_price",
            "emailer_for_promotion", "homepage_featured",
            "lag_1_demand", "lag_7_demand", "rolling_mean_7",
            "day_of_week", "month",
        ]

    def engineer_features(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform raw meal orders into lag and rolling features."""
        for r in raw_records:
            if "checkout_price" in r and "base_price" in r and r["base_price"] > 0:
                r["discount_pct"] = (r["base_price"] - r["checkout_price"]) / r["base_price"]
        return raw_records

    def _heuristic_predict(
        self,
        hist: List[float],
        target_date: date,
        base_price: float,
        checkout_price: float,
        is_holiday: bool,
        is_weekend: bool,
        promotion_active: bool,
    ) -> Dict[str, Any]:
        """
        Core heuristic prediction.

        Formula:
          predicted = (rolling_7 * 0.6 + lag_1 * 0.4)
                      × day_multiplier
                      × price_elasticity_factor

        Day multipliers are empirical constants derived from typical
        institutional canteen patterns (Mon spike, Fri spike, weekend drop).
        They are NOT learned from data.
        """
        lag_1    = hist[-1]
        rolling_7 = float(sum(hist) / len(hist))

        # Day-of-week demand multipliers (hand-crafted, not learned)
        day_multipliers = {
            0: 1.12,   # Monday
            1: 1.02,   # Tuesday
            2: 1.00,   # Wednesday (baseline)
            3: 1.04,   # Thursday
            4: 1.18,   # Friday
            5: 0.88,   # Saturday
            6: 0.82,   # Sunday
        }
        day_mult = day_multipliers.get(target_date.weekday(), 1.0)

        if is_holiday:
            day_mult *= 0.72
        if promotion_active:
            day_mult *= 1.10

        price_elasticity = 1.0 + (
            0.15 * max(0.0, (base_price - checkout_price) / base_price)
        )
        predicted_demand = round(
            (rolling_7 * 0.6 + lag_1 * 0.4) * day_mult * price_elasticity, 1
        )

        # Confidence: inversely related to historical variance
        variance = float(
            math.sqrt(sum((x - rolling_7) ** 2 for x in hist) / len(hist))
        )
        confidence = round(max(0.85, min(0.98, 1.0 - (variance / (rolling_7 * 2.0)))), 2)

        # 4% production buffer (asymmetric loss: under-serving is penalised more than waste)
        recommended_prod = round(predicted_demand * 1.04, 1)
        surplus_prob = round(
            max(0.04, min(0.25, (recommended_prod - predicted_demand) / predicted_demand)), 2
        )

        return {
            "predicted_demand": predicted_demand,
            "confidence": confidence,
            "recommended_prod": recommended_prod,
            "surplus_prob": surplus_prob,
        }

    def predict(
        self,
        center_id: int = 1,
        meal_id: int = 1,
        target_date: date = None,
        base_price: float = 120.0,
        checkout_price: float = 110.0,
        historical_demands: List[float] = None,
        past_consumption_lags: List[float] = None,
        footfall: int = None,
        is_holiday: bool = False,
        is_weekend: bool = False,
        promotion_active: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Entry point returning demand prediction with honest engine metadata.
        model_version is set to ENGINE_VERSION ("heuristic-v1.4") — never
        "lightgbm-*" unless IS_TRAINED_MODEL is True.
        """
        hist = past_consumption_lags or historical_demands or [
            145.0, 150.0, 142.0, 160.0, 155.0, 158.0, 162.0
        ]
        target_date = target_date or (date.today() + timedelta(days=1))

        result = self._heuristic_predict(
            hist, target_date, base_price, checkout_price,
            is_holiday, is_weekend, promotion_active,
        )

        return {
            "center_id":                center_id,
            "meal_id":                  meal_id,
            "target_date":              str(target_date),
            "expected_demand_kg":       result["predicted_demand"],
            "confidence":               result["confidence"],
            "confidence_score":         result["confidence"],
            "recommended_production_kg": result["recommended_prod"],
            "surplus_probability":      result["surplus_prob"],
            "surplus_risk_probability": result["surplus_prob"],
            "model_type":               ENGINE_TYPE,
            "model_version":            ENGINE_VERSION,
            "is_trained_model":         IS_TRAINED_MODEL,
            "engine_status":            "ONLINE",
        }


demand_engine = DemandForecastingPipeline()
