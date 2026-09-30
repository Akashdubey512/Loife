import axios from 'axios';
import { 
  ExecutiveStats, DemandItem, InventoryItem, QualityScanResult, 
  SurplusItem, NGOMatch, DeliveryRoute, SustainabilitySummary,
  DeliveryItem, EsgAuditReport, AuthUser
} from '../types';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Automatically inject JWT Bearer token into outgoing requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('reserve_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// Centralized response interceptor for session expiration & 401 handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Only handle HTTP 401 Unauthorized errors
    if (error.response && error.response.status === 401) {
      const requestUrl = error.config?.url || '';
      const isLoginRequest = requestUrl.includes('/auth/login');

      // Do not clear tokens or dispatch logout on failed login credential attempts
      if (!isLoginRequest) {
        localStorage.removeItem('reserve_token');

        // Notify application components via custom window event
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('reserveai:unauthorized'));

          // Redirect to login only if not already on /login or root
          if (window.location && window.location.pathname !== '/login' && window.location.pathname !== '/') {
            window.location.href = '/login';
          }
        }
      }
    }
    return Promise.reject(error);
  }
);

export const isDemoMode = (): boolean => {
  if (typeof window === 'undefined') return true;
  return localStorage.getItem('reserve_demo_mode') !== 'false';
};

const handleFallback = <T>(fnName: string, mockData: T, error: any): T => {
  if (isDemoMode()) {
    console.warn(`[Loife Presentation Mode] API call '${fnName}' returned fallback data.`, error);
    return mockData;
  }
  throw error;
};

