import { useState, useEffect, useCallback } from 'react';
import {
  Bot, Loader2, Play, Clock, CheckCircle2, XCircle, AlertTriangle,
  RefreshCw, Calendar, Users, FileText, Zap,
} from 'lucide-react';

// ─── Types ─────────────────────────────────────────────────────────────────

interface AgentSchedule {
  agent: string;
  name: string;
  schedule: string;
  next_run: string | null;
  last_run: AgentRun | null;
}

interface AgentRun {
  agent: string;
  start_time: string;
  end_time: string;
  status: string;
  summary: string;
}

interface DailyBrief {
  date: string;
  generated_at: string;
  executive_summary: string;
  hiring_signals: unknown[];
  pipeline_snapshot: Record<string, number>;
  new_opportunities: unknown[];
  priority_contacts: unknown[];
  contract_updates: unknown[];
}

interface EnrichmentReport {
  scan_date: string;
  contacts_scanned: number;
  stale_contacts: number;
  missing_fields: number;
  changes_detected: number;
  actions_recommended: number;
}

// ─── Agent Config ──────────────────────────────────────────────────────────

const AGENT_META: Record<string, { icon: typeof Bot; color: string; bg: string; description: string }> = {
  morning_briefing: {
    icon: Calendar,
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    description: 'Generates daily intelligence report with hiring signals, pipeline status, and priority contacts',
  },
  contact_enrichment: {
    icon: Users,
    color: 'text-emerald-600 dark:text-emerald-400',
    bg: 'bg-emerald-100 dark:bg-emerald-900/30',
    description: 'Scans contacts for staleness, missing fields, and role changes needing re-classification',
  },
};

// ─── Main Component ────────────────────────────────────────────────────────

