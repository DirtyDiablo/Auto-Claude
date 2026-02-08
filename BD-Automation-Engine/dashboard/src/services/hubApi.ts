/**
 * Hub API Client
 *
 * Client for the BD Intelligence Hub API (localhost:8100).
 * Provides access to all BD enhancements: Smart Query, Knowledge Graph,
 * BD Agents, Memory Context, and System Health.
 */

// =============================================================================
// TYPES
// =============================================================================

export interface HubApiConfig {
  baseUrl: string;
  timeout?: number;
}

export interface HubSearchResult {
  id: string;
  collection: string;
  score: number;
  content: string;
  metadata: Record<string, unknown>;
}

export interface HubStats {
  collections: {
    contacts: number;
    programs: number;
    documents: number;
    activities: number;
    jobs: number;
  };
  total_records: number;
  last_updated: string;
}

// Raw API response format
interface RawHubStats {
  qdrant: {
    contacts?: { vectors_count: number; points_count: number; status: string };
    programs?: { vectors_count: number; points_count: number; status: string };
    documents?: { vectors_count: number; points_count: number; status: string };
    activities?: { vectors_count: number; points_count: number; status: string };
    jobs?: { vectors_count: number; points_count: number; status: string };
  };
  memory?: { total_memories: number; by_type: Record<string, number>; backend: string };
  graph?: { working_dir: string; backend: string; files: number };
  cache?: { cached_queries: number; backend: string; threshold: number };
  timestamp: string;
}

interface RawSearchResponse {
  query: string;
  collection: string | null;
  results: Array<{
    id: string;
    score: number;
    payload: Record<string, unknown>;
    collection: string;
  }>;
  count: number;
  timestamp: string;
}

export interface HubHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  uptime: number;
  services: {
    qdrant: boolean;
    memory: boolean;
    graph: boolean;
    agents: boolean;
  };
}

export interface SmartQueryResult {
  answer: string;
  sources: Array<{
    collection: string;
    id: string;
    content: string;
    score: number;
  }>;
  strategy_used: string;
  confidence: number;
  query_analysis: {
    intent: string;
    entities: string[];
    suggested_strategy: string;
  };
}

export interface ProgramEcosystem {
  program: {
    name: string;
    acronym: string;
    agency: string;
    contract_value: string;
  };
  primes: Array<{
    name: string;
    role: string;
    relationship_strength: number;
  }>;
  subcontractors: Array<{
    name: string;
    role: string;
  }>;
  contacts: Array<{
    name: string;
    title: string;
    company: string;
    tier: number;
  }>;
  jobs: Array<{
    title: string;
    company: string;
    location: string;
  }>;
  graph_data: {
    nodes: Array<{
      id: string;
      label: string;
      type: string;
      size?: number;
    }>;
    edges: Array<{
      source: string;
      target: string;
      label?: string;
    }>;
  };
}

export interface ContactNetwork {
  contact: {
    name: string;
    title: string;
    company: string;
    tier: number;
  };
  employer: {
    name: string;
    type: string;
  };
  programs: Array<{
    name: string;
    role: string;
  }>;
  connections: Array<{
    name: string;
    relationship: string;
    strength: number;
  }>;
  graph_data: {
    nodes: Array<{
      id: string;
      label: string;
      type: string;
      size?: number;
    }>;
    edges: Array<{
      source: string;
      target: string;
      label?: string;
    }>;
  };
}

export interface TeamingPath {
  from_contractor: string;
  to_contractor: string;
  path: Array<{
    entity: string;
    type: string;
    relationship: string;
  }>;
  distance: number;
  strength: number;
}

export interface MemorySearchResult {
  results: Array<{
    id: string;
    content: string;
    entity_name: string;
    fact_type: string;
    created_at: string;
    confidence: number;
  }>;
  total: number;
}

export interface EntityFacts {
  entity_name: string;
  facts: Array<{
    id: string;
    content: string;
    fact_type: string;
    source: string;
    created_at: string;
    confidence: number;
  }>;
  summary: string;
}

export interface BDInsight {
  id: string;
  type: 'pattern' | 'opportunity' | 'risk' | 'recommendation';
  content: string;
  entities: string[];
  confidence: number;
  created_at: string;
}

