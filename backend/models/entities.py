from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship

from backend.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False, index=True)
    org_type = Column(String(50), default="UNIVERSITY")
    contact_email = Column(String(100), nullable=False)
    phone = Column(String(30))
    address = Column(Text)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    kitchens = relationship("Kitchen", back_populates="organization", cascade="all, delete-orphan")
    sustainability_metrics = relationship("SustainabilityMetric", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    role = Column(String(40), default="KITCHEN_MANAGER")  # SUPER_ADMIN, ORG_ADMIN, KITCHEN_MANAGER, QUALITY_INSPECTOR, LOGISTICS_COORDINATOR, NGO_REP
    phone_number = Column(String(30), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="users")


class Kitchen(Base):
    __tablename__ = "kitchens"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(120), nullable=False)
    facility_code = Column(String(50), unique=True, index=True)
    daily_meal_capacity = Column(Integer, default=1500)
    kitchen_type = Column(String(50), default="MESS_HALL")
    latitude = Column(Float, default=28.6139)
    longitude = Column(Float, default=77.2090)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="kitchens")
    inventory = relationship("Inventory", back_populates="kitchen", cascade="all, delete-orphan")
    production_batches = relationship("ProductionBatch", back_populates="kitchen", cascade="all, delete-orphan")
    sensor_readings = relationship("SensorReading", back_populates="kitchen", cascade="all, delete-orphan")
    machine_events = relationship("MachineEvent", back_populates="kitchen", cascade="all, delete-orphan")
    redistribution_requests = relationship("RedistributionRequest", back_populates="kitchen", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="kitchen", cascade="all, delete-orphan")


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    category = Column(String(50), default="COOKED_MEALS")  # GRAINS, VEGETABLES, DAIRY, FRUITS, MEAT_POULTRY, COOKED_MEALS, BAKERY
    perishable_type = Column(String(50), default="HIGHLY_PERISHABLE")
    default_shelf_life_hours = Column(Integer, default=24)
    carbon_footprint_per_kg = Column(Float, default=2.5)  # Poore & Nemecek (kg CO2e / kg)
    water_footprint_per_kg = Column(Float, default=650.0)  # Liters / kg

    inventory_items = relationship("Inventory", back_populates="food_item")
    demand_predictions = relationship("DemandPrediction", back_populates="food_item")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    current_quantity_kg = Column(Float, default=0.0)
    reorder_threshold_kg = Column(Float, default=15.0)
    storage_location = Column(String(80), default="Dry Pantry Rack 1")
    last_audited_at = Column(DateTime, default=utc_now)

    kitchen = relationship("Kitchen", back_populates="inventory")
    food_item = relationship("FoodItem", back_populates="inventory_items")
    batches = relationship("InventoryBatch", back_populates="inventory", cascade="all, delete-orphan")


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    batch_number = Column(String(60), unique=True, index=True, nullable=False)
    initial_quantity_kg = Column(Float, nullable=False)
    remaining_quantity_kg = Column(Float, nullable=False)
    procured_at = Column(DateTime, default=utc_now)
    expiry_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(40), default="OPTIMAL")  # OPTIMAL, NEARING_EXPIRY, EXPIRED, DEPLETED, REDISTRIBUTED

    inventory = relationship("Inventory", back_populates="batches")
    quality_scans = relationship("QualityResult", back_populates="batch")


class ProductionBatch(Base):
    __tablename__ = "production_batches"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    planned_quantity_kg = Column(Float, nullable=False)
    actual_produced_kg = Column(Float, nullable=True)
    surplus_quantity_kg = Column(Float, default=0.0)
    meal_slot = Column(String(30), default="LUNCH")  # BREAKFAST, LUNCH, DINNER, SNACK
    scheduled_for = Column(Date, nullable=False)
    status = Column(String(40), default="SCHEDULED")  # SCHEDULED, IN_PREPARATION, COMPLETED, SURPLUS_FLAGGED

    kitchen = relationship("Kitchen", back_populates="production_batches")
    food_item = relationship("FoodItem")


