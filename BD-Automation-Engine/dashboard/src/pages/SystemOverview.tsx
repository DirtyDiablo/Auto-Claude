/**
 * System Overview — Mission Control for the entire BD Intelligence platform.
 *
 * Sections:
 *  1. Alert Banner (conditional)
 *  2. Service Status Grid
 *  3. Platform Metrics
 *  4. Autonomous Agent Status + Recent Activity
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Server, Database, Activity, Cpu, Brain, Bot,
  RefreshCw, Loader2, CheckCircle2, XCircle, AlertTriangle,
  Users, Briefcase, Building2, BarChart3, Clock, Zap,
  Globe, Network, X,
} from 'lucide-react'

// ── Types ──────────────────────────────────────────────

interface ServiceStatus {
  status: 'online' | 'offline'
  code?: number
  latency_ms?: number
  error?: string
}

interface PlatformStats {
  timestamp: string
  services: Record<string, ServiceStatus>
  contacts: { total: number }
  programs: { total: number }
  jobs: { total: number }
  vectors: { total_vectors: number; collections: { name: string; points: number }[] }
  ml: { model_loaded: boolean; model_type: string; drift_status: string; trained_at?: string }
  automation: {
    scheduled_tasks: number
    enabled_tasks?: number
    active_workflows: number
    workflow_definitions?: number
    claude_queue: number
    claude_completed?: number
  }
  graph: { entities: number; relationships: number }
}

interface ScheduledTask {
  name: string
  description: string
  enabled: boolean
  last_run: string | null
  last_status: string | null
  next_run: string | null
  consecutive_failures: number
}

interface Alert {
  id: string
  severity: 'critical' | 'warning' | 'info'
  message: string
  source: string
}

// ── Component ──────────────────────────────────────────

export function SystemOverview() {
  const [stats, setStats] = useState<PlatformStats | null>(null)
  const [tasks, setTasks] = useState<ScheduledTask[]>([])
  const [loading, setLoading] = useState(false)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set())

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [statsRes, schedRes] = await Promise.all([
        fetch('/platform/stats').catch(() => null),
        fetch('/automation/schedule').catch(() => null),
      ])

      if (statsRes?.ok) {
        const data = await statsRes.json()
        setStats(data)

        // Generate alerts from stats
        const newAlerts: Alert[] = []
        for (const [name, svc] of Object.entries(data.services || {})) {
          const s = svc as ServiceStatus
          if (s.status === 'offline') {
            newAlerts.push({
              id: `svc-${name}`,
              severity: 'critical',
              message: `${name} is offline`,
              source: 'service_monitor',
            })
          }
        }
        if (data.ml?.drift_status === 'drifted') {
          newAlerts.push({
            id: 'ml-drift',
            severity: 'warning',
            message: 'ML model drift detected — retrain recommended',
            source: 'ml_monitor',
          })
        }
        setAlerts(newAlerts)
      }

      if (schedRes?.ok) {
        const data = await schedRes.json()
        setTasks(data.tasks || [])
      }
    } catch { /* ignore */ }
    setLoading(false)
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchData, 30_000)
    return () => clearInterval(interval)
  }, [fetchData])

  const dismissAlert = (id: string) => {
    setDismissedAlerts(prev => new Set([...prev, id]))
  }

  const timeAgo = (iso: string | null) => {
    if (!iso) return 'Never'
    const diff = Date.now() - new Date(iso).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    return `${Math.floor(hrs / 24)}d ago`
  }

  const activeAlerts = alerts.filter(a => !dismissedAlerts.has(a.id))

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Globe className="h-5 w-5 text-blue-500" />
              System Overview
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Platform health, service status, and operational metrics
            </p>
          </div>
          <div className="flex items-center gap-2">
            {stats && (
              <span className="text-xs text-slate-400">
                Updated: {new Date(stats.timestamp).toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={fetchData}
              disabled={loading}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Alert Banner */}
        {activeAlerts.length > 0 && (
          <div className="space-y-2">
            {activeAlerts.map(alert => (
              <div
                key={alert.id}
                className={`flex items-center justify-between px-4 py-2.5 rounded-xl border ${
                  alert.severity === 'critical'
                    ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300'
                    : alert.severity === 'warning'
                    ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300'
                    : 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm font-medium">{alert.message}</span>
                  <span className="text-[10px] opacity-60">{alert.source}</span>
                </div>
                <button
                  onClick={() => dismissAlert(alert.id)}
                  className="p-1 rounded hover:bg-black/10"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Service Status Grid */}
        <div>
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Service Status</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
            {[
              { name: 'Hub API', key: 'hub_api', icon: Server, port: ':8100' },
              { name: 'Qdrant', key: 'qdrant', icon: Database, port: ':6333' },
              { name: 'Dashboard', key: 'dashboard', icon: Globe, port: ':5173', alwaysOn: true },
              { name: 'Redis', key: 'redis', icon: Zap, port: ':6379' },
              { name: 'Neo4j', key: 'neo4j', icon: Network, port: ':7474' },
              { name: 'Scheduler', key: 'scheduler', icon: Clock, port: '', alwaysOn: stats?.automation?.scheduled_tasks ? true : false },
            ].map(svc => {
              const status = stats?.services?.[svc.key]
              const isOnline = status?.status === 'online' || svc.alwaysOn
              return (
                <div key={svc.key} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <svc.icon className="h-4 w-4 text-slate-500" />
                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">{svc.name}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className={`inline-block h-2 w-2 rounded-full ${isOnline ? 'bg-emerald-500' : 'bg-red-500'}`} />
                    <span className={`text-xs font-medium ${isOnline ? 'text-emerald-600' : 'text-red-600'}`}>
                      {isOnline ? 'Online' : 'Offline'}
                    </span>
                  </div>
                  {status?.latency_ms && (
                    <div className="text-[10px] text-slate-400 mt-1">{status.latency_ms}ms {svc.port}</div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Platform Metrics */}
        <div>
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Platform Metrics</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
            {[
              { label: 'Total Contacts', value: stats?.contacts?.total || 0, icon: Users, color: 'text-blue-600' },
              { label: 'Programs', value: stats?.programs?.total || 0, icon: Building2, color: 'text-purple-600' },
              { label: 'Jobs', value: stats?.jobs?.total || 0, icon: Briefcase, color: 'text-green-600' },
              { label: 'Vectors', value: stats?.vectors?.total_vectors || 0, icon: Database, color: 'text-cyan-600' },
              { label: 'Graph Entities', value: stats?.graph?.entities || 0, icon: Network, color: 'text-amber-600' },
              { label: 'Graph Relations', value: stats?.graph?.relationships || 0, icon: Activity, color: 'text-pink-600' },
            ].map(metric => (
              <div key={metric.label} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 text-center">
                <metric.icon className={`h-5 w-5 mx-auto mb-1 ${metric.color}`} />
                <div className={`text-2xl font-bold ${metric.color}`}>
                  {metric.value.toLocaleString()}
                </div>
                <div className="text-[10px] text-slate-500 uppercase mt-0.5">{metric.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Automation & ML Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {/* ML Status */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="h-4 w-4 text-indigo-500" />
              <span className="text-xs font-semibold text-slate-500 uppercase">ML Models</span>
            </div>
            <div className="flex items-center gap-2 mb-1">
              <span className={`h-2 w-2 rounded-full ${stats?.ml?.model_loaded ? 'bg-emerald-500' : 'bg-slate-400'}`} />
              <span className="text-sm text-slate-700 dark:text-slate-300">
                {stats?.ml?.model_loaded ? stats.ml.model_type : 'Not loaded'}
              </span>
            </div>
            <div className="text-xs text-slate-500">
              Drift: {stats?.ml?.drift_status || 'unknown'}
            </div>
            {stats?.ml?.trained_at && (
              <div className="text-xs text-slate-400 mt-1">
                Trained: {stats.ml.trained_at}
              </div>
            )}
          </div>

          {/* Automation */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Cpu className="h-4 w-4 text-purple-500" />
              <span className="text-xs font-semibold text-slate-500 uppercase">Automation</span>
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Scheduled Tasks</span>
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  {stats?.automation?.enabled_tasks || 0}/{stats?.automation?.scheduled_tasks || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Active Workflows</span>
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  {stats?.automation?.active_workflows || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Claude Queue</span>
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  {stats?.automation?.claude_queue || 0}
                </span>
              </div>
            </div>
          </div>

          {/* Vector Collections */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Database className="h-4 w-4 text-cyan-500" />
              <span className="text-xs font-semibold text-slate-500 uppercase">Vector Collections</span>
            </div>
            {stats?.vectors?.collections?.length ? (
              <div className="space-y-1">
                {stats.vectors.collections.slice(0, 5).map(col => (
                  <div key={col.name} className="flex justify-between text-xs">
                    <span className="text-slate-500 truncate">{col.name}</span>
                    <span className="font-mono text-slate-700 dark:text-slate-300">
                      {col.points.toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-400">No collections</div>
            )}
          </div>

          {/* Workflows */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Bot className="h-4 w-4 text-amber-500" />
              <span className="text-xs font-semibold text-slate-500 uppercase">Workflows</span>
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Definitions</span>
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  {stats?.automation?.workflow_definitions || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Active Runs</span>
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  {stats?.automation?.active_workflows || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Claude Done</span>
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  {stats?.automation?.claude_completed || 0}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Scheduled Agent Status */}
        <div>
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
            Scheduled Agents ({tasks.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3">
            {tasks.map(task => (
              <div
                key={task.name}
                className={`bg-white dark:bg-slate-800 rounded-xl border p-3 ${
                  task.consecutive_failures >= 3
                    ? 'border-red-300 dark:border-red-700'
                    : task.last_status === 'success'
                    ? 'border-emerald-200 dark:border-emerald-800'
                    : 'border-slate-200 dark:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  {task.last_status === 'success' && <CheckCircle2 className="h-3 w-3 text-emerald-500" />}
                  {task.last_status === 'failed' && <XCircle className="h-3 w-3 text-red-500" />}
                  {!task.last_status && <Clock className="h-3 w-3 text-slate-400" />}
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 truncate">
                    {task.name.replace(/_/g, ' ')}
                  </span>
                  {!task.enabled && (
                    <span className="text-[8px] px-1 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-500">OFF</span>
                  )}
                </div>
                <div className="text-[10px] text-slate-500 space-y-0.5">
                  <div>Last: {timeAgo(task.last_run)}</div>
                  <div>Next: {task.next_run ? new Date(task.next_run).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'}</div>
                </div>
                {task.consecutive_failures >= 3 && (
                  <div className="flex items-center gap-1 text-[10px] text-red-500 mt-1">
                    <AlertTriangle className="h-2.5 w-2.5" />
                    {task.consecutive_failures} failures
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
