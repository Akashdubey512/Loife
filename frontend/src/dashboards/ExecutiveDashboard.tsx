import React, { useEffect, useState } from 'react';
import {
  Scale,
  TrendingDown,
  CloudRain,
  Zap,
  IndianRupee,
  Leaf,
  Users,
  Award,
  DownloadCloud,
  Loader2,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid
} from 'recharts';
import { StatCard } from '../components/StatCard';
import { apiService } from '../services/api';
import { ExecutiveStats } from '../types';
import { useAuth } from '../context/AuthContext';
import storyGreenFuture from '../assets/illustrations/sustainability/story_green_future.png';

export const ExecutiveDashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<ExecutiveStats | null>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  // ESG export state
  const [esgLoading, setEsgLoading] = useState(false);
  const [esgError, setEsgError] = useState<string | null>(null);
  const [esgSuccess, setEsgSuccess] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setStatsLoading(true);
      setStatsError(null);
      try {
        const [statsData, trendsData] = await Promise.all([
          apiService.getExecutiveStats(),
          apiService.getMonthlyTrends()
        ]);
        setStats(statsData);
        setTrends(trendsData);
      } catch (err: any) {
        setStatsError(err?.response?.data?.detail || 'Failed to load executive stats.');
      } finally {
        setStatsLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleExportEsg = async () => {
    if (esgLoading) return;
    setEsgLoading(true);
    setEsgError(null);
    setEsgSuccess(null);
    try {
      const orgId = user?.organization_id ?? 1;
      const report = await apiService.getEsgAuditReport(orgId, 'FY 2026-Q3');

      // Download as JSON (the backend returns a structured JSON report)
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ESG_Report_${report.report_id ?? 'export'}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setEsgSuccess(`ESG report ${report.report_id} downloaded.`);
      setTimeout(() => setEsgSuccess(null), 5000);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setEsgError(typeof detail === 'string' ? detail : 'ESG report export failed. Check API connection.');
      setTimeout(() => setEsgError(null), 8000);
    } finally {
      setEsgLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Export */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Executive ESG &amp; Operations Overview</h1>
          <p className="text-xs text-gray-400 mt-1">
            Aggregate sustainability and operational metrics from the food rescue pipeline.
            {stats && stats.total_food_saved_kg === 0 && (
              <span className="ml-2 text-amber-400">(No verified deliveries yet — data will populate as redistributions are completed.)</span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-gray-300 font-medium">
            Fiscal Period: <span className="text-white font-bold">2026-Q3 (YTD)</span>
          </div>
          <button
            id="export-esg-btn"
            onClick={handleExportEsg}
            disabled={esgLoading}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 disabled:opacity-50 text-emerald-300 border border-emerald-500/40 text-xs font-bold transition"
          >
            {esgLoading
              ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Generating…</>
              : <><DownloadCloud className="h-3.5 w-3.5" /> Export ESG Report</>
            }
          </button>
        </div>
      </div>

      {/* Loife Community Banner: Together, small actions create lasting impact */}
      <div className="loife-surface-sage rounded-2xl p-4 md:p-5 flex flex-col sm:flex-row items-center justify-between gap-4 border border-[#77B7A5]/30">
        <div className="flex items-center gap-4">
          <div className="h-16 w-24 sm:h-20 sm:w-28 rounded-xl overflow-hidden shrink-0 border border-white/10 shadow-md">
            <img
              src={storyGreenFuture}
              alt="Community sustainability impact"
              className="w-full h-full object-cover"
            />
          </div>
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#174C3C]/40 border border-[#F2C45A]/30 text-[#F2C45A] text-[10px] font-bold uppercase tracking-wider mb-1">
              <Sparkles className="h-3 w-3 text-[#F2C45A]" /> Executive Mission
            </div>
            <h2 className="text-base sm:text-lg font-bold text-white">
              Together, small actions create lasting impact.
            </h2>
            <p className="text-xs text-gray-300 max-w-xl mt-0.5">
              Every meal diverted from landfills conserves water, cuts Scope 3 emissions, and directly supports community welfare across university and hospital dining clusters.
            </p>
          </div>
        </div>
        <div className="shrink-0 flex items-center gap-2">
          <div className="text-right hidden md:block">
            <span className="text-[10px] uppercase font-bold text-[#77B7A5] tracking-wider block">LCA Standard</span>
            <span className="text-xs font-mono text-white">Poore &amp; Nemecek 2018</span>
          </div>
        </div>
      </div>

      {/* ESG export feedback */}
      {esgError && (
        <div role="alert" className="flex items-center gap-2 p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs">
          <AlertCircle className="h-4 w-4 shrink-0" /> {esgError}
        </div>
      )}
      {esgSuccess && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs">
          <Award className="h-4 w-4 shrink-0" /> {esgSuccess}
        </div>
      )}

      {/* Stats loading / error */}
      {statsLoading && (
        <div className="flex items-center gap-2 text-gray-400 text-sm">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading stats…
        </div>
      )}
      {statsError && !statsLoading && (
        <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" /> {statsError}
        </div>
      )}

      {/* 6 Core Executive KPI Cards */}
      {!statsLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <StatCard
            title="Total Food Saved"
            value={stats ? `${(stats.total_food_saved_kg / 1000).toFixed(2)} MT` : '—'}
            subtitle={stats?.total_food_saved_kg === 0 ? 'No verified deliveries yet' : 'Rescued from overproduction & expiry'}
            change={stats && stats.total_food_saved_kg > 0 ? '+Live' : ''}
            isPositive={true}
            icon={Scale}
            accentColor="emerald"
          />
          <StatCard
            title="Food Waste Reduction"
            value={stats ? `${stats.waste_reduction_percentage}%` : '—'}
            subtitle="Vs baseline pre-system"
            change=""
            isPositive={true}
            icon={TrendingDown}
            accentColor="cyan"
          />
          <StatCard
            title="Carbon Footprint Avoided"
            value={stats ? `${(stats.carbon_reduction_kg / 1000).toFixed(2)} t CO₂e` : '—'}
            subtitle="Scope 3 supply emissions avoided (estimated)"
            change=""
            isPositive={true}
            icon={Leaf}
            accentColor="emerald"
          />
          <StatCard
            title="Water Footprint Saved"
            value={stats ? `${(stats.water_saved_liters / 1000000).toFixed(3)}M L` : '—'}
            subtitle="Virtual embedded agricultural water (estimated)"
            change=""
            isPositive={true}
            icon={CloudRain}
            accentColor="cyan"
          />
          <StatCard
            title="Energy Efficiency Est."
            value={stats ? `${stats.energy_efficiency_kwh.toLocaleString()} kWh` : '—'}
            subtitle="Proportional to rescued food (estimated)"
            change=""
            isPositive={true}
            icon={Zap}
            accentColor="amber"
          />
          <StatCard
            title="Cost Savings Realised"
            value={stats ? `₹${(stats.operational_cost_savings_inr / 100000).toFixed(2)} Lakh` : '—'}
            subtitle="Based on ₹110/kg food value estimate"
            change=""
            isPositive={true}
            icon={IndianRupee}
            accentColor="violet"
          />
        </div>
      )}

      {/* Main Analytics Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Waste Reduction vs Food Rescue Trajectory */}
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white">Monthly Waste &amp; Rescue Trend</h2>
              <p className="text-xs text-gray-400">Live monthly aggregations from verified database rescue and waste events</p>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5 text-rose-400">
                <span className="h-2.5 w-2.5 rounded-full bg-rose-500" /> Waste Generated
              </span>
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> Rescued &amp; Redistributed
              </span>
            </div>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorRescued" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorWaste" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                <XAxis dataKey="month" stroke="#9ca3af" fontSize={11} />
                <YAxis stroke="#9ca3af" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Area type="monotone" dataKey="food_rescued_kg" stroke="#10b981" strokeWidth={2.5} fillOpacity={1} fill="url(#colorRescued)" name="Rescued (kg)" />
                <Area type="monotone" dataKey="waste_generated_kg" stroke="#f43f5e" strokeWidth={2} fillOpacity={1} fill="url(#colorWaste)" name="Waste (kg)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Social Impact Card — dynamic from stats */}
        <div className="glass-card p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-bold text-white">Social Impact &amp; Meals</h2>
              <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400">
                <Users className="h-4 w-4" />
              </div>
            </div>
            <p className="text-xs text-gray-400 mb-4">
              Contribution to UN SDG 2 (Zero Hunger) &amp; SDG 12 (Responsible Consumption).
            </p>

            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                <span className="text-xs text-gray-400">Meals Served to Beneficiaries</span>
                <p className="text-3xl font-black text-emerald-400 mt-1">
                  {stats ? stats.meals_redistributed.toLocaleString() : '—'}
                </p>
                {stats && stats.meals_redistributed === 0 && (
                  <p className="text-[10px] text-amber-400 mt-1">Pending verified deliveries</p>
                )}
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/5">
                  <span className="text-gray-300">Active Verified Kitchens</span>
                  <span className="text-white font-bold font-mono">{stats?.active_kitchens_monitored ?? '—'}</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/5">
                  <span className="text-gray-300">NGO Partners (DB count)</span>
                  <span className="text-white font-bold font-mono">{stats?.active_ngo_partners ?? '—'}</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/5">
                  <span className="text-gray-300">ESG Score Contribution</span>
                  <span className="text-violet-400 font-bold font-mono">
                    {stats && stats.total_food_saved_kg > 0 ? 'Calculated' : 'Unavailable'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-white/5 flex items-center gap-2 text-[11px] text-gray-400">
            <Award className="h-4 w-4 text-amber-400 shrink-0" />
            <span>Impact figures are system-calculated estimates using Poore &amp; Nemecek (2018) LCA factors.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