class DemandHistory(Base):
    __tablename__ = "demand_history"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    meal_slot = Column(String(30), nullable=False)
    orders_count = Column(Integer, default=0)
    actual_consumption_kg = Column(Float, nullable=False)
    footfall = Column(Integer, default=0)
    is_holiday = Column(Boolean, default=False)
    weather_condition = Column(String(50), default="Sunny")


class DemandPrediction(Base):
    __tablename__ = "demand_predictions"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    prediction_date = Column(Date, nullable=False, index=True)
    meal_slot = Column(String(30), nullable=False)
    expected_demand_kg = Column(Float, nullable=False)
    confidence_score = Column(Float, default=0.92)
    recommended_production_kg = Column(Float, nullable=False)
    surplus_risk_probability = Column(Float, default=0.1)
    model_version = Column(String(50), default="heuristic-v1.4")
    generated_at = Column(DateTime, default=utc_now)

    food_item = relationship("FoodItem", back_populates="demand_predictions")


class WasteEvent(Base):
    __tablename__ = "waste_events"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("inventory_batches.id"), nullable=True)
    production_id = Column(Integer, ForeignKey("production_batches.id"), nullable=True)
    quantity_wasted_kg = Column(Float, nullable=False)
    waste_stage = Column(String(50), default="OVERPRODUCTION")  # STORAGE_EXPIRY, PREP_TRIMMING, OVERPRODUCTION, PLATE_LEFTOVER, EQUIPMENT_FAILURE
    primary_cause = Column(String(200), nullable=False)
    financial_loss_inr = Column(Float, default=0.0)
    logged_at = Column(DateTime, default=utc_now, index=True)


class WastePrediction(Base):
    __tablename__ = "waste_predictions"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=False)
    forecast_date = Column(Date, nullable=False, index=True)
    expected_waste_kg = Column(Float, nullable=False)
    waste_probability = Column(Float, nullable=False)
    predicted_root_cause = Column(String(150))
    prevention_recommendation = Column(Text)
    generated_at = Column(DateTime, default=utc_now)


class QualityResult(Base):
    __tablename__ = "quality_results"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("inventory_batches.id"), nullable=True)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    image_url = Column(String(300), nullable=False)
    freshness_level = Column(String(40), default="FRESH")  # FRESH, MODERATE, DEGRADING, ROTTEN
    freshness_score = Column(Float, default=95.0)  # 0 to 100
    remaining_shelf_life_days = Column(Float, default=3.0)
    redistribution_status = Column(String(50), default="SAFE_FOR_REDISTRIBUTION")  # SAFE_FOR_REDISTRIBUTION, PROCESS_IMMEDIATELY, COMPOST_ONLY, HAZARD_DISCARD
    confidence = Column(Float, default=0.95)
    scanned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    batch = relationship("InventoryBatch", back_populates="quality_scans")
    food_item = relationship("FoodItem")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=False)
    sensor_id = Column(String(50), nullable=False, index=True)
    sensor_type = Column(String(40), nullable=False)  # TEMPERATURE, HUMIDITY, GAS_METHANE, AMMONIA, DOOR_OPEN
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # °C, %RH, PPM
    storage_zone = Column(String(60), nullable=False)
    is_threshold_breached = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=utc_now, index=True)

    kitchen = relationship("Kitchen", back_populates="sensor_readings")


class EnergyConsumption(Base):
    __tablename__ = "energy_consumption"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=False)
    device_name = Column(String(80))
    power_kwh = Column(Float, nullable=False)
    cost_inr = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=utc_now, index=True)


class WaterConsumption(Base):
    __tablename__ = "water_consumption"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=False)
    flow_liters = Column(Float, nullable=False)
    usage_category = Column(String(50), default="FOOD_PREP")
    timestamp = Column(DateTime, default=utc_now, index=True)


class MachineEvent(Base):
    __tablename__ = "machine_events"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=False)
    machine_id = Column(String(50), nullable=False, index=True)
    machine_type = Column(String(60), default="BLAST_CHILLER")
    rotational_speed_rpm = Column(Float, default=1500.0)
    torque_nm = Column(Float, default=40.0)
    tool_wear_min = Column(Float, default=15.0)
    air_temp_k = Column(Float, default=300.0)
    process_temp_k = Column(Float, default=310.0)
    failure_probability = Column(Float, default=0.02)
    failure_type = Column(String(80), default="None")
    status = Column(String(40), default="HEALTHY")  # HEALTHY, MAINTENANCE_REQUIRED, CRITICAL_SHUTDOWN
    created_at = Column(DateTime, default=utc_now)

    kitchen = relationship("Kitchen", back_populates="machine_events")


