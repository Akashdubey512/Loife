"""
reServe AI - Food Waste Prediction Engine
Inputs: Production, Demand, Inventory, Expiry, Historical Waste
Outputs: Expected waste quantity, Waste probability, Root cause
"""

from typing import Dict, Any

class FoodWastePredictionEngine:
    def predict_waste(
        self,
        production_kg: float,
        expected_demand_kg: float,
        inventory_batches_near_expiry_kg: float,
        historical_waste_rate: float = 0.06
    ) -> Dict[str, Any]:
        """
        Calculates projected waste across production overages and inventory expiry decay.
        """
        # Overproduction delta
        overproduction_risk = max(0.0, production_kg - expected_demand_kg)
        
        # Expiry risk factor (portion of near expiry that can't be repurposed in current cycle)
        decay_risk = inventory_batches_near_expiry_kg * 0.35

        expected_waste = round(overproduction_risk * 0.7 + decay_risk, 1)
        waste_prob = round(min(0.85, (expected_waste / max(production_kg, 1.0)) * 1.5), 2)

        # Root cause classification
        if overproduction_risk > decay_risk and overproduction_risk > 10.0:
            root_cause = "Overproduction in scheduled meal slot exceeding projected demand"
            mitigation = f"Lower preparation threshold by {round(overproduction_risk * 0.8, 1)} kg or prepare in staged batches."
        elif decay_risk > 15.0:
            root_cause = "Cold chain batch expiration before consumption window"
            mitigation = "Trigger immediate pre-emptive redistribution or shift to secondary soup/curry processing."
        else:
            root_cause = "Normal operational trimming and plate return variance"
            mitigation = "Maintain standard prep hygiene; audit serving portion sizes."

        return {
            "expected_waste_kg": expected_waste,
            "waste_probability": waste_prob,
            "root_cause": root_cause,
            "recommended_mitigation": mitigation,
            "model_version": "waste-xgb-v2.1"
        }

waste_engine = FoodWastePredictionEngine()
