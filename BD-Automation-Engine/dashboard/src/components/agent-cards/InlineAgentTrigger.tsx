/**
 * InlineAgentTrigger - Compact action buttons for triggering agent tasks
 * from detail pages. Shows progress inline and results in a collapsible panel.
 */

import { useState } from 'react';
import { Bot, ChevronDown, ChevronUp } from 'lucide-react';
import { useAgentTask, type AgentTaskType } from '../../hooks/useAgentTask';
import { AgentTaskProgress } from './AgentTaskProgress';
import { AgentResultRenderer } from './AgentResultRenderer';

interface AgentAction {
  label: string;
  type: AgentTaskType;
  query: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string; // tailwind bg class like 'bg-blue-600'
}

interface InlineAgentTriggerProps {
  actions: AgentAction[];
  entityName: string;
  onNavigateToContact?: (name: string) => void;
  onNavigateToProgram?: (name: string) => void;
}

export function InlineAgentTrigger({
  actions,
  entityName,
  onNavigateToContact,
  onNavigateToProgram,
}: InlineAgentTriggerProps) {
  const agentTask = useAgentTask();
  const [expanded, setExpanded] = useState(false);
  const [activeAction, setActiveAction] = useState<string | null>(null);

  const handleTrigger = (action: AgentAction) => {
    setActiveAction(action.label);
    setExpanded(true);
    agentTask.startTask(action.type, action.query.replace('{entity}', entityName));
  };

  const hasResult = agentTask.isCompleted || agentTask.isError;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      {/* Action Buttons Row */}
      <div className="px-4 py-3 flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-400">
          <Bot className="h-4 w-4" />
          <span>AI Actions</span>
        </div>
        <div className="h-4 w-px bg-slate-200 dark:bg-slate-600" />
        {actions.map(action => {
          const Icon = action.icon;
          const isActive = activeAction === action.label && agentTask.isRunning;
          return (
            <button
              key={action.label}
              onClick={() => handleTrigger(action)}
              disabled={agentTask.isRunning}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 cursor-wait'
                  : agentTask.isRunning
                    ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                    : `${action.color} text-white hover:opacity-90 shadow-sm`
              }`}
            >
              <Icon className={`h-3.5 w-3.5 ${isActive ? 'animate-spin' : ''}`} />
              {action.label}
            </button>
          );
        })}

        {/* Expand/Collapse toggle when there's a result */}
        {(agentTask.isRunning || hasResult) && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="ml-auto flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700"
          >
            {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            {expanded ? 'Collapse' : 'Show Result'}
          </button>
        )}
      </div>

      {/* Expanded Progress + Result */}
      {expanded && (agentTask.isRunning || hasResult) && (
        <div className="px-4 pb-4 space-y-3 border-t border-slate-100 dark:border-slate-700 pt-3">
          {agentTask.isRunning && (
            <AgentTaskProgress task={agentTask.task} onCancel={agentTask.cancel} compact />
          )}
          {agentTask.isCompleted && (
            <AgentTaskProgress task={agentTask.task} compact />
          )}
          {agentTask.isError && (
            <AgentTaskProgress task={agentTask.task} compact />
          )}
          {agentTask.isCompleted && agentTask.task.result && (
            <AgentResultRenderer
              task={agentTask.task}
              onNavigateToContact={onNavigateToContact}
              onNavigateToProgram={onNavigateToProgram}
            />
          )}
        </div>
      )}
    </div>
  );
}
