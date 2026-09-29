import React from 'react';
import { 
  LayoutDashboard, 
  ChefHat, 
  Scan, 
  HeartHandshake, 
  Truck, 
  BarChart3,
  Cpu
} from 'lucide-react';
import { DashboardTab } from '../types';

interface SidebarProps {
  currentTab: DashboardTab;
  onSelectTab: (tab: DashboardTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const navItems: Array<{ id: DashboardTab; label: string; icon: React.FC<{ className?: string }>; badge?: string }> = [
    { id: 'executive', label: 'Executive Overview', icon: LayoutDashboard },
    { id: 'kitchen', label: 'Kitchen & Demand AI', icon: ChefHat, badge: '5 Batches' },
    { id: 'quality', label: 'CV Freshness Scan', icon: Scan, badge: 'CNN B0' },
    { id: 'redistribution', label: 'Redistribution Hub', icon: HeartHandshake, badge: '2 Ready' },
    { id: 'logistics', label: 'Logistics & Routes', icon: Truck, badge: 'Live GPS' },
    { id: 'sustainability', label: 'Sustainability & ESG', icon: BarChart3, badge: 'Scope 1-3' },
  ];

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
                {item.badge && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                    isActive ? 'bg-emerald-400/20 text-emerald-300' : 'bg-white/5 text-gray-400'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer System Status Card */}
      <div className="p-3.5 rounded-xl bg-gradient-to-br from-emerald-950/30 to-gray-900/60 border border-emerald-500/20">
        <div className="flex items-center gap-2 mb-1.5">
          <Cpu className="h-4 w-4 text-emerald-400" />
          <span className="text-xs font-bold text-gray-200">ML Model Mesh</span>
        </div>
        <div className="space-y-1 text-[11px] text-gray-400">
          <div className="flex justify-between">
            <span>Demand Engine:</span>
            <span className="text-emerald-400 font-mono">LightGBM 94.2%</span>
          </div>
          <div className="flex justify-between">
            <span>CV Model:</span>
            <span className="text-cyan-400 font-mono">EfficientNet-B0</span>
          </div>
          <div className="flex justify-between">
            <span>VRP Routing:</span>
            <span className="text-indigo-400 font-mono">OR-Tools v9.8</span>
          </div>
        </div>
        <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-gray-500">
          <span>PostgreSQL 15</span>
          <span className="text-emerald-400 flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span> Connected
          </span>
        </div>
      </div>
    </aside>
  );
};
