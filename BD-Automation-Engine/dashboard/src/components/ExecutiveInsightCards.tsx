import { useState, useEffect } from 'react';
import { Bell, Swords, Calendar, Clock, ChevronRight, AlertTriangle, Loader2 } from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

// ─── Recent Alerts Card ──────────────────────────────────────────────────────

interface RecentAlertsProps {
  onNavigate?: () => void;
}

export function RecentAlertsCard({ onNavigate }: RecentAlertsProps) {
  const [alerts, setAlerts] = useState<Array<{ id: string; title: string; priority: string; created_at: string }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const res = await hubApiClient.getNotifications(true, 5);
        if (mounted) setAlerts(res.notifications);
      } catch { /* skip */ }
      finally { if (mounted) setLoading(false); }
    }
    load();
    const interval = setInterval(load, 60000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  const priorityDot: Record<string, string> = {
    critical: 'bg-red-500',
    warning: 'bg-amber-500',
    info: 'bg-blue-500',
  };

  return (
    <div
      className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onNavigate}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onNavigate?.()}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-amber-50 dark:bg-amber-900/30">
            <Bell className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          </div>
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Recent Alerts</h3>
        </div>
        <ChevronRight className="h-4 w-4 text-slate-400" />
      </div>
      {loading ? (
        <div className="flex justify-center py-3"><Loader2 className="h-4 w-4 animate-spin text-slate-400" /></div>
      ) : alerts.length === 0 ? (
        <p className="text-xs text-slate-400 text-center py-3">No unread alerts</p>
      ) : (
        <div className="space-y-2">
          {alerts.slice(0, 5).map((a) => (
            <div key={a.id} className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${priorityDot[a.priority] || priorityDot.info}`} />
              <span className="text-xs text-slate-700 dark:text-slate-300 truncate flex-1">{a.title}</span>
              <span className="text-[10px] text-slate-400 flex-shrink-0">
                {timeAgo(a.created_at)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Competitive Pulse Card ──────────────────────────────────────────────────

interface CompetitivePulseProps {
  onNavigate?: () => void;
}

export function CompetitivePulseCard({ onNavigate }: CompetitivePulseProps) {
  const [data, setData] = useState<{
    competitors: Array<{ name: string; recent_awards: number; total_value_usd: number }>;
    expiring_soon: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const res = await hubApiClient.getCompetitiveSummary();
        if (mounted) setData(res);
      } catch { /* skip */ }
      finally { if (mounted) setLoading(false); }
    }
    load();
    return () => { mounted = false; };
  }, []);

  const formatUSD = (v: number) => {
    if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
    if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
    return `$${(v / 1e3).toFixed(0)}K`;
  };

  return (
    <div
      className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onNavigate}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onNavigate?.()}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-red-50 dark:bg-red-900/30">
            <Swords className="h-4 w-4 text-red-600 dark:text-red-400" />
          </div>
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Competitive Pulse</h3>
        </div>
        <ChevronRight className="h-4 w-4 text-slate-400" />
      </div>
      {loading ? (
        <div className="flex justify-center py-3"><Loader2 className="h-4 w-4 animate-spin text-slate-400" /></div>
      ) : !data ? (
        <p className="text-xs text-slate-400 text-center py-3">No data available</p>
      ) : (
        <>
          <div className="space-y-1.5 mb-2">
            {data.competitors.slice(0, 3).map((c) => (
              <div key={c.name} className="flex items-center justify-between">
                <span className="text-xs text-slate-700 dark:text-slate-300">{c.name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-400">{c.recent_awards} awards</span>
                  <span className="text-xs font-bold text-slate-900 dark:text-slate-100">{formatUSD(c.total_value_usd)}</span>
                </div>
              </div>
            ))}
          </div>
          {data.expiring_soon > 0 && (
            <div className="pt-2 border-t border-slate-100 dark:border-slate-700 flex items-center gap-1.5">
              <AlertTriangle className="h-3 w-3 text-amber-500" />
              <span className="text-[10px] text-amber-600 dark:text-amber-400">{data.expiring_soon} contracts expiring soon</span>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── Upcoming Meetings Card ──────────────────────────────────────────────────

interface UpcomingMeetingsProps {
  onNavigate?: () => void;
}

export function UpcomingMeetingsCard({ onNavigate }: UpcomingMeetingsProps) {
  // Mock upcoming meetings (in production would come from calendar API)
  const meetings = [
    { id: '1', title: 'DCGS Program Review', time: 'Tomorrow 10:00 AM', contact: 'J. Smith (GDIT)' },
    { id: '2', title: 'ISR Capture Strategy', time: 'Wed 2:00 PM', contact: 'M. Johnson (Leidos)' },
    { id: '3', title: 'SIGINT Integration Call', time: 'Fri 11:00 AM', contact: 'K. Ero (BAE)' },
  ];

  return (
    <div
      className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onNavigate}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onNavigate?.()}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-cyan-50 dark:bg-cyan-900/30">
            <Calendar className="h-4 w-4 text-cyan-600 dark:text-cyan-400" />
          </div>
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Upcoming Meetings</h3>
        </div>
        <ChevronRight className="h-4 w-4 text-slate-400" />
      </div>
      <div className="space-y-2">
        {meetings.map((m) => (
          <div key={m.id} className="flex items-start gap-2">
            <Clock className="h-3 w-3 text-slate-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-slate-700 dark:text-slate-300 truncate">{m.title}</p>
              <p className="text-[10px] text-slate-400">{m.time} &bull; {m.contact}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Helper ──────────────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'now';
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}
