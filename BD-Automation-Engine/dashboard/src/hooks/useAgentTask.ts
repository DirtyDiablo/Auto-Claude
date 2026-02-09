/**
 * useAgentTask Hook
 *
 * SSE-streaming hook for agent tasks. Creates a task via POST /agents/tasks/create,
 * then connects to GET /agents/tasks/{task_id}/stream for real-time updates.
 */

import { useState, useCallback, useRef } from 'react';

// =============================================================================
// TYPES
// =============================================================================

export type AgentTaskType =
  | 'program_analysis'
  | 'contact_enrichment'
  | 'competitive_report'
  | 'outreach_draft'
  | 'strategy_brief'
  | 'humint_analysis';

export type AgentTaskStatus = 'idle' | 'creating' | 'streaming' | 'completed' | 'error';

export interface AgentTaskStep {
  label: string;
  status: 'pending' | 'running' | 'done' | 'error';
  detail?: string;
  timestamp: number;
}

export interface AgentTaskResult {
  task_id: string;
  type: AgentTaskType;
  query: string;
  status: AgentTaskStatus;
  progress: number; // 0-100
  steps: AgentTaskStep[];
  result: Record<string, unknown> | null;
  error: string | null;
  startedAt: number | null;
  completedAt: number | null;
}

const INITIAL_RESULT: AgentTaskResult = {
  task_id: '',
  type: 'program_analysis',
  query: '',
  status: 'idle',
  progress: 0,
  steps: [],
  result: null,
  error: null,
  startedAt: null,
  completedAt: null,
};

// =============================================================================
// HOOK
// =============================================================================

const API_BASE = import.meta.env.VITE_API_BASE || '';

export function useAgentTask() {
  const [task, setTask] = useState<AgentTaskResult>({ ...INITIAL_RESULT });
  const abortRef = useRef<AbortController | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const reset = useCallback(() => {
    // Cleanup any running connections
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setTask({ ...INITIAL_RESULT });
  }, []);

  const startTask = useCallback(async (type: AgentTaskType, query: string) => {
    // Cleanup previous
    reset();

    const abortController = new AbortController();
    abortRef.current = abortController;

    setTask({
      ...INITIAL_RESULT,
      type,
      query,
      status: 'creating',
      startedAt: Date.now(),
    });

    try {
      // Step 1: Create task via POST
      const createRes = await fetch(`${API_BASE}/agents/tasks/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, query }),
        signal: abortController.signal,
      });

      if (!createRes.ok) {
        throw new Error(`Task creation failed: ${createRes.status}`);
      }

      const { task_id } = await createRes.json();

      setTask(prev => ({
        ...prev,
        task_id,
        status: 'streaming',
        steps: [{ label: 'Task created', status: 'done', timestamp: Date.now() }],
        progress: 5,
      }));

      // Step 2: Connect SSE stream
      const es = new EventSource(`${API_BASE}/agents/tasks/${task_id}/stream`);
      eventSourceRef.current = es;

      es.addEventListener('progress', (e) => {
        try {
          const data = JSON.parse(e.data);
          setTask(prev => ({
            ...prev,
            progress: data.progress ?? prev.progress,
            steps: data.step
              ? [...prev.steps, {
                  label: data.step,
                  status: 'running' as const,
                  detail: data.detail,
                  timestamp: Date.now(),
                }]
              : prev.steps,
          }));
        } catch { /* ignore parse errors */ }
      });

      es.addEventListener('complete', (e) => {
        try {
          const data = JSON.parse(e.data);
          setTask(prev => ({
            ...prev,
            status: 'completed',
            progress: 100,
            result: data.result ?? data,
            completedAt: Date.now(),
            steps: prev.steps.map(s => ({ ...s, status: 'done' as const })),
          }));
        } catch {
          setTask(prev => ({
            ...prev,
            status: 'completed',
            progress: 100,
            completedAt: Date.now(),
          }));
        }
        es.close();
        eventSourceRef.current = null;
      });

      es.addEventListener('error', (e) => {
        // SSE error event
        if (es.readyState === EventSource.CLOSED) return;
        let errorMsg = 'Agent task failed';
        try {
          if (e instanceof MessageEvent && e.data) {
            const data = JSON.parse(e.data);
            errorMsg = data.message || data.error || errorMsg;
          }
        } catch { /* use default */ }
        setTask(prev => ({
          ...prev,
          status: 'error',
          error: errorMsg,
          completedAt: Date.now(),
        }));
        es.close();
        eventSourceRef.current = null;
      });

      es.addEventListener('timeout', () => {
        setTask(prev => ({
          ...prev,
          status: 'error',
          error: 'Agent task timed out',
          completedAt: Date.now(),
        }));
        es.close();
        eventSourceRef.current = null;
      });

      // Generic message handler for untyped events
      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.status === 'complete' || data.done) {
            setTask(prev => ({
              ...prev,
              status: 'completed',
              progress: 100,
              result: data.result ?? data,
              completedAt: Date.now(),
            }));
            es.close();
            eventSourceRef.current = null;
          } else if (data.progress !== undefined) {
            setTask(prev => ({
              ...prev,
              progress: data.progress,
            }));
          }
        } catch { /* ignore */ }
      };

    } catch (err) {
      if (abortController.signal.aborted) return;
      setTask(prev => ({
        ...prev,
        status: 'error',
        error: err instanceof Error ? err.message : 'Failed to start agent task',
        completedAt: Date.now(),
      }));
    }
  }, [reset]);

  const cancel = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setTask(prev => ({
      ...prev,
      status: 'error',
      error: 'Cancelled by user',
      completedAt: Date.now(),
    }));
  }, []);

  return {
    task,
    startTask,
    cancel,
    reset,
    isRunning: task.status === 'creating' || task.status === 'streaming',
    isCompleted: task.status === 'completed',
    isError: task.status === 'error',
  };
}
