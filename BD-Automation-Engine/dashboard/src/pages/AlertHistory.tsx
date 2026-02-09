import { useState, useEffect, useCallback } from 'react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import {
  Bell, Filter, CheckCheck, Eye, Loader2,
  Briefcase, FileText, AlertTriangle, Calendar, Send,
  Clock, RefreshCw,
} from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  entity_type: string | null;
  entity_id: string | null;
  created_at: string;
  read_at: string | null;
  priority: string;
}

type TypeFilter = 'all' | 'new_jobs' | 'contract_update' | 'stale_data' | 'meeting' | 'outreach';
type PriorityFilter = 'all' | 'critical' | 'warning' | 'info';

// ─── Constants ───────────────────────────────────────────────────────────────

const TYPE_CONFIG: Record<string, { icon: React.ComponentType<{ className?: string }>; label: string; color: string }> = {
  new_jobs: { icon: Briefcase, label: 'Jobs', color: '#3b82f6' },
  contract_update: { icon: FileText, label: 'Contracts', color: '#8b5cf6' },
  stale_data: { icon: AlertTriangle, label: 'Stale Data', color: '#f59e0b' },
  meeting: { icon: Calendar, label: 'Meetings', color: '#06b6d4' },
  outreach: { icon: Send, label: 'Outreach', color: '#22c55e' },
  contacts_enriched: { icon: RefreshCw, label: 'Enrichment', color: '#ec4899' },
  alert: { icon: Bell, label: 'Alert', color: '#ef4444' },
};

const PRIORITY_STYLES: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  warning: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  info: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
};

const PIE_COLORS = ['#3b82f6', '#8b5cf6', '#f59e0b', '#06b6d4', '#22c55e', '#ec4899', '#ef4444'];

// ─── Component ───────────────────────────────────────────────────────────────

export function AlertHistory() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('all');
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>('all');
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await hubApiClient.getNotifications(false, 200);
      setNotifications(res.notifications);
    } catch {
      // API not available
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleMarkAllRead = async () => {
    const unread = notifications.filter(n => !n.read_at);
    for (const n of unread) {
      try {
        await hubApiClient.markNotificationRead(n.id);
      } catch { /* skip */ }
    }
    fetchData();
  };

  const handleMarkRead = async (id: string) => {
    try {
      await hubApiClient.markNotificationRead(id);
      setNotifications(prev =>
        prev.map(n => n.id === id ? { ...n, read_at: new Date().toISOString() } : n)
      );
    } catch { /* skip */ }
  };

  // Filter logic
  const filtered = notifications.filter(n => {
    if (showUnreadOnly && n.read_at) return false;
    if (typeFilter !== 'all' && n.type !== typeFilter) return false;
    if (priorityFilter !== 'all' && n.priority !== priorityFilter) return false;
    return true;
  });

  // Stats for charts
  const typeCounts: Record<string, number> = {};
  for (const n of notifications) {
    typeCounts[n.type] = (typeCounts[n.type] || 0) + 1;
  }
  const typeChartData = Object.entries(typeCounts).map(([type, count]) => ({
    name: TYPE_CONFIG[type]?.label || type,
    value: count,
  }));

  // Alerts over time (group by date)
  const dateCounts: Record<string, number> = {};
  for (const n of notifications) {
    const date = n.created_at.slice(0, 10);
    dateCounts[date] = (dateCounts[date] || 0) + 1;
  }
  const timelineData = Object.entries(dateCounts)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({ date: date.slice(5), count }));

  const unreadCount = notifications.filter(n => !n.read_at).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bell className="w-8 h-8 text-amber-600" />
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Alert History</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {notifications.length} total alerts &bull; {unreadCount} unread
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-3 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <CheckCheck className="w-4 h-4" /> Mark All Read
            </button>
          )}
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <span className="text-xs text-slate-500 font-medium">Type:</span>
            {(['all', 'new_jobs', 'contract_update', 'stale_data', 'meeting', 'outreach'] as TypeFilter[]).map(t => (
              <button
                key={t}
                onClick={() => setTypeFilter(t)}
                className={`px-2.5 py-1 text-xs rounded-lg transition-colors ${
                  typeFilter === t
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'
                }`}
              >
                {t === 'all' ? 'All' : TYPE_CONFIG[t]?.label || t}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Priority:</span>
            {(['all', 'critical', 'warning', 'info'] as PriorityFilter[]).map(p => (
              <button
                key={p}
                onClick={() => setPriorityFilter(p)}
                className={`px-2.5 py-1 text-xs rounded-lg transition-colors capitalize ${
                  priorityFilter === p
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
          <label className="flex items-center gap-2 text-xs text-slate-500 cursor-pointer ml-auto">
            <input
              type="checkbox"
              checked={showUnreadOnly}
              onChange={(e) => setShowUnreadOnly(e.target.checked)}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            Unread only
          </label>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* By Type */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">Alerts by Type</h3>
          {typeChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={typeChartData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={35}
                  outerRadius={65}
                  label={(props) => {
                    const entry = typeChartData[props.index ?? 0];
                    return `${entry?.name ?? ''}: ${entry?.value ?? 0}`;
                  }}
                  labelLine={false}
                >
                  {typeChartData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-400 text-center py-8">No data</p>
          )}
        </div>

        {/* Over Time */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">Alerts Over Time</h3>
          {timelineData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
                <Tooltip contentStyle={{ fontSize: 11 }} />
                <Area type="monotone" dataKey="count" fill="#3b82f6" fillOpacity={0.2} stroke="#3b82f6" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-400 text-center py-8">No data</p>
          )}
        </div>
      </div>

      {/* Alert List */}
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Alerts ({filtered.length})
          </h2>
        </div>
        <div className="divide-y divide-slate-100 dark:divide-slate-700">
          {filtered.length === 0 && (
            <div className="px-5 py-12 text-center text-slate-400">
              <Bell className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No alerts match your filters</p>
            </div>
          )}
          {filtered
            .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
            .map((n) => {
              const config = TYPE_CONFIG[n.type] || TYPE_CONFIG.alert;
              const Icon = config.icon;
              const isUnread = !n.read_at;
              return (
                <div
                  key={n.id}
                  className={`px-5 py-4 flex items-start gap-4 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors ${
                    isUnread ? 'bg-blue-50/50 dark:bg-blue-900/10' : ''
                  }`}
                >
                  <div
                    className="p-2 rounded-lg flex-shrink-0"
                    style={{ backgroundColor: `${config.color}15`, color: config.color }}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <p className={`text-sm font-medium ${isUnread ? 'text-slate-900 dark:text-slate-100' : 'text-slate-600 dark:text-slate-400'}`}>
                        {n.title}
                      </p>
                      {isUnread && (
                        <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">{n.message}</p>
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1 text-[10px] text-slate-400">
                        <Clock className="h-3 w-3" />
                        {new Date(n.created_at).toLocaleString()}
                      </span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded capitalize ${PRIORITY_STYLES[n.priority] || PRIORITY_STYLES.info}`}>
                        {n.priority}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    {isUnread && (
                      <button
                        onClick={() => handleMarkRead(n.id)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                        title="Mark as read"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
}
