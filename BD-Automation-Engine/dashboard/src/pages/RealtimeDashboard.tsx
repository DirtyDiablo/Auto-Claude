/**
 * Realtime Dashboard — Full real-time operations center.
 *
 * Layout:
 *  - Live activity feed (left 60%)
 *  - Active agent status cards (right top)
 *  - Pipeline stage counts (right middle)
 *  - Alert ticker at bottom
 */

import { useState, useEffect, useMemo, useCallback } from 'react'
import {
  Activity, Radio, Bot, ArrowUpRight, Bell, Loader2,
  RefreshCw, Wifi, WifiOff, BarChart3, Zap,
} from 'lucide-react'
import { useRealtimeUpdates } from '../hooks/useRealtimeUpdates'
import { RealtimeIndicator } from '../components/RealtimeIndicator'
import { LiveActivityFeed } from '../components/LiveActivityFeed'
import type { RealtimeEvent } from '../hooks/useRealtimeUpdates'

// ── Types ──────────────────────────────────────────────

interface ServerStatus {
  active_connections: number
  total_messages_sent: number
  uptime_seconds: number
  event_history_size: number
  events_per_minute: number
}

// ── Helpers ────────────────────────────────────────────

function extractAgentStatuses(events: RealtimeEvent[]) {
  const agents = new Map<string, { status: string; output: string; timestamp: string }>()
  for (const e of events) {
    if (e.type === 'agent_status' && e.data?.agent_name) {
      const name = e.data.agent_name as string
      if (!agents.has(name)) {
        agents.set(name, {
          status: (e.data.status as string) || 'unknown',
          output: (e.data.last_output as string) || '',
          timestamp: e.timestamp,
        })
      }
    }
  }
  return Array.from(agents.entries()).map(([name, info]) => ({ name, ...info }))
}

function extractPipelineCounts(events: RealtimeEvent[]) {
  const stages = new Map<string, number>()
  for (const e of events) {
    if (e.type === 'pipeline_move' && e.data?.to_stage) {
      const stage = e.data.to_stage as string
      stages.set(stage, (stages.get(stage) || 0) + 1)
    }
  }
  return Array.from(stages.entries())
    .map(([stage, count]) => ({ stage, count }))
    .sort((a, b) => b.count - a.count)
}

function extractAlerts(events: RealtimeEvent[]) {
  return events
    .filter((e) => e.type === 'notification')
    .slice(0, 10)
    .map((e) => ({
      level: (e.data?.level as string) || 'info',
      title: (e.data?.title as string) || '',
      message: (e.data?.message as string) || '',
      timestamp: e.timestamp,
    }))
}

const AGENT_STATUS_COLORS: Record<string, string> = {
  running: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  idle: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  completed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
}

const ALERT_LEVEL_COLORS: Record<string, string> = {
  info: 'border-l-blue-500',
  success: 'border-l-emerald-500',
  warning: 'border-l-amber-500',
  error: 'border-l-red-500',
}

// ── Component ──────────────────────────────────────────

