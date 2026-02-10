import { useState, useCallback, useEffect } from 'react';
import { Search, Zap, GitBranch, Layers, BarChart3, Clock, ChevronDown } from 'lucide-react';

interface SearchResult {
  id: string;
  content: string;
  score: number;
  source: string;
  channel_scores: Record<string, number>;
  metadata: Record<string, unknown>;
}

interface SearchResponse {
  results: SearchResult[];
  mode_used: string;
  search_latency_ms: number;
  total_candidates: number;
  channels_used: string[];
  query_expanded?: string;
}

interface BenchmarkRow {
  mode: string;
  'P@5': number;
  'P@10': number;
  'R@10': number;
  MRR: number;
  'NDCG@10': number;
  'Latency (ms)': number;
  'Queries with results': number;
}

const MODES = [
  { value: 'auto', label: 'Auto', icon: Zap, desc: 'Automatically routes to best channel' },
  { value: 'hybrid', label: 'Hybrid', icon: Layers, desc: 'Dense + BM25 Sparse + RRF' },
  { value: 'graph', label: 'Graph', icon: GitBranch, desc: 'Neo4j graph-first' },
  { value: 'graphrag', label: 'GraphRAG', icon: GitBranch, desc: 'Dense + Sparse + Graph' },
  { value: 'vector', label: 'Vector', icon: Search, desc: 'Dense vector only (legacy)' },
  { value: 'keyword', label: 'Keyword', icon: Search, desc: 'BM25 keyword only' },
];

const MODE_COLORS: Record<string, string> = {
  auto: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  hybrid: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  graph: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  graphrag: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
  vector: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300',
  keyword: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
};

