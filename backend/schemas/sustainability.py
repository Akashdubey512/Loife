from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

class SustainabilitySummary(BaseModel):
    timeframe: str = "LAST_30_DAYS"
    food_rescued_kg: float
    co2_avoided_kg: float
    water_saved_liters: float
    land_use_prevented_sqm: float
    financial_savings_inr: float
    meals_served_to_needy: int
    esg_score_contribution: str = "+18.4%"
    waste_diversion_rate_pct: float = 34.6
    pipeline_potential_kg: float = 0.0
    measured_verified_kg: float = 0.0
    model_config = ConfigDict(from_attributes=True)

class CategoryImpact(BaseModel):
    category: str
    kg_saved: float
    co2_kg: float
    water_liters: float
    land_sqm: float = 0.0
    model_config = ConfigDict(from_attributes=True)

class ExecutiveDashboardStats(BaseModel):
    total_food_saved_kg: float
    waste_reduction_percentage: float
    carbon_reduction_kg: float
    water_saved_liters: float
    energy_efficiency_kwh: float
    operational_cost_savings_inr: float
    meals_redistributed: int
    active_kitchens_monitored: int
    active_ngo_partners: int
    model_config = ConfigDict(from_attributes=True)

class EsgAuditReportOut(BaseModel):
    report_id: str
    organization_name: str
    audit_date: datetime
    reporting_period: str
    measured_rescued_kg: float
    total_food_saved_kg: float  # alias for measured_rescued_kg — consistent with analytics API
    pipeline_potential_kg: float
    co2e_avoided_kg: float
    virtual_water_conserved_liters: float
    land_use_prevented_sqm: float
    meals_served_to_needy: int
    equivalent_trees_planted: float
    car_km_emissions_offset: float
    verified_deliveries_count: int
    scope_3_compliance_status: str
    methodology: str
    category_breakdown: List[CategoryImpact]
    assumptions: List[str]
    model_config = ConfigDict(from_attributes=True)