export function AutonomousAgents() {
  const [schedules, setSchedules] = useState<AgentSchedule[]>([]);
  const [schedulerRunning, setSchedulerRunning] = useState(false);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [latestBrief, setLatestBrief] = useState<DailyBrief | null>(null);
  const [enrichmentReport, setEnrichmentReport] = useState<EnrichmentReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningAgent, setRunningAgent] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    const [schedResp, runsResp, briefResp, enrichResp] = await Promise.allSettled([
      fetch('/agents/autonomous/schedule'),
      fetch('/agents/autonomous/runs?limit=20'),
      fetch('/agents/autonomous/briefing/latest'),
      fetch('/agents/autonomous/enrichment/report'),
    ]);

    if (schedResp.status === 'fulfilled' && schedResp.value.ok) {
      const data = await schedResp.value.json();
      setSchedules(data.agents || []);
      setSchedulerRunning(data.running || false);
    }
    if (runsResp.status === 'fulfilled' && runsResp.value.ok) {
      const data = await runsResp.value.json();
      setRuns(data.runs || []);
    }
    if (briefResp.status === 'fulfilled' && briefResp.value.ok) {
      const data = await briefResp.value.json();
      if (data.available) setLatestBrief(data.brief);
    }
    if (enrichResp.status === 'fulfilled' && enrichResp.value.ok) {
      const data = await enrichResp.value.json();
      if (data.available) setEnrichmentReport(data.report);
    }

    setLoading(false);
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleRunNow = useCallback(async (agentName: string) => {
    setRunningAgent(agentName);
    try {
      await fetch(`/agents/autonomous/run/${agentName}`, { method: 'POST' });
      // Wait a moment then refresh
      setTimeout(() => fetchAll(), 500);
    } catch {
      // ignore
    } finally {
      setRunningAgent(null);
    }
  }, [fetchAll]);

  const handleToggleScheduler = useCallback(async () => {
    const endpoint = schedulerRunning ? '/agents/autonomous/stop' : '/agents/autonomous/start';
    try {
      const resp = await fetch(endpoint, { method: 'POST' });
      if (resp.ok) {
        const data = await resp.json();
        setSchedulerRunning(data.running);
        fetchAll();
      }
    } catch {
      // ignore
    }
  }, [schedulerRunning, fetchAll]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-slate-500">Loading autonomous agents...</span>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-orange-100 dark:bg-orange-900/30">
              <Bot className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white">Autonomous Agents</h1>
              <p className="text-sm text-slate-500">Scheduled intelligence workflows with human-in-the-loop approval</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleToggleScheduler}
              className={`px-4 py-2 text-sm font-medium rounded-lg flex items-center gap-2 transition-colors ${
                schedulerRunning
                  ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 hover:bg-red-200'
                  : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 hover:bg-green-200'
              }`}
            >
              {schedulerRunning ? <XCircle className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              {schedulerRunning ? 'Stop Scheduler' : 'Start Scheduler'}
            </button>
            <button onClick={fetchAll} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
              <RefreshCw className="w-4 h-4 text-slate-400" />
            </button>
          </div>
        </div>

        {/* Agent Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {schedules.map((agent) => {
            const meta = AGENT_META[agent.agent] || AGENT_META.morning_briefing;
            const Icon = meta.icon;
            const isRunning = runningAgent === agent.agent;
            const lastRun = agent.last_run;

            return (
              <div key={agent.agent} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${meta.bg}`}>
                      <Icon className={`w-5 h-5 ${meta.color}`} />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{agent.name}</h3>
                      <p className="text-xs text-slate-500">{meta.description}</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500 flex items-center gap-1"><Clock className="w-3 h-3" /> Schedule</span>
                    <span className="font-medium text-slate-700 dark:text-slate-300">{agent.schedule}</span>
                  </div>
                  {agent.next_run && (
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Next Run</span>
                      <span className="text-slate-400">{new Date(agent.next_run).toLocaleString()}</span>
                    </div>
                  )}
                  {lastRun && (
                    <>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-500">Last Run</span>
                        <span className="flex items-center gap-1">
                          {lastRun.status === 'success'
                            ? <CheckCircle2 className="w-3 h-3 text-green-500" />
                            : <XCircle className="w-3 h-3 text-red-500" />}
                          <span className="text-slate-400">{new Date(lastRun.end_time).toLocaleString()}</span>
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400 bg-slate-50 dark:bg-slate-700/50 rounded p-1.5">
                        {lastRun.summary}
                      </p>
                    </>
                  )}
                </div>

                <button
                  onClick={() => handleRunNow(agent.agent)}
                  disabled={isRunning}
                  className="w-full py-2 text-xs font-medium rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 disabled:opacity-50 flex items-center justify-center gap-1.5"
                >
                  {isRunning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  Run Now
                </button>
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Latest Briefing Preview */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-500" />
              Latest Briefing
            </h3>

            {latestBrief ? (
              <div className="space-y-3">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Date</span>
                  <span className="font-medium text-slate-700 dark:text-slate-300">{latestBrief.date}</span>
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-700/50 rounded-lg p-3">
                  {latestBrief.executive_summary}
                </p>
                <div className="grid grid-cols-3 gap-2">
                  <div className="text-center p-2 rounded-lg bg-red-50 dark:bg-red-900/20">
                    <p className="text-lg font-bold text-red-600 dark:text-red-400">{latestBrief.hiring_signals.length}</p>
                    <p className="text-[10px] text-slate-500">Signals</p>
                  </div>
                  <div className="text-center p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                    <p className="text-lg font-bold text-blue-600 dark:text-blue-400">{latestBrief.new_opportunities.length}</p>
                    <p className="text-[10px] text-slate-500">New Opps</p>
                  </div>
                  <div className="text-center p-2 rounded-lg bg-green-50 dark:bg-green-900/20">
                    <p className="text-lg font-bold text-green-600 dark:text-green-400">{latestBrief.priority_contacts.length}</p>
                    <p className="text-[10px] text-slate-500">Priority</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-6">
                <Calendar className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-sm text-slate-500">No briefings yet</p>
                <p className="text-xs text-slate-400">Run the Morning Briefing agent to generate</p>
              </div>
            )}
          </div>

          {/* Enrichment Report */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
              <Users className="w-4 h-4 text-emerald-500" />
              Latest Enrichment Scan
            </h3>

            {enrichmentReport ? (
              <div className="space-y-3">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Scan Date</span>
                  <span className="text-slate-400">{new Date(enrichmentReport.scan_date).toLocaleString()}</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50">
                    <p className="text-lg font-bold text-slate-900 dark:text-white">{enrichmentReport.contacts_scanned}</p>
                    <p className="text-[10px] text-slate-500">Scanned</p>
                  </div>
                  <div className="p-2 rounded-lg bg-amber-50 dark:bg-amber-900/20">
                    <p className="text-lg font-bold text-amber-600 dark:text-amber-400">{enrichmentReport.stale_contacts}</p>
                    <p className="text-[10px] text-slate-500">Stale</p>
                  </div>
                  <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20">
                    <p className="text-lg font-bold text-red-600 dark:text-red-400">{enrichmentReport.missing_fields}</p>
                    <p className="text-[10px] text-slate-500">Missing Fields</p>
                  </div>
                  <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                    <p className="text-lg font-bold text-blue-600 dark:text-blue-400">{enrichmentReport.changes_detected}</p>
                    <p className="text-[10px] text-slate-500">Total Issues</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-6">
                <Users className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-sm text-slate-500">No enrichment scans yet</p>
                <p className="text-xs text-slate-400">Run the Contact Enrichment agent to scan</p>
              </div>
            )}
          </div>
        </div>

        {/* Run History */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
          <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-700">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-500" />
              Execution History
            </h3>
          </div>

          {runs.length > 0 ? (
            <div className="max-h-48 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-white dark:bg-slate-800">
                  <tr className="border-b border-slate-100 dark:border-slate-700">
                    <th className="text-left py-2 px-4 text-xs font-medium text-slate-500 uppercase">Agent</th>
                    <th className="text-left py-2 px-4 text-xs font-medium text-slate-500 uppercase">Status</th>
                    <th className="text-left py-2 px-4 text-xs font-medium text-slate-500 uppercase">Summary</th>
                    <th className="text-left py-2 px-4 text-xs font-medium text-slate-500 uppercase">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {[...runs].reverse().map((run, idx) => (
                    <tr key={idx} className="border-b border-slate-50 dark:border-slate-700/50">
                      <td className="py-2 px-4 text-xs font-medium text-slate-700 dark:text-slate-300">
                        {run.agent.replace('_', ' ')}
                      </td>
                      <td className="py-2 px-4">
                        {run.status === 'success'
                          ? <CheckCircle2 className="w-4 h-4 text-green-500" />
                          : <XCircle className="w-4 h-4 text-red-500" />}
                      </td>
                      <td className="py-2 px-4 text-xs text-slate-500 max-w-xs truncate">{run.summary}</td>
                      <td className="py-2 px-4 text-xs text-slate-400">{new Date(run.end_time).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-8 text-center">
              <Clock className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-sm text-slate-500">No agent runs yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
