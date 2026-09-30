import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlertCircle, Eye, EyeOff, Loader2, Sparkles, Heart } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getRoleDashboardPath } from '../utils/roleNav';
import { LoifeLogo } from '../components/LoifeLogo';
import { Illustration } from '../components/Illustration';

import authSideArt from '../assets/illustrations/brand/story_small_actions.png';

export const LoginPage: React.FC = () => {
  const { login, isAuthenticated, isLoading, user } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // If already authenticated, redirect to the appropriate dashboard
  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      navigate(getRoleDashboardPath(user.role), { replace: true });
    }
  }, [isAuthenticated, isLoading, user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;

    if (!email.trim() || !password) {
      setError('Email and password are required.');
      return;
    }

    setError(null);
    setSubmitting(true);
    try {
      const loggedInUser = await login(email.trim(), password);
      navigate(getRoleDashboardPath(loggedInUser.role), { replace: true });
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Invalid email or password. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleDemoFill = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#080b11] flex items-center justify-center p-4 md:p-8">
      <div className="w-full max-w-4xl grid md:grid-cols-12 gap-0 rounded-3xl overflow-hidden glass-panel border border-white/10 shadow-2xl">
        
        {/* Left / Top Form Panel */}
        <div className="md:col-span-7 p-8 md:p-10 flex flex-col justify-between">
          <div>
            {/* Brand Logo */}
            <div className="flex items-center justify-between mb-8">
              <Link to="/" className="hover:opacity-90 transition">
                <LoifeLogo size="md" showTagline={false} />
              </Link>
              <Link to="/" className="text-xs text-gray-400 hover:text-white transition">
                ← Back
              </Link>
            </div>

            <div className="mb-6">
              <h1 className="text-2xl font-black text-white">Welcome Back</h1>
              <p className="text-xs md:text-sm text-gray-400 mt-1">
                Sign in to your Loife operations workspace
              </p>
            </div>

            {error && (
              <div
                role="alert"
                className="mb-5 flex items-start gap-2.5 p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-sm"
              >
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} noValidate className="space-y-4">
              <div>
                <label htmlFor="login-email" className="block text-xs font-semibold text-gray-300 mb-1.5">
                  Email Address
                </label>
                <input
                  id="login-email"
                  type="email"
                  autoComplete="email"
                  required
                  placeholder="admin@reserveai.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={submitting}
                  className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder-gray-600 focus:border-[#F2C45A] focus:outline-none focus:ring-1 focus:ring-[#F2C45A]/40 disabled:opacity-50 transition"
                />
              </div>

              <div>
                <label htmlFor="login-password" className="block text-xs font-semibold text-gray-300 mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="login-password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={submitting}
                    className="w-full px-4 py-2.5 pr-10 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder-gray-600 focus:border-[#F2C45A] focus:outline-none focus:ring-1 focus:ring-[#F2C45A]/40 disabled:opacity-50 transition"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <button
                id="login-submit-btn"
                type="submit"
                disabled={submitting}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-[#174C3C] hover:bg-[#145B59] disabled:bg-[#174C3C]/50 text-[#FFF6E8] font-bold text-sm transition shadow-lg shadow-[#174C3C]/40 border border-[#F2C45A]/30 mt-2"
              >
                {submitting ? (
                  <><Loader2 className="h-4 w-4 animate-spin text-[#F2C45A]" /> Signing in…</>
                ) : (
                  'Sign In'
                )}
              </button>
            </form>

            {/* Demo Quick Fill Shortcuts */}
            <div className="mt-6 pt-5 border-t border-white/10">
              <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-[#F2C45A]" /> Quick Demo Logins:
              </p>
              <div className="flex flex-wrap gap-1.5">
                {[
                  { label: 'Admin', email: 'admin@reserveai.com', pass: 'Admin@1234' },
                  { label: 'Kitchen', email: 'kitchen@reserveai.com', pass: 'Kitchen@1234' },
                  { label: 'Quality', email: 'quality@reserveai.com', pass: 'Quality@1234' },
                  { label: 'Logistics', email: 'logistics@reserveai.com', pass: 'Logistics@1234' },
                  { label: 'NGO', email: 'ngo@reserveai.com', pass: 'NGO@1234' },
                ].map((demo) => (
                  <button
                    key={demo.label}
                    type="button"
                    onClick={() => handleDemoFill(demo.email, demo.pass)}
                    className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 transition"
                  >
                    {demo.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <p className="text-center text-xs text-gray-500 mt-6">
            Don't have an account?{' '}
            <Link to="/signup" className="text-[#F2C45A] hover:text-[#F4A261] font-semibold transition">
              Sign up
            </Link>
          </p>
        </div>

        {/* Right Illustrated Side Panel (Visible on Desktop) */}
        <div className="hidden md:flex md:col-span-5 bg-gradient-to-br from-[#174C3C]/50 via-[#145B59]/40 to-[#080b11] p-8 flex-col justify-between border-l border-white/10 relative overflow-hidden">
          <div className="relative z-10">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#F2C45A]/15 border border-[#F2C45A]/30 text-[#F2C45A] text-[11px] font-semibold uppercase tracking-wider mb-4">
              <Heart className="h-3 w-3 text-[#D97757]" /> Nourishment & Care
            </span>
            <h2 className="text-2xl font-black text-white leading-tight">
              Good Food. Shared Life.
            </h2>
            <p className="text-xs text-[#FFF6E8]/75 mt-2 leading-relaxed">
              Every meal saved is dignity preserved and a carbon footprint avoided.
            </p>
          </div>

          <div className="relative z-10 my-4">
            <Illustration
              src={authSideArt}
              alt="Hands sharing a loaf of bread, heart and leaves"
              variant="compact"
              aspectRatio="4:3"
              caption="Small acts of kindness can make a big difference."
            />
          </div>

          <div className="relative z-10 text-[11px] text-gray-400">
            <span>reServe AI is now </span>
            <strong className="text-white">Loife</strong>
            <span className="block text-[10px] text-gray-500">Smart India Hackathon 2026 Enterprise Edition</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
