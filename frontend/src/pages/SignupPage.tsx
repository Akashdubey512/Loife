import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlertCircle, CheckCircle2, Eye, EyeOff, Loader2, Heart, Users } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { LoifeLogo } from '../components/LoifeLogo';
import { Illustration } from '../components/Illustration';

import signupSideArt from '../assets/illustrations/community/story_community_dining.png';

const PASSWORD_MIN = 8;

export const SignupPage: React.FC = () => {
  const { signup, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Already authenticated → redirect to dashboard
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  const validateEmail = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;

    // Client-side validation
    if (!fullName.trim()) { setError('Full name is required.'); return; }
    if (!email.trim()) { setError('Email address is required.'); return; }
    if (!validateEmail(email.trim())) { setError('Please enter a valid email address.'); return; }
    if (password.length < PASSWORD_MIN) { setError(`Password must be at least ${PASSWORD_MIN} characters.`); return; }
    if (password !== confirmPassword) { setError('Passwords do not match.'); return; }

    setError(null);
    setSubmitting(true);
    try {
      await signup({ email: email.trim(), password, full_name: fullName.trim() });
      setSuccess(true);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Registration failed. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-[#080b11] flex items-center justify-center p-4">
        <div className="w-full max-w-md text-center">
          <div className="glass-panel rounded-3xl p-8 border border-white/10">
            <div className="h-14 w-14 rounded-2xl bg-[#174C3C]/40 border border-[#F2C45A]/40 flex items-center justify-center mx-auto mb-5">
              <CheckCircle2 className="h-7 w-7 text-[#F2C45A]" />
            </div>
            <h1 className="text-2xl font-black text-white mb-2">Welcome to Loife</h1>
            <p className="text-sm text-gray-300 mb-6 leading-relaxed">
              Your account has been created. An administrator will assign your operational role.
              You can log in with your credentials right away.
            </p>
            <Link
              to="/login"
              id="signup-success-login-btn"
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#174C3C] hover:bg-[#145B59] text-[#FFF6E8] font-bold text-sm transition shadow-lg shadow-[#174C3C]/40 border border-[#F2C45A]/30"
            >
              Proceed to Sign In
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#080b11] flex items-center justify-center p-4 md:p-8">
      <div className="w-full max-w-4xl grid md:grid-cols-12 gap-0 rounded-3xl overflow-hidden glass-panel border border-white/10 shadow-2xl">
        
        {/* Form Column */}
        <div className="md:col-span-7 p-8 md:p-10 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-8">
              <Link to="/" className="hover:opacity-90 transition">
                <LoifeLogo size="md" showTagline={false} />
              </Link>
              <Link to="/" className="text-xs text-gray-400 hover:text-white transition">
                ← Back
              </Link>
            </div>

            <div className="mb-6">
              <h1 className="text-2xl font-black text-white">Create an Account</h1>
              <p className="text-xs md:text-sm text-gray-400 mt-1">
                Register to join the Loife circular redistribution network
              </p>
            </div>

            {/* Role note */}
            <div className="mb-5 p-3 rounded-xl bg-[#174C3C]/30 border border-[#77B7A5]/30 text-xs text-[#E8F2EC] leading-relaxed">
              <strong className="text-[#F2C45A]">Note:</strong> Public signup creates standard user access. Kitchen managers, inspectors, and NGO representatives receive role privileges from their organisation administrator.
            </div>

            {error && (
              <div role="alert" className="mb-5 flex items-start gap-2.5 p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-sm">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} noValidate className="space-y-4">
              <div>
                <label htmlFor="signup-name" className="block text-xs font-semibold text-gray-300 mb-1.5">Full Name</label>
                <input
                  id="signup-name"
                  type="text"
                  autoComplete="name"
                  required
                  placeholder="Chef Priya Sharma"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={submitting}
                  className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder-gray-600 focus:border-[#F2C45A] focus:outline-none focus:ring-1 focus:ring-[#F2C45A]/40 disabled:opacity-50 transition"
                />
              </div>

              <div>
                <label htmlFor="signup-email" className="block text-xs font-semibold text-gray-300 mb-1.5">Email Address</label>
                <input
                  id="signup-email"
                  type="email"
                  autoComplete="email"
                  required
                  placeholder="priya@kitchen.org"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={submitting}
                  className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder-gray-600 focus:border-[#F2C45A] focus:outline-none focus:ring-1 focus:ring-[#F2C45A]/40 disabled:opacity-50 transition"
                />
              </div>

              <div>
                <label htmlFor="signup-password" className="block text-xs font-semibold text-gray-300 mb-1.5">
                  Password <span className="text-gray-500 font-normal">(min. {PASSWORD_MIN} characters)</span>
                </label>
                <div className="relative">
                  <input
                    id="signup-password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    minLength={PASSWORD_MIN}
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

              <div>
                <label htmlFor="signup-confirm-password" className="block text-xs font-semibold text-gray-300 mb-1.5">Confirm Password</label>
                <input
                  id="signup-confirm-password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={submitting}
                  className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder-gray-600 focus:border-[#F2C45A] focus:outline-none focus:ring-1 focus:ring-[#F2C45A]/40 disabled:opacity-50 transition"
                />
              </div>

              <button
                id="signup-submit-btn"
                type="submit"
                disabled={submitting}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-[#174C3C] hover:bg-[#145B59] disabled:bg-[#174C3C]/50 text-[#FFF6E8] font-bold text-sm transition shadow-lg shadow-[#174C3C]/40 border border-[#F2C45A]/30 mt-3"
              >
                {submitting ? (
                  <><Loader2 className="h-4 w-4 animate-spin text-[#F2C45A]" /> Creating account…</>
                ) : (
                  'Create Account'
                )}
              </button>
            </form>
          </div>

          <p className="text-center text-xs text-gray-500 mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-[#F2C45A] hover:text-[#F4A261] font-semibold transition">Log in</Link>
          </p>
        </div>

        {/* Right Illustrated Side Panel */}
        <div className="hidden md:flex md:col-span-5 bg-gradient-to-br from-[#174C3C]/50 via-[#145B59]/40 to-[#080b11] p-8 flex-col justify-between border-l border-white/10 relative overflow-hidden">
          <div className="relative z-10">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#77B7A5]/15 border border-[#77B7A5]/30 text-[#77B7A5] text-[11px] font-semibold uppercase tracking-wider mb-4">
              <Users className="h-3 w-3 text-[#F2C45A]" /> Community Network
            </span>
            <h2 className="text-2xl font-black text-white leading-tight">
              Good Food Builds Stronger Communities
            </h2>
            <p className="text-xs text-[#FFF6E8]/75 mt-2 leading-relaxed">
              Join kitchens, charities, and dispatchers making every meal count across campus and city clusters.
            </p>
          </div>

          <div className="relative z-10 my-4">
            <Illustration
              src={signupSideArt}
              alt="Diverse people dining together at a welcoming community table"
              variant="compact"
              aspectRatio="4:3"
              caption="Together, we make every meal count."
            />
          </div>

          <div className="relative z-10 text-[11px] text-gray-400">
            <span>Powered by </span>
            <strong className="text-white">Loife</strong>
            <span className="block text-[10px] text-gray-500">SIH 2026 Enterprise Edition</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
