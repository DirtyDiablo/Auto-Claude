import { useState, useEffect, useCallback } from 'react';
import {
  Plug, Loader2, RefreshCw, CheckCircle2, XCircle, AlertTriangle,
  MessageSquare, Database, BookOpen, Send, ArrowDownUp,
} from 'lucide-react';

// ─── Types ─────────────────────────────────────────────────────────────────

interface SlackStatus {
  connected: boolean;
  mode: string;
  message_count: number;
  last_sent: string | null;
}

interface CRMStatus {
  connected: boolean;
  db_size_mb: number;
  last_sync: string | null;
  records_pushed: number;
  records_pulled: number;
  queue_total: number;
  queue_pending: number;
  errors: string[];
}

interface SyncLogEntry {
  timestamp: string;
  action: string;
  [key: string]: unknown;
}

// ─── Status Indicator ──────────────────────────────────────────────────────

function StatusDot({ status }: { status: 'green' | 'yellow' | 'red' }) {
  const colors = {
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
  };
  return (
    <div className="relative flex items-center justify-center">
      <div className={`w-2.5 h-2.5 rounded-full ${colors[status]}`} />
      {status === 'green' && (
        <div className={`absolute w-2.5 h-2.5 rounded-full ${colors[status]} animate-ping opacity-50`} />
      )}
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────────

export function Integrations() {
  const [slackStatus, setSlackStatus] = useState<SlackStatus | null>(null);
  const [crmStatus, setCrmStatus] = useState<CRMStatus | null>(null);
  const [syncLog, setSyncLog] = useState<SyncLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [testingSlack, setTestingSlack] = useState(false);

  // Fetch all statuses
  const fetchStatuses = useCallback(async () => {
    const [slackResp, crmResp, logResp] = await Promise.allSettled([
      fetch('/integrations/slack/status'),
      fetch('/integrations/crm/status'),
      fetch('/integrations/crm/log?limit=20'),
    ]);

    if (slackResp.status === 'fulfilled' && slackResp.value.ok) {
      setSlackStatus(await slackResp.value.json());
    }
    if (crmResp.status === 'fulfilled' && crmResp.value.ok) {
      setCrmStatus(await crmResp.value.json());
    }
    if (logResp.status === 'fulfilled' && logResp.value.ok) {
      const data = await logResp.value.json();
      setSyncLog(data.log || []);
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    fetchStatuses();
  }, [fetchStatuses]);

  // Trigger CRM sync
  const handleSync = useCallback(async () => {
    setSyncing(true);
    try {
      await fetch('/integrations/crm/sync', { method: 'POST' });
      await fetchStatuses();
    } catch {
      // ignore
    } finally {
      setSyncing(false);
    }
  }, [fetchStatuses]);

  // Test Slack notification
  const handleTestSlack = useCallback(async () => {
    setTestingSlack(true);
    try {
      await fetch('/integrations/slack/notify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: '#bd-test',
          message: 'Test notification from BD Intelligence Dashboard',
        }),
      });
      await fetchStatuses();
    } catch {
      // ignore
    } finally {
      setTestingSlack(false);
    }
  }, [fetchStatuses]);

  // Trigger daily digest
  const handleDigest = useCallback(async () => {
    try {
      await fetch('/integrations/slack/digest', { method: 'POST' });
      await fetchStatuses();
    } catch {
      // ignore
    }
  }, [fetchStatuses]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-slate-500">Loading integration status...</span>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-violet-100 dark:bg-violet-900/30">
            <Plug className="w-5 h-5 text-violet-600 dark:text-violet-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">Integrations</h1>
            <p className="text-sm text-slate-500">Manage connections to Slack, CRM, and external services</p>
          </div>
        </div>

        {/* Integration Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Slack Card */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
                  <MessageSquare className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Slack</h3>
                  <p className="text-xs text-slate-500">Notifications & Commands</p>
                </div>
              </div>
              <StatusDot status={slackStatus?.connected ? 'green' : slackStatus?.mode === 'jsonl_fallback' ? 'yellow' : 'red'} />
            </div>

            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Mode</span>
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  {slackStatus?.connected ? 'Live' : 'JSONL Fallback'}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Messages Sent</span>
                <span className="font-medium text-slate-700 dark:text-slate-300">{slackStatus?.message_count ?? 0}</span>
              </div>
              {slackStatus?.last_sent && (
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Last Sent</span>
                  <span className="text-slate-400">{new Date(slackStatus.last_sent).toLocaleString()}</span>
                </div>
              )}
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleTestSlack}
                disabled={testingSlack}
                className="flex-1 py-1.5 text-xs font-medium rounded-lg bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 hover:bg-purple-200 dark:hover:bg-purple-900/50 disabled:opacity-50 flex items-center justify-center gap-1"
              >
                {testingSlack ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                Test
              </button>
              <button
                onClick={handleDigest}
                className="flex-1 py-1.5 text-xs font-medium rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center gap-1"
              >
                <BookOpen className="w-3 h-3" />
                Digest
              </button>
            </div>
          </div>

          {/* Bullhorn CRM Card */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
                  <Database className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Bullhorn CRM</h3>
                  <p className="text-xs text-slate-500">Bidirectional Sync</p>
                </div>
              </div>
              <StatusDot status={crmStatus?.connected ? 'green' : 'red'} />
            </div>

            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Database</span>
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  {crmStatus?.connected ? `${crmStatus.db_size_mb} MB` : 'Not Found'}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Records Pulled</span>
                <span className="font-medium text-slate-700 dark:text-slate-300">{crmStatus?.records_pulled ?? 0}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Queue Pending</span>
                <span className={`font-medium ${(crmStatus?.queue_pending ?? 0) > 0 ? 'text-amber-600' : 'text-slate-700 dark:text-slate-300'}`}>
                  {crmStatus?.queue_pending ?? 0}
                </span>
              </div>
              {crmStatus?.last_sync && (
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Last Sync</span>
                  <span className="text-slate-400">{new Date(crmStatus.last_sync).toLocaleString()}</span>
                </div>
              )}
            </div>

            <button
              onClick={handleSync}
              disabled={syncing || !crmStatus?.connected}
              className="w-full py-1.5 text-xs font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-1.5"
            >
              {syncing ? <Loader2 className="w-3 h-3 animate-spin" /> : <ArrowDownUp className="w-3 h-3" />}
              {syncing ? 'Syncing...' : 'Sync Now'}
            </button>

            {crmStatus?.errors && crmStatus.errors.length > 0 && (
              <div className="mt-2 p-2 rounded-lg bg-red-50 dark:bg-red-900/20">
                <p className="text-[10px] text-red-600 dark:text-red-400">
                  {crmStatus.errors[crmStatus.errors.length - 1]}
                </p>
              </div>
            )}
          </div>

          {/* Notion Card */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-slate-100 dark:bg-slate-700">
                  <BookOpen className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Notion</h3>
                  <p className="text-xs text-slate-500">Database Sync</p>
                </div>
              </div>
              <StatusDot status="yellow" />
            </div>

            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Status</span>
                <span className="font-medium text-slate-700 dark:text-slate-300">Configured</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Databases</span>
                <span className="font-medium text-slate-700 dark:text-slate-300">5 connected</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Direction</span>
                <span className="text-slate-400">Read-only</span>
              </div>
            </div>

            <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50">
              <p className="text-[10px] text-slate-500 text-center">
                Notion sync managed via API settings
              </p>
            </div>
          </div>
        </div>

        {/* Sync Log */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
          <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-slate-400" />
              Sync Activity Log
            </h3>
            <button onClick={fetchStatuses} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
              <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
            </button>
          </div>

          {syncLog.length > 0 ? (
            <div className="max-h-64 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-white dark:bg-slate-800">
                  <tr className="border-b border-slate-100 dark:border-slate-700">
                    <th className="text-left py-2 px-4 text-xs font-medium text-slate-500 uppercase">Time</th>
                    <th className="text-left py-2 px-4 text-xs font-medium text-slate-500 uppercase">Action</th>
                    <th className="text-left py-2 px-4 text-xs font-medium text-slate-500 uppercase">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {[...syncLog].reverse().map((entry, idx) => (
                    <tr key={idx} className="border-b border-slate-50 dark:border-slate-700/50">
                      <td className="py-2 px-4 text-xs text-slate-400">
                        {new Date(entry.timestamp).toLocaleString()}
                      </td>
                      <td className="py-2 px-4">
                        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 font-medium">
                          {entry.action}
                        </span>
                      </td>
                      <td className="py-2 px-4 text-xs text-slate-500">
                        {Object.entries(entry)
                          .filter(([k]) => !['timestamp', 'action', 'last_placement_id', 'last_activity_id'].includes(k))
                          .map(([k, v]) => `${k}: ${v}`)
                          .join(', ') || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-8 text-center">
              <ArrowDownUp className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-sm text-slate-500">No sync activity yet</p>
              <p className="text-xs text-slate-400 mt-1">Trigger a sync to see activity here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
