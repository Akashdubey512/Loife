from backend.schemas.auth import Token, TokenPayload, LoginRequest, UserCreate, UserOut
from backend.schemas.kitchens import KitchenCreate, KitchenOut, KitchenOverview
from backend.schemas.inventory import FoodItemOut, InventoryOut, InventoryBatchOut, BatchCreate
from backend.schemas.demand import DemandForecastItem, DemandForecastResponse, ProductionBatchCreate, ProductionBatchOut
from backend.schemas.waste import WastePredictionOut, WasteEventCreate, WasteEventOut
from backend.schemas.quality import QualityScanResponse, QualityResultOut
from backend.schemas.sensors import SensorReadingCreate, SensorReadingOut, MachineHealthOut
from backend.schemas.redistribution import NGOPartnerOut, RedistributionRequestCreate, RedistributionRequestOut, NGOMatchRecommendation, MatchResponse
from backend.schemas.logistics import RouteOut, RouteOptimizeRequest, Waypoint
from backend.schemas.sustainability import SustainabilitySummary, CategoryImpact, ExecutiveDashboardStats

__all__ = [
    "Token", "TokenPayload", "LoginRequest", "UserCreate", "UserOut",
    "KitchenCreate", "KitchenOut", "KitchenOverview",
    "FoodItemOut", "InventoryOut", "InventoryBatchOut", "BatchCreate",
    "DemandForecastItem", "DemandForecastResponse", "ProductionBatchCreate", "ProductionBatchOut",
    "WastePredictionOut", "WasteEventCreate", "WasteEventOut",
    "QualityScanResponse", "QualityResultOut",
    "SensorReadingCreate", "SensorReadingOut", "MachineHealthOut",
    "NGOPartnerOut", "RedistributionRequestCreate", "RedistributionRequestOut", "NGOMatchRecommendation", "MatchResponse",
    "RouteOut", "RouteOptimizeRequest", "Waypoint",
    "SustainabilitySummary", "CategoryImpact", "ExecutiveDashboardStats"
]