export function RealtimeDashboard() {
  const { events, notifications, isConnected, connectionType, eventsPerMinute } =
    useRealtimeUpdates()

  const [serverStatus, setServerStatus] = useState<ServerStatus | null>(null)

  // Fetch server status periodically
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('/realtime/status')
      if (res.ok) setServerStatus(await res.json())
    } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 15000)
    return () => clearInterval(interval)
  }, [fetchStatus])

  // Derived data
  const agentStatuses = useMemo(() => extractAgentStatuses(events), [events])
  const pipelineCounts = useMemo(() => extractPipelineCounts(events), [events])
  const alerts = useMemo(() => extractAlerts(events), [events])

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Radio className="h-5 w-5 text-emerald-500" />
              Real-Time Operations
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Live event streaming — zero polling
            </p>
          </div>
          <div className="flex items-center gap-3">
            <RealtimeIndicator
              isConnected={isConnected}
              connectionType={connectionType}
              eventsPerMinute={eventsPerMinute}
            />
            <button
              onClick={fetchStatus}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700"
            >
              <RefreshCw className="h-4 w-4 text-slate-500" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Left — Activity Feed (60%) */}
        <div className="w-3/5 border-r border-slate-200 dark:border-slate-700 p-4 overflow-hidden flex flex-col">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-1.5">
            <Activity className="h-4 w-4 text-blue-500" />
            Live Activity Feed
            <span className="ml-auto text-xs font-normal text-slate-400">
              {events.length} events buffered
            </span>
          </h2>
          <div className="flex-1 overflow-hidden">
            <LiveActivityFeed events={events} maxHeight="calc(100vh - 220px)" />
          </div>
        </div>

        {/* Right — Panels (40%) */}
        <div className="w-2/5 p-4 overflow-y-auto space-y-4">
          {/* Server Status */}
          {serverStatus && (
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
              <h3 className="text-xs font-semibold text-slate-500 uppercase mb-3">Server Status</h3>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="text-lg font-bold text-slate-900 dark:text-white">
                    {serverStatus.active_connections}
                  </div>
                  <div className="text-[10px] text-slate-500">Connections</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-slate-900 dark:text-white">
                    {serverStatus.total_messages_sent.toLocaleString()}
                  </div>
                  <div className="text-[10px] text-slate-500">Messages Sent</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-slate-900 dark:text-white">
                    {serverStatus.events_per_minute}
                  </div>
                  <div className="text-[10px] text-slate-500">Events/min</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-slate-900 dark:text-white">
                    {Math.floor(serverStatus.uptime_seconds / 60)}m
                  </div>
                  <div className="text-[10px] text-slate-500">Uptime</div>
                </div>
              </div>
            </div>
          )}

          {/* Active Agents */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
            <h3 className="text-xs font-semibold text-slate-500 uppercase mb-3 flex items-center gap-1.5">
              <Bot className="h-3.5 w-3.5" />
              Agent Status
            </h3>
            {agentStatuses.length > 0 ? (
              <div className="space-y-2">
                {agentStatuses.map((agent) => (
                  <div
                    key={agent.name}
                    className="flex items-center gap-2 p-2 rounded-lg bg-slate-50 dark:bg-slate-700/30"
                  >
                    <Bot className="h-3.5 w-3.5 text-slate-500 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                        {agent.name}
                      </span>
                      {agent.output && (
                        <p className="text-[10px] text-slate-400 truncate">{agent.output}</p>
                      )}
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                        AGENT_STATUS_COLORS[agent.status] || AGENT_STATUS_COLORS.idle
                      }`}
                    >
                      {agent.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 text-center py-3">No agent activity yet</p>
            )}
          </div>

          {/* Pipeline Stages */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
            <h3 className="text-xs font-semibold text-slate-500 uppercase mb-3 flex items-center gap-1.5">
              <ArrowUpRight className="h-3.5 w-3.5" />
              Pipeline Movement
            </h3>
            {pipelineCounts.length > 0 ? (
              <div className="space-y-2">
                {pipelineCounts.map(({ stage, count }) => (
                  <div key={stage} className="flex items-center gap-2">
                    <span className="text-xs text-slate-700 dark:text-slate-300 flex-1">{stage}</span>
                    <div className="w-24 bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all"
                        style={{
                          width: `${Math.min(100, (count / Math.max(1, pipelineCounts[0]?.count)) * 100)}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs font-mono text-slate-500 w-8 text-right">{count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 text-center py-3">No pipeline moves yet</p>
            )}
          </div>

          {/* Recent Alerts */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
            <h3 className="text-xs font-semibold text-slate-500 uppercase mb-3 flex items-center gap-1.5">
              <Bell className="h-3.5 w-3.5" />
              Recent Alerts
            </h3>
            {alerts.length > 0 ? (
              <div className="space-y-1.5">
                {alerts.map((alert, i) => (
                  <div
                    key={`${alert.timestamp}-${i}`}
                    className={`border-l-2 ${
                      ALERT_LEVEL_COLORS[alert.level] || ALERT_LEVEL_COLORS.info
                    } pl-3 py-1.5`}
                  >
                    <div className="text-xs font-medium text-slate-700 dark:text-slate-300">
                      {alert.title}
                    </div>
                    <div className="text-[10px] text-slate-400">{alert.message}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 text-center py-3">No alerts yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
