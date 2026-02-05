import { useState, useEffect, useCallback } from 'react';
import { Activity, Play, CheckCircle, XCircle, Clock, RefreshCw, Loader } from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

interface PipelineRun {
  run_id: string;
  timestamp: string;
  success: boolean;
  duration_seconds: number;
  stats: {
    jobs_processed: number;
    hot_leads: number;
    warm_leads: number;
    cold_leads: number;
    briefings_generated: number;
    qa_approved: number;
    qa_needs_review: number;
  };
  errors: string[];
}

interface PipelineData {
  is_running: boolean;
  current_run: { run_id: string; started_at: string } | null;
  last_run: PipelineRun | null;
  history: PipelineRun[];
  stats: { total_runs: number; success_rate: number; avg_duration: number };
}

const PIPELINE_STAGES = [
  'Ingest', 'Mapping', 'Scoring', 'QA', 'Briefings',
  'Export', 'Webhooks', 'Email', 'Bullhorn', 'Dashboard', 'Knowledge',
];

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
      setData(res as PipelineData);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load pipeline status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleTrigger = async (testMode: boolean) => {
    setTriggering(true);
    try {
      const res = await hubApiClient.triggerPipeline({ test_mode: testMode });
      if (res.success) {
        setTimeout(fetchData, 2000);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to trigger pipeline');
    } finally {
      setTriggering(false);
    }
  };

  const formatDuration = (secs: number) => {
    if (secs < 60) return `${secs.toFixed(0)}s`;
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

  return (
    <div className="h-full overflow-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity className="w-8 h-8 text-indigo-600" />
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Pipeline Status</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">11-stage BD automation orchestrator</p>
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

      {/* Running Status */}
      {data?.is_running && data.current_run && (
        <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-4 flex items-center gap-3">
          <Loader className="w-5 h-5 text-indigo-600 animate-spin" />
          <div>
            <p className="font-medium text-indigo-700 dark:text-indigo-400">Pipeline Running</p>
            <p className="text-sm text-indigo-600 dark:text-indigo-500">
              Run ID: {data.current_run.run_id} | Started: {formatTime(data.current_run.started_at)}
            </p>
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
          <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
            {data?.last_run ? (
              <span className={data.last_run.success ? 'text-green-600' : 'text-red-600'}>
                {data.last_run.success ? 'Success' : 'Failed'}
              </span>
            ) : '-'}
          </p>
        </div>
      </div>

      {/* Pipeline Stages */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-5 shadow-sm border border-slate-200 dark:border-slate-700">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Pipeline Stages</h2>
        <div className="flex flex-wrap gap-2">
          {PIPELINE_STAGES.map((stage, i) => (
            <div
              key={stage}
              className="flex items-center gap-2 px-3 py-2 bg-slate-100 dark:bg-slate-700 rounded-lg"
            >
              <span className="w-5 h-5 flex items-center justify-center rounded-full bg-slate-300 dark:bg-slate-600 text-xs font-medium text-slate-700 dark:text-slate-300">
                {i + 1}
              </span>
              <span className="text-sm text-slate-700 dark:text-slate-300">{stage}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Last Run Details */}
      {data?.last_run && (
        <div className="bg-white dark:bg-slate-800 rounded-lg p-5 shadow-sm border border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Last Run Details</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-slate-500 dark:text-slate-400">Jobs Processed</p>
              <p className="text-lg font-medium text-slate-900 dark:text-slate-100">{data.last_run.stats.jobs_processed}</p>
            </div>
            <div>
              <p className="text-slate-500 dark:text-slate-400">Hot Leads</p>
              <p className="text-lg font-medium text-red-600">{data.last_run.stats.hot_leads}</p>
            </div>
            <div>
              <p className="text-slate-500 dark:text-slate-400">QA Approved</p>
              <p className="text-lg font-medium text-green-600">{data.last_run.stats.qa_approved}</p>
            </div>
            <div>
              <p className="text-slate-500 dark:text-slate-400">Duration</p>
              <p className="text-lg font-medium text-slate-900 dark:text-slate-100">{formatDuration(data.last_run.duration_seconds)}</p>
            </div>
          </div>
          {data.last_run.errors.length > 0 && (
            <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <p className="text-sm font-medium text-red-700 dark:text-red-400 mb-1">Errors:</p>
              {data.last_run.errors.map((err, i) => (
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
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Status</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Jobs</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Hot Leads</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Duration</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Errors</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {(!data?.history || data.history.length === 0) && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-500 dark:text-slate-400">
                    No pipeline runs yet
                  </td>
                </tr>
              )}
              {data?.history && [...data.history].reverse().map((run) => (
                <tr key={run.run_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                  <td className="px-4 py-3 font-mono text-xs text-slate-700 dark:text-slate-300">{run.run_id}</td>
                  <td className="px-4 py-3 text-xs text-slate-600 dark:text-slate-400">{formatTime(run.timestamp)}</td>
                  <td className="px-4 py-3 text-center">
                    {run.success ? (
                      <CheckCircle className="w-4 h-4 text-green-500 inline" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-500 inline" />
                    )}
                  </td>
                  <td className="px-4 py-3 text-center text-slate-700 dark:text-slate-300">{run.stats.jobs_processed}</td>
                  <td className="px-4 py-3 text-center text-red-600">{run.stats.hot_leads}</td>
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
