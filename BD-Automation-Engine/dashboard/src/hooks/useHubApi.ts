/**
 * Hub API React Hooks
 *
 * Custom hooks for interacting with the Hub API.
 * Provides state management, caching, and loading states.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  hubApiClient,
  type HubStats,
  type HubHealth,
  type SmartQueryResult,
  type AgentResponse,
  type SearchStrategy,
  type ProgramEcosystem,
  type ContactNetwork,
  type TeamingPath,
  type MemorySearchResult,
  type EntityFacts,
  type BDInsight,
  type CacheStats,
  type GraphStats,
} from '../services/hubApi';

// =============================================================================
// TYPES
// =============================================================================

interface UseHubQueryState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

interface UseHubMutationState<T, TArgs extends unknown[] = unknown[]> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (...args: TArgs) => Promise<T | null>;
  reset: () => void;
}

// =============================================================================
// HOOK: useHubHealth
// =============================================================================

export function useHubHealth(pollInterval: number = 0): UseHubQueryState<HubHealth> {
  const [data, setData] = useState<HubHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const health = await hubApiClient.getHealth();
      setData(health);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();

    if (pollInterval > 0) {
      const interval = setInterval(fetchHealth, pollInterval);
      return () => clearInterval(interval);
    }
  }, [fetchHealth, pollInterval]);

  return { data, loading, error, refetch: fetchHealth };
}

// =============================================================================
// HOOK: useHubStats
// =============================================================================

export function useHubStats(pollInterval: number = 0): UseHubQueryState<HubStats> {
  const [data, setData] = useState<HubStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const stats = await hubApiClient.getStats();
      setData(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stats');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();

    if (pollInterval > 0) {
      const interval = setInterval(fetchStats, pollInterval);
      return () => clearInterval(interval);
    }
  }, [fetchStats, pollInterval]);

  return { data, loading, error, refetch: fetchStats };
}

// =============================================================================
// HOOK: useHubCacheStats
// =============================================================================

export function useHubCacheStats(): UseHubQueryState<CacheStats> {
  const [data, setData] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCacheStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const stats = await hubApiClient.getCacheStats();
      setData(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch cache stats');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCacheStats();
  }, [fetchCacheStats]);

  return { data, loading, error, refetch: fetchCacheStats };
}

// =============================================================================
// HOOK: useHubGraphStats
// =============================================================================

export function useHubGraphStats(): UseHubQueryState<GraphStats> {
  const [data, setData] = useState<GraphStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchGraphStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const stats = await hubApiClient.getGraphStats();
      setData(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch graph stats');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGraphStats();
  }, [fetchGraphStats]);

  return { data, loading, error, refetch: fetchGraphStats };
}

// =============================================================================
// HOOK: useSmartQuery
// =============================================================================

export function useSmartQuery(): UseHubMutationState<SmartQueryResult, [query: string, strategy?: SearchStrategy]> {
  const [data, setData] = useState<SmartQueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (query: string, strategy: SearchStrategy = 'auto') => {
    try {
      setLoading(true);
      setError(null);
      const result = await hubApiClient.askSmart(query, strategy);
      setData(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Query failed';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, execute, reset };
}

// =============================================================================
// HOOK: useHubAgent
// =============================================================================

type AgentType = 'program' | 'company' | 'contact' | 'strategy';

export function useHubAgent(agentType: AgentType): UseHubMutationState<AgentResponse, [query: string]> {
  const [data, setData] = useState<AgentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (query: string) => {
    try {
      setLoading(true);
      setError(null);

      let result: AgentResponse;
      switch (agentType) {
        case 'program':
          result = await hubApiClient.runProgramAgent(query);
          break;
        case 'company':
          result = await hubApiClient.runCompanyAgent(query);
          break;
        case 'contact':
          result = await hubApiClient.runContactAgent(query);
          break;
        case 'strategy':
          result = await hubApiClient.runStrategyAgent(query);
          break;
        default:
          throw new Error(`Unknown agent type: ${agentType}`);
      }

      setData(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Agent execution failed';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [agentType]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, execute, reset };
}

// =============================================================================
// HOOK: useProgramEcosystem
// =============================================================================

export function useProgramEcosystem(): UseHubMutationState<ProgramEcosystem, [programName: string]> {
  const [data, setData] = useState<ProgramEcosystem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (programName: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await hubApiClient.getProgramEcosystem(programName);
      setData(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch program ecosystem';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, execute, reset };
}

// =============================================================================
// HOOK: useContactNetwork
// =============================================================================

export function useContactNetwork(): UseHubMutationState<ContactNetwork, [contactName: string]> {
  const [data, setData] = useState<ContactNetwork | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (contactName: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await hubApiClient.getContactNetwork(contactName);
      setData(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch contact network';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, execute, reset };
}

// =============================================================================
// HOOK: useTeamingPath
// =============================================================================

export function useTeamingPath(): UseHubMutationState<TeamingPath, [from: string, to: string]> {
  const [data, setData] = useState<TeamingPath | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (from: string, to: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await hubApiClient.findTeamingPath(from, to);
      setData(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to find teaming path';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, execute, reset };
}

// =============================================================================
// HOOK: useMemorySearch
// =============================================================================

export function useMemorySearch(): UseHubMutationState<MemorySearchResult, [query: string, limit?: number]> {
  const [data, setData] = useState<MemorySearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (query: string, limit: number = 10) => {
    try {
      setLoading(true);
      setError(null);
      const result = await hubApiClient.searchMemory(query, limit);
      setData(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Memory search failed';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, execute, reset };
}

// =============================================================================
// HOOK: useEntityFacts
// =============================================================================

export function useEntityFacts(): UseHubMutationState<EntityFacts, [entityName: string]> {
  const [data, setData] = useState<EntityFacts | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (entityName: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await hubApiClient.getEntityFacts(entityName);
      setData(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch entity facts';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, execute, reset };
}

// =============================================================================
// HOOK: useBDInsights
// =============================================================================

export function useBDInsights(
  type?: 'pattern' | 'opportunity' | 'risk' | 'recommendation',
  limit: number = 20
): UseHubQueryState<BDInsight[]> {
  const [data, setData] = useState<BDInsight[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInsights = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const insights = await hubApiClient.getInsights(type, limit);
      setData(insights);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch insights');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [type, limit]);

  useEffect(() => {
    fetchInsights();
  }, [fetchInsights]);

  return { data, loading, error, refetch: fetchInsights };
}

// =============================================================================
// HOOK: useAgentTasks
// =============================================================================

export interface AgentTask {
  task_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  crew_type: string;
  created_at: string;
  completed_at: string | null;
  result?: unknown;
  error?: string | null;
}

export function useAgentTasks(pollInterval: number = 5000): UseHubQueryState<{ total: number; tasks: AgentTask[] }> {
  const [data, setData] = useState<{ total: number; tasks: AgentTask[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      setError(null);
      const result = await hubApiClient.getAgentTasks() as unknown as { total: number; tasks: AgentTask[] };
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agent tasks');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTasks();

    if (pollInterval > 0) {
      const interval = setInterval(fetchTasks, pollInterval);
      return () => clearInterval(interval);
    }
  }, [fetchTasks, pollInterval]);

  return { data, loading, error, refetch: fetchTasks };
}

// =============================================================================
// HOOK: useHubConnection
// =============================================================================

export function useHubConnection(): {
  isConnected: boolean;
  isChecking: boolean;
  checkConnection: () => Promise<boolean>;
} {
  const [isConnected, setIsConnected] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const mountedRef = useRef(true);

  const checkConnection = useCallback(async () => {
    setIsChecking(true);
    try {
      const connected = await hubApiClient.testConnection();
      if (mountedRef.current) {
        setIsConnected(connected);
      }
      return connected;
    } catch {
      if (mountedRef.current) {
        setIsConnected(false);
      }
      return false;
    } finally {
      if (mountedRef.current) {
        setIsChecking(false);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    checkConnection();
    return () => {
      mountedRef.current = false;
    };
  }, [checkConnection]);

  return { isConnected, isChecking, checkConnection };
}

export default {
  useHubHealth,
  useHubStats,
  useHubCacheStats,
  useHubGraphStats,
  useSmartQuery,
  useHubAgent,
  useAgentTasks,
  useProgramEcosystem,
  useContactNetwork,
  useTeamingPath,
  useMemorySearch,
  useEntityFacts,
  useBDInsights,
  useHubConnection,
};
