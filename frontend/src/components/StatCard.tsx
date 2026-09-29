import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  change?: string;
  isPositive?: boolean;
  icon: React.FC<{ className?: string }>;
  accentColor?: 'emerald' | 'cyan' | 'violet' | 'amber';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  change,
  isPositive = true,
  icon: Icon,
  accentColor = 'emerald'
}) => {
  const colorMap = {
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20 group-hover:border-emerald-500/40',
    cyan: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20 group-hover:border-cyan-500/40',
    violet: 'text-violet-400 bg-violet-500/10 border-violet-500/20 group-hover:border-violet-500/40',
    amber: 'text-amber-400 bg-amber-500/10 border-amber-500/20 group-hover:border-amber-500/40',
  };

  return (
    <div className="glass-card p-5 rounded-2xl relative overflow-hidden group">
      {/* Background glow spot */}
      <div className="absolute -top-12 -right-12 w-28 h-28 bg-white/5 rounded-full blur-2xl group-hover:bg-white/10 transition-all pointer-events-none" />

      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-gray-400 tracking-wide uppercase">{title}</span>
        <div className={`p-2.5 rounded-xl border transition-all ${colorMap[accentColor]}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>

      <div className="flex items-baseline gap-2">
        <h3 className="text-2xl lg:text-3xl font-black tracking-tight text-white">{value}</h3>
        {change && (
          <span className={`text-xs font-bold flex items-center px-1.5 py-0.5 rounded ${
            isPositive ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'
          }`}>
            {isPositive ? <ArrowUpRight className="h-3 w-3 inline mr-0.5" /> : <ArrowDownRight className="h-3 w-3 inline mr-0.5" />}
            {change}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="text-xs text-gray-400 mt-1.5 font-medium">{subtitle}</p>
      )}
    </div>
  );
};
