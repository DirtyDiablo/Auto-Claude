import { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp, Loader2, RefreshCw, AlertTriangle, CheckCircle2,
  Zap, Shield, Briefcase, Brain, BarChart3, Calendar, Phone,
} from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

// ─── Types ─────────────────────────────────────────────────────────────────

interface ModelStatus {
  loaded: boolean;
  trained_at: string | null;
  accuracy: number | null;
  auc: number | null;
  feature_names: string[];
  feature_importance: Record<string, number>;
}

interface PredictionResult {
  probability: number;
  category: 'high' | 'medium' | 'low';
}

interface HiringSignal {
  signal_type: string;
  program: string;
  location: string;
  confidence: number;
  detected_at: string;
  details: Record<string, unknown>;
}

// ─── Constants ─────────────────────────────────────────────────────────────

const SIGNAL_STYLES: Record<string, { icon: typeof Zap; color: string; bg: string; label: string }> = {
  hiring_surge: { icon: TrendingUp, color: 'text-red-600 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900/30', label: 'Hiring Surge' },
  new_capability: { icon: Zap, color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-100 dark:bg-amber-900/30', label: 'New Capability' },
  clearance_escalation: { icon: Shield, color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-100 dark:bg-purple-900/30', label: 'Clearance Escalation' },
};

const CATEGORY_STYLES: Record<string, { color: string; bg: string; label: string }> = {
  high: { color: 'text-green-700 dark:text-green-400', bg: 'bg-green-100 dark:bg-green-900/30', label: 'High' },
  medium: { color: 'text-yellow-700 dark:text-yellow-400', bg: 'bg-yellow-100 dark:bg-yellow-900/30', label: 'Medium' },
  low: { color: 'text-red-700 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900/30', label: 'Low' },
};

// ─── Quick Predict Form ────────────────────────────────────────────────────

function QuickPredict() {
  const [tier, setTier] = useState(3);
  const [interactions, setInteractions] = useState(5);
  const [daysSince, setDaysSince] = useState(14);
  const [channel, setChannel] = useState('email');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);

  const handlePredict = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch('/ml/predict-response', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contact_tier: tier,
          interaction_count: interactions,
          days_since_last: daysSince,
          channel,
          program_value: '500000000',
          hiring_velocity: 3.0,
        }),
      });
      if (resp.ok) {
        setResult(await resp.json());
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [tier, interactions, daysSince, channel]);

  const catStyle = result ? CATEGORY_STYLES[result.category] : null;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4 flex items-center gap-2">
        <Brain className="w-4 h-4 text-blue-500" />
        Quick Response Prediction
      </h3>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Contact Tier</label>
          <select
            value={tier}
            onChange={(e) => setTier(Number(e.target.value))}
            className="w-full px-2 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
          >
            {[1, 2, 3, 4, 5, 6].map((t) => (
              <option key={t} value={t}>Tier {t}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Channel</label>
          <select
            value={channel}
            onChange={(e) => setChannel(e.target.value)}
            className="w-full px-2 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
          >
            <option value="email">Email</option>
            <option value="linkedin">LinkedIn</option>
            <option value="phone">Phone</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Past Interactions</label>
          <input
            type="number"
            value={interactions}
            onChange={(e) => setInteractions(Number(e.target.value))}
            min={0}
            max={50}
            className="w-full px-2 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
          />
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Days Since Last</label>
          <input
            type="number"
            value={daysSince}
            onChange={(e) => setDaysSince(Number(e.target.value))}
            min={0}
            className="w-full px-2 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
          />
        </div>
      </div>

      <button
        onClick={handlePredict}
        disabled={loading}
        className="w-full py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <TrendingUp className="w-4 h-4" />}
        Predict Response
      </button>

      {result && catStyle && (
        <div className="mt-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50 flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-500">Response Probability</p>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              {(result.probability * 100).toFixed(1)}%
            </p>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${catStyle.bg} ${catStyle.color}`}>
            {catStyle.label}
          </span>
        </div>
      )}
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────────

interface RecompetePrediction {
  program: string;
  expiry_date: string;
  months_remaining: number;
  value: number;
  incumbent: string;
  pts_past_performance: boolean;
  priority: string;
}

interface ChannelAnalysis {
  channel: string;
  total: number;
  success_rate: number;
  avg_response_days: number;
}

export function PredictiveInsights() {
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [signals, setSignals] = useState<HiringSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [signalsLoading, setSignalsLoading] = useState(false);
  const [recompetes, setRecompetes] = useState<RecompetePrediction[]>([]);
  const [channels, setChannels] = useState<ChannelAnalysis[]>([]);
  const [channelReco, setChannelReco] = useState('');

  // Fetch model status
  useEffect(() => {
    (async () => {
      try {
        const resp = await fetch('/ml/model-status');
        if (resp.ok) setModelStatus(await resp.json());
      } catch {
        // model not available yet
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // Fetch recompete predictions
  useEffect(() => {
    hubApiClient.getRecompetePredictions(18)
      .then(data => setRecompetes(data.recompetes || []))
      .catch(() => {/* endpoint not available */});
  }, []);

  // Fetch best channels
  useEffect(() => {
    hubApiClient.getBestChannels()
      .then(data => {
        setChannels(data.channels || []);
        setChannelReco(data.recommendation || '');
      })
      .catch(() => {/* endpoint not available */});
  }, []);

  // Fetch hiring signals
  const fetchSignals = useCallback(async (refresh = false) => {
    setSignalsLoading(true);
    try {
      const resp = await fetch(`/ml/hiring-signals?refresh=${refresh}`);
      if (resp.ok) {
        const data = await resp.json();
        setSignals(data.signals || []);
      }
    } catch {
      // signals not available
    } finally {
      setSignalsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSignals();
  }, [fetchSignals]);

  // Sort feature importances for chart
  const sortedFeatures = modelStatus?.feature_importance
    ? Object.entries(modelStatus.feature_importance).sort(([, a], [, b]) => b - a)
    : [];

  const maxImportance = sortedFeatures.length > 0 ? sortedFeatures[0][1] : 1;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-slate-500">Loading predictive models...</span>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
              <TrendingUp className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white">Predictive Insights</h1>
              <p className="text-sm text-slate-500">ML-powered response prediction and hiring signal detection</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Model Status Card */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-emerald-500" />
              Model Status
            </h3>

            {modelStatus?.loaded ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-green-700 dark:text-green-400 font-medium">Model Loaded</span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50">
                    <p className="text-[10px] text-slate-400 uppercase">Accuracy</p>
                    <p className="text-lg font-bold text-slate-900 dark:text-white">
                      {modelStatus.accuracy ? (modelStatus.accuracy * 100).toFixed(1) : '—'}%
                    </p>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50">
                    <p className="text-[10px] text-slate-400 uppercase">AUC</p>
                    <p className="text-lg font-bold text-slate-900 dark:text-white">
                      {modelStatus.auc ? modelStatus.auc.toFixed(3) : '—'}
                    </p>
                  </div>
                </div>

                {modelStatus.trained_at && (
                  <p className="text-[10px] text-slate-400">
                    Trained: {new Date(modelStatus.trained_at).toLocaleString()}
                  </p>
                )}

                {/* Feature Importance */}
                {sortedFeatures.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-slate-500 mb-2">Feature Importance</p>
                    <div className="space-y-1.5">
                      {sortedFeatures.map(([name, value]) => (
                        <div key={name} className="flex items-center gap-2">
                          <span className="text-[10px] text-slate-500 w-28 truncate">{name.replace(/_/g, ' ')}</span>
                          <div className="flex-1 h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-indigo-500 rounded-full"
                              style={{ width: `${(value / maxImportance) * 100}%` }}
                            />
                          </div>
                          <span className="text-[10px] text-slate-400 w-8 text-right">{(value * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-6">
                <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
                <p className="text-sm text-slate-500">Model not loaded</p>
                <p className="text-xs text-slate-400 mt-1">Start the API server to auto-train</p>
              </div>
            )}
          </div>

          {/* Quick Predict */}
          <QuickPredict />

          {/* Signal Summary */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                Signal Summary
              </h3>
              <button
                onClick={() => fetchSignals(true)}
                disabled={signalsLoading}
                className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-slate-400 ${signalsLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>

            {signals.length > 0 ? (
              <div className="space-y-3">
                {Object.entries(
                  signals.reduce<Record<string, number>>((acc, s) => {
                    acc[s.signal_type] = (acc[s.signal_type] || 0) + 1;
                    return acc;
                  }, {})
                ).map(([type, count]) => {
                  const style = SIGNAL_STYLES[type] || SIGNAL_STYLES.hiring_surge;
                  const Icon = style.icon;
                  return (
                    <div key={type} className={`flex items-center justify-between p-3 rounded-lg ${style.bg}`}>
                      <div className="flex items-center gap-2">
                        <Icon className={`w-4 h-4 ${style.color}`} />
                        <span className={`text-sm font-medium ${style.color}`}>{style.label}</span>
                      </div>
                      <span className={`text-lg font-bold ${style.color}`}>{count}</span>
                    </div>
                  );
                })}
                <p className="text-[10px] text-slate-400 text-center">
                  {signals.length} total signals detected
                </p>
              </div>
            ) : (
              <div className="text-center py-6">
                <CheckCircle2 className="w-8 h-8 text-green-400 mx-auto mb-2" />
                <p className="text-sm text-slate-500">No anomalies detected</p>
                <p className="text-xs text-slate-400 mt-1">All hiring patterns normal</p>
              </div>
            )}
          </div>
        </div>

        {/* Hiring Signals Table */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
          <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-blue-500" />
              Active Hiring Signals
            </h3>
            <span className="text-xs text-slate-400">{signals.length} signals</span>
          </div>

          {signals.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-700">
                    <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase">Type</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase">Program</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase">Location</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase">Confidence</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase">Details</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase">Detected</th>
                  </tr>
                </thead>
                <tbody>
                  {signals.map((signal, idx) => {
                    const style = SIGNAL_STYLES[signal.signal_type] || SIGNAL_STYLES.hiring_surge;
                    const Icon = style.icon;
                    const confPct = (signal.confidence * 100).toFixed(0);

                    return (
                      <tr key={idx} className="border-b border-slate-50 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-700/30">
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${style.bg} ${style.color}`}>
                            <Icon className="w-3 h-3" />
                            {style.label}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-medium text-slate-900 dark:text-white">{signal.program}</td>
                        <td className="py-3 px-4 text-slate-600 dark:text-slate-400">{signal.location}</td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  signal.confidence >= 0.8 ? 'bg-red-500' :
                                  signal.confidence >= 0.6 ? 'bg-amber-500' : 'bg-green-500'
                                }`}
                                style={{ width: `${signal.confidence * 100}%` }}
                              />
                            </div>
                            <span className="text-xs text-slate-500">{confPct}%</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-xs text-slate-500 max-w-xs truncate">
                          {signal.signal_type === 'hiring_surge' && signal.details.surge_ratio
                            ? `${signal.details.surge_ratio}x avg (${signal.details.latest_week_count} posts/wk)`
                            : signal.signal_type === 'new_capability' && signal.details.new_role
                            ? `New: ${signal.details.new_role}`
                            : signal.signal_type === 'clearance_escalation' && signal.details.new_clearance
                            ? `→ ${signal.details.new_clearance}`
                            : '—'}
                        </td>
                        <td className="py-3 px-4 text-xs text-slate-400">
                          {new Date(signal.detected_at).toLocaleDateString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 text-center">
              <Briefcase className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500">No hiring signals detected</p>
              <p className="text-xs text-slate-400 mt-1">Signals will appear when job posting anomalies are found</p>
            </div>
          )}
        </div>

        {/* Recompete Predictions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
            <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-700">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-orange-500" />
                Upcoming Recompetes
              </h3>
            </div>
            {recompetes.length > 0 ? (
              <div className="divide-y divide-slate-100 dark:divide-slate-700">
                {recompetes.slice(0, 8).map((rc, idx) => {
                  const urgency = rc.months_remaining <= 6 ? 'text-red-600 bg-red-50 dark:bg-red-900/20' :
                    rc.months_remaining <= 12 ? 'text-amber-600 bg-amber-50 dark:bg-amber-900/20' :
                    'text-blue-600 bg-blue-50 dark:bg-blue-900/20';
                  return (
                    <div key={idx} className="px-5 py-3 flex items-center justify-between">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">{rc.program}</p>
                        <p className="text-xs text-slate-500">{rc.incumbent || 'Unknown incumbent'}</p>
                      </div>
                      <div className="flex items-center gap-3 ml-3">
                        {rc.pts_past_performance && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 font-medium">
                            PTS PP
                          </span>
                        )}
                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${urgency}`}>
                          {rc.months_remaining}mo
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-12 text-center">
                <Calendar className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-sm text-slate-500">No recompete data available</p>
              </div>
            )}
          </div>

          {/* Best Channels */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
            <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-700">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
                <Phone className="w-4 h-4 text-green-500" />
                Best Outreach Channels
              </h3>
            </div>
            {channels.length > 0 ? (
              <div className="p-5 space-y-4">
                {channels.map((ch, idx) => {
                  const maxTotal = Math.max(...channels.map(c => c.total), 1);
                  return (
                    <div key={idx}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize">{ch.channel}</span>
                        <div className="flex items-center gap-3 text-xs text-slate-500">
                          <span>{ch.total} activities</span>
                          <span className={`font-medium ${ch.success_rate >= 0.3 ? 'text-green-600' : ch.success_rate >= 0.15 ? 'text-amber-600' : 'text-slate-400'}`}>
                            {(ch.success_rate * 100).toFixed(0)}% success
                          </span>
                        </div>
                      </div>
                      <div className="w-full h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-green-500 rounded-full transition-all"
                          style={{ width: `${(ch.total / maxTotal) * 100}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
                {channelReco && (
                  <div className="mt-3 p-3 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800">
                    <p className="text-xs text-indigo-700 dark:text-indigo-300">
                      <span className="font-semibold">Recommendation:</span> {channelReco}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-12 text-center">
                <Phone className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-sm text-slate-500">No channel data available</p>
                <p className="text-xs text-slate-400 mt-1">Log outreach activities to see channel performance</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
