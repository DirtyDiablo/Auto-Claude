import { useState, useEffect } from 'react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import {
  Swords, Trophy, MapPin, Loader2, Clock, Users,
} from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Competitor {
  name: string;
  recent_awards: number;
  total_value_usd: number;
  hiring_activity: number;
  top_locations: Array<[string, number]>;
  latest_award: string | null;
}

interface MarketShare {
  name: string;
  value_usd: number;
  share_pct: number;
  [key: string]: unknown;
}

interface Award {
  id: string;
  title: string;
  agency: string;
  contractor: string;
  value_usd: number;
  award_date: string;
  period: string;
}

interface ExpiringContract {
  id: string;
  title: string;
  agency: string;
  incumbent: string;
  value_usd: number;
  expiry_date: string;
  months_remaining: number;
  recompete_likely: boolean;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const COMPETITOR_COLORS: Record<string, string> = {
  'GDIT': '#3b82f6',
  'Leidos': '#8b5cf6',
  'SAIC': '#06b6d4',
  'CACI': '#f59e0b',
  'Peraton': '#ef4444',
  'BAE Systems': '#22c55e',
};

const PIE_COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4', '#f59e0b', '#ef4444', '#22c55e', '#ec4899', '#6366f1'];

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatUSD(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(0)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value}`;
}

function daysAgo(dateStr: string): string {
  const d = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86400000);
  if (d === 0) return 'Today';
  if (d === 1) return '1 day ago';
  return `${d}d ago`;
}

// ─── Component ───────────────────────────────────────────────────────────────

export function CompetitiveLandscape() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [marketShare, setMarketShare] = useState<MarketShare[]>([]);
  const [awards, setAwards] = useState<Award[]>([]);
  const [expiring, setExpiring] = useState<ExpiringContract[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalMarket, setTotalMarket] = useState(0);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const [summaryRes, awardsRes, expiringRes] = await Promise.all([
          hubApiClient.getCompetitiveSummary(),
          hubApiClient.getContractAwards(90),
          hubApiClient.getExpiringContracts(9),
        ]);
        if (!mounted) return;
        setCompetitors(summaryRes.competitors);
        setMarketShare(summaryRes.market_share);
        setTotalMarket(summaryRes.total_market_value);
        setAwards(awardsRes.awards);
        setExpiring(expiringRes.contracts);
      } catch {
        // API not available
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
      </div>
    );
  }

  // Build hiring heatmap data
  const heatmapData: Record<string, Record<string, number>> = {};
  for (const c of competitors) {
    heatmapData[c.name] = {};
    for (const [loc, count] of c.top_locations) {
      heatmapData[c.name][loc] = count;
    }
  }
  const locations = [...new Set(competitors.flatMap(c => c.top_locations.map(l => l[0])))].sort();
  const maxHiring = Math.max(1, ...competitors.flatMap(c => c.top_locations.map(l => l[1])));

  return (
    <div className="h-full overflow-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Swords className="w-8 h-8 text-red-600" />
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Competitive Landscape</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              DCGS portfolio competitive intelligence &bull; {formatUSD(totalMarket)} total market
            </p>
          </div>
        </div>
      </div>

      {/* Competitor Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {competitors.map((c) => {
          const color = COMPETITOR_COLORS[c.name] || '#6b7280';
          return (
            <div
              key={c.name}
              className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">{c.name}</h3>
                </div>
                <span className="text-lg font-bold" style={{ color }}>
                  {formatUSD(c.total_value_usd)}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="text-center">
                  <Trophy className="h-4 w-4 text-amber-500 mx-auto mb-1" />
                  <p className="text-lg font-bold text-slate-900 dark:text-slate-100">{c.recent_awards}</p>
                  <p className="text-[10px] text-slate-400">Awards</p>
                </div>
                <div className="text-center">
                  <Users className="h-4 w-4 text-blue-500 mx-auto mb-1" />
                  <p className="text-lg font-bold text-slate-900 dark:text-slate-100">{c.hiring_activity}</p>
                  <p className="text-[10px] text-slate-400">Hiring</p>
                </div>
                <div className="text-center">
                  <MapPin className="h-4 w-4 text-green-500 mx-auto mb-1" />
                  <p className="text-lg font-bold text-slate-900 dark:text-slate-100">{c.top_locations.length}</p>
                  <p className="text-[10px] text-slate-400">Locations</p>
                </div>
              </div>
              {c.latest_award && (
                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                  Latest: {c.latest_award}
                </p>
              )}
            </div>
          );
        })}
      </div>

      {/* Award Timeline + Market Share */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Award Timeline */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
          <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4">Recent Contract Awards</h2>
          <div className="space-y-3 max-h-[320px] overflow-y-auto">
            {awards
              .sort((a, b) => new Date(b.award_date).getTime() - new Date(a.award_date).getTime())
              .map((award) => {
                const color = COMPETITOR_COLORS[award.contractor] || '#6b7280';
                return (
                  <div
                    key={award.id}
                    className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50 border-l-3"
                    style={{ borderLeftColor: color }}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-bold" style={{ color }}>{award.contractor}</span>
                        <span className="text-[10px] text-slate-400">{award.agency}</span>
                      </div>
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">{award.title}</p>
                      <p className="text-xs text-slate-400 font-mono">{award.id}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="text-sm font-bold text-slate-900 dark:text-slate-100">{formatUSD(award.value_usd)}</p>
                      <p className="text-[10px] text-slate-400">{daysAgo(award.award_date)}</p>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* Market Share Donut */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
          <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4">DCGS Market Share (by Award Value)</h2>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={marketShare}
                dataKey="value_usd"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={95}
                label={(props) => {
                  const entry = marketShare[props.index ?? 0];
                  return `${entry?.name ?? ''} ${entry?.share_pct ?? 0}%`;
                }}
                labelLine={false}
              >
                {marketShare.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => formatUSD(Number(value))}
                contentStyle={{ fontSize: 11 }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Hiring Heatmap + Expiring Contracts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hiring Heatmap */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
          <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4">Hiring Heatmap (Competitor x Location)</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr>
                  <th className="text-left py-2 px-2 text-slate-500 font-medium">Competitor</th>
                  {locations.map((loc) => (
                    <th key={loc} className="text-center py-2 px-1 text-slate-500 font-medium">
                      <span className="block truncate max-w-[70px]" title={loc}>
                        {loc.split(',')[0]}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {competitors.map((c) => (
                  <tr key={c.name} className="border-t border-slate-100 dark:border-slate-700/50">
                    <td className="py-2 px-2 font-medium text-slate-700 dark:text-slate-300">{c.name}</td>
                    {locations.map((loc) => {
                      const val = heatmapData[c.name]?.[loc] || 0;
                      const intensity = val / maxHiring;
                      const bg = val === 0
                        ? 'bg-slate-100 dark:bg-slate-700/30'
                        : intensity > 0.7
                          ? 'bg-red-500 text-white'
                          : intensity > 0.4
                            ? 'bg-amber-400 text-amber-900'
                            : 'bg-green-200 dark:bg-green-900/40 text-green-800 dark:text-green-300';
                      return (
                        <td key={loc} className="py-1.5 px-1 text-center">
                          <span className={`inline-block w-8 h-6 rounded text-[10px] font-bold leading-6 ${bg}`}>
                            {val || '-'}
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Expiring Contracts */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Expiring Contracts (Recompete Opportunities)</h2>
            <span className="text-xs text-amber-600 dark:text-amber-400 font-medium">{expiring.length} contracts</span>
          </div>
          <div className="space-y-3">
            {expiring.map((c) => (
              <div
                key={c.id}
                className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600"
              >
                <div className="flex items-start justify-between mb-1">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">{c.title}</p>
                    <p className="text-xs text-slate-500">{c.agency} &bull; Incumbent: {c.incumbent}</p>
                  </div>
                  <span className="text-sm font-bold text-slate-900 dark:text-slate-100 ml-2">{formatUSD(c.value_usd)}</span>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <div className="flex items-center gap-2">
                    <Clock className="h-3 w-3 text-amber-500" />
                    <span className={`text-xs font-medium ${c.months_remaining <= 4 ? 'text-red-600' : 'text-amber-600'}`}>
                      {c.months_remaining}mo remaining
                    </span>
                  </div>
                  {c.recompete_likely && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                      Recompete likely
                    </span>
                  )}
                </div>
              </div>
            ))}
            {expiring.length === 0 && (
              <p className="text-sm text-slate-400 text-center py-4">No contracts expiring within horizon</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
