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
  DownloadCloud
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid 
} from 'recharts';
import { StatCard } from '../components/StatCard';
import { apiService } from '../services/api';
import { ExecutiveStats } from '../types';

export const ExecutiveDashboard: React.FC = () => {
  const [stats, setStats] = useState<ExecutiveStats | null>(null);
  const [trends, setTrends] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      const [statsData, trendsData] = await Promise.all([
        apiService.getExecutiveStats(),
        apiService.getMonthlyTrends()
      ]);
      setStats(statsData);
      setTrends(trendsData);
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner & Date Filter */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Executive ESG & Operations Overview</h1>
          <p className="text-xs text-gray-400 mt-1">
            Real-time aggregate telemetry across 6 institutional dining halls and processing units.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-gray-300 font-medium">
            Fiscal Period: <span className="text-white font-bold">2026-Q3 (YTD)</span>
          </div>
          <button className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 text-xs font-bold transition">
            <DownloadCloud className="h-3.5 w-3.5" />
            <span>Export ESG Report</span>
          </button>
        </div>
      </div>

      {/* 6 Core Executive KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          title="Total Food Saved"
          value={stats ? `${(stats.total_food_saved_kg / 1000).toFixed(1)} MT` : '14.3 MT'}
          subtitle="Rescued from overproduction & expiry"
          change="+24.8%"
          isPositive={true}
          icon={Scale}
          accentColor="emerald"
        />
        <StatCard
          title="Food Waste Reduction"
          value={stats ? `${stats.waste_reduction_percentage}%` : '38.2%'}
          subtitle="Vs baseline pre-AI implementation"
          change="-38.2%"
          isPositive={true}
          icon={TrendingDown}
          accentColor="cyan"
        />
        <StatCard
          title="Carbon Footprint Avoided"
          value={stats ? `${(stats.carbon_reduction_kg / 1000).toFixed(1)} t CO2e` : '35.6 t'}
          subtitle="Scope 3 supply emissions avoided"
          change="+18.5%"
          isPositive={true}
          icon={Leaf}
          accentColor="emerald"
        />
        <StatCard
          title="Water Footprint Saved"
          value={stats ? `${(stats.water_saved_liters / 1000000).toFixed(2)}M L` : '7.84M L'}
          subtitle="Virtual embedded agricultural water"
          change="+22.1%"
          isPositive={true}
          icon={CloudRain}
          accentColor="cyan"
        />
        <StatCard
          title="Energy Saved"
          value={stats ? `${stats.energy_efficiency_kwh.toLocaleString()} kWh` : '12,400 kWh'}
          subtitle="Smart chiller & thermal optimization"
          change="+14.2%"
          isPositive={true}
          icon={Zap}
          accentColor="amber"
        />
        <StatCard
          title="Cost Savings Realized"
          value={stats ? `₹${(stats.operational_cost_savings_inr / 100000).toFixed(2)} Lakh` : '₹15.68 Lakh'}
          subtitle="Procurement efficiency & tax credits"
          change="+31.4%"
          isPositive={true}
          icon={IndianRupee}
          accentColor="violet"
        />
      </div>

      {/* Main Analytics Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Waste Reduction vs Food Rescue Trajectory */}
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white">Monthly Waste Reduction & Food Rescued</h2>
              <p className="text-xs text-gray-400">Trajectory demonstrating inversion of waste generation vs rescue capacity (kg)</p>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5 text-rose-400">
                <span className="h-2.5 w-2.5 rounded-full bg-rose-500"></span> Waste Generated
              </span>
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500"></span> Rescued & Redistributed
              </span>
            </div>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorRescued" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                  </linearGradient>
                  <linearGradient id="colorWaste" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0}/>
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

        {/* Social Impact & NGO Partners Card */}
        <div className="glass-card p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-bold text-white">Social Impact & Meals</h2>
              <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400">
                <Users className="h-4 w-4" />
              </div>
            </div>
            <p className="text-xs text-gray-400 mb-4">Direct contribution to UN SDG 2 (Zero Hunger) & SDG 12 (Responsible Consumption).</p>

            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                <span className="text-xs text-gray-400">Vulnerable Meals Served</span>
                <p className="text-3xl font-black text-emerald-400 mt-1">28,500+</p>
                <div className="w-full bg-gray-700/40 h-2 rounded-full mt-2.5 overflow-hidden">
                  <div className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full" style={{ width: '82%' }}></div>
                </div>
                <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                  <span>Target: 35,000</span>
                  <span className="text-emerald-400 font-bold">81.4% achieved</span>
                </div>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/5">
                  <span className="text-gray-300">Active Verified NGOs</span>
                  <span className="text-white font-bold font-mono">14 Partners</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/5">
                  <span className="text-gray-300">Redistribution Latency</span>
                  <span className="text-emerald-400 font-bold font-mono">42 min avg</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/5">
                  <span className="text-gray-300">ESG Compliance Index</span>
                  <span className="text-violet-400 font-bold font-mono">Tier A (94.2)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-white/5 flex items-center gap-2 text-[11px] text-gray-400">
            <Award className="h-4 w-4 text-amber-400 shrink-0" />
            <span>Audited under ISO 14001 & GHG Protocol Scope 3 Standard.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
