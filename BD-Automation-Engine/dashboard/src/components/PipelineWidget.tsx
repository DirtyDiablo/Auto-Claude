import { useState, useEffect } from 'react';
import { Activity, Play, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

interface PipelineWidgetData {
  is_running: boolean;
  current_run: {
    run_id: string;
    current_step: number;
    total_steps: number;
    status: string;
  } | null;
  last_run: {
    run_id: string;
    status: string;
    duration_seconds: number;
    completed_at: string;
    summary: {
      steps_completed: number;
      steps_failed: number;
      total_records: number;
    };
  } | null;
  stats: {
    total_runs: number;
    success_rate: number;
    avg_duration: number;
  };
}

interface PipelineWidgetProps {
  onNavigate?: () => void;
}

export function PipelineWidget({ onNavigate }: PipelineWidgetProps) {
  const [data, setData] = useState<PipelineWidgetData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function fetch() {
      try {
        const res = await hubApiClient.getPipelineStatus();
        if (mounted) setData(res as unknown as PipelineWidgetData);
      } catch {
        // API not available
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetch();
    const interval = setInterval(fetch, 30000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
        <div className="flex items-center gap-2 text-slate-400">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm">Loading pipeline...</span>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const formatDuration = (secs: number) => {
    if (secs < 60) return `${secs.toFixed(0)}s`;
    const mins = Math.floor(secs / 60);
    const rem = Math.round(secs % 60);
    return `${mins}m ${rem}s`;
  };

  const formatTimeAgo = (iso: string) => {
    try {
      const diff = Date.now() - new Date(iso).getTime();
      const mins = Math.floor(diff / 60000);
      if (mins < 1) return 'just now';
      if (mins < 60) return `${mins}m ago`;
      const hours = Math.floor(mins / 60);
      if (hours < 24) return `${hours}h ago`;
      return `${Math.floor(hours / 24)}d ago`;
    } catch {
      return '';
    }
  };

  return (
    <div
      className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onNavigate}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onNavigate?.()}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-900/30">
            <Activity className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
          </div>
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Pipeline Status</h3>
        </div>
        {data.is_running ? (
          <span className="flex items-center gap-1 text-xs text-indigo-600 dark:text-indigo-400">
            <Loader2 className="h-3 w-3 animate-spin" />
            Running
          </span>
        ) : (
          <span className="text-xs text-slate-400">
            {data.stats.total_runs} runs
          </span>
        )}
      </div>

      {/* Progress bar when running */}
      {data.is_running && data.current_run && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Step {data.current_run.current_step}/{data.current_run.total_steps}</span>
          </div>
          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
            <div
              className="h-2 rounded-full bg-gradient-to-r from-indigo-500 to-blue-500 transition-all duration-500"
              style={{ width: `${(data.current_run.current_step / data.current_run.total_steps) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-2">
        <div className="text-center">
          <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
            {data.last_run ? (
              data.last_run.status === 'completed' ? (
                <CheckCircle className="h-5 w-5 text-green-500 mx-auto" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500 mx-auto" />
              )
            ) : (
              <Play className="h-5 w-5 text-slate-400 mx-auto" />
            )}
          </p>
          <p className="text-[10px] text-slate-400 mt-0.5">Last Run</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
            {((data.stats.success_rate ?? 0) * 100).toFixed(0)}%
          </p>
          <p className="text-[10px] text-slate-400">Success</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
            {data.stats.avg_duration ? formatDuration(data.stats.avg_duration) : '-'}
          </p>
          <p className="text-[10px] text-slate-400">Avg Time</p>
        </div>
      </div>

      {/* Last run info */}
      {data.last_run?.completed_at && (
        <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-700">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatTimeAgo(data.last_run.completed_at)}
            </span>
            <span>{data.last_run.summary.steps_completed}/{data.last_run.summary.steps_completed + data.last_run.summary.steps_failed} steps OK</span>
          </div>
        </div>
      )}
    </div>
  );
}
