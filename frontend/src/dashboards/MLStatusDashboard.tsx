import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Cpu,
  Activity,
  FlaskConical,
  Eye,
  Leaf,
  Truck,
  Thermometer,
  Zap,
  Wrench
} from 'lucide-react';
import { apiService } from '../services/api';
import { MLStatusResponse, MLEngineStatus } from '../types';

const ENGINE_ICONS: Record<string, React.ElementType> = {
  demand_forecasting: Activity,
  predictive_maintenance: Wrench,
  energy_forecasting: Zap,
  waste_prediction: AlertTriangle,
  cv_freshness_classifier: Eye,
  enose_beef_quality: FlaskConical,
  sustainability_lca: Leaf,
  route_optimization: Truck,
};

const getStatusColor = (engine: MLEngineStatus) => {
  if (engine.status === 'ERROR') return { bg: 'bg-rose-950/40', border: 'border-rose-500/40', badge: 'bg-rose-500/20 text-rose-300 border-rose-500/40', dot: 'bg-rose-500' };
  if (engine.simulated) return { bg: 'bg-amber-950/30', border: 'border-amber-500/30', badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30', dot: 'bg-amber-400' };
  if (engine.status === 'fallback') return { bg: 'bg-slate-900/40', border: 'border-white/10', badge: 'bg-slate-500/20 text-slate-300 border-slate-500/30', dot: 'bg-slate-400' };
  if (engine.trained) return { bg: 'bg-emerald-950/30', border: 'border-emerald-500/30', badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30', dot: 'bg-emerald-500' };
  if (engine.status === 'active') return { bg: 'bg-cyan-950/30', border: 'border-cyan-500/30', badge: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30', dot: 'bg-cyan-400' };
  return { bg: 'bg-white/[0.03]', border: 'border-white/10', badge: 'bg-white/10 text-gray-300 border-white/10', dot: 'bg-gray-500' };
};

const getStatusLabel = (engine: MLEngineStatus): string => {
  if (engine.status === 'ERROR') return 'ERROR';
  if (engine.simulated) return 'SIMULATED';
  if (engine.trained) return 'TRAINED ✓';
  if (engine.status === 'active') return 'ACTIVE';
  if (engine.status === 'fallback') return 'FALLBACK';
  return engine.status?.toUpperCase() || 'UNKNOWN';
};

export const MLStatusDashboard: React.FC = () => {
  const [status, setStatus] = useState<MLStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getMlStatus();
      setStatus(data);
      setLastRefresh(new Date());
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to load ML status. Check backend connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">ML Engine Status Monitor</h1>
          <p className="text-xs text-gray-400 mt-1">
            Live verification of all ML/CV model artifacts and operational status. Truthful report — no fabrication.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastRefresh && (
            <span className="text-[11px] text-gray-500 font-mono">
              Last: {lastRefresh.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchStatus}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-gray-200 text-xs font-bold transition disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-sm flex items-center gap-3">
          <XCircle className="h-5 w-5 shrink-0 text-rose-400" />
          <div>
            <p className="font-bold">ML Status Unavailable</p>
            <p className="text-xs text-rose-400 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && !status && (
        <div className="flex items-center gap-3 text-gray-400 text-sm p-6">
          <RefreshCw className="h-5 w-5 animate-spin" />
          Querying ML engine registry...
        </div>
      )}

      {/* Summary Cards */}
      {status && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="glass-card p-4 rounded-2xl text-center">
              <Cpu className="h-5 w-5 text-emerald-400 mx-auto mb-2" />
              <p className="text-2xl font-black text-white">{status.total_engines}</p>
              <p className="text-[10px] text-gray-400 uppercase tracking-wider mt-0.5">Total Engines</p>
            </div>
            <div className="glass-card p-4 rounded-2xl text-center">
              <CheckCircle2 className="h-5 w-5 text-emerald-400 mx-auto mb-2" />
              <p className="text-2xl font-black text-emerald-400">{status.trained_models}</p>
              <p className="text-[10px] text-gray-400 uppercase tracking-wider mt-0.5">Trained Models</p>
            </div>
            <div className="glass-card p-4 rounded-2xl text-center">
              <Activity className="h-5 w-5 text-cyan-400 mx-auto mb-2" />
              <p className="text-2xl font-black text-cyan-400">{status.active_engines}</p>
              <p className="text-[10px] text-gray-400 uppercase tracking-wider mt-0.5">Active Engines</p>
            </div>
            <div className="glass-card p-4 rounded-2xl text-center">
              <span className={`block text-2xl font-black mt-1 ${status.ml_status === 'OPERATIONAL' ? 'text-emerald-400' : 'text-rose-400'}`}>
                {status.ml_status}
              </span>
              <p className="text-[10px] text-gray-400 uppercase tracking-wider mt-0.5">Platform Status</p>
            </div>
          </div>

          {/* Honesty Notice */}
          <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/20 text-xs text-amber-300 flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-amber-400" />
            <div>
              <strong className="block">Engineering Honesty Policy:</strong>
              Simulated engines report approximate outputs based on heuristics, NOT real trained weights.
              Fruit CV is SIMULATED — human verification is mandatory before any food safety decision.
              Waste ML is FALLBACK (rule-based) — 0 production waste events in training data.
            </div>
          </div>

          {/* Engine Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {status.engines.map((engine, i) => {
              const colors = getStatusColor(engine);
              const Icon = ENGINE_ICONS[engine.engine] || Cpu;
              return (
                <div
                  key={`engine-${engine.engine}-${i}`}
                  className={`${colors.bg} ${colors.border} border rounded-2xl p-5 space-y-3`}
                >
                  {/* Engine Header */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <div className={`h-9 w-9 rounded-xl flex items-center justify-center ${colors.bg} border ${colors.border}`}>
                        <Icon className="h-4.5 w-4.5 text-gray-200" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">
                          {engine.engine.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </h3>
                        <p className="text-[11px] text-gray-400 font-mono mt-0.5">
                          {engine.model_version || engine.model_type || 'unknown'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <span className={`h-2 w-2 rounded-full ${colors.dot}`} />
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${colors.badge}`}>
                        {getStatusLabel(engine)}
                      </span>
                    </div>
                  </div>

                  {/* Engine Details */}
                  <div className="space-y-1.5 text-[11px]">
                    {engine.endpoint && (
                      <div className="flex items-center justify-between">
                        <span className="text-gray-400">Endpoint:</span>
                        <span className="font-mono text-cyan-400 truncate max-w-[60%]">{engine.endpoint}</span>
                      </div>
                    )}
                    {engine.scope && (
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-gray-400 shrink-0">Scope:</span>
                        <span className="text-amber-300 text-right font-medium">{engine.scope}</span>
                      </div>
                    )}
                    {engine.reason && (
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-gray-400 shrink-0">Reason:</span>
                        <span className="text-gray-300 text-right">{engine.reason}</span>
                      </div>
                    )}
                    {engine.benchmark && (
                      <div className="flex items-center justify-between">
                        <span className="text-gray-400">Benchmark:</span>
                        <span className="text-violet-300 font-mono">{engine.benchmark}</span>
                      </div>
                    )}
                    {engine.average_gap_pct !== undefined && (
                      <div className="flex items-center justify-between">
                        <span className="text-gray-400">Avg Gap vs Optimal:</span>
                        <span className="text-emerald-300 font-mono font-bold">{engine.average_gap_pct}%</span>
                      </div>
                    )}
                    {engine.product_count !== undefined && (
                      <div className="flex items-center justify-between">
                        <span className="text-gray-400">LCA Products:</span>
                        <span className="text-cyan-300 font-mono">{engine.product_count} categories</span>
                      </div>
                    )}
                    {engine.error && (
                      <div className="mt-2 p-2 rounded-lg bg-rose-950/60 border border-rose-500/30 text-rose-300">
                        <strong className="block text-[10px] uppercase tracking-wider mb-0.5">Error:</strong>
                        {engine.error}
                      </div>
                    )}
                  </div>

                  {/* Model Type Tag */}
                  {engine.model_type && (
                    <div className="pt-2 border-t border-white/5 flex items-center justify-between">
                      <span className="text-[10px] text-gray-500">Model Type</span>
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-white/5 text-gray-300">
                        {engine.model_type}
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};
