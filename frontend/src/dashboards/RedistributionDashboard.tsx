import React, { useEffect, useState } from 'react';
import { 
  MapPin, 
  CheckCircle2, 
  Sparkles, 
  Send,
  AlertTriangle,
  Heart
} from 'lucide-react';
import { apiService } from '../services/api';
import { SurplusItem, NGOMatch } from '../types';
import heroBreadSharing from '../assets/illustrations/brand/hero_bread_sharing.png';

export const RedistributionDashboard: React.FC = () => {
  const [surplusList, setSurplusList] = useState<SurplusItem[]>([]);
  const [selectedSurplus, setSelectedSurplus] = useState<SurplusItem | null>(null);
  const [matches, setMatches] = useState<NGOMatch[]>([]);
  const [matchingLoading, setMatchingLoading] = useState(false);
  const [dispatchedSuccess, setDispatchedSuccess] = useState(false);

  const loadMatches = async (reqId: number) => {
    setMatchingLoading(true);
    try {
      const matchData = await apiService.matchNGOs(reqId);
      setMatches(matchData);
    } finally {
      setMatchingLoading(false);
    }
  };

  useEffect(() => {
    const fetchSurplus = async () => {
      const data = await apiService.getSurplusList();
      setSurplusList(data);
      if (data.length > 0) {
        setSelectedSurplus(data[0]);
        loadMatches(data[0].id);
      }
    };
    fetchSurplus();
  }, []);

  const handleSelectSurplus = (item: SurplusItem) => {
    setSelectedSurplus(item);
    setDispatchedSuccess(false);
    loadMatches(item.id);
  };

  const [claimingLoading, setClaimingLoading] = useState(false);
  const [claimError, setClaimError] = useState<string | null>(null);
  const [claimSuccess, setClaimSuccess] = useState<string | null>(null);

  const handleClaim = async (ngoId: number, ngoName: string) => {
    if (!selectedSurplus) return;
    setClaimingLoading(true);
    setClaimError(null);
    setClaimSuccess(null);
    try {
      await apiService.claimSurplus(selectedSurplus.id, ngoId);
      setDispatchedSuccess(true);
      setClaimSuccess(`Successfully claimed Lot #${selectedSurplus.id} for ${ngoName}. Logistics dispatch scheduled.`);
      setSurplusList(prev => prev.map(s => s.id === selectedSurplus.id ? { ...s, status: 'MATCHED', claimed_by_ngo_name: ngoName } : s));
      setSelectedSurplus(prev => prev ? { ...prev, status: 'MATCHED', claimed_by_ngo_name: ngoName } : null);
    } catch (err: any) {
      if (err.response?.status === 409) {
        setClaimError(`Duplicate Claim Prevented (HTTP 409 Conflict): Lot #${selectedSurplus.id} is already claimed or closed.`);
      } else {
        setClaimError(err.response?.data?.detail || 'Claim request could not be processed.');
      }
    } finally {
      setClaimingLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Surplus Food Redistribution Network</h1>
          <p className="text-xs text-gray-400 mt-1">
            Autonomous multi-factor matching connecting edible surplus with verified local NGOs, shelters, and food banks.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">Total Rescued Today:</span>
          <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            83.0 kg (208 meals)
          </span>
        </div>
      </div>

      {/* Loife NGO Community Care Banner */}
      <div className="loife-surface-warm p-4 md:p-5 rounded-2xl border border-[#F2C45A]/35 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-lg">
        <div className="flex items-center gap-4">
          <div className="h-16 w-24 sm:h-20 sm:w-28 rounded-xl overflow-hidden shrink-0 border border-white/10 shadow-md">
            <img
              src={heroBreadSharing}
              alt="Sharing bread with dignity"
              className="w-full h-full object-cover"
            />
          </div>
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#174C3C]/50 border border-[#F2C45A]/30 text-[#F2C45A] text-[10px] font-bold uppercase tracking-wider mb-1">
              <Heart className="h-3 w-3 text-[#D97757]" /> Community Redistribution &amp; Dignity
            </div>
            <h2 className="text-base sm:text-lg font-bold text-white">
              Share a meal. Share a little more hope.
            </h2>
            <p className="text-xs text-gray-300 max-w-xl mt-0.5 leading-relaxed">
              Every surplus lot declared by campus and institutional dining is verified for quality and reserved for trusted charity partners to nourish local families with dignity.
            </p>
          </div>
        </div>
        <div className="shrink-0 text-right hidden lg:block">
          <span className="text-[10px] uppercase font-bold text-[#F2C45A] tracking-wider block">Verified Partners</span>
          <span className="text-xs text-gray-400">Robin Hood Army • Feeding India</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 6 Cols: Available Surplus Batches */}
        <div className="lg:col-span-6 space-y-4">
          <div className="glass-card p-6 rounded-2xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-white">Active Surplus Lots Ready for Claim</h2>
              <span className="text-xs text-gray-400 font-mono">{surplusList.length} Lots Available</span>
            </div>

            <div className="space-y-3">
              {surplusList.map((item) => {
                const isSelected = selectedSurplus?.id === item.id;
                return (
                  <div
                    key={item.id}
                    onClick={() => handleSelectSurplus(item)}
                    className={`p-4 rounded-xl cursor-pointer transition-all border ${
                      isSelected
                        ? 'bg-emerald-950/30 border-emerald-500/50 shadow-md shadow-emerald-500/10'
                        : 'bg-white/5 border-white/5 hover:bg-white/[0.08]'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-sm font-bold text-white">{item.food_item_name}</h3>
                        <p className="text-xs text-gray-400 mt-0.5 font-mono">
                          Quantity: <strong className="text-emerald-400">{item.quantity_kg} kg</strong> (~{item.estimated_meals} meals)
                        </p>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                        item.status === 'MATCHED'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}>
                        {item.status}
                      </span>
                    </div>

                    {item.claimed_by_ngo_name && (
                      <div className="mt-2 pt-2 border-t border-white/5">
                        <span className="text-[11px] text-emerald-400 font-bold font-mono">
                          Assigned: {item.claimed_by_ngo_name}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right 6 Cols: AI NGO Compatibility Matcher */}
        <div className="lg:col-span-6 space-y-4">
          <div className="glass-card p-6 rounded-2xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-emerald-400" />
                  <h2 className="text-base font-bold text-white">AI Compatibility Ranking</h2>
                </div>
                <p className="text-xs text-gray-400 mt-0.5">
                  Multi-factor optimization: Distance, Capacity, Cold chain, and Urgency
                </p>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                Matching Engine
              </span>
            </div>

            {claimSuccess && (
              <div className="mb-4 p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/50 flex items-center gap-2 text-xs text-emerald-300">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
                <span>{claimSuccess}</span>
              </div>
            )}

            {claimError && (
              <div className="mb-4 p-3 rounded-xl bg-rose-950/60 border border-rose-500/50 flex items-center gap-2 text-xs text-rose-300">
                <AlertTriangle className="h-4 w-4 shrink-0 text-rose-400" />
                <span>{claimError}</span>
              </div>
            )}

            <div className="space-y-3">
              {matchingLoading ? (
                <div className="p-8 text-center text-xs text-gray-400">
                  Computing optimal NGO pairings...
                </div>
              ) : (
                matches.map((ngo, index) => (
                  <div 
                    key={ngo.ngo_id} 
                    className="p-4 rounded-xl bg-white/5 border border-white/5 hover:border-emerald-500/30 transition flex flex-col justify-between"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-xs font-bold text-white">{ngo.ngo_name}</h3>
                          {index === 0 && (
                            <span className="px-1.5 py-0.2 text-[9px] font-black rounded bg-emerald-400 text-gray-950 uppercase tracking-wider">
                              Best Match
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-gray-400 flex items-center gap-1 mt-1">
                          <MapPin className="h-3 w-3 text-emerald-400" />
                          {ngo.address}
                        </p>
                      </div>

                      <div className="text-right">
                        <span className="text-sm font-black font-mono text-emerald-400">{ngo.compatibility_score}%</span>
                        <p className="text-[10px] text-gray-500">Compatibility</p>
                      </div>
                    </div>

                    <div className="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-end text-xs">
                      <button
                        onClick={() => handleClaim(ngo.ngo_id, ngo.ngo_name)}
                        disabled={claimingLoading}
                        className="px-3 py-1 rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-gray-950 font-bold text-xs flex items-center gap-1 transition shadow-sm"
                      >
                        <Send className="h-3 w-3" />
                        <span>{claimingLoading ? 'Dispatching...' : 'Dispatch'}</span>
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
