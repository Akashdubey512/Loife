"""
reServe AI - Sustainability Intelligence Engine
Implements lifecycle assessment formulas from Poore & Nemecek (Science 2018)
and Our World in Data (OWID) food footprints.
"""

from typing import Dict, Any

# Poore & Nemecek (2018) verified factors:
# Footprints per kilogram of food saved / diverted
FACTORS = {
    "GRAINS": {"co2_kg": 1.4, "water_l": 1200.0, "land_sqm": 2.1},
    "VEGETABLES": {"co2_kg": 0.5, "water_l": 322.0, "land_sqm": 0.4},
    "FRUITS": {"co2_kg": 0.7, "water_l": 280.0, "land_sqm": 0.6},
    "DAIRY": {"co2_kg": 3.2, "water_l": 628.0, "land_sqm": 4.5},
    "MEAT_POULTRY": {"co2_kg": 9.8, "water_l": 4325.0, "land_sqm": 12.2},
    "COOKED_MEALS": {"co2_kg": 2.5, "water_l": 550.0, "land_sqm": 2.0},
    "BAKERY": {"co2_kg": 1.6, "water_l": 1100.0, "land_sqm": 1.8},
}

class SustainabilityIntelligenceEngine:
    def calculate_impact(self, category: str, quantity_kg: float) -> Dict[str, float]:
        factors = FACTORS.get(category.upper(), FACTORS["COOKED_MEALS"])
        co2_avoided = round(quantity_kg * factors["co2_kg"], 2)
        water_saved = round(quantity_kg * factors["water_l"], 1)
        land_prevented = round(quantity_kg * factors["land_sqm"], 2)
        financial_val = round(quantity_kg * 110.0, 2)  # Average INR 110/kg meal value

        return {
            "quantity_kg": quantity_kg,
            "category": category,
            "co2_avoided_kg": co2_avoided,
            "water_saved_liters": water_saved,
            "land_prevented_sqm": land_prevented,
            "financial_savings_inr": financial_val,
            "equivalent_trees_planted": round(co2_avoided / 21.77, 1), # 1 tree absorbs ~21.77kg CO2/year
            "car_km_emissions_offset": round(co2_avoided / 0.192, 1)  # Average passenger car emits 0.192 kg CO2/km
        }

sustainability_engine = SustainabilityIntelligenceEngine()
