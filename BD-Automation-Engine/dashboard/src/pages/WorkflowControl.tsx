/**
 * Phase 23A — WorkflowControl Dashboard Page
 *
 * Production workflow management with:
 * - Active workflows table with live status
 * - Pending human approvals with action buttons
 * - Execution history with timeline viewer
 * - Schedule management
 * - Workflow stats overview
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Activity, Play, Pause, XCircle, Clock, CheckCircle,
  AlertTriangle, RotateCcw, Calendar, ChevronDown,
  ChevronRight, Loader2, Eye, RefreshCw,
} from 'lucide-react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface WorkflowExecution {
  thread_id: string
  workflow_name: string
  status: string
  started_at: string
  completed_at: string | null
  current_node: string | null
  step_count: number
  errors: { error?: string; node?: string }[]
  pending_approvals: string[]
}

interface ApprovalRequest {
  request_id: string
  thread_id: string
  workflow_name: string
  node_name: string
  description: string
  state_snapshot: Record<string, unknown>
  options: string[]
  urgency: string
  created_at: string
  expires_at: string
  status: string
}

interface ScheduledWorkflow {
  schedule_id: string
  workflow_name: string
  cron_expression: string
  enabled: boolean
  last_run: string | null
  next_run: string | null
  run_count: number
}

interface WorkflowInfo {
  name: string
  description: string
  node_count: number
  edge_count: number
  interrupt_nodes: string[]
  parallel_groups: string[][]
  entry_point: string
}

interface WorkflowStats {
  total_executions: number
  by_status: Record<string, number>
  by_workflow: Record<string, number>
  avg_duration_seconds: number
  registered_workflows: number
  active_schedules: number
  approval_stats: {
    total_requests: number
    pending: number
    approved: number
    rejected: number
    avg_response_seconds: number
  }
}

interface TimelineData {
  thread_id: string
  workflow_name: string
  status: string
  total_steps: number
  total_duration_seconds: number
  nodes_visited: {
    step: number
    node_name: string
    duration_seconds: number
    state_keys_modified: string[]
  }[]
  errors: { step: number; node_name: string; error: string }[]
  interrupts: { step: number; node_name: string; description: string }[]
}

// ---------------------------------------------------------------------------
// Status helpers
// ---------------------------------------------------------------------------

const STATUS_COLORS: Record<string, string> = {
  running: 'bg-blue-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
  interrupted: 'bg-yellow-500',
  cancelled: 'bg-gray-500',
  pending: 'bg-blue-300',
}

const URGENCY_BADGES: Record<string, string> = {
  critical: 'bg-red-600 text-white',
  high: 'bg-orange-500 text-white',
  normal: 'bg-blue-500 text-white',
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium text-white ${STATUS_COLORS[status] || 'bg-gray-400'}`}>
      {status === 'running' && <Loader2 className="h-3 w-3 animate-spin" />}
      {status === 'completed' && <CheckCircle className="h-3 w-3" />}
      {status === 'failed' && <XCircle className="h-3 w-3" />}
      {status === 'interrupted' && <Pause className="h-3 w-3" />}
      {status}
    </span>
  )
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function WorkflowControl() {
  const [tab, setTab] = useState<'active' | 'approvals' | 'history' | 'schedules' | 'stats'>('active')
  const [active, setActive] = useState<WorkflowExecution[]>([])
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([])
  const [history, setHistory] = useState<WorkflowExecution[]>([])
  const [schedules, setSchedules] = useState<ScheduledWorkflow[]>([])
  const [registry, setRegistry] = useState<WorkflowInfo[]>([])
  const [stats, setStats] = useState<WorkflowStats | null>(null)
  const [timeline, setTimeline] = useState<TimelineData | null>(null)
  const [selectedThread, setSelectedThread] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [startWorkflow, setStartWorkflow] = useState('')
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [activeRes, approvalRes, historyRes, schedRes, regRes, statsRes] = await Promise.allSettled([
        fetch('/workflows/active').then(r => r.json()),
        fetch('/workflows/approvals').then(r => r.json()),
        fetch('/workflows/history?limit=50').then(r => r.json()),
        fetch('/workflows/schedules').then(r => r.json()),
        fetch('/workflows/registry').then(r => r.json()),
        fetch('/workflows/stats').then(r => r.json()),
      ])
      if (activeRes.status === 'fulfilled') setActive(activeRes.value.workflows || [])
      if (approvalRes.status === 'fulfilled') setApprovals(approvalRes.value.approvals || [])
      if (historyRes.status === 'fulfilled') setHistory(historyRes.value.history || [])
      if (schedRes.status === 'fulfilled') setSchedules(schedRes.value.schedules || [])
      if (regRes.status === 'fulfilled') setRegistry(regRes.value.workflows || [])
      if (statsRes.status === 'fulfilled') setStats(statsRes.value)
    } catch {
      // API may not be running
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  // Auto-refresh active workflows
  useEffect(() => {
    const interval = setInterval(() => {
      if (tab === 'active') {
        fetch('/workflows/active').then(r => r.json()).then(d => setActive(d.workflows || [])).catch(() => {})
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [tab])

  // Actions
  const handleStartWorkflow = async (name: string) => {
    setActionLoading(name)
    try {
      await fetch('/workflows/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workflow_name: name, input_state: {} }),
      })
      await fetchData()
    } catch { /* ignore */ }
    setActionLoading(null)
  }

  const handleCancel = async (threadId: string) => {
    setActionLoading(threadId)
    try {
      await fetch(`/workflows/${threadId}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'User cancelled from dashboard' }),
      })
      await fetchData()
    } catch { /* ignore */ }
    setActionLoading(null)
  }

  const handleApproval = async (requestId: string, decision: string) => {
    setActionLoading(requestId)
    try {
      await fetch(`/workflows/approvals/${requestId}/decide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, decided_by: 'dashboard_user' }),
      })
      await fetchData()
    } catch { /* ignore */ }
    setActionLoading(null)
  }

  const handleViewTimeline = async (threadId: string) => {
    setSelectedThread(threadId)
    try {
      const res = await fetch(`/workflows/${threadId}/timeline`)
      if (res.ok) setTimeline(await res.json())
    } catch {
      setTimeline(null)
    }
  }

  const handleToggleSchedule = async (scheduleId: string, enabled: boolean) => {
    try {
      await fetch(`/workflows/schedules/${scheduleId}?enabled=${enabled}`, { method: 'PATCH' })
      await fetchData()
    } catch { /* ignore */ }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Workflow Control</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Production LangGraph workflows — {registry.length} registered, {active.length} active
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={startWorkflow}
            onChange={e => setStartWorkflow(e.target.value)}
            className="text-sm border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
          >
            <option value="">Start Workflow...</option>
            {registry.map(w => <option key={w.name} value={w.name}>{w.name}</option>)}
          </select>
          <button
            onClick={() => startWorkflow && handleStartWorkflow(startWorkflow)}
            disabled={!startWorkflow || actionLoading === startWorkflow}
            className="flex items-center gap-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {actionLoading === startWorkflow ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            Start
          </button>
          <button onClick={fetchData} disabled={loading}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b dark:border-gray-700">
        {(['active', 'approvals', 'history', 'schedules', 'stats'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${
              tab === t ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            {t}
            {t === 'approvals' && approvals.length > 0 && (
              <span className="ml-1 bg-red-500 text-white text-xs px-1.5 rounded-full">{approvals.length}</span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === 'active' && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Workflow</th>
                <th className="text-left px-4 py-3 font-medium">Thread ID</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-left px-4 py-3 font-medium">Current Node</th>
                <th className="text-left px-4 py-3 font-medium">Steps</th>
                <th className="text-left px-4 py-3 font-medium">Started</th>
                <th className="text-right px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y dark:divide-gray-800">
              {active.length === 0 && (
                <tr><td colSpan={7} className="text-center py-8 text-gray-400">No active workflows</td></tr>
              )}
              {active.map(ex => (
                <tr key={ex.thread_id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-medium">{ex.workflow_name}</td>
                  <td className="px-4 py-3 font-mono text-xs">{ex.thread_id}</td>
                  <td className="px-4 py-3"><StatusBadge status={ex.status} /></td>
                  <td className="px-4 py-3">{ex.current_node || '—'}</td>
                  <td className="px-4 py-3">{ex.step_count}</td>
                  <td className="px-4 py-3 text-gray-500">{timeAgo(ex.started_at)}</td>
                  <td className="px-4 py-3 text-right space-x-1">
                    <button onClick={() => handleViewTimeline(ex.thread_id)}
                      className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700" title="View Timeline">
                      <Eye className="h-4 w-4" />
                    </button>
                    {ex.status === 'running' && (
                      <button onClick={() => handleCancel(ex.thread_id)}
                        disabled={actionLoading === ex.thread_id}
                        className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600" title="Cancel">
                        <XCircle className="h-4 w-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'approvals' && (
        <div className="space-y-4">
          {approvals.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              <CheckCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No pending approvals</p>
            </div>
          )}
          {approvals.map(req => (
            <div key={req.request_id} className="bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{req.workflow_name}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${URGENCY_BADGES[req.urgency] || URGENCY_BADGES.normal}`}>
                      {req.urgency}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{req.description}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    Node: {req.node_name} | Thread: {req.thread_id} | Expires: {new Date(req.expires_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex gap-2">
                  {req.options.map(opt => (
                    <button
                      key={opt}
                      onClick={() => handleApproval(req.request_id, opt)}
                      disabled={actionLoading === req.request_id}
                      className={`px-3 py-1.5 text-sm rounded-lg font-medium ${
                        opt === 'approve' ? 'bg-green-600 text-white hover:bg-green-700' :
                        opt === 'reject' ? 'bg-red-600 text-white hover:bg-red-700' :
                        'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
                      } disabled:opacity-50`}
                    >
                      {actionLoading === req.request_id ? '...' : opt}
                    </button>
                  ))}
                </div>
              </div>
              {Object.keys(req.state_snapshot).length > 0 && (
                <div className="mt-3 bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                  <p className="text-xs font-medium text-gray-500 mb-1">State Preview</p>
                  <pre className="text-xs overflow-x-auto max-h-32">
                    {JSON.stringify(req.state_snapshot, null, 2).slice(0, 500)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === 'history' && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Date</th>
                <th className="text-left px-4 py-3 font-medium">Workflow</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-left px-4 py-3 font-medium">Steps</th>
                <th className="text-left px-4 py-3 font-medium">Errors</th>
                <th className="text-right px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y dark:divide-gray-800">
              {history.length === 0 && (
                <tr><td colSpan={6} className="text-center py-8 text-gray-400">No execution history</td></tr>
              )}
              {history.map(ex => (
                <tr key={ex.thread_id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                  <td className="px-4 py-3 text-gray-500">{new Date(ex.started_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3 font-medium">{ex.workflow_name}</td>
                  <td className="px-4 py-3"><StatusBadge status={ex.status} /></td>
                  <td className="px-4 py-3">{ex.step_count}</td>
                  <td className="px-4 py-3">{ex.errors.length > 0 ? <span className="text-red-500">{ex.errors.length}</span> : '—'}</td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => handleViewTimeline(ex.thread_id)}
                      className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700" title="View Timeline">
                      <Eye className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'schedules' && (
        <div className="space-y-4">
          {schedules.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              <Calendar className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No workflow schedules configured</p>
            </div>
          )}
          {schedules.map(sched => (
            <div key={sched.schedule_id} className="bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 p-4 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold">{sched.workflow_name}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs ${sched.enabled ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-800'}`}>
                    {sched.enabled ? 'Active' : 'Paused'}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  Cron: <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">{sched.cron_expression}</code>
                  {' '} | Runs: {sched.run_count}
                  {sched.last_run && ` | Last: ${timeAgo(sched.last_run)}`}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleStartWorkflow(sched.workflow_name)}
                  className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Run Now
                </button>
                <button
                  onClick={() => handleToggleSchedule(sched.schedule_id, !sched.enabled)}
                  className={`px-3 py-1.5 text-sm rounded-lg ${sched.enabled ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200' : 'bg-green-100 text-green-800 hover:bg-green-200'}`}
                >
                  {sched.enabled ? 'Pause' : 'Enable'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'stats' && stats && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wider">Total Runs</p>
              <p className="text-2xl font-bold mt-1">{stats.total_executions}</p>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wider">Avg Duration</p>
              <p className="text-2xl font-bold mt-1">{stats.avg_duration_seconds}s</p>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wider">Registered</p>
              <p className="text-2xl font-bold mt-1">{stats.registered_workflows}</p>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wider">Pending Approvals</p>
              <p className="text-2xl font-bold mt-1">{stats.approval_stats?.pending || 0}</p>
            </div>
          </div>

          {/* By Status */}
          <div className="bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 p-4">
            <h3 className="font-semibold mb-3">Executions by Status</h3>
            <div className="flex gap-4 flex-wrap">
              {Object.entries(stats.by_status || {}).map(([status, count]) => (
                <div key={status} className="flex items-center gap-2">
                  <StatusBadge status={status} />
                  <span className="text-sm font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* By Workflow */}
          <div className="bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 p-4">
            <h3 className="font-semibold mb-3">Executions by Workflow</h3>
            <div className="space-y-2">
              {Object.entries(stats.by_workflow || {}).map(([wf, count]) => (
                <div key={wf} className="flex items-center justify-between">
                  <span className="text-sm">{wf}</span>
                  <span className="text-sm font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Timeline Modal */}
      {selectedThread && timeline && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-3xl w-full max-h-[80vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold">Execution Timeline</h3>
                <p className="text-sm text-gray-500">
                  {timeline.workflow_name} — {timeline.total_steps} steps in {timeline.total_duration_seconds}s
                </p>
              </div>
              <button onClick={() => { setSelectedThread(null); setTimeline(null) }}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
                <XCircle className="h-5 w-5" />
              </button>
            </div>
            <StatusBadge status={timeline.status} />
            <div className="mt-4 space-y-2">
              {timeline.nodes_visited.map((node, i) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-xs font-bold text-blue-600">
                    {node.step}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm">{node.node_name}</span>
                      <span className="text-xs text-gray-400">{node.duration_seconds}s</span>
                    </div>
                    {node.state_keys_modified.length > 0 && (
                      <p className="text-xs text-gray-500 mt-0.5">
                        Modified: {node.state_keys_modified.join(', ')}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            {timeline.errors.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-semibold text-red-600 mb-2">Errors</h4>
                {timeline.errors.map((err, i) => (
                  <div key={i} className="text-xs bg-red-50 dark:bg-red-900/20 rounded p-2 mb-1">
                    Step {err.step} ({err.node_name}): {err.error}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