class NGOPartner(Base):
    __tablename__ = "ngo_partners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    registration_number = Column(String(80), unique=True)
    contact_person = Column(String(100))
    phone = Column(String(30), nullable=False)
    email = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    daily_meal_capacity = Column(Integer, default=500)
    has_cold_storage = Column(Boolean, default=False)
    verification_status = Column(String(40), default="VERIFIED")
    rating = Column(Float, default=4.8)

    redistributions = relationship("RedistributionRequest", back_populates="claimed_by_ngo")


class RedistributionRequest(Base):
    __tablename__ = "redistribution_requests"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    claimed_by_ngo_id = Column(Integer, ForeignKey("ngo_partners.id"), nullable=True)
    quantity_kg = Column(Float, nullable=False)
    estimated_meals = Column(Integer, nullable=False)
    available_from = Column(DateTime, default=utc_now)
    expires_at = Column(DateTime, nullable=False)
    safe_temp_celsius = Column(Float, default=65.0)  # Hot holding or cold holding
    status = Column(String(40), default="POSTED")  # POSTED, MATCHED, ASSIGNED_TO_ROUTE, PICKED_UP, DELIVERED, CANCELLED
    created_at = Column(DateTime, default=utc_now, index=True)

    kitchen = relationship("Kitchen", back_populates="redistribution_requests")
    food_item = relationship("FoodItem")
    claimed_by_ngo = relationship("NGOPartner", back_populates="redistributions")
    deliveries = relationship("Delivery", back_populates="request")


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    route_code = Column(String(40), unique=True, index=True, nullable=False)
    vehicle_id = Column(String(40), nullable=False)
    driver_name = Column(String(100), nullable=False)
    driver_phone = Column(String(30), nullable=False)
    total_distance_km = Column(Float, default=0.0)
    estimated_duration_min = Column(Integer, default=0)
    waypoints_geojson = Column(Text, nullable=True)
    status = Column(String(40), default="PLANNED")  # PLANNED, IN_TRANSIT, COMPLETED, ABORTED
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    deliveries = relationship("Delivery", back_populates="route")


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    request_id = Column(Integer, ForeignKey("redistribution_requests.id"), nullable=False)
    stop_sequence = Column(Integer, default=1)
    pickup_time = Column(DateTime, nullable=True)
    delivered_time = Column(DateTime, nullable=True)
    proof_of_delivery_image = Column(String(300), nullable=True)
    temperature_at_delivery = Column(Float, nullable=True)
    recipient_sign_name = Column(String(100), nullable=True)
    status = Column(String(40), default="PENDING")  # PENDING, COLLECTED, DELIVERED, REJECTED

    route = relationship("Route", back_populates="deliveries")
    request = relationship("RedistributionRequest", back_populates="deliveries")


class SustainabilityMetric(Base):
    __tablename__ = "sustainability_metrics"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    food_rescued_kg = Column(Float, default=0.0)
    co2_avoided_kg = Column(Float, default=0.0)
    water_saved_liters = Column(Float, default=0.0)
    land_use_prevented_sqm = Column(Float, default=0.0)
    cost_savings_inr = Column(Float, default=0.0)
    meals_served_to_needy = Column(Integer, default=0)

    organization = relationship("Organization", back_populates="sustainability_metrics")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=True)
    alert_type = Column(String(60), nullable=False)  # CRITICAL_STORAGE_BREACH, SURPLUS_SPOILED_RISK, MACHINE_FAILURE_IMMINENT, LOGISTICS_DELAY
    severity = Column(String(30), default="WARNING")  # INFO, WARNING, CRITICAL
    message = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    kitchen = relationship("Kitchen", back_populates="alerts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(80), nullable=False)
    entity_name = Column(String(60), nullable=False)
    entity_id = Column(String(60), nullable=False)
    payload_diff = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=utc_now, index=True)
