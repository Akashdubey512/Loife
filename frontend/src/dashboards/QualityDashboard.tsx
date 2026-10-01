import React, { useState, useRef, useEffect } from 'react';
import { 
  UploadCloud, 
  Clock, 
  ShieldCheck, 
  Camera,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  UserCheck,
  Info,
  X,
  ChevronRight
} from 'lucide-react';
import { apiService } from '../services/api';
import { QualityScanResult } from '../types';
import storySmallActions from '../assets/illustrations/brand/story_small_actions.png';

export const QualityDashboard: React.FC = () => {
  const [scanning, setScanning] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verificationSuccess, setVerificationSuccess] = useState(false);
  const [inspectorNotes, setInspectorNotes] = useState('Sensory smell, texture, and visual surface inspected. Batch meets standard.');
  const [scanError, setScanError] = useState<string | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [recentScans, setRecentScans] = useState<any[]>([]);
  const [scanResult, setScanResult] = useState<QualityScanResult | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Load recent scans from backend on mount
  useEffect(() => {
    const loadRecent = async () => {
      try {
        const scans = await apiService.getQualityScans(10);
        setRecentScans(scans);
      } catch {
        // Non-critical — just show empty state
        setRecentScans([]);
      }
    };
    loadRecent();
  }, []);

  const resetScan = () => {
    setScanResult(null);
    setPreviewUrl(null);
    setSelectedFile(null);
    setScanError(null);
    setVerifyError(null);
    setVerificationSuccess(false);
  };

  const handleFileSelected = (file: File) => {
    // Validate file type client-side (backend will re-validate via magic bytes)
    const allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    if (!allowed.includes(file.type)) {
      setScanError('Unsupported file type. Please upload a JPEG, PNG, WebP, or GIF image.');
      return;
    }
    // Validate size (5 MB limit matches backend)
    if (file.size > 5 * 1024 * 1024) {
      setScanError('Image exceeds 5 MB limit. Please use a smaller file.');
      return;
    }
    setScanError(null);
    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
    setScanResult(null);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    handleFileSelected(file);
    // Reset input so same file can be re-selected
    event.target.value = '';
  };

  const handleScan = async () => {
    if (!selectedFile) return;
    setScanning(true);
    setScanError(null);
    setVerificationSuccess(false);
    setScanResult(null);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('food_item_id', '1');
      formData.append('food_name', selectedFile.name.split('.')[0].replace(/_/g, ' ') || 'Inspected Produce');

      const result = await apiService.scanFoodImage(formData);
      setScanResult(result);
      // Refresh recent scans list
      try {
        const scans = await apiService.getQualityScans(10);
        setRecentScans(scans);
      } catch { /* non-critical */ }
    } catch (err: any) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      if (status === 400 || status === 413 || status === 415) {
        setScanError(`Image rejected by server: ${typeof detail === 'string' ? detail : 'Invalid image format or size.'}`);
      } else if (status === 401) {
        setScanError('Session expired. Please log in again.');
      } else if (status === 403) {
        setScanError('You do not have permission to perform quality scans.');
      } else if (!err?.response && err?.code === 'ECONNABORTED') {
        setScanError('Scan timed out. The CV engine may be busy — please retry.');
      } else {
        setScanError(
          typeof detail === 'string'
            ? detail
            : 'Quality scan failed. Check backend connection and retry.'
        );
      }
    } finally {
      setScanning(false);
    }
  };

  const handleHumanVerification = async () => {
    if (!scanResult) return;
    setVerifying(true);
    setVerifyError(null);
    try {
      const res = await apiService.verifyQualityScan(scanResult.id, {
        inspector_notes: inspectorNotes,
        verdict: scanResult.redistribution_status === 'SAFE_FOR_REDISTRIBUTION'
          ? 'APPROVED_FOR_REDISTRIBUTION'
          : scanResult.redistribution_status === 'COMPOST_ONLY'
          ? 'DOWNGRADE_TO_COMPOST'
          : 'HOLD_FOR_LAB_TEST',
        override_model_decision: false
      });
      setVerificationSuccess(true);
      setScanResult(prev => prev ? { 
        ...prev, 
        human_verified: true, 
        inspector_name: res.inspector_name || 'Quality Inspector',
        food_safety_verdict: res.food_safety_verdict || 'APPROVED_FOR_REDISTRIBUTION'
      } : null);
    } catch (err: any) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      if (status === 403) {
        setVerifyError('Only Quality Inspectors or Kitchen Managers can verify scans.');
      } else if (status === 404) {
        setVerifyError('Scan record not found. Please re-scan the item.');
      } else {
        setVerifyError(
          typeof detail === 'string'
            ? detail
            : 'Verification failed. Check your role permissions and retry.'
        );
      }
    } finally {
      setVerifying(false);
    }
  };

  const getBadgeStyle = (status: string) => {
    switch (status) {
      case 'SAFE_FOR_REDISTRIBUTION':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'PROCESS_IMMEDIATELY':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'COMPOST_ONLY':
        return 'bg-orange-500/20 text-orange-300 border-orange-500/40';
      default:
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Computer Vision Food Quality & Multi-Factor Safety</h1>
          <p className="text-xs text-gray-400 mt-1">
            Multi-factor safety clearance with CV optical scoring, cold-chain sensor checks and mandatory human inspector sign-off.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">FSSAI Safety Rules:</span>
          <span className="text-xs font-mono font-bold px-2 py-1 rounded bg-white/5 text-emerald-400 border border-white/10">
            Multi-Factor Verified
          </span>
        </div>
      </div>

      {/* Loife Quality Care Banner */}
      <div className="loife-surface-warm p-4 md:p-5 rounded-2xl border border-[#F2C45A]/30 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-lg">
        <div className="flex items-center gap-4">
          <div className="h-16 w-24 sm:h-20 sm:w-28 rounded-xl overflow-hidden shrink-0 border border-white/10 shadow-md">
            <img
              src={storySmallActions}
              alt="Food care and inspection symbol"
              className="w-full h-full object-cover"
            />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded-full bg-[#174C3C]/50 border border-[#F2C45A]/30 text-[#F2C45A] text-[10px] font-bold uppercase tracking-wider">
                Safety &amp; Integrity
              </span>
            </div>
            <h2 className="text-base sm:text-lg font-bold text-white">
              Every safe meal is a promise kept.
            </h2>
            <p className="text-xs text-gray-300 max-w-xl mt-0.5 leading-relaxed">
              Safe food redistribution relies on rigorous human verification alongside sensory checks and temperature records. Only inspected batches proceed to community partners.
            </p>
          </div>
        </div>
        <div className="shrink-0 text-right hidden lg:block">
          <span className="text-[10px] uppercase font-bold text-[#F2C45A] tracking-wider block">FSSAI Protocol</span>
          <span className="text-xs text-gray-400">Mandatory Human Sign-off</span>
        </div>
      </div>

      {/* Main Scanner Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 5 Cols: Upload */}
        <div className="lg:col-span-5 space-y-4">
          <div className="glass-card p-6 rounded-2xl">
            <h2 className="text-base font-bold text-white mb-2">Food Image Capture / Upload</h2>
            <p className="text-xs text-gray-400 mb-4">
              Upload a live food inspection photo. Image is sent to the backend quality engine for real inference.
            </p>

            {/* Hidden file input */}
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileUpload} 
              accept="image/jpeg,image/png,image/webp,image/gif" 
              className="hidden" 
            />

            {/* Preview or drop zone */}
            {previewUrl ? (
              <div className="relative rounded-2xl overflow-hidden border border-white/10 mb-4">
                <img src={previewUrl} alt="Selected food" className="w-full max-h-52 object-cover" />
                <button
                  onClick={resetScan}
                  className="absolute top-2 right-2 h-7 w-7 rounded-full bg-black/70 flex items-center justify-center text-white hover:bg-rose-600 transition"
                  title="Remove image"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
                <div className="absolute bottom-0 inset-x-0 bg-black/60 px-3 py-2 text-[11px] text-gray-200 truncate font-mono">
                  {selectedFile?.name}
                </div>
              </div>
            ) : (
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-white/10 hover:border-emerald-500/50 rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition bg-white/[0.01] hover:bg-white/[0.03] mb-4"
              >
                <div className="h-12 w-12 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-3">
                  <UploadCloud className="h-6 w-6" />
                </div>
                <p className="text-xs font-bold text-gray-200">Click or drag &amp; drop inspection photo</p>
                <p className="text-[11px] text-gray-500 mt-1">JPEG, PNG, WebP up to 5 MB</p>
                <button 
                  type="button"
                  className="mt-4 px-3.5 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-gray-950 text-xs font-bold transition flex items-center gap-1.5 shadow-md shadow-emerald-500/20"
                >
                  <Camera className="h-3.5 w-3.5" />
                  <span>Select Device Image</span>
                </button>
              </div>
            )}

            {/* Error */}
            {scanError && (
              <div className="mb-3 p-3 rounded-xl bg-rose-950/50 border border-rose-500/40 text-rose-300 text-xs flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-rose-400" />
                <span>{scanError}</span>
              </div>
            )}

            {/* Scan button */}
            {selectedFile && !scanResult && (
              <button
                onClick={handleScan}
                disabled={scanning}
                className="w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-gray-950 text-xs font-bold transition flex items-center justify-center gap-2 shadow-md shadow-emerald-500/20"
              >
                {scanning ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Analyzing image...
                  </>
                ) : (
                  <>
                    <ShieldCheck className="h-4 w-4" />
                    Run Quality Scan
                  </>
                )}
              </button>
            )}

            {scanResult && (
              <button
                onClick={resetScan}
                className="w-full py-2 rounded-xl bg-white/10 hover:bg-white/15 text-gray-200 text-xs font-bold transition"
              >
                Scan Another Item
              </button>
            )}

            {/* Recent scans */}
            {recentScans.length > 0 && (
              <div className="mt-5 pt-4 border-t border-white/5">
                <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block mb-2.5">
                  Recent Scans (last {recentScans.length}):
                </span>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {recentScans.map((scan, i) => (
                    <div key={`recent-${scan.id}-${i}`} className="flex items-center justify-between p-2 rounded-lg bg-white/5 text-[11px]">
                      <span className="text-gray-300 font-mono truncate max-w-[60%]">
                        Scan #{scan.id} — {scan.freshness_level}
                      </span>
                      <span className={`font-bold ${
                        scan.freshness_score >= 80 ? 'text-emerald-400' :
                        scan.freshness_score >= 50 ? 'text-amber-400' : 'text-rose-400'
                      }`}>{scan.freshness_score?.toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right 7 Cols: Result */}
        <div className="lg:col-span-7">
          <div className="glass-card p-6 rounded-2xl relative overflow-hidden">
            {scanning ? (
              <div className="h-96 flex flex-col items-center justify-center gap-3">
                <RefreshCw className="h-8 w-8 text-emerald-400 animate-spin" />
                <p className="text-xs font-bold text-white">Analyzing image...</p>
                <span className="text-[11px] text-gray-500 font-mono">Running backend CV engine — please wait</span>
              </div>
            ) : !selectedFile && !scanResult ? (
              <div className="h-96 flex flex-col items-center justify-center gap-3 text-center">
                <div className="h-16 w-16 rounded-2xl bg-white/5 flex items-center justify-center">
                  <UploadCloud className="h-8 w-8 text-gray-500" />
                </div>
                <p className="text-sm font-bold text-gray-400">No image selected</p>
                <p className="text-xs text-gray-500 max-w-xs">
                  Upload a food image on the left to run the quality assessment engine.
                </p>
              </div>
            ) : selectedFile && !scanResult && !scanning ? (
              <div className="h-96 flex flex-col items-center justify-center gap-3 text-center">
                <div className="h-16 w-16 rounded-2xl bg-emerald-500/10 flex items-center justify-center">
                  <Camera className="h-8 w-8 text-emerald-400" />
                </div>
                <p className="text-sm font-bold text-white">Image ready</p>
                <p className="text-xs text-gray-400 max-w-xs">Click "Run Quality Scan" to send this image to the backend engine.</p>
                <ChevronRight className="h-5 w-5 text-gray-500" />
              </div>
            ) : scanResult ? (
              <div className="space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-white/5">
                  <div className="flex items-center gap-4">
                    {(previewUrl || scanResult.image_url) && (
                      <img 
                        src={previewUrl || scanResult.image_url} 
                        alt="Scanned Food" 
                        className="w-20 h-20 rounded-2xl object-cover border border-white/10 shadow-lg shrink-0"
                      />
                    )}
                    <div>
                      <span className="text-[10px] font-mono text-gray-400 uppercase tracking-wider">Lot Identification</span>
                      <h3 className="text-base font-bold text-white mt-0.5">{scanResult.food_name || 'Scanned Item'}</h3>
                      <p className="text-[11px] text-gray-400 mt-1 flex items-center gap-1.5 font-mono">
                        <Clock className="h-3 w-3" />
                        Scanned: {new Date(scanResult.inspected_at).toLocaleTimeString()}
                      </p>
                      {/* Model truthfulness notice */}
                      {scanResult.simulated && (
                        <div className="mt-1.5 flex items-center gap-1.5 px-2 py-1 rounded-lg bg-amber-950/40 border border-amber-500/30 text-[10px] text-amber-300">
                          <Info className="h-3 w-3 shrink-0" />
                          <span>AI model simulation — human verification required</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <span className={`px-3 py-1.5 rounded-xl border text-xs font-bold uppercase tracking-wider self-start ${getBadgeStyle(scanResult.redistribution_status)}`}>
                    {scanResult.redistribution_status.replace(/_/g, ' ')}
                  </span>
                </div>

                {/* Simulation notice banner */}
                {scanResult.simulation_notice && (
                  <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/30 text-xs text-amber-300 flex items-start gap-2">
                    <Info className="h-4 w-4 shrink-0 mt-0.5 text-amber-400" />
                    <span>{scanResult.simulation_notice}</span>
                  </div>
                )}

                {/* Multi-Factor Safety Triple-Check Banner */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3.5 rounded-xl bg-white/[0.03] border border-white/10 text-xs">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                    <div>
                      <span className="text-[10px] text-gray-400 block">1. Optical Freshness</span>
                      <strong className="text-white">{scanResult.freshness_score}% Fresh</strong>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {scanResult.sensor_safety_cleared !== false ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
                    )}
                    <div>
                      <span className="text-[10px] text-gray-400 block">2. Cold-Chain Log</span>
                      <strong className={scanResult.sensor_safety_cleared !== false ? "text-emerald-300" : "text-rose-400"}>
                        {scanResult.sensor_safety_cleared !== false ? "No Breach Detected" : "Temp Spike Alert"}
                      </strong>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                    <div>
                      <span className="text-[10px] text-gray-400 block">3. Expiry Rules</span>
                      <strong className="text-white">{scanResult.remaining_shelf_life_days}d Remaining</strong>
                    </div>
                  </div>
                </div>

                {/* Defects */}
                {scanResult.defects_detected && scanResult.defects_detected.length > 0 && (
                  <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 text-xs text-rose-300">
                    <span className="font-bold text-rose-400 block mb-1">Defects / Flags Detected:</span>
                    <ul className="list-disc pl-4 space-y-0.5">
                      {scanResult.defects_detected.map((d, i) => <li key={i}>{d}</li>)}
                    </ul>
                  </div>
                )}

                {/* Score Gauges */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 text-center">
                    <span className="text-xs text-gray-400 font-medium">Freshness Score</span>
                    <p className={`text-2xl font-black mt-1 font-mono ${
                      scanResult.freshness_score >= 80 ? 'text-emerald-400' :
                      scanResult.freshness_score >= 50 ? 'text-amber-400' : 'text-rose-400'
                    }`}>
                      {scanResult.freshness_score}%
                    </p>
                    <span className="text-[10px] text-gray-500 font-mono">Confidence: {(scanResult.confidence * 100).toFixed(1)}%</span>
                    {scanResult.simulated && (
                      <span className="block text-[9px] text-amber-400 mt-0.5 font-mono">SIMULATED</span>
                    )}
                  </div>

                  <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 text-center">
                    <span className="text-xs text-gray-400 font-medium">Predicted Shelf-Life</span>
                    <p className="text-2xl font-black mt-1 font-mono text-cyan-400">
                      {scanResult.remaining_shelf_life_days} <span className="text-sm font-normal text-gray-400">days</span>
                    </p>
                    <span className="text-[10px] text-gray-500 font-mono">Controlled Atmosphere</span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 text-center">
                    <span className="text-xs text-gray-400 font-medium">Quality Tier</span>
                    <p className="text-xl font-black mt-1 text-white">
                      {scanResult.freshness_level}
                    </p>
                    <span className="text-[10px] text-emerald-400 font-bold">FSSAI Guideline</span>
                  </div>
                </div>

                {/* Human Verification Clearance Box */}
                <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <UserCheck className="h-4 w-4 text-emerald-400" />
                      <h4 className="text-xs font-bold text-white">Human Inspector Verification Sign-Off</h4>
                    </div>
                    {scanResult.human_verified ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500 text-gray-950 uppercase tracking-wider flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3" /> Certified Clear
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase tracking-wider">
                        Pending Sign-Off
                      </span>
                    )}
                  </div>

                  {verificationSuccess && (
                    <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                      <span>Inspector verification recorded. Batch certified eligible for redistribution dispatch!</span>
                    </div>
                  )}

                  {verifyError && (
                    <div className="p-2.5 rounded-lg bg-rose-950/40 border border-rose-500/30 text-xs text-rose-300 flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
                      <span>{verifyError}</span>
                    </div>
                  )}

                  {!scanResult.human_verified && (
                    <div className="space-y-2">
                      <input 
                        type="text"
                        value={inspectorNotes}
                        onChange={(e) => setInspectorNotes(e.target.value)}
                        placeholder="Inspector notes and observations..."
                        className="w-full px-3 py-1.5 rounded-lg bg-black/40 border border-white/10 text-xs text-gray-200 focus:outline-none focus:border-emerald-500"
                      />
                      <button
                        onClick={handleHumanVerification}
                        disabled={verifying}
                        className="w-full py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-gray-950 text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-md shadow-emerald-500/20 disabled:opacity-50"
                      >
                        <ShieldCheck className="h-4 w-4" />
                        <span>{verifying ? 'Recording Verification Sign-Off...' : 'Approve & Certify for Redistribution'}</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
};
