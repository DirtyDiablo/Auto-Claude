/**
 * Automation Center — Scheduled tasks, multi-agent workflows, Claude task queue.
 *
 * Three tabs:
 *  1. Scheduled Tasks: grid of task cards with status, schedule, run now
 *  2. Workflows: active workflow progress + history
 *  3. Claude Tasks: research task queue + results
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Clock, Play, Pause, RefreshCw, Loader2, CheckCircle2,
  XCircle, Timer, Cpu, Bot, Brain, Sparkles,
  ChevronRight, ArrowRight, Send, FileText, AlertTriangle,
} from 'lucide-react'

// ── Types ──────────────────────────────────────────────

interface ScheduledTask {
  name: string
  description: string
  cron_expression: string
  enabled: boolean
  last_run: string | null
  last_status: string | null
  next_run: string | null
  avg_duration_sec: number
  failure_count: number
  consecutive_failures: number
  total_runs: number
}

interface WorkflowDef {
  name: string
  description: string
  total_steps: number
}

interface WorkflowRun {
  run_id: string
  workflow_name: string
  status: string
  steps_completed: number
  current_step: string | null
  started_at: string | null
  ended_at: string | null
  human_gate_pending: boolean
  step_results: Record<string, unknown>
  error: string | null
}

interface ClaudeTaskStats {
  pending: number
  in_progress: number
  completed: number
  failed: number
  total: number
  task_types: string[]
}

interface ClaudeTask {
  task_id: string
  task_type: string
  prompt: string
  priority: string
  status: string
  submitted_at: string
  completed_at: string | null
  estimated_tokens: number
}

type TabKey = 'schedule' | 'workflows' | 'claude'

// ── Component ──────────────────────────────────────────

export function AutomationCenter() {
  const [tab, setTab] = useState<TabKey>('schedule')
  const [loading, setLoading] = useState(false)

  // Schedule state
  const [tasks, setTasks] = useState<ScheduledTask[]>([])
  const [runningTask, setRunningTask] = useState<string | null>(null)

  // Workflow state
  const [workflowDefs, setWorkflowDefs] = useState<WorkflowDef[]>([])
  const [activeRuns, setActiveRuns] = useState<WorkflowRun[]>([])
  const [launchingWorkflow, setLaunchingWorkflow] = useState<string | null>(null)

  // Claude state
  const [claudeStats, setClaudeStats] = useState<ClaudeTaskStats | null>(null)
  const [claudeTasks, setClaudeTasks] = useState<ClaudeTask[]>([])
  const [newPrompt, setNewPrompt] = useState('')
  const [newTaskType, setNewTaskType] = useState('deep_research')
  const [submitting, setSubmitting] = useState(false)

  // Fetch data
  const fetchSchedule = useCallback(async () => {
    try {
      const res = await fetch('/automation/schedule')
      if (res.ok) {
        const data = await res.json()
        setTasks(data.tasks || [])
      }
    } catch { /* ignore */ }
  }, [])

  const fetchWorkflows = useCallback(async () => {
    try {
      const [defsRes, activeRes] = await Promise.all([
        fetch('/automation/workflows/definitions'),
        fetch('/automation/workflows/active'),
      ])
      if (defsRes.ok) {
        const d = await defsRes.json()
        setWorkflowDefs(d.workflows || [])
      }
      if (activeRes.ok) {
        const a = await activeRes.json()
        setActiveRuns(a.active || [])
      }
    } catch { /* ignore */ }
  }, [])

  const fetchClaude = useCallback(async () => {
    try {
      const [queueRes, tasksRes] = await Promise.all([
        fetch('/automation/claude/queue'),
        fetch('/automation/claude/tasks'),
      ])
      if (queueRes.ok) {
        const q = await queueRes.json()
        setClaudeStats(q.stats || null)
      }
      if (tasksRes.ok) {
        const t = await tasksRes.json()
        setClaudeTasks(t.tasks || [])
      }
    } catch { /* ignore */ }
  }, [])

  const fetchAll = useCallback(async () => {
    setLoading(true)
    await Promise.all([fetchSchedule(), fetchWorkflows(), fetchClaude()])
    setLoading(false)
  }, [fetchSchedule, fetchWorkflows, fetchClaude])

  useEffect(() => { fetchAll() }, [fetchAll])

  // Actions
  const handleRunNow = useCallback(async (name: string) => {
    setRunningTask(name)
    try {
      await fetch(`/automation/tasks/${name}/run`, { method: 'POST' })
      await fetchSchedule()
    } catch { /* ignore */ }
    setRunningTask(null)
  }, [fetchSchedule])

  const handleToggleTask = useCallback(async (name: string, enabled: boolean) => {
    try {
      await fetch(`/automation/tasks/${name}/enable?enabled=${enabled}`, { method: 'POST' })
      await fetchSchedule()
    } catch { /* ignore */ }
  }, [fetchSchedule])

  const handleLaunchWorkflow = useCallback(async (name: string) => {
    setLaunchingWorkflow(name)
    try {
      await fetch('/automation/workflows/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workflow: name, params: {} }),
      })
      await fetchWorkflows()
    } catch { /* ignore */ }
    setLaunchingWorkflow(null)
  }, [fetchWorkflows])

  const handleApproveGate = useCallback(async (runId: string) => {
    try {
      await fetch(`/automation/workflows/${runId}/approve`, { method: 'POST' })
      await fetchWorkflows()
    } catch { /* ignore */ }
  }, [fetchWorkflows])

  const handleSubmitClaude = useCallback(async () => {
    if (!newPrompt.trim()) return
    setSubmitting(true)
    try {
      await fetch('/automation/claude/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_type: newTaskType, prompt: newPrompt }),
      })
      setNewPrompt('')
      await fetchClaude()
    } catch { /* ignore */ }
    setSubmitting(false)
  }, [newPrompt, newTaskType, fetchClaude])

  // Helpers
  const statusIcon = (status: string | null) => {
    if (status === 'success') return <CheckCircle2 className="h-4 w-4 text-emerald-500" />
    if (status === 'failed') return <XCircle className="h-4 w-4 text-red-500" />
    if (status === 'running') return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
    return <Clock className="h-4 w-4 text-slate-400" />
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

  const tabs: { key: TabKey; label: string; icon: typeof Clock }[] = [
    { key: 'schedule', label: 'Scheduled Tasks', icon: Clock },
    { key: 'workflows', label: 'Workflows', icon: Bot },
    { key: 'claude', label: 'Claude Tasks', icon: Brain },
  ]

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Cpu className="h-5 w-5 text-indigo-500" />
              Automation Center
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Scheduled tasks, multi-agent workflows, and AI research queue
            </p>
          </div>
          <button
            onClick={fetchAll}
            disabled={loading}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mt-3">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-colors ${
                tab === t.key
                  ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300'
                  : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
            >
              <t.icon className="h-4 w-4" />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">

        {/* ── Scheduled Tasks Tab ── */}
        {tab === 'schedule' && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {tasks.map((task) => (
              <div
                key={task.name}
                className={`bg-white dark:bg-slate-800 rounded-xl border p-4 ${
                  task.consecutive_failures >= 3
                    ? 'border-red-300 dark:border-red-700'
                    : 'border-slate-200 dark:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {statusIcon(task.last_status)}
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                      {task.name.replace(/_/g, ' ')}
                    </h3>
                  </div>
                  <button
                    onClick={() => handleToggleTask(task.name, !task.enabled)}
                    className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                      task.enabled
                        ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
                        : 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-400'
                    }`}
                  >
                    {task.enabled ? 'ON' : 'OFF'}
                  </button>
                </div>

                <p className="text-xs text-slate-500 mb-3">{task.description}</p>

                <div className="space-y-1 text-xs text-slate-500">
                  <div className="flex justify-between">
                    <span>Schedule:</span>
                    <span className="font-mono text-slate-700 dark:text-slate-300">{task.cron_expression}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Last run:</span>
                    <span>{timeAgo(task.last_run)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Next run:</span>
                    <span>{task.next_run ? new Date(task.next_run).toLocaleTimeString() : 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total runs:</span>
                    <span>{task.total_runs}</span>
                  </div>
                  {task.avg_duration_sec > 0 && (
                    <div className="flex justify-between">
                      <span>Avg duration:</span>
                      <span>{task.avg_duration_sec.toFixed(1)}s</span>
                    </div>
                  )}
                  {task.consecutive_failures >= 3 && (
                    <div className="flex items-center gap-1 text-red-500 mt-1">
                      <AlertTriangle className="h-3 w-3" />
                      <span>{task.consecutive_failures} consecutive failures</span>
                    </div>
                  )}
                </div>

                <button
                  onClick={() => handleRunNow(task.name)}
                  disabled={runningTask === task.name}
                  className="mt-3 w-full px-3 py-1.5 text-xs font-medium bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-300 rounded-lg hover:bg-indigo-100 disabled:opacity-50 flex items-center justify-center gap-1"
                >
                  {runningTask === task.name ? (
                    <><Loader2 className="h-3 w-3 animate-spin" /> Running...</>
                  ) : (
                    <><Play className="h-3 w-3" /> Run Now</>
                  )}
                </button>
              </div>
            ))}
            {tasks.length === 0 && (
              <div className="col-span-full text-center py-12 text-slate-400">
                <Clock className="h-10 w-10 mx-auto mb-2" />
                <p>No scheduled tasks found. Start the API server.</p>
              </div>
            )}
          </div>
        )}

        {/* ── Workflows Tab ── */}
        {tab === 'workflows' && (
          <div className="space-y-6">
            {/* Available Workflows */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Available Workflows</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {workflowDefs.map((wf) => (
                  <div key={wf.name} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
                        {wf.name.replace(/_/g, ' ')}
                      </h4>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-500">
                        {wf.total_steps} steps
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mb-3">{wf.description}</p>
                    <button
                      onClick={() => handleLaunchWorkflow(wf.name)}
                      disabled={launchingWorkflow === wf.name}
                      className="w-full px-3 py-1.5 text-xs font-medium bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-300 rounded-lg hover:bg-purple-100 disabled:opacity-50 flex items-center justify-center gap-1"
                    >
                      {launchingWorkflow === wf.name ? (
                        <><Loader2 className="h-3 w-3 animate-spin" /> Launching...</>
                      ) : (
                        <><Sparkles className="h-3 w-3" /> Launch Workflow</>
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Active Runs */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                Active Runs ({activeRuns.length})
              </h3>
              {activeRuns.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-sm">No active workflow runs</div>
              ) : (
                <div className="space-y-3">
                  {activeRuns.map((run) => (
                    <div key={run.run_id} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {run.status === 'running' && <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />}
                          {run.status === 'paused' && <Pause className="h-4 w-4 text-amber-500" />}
                          <span className="text-sm font-semibold text-slate-900 dark:text-white">
                            {run.workflow_name.replace(/_/g, ' ')}
                          </span>
                        </div>
                        <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                          run.status === 'running' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' :
                          run.status === 'paused' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300' :
                          'bg-slate-100 text-slate-500'
                        }`}>
                          {run.status}
                        </span>
                      </div>

                      {/* Progress */}
                      <div className="flex items-center gap-2 mb-2">
                        <div className="flex-1 bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
                          <div
                            className="bg-gradient-to-r from-indigo-500 to-purple-500 h-1.5 rounded-full transition-all"
                            style={{ width: `${Math.max(10, (run.steps_completed / 6) * 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-500">{run.steps_completed} steps</span>
                      </div>

                      {run.current_step && (
                        <div className="flex items-center gap-1 text-xs text-slate-500 mb-2">
                          <ArrowRight className="h-3 w-3" />
                          <span>Current: <strong>{run.current_step}</strong></span>
                        </div>
                      )}

                      {run.human_gate_pending && (
                        <button
                          onClick={() => handleApproveGate(run.run_id)}
                          className="w-full mt-2 px-3 py-1.5 text-xs font-medium bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded-lg hover:bg-amber-100 flex items-center justify-center gap-1"
                        >
                          <CheckCircle2 className="h-3 w-3" /> Approve & Continue
                        </button>
                      )}

                      <div className="text-[10px] text-slate-400 mt-2">
                        ID: {run.run_id} | Started: {timeAgo(run.started_at)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Claude Tasks Tab ── */}
        {tab === 'claude' && (
          <div className="space-y-6">
            {/* Stats */}
            {claudeStats && (
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {[
                  { label: 'Pending', value: claudeStats.pending, color: 'text-amber-600' },
                  { label: 'In Progress', value: claudeStats.in_progress, color: 'text-blue-600' },
                  { label: 'Completed', value: claudeStats.completed, color: 'text-emerald-600' },
                  { label: 'Failed', value: claudeStats.failed, color: 'text-red-600' },
                  { label: 'Total', value: claudeStats.total, color: 'text-slate-700 dark:text-white' },
                ].map(s => (
                  <div key={s.label} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-3 text-center">
                    <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
                    <div className="text-[10px] text-slate-500 uppercase">{s.label}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Submit New Task */}
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-1.5">
                <Brain className="h-4 w-4 text-indigo-500" />
                Submit Research Task
              </h3>
              <div className="flex gap-2 mb-3">
                <select
                  value={newTaskType}
                  onChange={(e) => setNewTaskType(e.target.value)}
                  className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm"
                >
                  <option value="deep_research">Deep Research</option>
                  <option value="contact_analysis">Contact Analysis</option>
                  <option value="competitive_brief">Competitive Brief</option>
                  <option value="proposal_section">Proposal Section</option>
                  <option value="data_reconciliation">Data Reconciliation</option>
                </select>
                <input
                  type="text"
                  value={newPrompt}
                  onChange={(e) => setNewPrompt(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSubmitClaude()}
                  placeholder="Describe the research task..."
                  className="flex-1 px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  onClick={handleSubmitClaude}
                  disabled={submitting || !newPrompt.trim()}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-1.5"
                >
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  Submit
                </button>
              </div>
            </div>

            {/* Task List */}
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Task Queue</h3>
              </div>
              {claudeTasks.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-sm">No tasks submitted yet</div>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-700/50">
                  {claudeTasks.slice(0, 20).map((task) => (
                    <div key={task.task_id} className="px-4 py-3 flex items-center gap-3">
                      <div className="flex-shrink-0">
                        {task.status === 'pending' && <Timer className="h-4 w-4 text-amber-500" />}
                        {task.status === 'in_progress' && <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />}
                        {task.status === 'completed' && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
                        {task.status === 'failed' && <XCircle className="h-4 w-4 text-red-500" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-slate-900 dark:text-white truncate">{task.prompt}</div>
                        <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-0.5">
                          <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700">
                            {task.task_type.replace(/_/g, ' ')}
                          </span>
                          <span>{task.priority}</span>
                          <span>~{task.estimated_tokens} tokens</span>
                        </div>
                      </div>
                      <div className="text-xs text-slate-400 flex-shrink-0">
                        {timeAgo(task.submitted_at)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
