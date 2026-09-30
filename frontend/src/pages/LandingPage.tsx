import React from 'react';
import { Link } from 'react-router-dom';
import {
  ChefHat, Scan, HeartHandshake, Truck, BarChart3,
  ArrowRight, Globe, TrendingDown, Users, Sparkles,
  LayoutDashboard, Heart, Sprout
} from 'lucide-react';
import { LoifeLogo } from '../components/LoifeLogo';
import { Illustration } from '../components/Illustration';

// Artwork imports
import heroBreadSharing from '../assets/illustrations/brand/hero_bread_sharing.png';
import storyParkBench from '../assets/illustrations/community/story_park_bench_icecream.png';
import storyCommunityDining from '../assets/illustrations/community/story_community_dining.png';
import storyThaliMindful from '../assets/illustrations/food/story_thali_mindful.png';
import storyGreenFuture from '../assets/illustrations/sustainability/story_green_future.png';
import storySmallActions from '../assets/illustrations/brand/story_small_actions.png';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#080b11] text-gray-100 flex flex-col font-sans overflow-x-hidden selection:bg-[#F2C45A]/30 selection:text-[#FFF6E8]">
      {/* ── Top Navigation ── */}
      <nav className="sticky top-0 z-50 glass-panel border-b border-white/10 px-6 py-3 flex items-center justify-between backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <Link to="/" className="hover:opacity-95 transition">
            <LoifeLogo size="md" showTagline={false} />
          </Link>
        </div>

        <div className="hidden md:flex items-center gap-7 text-sm text-gray-400 font-medium">
          <a href="#stories" className="hover:text-[#F2C45A] transition flex items-center gap-1.5">
            <Heart className="h-3.5 w-3.5 text-[#F2C45A]" /> Stories
          </a>
          <a href="#solution" className="hover:text-white transition">Solution</a>
          <a href="#workflow" className="hover:text-white transition">Workflow</a>
          <a href="#roles" className="hover:text-white transition">Roles</a>
          <a href="#impact" className="hover:text-[#77B7A5] transition flex items-center gap-1.5">
            <Sprout className="h-3.5 w-3.5 text-[#77B7A5]" /> Sustainability
          </a>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/login"
            id="nav-login-btn"
            className="px-4 py-2 rounded-xl text-sm font-semibold text-gray-300 hover:text-white border border-white/10 hover:bg-white/5 transition"
          >
            Log In
          </Link>
          <Link
            to="/signup"
            id="nav-signup-btn"
            className="px-5 py-2 rounded-xl text-sm font-bold bg-[#174C3C] hover:bg-[#145B59] text-[#FFF6E8] transition shadow-lg shadow-[#174C3C]/40 border border-[#F2C45A]/30 flex items-center gap-1.5"
          >
            <span>Get Started</span>
            <ArrowRight className="h-3.5 w-3.5 text-[#F2C45A]" />
          </Link>
        </div>
      </nav>

      {/* ── Hero Section ── */}
      <section className="relative flex flex-col items-center justify-center px-6 pt-10 pb-20 overflow-hidden">
        {/* Ambient atmospheric glows */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-10 left-1/2 -translate-x-1/2 w-[900px] h-[450px] bg-gradient-to-b from-[#174C3C]/25 via-[#F2C45A]/10 to-transparent blur-[130px] rounded-full" />
          <div className="absolute top-1/3 right-1/4 w-[450px] h-[300px] bg-[#D97757]/10 blur-[100px] rounded-full" />
        </div>

        <div className="relative z-10 max-w-5xl mx-auto w-full text-center">
          {/* Tagline Badge -- above image */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#174C3C]/40 border border-[#F2C45A]/35 text-[#F2C45A] text-xs font-semibold mb-6 shadow-sm">
            <Sparkles className="h-3.5 w-3.5 text-[#F2C45A]" />
            <span>A small loaf of bread can save a life</span>
          </div>

          {/* Headline -- above image */}
          <h1 className="text-5xl md:text-7xl font-black leading-tight tracking-tight text-white mb-8">
            Good Food. <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#F2C45A] via-[#F4A261] to-[#77B7A5]">Shared Life.</span>
          </h1>

          {/* Hero Illustration -- fully visible between headline and body text */}
          <div className="relative max-w-4xl mx-auto mb-10">
            <div className="absolute -inset-1 rounded-3xl bg-gradient-to-r from-[#F2C45A]/20 via-[#174C3C]/30 to-[#77B7A5]/20 blur-xl opacity-75" />
            <Illustration
              src={heroBreadSharing}
              alt="An adult gently offering a warm loaf of bread to a joyful child"
              variant="hero"
              aspectRatio="16:9"
              badge="Nourishment &amp; Kindness"
            />
          </div>

          {/* Subtitle + CTAs -- below image */}
          <p className="text-lg md:text-xl text-[#FFF6E8]/85 max-w-2xl mx-auto mb-8 leading-relaxed font-normal">
            Turning surplus institutional food into nourishment, connection, and a better tomorrow.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/signup"
              id="hero-signup-btn"
              className="flex items-center gap-2.5 px-8 py-3.5 rounded-2xl bg-[#174C3C] hover:bg-[#145B59] text-[#FFF6E8] font-bold text-sm transition shadow-xl shadow-[#174C3C]/50 border border-[#F2C45A]/40 group"
            >
              <span>Join the Movement</span>
              <ArrowRight className="h-4 w-4 text-[#F2C45A] group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/login"
              id="hero-login-btn"
              className="flex items-center gap-2 px-7 py-3.5 rounded-2xl border border-white/15 hover:bg-white/5 text-[#FFF6E8] font-semibold text-sm transition"
            >
              <span>Explore Demo Dashboard</span>
            </Link>
          </div>
        </div>
      </section>

      {/* ── Community Storytelling Section ── */}
      <section id="stories" className="px-6 py-24 max-w-6xl mx-auto w-full">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#174C3C]/30 border border-[#77B7A5]/30 text-[#77B7A5] text-xs font-semibold uppercase tracking-wider mb-3">
            <Heart className="h-3 w-3 text-[#D97757]" /> Community Stories
          </div>
          <h2 className="text-3xl md:text-4xl font-black text-white mb-4">
            The Hearts Behind Every Meal
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto text-sm md:text-base leading-relaxed">
            Behind every metric and dispatch is a human story. Loife connects institutional dining halls with local communities to ensure no meal goes unshared.
          </p>
        </div>

        {/* Stories Grid */}
        <div className="space-y-16">
          {/* Story A & Story B Row */}
          <div className="grid md:grid-cols-2 gap-8 items-stretch">
            {/* Story A: Share Food, Share Love */}
            <div className="loife-surface-warm p-6 rounded-3xl flex flex-col justify-between">
              <div>
                <Illustration
                  src={storyParkBench}
                  alt="Two friends on a sunny park bench smiling and sharing ice cream"
                  variant="card"
                  aspectRatio="4:3"
                  badge="Story A • Human Connection"
                />
                <h3 className="text-xl font-bold text-white mt-6 mb-2">Share Food. Share Love.</h3>
                <p className="text-sm text-gray-300 leading-relaxed">
                  Food is a catalyst for joy and belonging. When surplus is redirected before decay, everyday treats and warm meals find people who appreciate them most.
                </p>
              </div>
              <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-[#F2C45A] font-semibold">
                <span>Every Meal Matters</span>
                <span className="text-gray-400 font-normal">Social Nourishment</span>
              </div>
            </div>

            {/* Story B: Good Food Builds Stronger Communities */}
            <div className="loife-surface-sage p-6 rounded-3xl flex flex-col justify-between">
              <div>
                <Illustration
                  src={storyCommunityDining}
                  alt="A welcoming community dining hall with diverse people sharing warm dishes"
                  variant="card"
                  aspectRatio="4:3"
                  badge="Story B • Communal Tables"
                />
                <h3 className="text-xl font-bold text-white mt-6 mb-2">Good Food Builds Stronger Communities</h3>
                <p className="text-sm text-gray-300 leading-relaxed">
                  A meal is better together. Loife pairs university messes, banquets, and corporate dining clusters with partner shelters so that wholesome food fills community tables.
                </p>
              </div>
              <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-[#77B7A5] font-semibold">
                <span>Nourishment Creates Connection</span>
                <span className="text-gray-400 font-normal">Community Resilience</span>
              </div>
            </div>
          </div>

          {/* Story C: Take Only What You Need (Full Width Feature with Hindi Callout) */}
          <div className="loife-surface-terracotta p-8 md:p-12 rounded-3xl grid md:grid-cols-12 gap-8 items-center">
            <div className="md:col-span-6 space-y-4">
              <span className="px-3 py-1 rounded-full bg-[#D97757]/20 border border-[#D97757]/40 text-[#F4A261] text-xs font-bold uppercase tracking-wider">
                Story C • Mindful Consumption
              </span>
              <h3 className="text-2xl md:text-3xl font-black text-white">
                Take Only What You Need
              </h3>
              
              {/* Highlighted Quote in Hindi & English */}
              <div className="p-5 rounded-2xl bg-[#080b11]/60 border border-[#F2C45A]/30 space-y-2">
                <p className="text-xl md:text-2xl font-serif text-[#F2C45A] font-medium tracking-wide">
                  “इतना ही लो थाली में, व्यर्थ न जाए नाली में”
                </p>
                <p className="text-xs text-[#FFF6E8]/70 italic">
                  Take only what you need on your plate, so not a single morsel is wasted.
                </p>
              </div>

              <p className="text-sm text-gray-300 leading-relaxed">
                Waste reduction begins before cooking starts. Loife empowers kitchen managers with machine learning demand forecasting to prep with purpose and cultivate a culture of mindful portions.
              </p>
            </div>
            <div className="md:col-span-6">
              <Illustration
                src={storyThaliMindful}
                alt="A person thoughtfully dining on a balanced Indian thali meal"
                variant="card"
                aspectRatio="4:3"
                caption="Plan with care. Prepare with purpose. Respect every grain."
              />
            </div>
          </div>

          {/* Story D & Story E Row */}
          <div className="grid md:grid-cols-2 gap-8 items-stretch">
            {/* Story D: A Healthier Tomorrow */}
            <div className="loife-surface-sage p-6 rounded-3xl flex flex-col justify-between">
              <div>
                <Illustration
                  src={storyGreenFuture}
                  alt="Family and volunteers sharing wholesome food in a green sunlit garden"
                  variant="card"
                  aspectRatio="4:3"
                  badge="Story D • Sustainability"
                />
                <h3 className="text-xl font-bold text-white mt-6 mb-2">Less Waste Today. A Healthier Tomorrow.</h3>
                <p className="text-sm text-gray-300 leading-relaxed">
                  Food waste accounts for 8–10% of global greenhouse emissions. Diverting safe meals avoids methane emissions from landfills and conserves virtual water, tracked with Poore &amp; Nemecek LCA accounting.
                </p>
              </div>
              <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-[#77B7A5] font-semibold">
                <span>Scope 3 Emission Offsets</span>
                <span className="text-gray-400 font-normal">Environmental Care</span>
              </div>
            </div>

            {/* Story E: Small Actions, Big Impact */}
            <div className="loife-surface-warm p-6 rounded-3xl flex flex-col justify-between">
              <div>
                <Illustration
                  src={storySmallActions}
                  alt="Open hands cupping a golden loaf of bread, heart, and sprout leaves"
                  variant="card"
                  aspectRatio="4:3"
                  badge="Story E • The Loife Philosophy"
                />
                <h3 className="text-xl font-bold text-white mt-6 mb-2">Small Actions, Big Impact</h3>
                <p className="text-sm text-gray-300 leading-relaxed">
                  A loaf of bread, a shared meal, a route planned with care—small acts of mindful kindness combine to create lasting institutional change and nourish thousands.
                </p>
              </div>
              <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-[#F2C45A] font-semibold">
                <span>Together, We Make Every Meal Count</span>
                <span className="text-gray-400 font-normal">Circular Impact</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Problem Statement ── */}
      <section className="px-6 py-20 max-w-5xl mx-auto w-full">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-black text-white mb-4">The Challenge We Solve</h2>
          <p className="text-gray-400 max-w-2xl mx-auto text-sm leading-relaxed">
            Institutional dining facilities—universities, hospital canteens, corporate IT parks—routinely overproduce by 15–25% due to volatile demand, absence of cold-chain tracking, and disjointed donation logistics.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { icon: TrendingDown, color: '#D97757', title: 'Unpredicted Footfall', desc: 'Kitchens overproduce due to exam schedules, holidays, and sudden weather shifts, causing avoidable daily prep loss.' },
            { icon: Globe, color: '#F2C45A', title: 'Redistribution Friction', desc: 'Edible surplus spoils in storage while local charities and shelters struggle with food shortages just a few kilometers away.' },
            { icon: BarChart3, color: '#77B7A5', title: 'Missing ESG Proof', desc: 'Institutions lack scientific, auditable life-cycle data to certify carbon offsets and virtual water conserved for BRSR compliance.' },
          ].map(({ icon: Icon, color, title, desc }) => (
            <div key={title} className="glass-card p-6 rounded-2xl border border-white/10">
              <div
                className="h-10 w-10 rounded-xl flex items-center justify-center mb-4"
                style={{ backgroundColor: `${color}20` }}
              >
                <Icon className="h-5 w-5" style={{ color }} />
              </div>
              <h3 className="text-base font-bold text-white mb-2">{title}</h3>
              <p className="text-sm text-gray-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── The Loife Solution ── */}
      <section id="solution" className="px-6 py-20 bg-gradient-to-b from-transparent via-[#174C3C]/10 to-transparent">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-black text-white mb-4">The Loife Circular Platform</h2>
            <p className="text-gray-400 max-w-2xl mx-auto text-sm leading-relaxed">
              An enterprise ecosystem bridging culinary forecasting, computer vision quality validation,
              logistics dispatch, and ESG life-cycle accounting.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[
              { icon: ChefHat, color: '#F2C45A', title: 'Demand Forecasting', desc: 'LightGBM predictive models estimate sub-meal headcount to prevent overproduction before cooking begins.' },
              { icon: Scan, color: '#77B7A5', title: 'Computer Vision Inspection', desc: 'EfficientNet-B0 visual scanning detects surface oxidation, assigning an objective Freshness Score (0–100) and safety window.' },
              { icon: HeartHandshake, color: '#D97757', title: 'Autonomous NGO Matching', desc: 'Distance and capacity-based matching connects verified charities with available surplus within safe consumption windows.' },
              { icon: Truck, color: '#38BDF8', title: 'Fleet Route Optimization', desc: 'Capacitated Vehicle Routing Problem solver plans multi-stop pickups to minimize transit time and carbon footprint.' },
              { icon: BarChart3, color: '#A78BFA', title: 'Poore & Nemecek ESG Accounting', desc: 'Calculates verified kg CO₂e avoided and liters of virtual water conserved for Scope 3 sustainability compliance.' },
              { icon: LayoutDashboard, color: '#10B981', title: 'Executive Operations Control', desc: 'Role-gated dashboards providing operational transparency, compliance audit trails, and live status.' },
            ].map(({ icon: Icon, color, title, desc }) => (
              <div key={title} className="glass-card p-5 rounded-2xl group hover:border-[#F2C45A]/30 transition-all duration-300">
                <div
                  className="h-9 w-9 rounded-lg flex items-center justify-center mb-3"
                  style={{ backgroundColor: `${color}20` }}
                >
                  <Icon className="h-4.5 w-4.5" style={{ color }} />
                </div>
                <h3 className="text-sm font-bold text-white mb-1.5">{title}</h3>
                <p className="text-xs text-gray-400 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Workflow Steps ── */}
      <section id="workflow" className="px-6 py-20 max-w-5xl mx-auto w-full">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-black text-white mb-4">Five Steps: From Kitchen to Community</h2>
          <p className="text-gray-400 max-w-xl mx-auto text-sm">A seamless, closed-loop circular redistribution workflow.</p>
        </div>
        <div className="flex flex-col md:flex-row items-start gap-4 md:gap-0">
          {[
            { step: '01', label: 'Predict', desc: 'AI forecast tailors daily prep to real footfall', color: '#10B981' },
            { step: '02', label: 'Inspect', desc: 'CV scan validates food freshness & safety', color: '#77B7A5' },
            { step: '03', label: 'Match', desc: 'Surplus paired with nearest verified NGO', color: '#D97757' },
            { step: '04', label: 'Deliver', desc: 'Optimized routing dispatches prompt pickup', color: '#38BDF8' },
            { step: '05', label: 'Certify', desc: 'Audit logs record verified ESG savings', color: '#F2C45A' },
          ].map(({ step, label, desc, color }, idx) => (
            <div key={step} className="flex md:flex-col items-start md:items-center flex-1 gap-4 md:gap-2 relative pb-6 md:pb-0">
              <div className="flex flex-col md:flex-row items-center md:w-full">
                <div
                  className="h-12 w-12 rounded-2xl flex items-center justify-center shrink-0 border"
                  style={{ backgroundColor: `${color}15`, borderColor: `${color}40` }}
                >
                  <span className="text-sm font-black" style={{ color }}>{step}</span>
                </div>
                {idx < 4 && (
                  <div className="hidden md:block flex-1 h-px bg-gradient-to-r from-white/10 to-transparent mx-2" />
                )}
              </div>
              <div className="md:text-center md:px-2 md:mt-3">
                <p className="text-sm font-bold text-white">{label}</p>
                <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Built for Every Stakeholder ── */}
      <section id="roles" className="px-6 py-20 bg-gradient-to-b from-transparent via-[#174C3C]/10 to-transparent">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-black text-white mb-4">Dedicated Persona Dashboards</h2>
            <p className="text-gray-400 max-w-xl mx-auto text-sm">Role-based controls tailored to each stakeholder in the food redistribution network.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { role: 'Kitchen Manager', desc: 'Demand forecast planning, batch logging with QR codes, and surplus donation declarations.', color: 'from-[#174C3C] to-[#145B59]', initials: 'KM' },
              { role: 'Quality Inspector', desc: 'Computer vision food safety scans, sensory checks, remaining shelf-life verification, and sign-offs.', color: 'from-[#F2C45A] to-[#D97757]', initials: 'QI' },
              { role: 'NGO Representative', desc: 'Surplus marketplace browsing, instant batch claims, pickup scheduling, and beneficiary meal logs.', color: 'from-[#D97757] to-[#8B6246]', initials: 'NR' },
              { role: 'Logistics Coordinator', desc: 'Fleet dispatching, GPS route simulation, waypoint tracking, and recipient handoff confirmation.', color: 'from-[#145B59] to-[#77B7A5]', initials: 'LC' },
              { role: 'Sustainability Admin', desc: 'Executive KPI control tower, Scope 3 emission accounting, and downloadable ESG compliance certificates.', color: 'from-[#174C3C] to-[#29332F]', initials: 'SA' },
            ].map(({ role, desc, color, initials }) => (
              <div key={role} className="glass-card p-5 rounded-2xl flex gap-3 border border-white/10 hover:border-[#F2C45A]/25 transition">
                <div className={`h-9 w-9 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center text-white font-bold text-xs shrink-0 shadow-md`}>
                  {initials}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white mb-1">{role}</h3>
                  <p className="text-xs text-gray-400 leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Call to Action ── */}
      <section className="px-6 py-20 max-w-5xl mx-auto w-full text-center">
        <div className="loife-surface-warm p-12 rounded-3xl border border-[#F2C45A]/30 relative overflow-hidden">
          <div className="relative z-10">
            <h2 className="text-3xl md:text-4xl font-black text-white mb-4">
              Good Food. Shared Life.
            </h2>
            <p className="text-[#FFF6E8]/80 mb-8 max-w-lg mx-auto text-sm leading-relaxed">
              Every meal matters. Sign up to explore the Loife platform with pre-loaded demo personas or connect your institutional kitchen today.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/signup"
                id="cta-signup-btn"
                className="flex items-center gap-2 px-8 py-3.5 rounded-xl bg-[#174C3C] hover:bg-[#145B59] text-[#FFF6E8] font-bold text-sm transition shadow-xl shadow-[#174C3C]/50 border border-[#F2C45A]/40"
              >
                Create Account <ArrowRight className="h-4 w-4 text-[#F2C45A]" />
              </Link>
              <Link
                to="/login"
                id="cta-login-btn"
                className="flex items-center gap-2 px-8 py-3.5 rounded-xl border border-white/20 hover:bg-white/5 text-[#FFF6E8] font-semibold text-sm transition"
              >
                Log In
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-white/10 px-6 py-10 bg-[#06080D]">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <LoifeLogo size="sm" showTagline={true} />
          </div>
          <div className="flex items-center gap-6 text-xs text-gray-400 font-medium">
            <Link to="/login" className="hover:text-white transition">Login</Link>
            <Link to="/signup" className="hover:text-white transition">Sign Up</Link>
            <a href="#stories" className="hover:text-[#F2C45A] transition">Community Stories</a>
            <span className="text-[#77B7A5]">Smart India Hackathon 2026 Enterprise</span>
          </div>
          <p className="text-xs text-gray-500 text-center md:text-right">
            Loife circular food ecosystem • Certified LCA methodology under Poore &amp; Nemecek (2018).
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