export function SearchLab() {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('auto');
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<Array<{ query: string; mode: string; latency: number; count: number; time: string }>>([]);
  const [benchmarkResults, setBenchmarkResults] = useState<BenchmarkRow[] | null>(null);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [tab, setTab] = useState<'search' | 'benchmark' | 'history'>('search');
  const [compareMode, setCompareMode] = useState(false);
  const [compareModes, setCompareModes] = useState<string[]>(['hybrid', 'graphrag']);
  const [compareResults, setCompareResults] = useState<Record<string, SearchResponse>>({});

  const doSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const resp = await fetch('/search/v2', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, mode, top_k: 10, use_rerank: true, expand_query: true }),
      });
      const data: SearchResponse = await resp.json();
      setResults(data);
      setHistory(prev => [{
        query,
        mode: data.mode_used,
        latency: data.search_latency_ms,
        count: data.results.length,
        time: new Date().toLocaleTimeString(),
      }, ...prev].slice(0, 20));
    } catch {
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, [query, mode]);

  const doCompare = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    const res: Record<string, SearchResponse> = {};
    for (const m of compareModes) {
      try {
        const resp = await fetch('/search/v2', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, mode: m, top_k: 10, use_rerank: true }),
        });
        res[m] = await resp.json();
      } catch { /* skip */ }
    }
    setCompareResults(res);
    setLoading(false);
  }, [query, compareModes]);

  const runBenchmark = useCallback(async () => {
    setBenchmarkLoading(true);
    try {
      const resp = await fetch('/search/v2/benchmark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modes: ['vector', 'hybrid', 'graphrag'] }),
      });
      const data = await resp.json();
      setBenchmarkResults(data.comparison || []);
    } catch {
      setBenchmarkResults(null);
    } finally {
      setBenchmarkLoading(false);
    }
  }, []);

  // Load latest benchmark on mount
  useEffect(() => {
    fetch('/search/v2/benchmark/latest')
      .then(r => r.json())
      .then(data => {
        if (data.results) {
          const rows: BenchmarkRow[] = Object.entries(data.results).map(([m, r]: [string, any]) => ({
            mode: m,
            'P@5': r.precision_at_5,
            'P@10': r.precision_at_10,
            'R@10': r.recall_at_10,
            MRR: r.mrr,
            'NDCG@10': r.ndcg_at_10,
            'Latency (ms)': r.mean_latency_ms,
            'Queries with results': r.queries_with_results,
          }));
          setBenchmarkResults(rows);
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Search Lab</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Hybrid GraphRAG search testing and benchmarking</p>
        </div>
        <div className="flex gap-2">
          {(['search', 'benchmark', 'history'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                tab === t ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {tab === 'search' && (
        <div className="space-y-4">
          {/* Search bar */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  value={query} onChange={e => setQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && (compareMode ? doCompare() : doSearch())}
                  placeholder="Search contacts, programs, companies, jobs..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
              <select value={mode} onChange={e => setMode(e.target.value)}
                className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-sm">
                {MODES.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
              </select>
              <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <input type="checkbox" checked={compareMode} onChange={e => setCompareMode(e.target.checked)}
                  className="rounded border-gray-300" />
                Compare
              </label>
              <button onClick={compareMode ? doCompare : doSearch} disabled={loading || !query.trim()}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>
            {compareMode && (
              <div className="mt-2 flex gap-2 flex-wrap">
                {MODES.filter(m => m.value !== 'auto').map(m => (
                  <label key={m.value} className="flex items-center gap-1 text-xs">
                    <input type="checkbox" checked={compareModes.includes(m.value)}
                      onChange={e => setCompareModes(prev => e.target.checked ? [...prev, m.value] : prev.filter(x => x !== m.value))}
                      className="rounded border-gray-300" />
                    {m.label}
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Single results */}
          {!compareMode && results && (
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${MODE_COLORS[results.mode_used] || MODE_COLORS.auto}`}>
                  {results.mode_used}
                </span>
                <span>{results.results.length} results</span>
                <span>{results.total_candidates} candidates</span>
                <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{results.search_latency_ms}ms</span>
                {results.query_expanded && results.query_expanded !== query && (
                  <span className="text-xs text-indigo-600 dark:text-indigo-400">Expanded: {results.query_expanded.slice(0, 80)}</span>
                )}
              </div>
              {results.results.map((r, i) => (
                <div key={r.id + i} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 dark:text-gray-100 line-clamp-3">{r.content || '(no content)'}</p>
                      <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
                        <span className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700">{r.source}</span>
                        {Object.entries(r.channel_scores).map(([ch, sc]) => (
                          <span key={ch} className="px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300">
                            {ch}: {sc.toFixed(3)}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-lg font-semibold text-indigo-600 dark:text-indigo-400">{r.score.toFixed(3)}</div>
                      <div className="w-16 h-1.5 bg-gray-200 dark:bg-gray-700 rounded mt-1">
                        <div className="h-full bg-indigo-600 rounded" style={{ width: `${Math.min(r.score * 100, 100)}%` }} />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Compare results */}
          {compareMode && Object.keys(compareResults).length > 0 && (
            <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${Object.keys(compareResults).length}, 1fr)` }}>
              {Object.entries(compareResults).map(([m, resp]) => (
                <div key={m} className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <span className={`px-2 py-0.5 rounded text-xs ${MODE_COLORS[m] || MODE_COLORS.auto}`}>{m}</span>
                    <span className="text-gray-500">{resp.search_latency_ms}ms</span>
                  </div>
                  {resp.results.slice(0, 5).map((r, i) => (
                    <div key={r.id + i} className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-2 text-xs">
                      <p className="line-clamp-2 text-gray-700 dark:text-gray-300">{r.content || '(no content)'}</p>
                      <span className="text-indigo-600 font-medium">{r.score.toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'benchmark' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <button onClick={runBenchmark} disabled={benchmarkLoading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
              {benchmarkLoading ? 'Running 50 queries...' : 'Run Benchmark'}
            </button>
            <p className="text-sm text-gray-500">50 queries across 5 categories: entity, relationship, semantic, keyword, multihop</p>
          </div>
          {benchmarkResults && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    {['Mode', 'P@5', 'P@10', 'R@10', 'MRR', 'NDCG@10', 'Latency', 'Results'].map(h => (
                      <th key={h} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {benchmarkResults.map(row => (
                    <tr key={row.mode} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750">
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${MODE_COLORS[row.mode] || ''}`}>{row.mode}</span>
                      </td>
                      <td className="px-4 py-3 font-mono">{row['P@5'].toFixed(3)}</td>
                      <td className="px-4 py-3 font-mono">{row['P@10'].toFixed(3)}</td>
                      <td className="px-4 py-3 font-mono">{row['R@10'].toFixed(3)}</td>
                      <td className="px-4 py-3 font-mono font-semibold text-indigo-600 dark:text-indigo-400">{row.MRR.toFixed(3)}</td>
                      <td className="px-4 py-3 font-mono">{row['NDCG@10'].toFixed(3)}</td>
                      <td className="px-4 py-3 text-gray-500">{row['Latency (ms)']}ms</td>
                      <td className="px-4 py-3">{row['Queries with results']}/50</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'history' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                {['Time', 'Query', 'Mode', 'Results', 'Latency'].map(h => (
                  <th key={h} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {history.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No search history yet</td></tr>
              )}
              {history.map((h, i) => (
                <tr key={i} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 cursor-pointer"
                  onClick={() => { setQuery(h.query); setTab('search'); }}>
                  <td className="px-4 py-3 text-gray-500 text-xs">{h.time}</td>
                  <td className="px-4 py-3 truncate max-w-xs">{h.query}</td>
                  <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${MODE_COLORS[h.mode] || ''}`}>{h.mode}</span></td>
                  <td className="px-4 py-3">{h.count}</td>
                  <td className="px-4 py-3 text-gray-500">{h.latency}ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
