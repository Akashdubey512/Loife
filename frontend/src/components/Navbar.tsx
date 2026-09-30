import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Leaf,
  Bell,
  ShieldCheck,
  ChevronDown,
  Building2,
  UserCheck,
  LogOut,
  LogIn,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getDefaultTab } from '../utils/roleNav';
import { DashboardTab } from '../types';
import { LoifeLogo } from './LoifeLogo';

interface NavbarProps {
  activeTab: string;
  onSelectPersonaTab?: (tab: DashboardTab) => void;
}

// Demo personas — credentials live only here and are labelled clearly as DEMO shortcuts
const DEMO_PERSONAS = [
  { role: 'SUPER_ADMIN',           email: 'admin@reserveai.com',    password: 'Admin@1234',     name: 'Dr. Vikram Malhotra',  title: 'Sustainability Director & Admin',  initials: 'VM', color: 'from-violet-500 to-indigo-600' },
  { role: 'KITCHEN_MANAGER',       email: 'kitchen@reserveai.com',  password: 'Kitchen@1234',   name: 'Chef Priya Sharma',    title: 'Executive Head Chef',             initials: 'PS', color: 'from-emerald-500 to-teal-600' },
  { role: 'QUALITY_INSPECTOR',     email: 'quality@reserveai.com',  password: 'Quality@1234',   name: 'Aarav Mehta',          title: 'Food Safety & QA Lead',           initials: 'AM', color: 'from-amber-500 to-orange-600' },
  { role: 'LOGISTICS_COORDINATOR', email: 'logistics@reserveai.com',password: 'Logistics@1234', name: 'Rohan Verma',          title: 'Fleet Logistics Dispatcher',      initials: 'RV', color: 'from-blue-500 to-cyan-600' },
  { role: 'NGO_REP',               email: 'ngo@reserveai.com',      password: 'NGO@1234',       name: 'Kabir Singhania',      title: 'Robin Hood Army Representative',  initials: 'KS', color: 'from-rose-500 to-pink-600' },
];

export const Navbar: React.FC<NavbarProps> = ({ activeTab: _activeTab, onSelectPersonaTab }) => {
  const { user, login, logout } = useAuth();
  const navigate = useNavigate();

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [authSuccess, setAuthSuccess] = useState<string | null>(null);
  const [switchError, setSwitchError] = useState<string | null>(null);

  const currentPersona = DEMO_PERSONAS.find((p) => p.role === user?.role) ?? DEMO_PERSONAS[1];

  const handleSelectPersona = async (persona: typeof DEMO_PERSONAS[0]) => {
    setSwitchError(null);
    try {
      const loggedInUser = await login(persona.email, persona.password);
      setAuthSuccess(`[DEMO] Switched to ${persona.name} (${loggedInUser.role})`);
      setDropdownOpen(false);
      if (onSelectPersonaTab) {
        onSelectPersonaTab(getDefaultTab(loggedInUser.role));
      }
      setTimeout(() => setAuthSuccess(null), 3000);
    } catch {
      setSwitchError(`Demo login failed for ${persona.name}. Check backend is running.`);
      setTimeout(() => setSwitchError(null), 5000);
    }
  };

  const handleLogout = () => {
    logout();
    setDropdownOpen(false);
    setAuthSuccess('Logged out successfully');
    setTimeout(() => setAuthSuccess(null), 3000);
    navigate('/');
  };

  return (
    <>
      <header className="sticky top-0 z-50 glass-panel border-b border-white/10 px-6 py-3 flex items-center justify-between">
        {/* Brand & Live Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <LoifeLogo size="md" showTagline={true} />
          </div>

          <div className="hidden lg:flex items-center gap-2 pl-6 border-l border-white/10">
            <Building2 className="h-4 w-4 text-emerald-400" />
            <span className="text-xs font-semibold text-gray-200">Apex University Dining Cluster</span>
            <ChevronDown className="h-3 w-3 text-gray-400" />
          </div>
        </div>

        {/* Right Controls & Profile */}
        <div className="flex items-center gap-3">
          {/* Alerts notification icon */}
          <button className="relative p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white transition">
            <Bell className="h-4 w-4" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-amber-400 animate-ping" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-amber-400" />
          </button>

          {/* User Profile & Persona Switcher */}
          {user ? (
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-3 pl-3 border-l border-white/10 hover:opacity-90 transition focus:outline-none"
              >
                <div
                  className={`h-9 w-9 rounded-full bg-gradient-to-br ${currentPersona.color} flex items-center justify-center font-bold text-white text-xs ring-2 ring-emerald-500/40 shadow-inner`}
                >
                  {user.full_name
                    ? user.full_name
                        .split(' ')
                        .map((n) => n[0])
                        .join('')
                        .slice(0, 2)
                    : 'U'}
                </div>
                <div className="hidden md:block text-left">
                  <p className="text-xs font-semibold text-white leading-none">{user.full_name}</p>
                  <p className="text-[10px] text-emerald-400 font-medium mt-0.5 flex items-center gap-1">
                    <ShieldCheck className="h-3 w-3 inline" />
                    {user.role}
                  </p>
                </div>
                <ChevronDown className={`h-3 w-3 text-gray-400 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Dropdown */}
              {dropdownOpen && (
                <div className="absolute right-0 mt-3 w-72 glass-panel border border-white/15 rounded-2xl shadow-2xl p-2 z-50 backdrop-blur-2xl">
                  <div className="px-3 py-2 border-b border-white/10 mb-2">
                    <p className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                      Demo Persona Switcher
                    </p>
                    <p className="text-xs text-amber-400 font-medium mt-0.5">
                      For SIH demonstration only
                    </p>
                  </div>

                  <div className="space-y-1">
                    {DEMO_PERSONAS.map((persona) => {
                      const isSelected = user?.role === persona.role;
                      return (
                        <button
                          key={persona.role}
                          onClick={() => handleSelectPersona(persona)}
                          className={`w-full text-left p-2 rounded-xl flex items-center gap-2.5 transition ${
                            isSelected
                              ? 'bg-emerald-500/20 border border-emerald-500/40 text-white'
                              : 'hover:bg-white/5 text-gray-300'
                          }`}
                        >
                          <div
                            className={`h-7 w-7 rounded-lg bg-gradient-to-br ${persona.color} flex items-center justify-center font-bold text-white text-[10px] shrink-0`}
                          >
                            {persona.initials}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold truncate text-white">{persona.name}</p>
                            <p className="text-[10px] text-gray-400 truncate">{persona.title}</p>
                          </div>
                          {isSelected && <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />}
                        </button>
                      );
                    })}
                  </div>

                  <div className="pt-2 border-t border-white/10 mt-2">
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-rose-400 hover:bg-rose-500/10 flex items-center gap-2"
                    >
                      <LogOut className="h-3.5 w-3.5 text-rose-400" /> Sign Out
                    </button>
                  </div>

                  {switchError && (
                    <div className="mt-2 px-3 py-2 rounded-lg bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs">
                      {switchError}
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 pl-3 border-l border-white/10">
              <button
                onClick={() => navigate('/login')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-gray-300 hover:text-white border border-white/10 hover:bg-white/5 transition"
              >
                <LogIn className="h-3.5 w-3.5" /> Log In
              </button>
              <button
                onClick={() => navigate('/signup')}
                className="px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-gray-950 transition"
              >
                Sign Up
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Floating Feedback Toast */}
      {authSuccess && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-xl bg-emerald-950 border border-emerald-500/50 text-emerald-300 text-xs shadow-2xl">
          <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
          <span>{authSuccess}</span>
        </div>
      )}
    </>
  );
};
