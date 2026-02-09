/**
 * AgentTaskProgress - Inline progress bar + steps for a running agent task.
 * Used inside detail pages and the AgentPanel.
 */

import { Loader2, CheckCircle2, AlertCircle, XCircle, Clock } from 'lucide-react';
import type { AgentTaskResult, AgentTaskStep } from '../../hooks/useAgentTask';

interface AgentTaskProgressProps {
  task: AgentTaskResult;
  onCancel?: () => void;
  compact?: boolean;
}

function StepDot({ step }: { step: AgentTaskStep }) {
  switch (step.status) {
    case 'done':
      return <CheckCircle2 className="h-3.5 w-3.5 text-green-500 flex-shrink-0" />;
    case 'running':
      return <Loader2 className="h-3.5 w-3.5 text-blue-500 animate-spin flex-shrink-0" />;
    case 'error':
      return <XCircle className="h-3.5 w-3.5 text-red-500 flex-shrink-0" />;
    default:
      return <Clock className="h-3.5 w-3.5 text-slate-300 flex-shrink-0" />;
  }
}

export function AgentTaskProgress({ task, onCancel, compact = false }: AgentTaskProgressProps) {
  if (task.status === 'idle') return null;

  const elapsed = task.startedAt
    ? ((task.completedAt || Date.now()) - task.startedAt) / 1000
    : 0;

  return (
    <div className={`rounded-lg border ${
      task.status === 'error' ? 'border-red-200 bg-red-50' :
      task.status === 'completed' ? 'border-green-200 bg-green-50' :
      'border-blue-200 bg-blue-50'
    } ${compact ? 'p-3' : 'p-4'}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {task.status === 'completed' ? (
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          ) : task.status === 'error' ? (
            <AlertCircle className="h-4 w-4 text-red-600" />
          ) : (
            <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
          )}
          <span className={`text-sm font-medium ${
            task.status === 'error' ? 'text-red-900' :
            task.status === 'completed' ? 'text-green-900' :
            'text-blue-900'
          }`}>
            {task.status === 'creating' ? 'Starting agent...' :
             task.status === 'streaming' ? 'Agent working...' :
             task.status === 'completed' ? 'Task complete' :
             'Task failed'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">{elapsed.toFixed(1)}s</span>
          {(task.status === 'creating' || task.status === 'streaming') && onCancel && (
            <button
              onClick={onCancel}
              className="text-xs text-red-600 hover:text-red-800 font-medium"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1.5 bg-white/60 rounded-full overflow-hidden mb-2">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            task.status === 'error' ? 'bg-red-500' :
            task.status === 'completed' ? 'bg-green-500' :
            'bg-blue-500'
          }`}
          style={{ width: `${task.progress}%` }}
        />
      </div>

      {/* Steps (non-compact mode) */}
      {!compact && task.steps.length > 0 && (
        <div className="space-y-1 mt-2">
          {task.steps.slice(-4).map((step, i) => (
            <div key={i} className="flex items-center gap-2">
              <StepDot step={step} />
              <span className="text-xs text-slate-600">{step.label}</span>
              {step.detail && (
                <span className="text-xs text-slate-400 truncate">— {step.detail}</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Error message */}
      {task.error && (
        <p className="text-xs text-red-600 mt-1">{task.error}</p>
      )}
    </div>
  );
}
