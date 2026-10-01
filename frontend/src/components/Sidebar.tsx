import React from 'react';
import {
  LayoutDashboard,
  ChefHat,
  Scan,
  HeartHandshake,
  Truck,
  BarChart3,
  Cpu,
} from 'lucide-react';
import { DashboardTab } from '../types';
import { useAuth } from '../context/AuthContext';
import { getAllowedTabs } from '../utils/roleNav';

interface SidebarProps {
  currentTab: DashboardTab;
  onSelectTab: (tab: DashboardTab) => void;
}

const ALL_NAV_ITEMS: Array<{ id: DashboardTab; label: string; icon: React.FC<{ className?: string }> }> = [
  { id: 'executive',      label: 'Executive Overview',  icon: LayoutDashboard },
  { id: 'kitchen',        label: 'Kitchen & Demand',    icon: ChefHat },
  { id: 'quality',        label: 'CV Freshness Scan',   icon: Scan },
  { id: 'redistribution', label: 'Redistribution Hub',  icon: HeartHandshake },
  { id: 'logistics',      label: 'Logistics & Routes',  icon: Truck },
  { id: 'sustainability', label: 'Sustainability & ESG', icon: BarChart3 },
  { id: 'ml_status',      label: 'ML Engine Status',    icon: Cpu },
];

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const { user } = useAuth();
  const allowedTabs = user ? getAllowedTabs(user.role) : ['executive'];

  // Only show nav items the current role is permitted to see
  const navItems = ALL_NAV_ITEMS.filter((item) => allowedTabs.includes(item.id));

  return (
    <aside className="w-64 glass-panel border-r border-white/10 flex flex-col justify-between p-4 shrink-0 min-h-[calc(100vh-61px)]">
      <div>
        <div className="text-[11px] font-bold text-gray-500 uppercase tracking-wider px-3 mb-2">
          Operations Command
        </div>
        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                id={`sidebar-tab-${item.id}`}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-emerald-500/20 to-teal-500/10 text-emerald-300 border border-emerald-500/40 shadow-sm shadow-emerald-500/10'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`h-4 w-4 ${isActive ? 'text-emerald-400' : 'text-gray-400'}`} />
                  <span>{item.label}</span>
                </div>

              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer System Status Card — honest labels */}
      <div className="p-3.5 rounded-xl bg-gradient-to-br from-emerald-950/30 to-gray-900/60 border border-emerald-500/20">
        <div className="flex items-center gap-2 mb-1.5">
          <Cpu className="h-4 w-4 text-emerald-400" />
          <span className="text-xs font-bold text-gray-200">Inference Engine Status</span>
        </div>
        <div className="space-y-1 text-[11px] text-gray-400">
          <div className="flex justify-between">
            <span>Demand Engine:</span>
            <span className="text-emerald-400 font-mono">Heuristic v1.4</span>
          </div>

          <div className="flex justify-between">
            <span>Route Planner:</span>
            <span className="text-indigo-400 font-mono">Greedy Heuristic</span>
          </div>
        </div>
        <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-gray-500">
          <span>SQLite (Dev DB)</span>
          <span className="text-emerald-400 flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Connected
          </span>
        </div>
      </div>
    </aside>
  );
};
