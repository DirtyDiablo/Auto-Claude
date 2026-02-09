/**
 * Agent Panel Page
 *
 * BD Agent execution interface with 4 agent cards and 3 workflow buttons.
 */

import { useState } from 'react';
import {
  Bot,
  Building2,
  Search,
  Users,
  Target,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  FileText,
  Calendar,
  Clock,
  ArrowUpDown,
  Eye,
  RefreshCw,
  XCircle,
  Zap,
  Play,
} from 'lucide-react';
import { AgentCard } from '../components/hub/AgentCard';
import { useHubAgent, useAgentTasks, type AgentTask } from '../hooks/useHubApi';
import { hubApiClient, type WorkflowResult } from '../services/hubApi';
import { useAgentTask, type AgentTaskType } from '../hooks/useAgentTask';
import { AgentTaskProgress, AgentResultRenderer } from '../components/agent-cards';

const QUICK_LAUNCH_TYPES: Array<{ value: AgentTaskType; label: string }> = [
  { value: 'program_analysis', label: 'Program Analysis' },
  { value: 'contact_enrichment', label: 'Contact Enrichment' },
  { value: 'competitive_report', label: 'Competitive Report' },
  { value: 'outreach_draft', label: 'Outreach Draft' },
  { value: 'strategy_brief', label: 'Strategy Brief' },
  { value: 'humint_analysis', label: 'HUMINT Analysis' },
];