export interface AgentResponse {
  agent: string;
  query: string;
  response: string;
  confidence: number;
  sources: string[];
  execution_time: number;
}

export interface WorkflowResult {
  workflow: string;
  status: 'completed' | 'failed' | 'partial';
  result: Record<string, unknown>;
  steps_completed: number;
  total_steps: number;
  execution_time: number;
}

export interface CacheStats {
  hit_rate: number;
  total_requests: number;
  cache_size: number;
  entries: number;
}

export interface GraphStats {
  total_nodes: number;
  total_edges: number;
  node_types: Record<string, number>;
  edge_types: Record<string, number>;
}

export type SearchStrategy = 'auto' | 'semantic' | 'keyword' | 'hybrid' | 'lightrag';

// =============================================================================
// HUB API CLIENT CLASS
// =============================================================================

export class HubApiClient {
  private baseUrl: string;
  private timeout: number;

  constructor(config: HubApiConfig = { baseUrl: import.meta.env.VITE_API_BASE || '' }) {
    this.baseUrl = config.baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.timeout = config.timeout || 30000;
  }

  // ---------------------------------------------------------------------------
  // PRIVATE HELPERS
  // ---------------------------------------------------------------------------

  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Hub API error (${response.status}): ${errorText}`);
      }

      return await response.json();
    } finally {
      clearTimeout(timeoutId);
    }
  }

  private buildQueryString(params: Record<string, string | number | boolean | undefined>): string {
    const filtered = Object.entries(params)
      .filter(([, value]) => value !== undefined)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
    return filtered.length > 0 ? `?${filtered.join('&')}` : '';
  }

  // ---------------------------------------------------------------------------
  // HEALTH & STATS
  // ---------------------------------------------------------------------------

  async getHealth(): Promise<HubHealth> {
    const raw = await this.fetch<{ status: string; timestamp: string }>('/health');
    // Transform raw health to expected format
    return {
      status: raw.status as 'healthy' | 'degraded' | 'unhealthy',
      version: '1.0.0',
      uptime: 0, // Not provided by API
      services: {
        qdrant: raw.status === 'healthy',
        memory: raw.status === 'healthy',
        graph: raw.status === 'healthy',
        agents: raw.status === 'healthy',
      },
    };
  }

  async getStats(): Promise<HubStats> {
    const raw = await this.fetch<RawHubStats>('/stats');
    // Transform raw stats to expected format
    return {
      collections: {
        contacts: raw.qdrant?.contacts?.points_count || 0,
        programs: raw.qdrant?.programs?.points_count || 0,
        documents: raw.qdrant?.documents?.points_count || 0,
        activities: raw.qdrant?.activities?.points_count || 0,
        jobs: raw.qdrant?.jobs?.points_count || 0,
      },
      total_records:
        (raw.qdrant?.contacts?.points_count || 0) +
        (raw.qdrant?.programs?.points_count || 0) +
        (raw.qdrant?.documents?.points_count || 0) +
        (raw.qdrant?.activities?.points_count || 0) +
        (raw.qdrant?.jobs?.points_count || 0),
      last_updated: raw.timestamp,
    };
  }

  async getCacheStats(): Promise<CacheStats> {
    const raw = await this.fetch<{
      cached_queries: number;
      backend: string;
      threshold: number;
    }>('/cache/stats');
    return {
      hit_rate: raw.threshold,
      total_requests: raw.cached_queries * 2, // Estimate
      cache_size: raw.cached_queries * 1024, // Estimate
      entries: raw.cached_queries,
    };
  }

  async testConnection(): Promise<boolean> {
    try {
      const health = await this.getHealth();
      return health.status === 'healthy' || health.status === 'degraded';
    } catch {
      return false;
    }
  }

  // ---------------------------------------------------------------------------
  // SEARCH
  // ---------------------------------------------------------------------------

  async search(
    query: string,
    collection?: string,
    limit: number = 10
  ): Promise<HubSearchResult[]> {
    const params = this.buildQueryString({ q: query, collection, limit });
    const raw = await this.fetch<RawSearchResponse>(`/search${params}`);
    // Transform raw results to expected format
    return raw.results.map((r) => ({
      id: r.id,
      collection: r.collection,
      score: r.score,
      content: (r.payload.name as string) || (r.payload.title as string) || '',
      metadata: r.payload,
    }));
  }

  async searchHybrid(
    query: string,
    collection?: string,
    limit: number = 10,
    alpha: number = 0.5
  ): Promise<HubSearchResult[]> {
    const params = this.buildQueryString({ q: query, collection, limit, alpha });
    return this.fetch<HubSearchResult[]>(`/search/hybrid${params}`);
  }

  // ---------------------------------------------------------------------------
  // RAG & SMART QUERY
  // ---------------------------------------------------------------------------

  async ask(query: string, collection?: string): Promise<{ answer: string; sources: HubSearchResult[]; confidence: number }> {
    const params = this.buildQueryString({ q: query, collection });
    const raw = await this.fetch<{
      answer: string;
      sources: Array<{ id: string; score: number; payload: Record<string, unknown>; collection: string }>;
      confidence: number;
    }>(`/ask${params}`);
    return {
      answer: raw.answer,
      sources: raw.sources.map((s) => ({
        id: s.id,
        collection: s.collection,
        score: s.score,
        content: (s.payload.name as string) || (s.payload.title as string) || '',
        metadata: s.payload,
      })),
      confidence: raw.confidence,
    };
  }

  async askSmart(
    query: string,
    strategy: SearchStrategy = 'auto'
  ): Promise<SmartQueryResult> {
    const params = this.buildQueryString({ q: query, strategy });
    const raw = await this.fetch<{
      answer: string;
      query_type: string;
      systems_used: string[];
      sources: Array<{ text?: string; score: number; source?: string; collection?: string; id?: string; payload?: Record<string, unknown> }>;
      cache_hit: boolean;
    }>(`/ask/smart${params}`);
    return {
      answer: raw.answer,
      sources: (raw.sources || []).map((s) => ({
        collection: s.collection || s.source || 'unknown',
        id: s.id || '',
        content: s.text || (s.payload?.name as string) || (s.payload?.title as string) || '',
        score: s.score || 0,
      })),
      strategy_used: raw.systems_used?.join(', ') || strategy,
      confidence: raw.cache_hit ? 1.0 : 0.7,
      query_analysis: {
        intent: raw.query_type || 'unknown',
        entities: [],
        suggested_strategy: strategy,
      },
    };
  }

  async analyzeQuery(query: string): Promise<{ intent: string; entities: string[]; suggested_strategy: string }> {
    const params = this.buildQueryString({ q: query });
    return this.fetch<{ intent: string; entities: string[]; suggested_strategy: string }>(`/rag/analyze${params}`);
  }

  async getRouterDecision(query: string): Promise<{ strategy: string; confidence: number; reasoning: string }> {
    const params = this.buildQueryString({ q: query });
    return this.fetch<{ strategy: string; confidence: number; reasoning: string }>(`/rag/router${params}`);
  }

  // ---------------------------------------------------------------------------
  // KNOWLEDGE GRAPH
  // ---------------------------------------------------------------------------

  async getProgramEcosystem(programName: string): Promise<ProgramEcosystem> {
    return this.fetch<ProgramEcosystem>(`/bdgraph/program/${encodeURIComponent(programName)}`);
  }

  async getContactNetwork(contactName: string): Promise<ContactNetwork> {
    return this.fetch<ContactNetwork>(`/bdgraph/contact/${encodeURIComponent(contactName)}`);
  }

  async findTeamingPath(fromContractor: string, toContractor: string): Promise<TeamingPath> {
    return this.fetch<TeamingPath>(
      `/bdgraph/teaming/${encodeURIComponent(fromContractor)}/${encodeURIComponent(toContractor)}`
    );
  }

  async queryGraph(query: string): Promise<{ nodes: unknown[]; edges: unknown[] }> {
    const params = this.buildQueryString({ q: query });
    return this.fetch<{ nodes: unknown[]; edges: unknown[] }>(`/bdgraph/query${params}`);
  }

  async getGraphStats(): Promise<GraphStats> {
    const raw = await this.fetch<{
      total_entities: number;
      entities_by_type: Record<string, number>;
      total_relationships: number;
      relationships_by_type: Record<string, number>;
      available: boolean;
    }>('/bdgraph/stats');
    return {
      total_nodes: raw.total_entities,
      total_edges: raw.total_relationships,
      node_types: raw.entities_by_type,
      edge_types: raw.relationships_by_type,
    };
  }

  // ---------------------------------------------------------------------------
  // MEMORY
  // ---------------------------------------------------------------------------

  async searchMemory(
    query: string,
    limit: number = 10
  ): Promise<MemorySearchResult> {
    const params = this.buildQueryString({ q: query, limit });
    return this.fetch<MemorySearchResult>(`/memory/search${params}`);
  }

  async getEntityFacts(entityName: string): Promise<EntityFacts> {
    return this.fetch<EntityFacts>(`/memory/entity/${encodeURIComponent(entityName)}`);
  }

  async getInsights(
    type?: 'pattern' | 'opportunity' | 'risk' | 'recommendation',
    limit: number = 20
  ): Promise<BDInsight[]> {
    const params = this.buildQueryString({ type, limit });
    return this.fetch<BDInsight[]>(`/memory/insights${params}`);
  }

  async getContactContext(contactName: string): Promise<{
    contact: { name: string; title: string; company: string };
    call_history: Array<{ date: string; notes: string; outcome: string }>;
    interactions: Array<{ type: string; date: string; summary: string }>;
    insights: string[];
  }> {
    return this.fetch(`/memory/contact/${encodeURIComponent(contactName)}`);
  }

  async getProgramContext(programName: string): Promise<{
    program: { name: string; agency: string; prime: string };
    intel_history: Array<{ date: string; type: string; content: string }>;
    patterns: string[];
    opportunities: string[];
  }> {
    return this.fetch(`/memory/program/${encodeURIComponent(programName)}`);
  }

  // ---------------------------------------------------------------------------
  // AGENTS
  // ---------------------------------------------------------------------------

  private normalizeAgentResponse(raw: Partial<AgentResponse>, query: string): AgentResponse {
    return {
      agent: raw.agent || 'Unknown Agent',
      query: raw.query || query,
      response: raw.response || '',
      confidence: raw.confidence ?? 0.5,
      sources: raw.sources || [],
      execution_time: raw.execution_time ?? 0,
    };
  }

  async runProgramAgent(query: string): Promise<AgentResponse> {
    const params = this.buildQueryString({ q: query });
    const raw = await this.fetch<Partial<AgentResponse>>(`/agent/program${params}`);
    return this.normalizeAgentResponse(raw, query);
  }

  async runCompanyAgent(query: string): Promise<AgentResponse> {
    const params = this.buildQueryString({ q: query });
    const raw = await this.fetch<Partial<AgentResponse>>(`/agent/company${params}`);
    return this.normalizeAgentResponse(raw, query);
  }

  async runContactAgent(query: string): Promise<AgentResponse> {
    const params = this.buildQueryString({ q: query });
    const raw = await this.fetch<Partial<AgentResponse>>(`/agent/contact${params}`);
    return this.normalizeAgentResponse(raw, query);
  }

  async runStrategyAgent(query: string): Promise<AgentResponse> {
    const params = this.buildQueryString({ q: query });
    const raw = await this.fetch<Partial<AgentResponse>>(`/agent/strategy${params}`);
    return this.normalizeAgentResponse(raw, query);
  }

  // ---------------------------------------------------------------------------
  // WORKFLOWS
  // ---------------------------------------------------------------------------

  async analyzeProgram(programName: string): Promise<WorkflowResult> {
    return this.fetch<WorkflowResult>('/agents/analyze-program', {
      method: 'POST',
      body: JSON.stringify({ program_name: programName }),
    });
  }

  async prepareOutreach(contactName: string, context?: string): Promise<WorkflowResult> {
    return this.fetch<WorkflowResult>('/agents/prepare-outreach', {
      method: 'POST',
      body: JSON.stringify({ contact_name: contactName, context }),
    });
  }

  async generateWeeklyIntel(): Promise<WorkflowResult> {
    return this.fetch<WorkflowResult>('/agents/weekly-intel', {
      method: 'POST',
    });
  }

  // ---------------------------------------------------------------------------
  // COLLECTION DATA (for DataAdapter)
  // ---------------------------------------------------------------------------

  async getJobs(limit: number = 1000): Promise<HubSearchResult[]> {
    return this.search('*', 'jobs', limit);
  }

  async getPrograms(limit: number = 1000): Promise<HubSearchResult[]> {
    return this.search('*', 'programs', limit);
  }

  async getContacts(limit: number = 10000): Promise<HubSearchResult[]> {
    return this.search('*', 'contacts', limit);
  }

  async getDocuments(limit: number = 1000): Promise<HubSearchResult[]> {
    return this.search('*', 'documents', limit);
  }

  async getActivities(limit: number = 1000): Promise<HubSearchResult[]> {
    return this.search('*', 'activities', limit);
  }

  // ---------------------------------------------------------------------------
  // QA & PIPELINE
  // ---------------------------------------------------------------------------

  async getQAStats(): Promise<{ total_items: number; pending: number; reviewed: number; timestamp: string }> {
    return this.fetch('/qa/stats');
  }

  async getQAReviewQueue(params?: {
    limit?: number;
    offset?: number;
    status?: 'pending' | 'reviewed';
  }): Promise<{ items: Array<Record<string, unknown>>; total: number; limit: number; offset: number }> {
    const qs = params
      ? '?' + Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => `${k}=${v}`).join('&')
      : '';
    return this.fetch(`/qa/review-queue${qs}`);
  }

  async resolveQAItem(
    itemId: string,
    action: 'approve' | 'reject' | 'fix',
    notes?: string,
  ): Promise<{ success: boolean; item: Record<string, unknown> }> {
    return this.fetch(`/qa/review-queue/${encodeURIComponent(itemId)}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ action, notes }),
    });
  }

  async getPipelineStatus(): Promise<{
    is_running: boolean;
    current_run: Record<string, unknown> | null;
    last_run: Record<string, unknown> | null;
    history: Array<Record<string, unknown>>;
    stats: { total_runs: number; success_rate: number; avg_duration: number };
  }> {
    return this.fetch('/pipeline/status');
  }

  async triggerPipeline(params?: {
    input_file?: string;
    test_mode?: boolean;
    hot_leads_only?: boolean;
  }): Promise<{ success: boolean; run_id: string; status: string }> {
    return this.fetch('/pipeline/trigger', {
      method: 'POST',
      body: JSON.stringify(params || {}),
    });
  }

  async getAlerts(limit: number = 20): Promise<{ alerts: Array<Record<string, unknown>>; count: number }> {
    return this.fetch(`/alerts?limit=${limit}`);
  }

  async getAgentTasks(): Promise<{ total: number; tasks: Array<Record<string, unknown>> }> {
    return this.fetch('/agents/tasks');
  }

  async getAgentStatus(taskId: string): Promise<Record<string, unknown>> {
    return this.fetch(`/agents/status/${encodeURIComponent(taskId)}`);
  }

  // ---------------------------------------------------------------------------
  // CONFIGURATION
  // ---------------------------------------------------------------------------

  setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/$/, '');
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  setTimeout(timeout: number): void {
    this.timeout = timeout;
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

// Default Hub API URL - empty string uses vite proxy in dev, direct URL in production
const DEFAULT_HUB_URL = import.meta.env.VITE_API_BASE || '';

// Get URL from localStorage or use default
function getStoredHubUrl(): string {
  if (typeof window !== 'undefined' && window.localStorage) {
    return localStorage.getItem('hub_api_url') || DEFAULT_HUB_URL;
  }
  return DEFAULT_HUB_URL;
}

// Create singleton instance
export const hubApiClient = new HubApiClient({ baseUrl: getStoredHubUrl() });

// Helper to update and persist Hub URL
export function setHubApiUrl(url: string): void {
  hubApiClient.setBaseUrl(url);
  if (typeof window !== 'undefined' && window.localStorage) {
    localStorage.setItem('hub_api_url', url);
  }
}

// Helper to get current Hub URL
export function getHubApiUrl(): string {
  return hubApiClient.getBaseUrl();
}

export default hubApiClient;