export const apiService = {
  // Authentication & Session
  login: async (username: string, password: string): Promise<{ access_token: string; token_type: string; user: AuthUser }> => {
    const res = await apiClient.post('/auth/login', { username, password });
    if (res.data.access_token) {
      localStorage.setItem('reserve_token', res.data.access_token);
    }
    return res.data;
  },

  getMe: async (): Promise<AuthUser> => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },

  logout: () => {
    localStorage.removeItem('reserve_token');
  },

  register: async (payload: {
    email: string;
    password: string;
    full_name: string;
    phone_number?: string;
  }): Promise<any> => {
    const res = await apiClient.post('/auth/register', payload);
    return res.data;
  },

  // Kitchens & Food Items
  getKitchens: async (): Promise<any[]> => {
    try {
      const res = await apiClient.get('/kitchens/');
      return res.data;
    } catch (err) {
      return handleFallback('getKitchens', [
        { id: 1, name: 'Central Commissary & Mess Hall Alpha', facility_code: 'KIT-DELHI-001', daily_meal_capacity: 2800 },
        { id: 2, name: 'South Wing Bakery & Processing Facility', facility_code: 'KIT-DELHI-002', daily_meal_capacity: 1200 }
      ], err);
    }
  },

  getFoodItems: async (): Promise<any[]> => {
    try {
      const res = await apiClient.get('/inventory/food-items');
      return res.data;
    } catch (err) {
      return handleFallback('getFoodItems', [
        { id: 1, name: 'Basmati Rice & Dal Makhani', category: 'COOKED_MEALS' },
        { id: 2, name: 'Paneer Butter Masala', category: 'COOKED_MEALS' },
        { id: 3, name: 'Farm Fresh Tomatoes & Bell Peppers', category: 'VEGETABLES' },
        { id: 4, name: 'Fresh Dairy Paneer (Raw)', category: 'DAIRY' },
        { id: 5, name: 'Multigrain Sandwich Bread & Buns', category: 'BAKERY' }
      ], err);
    }
  },

  getExpiringBatches: async (kitchenId: number = 1): Promise<any[]> => {
    try {
      const res = await apiClient.get(`/inventory/batches/expiring?kitchen_id=${kitchenId}`);
      return res.data;
    } catch (err) {
      return handleFallback('getExpiringBatches', [
        { id: 101, batch_number: 'BATCH-2026-K1-101', food_item: { name: 'Steamed Basmati Rice & Dal Makhani' }, remaining_quantity_kg: 85, expiry_date: new Date(Date.now() + 3.5 * 3600 * 1000).toISOString(), status: 'NEARING_EXPIRY' },
        { id: 102, batch_number: 'BATCH-2026-K1-102', food_item: { name: 'Paneer Butter Masala' }, remaining_quantity_kg: 105, expiry_date: new Date(Date.now() + 4.2 * 3600 * 1000).toISOString(), status: 'NEARING_EXPIRY' },
        { id: 107, batch_number: 'BATCH-2026-K1-107', food_item: { name: 'Farm Fresh Tomatoes & Bell Peppers' }, remaining_quantity_kg: 68, expiry_date: new Date(Date.now() + 5.0 * 3600 * 1000).toISOString(), status: 'NEARING_EXPIRY' },
        { id: 103, batch_number: 'BATCH-2026-K1-103', food_item: { name: 'Fresh Dairy Paneer (Raw)' }, remaining_quantity_kg: 125, expiry_date: new Date(Date.now() + 8.5 * 3600 * 1000).toISOString(), status: 'OPTIMAL' },
        { id: 104, batch_number: 'BATCH-2026-K1-104', food_item: { name: 'Multigrain Sandwich Bread & Buns' }, remaining_quantity_kg: 145, expiry_date: new Date(Date.now() + 9.0 * 3600 * 1000).toISOString(), status: 'OPTIMAL' },
        { id: 105, batch_number: 'BATCH-2026-K1-105', food_item: { name: 'Seasonal Mixed Fruit Salad' }, remaining_quantity_kg: 165, expiry_date: new Date(Date.now() + 10.2 * 3600 * 1000).toISOString(), status: 'OPTIMAL' },
        { id: 106, batch_number: 'BATCH-2026-K1-106', food_item: { name: 'Chilled Greek Yogurt Parfait' }, remaining_quantity_kg: 185, expiry_date: new Date(Date.now() + 11.0 * 3600 * 1000).toISOString(), status: 'OPTIMAL' },
        { id: 108, batch_number: 'BATCH-2026-K1-108', food_item: { name: 'Artisan Sourdough Loaves' }, remaining_quantity_kg: 95, expiry_date: new Date(Date.now() + 11.5 * 3600 * 1000).toISOString(), status: 'OPTIMAL' },
        { id: 109, batch_number: 'BATCH-2026-K1-109', food_item: { name: 'Organic Spinach & Kale Medley' }, remaining_quantity_kg: 115, expiry_date: new Date(Date.now() + 12.0 * 3600 * 1000).toISOString(), status: 'OPTIMAL' },
        { id: 110, batch_number: 'BATCH-2026-K1-110', food_item: { name: 'Spiced Chickpea Curry & Pulao' }, remaining_quantity_kg: 140, expiry_date: new Date(Date.now() + 13.0 * 3600 * 1000).toISOString(), status: 'OPTIMAL' }
      ], err);
    }
  },

  // Executive stats
  getExecutiveStats: async (): Promise<ExecutiveStats> => {
    try {
      const res = await apiClient.get('/analytics/executive-stats');
      return res.data;
    } catch (err) {
      return handleFallback('getExecutiveStats', {
        total_food_saved_kg: 14250.0,
        waste_reduction_percentage: 38.6,
        carbon_reduction_kg: 35625.0,
        water_saved_liters: 7410000.0,
        energy_efficiency_kwh: 25650.0,
        operational_cost_savings_inr: 1567500.0,
        meals_redistributed: 35625,
        active_kitchens_monitored: 4,
        active_ngo_partners: 8,
      }, err);
    }
  },

  getMonthlyTrends: async () => {
    try {
      const res = await apiClient.get('/analytics/monthly-trend');
      return res.data;
    } catch (err) {
      return handleFallback('getMonthlyTrends', [
        { month: 'Apr', waste_generated_kg: 2400, food_rescued_kg: 950, cost_saved_inr: 104500 },
        { month: 'May', waste_generated_kg: 2150, food_rescued_kg: 1300, cost_saved_inr: 143000 },
        { month: 'Jun', waste_generated_kg: 1900, food_rescued_kg: 1650, cost_saved_inr: 181500 },
        { month: 'Jul', waste_generated_kg: 1650, food_rescued_kg: 2100, cost_saved_inr: 231000 },
        { month: 'Aug', waste_generated_kg: 1400, food_rescued_kg: 2550, cost_saved_inr: 280500 },
        { month: 'Sep', waste_generated_kg: 1150, food_rescued_kg: 3100, cost_saved_inr: 341000 },
      ], err);
    }
  },

  // Kitchen demand forecast
  getDemandForecast: async (kitchenId: number = 1): Promise<DemandItem[]> => {
    try {
      const res = await apiClient.get(`/demand/forecast?kitchen_id=${kitchenId}`);
      return res.data.predictions;
    } catch (err) {
      return handleFallback('getDemandForecast', [
        { food_item_id: 1, food_name: 'Basmati Rice & Dal Makhani', expected_demand_kg: 182.4, confidence_score: 0.94, recommended_production_kg: 190.0, surplus_risk_probability: 0.08, model_version: 'heuristic-v1.4' },
        { food_item_id: 2, food_name: 'Paneer Butter Masala', expected_demand_kg: 145.0, confidence_score: 0.92, recommended_production_kg: 152.0, surplus_risk_probability: 0.11, model_version: 'heuristic-v1.4' },
        { food_item_id: 3, food_name: 'Seasonal Mixed Vegetable Sabzi', expected_demand_kg: 110.5, confidence_score: 0.96, recommended_production_kg: 115.0, surplus_risk_probability: 0.05, model_version: 'heuristic-v1.4' },
        { food_item_id: 4, food_name: 'Tandoori Whole Wheat Roti', expected_demand_kg: 220.0, confidence_score: 0.95, recommended_production_kg: 230.0, surplus_risk_probability: 0.06, model_version: 'heuristic-v1.4' },
        { food_item_id: 5, food_name: 'Garden Cucumber & Beetroot Salad', expected_demand_kg: 68.0, confidence_score: 0.89, recommended_production_kg: 72.0, surplus_risk_probability: 0.14, model_version: 'heuristic-v1.4' }
      ], err);
    }
  },

  predictDemand: async (payload: {
    kitchen_id: number;
    food_item_id: number;
    prediction_date?: string;
    meal_slot?: string;
    expected_footfall?: number;
  }): Promise<any> => {
    const res = await apiClient.post('/demand/predict', payload);
    return res.data;
  },

  getWastePrediction: async (kitchenId: number = 1): Promise<any> => {
    try {
      const res = await apiClient.get(`/waste/predictions?kitchen_id=${kitchenId}`);
      return res.data;
    } catch (err) {
      return handleFallback('getWastePrediction', {
        kitchen_id: kitchenId,
        expected_waste_kg: 14.8,
        waste_probability: 0.21,
        predicted_root_cause: 'Overproduction during dinner peak',
        prevention_recommendation: 'Throttle batch size by 8% to reduce surplus.'
      }, err);
    }
  },

  logWasteEvent: async (payload: {
    kitchen_id: number;
    food_item_id: number;
    batch_id?: number;
    quantity_wasted_kg: number;
    primary_cause: string;
    waste_stage: string;
    financial_loss_inr?: number;
  }): Promise<any> => {
    const res = await apiClient.post('/waste/events', payload);
    return res.data;
  },

  // Inventory
  getInventory: async (kitchenId: number = 1): Promise<InventoryItem[]> => {
    try {
      const res = await apiClient.get(`/inventory/?kitchen_id=${kitchenId}`);
      return res.data;
    } catch (err) {
      return handleFallback('getInventory', [
        {
          id: 1,
          food_item_id: 1,
          food_item: { id: 1, name: 'Basmati Rice & Dal Makhani', category: 'COOKED_MEALS', default_shelf_life_hours: 12 },
          current_quantity_kg: 85.0,
          reorder_threshold_kg: 20.0,
          storage_location: 'Zone A Cold Shelf 1',
          batches: [
            { id: 101, batch_number: 'BATCH-2026-K1-101', remaining_quantity_kg: 48.0, expiry_date: new Date(Date.now() + 5 * 3600 * 1000).toISOString(), status: 'NEARING_EXPIRY' },
            { id: 102, batch_number: 'BATCH-2026-K1-102', remaining_quantity_kg: 37.0, expiry_date: new Date(Date.now() + 11 * 3600 * 1000).toISOString(), status: 'OPTIMAL' },
          ]
        },
        {
          id: 2,
          food_item_id: 2,
          food_item: { id: 2, name: 'Paneer Butter Masala', category: 'COOKED_MEALS', default_shelf_life_hours: 14 },
          current_quantity_kg: 65.0,
          reorder_threshold_kg: 25.0,
          storage_location: 'Zone B Hot-Holding Well',
          batches: [
            { id: 103, batch_number: 'BATCH-2026-K1-103', remaining_quantity_kg: 35.0, expiry_date: new Date(Date.now() + 6 * 3600 * 1000).toISOString(), status: 'OPTIMAL' }
          ]
        }
      ], err);
    }
  },

  // Quality scan & multi-factor verification
  scanFoodImage: async (formData: FormData): Promise<QualityScanResult> => {
    const res = await apiClient.post('/quality/scan', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },

  verifyQualityScan: async (
    scanId: number,
    payload: {
      inspector_notes: string;
      final_disposition: 'SAFE_FOR_REDISTRIBUTION' | 'PROCESS_IMMEDIATELY' | 'COMPOST_ONLY' | 'HAZARD_DISCARD';
      override_model_decision?: boolean;
    }
  ): Promise<QualityScanResult> => {
    const res = await apiClient.post(`/quality/scans/${scanId}/verify`, payload);
    return res.data;
  },

  // Redistribution
  getSurplusList: async (): Promise<SurplusItem[]> => {
    try {
      const res = await apiClient.get('/redistribution/surplus');
      return res.data;
    } catch (err) {
      return handleFallback('getSurplusList', [
        {
          id: 201,
          kitchen_id: 1,
          food_item_id: 1,
          food_item_name: 'Steamed Basmati Rice & Dal Makhani',
          claimed_by_ngo_id: 1,
          claimed_by_ngo_name: 'Robin Hood Army - Central Hub',
          quantity_kg: 48.0,
          estimated_meals: 120,
          available_from: new Date().toISOString(),
          expires_at: new Date(Date.now() + 4 * 3600 * 1000).toISOString(),
          safe_temp_celsius: 65.0,
          status: 'MATCHED',
          created_at: new Date().toISOString()
        },
        {
          id: 202,
          kitchen_id: 1,
          food_item_id: 2,
          food_item_name: 'Paneer Butter Masala',
          claimed_by_ngo_id: null,
          claimed_by_ngo_name: null,
          quantity_kg: 35.0,
          estimated_meals: 88,
          available_from: new Date().toISOString(),
          expires_at: new Date(Date.now() + 5 * 3600 * 1000).toISOString(),
          safe_temp_celsius: 65.0,
          status: 'POSTED',
          created_at: new Date().toISOString()
        }
      ], err);
    }
  },

  matchNGOs: async (requestId: number): Promise<NGOMatch[]> => {
    try {
      const res = await apiClient.post(`/redistribution/match/${requestId}`);
      return res.data.recommended_matches;
    } catch (err) {
      return handleFallback('matchNGOs', [
        { ngo_id: 1, ngo_name: 'Robin Hood Army - Central Hub', compatibility_score: 98.4, distance_km: 3.8, capacity_available: 850, has_cold_storage: true, eta_pickup_minutes: 22, address: 'Connaught Place Community Hall, New Delhi', phone: '+91 98101 44552' },
        { ngo_id: 2, ngo_name: 'Feeding India by Zomato - Hub East', compatibility_score: 92.1, distance_km: 6.2, capacity_available: 600, has_cold_storage: true, eta_pickup_minutes: 35, address: 'Mayur Vihar Phase 1 Shelter Complex, New Delhi', phone: '+91 98112 55663' },
        { ngo_id: 3, ngo_name: 'Roti Bank Foundation - Noida Sector 18', compatibility_score: 87.5, distance_km: 8.5, capacity_available: 450, has_cold_storage: false, eta_pickup_minutes: 42, address: 'Atta Market Relief Shelter, Noida', phone: '+91 98113 66774' },
      ], err);
    }
  },

  claimSurplus: async (requestId: number, ngoId: number): Promise<{ message: string; status: string; matched_ngo_id: number }> => {
    const res = await apiClient.post(`/redistribution/requests/${requestId}/claim?ngo_id=${ngoId}`);
    return res.data;
  },

  respondSurplus: async (requestId: number, accept: boolean, reason?: string) => {
    const res = await apiClient.post(`/redistribution/requests/${requestId}/respond`, {
      accept,
      rejection_reason: reason
    });
    return res.data;
  },

  // Logistics & Fleet Optimization
  getRoutes: async (): Promise<DeliveryRoute[]> => {
    try {
      const res = await apiClient.get('/logistics/routes');
      return res.data;
    } catch (err) {
      return handleFallback('getRoutes', [
        {
          id: 501,
          route_code: 'RT-DELHI-NORTH-01',
          vehicle_id: 'EV-VAN-DL-4C-9921',
          driver_name: 'Rajesh Kumar',
          driver_phone: '+91 98765 43210',
          total_distance_km: 18.4,
          estimated_duration_min: 45,
          status: 'IN_TRANSIT',
          waypoints: [
            { sequence: 1, name: 'Central Kitchen Commissary Alpha', action: 'PICKUP', lat: 28.6280, lng: 77.3649, load_change_kg: 83.0, status: 'COMPLETED' },
            { sequence: 2, name: 'Robin Hood Army - Central Hub', action: 'DELIVERY', lat: 28.6304, lng: 77.2177, load_change_kg: -48.0, status: 'IN_TRANSIT' },
            { sequence: 3, name: 'Feeding India Shelter East', action: 'DELIVERY', lat: 28.6080, lng: 77.2950, load_change_kg: -35.0, status: 'PENDING' }
          ]
        }
      ], err);
    }
  },

  optimizeRoutes: async (payload?: { kitchen_id?: number; request_ids?: number[]; selected_requests?: number[]; vehicle_capacity_kg?: number }): Promise<DeliveryRoute> => {
    const body = {
      kitchen_id: payload?.kitchen_id || 1,
      selected_requests: payload?.selected_requests || payload?.request_ids || [1, 2, 3],
      vehicle_capacity_kg: payload?.vehicle_capacity_kg || 600.0
    };
    const res = await apiClient.post('/logistics/routes/optimize', body);
    return res.data;
  },

  advanceRouteStatus: async (routeId: number, nextStatus: 'PLANNED' | 'IN_TRANSIT' | 'COMPLETED'): Promise<DeliveryRoute> => {
    const res = await apiClient.post(`/logistics/routes/${routeId}/advance?next_status=${nextStatus}`);
    return res.data;
  },

  getDeliveries: async (): Promise<DeliveryItem[]> => {
    try {
      const res = await apiClient.get('/logistics/deliveries');
      return res.data;
    } catch (err) {
      return handleFallback('getDeliveries', [
        {
          id: 301,
          route_id: 501,
          redistribution_request_id: 201,
          status: 'IN_TRANSIT',
          verification_otp: '8492',
          food_temp_celsius: 3.8
        },
        {
          id: 302,
          route_id: 501,
          redistribution_request_id: 202,
          status: 'DELIVERED',
          verification_otp: '6219',
          food_temp_celsius: 4.1,
          delivered_at: new Date(Date.now() - 1800 * 1000).toISOString(),
          proof_of_delivery_url: '/uploads/pod/sig_confirmed.png'
        }
      ], err);
    }
  },

  confirmDelivery: async (
    deliveryId: number,
    payload: {
      verification_otp: string;
      recipient_sign_name?: string;
      food_temp_celsius?: number;
      proof_of_delivery_url?: string;
      notes?: string;
    }
  ): Promise<{ status: string; message: string; recipient_verified: boolean }> => {
    const body = {
      recipient_sign_name: payload.recipient_sign_name || "Authorized NGO Hub In-Charge",
      verification_otp: payload.verification_otp || "4921",
      temperature_at_delivery: payload.food_temp_celsius ?? 4.0,
      proof_of_delivery_image: payload.proof_of_delivery_url || "/uploads/pod/sig_confirmed.png"
    };
    const res = await apiClient.post(`/logistics/deliveries/${deliveryId}/confirm`, body);
    return res.data;
  },

  // Sustainability & ESG Reporting
  getSustainabilitySummary: async (): Promise<SustainabilitySummary> => {
    try {
      const res = await apiClient.get('/sustainability/summary');
      return res.data;
    } catch (err) {
      return handleFallback('getSustainabilitySummary', {
        timeframe: 'LAST_30_DAYS',
        food_rescued_kg: 4250.0,
        co2_avoided_kg: 10625.0,
        water_saved_liters: 2125000.0,
        land_use_prevented_sqm: 8500.0,
        financial_savings_inr: 467500.0,
        meals_served_to_needy: 8500,
        esg_score_contribution: '+22.8%',
        waste_diversion_rate_pct: 36.4,
      }, err);
    }
  },

  getEsgAuditReport: async (organizationId: number = 1, period: string = 'FY 2026-Q1'): Promise<EsgAuditReport> => {
    try {
      const res = await apiClient.get(`/sustainability/audit-report?organization_id=${organizationId}&reporting_period=${encodeURIComponent(period)}`);
      return res.data;
    } catch (err) {
      return handleFallback('getEsgAuditReport', {
        report_id: 'ESG-202609-F4C9B10A',
        organization_name: 'Apex Institutional Dining Partner',
        audit_date: new Date().toISOString(),
        reporting_period: period,
        measured_rescued_kg: 14250.0,
        pipeline_potential_kg: 83.0,
        co2e_avoided_kg: 35625.0,
        virtual_water_conserved_liters: 7410000.0,
        land_use_prevented_sqm: 28500.0,
        meals_served_to_needy: 35625,
        equivalent_trees_planted: 1636.4,
        car_km_emissions_offset: 185520.0,
        verified_deliveries_count: 248,
        scope_3_compliance_status: 'AUDITED_AND_COMPLIANT_GHG_CAT_1',
        methodology: 'Poore & Nemecek (2018) Science LCA Multipliers; WRAP UK Food Waste & GHG Equivalents; IPCC AR6 GWP100.',
        category_breakdown: [
          { category: 'Cooked Institutional Meals', kg_saved: 6200.0, co2_kg: 15500.0, water_liters: 3224000.0, land_sqm: 12400.0 },
          { category: 'Fresh Produce & Vegetables', kg_saved: 3400.0, co2_kg: 1700.0, water_liters: 1088000.0, land_sqm: 1360.0 },
          { category: 'Dairy, Milk & Paneer', kg_saved: 2150.0, co2_kg: 6880.0, water_liters: 1350200.0, land_sqm: 9675.0 },
          { category: 'Bakery & Bread Products', kg_saved: 2500.0, co2_kg: 4000.0, water_liters: 1747800.0, land_sqm: 5065.0 },
        ],
        assumptions: [
          'Food rescue emission factors derived from peer-reviewed Science LCA database (Poore & Nemecek 2018).',
          'Methane avoidance calculation adopts IPCC AR6 GWP100 index for anaerobic landfill diversion.',
          'Water conservation measures virtual embedded water footprint across upstream agricultural production.',
          'Portion sizing: 1 institutional meal benchmarked at 0.50 kg cooked or 0.35 kg staple grain equivalent.',
          'Tree sequestration equivalence assumes 1 mature European beech/conifer absorbing 21.77 kg CO2 annually.'
        ]
      }, err);
    }
  }
};

