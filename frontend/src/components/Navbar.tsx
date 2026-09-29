import React, { useState, useEffect } from 'react';
import { 
  Leaf, 
  Bell, 
  ShieldCheck, 
  ChevronDown, 
  Radio, 
  Building2,
  UserCheck,
  LogOut,
  LogIn,
  KeyRound,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { apiService } from '../services/api';
import { AuthUser } from '../types';

interface NavbarProps {
  activeTab: string;
}

interface DemoPersona {
  role: string;
  name: string;
  title: string;
  email: string;
  password: string;
  initials: string;
  color: string;
}

const DEMO_PERSONAS: DemoPersona[] = [
  {
    role: 'SUPER_ADMIN',
    name: 'Dr. Vikram Malhotra',
    title: 'Sustainability Director & Admin',
    email: 'admin@reserveai.com',
    password: 'Admin@1234',
    initials: 'VM',
    color: 'from-violet-500 to-indigo-600'
  },
  {
    role: 'KITCHEN_MANAGER',
    name: 'Chef Priya Sharma',
    title: 'Executive Head Chef',
    email: 'kitchen@reserveai.com',
    password: 'Kitchen@1234',
    initials: 'PS',
    color: 'from-emerald-500 to-teal-600'
  },
  {
    role: 'QUALITY_INSPECTOR',
    name: 'Aarav Mehta',
    title: 'Food Safety & QA Lead',
    email: 'quality@reserveai.com',
    password: 'Quality@1234',
    initials: 'AM',
    color: 'from-amber-500 to-orange-600'
  },
  {
    role: 'LOGISTICS_COORDINATOR',
    name: 'Rohan Verma',
    title: 'Fleet Logistics Dispatcher',
    email: 'logistics@reserveai.com',
    password: 'Logistics@1234',
    initials: 'RV',
    color: 'from-blue-500 to-cyan-600'
  },
  {
    role: 'NGO_REP',
    name: 'Kabir Singhania',
    title: 'Robin Hood Army Representative',
    email: 'ngo@reserveai.com',
    password: 'NGO@1234',
    initials: 'KS',
    color: 'from-rose-500 to-pink-600'
  }
];

export const Navbar: React.FC<NavbarProps> = ({ activeTab: _activeTab }) => {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const [customEmail, setCustomEmail] = useState('');
  const [customPassword, setCustomPassword] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [authSuccess, setAuthSuccess] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState<boolean>(() => typeof window !== 'undefined' && localStorage.getItem('reserve_demo_mode') === 'true');

  const toggleDemoMode = () => {
    const nextVal = !demoMode;
    setDemoMode(nextVal);
    if (typeof window !== 'undefined') {
      localStorage.setItem('reserve_demo_mode', String(nextVal));
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('reserve_token');
      if (token) {
        try {
          const profile = await apiService.getMe();
          setCurrentUser(profile);
          return;
        } catch {
          localStorage.removeItem('reserve_token');
        }
      }
      // Auto-authenticate as default Chef Priya Sharma (Kitchen Manager) or Admin
      try {
        const res = await apiService.login('kitchen@reserveai.com', 'Kitchen@1234');
        if (res.user) {
          setCurrentUser(res.user);
        }
      } catch {
        // Fallback default persona state
        setCurrentUser({
          id: 2,
          email: 'kitchen@reserveai.com',
          full_name: 'Chef Priya Sharma',
          role: 'KITCHEN_MANAGER',
          organization_id: 1,
          is_active: true
        });
      }
    };
    initAuth();
  }, []);

  const handleSelectPersona = async (persona: DemoPersona) => {
    setAuthError(null);
    try {
      const res = await apiService.login(persona.email, persona.password);
      setCurrentUser(res.user);
      setAuthSuccess(`Switched persona to ${persona.name} (${persona.role})`);
      setDropdownOpen(false);
      setTimeout(() => setAuthSuccess(null), 3000);
    } catch {
      // In local offline fallback mode
      setCurrentUser({
        id: 1,
        email: persona.email,
        full_name: persona.name,
        role: persona.role,
        organization_id: 1,
        is_active: true
      });
      setAuthSuccess(`Switched persona to ${persona.name} (${persona.role})`);
      setDropdownOpen(false);
      setTimeout(() => setAuthSuccess(null), 3000);
    }
  };

  const handleCustomLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    try {
      const res = await apiService.login(customEmail, customPassword);
      setCurrentUser(res.user);
      setLoginModalOpen(false);
      setAuthSuccess(`Successfully logged in as ${res.user.full_name}`);
      setTimeout(() => setAuthSuccess(null), 3000);
    } catch (err: any) {
      setAuthError(err.response?.data?.detail || 'Invalid email or password');
    }
  };

  const handleLogout = () => {
    apiService.logout();
    setCurrentUser(null);
    setDropdownOpen(false);
    setAuthSuccess('Logged out successfully');
    setTimeout(() => setAuthSuccess(null), 3000);
  };

  const currentPersona = DEMO_PERSONAS.find(p => p.role === currentUser?.role) || DEMO_PERSONAS[0];

  return (
    <>
      <header className="sticky top-0 z-50 glass-panel border-b border-white/10 px-6 py-3 flex items-center justify-between">
        {/* Brand & Live Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <Leaf className="h-5 w-5 text-gray-950 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-gray-100 to-gray-300 bg-clip-text text-transparent">
                  reServe<span className="text-emerald-400 font-black">AI</span>
                </span>
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  SIH 2026 Enterprise
                </span>
              </div>
              <p className="text-xs text-gray-400 flex items-center gap-1.5 font-medium">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 pulse-beacon"></span>
                Autonomous Food Waste & Redistribution System
              </p>
            </div>
          </div>

          <div className="hidden lg:flex items-center gap-2 pl-6 border-l border-white/10">
            <Building2 className="h-4 w-4 text-emerald-400" />
            <span className="text-xs font-semibold text-gray-200">Apex University Dining Cluster</span>
            <ChevronDown className="h-3 w-3 text-gray-400" />
          </div>
        </div>

        {/* Right Controls & Profile */}
        <div className="flex items-center gap-3">
          {/* Live Stack / Demo Mode Toggle */}
          <button
            onClick={toggleDemoMode}
            title="Toggle between Live Production Stack and Simulated Offline Demo Mode"
            className={`hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono border transition ${
              demoMode
                ? 'bg-amber-950/50 border-amber-500/50 text-amber-300 hover:bg-amber-900/50 shadow-sm shadow-amber-500/10'
                : 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400 hover:bg-emerald-900/30'
            }`}
          >
            <span className={`h-2 w-2 rounded-full ${demoMode ? 'bg-amber-400' : 'bg-emerald-400 pulse-beacon'}`}></span>
            <span>{demoMode ? 'Mode: Simulated Demo' : 'Mode: Live Stack'}</span>
          </button>

          {/* Telemetry pill */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
            <Radio className="h-3.5 w-3.5 animate-pulse text-emerald-400" />
            <span>IoT Gateway: Live (12ms)</span>
          </div>

          {/* Alerts notification icon */}
          <button className="relative p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white transition">
            <Bell className="h-4 w-4" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-amber-400 animate-ping"></span>
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-amber-400"></span>
          </button>

          {/* User Profile & Persona Switcher */}
          <div className="relative">
            <button 
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-3 pl-3 border-l border-white/10 hover:opacity-90 transition focus:outline-none"
            >
              <div className={`h-9 w-9 rounded-full bg-gradient-to-br ${currentPersona.color} flex items-center justify-center font-bold text-white text-xs ring-2 ring-emerald-500/40 shadow-inner`}>
                {currentUser?.full_name ? currentUser.full_name.split(' ').map(n => n[0]).join('').slice(0, 2) : 'AI'}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-xs font-semibold text-white leading-none">
                  {currentUser?.full_name || 'Guest User'}
                </p>
                <p className="text-[10px] text-emerald-400 font-medium mt-0.5 flex items-center gap-1">
                  <ShieldCheck className="h-3 w-3 inline" />
                  {currentUser?.role || 'DEMO_MODE'}
                </p>
              </div>
              <ChevronDown className={`h-3 w-3 text-gray-400 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Persona Switcher Dropdown */}
            {dropdownOpen && (
              <div className="absolute right-0 mt-3 w-72 glass-panel border border-white/15 rounded-2xl shadow-2xl p-2 z-50 backdrop-blur-2xl">
                <div className="px-3 py-2 border-b border-white/10 mb-2">
                  <p className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">Switch Persona / Test Role</p>
                  <p className="text-xs text-emerald-400 font-medium mt-0.5">Instant RBAC Demonstration</p>
                </div>

                <div className="space-y-1">
                  {DEMO_PERSONAS.map((persona) => {
                    const isSelected = currentUser?.role === persona.role;
                    return (
                      <button
                        key={persona.role}
                        onClick={() => handleSelectPersona(persona)}
                        className={`w-full text-left p-2 rounded-xl flex items-center gap-2.5 transition ${
                          isSelected ? 'bg-emerald-500/20 border border-emerald-500/40 text-white' : 'hover:bg-white/5 text-gray-300'
                        }`}
                      >
                        <div className={`h-7 w-7 rounded-lg bg-gradient-to-br ${persona.color} flex items-center justify-center font-bold text-white text-[10px] shrink-0`}>
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

                <div className="pt-2 border-t border-white/10 mt-2 space-y-1">
                  <button
                    onClick={() => { setDropdownOpen(false); setLoginModalOpen(true); }}
                    className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-gray-300 hover:text-white hover:bg-white/5 flex items-center gap-2"
                  >
                    <LogIn className="h-3.5 w-3.5 text-cyan-400" /> Custom Credentials Login
                  </button>
                  {currentUser && (
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-rose-400 hover:bg-rose-500/10 flex items-center gap-2"
                    >
                      <LogOut className="h-3.5 w-3.5 text-rose-400" /> Sign Out
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Floating Feedback Toast */}
      {authSuccess && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-xl bg-emerald-950 border border-emerald-500/50 text-emerald-300 text-xs shadow-2xl animate-in fade-in slide-in-from-bottom-3 duration-300">
          <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
          <span>{authSuccess}</span>
        </div>
      )}

      {/* Custom Login Modal */}
      {loginModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4">
          <div className="glass-panel border border-white/15 rounded-3xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
              <div className="flex items-center gap-2">
                <KeyRound className="h-5 w-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white">Manual Account Login</h3>
              </div>
              <button 
                onClick={() => setLoginModalOpen(false)}
                className="text-gray-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCustomLogin} className="space-y-4">
              {authError && (
                <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{authError}</span>
                </div>
              )}

              <div>
                <label className="text-xs text-gray-300 font-semibold block mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="chef@reserveai.com"
                  value={customEmail}
                  onChange={(e) => setCustomEmail(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-xs focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs text-gray-300 font-semibold block mb-1">Password</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={customPassword}
                  onChange={(e) => setCustomPassword(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-xs focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setLoginModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs text-gray-400 hover:text-white hover:bg-white/5"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-gray-950 shadow-lg shadow-emerald-500/20"
                >
                  Sign In
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