export function AgentPanel() {
  // Agent hooks
  const programAgent = useHubAgent('program');
  const companyAgent = useHubAgent('company');
  const contactAgent = useHubAgent('contact');
  const strategyAgent = useHubAgent('strategy');

  // Streaming agent task
  const agentTask = useAgentTask();
  const [quickLaunchQuery, setQuickLaunchQuery] = useState('');
  const [quickLaunchType, setQuickLaunchType] = useState<AgentTaskType>('program_analysis');

  // Agent task polling (every 5 seconds)
  const { data: taskData, loading: tasksLoading, refetch: refetchTasks } = useAgentTasks(5000);
  const [expandedTask, setExpandedTask] = useState<string | null>(null);
  const [sortField, setSortField] = useState<'created_at' | 'status' | 'crew_type'>('created_at');
  const [sortAsc, setSortAsc] = useState(false);

  // Workflow state
  const [workflowLoading, setWorkflowLoading] = useState<string | null>(null);
  const [workflowResult, setWorkflowResult] = useState<WorkflowResult | null>(null);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [workflowInput, setWorkflowInput] = useState('');

  const handleQuickLaunch = () => {
    if (!quickLaunchQuery.trim()) return;
    agentTask.startTask(quickLaunchType, quickLaunchQuery);
  };

  // Workflow handlers
  const handleAnalyzeProgram = async () => {
    if (!workflowInput.trim()) return;
    setWorkflowLoading('analyze');
    setWorkflowError(null);
    try {
      const result = await hubApiClient.analyzeProgram(workflowInput);
      setWorkflowResult(result);
    } catch (err) {
      setWorkflowError(err instanceof Error ? err.message : 'Workflow failed');
    } finally {
      setWorkflowLoading(null);
    }
  };

  const handlePrepareOutreach = async () => {
    if (!workflowInput.trim()) return;
    setWorkflowLoading('outreach');
    setWorkflowError(null);
    try {
      const result = await hubApiClient.prepareOutreach(workflowInput);
      setWorkflowResult(result);
    } catch (err) {
      setWorkflowError(err instanceof Error ? err.message : 'Workflow failed');
    } finally {
      setWorkflowLoading(null);
    }
  };

  const handleWeeklyIntel = async () => {
    setWorkflowLoading('weekly');
    setWorkflowError(null);
    try {
      const result = await hubApiClient.generateWeeklyIntel();
      setWorkflowResult(result);
    } catch (err) {
      setWorkflowError(err instanceof Error ? err.message : 'Workflow failed');
    } finally {
      setWorkflowLoading(null);
    }
  };

  return (
    <div className="p-6 h-full overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-gradient-to-br from-green-500 to-emerald-500">
            <Bot className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">BD Agents</h1>
            <p className="text-slate-500">
              AI-powered agents for program research, company analysis, and BD strategy
            </p>
          </div>
        </div>
      </div>

      {/* Agent Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Program Intel Agent */}
        <AgentCard
          title="Program Intel Agent"
          description="Research federal programs, contracts, and opportunities"
          placeholder="e.g., Tell me about AF DCGS contract structure..."
          icon={Building2}
          onExecute={programAgent.execute}
          loading={programAgent.loading}
          result={programAgent.data}
          error={programAgent.error}
        />

        {/* Company Research Agent */}
        <AgentCard
          title="Company Research Agent"
          description="Analyze contractors, capabilities, and market position"
          placeholder="e.g., What programs does Leidos prime?..."
          icon={Search}
          onExecute={companyAgent.execute}
          loading={companyAgent.loading}
          result={companyAgent.data}
          error={companyAgent.error}
        />

        {/* Contact Finder Agent */}
        <AgentCard
          title="Contact Finder Agent"
          description="Find key contacts by program, company, or role"
          placeholder="e.g., Who are the decision makers for GBSD?..."
          icon={Users}
          onExecute={contactAgent.execute}
          loading={contactAgent.loading}
          result={contactAgent.data}
          error={contactAgent.error}
        />

        {/* BD Strategy Agent */}
        <AgentCard
          title="BD Strategy Agent"
          description="Get strategic recommendations for pursuit and capture"
          placeholder="e.g., How should we approach the DCGS recompete?..."
          icon={Target}
          onExecute={strategyAgent.execute}
          loading={strategyAgent.loading}
          result={strategyAgent.data}
          error={strategyAgent.error}
        />
      </div>

      {/* Quick Launch - SSE Streaming Agent */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-8">
        <div className="p-4 border-b border-slate-100 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-blue-600" />
            <span className="font-semibold text-slate-900">Quick Launch Agent Task</span>
            <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full font-medium">Streaming</span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Launch a task with real-time SSE progress updates and structured results
          </p>
        </div>
        <div className="p-4">
          <div className="flex gap-3 mb-4">
            <select
              value={quickLaunchType}
              onChange={(e) => setQuickLaunchType(e.target.value as AgentTaskType)}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
            >
              {QUICK_LAUNCH_TYPES.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
            <input
              type="text"
              value={quickLaunchQuery}
              onChange={(e) => setQuickLaunchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuickLaunch()}
              placeholder="Enter query (e.g., AF DCGS, Leidos, John Smith)..."
              className="flex-1 px-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              onClick={handleQuickLaunch}
              disabled={agentTask.isRunning || !quickLaunchQuery.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              {agentTask.isRunning ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              {agentTask.isRunning ? 'Running...' : 'Launch'}
            </button>
          </div>

          {/* Live Progress */}
          {(agentTask.isRunning || agentTask.isCompleted || agentTask.isError) && (
            <div className="space-y-3">
              <AgentTaskProgress
                task={agentTask.task}
                onCancel={agentTask.cancel}
              />
              {agentTask.isCompleted && agentTask.task.result && (
                <AgentResultRenderer task={agentTask.task} />
              )}
              {(agentTask.isCompleted || agentTask.isError) && (
                <div className="flex justify-end">
                  <button
                    onClick={agentTask.reset}
                    className="text-xs text-slate-500 hover:text-slate-700 px-3 py-1 rounded hover:bg-slate-100"
                  >
                    Clear result
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Workflows Section */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-gradient-to-r from-amber-50 to-orange-50">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-amber-600" />
            <span className="font-semibold text-slate-900">Automated Workflows</span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Run multi-step BD workflows that combine multiple agents
          </p>
        </div>

        <div className="p-4">
          {/* Workflow Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Target (for Analyze Program and Prepare Outreach workflows)
            </label>
            <input
              type="text"
              value={workflowInput}
              onChange={(e) => setWorkflowInput(e.target.value)}
              placeholder="Enter program or contact name..."
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
            />
          </div>

          {/* Workflow Buttons */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <button
              onClick={handleAnalyzeProgram}
              disabled={workflowLoading !== null || !workflowInput.trim()}
              className="flex items-center justify-center gap-2 px-4 py-3 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
            >
              {workflowLoading === 'analyze' ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <FileText className="h-5 w-5" />
              )}
              <span className="font-medium">Analyze Program</span>
            </button>

            <button
              onClick={handlePrepareOutreach}
              disabled={workflowLoading !== null || !workflowInput.trim()}
              className="flex items-center justify-center gap-2 px-4 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
            >
              {workflowLoading === 'outreach' ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Users className="h-5 w-5" />
              )}
              <span className="font-medium">Prepare Outreach</span>
            </button>

            <button
              onClick={handleWeeklyIntel}
              disabled={workflowLoading !== null}
              className="flex items-center justify-center gap-2 px-4 py-3 bg-rose-600 text-white rounded-lg hover:bg-rose-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
            >
              {workflowLoading === 'weekly' ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Calendar className="h-5 w-5" />
              )}
              <span className="font-medium">Weekly Intel</span>
            </button>
          </div>

          {/* Workflow Loading Progress */}
          {workflowLoading && (
            <div className="mb-4 p-4 bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg border border-amber-200">
              <div className="flex items-center gap-3 mb-3">
                <Loader2 className="h-5 w-5 text-amber-600 animate-spin" />
                <span className="font-medium text-amber-900">
                  Running {workflowLoading === 'analyze' ? 'Program Analysis' : workflowLoading === 'outreach' ? 'Outreach Preparation' : 'Weekly Intel'} Workflow...
                </span>
              </div>
              <div className="w-full h-2 bg-amber-100 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-amber-400 to-orange-500 rounded-full animate-progress" />
              </div>
              <div className="mt-2 flex justify-between text-xs text-amber-600">
                <span>Gathering data...</span>
                <span>Multi-agent processing</span>
              </div>
            </div>
          )}

          {/* Workflow Error */}
          {workflowError && !workflowLoading && (
            <div className="mb-4 p-3 bg-red-50 rounded-lg flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-red-800">Workflow Failed</p>
                <p className="text-sm text-red-600">{workflowError}</p>
              </div>
            </div>
          )}

          {/* Workflow Result */}
          {workflowResult && !workflowLoading && (
            <div className={`p-4 rounded-lg border ${
              workflowResult.status === 'completed' ? 'bg-green-50 border-green-200' :
              workflowResult.status === 'failed' ? 'bg-red-50 border-red-200' :
              'bg-amber-50 border-amber-200'
            }`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  {workflowResult.status === 'completed' ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : workflowResult.status === 'failed' ? (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-yellow-500" />
                  )}
                  <span className={`font-medium capitalize ${
                    workflowResult.status === 'completed' ? 'text-green-900' :
                    workflowResult.status === 'failed' ? 'text-red-900' : 'text-amber-900'
                  }`}>
                    {workflowResult.workflow.replace(/-/g, ' ')} - {workflowResult.status}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  {/* Steps Progress */}
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      {Array.from({ length: workflowResult.total_steps }).map((_, i) => (
                        <div
                          key={i}
                          className={`w-2 h-2 rounded-full ${
                            i < workflowResult.steps_completed
                              ? workflowResult.status === 'completed' ? 'bg-green-500' : 'bg-amber-500'
                              : 'bg-slate-300'
                          }`}
                        />
                      ))}
                    </div>
                    <span className="text-xs text-slate-500">
                      {workflowResult.steps_completed}/{workflowResult.total_steps}
                    </span>
                  </div>
                  <span className="text-sm text-slate-500">
                    {workflowResult.execution_time.toFixed(1)}s
                  </span>
                </div>
              </div>

              {/* Result Content */}
              {workflowResult.result && (
                <div className="bg-white rounded-lg border border-slate-200 p-4 mt-3">
                  <pre className="text-sm text-slate-700 whitespace-pre-wrap overflow-auto max-h-64 font-mono">
                    {JSON.stringify(workflowResult.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Task History */}
      <div className="mt-8 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-slate-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-slate-600" />
              <span className="font-semibold text-slate-900">Task History</span>
              {taskData && taskData.total > 0 && (
                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                  {taskData.total}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Auto-refresh 5s</span>
              <button
                onClick={() => refetchTasks()}
                className="p-1.5 hover:bg-slate-200 rounded-lg transition-colors"
                title="Refresh now"
              >
                <RefreshCw className={`h-4 w-4 text-slate-500 ${tasksLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>

        {(!taskData || taskData.tasks.length === 0) && !tasksLoading && (
          <div className="p-8 text-center text-slate-400">
            <Bot className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No agent tasks yet. Trigger an agent or workflow above.</p>
          </div>
        )}

        {taskData && taskData.tasks.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Task ID
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:text-slate-700"
                    onClick={() => { setSortField('crew_type'); setSortAsc(sortField === 'crew_type' ? !sortAsc : true); }}
                  >
                    <div className="flex items-center gap-1">
                      Type <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:text-slate-700"
                    onClick={() => { setSortField('status'); setSortAsc(sortField === 'status' ? !sortAsc : true); }}
                  >
                    <div className="flex items-center gap-1">
                      Status <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:text-slate-700"
                    onClick={() => { setSortField('created_at'); setSortAsc(sortField === 'created_at' ? !sortAsc : true); }}
                  >
                    <div className="flex items-center gap-1">
                      Created <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {[...taskData.tasks]
                  .sort((a, b) => {
                    const aVal = a[sortField] || '';
                    const bVal = b[sortField] || '';
                    const cmp = String(aVal).localeCompare(String(bVal));
                    return sortAsc ? cmp : -cmp;
                  })
                  .map((task: AgentTask) => {
                    const statusConfig: Record<string, { color: string; bg: string; icon: typeof CheckCircle2 }> = {
                      completed: { color: 'text-green-700', bg: 'bg-green-100', icon: CheckCircle2 },
                      running: { color: 'text-blue-700', bg: 'bg-blue-100', icon: Loader2 },
                      queued: { color: 'text-amber-700', bg: 'bg-amber-100', icon: Clock },
                      failed: { color: 'text-red-700', bg: 'bg-red-100', icon: XCircle },
                    };
                    const cfg = statusConfig[task.status] || statusConfig.queued;
                    const StatusIcon = cfg.icon;
                    const created = new Date(task.created_at);
                    const completed = task.completed_at ? new Date(task.completed_at) : null;
                    const duration = completed
                      ? ((completed.getTime() - created.getTime()) / 1000).toFixed(1) + 's'
                      : task.status === 'running'
                        ? ((Date.now() - created.getTime()) / 1000).toFixed(0) + 's...'
                        : '-';

                    return (
                      <tr key={task.task_id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3">
                          <code className="text-xs font-mono text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                            {task.task_id.slice(0, 8)}
                          </code>
                        </td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full font-medium capitalize">
                            {task.crew_type.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center gap-1 px-2 py-1 ${cfg.bg} ${cfg.color} text-xs rounded-full font-medium capitalize`}>
                            <StatusIcon className={`h-3 w-3 ${task.status === 'running' ? 'animate-spin' : ''}`} />
                            {task.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-600">
                          {created.toLocaleTimeString()}
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-600 font-mono">
                          {duration}
                        </td>
                        <td className="px-4 py-3 text-right">
                          {(task.status === 'completed' || task.status === 'failed') && (
                            <button
                              onClick={() => setExpandedTask(expandedTask === task.task_id ? null : task.task_id)}
                              className="p-1.5 hover:bg-slate-200 rounded-lg transition-colors"
                              title="View result"
                            >
                              <Eye className="h-4 w-4 text-slate-500" />
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        )}

        {/* Expanded Task Result */}
        {expandedTask && taskData?.tasks.find(t => t.task_id === expandedTask) && (
          <div className="border-t border-slate-200 p-4 bg-slate-50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-slate-700">
                Result for {expandedTask.slice(0, 8)}...
              </span>
              <button
                onClick={() => setExpandedTask(null)}
                className="text-xs text-slate-500 hover:text-slate-700"
              >
                Close
              </button>
            </div>
            <pre className="text-xs text-slate-600 bg-white rounded-lg border border-slate-200 p-3 overflow-auto max-h-48 font-mono">
              {JSON.stringify(
                taskData.tasks.find(t => t.task_id === expandedTask),
                null,
                2
              )}
            </pre>
          </div>
        )}
      </div>

      {/* Tips */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-medium text-blue-900 mb-2">Tips for Better Results</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Be specific with program names (e.g., "AF DCGS" instead of just "DCGS")</li>
          <li>• Include context in strategy queries (e.g., "as a small business subcontractor")</li>
          <li>• Use company full names for better matching (e.g., "Leidos" not "LHI")</li>
          <li>• Combine multiple queries to build a complete picture</li>
        </ul>
      </div>
    </div>
  );
}

export default AgentPanel;
