import { useState, useEffect, useCallback } from 'react';
import {
  Activity, Play, CheckCircle, XCircle, Clock, RefreshCw, Loader,
  AlertTriangle, ArrowRight, Timer,
} from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

interface StepResult {
  step_id: string;
  step_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number;
  records_processed: number;
  error: string | null;
}

interface PipelineRun {
  run_id: string;
  test_mode: boolean;
  status: 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at: string | null;
  duration_seconds: number;
  current_step: number;
  total_steps: number;
  steps: StepResult[];
  errors: string[];
  summary: {
    steps_completed: number;
    steps_failed: number;
    total_records: number;
  };
}

interface StepDefinition {
  id: string;
  name: string;
  description: string;
}

interface PipelineData {
  is_running: boolean;
  current_run: PipelineRun | null;
  last_run: PipelineRun | null;
  history: PipelineRun[];
  steps_definition: StepDefinition[];
  stats: { total_runs: number; success_rate: number; avg_duration: number };
}

const STEP_STATUS_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  pending: { bg: 'bg-slate-100 dark:bg-slate-700', text: 'text-slate-400', border: 'border-slate-200 dark:border-slate-600' },
  running: { bg: 'bg-indigo-50 dark:bg-indigo-900/30', text: 'text-indigo-600 dark:text-indigo-400', border: 'border-indigo-300 dark:border-indigo-700' },
  completed: { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-600 dark:text-green-400', border: 'border-green-200 dark:border-green-800' },
  failed: { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-600 dark:text-red-400', border: 'border-red-200 dark:border-red-800' },
  skipped: { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-600 dark:text-amber-400', border: 'border-amber-200 dark:border-amber-800' },
};

function StepIcon({ status }: { status: string }) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'failed':
      return <XCircle className="w-4 h-4 text-red-500" />;
    case 'running':
      return <Loader className="w-4 h-4 text-indigo-500 animate-spin" />;
    case 'skipped':
      return <AlertTriangle className="w-4 h-4 text-amber-500" />;
    default:
      return <Clock className="w-4 h-4 text-slate-400" />;
  }
}

