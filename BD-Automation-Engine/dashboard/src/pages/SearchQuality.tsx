/**
 * Search Quality Dashboard — Domain embedding benchmarks and query expansion.
 *
 * Sections:
 *  1. Status card (adapter trained, corpus size, benchmark scores)
 *  2. Benchmark results comparison table
 *  3. Query expansion test (type query, see expanded version)
 *  4. Corpus stats card
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Search, BarChart3, Loader2, RefreshCw, Microscope,
  Sparkles, Database, Zap, ArrowRight,
} from 'lucide-react'

// ── Types ──────────────────────────────────────────────

interface EmbeddingStatus {
  torch_available: boolean
  adapter_trained: boolean
  training_pairs: number
  trained_at: string
  final_loss: number
  corpus: {
    total_documents: number
    total_tokens_approx: number
    category_distribution: Record<string, number>
  } | null
  benchmark: {
    methods: Array<{
      method: string
      precision_at_5: number
      recall_at_10: number
      mrr: number
      ndcg_at_10: number
    }>
    best_method: string
    improvement_pct: number
  } | null
}

interface ExpandResult {
  original: string
  expanded: string
  acronyms_resolved: string[]
  synonyms_added: string[]
  expansion_count: number
}

// ── Component ──────────────────────────────────────────

export function SearchQuality() {
  const [status, setStatus] = useState<EmbeddingStatus | null>(null)
  const [loading, setLoading] = useState(false)

  // Query expansion test
  const [testQuery, setTestQuery] = useState('')
  const [expandResult, setExpandResult] = useState<ExpandResult | null>(null)
  const [expanding, setExpanding] = useState(false)

  // Actions
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const fetchStatus = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch('/embeddings/status')
      if (res.ok) setStatus(await res.json())
    } catch { /* ignore */ }
    setLoading(false)
  }, [])

  useEffect(() => { fetchStatus() }, [fetchStatus])

  const handleExpand = useCallback(async () => {
    if (!testQuery.trim()) return
    setExpanding(true)
    try {
      const res = await fetch('/embeddings/expand-query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: testQuery }),
      })
      if (res.ok) setExpandResult(await res.json())
    } catch { /* ignore */ }
    setExpanding(false)
  }, [testQuery])

  const handleAction = useCallback(async (action: string) => {
    setActionLoading(action)
    try {
      const endpoints: Record<string, { url: string; method: string }> = {
        build_corpus: { url: '/embeddings/build-corpus', method: 'POST' },
        run_benchmark: { url: '/embeddings/benchmark', method: 'POST' },
      }
      const ep = endpoints[action]
      if (ep) {
        await fetch(ep.url, { method: ep.method })
        await fetchStatus()
      }
    } catch { /* ignore */ }
    setActionLoading(null)
  }, [fetchStatus])

  const metricBar = (value: number) => (
    <div className="w-24 bg-slate-200 dark:bg-slate-700 rounded-full h-2">
      <div
        className="bg-gradient-to-r from-blue-500 to-cyan-400 h-2 rounded-full transition-all"
        style={{ width: `${Math.round(value * 100)}%` }}
      />
    </div>
  )

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Microscope className="h-5 w-5 text-purple-500" />
              Search Quality
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Domain embeddings, query expansion, and retrieval benchmarks
            </p>
          </div>
          <button
            onClick={fetchStatus}
            disabled={loading}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Corpus */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Database className="h-4 w-4 text-blue-500" />
              <span className="text-xs font-semibold text-slate-500 uppercase">Domain Corpus</span>
            </div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {status?.corpus?.total_documents?.toLocaleString() || 0}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              ~{(status?.corpus?.total_tokens_approx || 0).toLocaleString()} tokens
            </div>
            {status?.corpus?.category_distribution && (
              <div className="mt-3 space-y-1">
                {Object.entries(status.corpus.category_distribution).slice(0, 5).map(([cat, count]) => (
                  <div key={cat} className="flex justify-between text-xs">
                    <span className="text-slate-500">{cat}</span>
                    <span className="text-slate-700 dark:text-slate-300 font-mono">{count}</span>
                  </div>
                ))}
              </div>
            )}
            <button
              onClick={() => handleAction('build_corpus')}
              disabled={actionLoading === 'build_corpus'}
              className="mt-3 w-full px-3 py-1.5 text-xs font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300 rounded-lg hover:bg-blue-100 disabled:opacity-50"
            >
              {actionLoading === 'build_corpus' ? (
                <span className="flex items-center justify-center gap-1"><Loader2 className="h-3 w-3 animate-spin" /> Building...</span>
              ) : 'Build Corpus'}
            </button>
          </div>

          {/* Adapter */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="h-4 w-4 text-amber-500" />
              <span className="text-xs font-semibold text-slate-500 uppercase">Domain Adapter</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`inline-flex h-2.5 w-2.5 rounded-full ${status?.adapter_trained ? 'bg-emerald-500' : 'bg-slate-400'}`} />
              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                {status?.adapter_trained ? 'Trained' : 'Not trained'}
              </span>
            </div>
            {status?.adapter_trained && (
              <div className="mt-2 space-y-1 text-xs text-slate-500">
                <div>Pairs: {status.training_pairs?.toLocaleString()}</div>
                <div>Loss: {status.final_loss?.toFixed(4)}</div>
                <div>PyTorch: {status.torch_available ? 'Available' : 'Not installed'}</div>
              </div>
            )}
            {!status?.adapter_trained && (
              <div className="mt-2 text-xs text-slate-400">
                Build corpus first, then train the adapter to improve domain search.
              </div>
            )}
          </div>

          {/* Benchmark */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 className="h-4 w-4 text-green-500" />
              <span className="text-xs font-semibold text-slate-500 uppercase">Benchmark</span>
            </div>
            {status?.benchmark?.methods?.length ? (
              <div className="space-y-1 text-xs">
                <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Best: {status.benchmark.best_method}
                </div>
                {status.benchmark.improvement_pct > 0 && (
                  <div className="text-emerald-600 font-medium">
                    +{status.benchmark.improvement_pct}% improvement
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs text-slate-400">No benchmark data yet.</div>
            )}
            <button
              onClick={() => handleAction('run_benchmark')}
              disabled={actionLoading === 'run_benchmark'}
              className="mt-3 w-full px-3 py-1.5 text-xs font-medium bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-300 rounded-lg hover:bg-green-100 disabled:opacity-50"
            >
              {actionLoading === 'run_benchmark' ? (
                <span className="flex items-center justify-center gap-1"><Loader2 className="h-3 w-3 animate-spin" /> Running...</span>
              ) : 'Run Benchmark'}
            </button>
          </div>
        </div>

        {/* Benchmark Results Table */}
        {status?.benchmark?.methods?.length ? (
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Method Comparison</h3>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700 text-left text-xs text-slate-500 uppercase">
                  <th className="px-4 py-3">Method</th>
                  <th className="px-4 py-3">P@5</th>
                  <th className="px-4 py-3">R@10</th>
                  <th className="px-4 py-3">MRR</th>
                  <th className="px-4 py-3">NDCG@10</th>
                </tr>
              </thead>
              <tbody>
                {status.benchmark.methods.map((m) => (
                  <tr
                    key={m.method}
                    className={`border-b border-slate-100 dark:border-slate-700/50 ${
                      m.method === status.benchmark?.best_method
                        ? 'bg-emerald-50 dark:bg-emerald-900/20'
                        : ''
                    }`}
                  >
                    <td className="px-4 py-2.5 font-medium text-slate-900 dark:text-white">
                      {m.method.replace(/_/g, ' ')}
                      {m.method === status.benchmark?.best_method && (
                        <span className="ml-2 px-1.5 py-0.5 rounded text-[10px] bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
                          best
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs">{m.precision_at_5.toFixed(3)}</span>
                        {metricBar(m.precision_at_5)}
                      </div>
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs">{m.recall_at_10.toFixed(3)}</span>
                        {metricBar(m.recall_at_10)}
                      </div>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">{m.mrr.toFixed(3)}</td>
                    <td className="px-4 py-2.5 font-mono text-xs">{m.ndcg_at_10.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {/* Query Expansion Test */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-1.5">
            <Zap className="h-4 w-4 text-amber-500" />
            Query Expansion Test
          </h3>
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleExpand()}
              placeholder="Type a query with acronyms... e.g. 'DCGS network engineer TS/SCI'"
              className="flex-1 px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <button
              onClick={handleExpand}
              disabled={expanding || !testQuery.trim()}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50 flex items-center gap-1.5"
            >
              {expanding ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Expand
            </button>
          </div>

          {expandResult && (
            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <span className="text-xs text-slate-500 w-16 flex-shrink-0 pt-0.5">Original:</span>
                <span className="text-sm text-slate-700 dark:text-slate-300">{expandResult.original}</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-xs text-slate-500 w-16 flex-shrink-0 pt-0.5">Expanded:</span>
                <span className="text-sm text-slate-900 dark:text-white font-medium">{expandResult.expanded}</span>
              </div>
              {expandResult.acronyms_resolved.length > 0 && (
                <div className="flex items-start gap-2">
                  <span className="text-xs text-slate-500 w-16 flex-shrink-0 pt-0.5">Acronyms:</span>
                  <div className="flex flex-wrap gap-1">
                    {expandResult.acronyms_resolved.map((a, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs">
                        {a}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {expandResult.synonyms_added.length > 0 && (
                <div className="flex items-start gap-2">
                  <span className="text-xs text-slate-500 w-16 flex-shrink-0 pt-0.5">Synonyms:</span>
                  <div className="flex flex-wrap gap-1">
                    {expandResult.synonyms_added.map((s, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 text-xs">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
