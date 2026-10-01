export type DashboardTab = 
  | 'executive'
  | 'kitchen'
  | 'quality'
  | 'redistribution'
  | 'logistics'
  | 'sustainability'
  | 'ml_status';

export interface ExecutiveStats {
  total_food_saved_kg: number;
  waste_reduction_percentage: number;
  carbon_reduction_kg: number;
  water_saved_liters: number;
  energy_efficiency_kwh: number;
  operational_cost_savings_inr: number;
  meals_redistributed: number;
  active_kitchens_monitored: number;
  active_ngo_partners: number;
}

export interface DemandItem {
  food_item_id: number;
  food_name: string;
  expected_demand_kg: number;
  confidence_score: number;
  recommended_production_kg: number;
  surplus_risk_probability: number;
  model_version: string;
}

export interface InventoryItem {
  id: number;
  food_item_id: number;
  food_item: {
    id: number;
    name: string;
    category: string;
    default_shelf_life_hours: number;
  };
  current_quantity_kg: number;
  reorder_threshold_kg: number;
  storage_location: string;
  batches: Array<{
    id: number;
    batch_number: string;
    remaining_quantity_kg: number;
    expiry_date: string;
    status: string;
  }>;
}

export interface QualityScanResult {
  id: number;
  food_item_id: number;
  food_name: string;
  image_url: string;
  freshness_score: number;
  freshness_level: 'FRESH' | 'MODERATE' | 'DEGRADING' | 'ROTTEN';
  remaining_shelf_life_days: number;
  redistribution_status: 'SAFE_FOR_REDISTRIBUTION' | 'PROCESS_IMMEDIATELY' | 'COMPOST_ONLY' | 'HAZARD_DISCARD';
  confidence: number;
  inspected_at: string;
  defects_detected: string[];
  sensor_safety_cleared?: boolean;
  human_verified?: boolean;
  food_safety_verdict?: string;
  inspector_name?: string;
  // Truthfulness fields from backend
  simulated?: boolean;
  simulation_notice?: string | null;
}

export interface MLEngineStatus {
  engine: string;
  model_type?: string;
  model_version?: string;
  trained?: boolean;
  simulated?: boolean;
  status?: string;
  reason?: string;
  scope?: string;
  endpoint?: string;
  error?: string;
  product_count?: number;
  benchmark?: string;
  average_gap_pct?: number;
}

export interface MLStatusResponse {
  platform: string;
  ml_status: string;
  trained_models: number;
  active_engines: number;
  total_engines: number;
  engines: MLEngineStatus[];
}

export interface SurplusItem {
  id: number;
  kitchen_id: number;
  food_item_id: number;
  food_item_name: string;
  claimed_by_ngo_id?: number | null;
  claimed_by_ngo_name?: string | null;
  quantity_kg: number;
  estimated_meals: number;
  available_from: string;
  expires_at: string;
  safe_temp_celsius?: number;
  status: 'POSTED' | 'MATCHED' | 'ASSIGNED_TO_ROUTE' | 'PICKED_UP' | 'DELIVERED';
  created_at: string;
}

export interface NGOMatch {
  ngo_id: number;
  ngo_name: string;
  compatibility_score: number;
  distance_km: number;
  capacity_available: number;
  has_cold_storage: boolean;
  eta_pickup_minutes: number;
  address: string;
  phone: string;
}

export interface RouteWaypoint {
  sequence: number;
  name: string;
  action: 'PICKUP' | 'DELIVERY';
  lat: number;
  lng: number;
  load_change_kg: number;
  status: 'COMPLETED' | 'IN_TRANSIT' | 'PENDING';
}

export interface DeliveryRoute {
  id: number;
  route_code: string;
  vehicle_id: string;
  driver_name: string;
  driver_phone: string;
  total_distance_km: number;
  estimated_duration_min: number;
  waypoints: RouteWaypoint[];
  status: 'PLANNED' | 'IN_TRANSIT' | 'COMPLETED';
}

export interface DeliveryItem {
  id: number;
  redistribution_request_id: number;
  route_id?: number;
  status: 'SCHEDULED' | 'PICKED_UP' | 'IN_TRANSIT' | 'DELIVERED' | 'FAILED';
  verification_otp?: string;
  food_temp_celsius?: number;
  delivered_at?: string;
  proof_of_delivery_url?: string;
}

export interface SustainabilitySummary {
  timeframe: string;
  food_rescued_kg: number;
  co2_avoided_kg: number;
  water_saved_liters: number;
  land_use_prevented_sqm: number;
  financial_savings_inr: number;
  meals_served_to_needy: number;
  esg_score_contribution: string;
  waste_diversion_rate_pct: number;
  pipeline_potential_kg?: number;
  measured_verified_kg?: number;
}

export interface CategoryImpact {
  category: string;
  kg_saved: number;
  co2_kg: number;
  water_liters: number;
  land_sqm: number;
}

export interface EsgAuditReport {
  report_id: string;
  organization_name: string;
  audit_date: string;
  reporting_period: string;
  measured_rescued_kg: number;
  pipeline_potential_kg: number;
  co2e_avoided_kg: number;
  virtual_water_conserved_liters: number;
  land_use_prevented_sqm: number;
  meals_served_to_needy: number;
  equivalent_trees_planted: number;
  car_km_emissions_offset: number;
  verified_deliveries_count: number;
  scope_3_compliance_status: string;
  methodology: string;
  category_breakdown: CategoryImpact[];
  assumptions: string[];
}

export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  role: 'SUPER_ADMIN' | 'ORG_ADMIN' | 'KITCHEN_MANAGER' | 'QUALITY_INSPECTOR' | 'LOGISTICS_COORDINATOR' | 'NGO_REP' | 'NGO_COORDINATOR' | 'LOGISTICS_DRIVER' | 'ESG_AUDITOR' | string;
  organization_id?: number | null;
  phone_number?: string | null;
  is_active: boolean;
}

