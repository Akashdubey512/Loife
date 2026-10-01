import React, { useEffect, useState } from 'react';
import { 
  Truck, 
  MapPin, 
  ShieldCheck, 
  CheckCircle2,
  Navigation,
  KeyRound
} from 'lucide-react';
import { apiService } from '../services/api';
import { DeliveryRoute } from '../types';
import storyCommunityDining from '../assets/illustrations/community/story_community_dining.png';

export const LogisticsDashboard: React.FC = () => {
  const [activeRoute, setActiveRoute] = useState<DeliveryRoute | null>(null);
  const [optimizing, setOptimizing] = useState(false);
  const [advancing, setAdvancing] = useState(false);
  const [confirmingPod, setConfirmingPod] = useState(false);
  const [otpCode, setOtpCode] = useState('8492');
  const [deliveredFoodTemp, setDeliveredFoodTemp] = useState('3.8');
  const [podSuccessMessage, setPodSuccessMessage] = useState<string | null>(null);

  const fetchRoutes = async () => {
    const data = await apiService.getRoutes();
    if (data.length > 0) {
      setActiveRoute(data[0]);
    }
  };

  useEffect(() => {
    fetchRoutes();
  }, []);

  const handleOptimizeRoute = async () => {
    setOptimizing(true);
    setPodSuccessMessage(null);
    try {
      const optimized = await apiService.optimizeRoutes({ kitchen_id: 1, request_ids: [1, 2, 3] });
      setActiveRoute(optimized);
      setPodSuccessMessage(`Route optimised using greedy heuristic algorithm! Route Code: ${optimized.route_code}, Stops: ${optimized.waypoints?.length || 0}`);
    } catch {
      await fetchRoutes();
    } finally {
      setOptimizing(false);
    }
  };

  const handleAdvanceStatus = async () => {
    if (!activeRoute) return;
    setAdvancing(true);
    const nextStatus = activeRoute.status === 'PLANNED' ? 'IN_TRANSIT' : 'COMPLETED';
    try {
      const updated = await apiService.advanceRouteStatus(activeRoute.id, nextStatus);
      setActiveRoute(updated);
      setPodSuccessMessage(`Route status advanced to ${updated.status}. Vehicle in transit.`);
    } catch {
      setActiveRoute(prev => prev ? { ...prev, status: nextStatus } : null);
    } finally {
      setAdvancing(false);
    }
  };

  const handleConfirmDelivery = async () => {
    setConfirmingPod(true);
    setPodSuccessMessage(null);
    try {
      const deliveries = await apiService.getDeliveries();
      const targetDelivery = deliveries.find(d => (activeRoute ? d.route_id === activeRoute.id : true) && d.status !== 'DELIVERED') || deliveries[0];
      if (!targetDelivery) {
        setPodSuccessMessage('Error: No active delivery found for this route. Optimize a route first.');
        return;
      }
      const deliveryId = targetDelivery.id;

      const res = await apiService.confirmDelivery(deliveryId, {
        verification_otp: otpCode,
        recipient_sign_name: "Authorized NGO Hub In-Charge",
        food_temp_celsius: parseFloat(deliveredFoodTemp) || 4.0,
        notes: "Recipient inspected thermal seals and confirmed lot count."
      });
      setPodSuccessMessage(`Proof of Delivery verified for Delivery #${deliveryId}! OTP confirmed, cold-chain certified at ${deliveredFoodTemp}°C.`);
      await fetchRoutes();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const status = err?.response?.status;
      if (status === 400) {
        setPodSuccessMessage(`Error: ${typeof detail === 'string' ? detail : 'Invalid OTP or delivery data.'}`);
      } else if (status === 404) {
        setPodSuccessMessage('Error: Delivery record not found. Optimize a route first.');
      } else if (status === 401) {
        setPodSuccessMessage('Error: Session expired. Please log in again.');
      } else {
        setPodSuccessMessage(`Error: ${typeof detail === 'string' ? detail : 'Delivery confirmation failed. Check backend connection.'}`);
      }
    } finally {
      setConfirmingPod(false);
    }
  };


  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Smart Logistics & Fleet Route Optimization</h1>
          <p className="text-xs text-gray-400 mt-1">
            Multi-stop route planning using a greedy heuristic with temperature telemetry and OTP verification.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleOptimizeRoute}
            disabled={optimizing}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-gray-950 text-xs font-bold transition shadow-md shadow-emerald-500/20 disabled:opacity-50"
          >
            <Navigation className={`h-3.5 w-3.5 ${optimizing ? 'animate-spin' : ''}`} />
            <span>{optimizing ? 'Re-Routing...' : 'Re-Optimise Route'}</span>
          </button>
        </div>
      </div>

      {/* Loife Logistics Community Banner */}
      <div className="loife-surface-sage p-4 md:p-5 rounded-2xl border border-[#77B7A5]/30 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-lg">
        <div className="flex items-center gap-4">
          <div className="h-16 w-24 sm:h-20 sm:w-28 rounded-xl overflow-hidden shrink-0 border border-white/10 shadow-md">
            <img
              src={storyCommunityDining}
              alt="Community delivery destination"
              className="w-full h-full object-cover"
            />
          </div>
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#145B59]/40 border border-[#77B7A5]/30 text-[#77B7A5] text-[10px] font-bold uppercase tracking-wider mb-1">
              <Truck className="h-3 w-3 text-[#38BDF8]" /> Fleet Dispatch &amp; Care
            </div>
            <h2 className="text-base sm:text-lg font-bold text-white">
              Every delivery carries more than food.
            </h2>
            <p className="text-xs text-gray-300 max-w-xl mt-0.5 leading-relaxed">
              Optimized multi-stop routing connects surplus from campus dining directly with community dining centers, preserving cold-chain integrity and ensuring timely delivery.
            </p>
          </div>
        </div>
        <div className="shrink-0 text-right hidden lg:block">
          <span className="text-[10px] uppercase font-bold text-[#77B7A5] tracking-wider block">Real-time Handover</span>
          <span className="text-xs text-gray-400">Secure OTP &amp; Temp Log</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Cols: Interactive Map Simulation */}
        <div className="lg:col-span-7 glass-card p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-white">Live Route Telemetry & Waypoints</h2>
                <p className="text-xs text-gray-400">Route Code: <strong className="text-emerald-400 font-mono">{activeRoute?.route_code || 'RT-DELHI-NORTH-01'}</strong></p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-2.5 py-1 rounded bg-white/5 border border-white/10 text-cyan-400">
                  Cold Chain: 3.4°C
                </span>
                <button
                  onClick={handleAdvanceStatus}
                  disabled={advancing || activeRoute?.status === 'COMPLETED'}
                  className="px-2.5 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-bold text-gray-200 transition disabled:opacity-50"
                >
                  {advancing ? 'Updating...' : activeRoute?.status === 'PLANNED' ? 'Start Route' : activeRoute?.status === 'IN_TRANSIT' ? 'Mark Completed' : 'Completed'}
                </button>
              </div>
            </div>

            {/* Vector Simulated Map Visualizer */}
            <div className="relative w-full h-80 rounded-2xl bg-[#090d16] border border-white/10 overflow-hidden flex items-center justify-center p-4">
              <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f293720_1px,transparent_1px),linear-gradient(to_bottom,#1f293720_1px,transparent_1px)] bg-[size:32px_32px]"></div>

              <svg className="absolute inset-0 w-full h-full" viewBox="0 0 600 320" fill="none">
                <path
                  d="M 100 240 Q 220 180 320 130 T 500 80"
                  stroke="#10b981"
                  strokeWidth="3"
                  strokeDasharray="6 6"
                  className="animate-[dash_20s_linear_infinite]"
                />
                
                <circle cx="100" cy="240" r="8" fill="#10b981" />
                <circle cx="100" cy="240" r="14" stroke="#10b981" strokeWidth="2" opacity="0.4" />
                
                <circle cx="280" cy="150" r="7" fill="#06b6d4" />
                <circle cx="280" cy="150" r="16" stroke="#06b6d4" strokeWidth="2" opacity="0.5" className="animate-ping" />

                <circle cx="320" cy="130" r="8" fill="#f59e0b" />
                <circle cx="500" cy="80" r="8" fill="#8b5cf6" />
              </svg>

              <div className="absolute bottom-6 left-6 p-2.5 rounded-xl bg-gray-900/90 border border-white/10 text-xs">
                <div className="flex items-center gap-1.5 text-emerald-400 font-bold">
                  <MapPin className="h-3.5 w-3.5" /> Stop 1: Central Kitchen (Hub)
                </div>
                <p className="text-[10px] text-gray-400 mt-0.5">Picked up 83.0 kg • 15:30</p>
              </div>

              <div className="absolute top-16 right-6 p-2.5 rounded-xl bg-gray-900/90 border border-white/10 text-xs">
                <div className="flex items-center gap-1.5 text-violet-400 font-bold">
                  <MapPin className="h-3.5 w-3.5" /> Stop 3: Feeding India Shelter
                </div>
                <p className="text-[10px] text-gray-400 mt-0.5">Pending • ETA 16:45</p>
              </div>

              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 p-3 rounded-xl bg-gray-950/95 border border-cyan-500/50 shadow-2xl text-xs space-y-1 z-10">
                <div className="flex items-center justify-between gap-4">
                  <span className="font-bold text-white flex items-center gap-1">
                    <Truck className="h-3.5 w-3.5 text-cyan-400" /> {activeRoute?.vehicle_id || 'EV-VAN-DL-4C'}
                  </span>
                  <span className="text-[10px] font-mono text-emerald-400 font-bold">38 km/h</span>
                </div>
                <p className="text-[10px] text-gray-400">Driver: {activeRoute?.driver_name || 'Rajesh Kumar'}</p>
                <div className="pt-1 flex items-center justify-between text-[10px] font-mono text-cyan-300">
                  <span>Reefer: 3.4°C</span>
                  <span>Dist: {activeRoute?.total_distance_km || 18.4} km</span>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-white/5 text-center">
            <div className="p-2.5 rounded-xl bg-white/5">
              <span className="text-[10px] text-gray-400">Total Distance</span>
              <p className="text-base font-black text-white font-mono">{activeRoute?.total_distance_km || 18.4} km</p>
            </div>
            <div className="p-2.5 rounded-xl bg-white/5">
              <span className="text-[10px] text-gray-400">Est. Duration</span>
              <p className="text-base font-black text-white font-mono">{activeRoute?.estimated_duration_min || 42} min</p>
            </div>
            <div className="p-2.5 rounded-xl bg-white/5">
              <span className="text-[10px] text-gray-400">Rescued Load</span>
              <p className="text-base font-black text-emerald-400 font-mono">83.0 kg</p>
            </div>
          </div>
        </div>

        {/* Right 5 Cols: Waypoints Sequence & Delivery Verification */}
        <div className="lg:col-span-5 space-y-4">
          <div className="glass-card p-6 rounded-2xl">
            <h2 className="text-base font-bold text-white mb-1">Optimized Stop Sequence</h2>
            <p className="text-xs text-gray-400 mb-4">Greedy heuristic waypoint order factoring food shelf life</p>

            <div className="space-y-4">
              {activeRoute?.waypoints.map((wp, index) => {
                const isLast = index === activeRoute.waypoints.length - 1;
                return (
                  <div key={wp.sequence} className="relative flex items-start gap-3">
                    {!isLast && (
                      <div className="absolute left-3.5 top-7 w-0.5 h-12 bg-white/10" />
                    )}

                    <div className={`h-7 w-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                      wp.status === 'COMPLETED' ? 'bg-emerald-500 text-gray-950' :
                      wp.status === 'IN_TRANSIT' ? 'bg-cyan-500 text-gray-950 animate-pulse' :
                      'bg-white/10 text-gray-400'
                    }`}>
                      {wp.sequence}
                    </div>

                    <div className="flex-1 p-3 rounded-xl bg-white/5 border border-white/5">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-white">{wp.name}</h4>
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          wp.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-300' :
                          wp.status === 'IN_TRANSIT' ? 'bg-cyan-500/20 text-cyan-300' :
                          'bg-white/5 text-gray-400'
                        }`}>
                          {wp.status}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center justify-between text-[11px] text-gray-400">
                        <span>Action: <strong className="text-gray-200">{wp.action}</strong></span>
                        <span className="font-mono text-emerald-400">{wp.load_change_kg > 0 ? `+${wp.load_change_kg}` : wp.load_change_kg} kg</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* OTP Proof of Delivery Verification Box */}
            <div className="mt-6 p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                <h4 className="text-xs font-bold text-white">Digital Proof of Delivery (PoD)</h4>
              </div>
              <p className="text-[11px] text-gray-400">
                Driver verifies handover via 4-digit recipient OTP + food temperature log upon physical arrival.
              </p>

              {podSuccessMessage && (
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>{podSuccessMessage}</span>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-gray-400 block mb-1">Recipient OTP</label>
                  <div className="relative">
                    <input 
                      type="text" 
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value)}
                      placeholder="4-digit OTP"
                      className="w-full pl-7 pr-2 py-1.5 rounded-lg bg-black/40 border border-white/10 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
                    />
                    <KeyRound className="h-3.5 w-3.5 text-gray-400 absolute left-2 top-2" />
                  </div>
                </div>
                <div>
                  <label className="text-[10px] text-gray-400 block mb-1">Arrival Temp (°C)</label>
                  <input 
                    type="number" 
                    step="0.1"
                    value={deliveredFoodTemp}
                    onChange={(e) => setDeliveredFoodTemp(e.target.value)}
                    placeholder="e.g. 3.8"
                    className="w-full px-3 py-1.5 rounded-lg bg-black/40 border border-white/10 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <button
                onClick={handleConfirmDelivery}
                disabled={confirmingPod || !otpCode}
                className="w-full py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-gray-950 text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-md shadow-emerald-500/20 disabled:opacity-50"
              >
                <CheckCircle2 className="h-4 w-4" />
                <span>{confirmingPod ? 'Verifying OTP with Ledger...' : 'Confirm Delivery Handover'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