export function PipelineStatus() {
  const [data, setData] = useState<PipelineData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await hubApiClient.getPipelineStatus();
      setData(res as unknown as PipelineData);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load pipeline status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleTrigger = async (testMode: boolean) => {
    setTriggering(true);
    try {
      await hubApiClient.triggerPipeline({ test_mode: testMode });
      setTimeout(fetchData, 1500);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to trigger pipeline');
    } finally {
      setTriggering(false);
    }
  };

  const formatDuration = (secs: number) => {
    if (secs < 60) return `${secs.toFixed(1)}s`;
    const mins = Math.floor(secs / 60);
    const rem = Math.round(secs % 60);
    return `${mins}m ${rem}s`;
  };

  const formatTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  };

  // Determine which steps to show (from current/last run or definitions)
  const activeRun = data?.current_run ?? data?.last_run;
  const steps = activeRun?.steps ?? [];
  const stepDefs = data?.steps_definition ?? [];

  return (
    <div className="h-full overflow-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity className="w-8 h-8 text-indigo-600" />
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Pipeline Orchestrator</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">8-step BD automation pipeline</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => handleTrigger(true)}
            disabled={triggering || data?.is_running}
            className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 transition-colors"
          >
            <Play className="w-4 h-4" /> Test Run
          </button>
          <button
            onClick={() => handleTrigger(false)}
            disabled={triggering || data?.is_running}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            <Play className="w-4 h-4" /> Full Pipeline
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Running banner */}
      {data?.is_running && data.current_run && (
        <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Loader className="w-5 h-5 text-indigo-600 animate-spin" />
              <div>
                <p className="font-medium text-indigo-700 dark:text-indigo-400">Pipeline Running</p>
                <p className="text-sm text-indigo-600 dark:text-indigo-500">
                  Step {data.current_run.current_step} of {data.current_run.total_steps}
                  {data.current_run.test_mode && ' (Test Mode)'}
                </p>
              </div>
            </div>
            <div className="w-32">
              <div className="w-full bg-indigo-200 dark:bg-indigo-800 rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-indigo-600 transition-all duration-500"
                  style={{ width: `${(data.current_run.current_step / data.current_run.total_steps) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-800 rounded-lg p-5 shadow-sm border border-slate-200 dark:border-slate-700">
          <p className="text-sm text-slate-500 dark:text-slate-400">Total Runs</p>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{data?.stats.total_runs ?? 0}</p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg p-5 shadow-sm border border-slate-200 dark:border-slate-700">
          <p className="text-sm text-slate-500 dark:text-slate-400">Success Rate</p>
          <p className={`text-2xl font-bold ${(data?.stats.success_rate ?? 0) >= 0.8 ? 'text-green-600' : 'text-yellow-600'}`}>
            {((data?.stats.success_rate ?? 0) * 100).toFixed(0)}%
          </p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg p-5 shadow-sm border border-slate-200 dark:border-slate-700">
          <p className="text-sm text-slate-500 dark:text-slate-400">Avg Duration</p>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {data?.stats.avg_duration ? formatDuration(data.stats.avg_duration) : '-'}
          </p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg p-5 shadow-sm border border-slate-200 dark:border-slate-700">
          <p className="text-sm text-slate-500 dark:text-slate-400">Last Run</p>
          <p className="text-lg font-bold">
            {data?.last_run ? (
              <span className={data.last_run.status === 'completed' ? 'text-green-600' : 'text-red-600'}>
                {data.last_run.status === 'completed' ? 'Success' : 'Failed'}
              </span>
            ) : '-'}
          </p>
        </div>
      </div>

      {/* 8-Step Pipeline Visual */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-5 shadow-sm border border-slate-200 dark:border-slate-700">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Pipeline Steps</h2>
        {steps.length > 0 ? (
          <div className="space-y-2">
            {steps.map((step, i) => {
              const style = STEP_STATUS_STYLES[step.status] || STEP_STATUS_STYLES.pending;
              return (
                <div key={step.step_id}>
                  <div className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${style.border} ${style.bg}`}>
                    <span className="w-6 h-6 flex items-center justify-center rounded-full bg-slate-200 dark:bg-slate-600 text-xs font-bold text-slate-600 dark:text-slate-300">
                      {i + 1}
                    </span>
                    <StepIcon status={step.status} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-medium ${style.text}`}>{step.step_name}</span>
                        <span className="text-xs text-slate-400 capitalize">{step.status}</span>
                      </div>
                      {step.error && (
                        <p className="text-xs text-red-500 mt-0.5 truncate">{step.error}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-500">
                      {step.records_processed > 0 && (
                        <span>{step.records_processed} records</span>
                      )}
                      {step.duration_seconds > 0 && (
                        <span className="flex items-center gap-1">
                          <Timer className="w-3 h-3" />
                          {formatDuration(step.duration_seconds)}
                        </span>
                      )}
                    </div>
                  </div>
                  {i < steps.length - 1 && (
                    <div className="flex justify-center py-0.5">
                      <ArrowRight className="w-3 h-3 text-slate-300 dark:text-slate-600 rotate-90" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : stepDefs.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {stepDefs.map((def, i) => (
              <div
                key={def.id}
                className="flex items-center gap-2 px-3 py-2 bg-slate-100 dark:bg-slate-700 rounded-lg"
                title={def.description}
              >
                <span className="w-5 h-5 flex items-center justify-center rounded-full bg-slate-300 dark:bg-slate-600 text-xs font-medium text-slate-700 dark:text-slate-300">
                  {i + 1}
                </span>
                <span className="text-sm text-slate-700 dark:text-slate-300">{def.name}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-400 text-center py-4">No pipeline data available. Run the pipeline to see steps.</p>
        )}
      </div>

      {/* Last Run Summary */}
      {activeRun && activeRun.status !== 'running' && (
        <div className="bg-white dark:bg-slate-800 rounded-lg p-5 shadow-sm border border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Last Run Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
            <div>
              <p className="text-slate-500 dark:text-slate-400">Run ID</p>
              <p className="font-mono text-sm text-slate-900 dark:text-slate-100">{activeRun.run_id}</p>
            </div>
            <div>
              <p className="text-slate-500 dark:text-slate-400">Status</p>
              <p className={`font-medium ${activeRun.status === 'completed' ? 'text-green-600' : 'text-red-600'}`}>
                {activeRun.status === 'completed' ? 'Completed' : 'Failed'}
              </p>
            </div>
            <div>
              <p className="text-slate-500 dark:text-slate-400">Duration</p>
              <p className="text-slate-900 dark:text-slate-100">{formatDuration(activeRun.duration_seconds)}</p>
            </div>
            <div>
              <p className="text-slate-500 dark:text-slate-400">Steps OK</p>
              <p className="text-slate-900 dark:text-slate-100">
                {activeRun.summary.steps_completed}/{activeRun.total_steps}
              </p>
            </div>
            <div>
              <p className="text-slate-500 dark:text-slate-400">Records</p>
              <p className="text-slate-900 dark:text-slate-100">{activeRun.summary.total_records}</p>
            </div>
          </div>
          {activeRun.errors.length > 0 && (
            <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <p className="text-sm font-medium text-red-700 dark:text-red-400 mb-1">Errors:</p>
              {activeRun.errors.map((err, i) => (
                <p key={i} className="text-xs text-red-600 dark:text-red-500">{err}</p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Run History */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Run History</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900/50">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Run ID</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Time</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Mode</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Status</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Steps</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Records</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Duration</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Errors</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {(!data?.history || data.history.length === 0) && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-slate-500 dark:text-slate-400">
                    No pipeline runs yet. Click "Test Run" or "Full Pipeline" to start.
                  </td>
                </tr>
              )}
              {data?.history && [...data.history].reverse().map((run) => (
                <tr key={run.run_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                  <td className="px-4 py-3 font-mono text-xs text-slate-700 dark:text-slate-300">{run.run_id}</td>
                  <td className="px-4 py-3 text-xs text-slate-600 dark:text-slate-400">
                    {run.completed_at ? formatTime(run.completed_at) : formatTime(run.started_at)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      run.test_mode
                        ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                        : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                    }`}>
                      {run.test_mode ? 'Test' : 'Full'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {run.status === 'completed' ? (
                      <CheckCircle className="w-4 h-4 text-green-500 inline" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-500 inline" />
                    )}
                  </td>
                  <td className="px-4 py-3 text-center text-slate-700 dark:text-slate-300">
                    {run.summary?.steps_completed ?? 0}/{run.total_steps}
                  </td>
                  <td className="px-4 py-3 text-center text-slate-700 dark:text-slate-300">
                    {run.summary?.total_records ?? 0}
                  </td>
                  <td className="px-4 py-3 text-center text-slate-600 dark:text-slate-400">
                    <Clock className="w-3 h-3 inline mr-1" />
                    {formatDuration(run.duration_seconds)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {run.errors.length > 0 ? (
                      <span className="px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-full text-xs">
                        {run.errors.length}
                      </span>
                    ) : (
                      <span className="text-green-600 text-xs">0</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
