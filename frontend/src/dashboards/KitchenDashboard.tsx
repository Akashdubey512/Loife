import React, { useEffect, useState } from 'react';
import { 
  Sparkles, 
  Clock, 
  CheckCircle2,
  Building2,
  TrendingDown,
  AlertTriangle,
  PlusCircle,
  Trash2,
  RefreshCw,
  Send,
  Boxes
} from 'lucide-react';
import { apiService } from '../services/api';
import { DemandItem } from '../types';
import storyThaliMindful from '../assets/illustrations/food/story_thali_mindful.png';

export const KitchenDashboard: React.FC = () => {
  const [kitchens, setKitchens] = useState<any[]>([]);
  const [selectedKitchenId, setSelectedKitchenId] = useState<number>(1);
  const [demands, setDemands] = useState<DemandItem[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<string>('LUNCH');
  const [foodItems, setFoodItems] = useState<any[]>([]);
  const [expiringBatches, setExpiringBatches] = useState<any[]>([]);
  const [wastePrediction, setWastePrediction] = useState<any>(null);
  const [dataLoading, setDataLoading] = useState(false);
  const [dataError, setDataError] = useState<string | null>(null);
  const [initError, setInitError] = useState<string | null>(null);

  // Forecast Generator state
  const [forecastModalOpen, setForecastModalOpen] = useState(false);
  const [selectedFoodItemId, setSelectedFoodItemId] = useState<number>(1);
  const [forecastFootfall, setForecastFootfall] = useState<number>(450);
  const [forecastingLoading, setForecastingLoading] = useState(false);
  const [forecastSuccessMsg, setForecastSuccessMsg] = useState<string | null>(null);
  const [dashboardForecastMsg, setDashboardForecastMsg] = useState<string | null>(null);

  // Waste Event Logger state
  const [wasteModalOpen, setWasteModalOpen] = useState(false);
  const [wasteQuantityKg, setWasteQuantityKg] = useState<string>('8.5');
  const [wasteCause, setWasteCause] = useState<string>('OVERPRODUCTION');
  const [wasteStage, setWasteStage] = useState<string>('LEFTOVER_BUFFET');
  const [wasteErrorMsg, setWasteErrorMsg] = useState<string | null>(null);

  // Declare Surplus state (Posts directly to Redistribution Hub)
  const [surplusModalOpen, setSurplusModalOpen] = useState(false);
  const [surplusQuantityKg, setSurplusQuantityKg] = useState<string>('15.0');
  const [surplusExpiryHours, setSurplusExpiryHours] = useState<string>('6');
  const [surplusLoading, setSurplusLoading] = useState(false);
  const [surplusSuccessMsg, setSurplusSuccessMsg] = useState<string | null>(null);

  // Load Kitchens and Food items on mount
  useEffect(() => {
    const fetchInit = async () => {
      try {
        const kList = await apiService.getKitchens();
        setKitchens(kList);
        if (kList.length > 0) {
          setSelectedKitchenId(kList[0].id);
        }
      } catch (err: any) {
        const detail = err?.response?.data?.detail;
        setInitError(typeof detail === 'string' ? detail : 'Failed to load kitchen list. Check backend connection.');
      }

      try {
        const fList = await apiService.getFoodItems();
        setFoodItems(fList);
        if (fList.length > 0) {
          setSelectedFoodItemId(fList[0].id);
        }
      } catch { /* non-critical */ }
    };
    fetchInit();
  }, []);

  // Load operational data whenever kitchen or slot changes
  const loadKitchenData = async (kId: number) => {
    setDataLoading(true);
    setDataError(null);
    try {
      const [dData, wData, bData] = await Promise.allSettled([
        apiService.getDemandForecast(kId),
        apiService.getWastePrediction(kId),
        apiService.getExpiringBatches(kId)
      ]);
      if (dData.status === 'fulfilled') setDemands(dData.value);
      else setDemands([]);
      if (wData.status === 'fulfilled') setWastePrediction(wData.value);
      else setWastePrediction(null);
      if (bData.status === 'fulfilled') setExpiringBatches(bData.value);
      else setExpiringBatches([]);

      const failed = [dData, wData, bData].filter(r => r.status === 'rejected');
      if (failed.length === 3) {
        setDataError('Failed to load kitchen data. Check backend connection.');
      }
    } finally {
      setDataLoading(false);
    }
  };


  useEffect(() => {
    loadKitchenData(selectedKitchenId);
  }, [selectedKitchenId, selectedSlot]);

  // Handle Run AI Forecast (Workflow A)
  const handleGenerateForecast = async (e: React.FormEvent) => {
    e.preventDefault();
    setForecastingLoading(true);
    setForecastSuccessMsg(null);
    try {
      const res = await apiService.predictDemand({
        kitchen_id: selectedKitchenId,
        food_item_id: selectedFoodItemId,
        meal_slot: selectedSlot,
        expected_footfall: forecastFootfall
      });

      const msg = `AI Forecast Generated & Persisted to DB Schedule! Item: ${res.food_name || 'Selected Item'} | Expected Demand: ${res.expected_demand_kg} kg | Inventory on Hand: ${res.current_inventory_on_hand_kg || 0} kg | Net Prep Target: ${res.net_recommended_production_kg} kg`;
      setForecastSuccessMsg(msg);
      setDashboardForecastMsg(msg);

      // Immediately append/update demands state in UI
      setDemands(prev => {
        const existingIdx = prev.findIndex(item => item.food_item_id === res.food_item_id);
        const newItem: DemandItem = {
          food_item_id: res.food_item_id,
          food_name: res.food_name || `Item #${res.food_item_id}`,
          expected_demand_kg: res.expected_demand_kg,
          confidence_score: res.confidence_score,
          recommended_production_kg: res.net_recommended_production_kg || res.recommended_production_kg,
          surplus_risk_probability: res.surplus_risk_probability,
          model_version: res.model_version || 'demand-lgbm-v1.0'
        };
        if (existingIdx >= 0) {
          const copy = [...prev];
          copy[existingIdx] = newItem;
          return copy;
        }
        return [newItem, ...prev];
      });

      // Reload demands from persisted DB
      await loadKitchenData(selectedKitchenId);
      setTimeout(() => {
        setForecastModalOpen(false);
      }, 1200);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setForecastSuccessMsg(null);
      alert(`Forecast failed: ${typeof detail === 'string' ? detail : 'API error — check backend connection.'}`);
    } finally {
      setForecastingLoading(false);
    }
  };

  // Handle Log Waste Event (Workflow B)
  const [wasteLoading, setWasteLoading] = useState(false);
  const [wasteSuccessMsg, setWasteSuccessMsg] = useState<string | null>(null);

  const handleLogWaste = async (e: React.FormEvent) => {
    e.preventDefault();
    setWasteLoading(true);
    setWasteSuccessMsg(null);
    setWasteErrorMsg(null);
    try {
      const qty = parseFloat(wasteQuantityKg) || 5.0;
      await apiService.logWasteEvent({
        kitchen_id: selectedKitchenId,
        food_item_id: selectedFoodItemId,
        batch_id: expiringBatches[0]?.id || undefined,
        quantity_wasted_kg: qty,
        primary_cause: wasteCause,
        waste_stage: wasteStage
      });

      let extraNotice = '';
      // If overproduction or leftover buffet, automatically post edible portion to Redistribution Hub!
      if (wasteCause === 'OVERPRODUCTION' || wasteStage === 'LEFTOVER_BUFFET') {
        try {
          const expTime = new Date(Date.now() + 6 * 3600 * 1000).toISOString();
          await apiService.createSurplus({
            kitchen_id: selectedKitchenId,
            food_item_id: selectedFoodItemId,
            quantity_kg: qty,
            expires_at: expTime,
            safe_temp_celsius: 65.0
          });
          extraNotice = ' & Edible portion automatically posted live to Redistribution Hub!';
        } catch { /* non-critical */ }
      }

      setWasteSuccessMsg(`Waste event logged: ${qty} kg${extraNotice}`);
      await loadKitchenData(selectedKitchenId);
      setTimeout(() => {
        setWasteModalOpen(false);
        setWasteSuccessMsg(null);
      }, 1800);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const status = err?.response?.status;
      if (status === 401) {
        setWasteErrorMsg('Unauthorised: please log in and try again.');
      } else if (typeof detail === 'string') {
        setWasteErrorMsg(`API error: ${detail}`);
      } else {
        setWasteErrorMsg('Waste logging failed. Check backend connection.');
      }
    } finally {
      setWasteLoading(false);
    }
  };

  // Handle Declare Surplus (Posts directly to Redistribution Hub)
  const handleDeclareSurplus = async (e: React.FormEvent) => {
    e.preventDefault();
    setSurplusLoading(true);
    setSurplusSuccessMsg(null);
    try {
      const qty = parseFloat(surplusQuantityKg) || 10.0;
      const hrs = parseInt(surplusExpiryHours) || 6;
      const expiresAt = new Date(Date.now() + hrs * 3600 * 1000).toISOString();

      await apiService.createSurplus({
        kitchen_id: selectedKitchenId,
        food_item_id: selectedFoodItemId,
        quantity_kg: qty,
        expires_at: expiresAt,
        safe_temp_celsius: 65.0
      });

      setSurplusSuccessMsg(`Surplus lot declared (${qty} kg) and posted live to the Redistribution Hub!`);
      await loadKitchenData(selectedKitchenId);
      setTimeout(() => {
        setSurplusModalOpen(false);
        setSurplusSuccessMsg(null);
      }, 1500);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      alert(`Surplus declaration failed: ${typeof detail === 'string' ? detail : 'API error — check backend connection.'}`);
    } finally {
      setSurplusLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Init / connection error */}
      {initError && (
        <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0" /> {initError}
        </div>
      )}
      {dataError && (
        <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0" /> {dataError}
        </div>
      )}
      {/* Header & Facility Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Kitchen Operations & Predictive Demand</h1>
          <p className="text-xs text-gray-400 mt-1">
            Dynamic portioning, production scheduling, and inventory management via heuristic forecasting engine.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Kitchen Selector Dropdown */}
          <div className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-xl border border-white/10">
            <Building2 className="h-4 w-4 text-emerald-400" />
            <select
              value={selectedKitchenId}
              onChange={(e) => setSelectedKitchenId(Number(e.target.value))}
              aria-label="Select Kitchen Facility"
              className="bg-transparent text-xs font-semibold text-gray-200 focus:outline-none cursor-pointer"
            >
              {kitchens.map((k, idx) => (
                <option key={`kitchen-${k.id}-${idx}`} value={k.id} className="bg-gray-900 text-white">
                  {k.name} ({k.facility_code})
                </option>
              ))}
            </select>
          </div>

          {/* Shift Slot Selector */}
          <div className="flex items-center gap-1 bg-white/5 p-1 rounded-xl border border-white/10">
            {['BREAKFAST', 'LUNCH', 'DINNER'].map((slot) => (
              <button
                key={slot}
                onClick={() => setSelectedSlot(slot)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                  selectedSlot === slot
                    ? 'bg-emerald-500 text-gray-950 shadow-md shadow-emerald-500/20'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {slot}
              </button>
            ))}
          </div>

          {/* Action Buttons */}
          <button
            onClick={() => setForecastModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-gray-950 transition shadow-lg shadow-emerald-500/20"
          >
            <Sparkles className="h-4 w-4" /> Run AI Forecast
          </button>

          <button
            onClick={() => setSurplusModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-gray-950 transition shadow-lg shadow-cyan-500/20"
          >
            <Boxes className="h-4 w-4" /> Declare Surplus
          </button>

          <button
            onClick={() => setWasteModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-white/10 hover:bg-white/15 text-rose-300 border border-rose-500/30 transition"
          >
            <Trash2 className="h-4 w-4 text-rose-400" /> Record Waste
          </button>
        </div>
      </div>

      {/* Dashboard Forecast Toast/Banner */}
      {dashboardForecastMsg && (
        <div className="p-4 rounded-2xl bg-emerald-950/70 border border-emerald-500/60 text-emerald-300 text-xs flex items-center justify-between gap-3 shadow-xl animate-in fade-in duration-300">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
            <span className="font-medium">{dashboardForecastMsg}</span>
          </div>
          <button
            onClick={() => setDashboardForecastMsg(null)}
            className="text-gray-400 hover:text-white text-xs font-bold px-2 py-1 rounded bg-white/10"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Loife Kitchen Mindful Prep Banner */}
      <div className="loife-surface-warm p-4 md:p-5 rounded-2xl border border-[#F2C45A]/30 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-lg">
        <div className="flex items-center gap-4">
          <div className="h-16 w-24 sm:h-20 sm:w-28 rounded-xl overflow-hidden shrink-0 border border-white/10 shadow-md">
            <img
              src={storyThaliMindful}
              alt="Mindful thali prep"
              className="w-full h-full object-cover"
            />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded-full bg-[#174C3C]/50 border border-[#F2C45A]/30 text-[#F2C45A] text-[10px] font-bold uppercase tracking-wider">
                Plan with care • Prepare with purpose
              </span>
              {demands.length > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                  {demands[0].model_version || 'demand-lgbm-v1.0'}
                </span>
              )}
            </div>
            <h2 className="text-sm sm:text-base font-bold text-white">
              AI Chef Operational Advisory (Active Shift)
            </h2>
            <p className="text-xs text-gray-300 max-w-2xl mt-0.5 leading-relaxed">
              {demands.length > 0
                ? `Demand forecast ready for ${demands.length} items. Highest risk: ${demands.sort((a,b) => b.surplus_risk_probability - a.surplus_risk_probability)[0]?.food_name} (${(demands[0].surplus_risk_probability * 100).toFixed(0)}% surplus risk). Review production targets and dispatch expiring batches to NGO partners.`
                : expiringBatches.length > 0
                ? `${expiringBatches.filter((b: any) => b.status === 'NEARING_EXPIRY').length} batches nearing expiry. Run demand forecast to get production recommendations.`
                : 'Run a demand forecast to receive AI-driven production recommendations for this shift.'}
            </p>
          </div>
        </div>
        <div className="shrink-0 text-right hidden lg:block">
          <p className="text-xs font-serif text-[#F2C45A] italic">
            “इतना ही लो थाली में”
          </p>
          <span className="text-[10px] text-gray-400">Respect every ingredient</span>
        </div>
      </div>

      {/* Grid: Demand Forecast vs Expiring Inventory */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Demand Forecast & Production Planning */}
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white">Today's Demand Forecast & Recommended Production</h2>
              <p className="text-xs text-gray-400">Heuristic forecasting engine factoring inventory on hand & attendance</p>
            </div>
            <button
              onClick={() => loadKitchenData(selectedKitchenId)}
              className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition"
              title="Refresh Forecast Data"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-white/10 text-gray-400 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-3">Meal Item</th>
                  <th className="py-3 px-3">Expected Demand</th>
                  <th className="py-3 px-3">Recommended Prep</th>
                  <th className="py-3 px-3">Surplus Risk</th>
                  <th className="py-3 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {demands.map((item, index) => (
                  <tr key={`demand-${item.food_item_id}-${index}`} className="hover:bg-white/5 transition">
                    <td className="py-3.5 px-3 font-semibold text-white">
                      {item.food_name}
                    </td>
                    <td className="py-3.5 px-3 font-mono text-gray-200">
                      {item.expected_demand_kg} kg
                    </td>
                    <td className="py-3.5 px-3 font-mono font-bold text-emerald-400">
                      {item.recommended_production_kg} kg
                    </td>
                    <td className="py-3.5 px-3 font-mono">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        item.surplus_risk_probability > 0.1
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : 'bg-emerald-500/10 text-emerald-400'
                      }`}>
                        {(item.surplus_risk_probability * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="py-3.5 px-3">
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400">
                        <CheckCircle2 className="h-3 w-3" /> Scheduled
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Col: Expiring Batches & Waste Prediction */}
        <div className="space-y-6">
          {/* Expiring Batches */}
          <div className="glass-card p-6 rounded-2xl">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-amber-400" />
                <h2 className="text-base font-bold text-white">Expiring Items Alert</h2>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">
                Action Required
              </span>
            </div>
            <p className="text-xs text-gray-400 mb-5">Batches nearing shelf-life limit within next 12 hours.</p>

            <style>{`
              @keyframes floatDriftA {
                0%   { transform: translate(0px, 0px) rotate(0deg); }
                25%  { transform: translate(8px, -15px) rotate(1.5deg); }
                50%  { transform: translate(-7px, -6px) rotate(-1deg); }
                75%  { transform: translate(9px, -20px) rotate(2deg); }
                100% { transform: translate(0px, 0px) rotate(0deg); }
              }
              @keyframes floatDriftB {
                0%   { transform: translate(0px, 0px) rotate(0deg); }
                25%  { transform: translate(-11px, -10px) rotate(-2deg); }
                50%  { transform: translate(7px, -22px) rotate(1.5deg); }
                75%  { transform: translate(-8px, -12px) rotate(-1.5deg); }
                100% { transform: translate(0px, 0px) rotate(0deg); }
              }
              @keyframes floatDriftC {
                0%   { transform: translate(0px, 0px) rotate(0deg); }
                30%  { transform: translate(12px, -18px) rotate(2.5deg); }
                55%  { transform: translate(-10px, -26px) rotate(-2deg); }
                80%  { transform: translate(6px, -9px) rotate(1deg); }
                100% { transform: translate(0px, 0px) rotate(0deg); }
              }
              @keyframes floatDriftD {
                0%   { transform: translate(0px, 0px) rotate(0deg); }
                20%  { transform: translate(-9px, -19px) rotate(-2deg); }
                50%  { transform: translate(11px, -11px) rotate(2deg); }
                75%  { transform: translate(-6px, -24px) rotate(-1deg); }
                100% { transform: translate(0px, 0px) rotate(0deg); }
              }
              @keyframes floatDriftE {
                0%   { transform: translate(0px, 0px) rotate(0deg); }
                30%  { transform: translate(-12px, -14px) rotate(1.5deg); }
                60%  { transform: translate(10px, -23px) rotate(-2.5deg); }
                85%  { transform: translate(-5px, -7px) rotate(1deg); }
                100% { transform: translate(0px, 0px) rotate(0deg); }
              }
              @keyframes moteOrbit {
                0%   { transform: translate(0, 0) scale(1);   opacity: 0; }
                20%  { opacity: 0.9; }
                50%  { opacity: 0.5; }
                80%  { opacity: 0.8; }
                100% { transform: translate(var(--mx), var(--my)) scale(0.4); opacity: 0; }
              }
              .bubble-float-A { animation: floatDriftA var(--float-dur, 4.8s) ease-in-out infinite; }
              .bubble-float-B { animation: floatDriftB var(--float-dur, 5.4s) ease-in-out infinite; }
              .bubble-float-C { animation: floatDriftC var(--float-dur, 4.2s) ease-in-out infinite; }
              .bubble-float-D { animation: floatDriftD var(--float-dur, 6.0s) ease-in-out infinite; }
              .bubble-float-E { animation: floatDriftE var(--float-dur, 5.1s) ease-in-out infinite; }
              .batch-bubble:hover {
                transform: translateY(-16px) scale(1.1) !important;
                z-index: 30;
                animation-play-state: paused !important;
              }
              .mote {
                position: absolute;
                width: 3px; height: 3px;
                border-radius: 50%;
                background: #10b981;
                box-shadow: 0 0 5px 2px #10b981aa;
                animation: moteOrbit var(--m-dur, 3s) ease-out infinite;
                animation-delay: var(--m-delay, 0s);
                pointer-events: none;
                top: 50%; left: 50%;
                margin: -1.5px 0 0 -1.5px;
              }
            `}</style>

            <div className="flex flex-wrap items-center justify-center gap-3.5 min-h-[300px] py-4">
              {(() => {
                const displayBatches = expiringBatches.slice(0, 10);

                if (displayBatches.length === 0) {
                  return (
                    <div className="flex flex-col items-center justify-center min-h-[200px] text-center">
                      <p className="text-xs text-gray-400">No batch records available.</p>
                      <p className="text-[11px] text-gray-500 mt-1">Add inventory batches to see expiry tracking.</p>
                    </div>
                  );
                }

                const floatSettings = [
                  { animClass: 'bubble-float-A', dur: '4.6s', delay: '-1.2s', offsetY: '-8px' },
                  { animClass: 'bubble-float-B', dur: '5.8s', delay: '-3.4s', offsetY: '12px' },
                  { animClass: 'bubble-float-C', dur: '4.1s', delay: '-0.7s', offsetY: '-14px' },
                  { animClass: 'bubble-float-D', dur: '6.3s', delay: '-4.2s', offsetY: '8px' },
                  { animClass: 'bubble-float-E', dur: '5.0s', delay: '-2.1s', offsetY: '-4px' },
                  { animClass: 'bubble-float-B', dur: '4.7s', delay: '-3.8s', offsetY: '14px' },
                  { animClass: 'bubble-float-A', dur: '6.1s', delay: '-1.5s', offsetY: '-10px' },
                  { animClass: 'bubble-float-D', dur: '4.9s', delay: '-2.7s', offsetY: '6px' },
                  { animClass: 'bubble-float-C', dur: '6.5s', delay: '-0.4s', offsetY: '-12px' },
                  { animClass: 'bubble-float-E', dur: '5.3s', delay: '-4.8s', offsetY: '4px' },
                ];

                return displayBatches.map((batch: any, index: number) => {
                  const isExpiring = batch.status === 'NEARING_EXPIRY';
                  const kg = Math.round(batch.remaining_quantity_kg);
                  const size = kg <= 70 ? 70 : kg <= 95 ? 80 : kg <= 125 ? 90 : kg <= 150 ? 100 : kg <= 170 ? 110 : 120;
                  const shortCode = batch.batch_number?.split('-').pop() || `#${batch.id}`;
                  const setting = floatSettings[index % floatSettings.length];

                  // 6 luminous motes at varied radii for optimal green bubbles
                  const motes = !isExpiring ? [
                    { mx: '32px',  my: '-30px', dur: '2.8s', delay: '0s'    },
                    { mx: '-34px', my: '-22px', dur: '3.4s', delay: '0.6s'  },
                    { mx: '28px',  my: '34px',  dur: '2.6s', delay: '1.1s'  },
                    { mx: '-26px', my: '32px',  dur: '3.8s', delay: '0.3s'  },
                    { mx: '38px',  my: '10px',  dur: '3.1s', delay: '1.5s'  },
                    { mx: '-32px', my: '8px',   dur: '2.9s', delay: '0.8s'  },
                  ] : [];

                  return (
                    <div
                      key={`batch-${batch.id}-${index}`}
                      className={`batch-bubble ${setting.animClass} relative group cursor-pointer transition-all duration-300`}
                      style={{
                        '--float-dur': setting.dur,
                        animationDelay: setting.delay,
                        marginTop: setting.offsetY,
                      } as React.CSSProperties}
                      onClick={() => setWasteModalOpen(true)}
                    >
                      {/* Mote particles for OPTIMAL green bubbles */}
                      {motes.map((m, mi) => (
                        <span
                          key={mi}
                          className="mote"
                          style={{
                            '--mx': m.mx,
                            '--my': m.my,
                            '--m-dur': m.dur,
                            '--m-delay': m.delay,
                          } as React.CSSProperties}
                        />
                      ))}

                      {/* Circle */}
                      <div
                        className={`rounded-full flex flex-col items-center justify-center border-2 shadow-lg transition-all duration-300 relative
                          ${isExpiring
                            ? 'bg-amber-950/60 border-amber-400/60 shadow-amber-500/20 group-hover:border-amber-400 group-hover:shadow-amber-500/40'
                            : 'bg-emerald-950/50 border-emerald-500/40 shadow-emerald-500/10 group-hover:border-emerald-400 group-hover:shadow-emerald-500/40 group-hover:shadow-lg'
                          }`}
                        style={{
                          width: size,
                          height: size,
                          boxShadow: !isExpiring ? '0 0 18px 2px #10b98122, inset 0 0 12px #10b98110' : undefined,
                        }}
                      >
                        <span className={`text-[10px] font-bold uppercase tracking-wider mb-0.5 ${isExpiring ? 'text-amber-400' : 'text-emerald-400'}`}>
                          {shortCode}
                        </span>
                        <span className="text-white font-black text-sm leading-tight">
                          {kg} <span className="text-[10px] font-normal text-gray-400">kg</span>
                        </span>

                        {/* Hover overlay: Log Waste */}
                        <span className="absolute inset-0 rounded-full flex items-center justify-center bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-200 text-[10px] font-bold text-rose-400">
                          Log →
                        </span>
                      </div>

                      {/* Expiring pulse ring */}
                      {isExpiring && (
                        <span className="absolute inset-0 rounded-full border-2 border-amber-400/40 animate-ping" style={{ animationDuration: '2s' }} />
                      )}
                    </div>
                  );
                });
              })()}
            </div>
          </div>


            <div className="glass-card p-6 rounded-2xl border-l-4 border-l-cyan-500">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Shift Waste Risk Forecast</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300">
                Rule-based waste risk
              </span>
            </div>
            {wastePrediction ? (
              <>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-white">
                    {wastePrediction.expected_waste_kg} kg
                  </span>
                  <span className="text-xs text-cyan-400 font-bold">
                    ({(wastePrediction.waste_probability * 100).toFixed(0)}% risk prob)
                  </span>
                </div>
                <p className="text-xs text-gray-300 mt-2 leading-relaxed">
                  <strong>Root Cause:</strong> {wastePrediction.predicted_root_cause}
                </p>
                <p className="text-xs text-emerald-400 mt-1 font-medium">
                  💡 <strong>Action:</strong> {wastePrediction.prevention_recommendation}
                </p>
              </>
            ) : (
              <p className="text-xs text-gray-400 mt-2">No waste prediction data available.</p>
            )}
          </div>
        </div>
      </div>

      {/* Modal: Generate AI Demand Forecast (Workflow A) */}
      {forecastModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4">
          <div className="glass-panel border border-white/15 rounded-3xl p-6 max-w-lg w-full shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white">Run AI Demand Forecasting</h3>
              </div>
              <button 
                onClick={() => setForecastModalOpen(false)}
                className="text-gray-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleGenerateForecast} className="space-y-4">
              {forecastSuccessMsg && (
                <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-xs flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  <span>{forecastSuccessMsg}</span>
                </div>
              )}

              <div>
                <label className="text-xs text-gray-300 font-semibold block mb-1">Food Catalog Item</label>
                <select
                  value={selectedFoodItemId}
                  onChange={(e) => setSelectedFoodItemId(Number(e.target.value))}
                  aria-label="Select Food Catalog Item"
                  className="w-full px-3 py-2 rounded-xl bg-gray-900 border border-white/15 text-white text-xs focus:border-emerald-500 focus:outline-none"
                >
                  {foodItems.map((fi, idx) => (
                    <option key={`fi-pred-${fi.id}-${idx}`} value={fi.id}>
                      {fi.name} ({fi.category})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-300 font-semibold block mb-1">Meal Slot</label>
                  <select
                    value={selectedSlot}
                    onChange={(e) => setSelectedSlot(e.target.value)}
                    aria-label="Select Meal Slot"
                    className="w-full px-3 py-2 rounded-xl bg-gray-900 border border-white/15 text-white text-xs focus:border-emerald-500 focus:outline-none"
                  >
                    <option value="BREAKFAST">BREAKFAST</option>
                    <option value="LUNCH">LUNCH</option>
                    <option value="DINNER">DINNER</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs text-gray-300 font-semibold block mb-1">Expected Footfall (Guests)</label>
                  <input
                    type="number"
                    min="50"
                    max="5000"
                    value={forecastFootfall}
                    onChange={(e) => setForecastFootfall(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/15 text-white text-xs focus:border-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <p className="text-[11px] text-gray-400 bg-white/5 p-3 rounded-xl border border-white/5">
                ℹ️ The heuristic forecasting engine computes a rolling-average + day-of-week prediction, checks inventory on hand, subtracts available stock, and persists the net recommended production quantity to the kitchen schedule.
              </p>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setForecastModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={forecastingLoading}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-gray-950 shadow-lg shadow-emerald-500/20 disabled:opacity-50"
                >
                  {forecastingLoading ? 'Computing Forecast...' : 'Generate & Persist Forecast'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Record Food Waste Event (Workflow B) */}
      {wasteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4">
          <div className="glass-panel border border-white/15 rounded-3xl p-6 max-w-lg w-full shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
              <div className="flex items-center gap-2">
                <Trash2 className="h-5 w-5 text-rose-400" />
                <h3 className="text-base font-bold text-white">Record Verified Food Waste Event</h3>
              </div>
              <button 
                onClick={() => setWasteModalOpen(false)}
                className="text-gray-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleLogWaste} className="space-y-4">
              {wasteSuccessMsg && (
                <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-xs flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  <span>{wasteSuccessMsg}</span>
                </div>
              )}

              <div>
                <label className="text-xs text-gray-300 font-semibold block mb-1">Food Item</label>
                <select
                  value={selectedFoodItemId}
                  onChange={(e) => setSelectedFoodItemId(Number(e.target.value))}
                  aria-label="Select Food Item for Waste Event"
                  className="w-full px-3 py-2 rounded-xl bg-gray-900 border border-white/15 text-white text-xs focus:border-emerald-500 focus:outline-none"
                >
                  {foodItems.map((fi, idx) => (
                    <option key={`fi-waste-${fi.id}-${idx}`} value={fi.id}>
                      {fi.name} ({fi.category})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs text-gray-300 font-semibold block mb-1">Quantity Wasted (kg)</label>
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  required
                  value={wasteQuantityKg}
                  onChange={(e) => setWasteQuantityKg(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/15 text-white text-xs focus:border-rose-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-300 font-semibold block mb-1">Primary Root Cause</label>
                  <select
                    value={wasteCause}
                    onChange={(e) => setWasteCause(e.target.value)}
                    aria-label="Select Primary Root Cause"
                    className="w-full px-3 py-2 rounded-xl bg-gray-900 border border-white/15 text-white text-xs focus:border-rose-500 focus:outline-none"
                  >
                    <option value="OVERPRODUCTION">Overproduction</option>
                    <option value="EXPIRY_REACHED">Expiry Date Reached</option>
                    <option value="REFRIGERATION_FAILURE">Cold Storage Breach</option>
                    <option value="BURNED_OVERCOOKED">Preparation Loss / Burned</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs text-gray-300 font-semibold block mb-1">Waste Stage</label>
                  <select
                    value={wasteStage}
                    onChange={(e) => setWasteStage(e.target.value)}
                    aria-label="Select Waste Stage"
                    className="w-full px-3 py-2 rounded-xl bg-gray-900 border border-white/15 text-white text-xs focus:border-rose-500 focus:outline-none"
                  >
                    <option value="PREPARATION">Food Prep & Peeling</option>
                    <option value="STORAGE_SPOILAGE">Storage Spoilage</option>
                    <option value="LEFTOVER_BUFFET">Service / Buffet Leftover</option>
                  </select>
                </div>
              </div>

              <p className="text-[11px] text-gray-400 bg-white/5 p-3 rounded-xl border border-white/5">
                ⚠️ Recording a verified waste event updates the inventory batch quantity atomically, triggers financial loss accounting (INR 110/kg), and feeds the waste reduction analytics dashboard.
              </p>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setWasteModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={wasteLoading}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-rose-500 hover:bg-rose-400 text-white shadow-lg shadow-rose-500/20 disabled:opacity-50"
                >
                  {wasteLoading ? 'Recording Event...' : 'Confirm & Log Waste'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Declare Surplus Food (Posts directly to Redistribution Hub) */}
      {surplusModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4">
          <div className="glass-panel border border-white/15 rounded-3xl p-6 max-w-lg w-full shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
              <div className="flex items-center gap-2">
                <Boxes className="h-5 w-5 text-cyan-400" />
                <h3 className="text-base font-bold text-white">Declare Surplus Food for Redistribution</h3>
              </div>
              <button 
                onClick={() => setSurplusModalOpen(false)}
                className="text-gray-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleDeclareSurplus} className="space-y-4">
              {surplusSuccessMsg && (
                <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-xs flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  <span>{surplusSuccessMsg}</span>
                </div>
              )}

              <div>
                <label className="text-xs text-gray-300 font-semibold block mb-1">Surplus Food Item</label>
                <select
                  value={selectedFoodItemId}
                  onChange={(e) => setSelectedFoodItemId(Number(e.target.value))}
                  aria-label="Select Surplus Food Item"
                  className="w-full px-3 py-2 rounded-xl bg-gray-900 border border-white/15 text-white text-xs focus:border-cyan-500 focus:outline-none"
                >
                  {foodItems.map((fi, idx) => (
                    <option key={`fi-surplus-${fi.id}-${idx}`} value={fi.id}>
                      {fi.name} ({fi.category})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-300 font-semibold block mb-1">Surplus Quantity (kg)</label>
                  <input
                    type="number"
                    step="0.5"
                    min="1"
                    required
                    value={surplusQuantityKg}
                    onChange={(e) => setSurplusQuantityKg(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/15 text-white text-xs focus:border-cyan-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-xs text-gray-300 font-semibold block mb-1">Safe Shelf Life (Hours)</label>
                  <input
                    type="number"
                    min="1"
                    max="48"
                    required
                    value={surplusExpiryHours}
                    onChange={(e) => setSurplusExpiryHours(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/15 text-white text-xs focus:border-cyan-500 focus:outline-none"
                  />
                </div>
              </div>

              <p className="text-[11px] text-gray-400 bg-white/5 p-3 rounded-xl border border-white/5">
                ℹ️ Declaring surplus posts this lot directly to the **Redistribution Hub** for local NGO matching, vehicle dispatch, and social impact tracking.
              </p>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setSurplusModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={surplusLoading}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-gray-950 shadow-lg shadow-cyan-500/20 disabled:opacity-50"
                >
                  {surplusLoading ? 'Posting to Hub...' : 'Post Surplus to Hub'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
