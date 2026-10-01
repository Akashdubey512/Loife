import axios from 'axios';
import { 
  ExecutiveStats, DemandItem, InventoryItem, QualityScanResult, 
  SurplusItem, NGOMatch, DeliveryRoute, SustainabilitySummary,
  DeliveryItem, EsgAuditReport, AuthUser
} from '../types';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30s for ML inference endpoints
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
    const res = await apiClient.get('/kitchens/');
    return res.data;
  },

  getFoodItems: async (): Promise<any[]> => {
    const res = await apiClient.get('/inventory/food-items');
    return res.data;
  },

  getExpiringBatches: async (kitchenId: number = 1): Promise<any[]> => {
    const res = await apiClient.get(`/inventory/batches/expiring?kitchen_id=${kitchenId}`);
    return res.data;
  },

  // Executive stats
  getExecutiveStats: async (): Promise<ExecutiveStats> => {
    const res = await apiClient.get('/analytics/executive-stats');
    return res.data;
  },

  getMonthlyTrends: async () => {
    const res = await apiClient.get('/analytics/monthly-trend');
    return res.data;
  },

  // Kitchen demand forecast
  getDemandForecast: async (kitchenId: number = 1): Promise<DemandItem[]> => {
    const res = await apiClient.get(`/demand/forecast?kitchen_id=${kitchenId}`);
    return res.data.predictions ?? res.data;
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
    const res = await apiClient.get(`/waste/predictions?kitchen_id=${kitchenId}`);
    return res.data;
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
    const res = await apiClient.get(`/inventory/?kitchen_id=${kitchenId}`);
    return res.data;
  },

  createInventoryBatch: async (payload: {
    kitchen_id: number;
    food_item_id: number;
    quantity_kg: number;
    expiry_date: string;
    batch_number?: string;
  }): Promise<any> => {
    const res = await apiClient.post('/inventory/batches', payload);
    return res.data;
  },

  // Quality scan & multi-factor verification
  scanFoodImage: async (formData: FormData): Promise<QualityScanResult> => {
    const res = await apiClient.post('/quality/scan', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000, // CV inference may take longer
    });
    return res.data;
  },

  getQualityScans: async (limit: number = 15): Promise<any[]> => {
    const res = await apiClient.get(`/quality/scans?limit=${limit}`);
    return res.data;
  },

  verifyQualityScan: async (
    scanId: number,
    payload: {
      inspector_notes: string;
      verdict?: string;
      final_disposition?: string;
      override_model_decision?: boolean;
    }
  ): Promise<any> => {
    // Backend expects 'verdict' field; map final_disposition -> verdict for compatibility
    const body = {
      verdict: payload.verdict || (payload.final_disposition === 'SAFE_FOR_REDISTRIBUTION'
        ? 'APPROVED_FOR_REDISTRIBUTION'
        : payload.final_disposition === 'COMPOST_ONLY'
        ? 'DOWNGRADE_TO_COMPOST'
        : 'APPROVED_FOR_REDISTRIBUTION'),
      inspector_notes: payload.inspector_notes,
      override_model_decision: payload.override_model_decision ?? false,
    };
    const res = await apiClient.post(`/quality/scans/${scanId}/verify`, body);
    return res.data;
  },

  // Redistribution
  getSurplusList: async (): Promise<SurplusItem[]> => {
    const res = await apiClient.get('/redistribution/surplus');
    return res.data;
  },

  createSurplus: async (payload: {
    kitchen_id: number;
    food_item_id: number;
    quantity_kg: number;
    expires_at: string;
    safe_temp_celsius?: number;
  }): Promise<any> => {
    const res = await apiClient.post('/redistribution/surplus', payload);
    return res.data;
  },

  matchNGOs: async (requestId: number): Promise<NGOMatch[]> => {
    const res = await apiClient.post(`/redistribution/match/${requestId}`);
    return res.data.recommended_matches ?? res.data;
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
    const res = await apiClient.get('/logistics/routes');
    return res.data;
  },

  optimizeRoutes: async (payload?: { kitchen_id?: number; request_ids?: number[]; selected_requests?: number[]; vehicle_capacity_kg?: number }): Promise<DeliveryRoute> => {
    const body = {
      kitchen_id: payload?.kitchen_id || 1,
      selected_requests: payload?.selected_requests || payload?.request_ids || [],
      vehicle_capacity_kg: payload?.vehicle_capacity_kg || 600.0
    };
    const res = await apiClient.post('/logistics/routes/optimize', body);
    return res.data;
  },

  advanceRouteStatus: async (routeId: number, nextStatus?: string): Promise<DeliveryRoute> => {
    // Backend auto-advances: PLANNED->IN_TRANSIT->COMPLETED, no next_status param needed
    const res = await apiClient.post(`/logistics/routes/${routeId}/advance`);
    return res.data;
  },

  getDeliveries: async (): Promise<DeliveryItem[]> => {
    const res = await apiClient.get('/logistics/deliveries');
    return res.data;
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
      recipient_sign_name: payload.recipient_sign_name || 'Authorized NGO Hub In-Charge',
      verification_otp: payload.verification_otp,
      temperature_at_delivery: payload.food_temp_celsius ?? 4.0,
      proof_of_delivery_image: payload.proof_of_delivery_url || '/uploads/pod/sig_confirmed.png'
    };
    const res = await apiClient.post(`/logistics/deliveries/${deliveryId}/confirm`, body);
    return res.data;
  },

  // Sustainability & ESG Reporting
  getSustainabilitySummary: async (): Promise<SustainabilitySummary> => {
    const res = await apiClient.get('/sustainability/summary');
    return res.data;
  },

  getEsgAuditReport: async (organizationId: number = 1, period: string = 'FY 2026-Q1'): Promise<EsgAuditReport> => {
    const res = await apiClient.get(`/sustainability/audit-report?organization_id=${organizationId}&reporting_period=${encodeURIComponent(period)}`);
    return res.data;
  },

  // ML Status
  getMlStatus: async (): Promise<any> => {
    const res = await apiClient.get('/ml/status');
    return res.data;
  },

  // Energy Prediction
  predictEnergy: async (payload: {
    kitchen_id: number;
    appliance_type?: string;
    date?: string;
    hour?: number;
    temperature_celsius?: number;
  }): Promise<any> => {
    const res = await apiClient.post('/energy/predict', payload);
    return res.data;
  },

  getEnergyHistory: async (kitchenId: number = 1): Promise<any[]> => {
    const res = await apiClient.get(`/energy/history?kitchen_id=${kitchenId}`);
    return res.data;
  },

  // Predictive Maintenance
  evaluateMaintenance: async (payload: {
    equipment_id: number;
    kitchen_id?: number;
    sensor_readings?: Record<string, number>;
  }): Promise<any> => {
    const res = await apiClient.post('/maintenance/evaluate', payload);
    return res.data;
  },

  getMaintenanceAlerts: async (kitchenId?: number): Promise<any[]> => {
    const url = kitchenId ? `/maintenance/alerts?kitchen_id=${kitchenId}` : '/maintenance/alerts';
    const res = await apiClient.get(url);
    return res.data;
  },

  // E-Nose / Beef Quality Sensor
  evaluateEnose: async (payload: {
    sensor_id?: string;
    readings: Record<string, number>;
    sample_label?: string;
  }): Promise<any> => {
    const res = await apiClient.post('/sensors/enose/evaluate', payload);
    return res.data;
  },

  // Admin / Users
  listUsers: async (): Promise<any[]> => {
    const res = await apiClient.get('/users/');
    return res.data;
  },

  // Organizations
  listOrganizations: async (): Promise<any[]> => {
    const res = await apiClient.get('/organizations/');
    return res.data;
  },
};
