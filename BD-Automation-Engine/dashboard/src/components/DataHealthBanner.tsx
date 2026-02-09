import { useState, useEffect } from 'react';
import { Database, AlertTriangle, CheckCircle2, XCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

interface CollectionFreshness {
  count: number;
  last_indexed: string | null;
  staleness_days: number | null;
  status: string;
}

interface FreshnessData {
  collections: Record<string, CollectionFreshness>;
  scraper_last_run: string | null;
  tango_last_sync: string | null;
  alerts: Array<{ level: string; message: string }>;
  timestamp: string;
}

function StalenessIndicator({ days }: { days: number | null }) {
  if (days === null || days < 0) {
    return <span className="inline-flex items-center gap-1 text-xs text-slate-400"><span className="w-2 h-2 rounded-full bg-slate-300" />Unknown</span>;
  }
  if (days === 0) {
    return <span className="inline-flex items-center gap-1 text-xs text-green-600 dark:text-green-400"><span className="w-2 h-2 rounded-full bg-green-500" />Today</span>;
  }
  if (days <= 3) {
    return <span className="inline-flex items-center gap-1 text-xs text-green-600 dark:text-green-400"><span className="w-2 h-2 rounded-full bg-green-500" />{days}d ago</span>;
  }
  if (days <= 7) {
    return <span className="inline-flex items-center gap-1 text-xs text-yellow-600 dark:text-yellow-400"><span className="w-2 h-2 rounded-full bg-yellow-500" />{days}d ago</span>;
  }
  if (days <= 14) {
    return <span className="inline-flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400"><span className="w-2 h-2 rounded-full bg-amber-500" />{days}d stale</span>;
  }
  return <span className="inline-flex items-center gap-1 text-xs text-red-600 dark:text-red-400"><span className="w-2 h-2 rounded-full bg-red-500" />{days}d stale</span>;
}

function overallHealth(data: FreshnessData): 'green' | 'yellow' | 'red' {
  const criticals = data.alerts.filter(a => a.level === 'critical').length;
  const warnings = data.alerts.filter(a => a.level === 'warning').length;
  if (criticals > 0) return 'red';
  if (warnings > 0) return 'yellow';
  return 'green';
}

const HEALTH_STYLES = {
  green: {
    bg: 'bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20',
    border: 'border-green-200 dark:border-green-800',
    icon: CheckCircle2,
    iconColor: 'text-green-600 dark:text-green-400',
    label: 'All Systems Fresh',
  },
  yellow: {
    bg: 'bg-gradient-to-r from-amber-50 to-yellow-50 dark:from-amber-900/20 dark:to-yellow-900/20',
    border: 'border-amber-200 dark:border-amber-800',
    icon: AlertTriangle,
    iconColor: 'text-amber-600 dark:text-amber-400',
    label: 'Some Data Stale',
  },
  red: {
    bg: 'bg-gradient-to-r from-red-50 to-rose-50 dark:from-red-900/20 dark:to-rose-900/20',
    border: 'border-red-200 dark:border-red-800',
    icon: XCircle,
    iconColor: 'text-red-600 dark:text-red-400',
    label: 'Data Critically Stale',
  },
};

export function DataHealthBanner() {
  const [data, setData] = useState<FreshnessData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function fetch() {
      try {
        const result = await hubApiClient.getDataFreshness();
        if (mounted) setData(result);
      } catch {
        // API not available
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetch();
    const interval = setInterval(fetch, 120000); // Refresh every 2 min
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  if (loading || !data) return null;

  const health = overallHealth(data);
  const style = HEALTH_STYLES[health];
  const StatusIcon = style.icon;
  const collections = Object.entries(data.collections);

  return (
    <div className={`rounded-xl border ${style.border} ${style.bg} overflow-hidden transition-all`}>
      {/* Summary bar */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:opacity-90 transition-opacity"
      >
        <div className="flex items-center gap-3">
          <StatusIcon className={`h-5 w-5 ${style.iconColor}`} />
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              Data Health: {style.label}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {collections.length} collections
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {data.alerts.filter(a => a.level !== 'info').length > 0 && (
            <span className="text-xs bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300 px-2 py-0.5 rounded-full">
              {data.alerts.filter(a => a.level !== 'info').length} alerts
            </span>
          )}
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          )}
        </div>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* Collection grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
            {collections.map(([name, info]) => (
              <div
                key={name}
                className="bg-white/80 dark:bg-slate-800/60 rounded-lg px-3 py-2 border border-slate-200/50 dark:border-slate-700/50"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300 capitalize">{name}</span>
                  <Database className="h-3 w-3 text-slate-400" />
                </div>
                <p className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  {info.count.toLocaleString()}
                </p>
                <StalenessIndicator days={info.staleness_days} />
              </div>
            ))}
          </div>

          {/* Alerts */}
          {data.alerts.filter(a => a.level !== 'info').length > 0 && (
            <div className="space-y-1">
              {data.alerts.filter(a => a.level !== 'info').map((alert, i) => (
                <div
                  key={i}
                  className={`text-xs px-3 py-1.5 rounded-lg ${
                    alert.level === 'critical'
                      ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
                      : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
                  }`}
                >
                  {alert.message}
                </div>
              ))}
            </div>
          )}

          {/* Source timestamps */}
          <div className="flex gap-4 text-[10px] text-slate-500 dark:text-slate-400">
            {data.scraper_last_run && (
              <span>Scraper: {new Date(data.scraper_last_run).toLocaleString()}</span>
            )}
            {data.tango_last_sync && (
              <span>Tango: {new Date(data.tango_last_sync).toLocaleString()}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
