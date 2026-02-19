/**
 * Graph Analytics Dashboard - Influence scoring, community detection, Smart Query, Data Quality.
 *
 * Tabs:
 *  1. Influence Leaderboard — PageRank, betweenness, eigenvector composite scores
 *  2. Communities — Louvain-detected clusters with key entities
 *  3. Hidden Gems — High-centrality but low-tier contacts
 *  4. Smart Query — Intelligent Q&A with query_type + systems_used badges
 *  5. Data Quality — Quality score distribution from Intelligent DB Enhancement
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Crown, Loader2, Sparkles,
  BarChart3, Gem,
  CircleDot, Layers, RefreshCw, ShieldCheck, Brain,
  Zap, Database,
} from 'lucide-react'
import { useSmartQuery, useQualityStats } from '../hooks/useHubApi'

// ── Types ──────────────────────────────────────────────────

interface InfluenceEntry {
  entity_id: string
  name: string
  type: string
  pagerank: number
  betweenness: number
  eigenvector: number
  degree: number
  composite: number
  rank: number
  is_hidden_gem: boolean
  properties: Record<string, unknown>
}

interface CommunityEntry {
  id: number
  label: string
  size: number
  dominant_type: string
  type_distribution: Record<string, number>
  key_entities: string[]
  density: number
}

interface CommunitySummary {
  total_communities: number
  total_entities: number
  modularity: number
  communities: CommunityEntry[]
}

interface HiddenGem {
  entity_id: string
  name: string
  type: string
  composite: number
  pagerank: number
  betweenness: number
  degree: number
  tier: string
  company: string
  title: string
}

type TabKey = 'leaderboard' | 'communities' | 'gems' | 'smart' | 'quality'

// ── Component ──────────────────────────────────────────────

export function GraphAnalytics() {
  const [tab, setTab] = useState<TabKey>('leaderboard')
  const [loading, setLoading] = useState(false)

  // Leaderboard state
  const [leaderboard, setLeaderboard] = useState<InfluenceEntry[]>([])
  const [typeFilter, setTypeFilter] = useState<string>('')

  // Communities state
  const [commSummary, setCommSummary] = useState<CommunitySummary | null>(null)

  // Hidden gems state
  const [gems, setGems] = useState<HiddenGem[]>([])

  // Smart Query state
  const [smartInput, setSmartInput] = useState('')
  const smartQuery = useSmartQuery()

  // Data Quality state
  const qualityStats = useQualityStats()

  // ── Data fetching ────────────────────────────────────

  const fetchLeaderboard = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ limit: '30' })
      if (typeFilter) params.set('entity_type', typeFilter)
      const res = await fetch(`/graph/influence/leaderboard?${params}`)
      if (res.ok) {
        const data = await res.json()
        setLeaderboard(data.leaderboard || [])
      }
    } catch { /* ignore */ }
    setLoading(false)
  }, [typeFilter])

  const fetchCommunities = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch('/graph/communities/summary')
      if (res.ok) {
        const data = await res.json()
        setCommSummary(data)
      }
    } catch { /* ignore */ }
    setLoading(false)
  }, [])

  const fetchGems = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch('/graph/influence/hidden-gems?limit=25')
      if (res.ok) {
        const data = await res.json()
        setGems(data.hidden_gems || [])
      }
    } catch { /* ignore */ }
    setLoading(false)
  }, [])

  const handleSmartQuery = useCallback(async () => {
    if (!smartInput.trim()) return
    await smartQuery.execute(smartInput)
  }, [smartInput, smartQuery])

  // Auto-fetch on tab switch
  useEffect(() => {
    if (tab === 'leaderboard') fetchLeaderboard()
    else if (tab === 'communities') fetchCommunities()
    else if (tab === 'gems') fetchGems()
  }, [tab, fetchLeaderboard, fetchCommunities, fetchGems])

  // ── Helpers ──────────────────────────────────────────

  const typeColor = (t: string) => {
    const map: Record<string, string> = {
      Contact: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
      Contractor: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
      Program: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
      Job: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
      Location: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
    }
    return map[t] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
  }

  const scoreBar = (value: number) => (
    <div className="w-20 bg-slate-200 dark:bg-slate-700 rounded-full h-2">
      <div
        className="bg-gradient-to-r from-blue-500 to-cyan-400 h-2 rounded-full transition-all"
        style={{ width: `${Math.round(value * 100)}%` }}
      />
    </div>
  )

  // ── Tabs ─────────────────────────────────────────────

  const SMART_QUERY_PROMPTS = [
    'Who are the top contacts at Leidos on DCGS programs?',
    'Which contractors compete on ISR programs?',
    'What programs does Northrop Grumman prime?',
    'Find Tier 1 contacts working on Cyber programs',
  ]

  const getQualityBarColor = (range: string) => {
    if (range.startsWith('80')) return 'from-green-500 to-emerald-400'
    if (range.startsWith('60')) return 'from-lime-500 to-green-400'
    if (range.startsWith('40')) return 'from-amber-500 to-yellow-400'
    if (range.startsWith('20')) return 'from-orange-500 to-amber-400'
    return 'from-red-500 to-orange-400'
  }

  const tabs: { key: TabKey; label: string; icon: typeof Crown }[] = [
    { key: 'leaderboard', label: 'Influence', icon: Crown },
    { key: 'communities', label: 'Communities', icon: Layers },
    { key: 'gems', label: 'Hidden Gems', icon: Gem },
    { key: 'smart', label: 'Smart Query', icon: Brain },
    { key: 'quality', label: 'Data Quality', icon: ShieldCheck },
  ]

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-500" />
              Graph Analytics
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              PageRank influence, community clusters, Smart Query, and Data Quality
            </p>
          </div>
          {tab !== 'smart' && tab !== 'quality' && (
            <button
              onClick={() => {
                if (tab === 'leaderboard') fetchLeaderboard()
                else if (tab === 'communities') fetchCommunities()
                else if (tab === 'gems') fetchGems()
              }}
              disabled={loading}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          )}
        </div>

        {/* Tab bar */}
        <div className="flex gap-1 mt-3">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                tab === t.key
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                  : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700/50'
              }`}
            >
              <t.icon className="h-3.5 w-3.5" />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6 space-y-4">
        {/* ── LEADERBOARD ────────────────────── */}
        {tab === 'leaderboard' && (
          <>
            {/* Filter */}
            <div className="flex gap-2 items-center">
              <span className="text-sm text-slate-500">Filter:</span>
              {['', 'Contact', 'Contractor', 'Program'].map((t) => (
                <button
                  key={t}
                  onClick={() => setTypeFilter(t)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    typeFilter === t
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
                  }`}
                >
                  {t || 'All'}
                </button>
              ))}
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                <span className="ml-2 text-sm text-slate-500">Computing influence scores...</span>
              </div>
            ) : (
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-700 text-left text-xs text-slate-500 uppercase">
                      <th className="px-4 py-3 w-12">#</th>
                      <th className="px-4 py-3">Entity</th>
                      <th className="px-4 py-3">Type</th>
                      <th className="px-4 py-3">Composite</th>
                      <th className="px-4 py-3">PageRank</th>
                      <th className="px-4 py-3">Betweenness</th>
                      <th className="px-4 py-3">Eigenvector</th>
                      <th className="px-4 py-3 text-center">Degree</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leaderboard.map((entry, i) => (
                      <tr
                        key={entry.entity_id}
                        className="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-700/30"
                      >
                        <td className="px-4 py-2.5 font-mono text-slate-400">
                          {i < 3 ? (
                            <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                              i === 0 ? 'bg-yellow-100 text-yellow-700' :
                              i === 1 ? 'bg-slate-100 text-slate-600' :
                              'bg-orange-100 text-orange-600'
                            }`}>
                              {i + 1}
                            </span>
                          ) : (
                            i + 1
                          )}
                        </td>
                        <td className="px-4 py-2.5 font-medium text-slate-900 dark:text-white">
                          <div className="flex items-center gap-1.5">
                            {entry.name}
                            {entry.is_hidden_gem && <Gem className="h-3.5 w-3.5 text-amber-500" />}
                          </div>
                        </td>
                        <td className="px-4 py-2.5">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${typeColor(entry.type)}`}>
                            {entry.type}
                          </span>
                        </td>
                        <td className="px-4 py-2.5">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs">{entry.composite.toFixed(3)}</span>
                            {scoreBar(entry.composite)}
                          </div>
                        </td>
                        <td className="px-4 py-2.5 font-mono text-xs">{entry.pagerank.toFixed(3)}</td>
                        <td className="px-4 py-2.5 font-mono text-xs">{entry.betweenness.toFixed(3)}</td>
                        <td className="px-4 py-2.5 font-mono text-xs">{entry.eigenvector.toFixed(3)}</td>
                        <td className="px-4 py-2.5 text-center font-mono text-xs">{entry.degree}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {leaderboard.length === 0 && (
                  <div className="px-4 py-8 text-center text-slate-500">
                    No influence data yet. Populate the knowledge graph first.
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* ── COMMUNITIES ────────────────────── */}
        {tab === 'communities' && (
          <>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                <span className="ml-2 text-sm text-slate-500">Detecting communities...</span>
              </div>
            ) : commSummary ? (
              <>
                {/* Summary cards */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                    <div className="text-xs text-slate-500 uppercase">Communities</div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                      {commSummary.total_communities}
                    </div>
                  </div>
                  <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                    <div className="text-xs text-slate-500 uppercase">Total Entities</div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                      {commSummary.total_entities.toLocaleString()}
                    </div>
                  </div>
                  <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                    <div className="text-xs text-slate-500 uppercase">Modularity</div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                      {commSummary.modularity.toFixed(3)}
                    </div>
                  </div>
                </div>

                {/* Community list */}
                <div className="space-y-3">
                  {commSummary.communities.map((c) => (
                    <div
                      key={c.id}
                      className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <CircleDot className="h-4 w-4 text-blue-500" />
                          <span className="font-semibold text-slate-900 dark:text-white text-sm">
                            {c.label}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-slate-500">
                          <span>{c.size} entities</span>
                          <span>density: {c.density.toFixed(3)}</span>
                        </div>
                      </div>

                      {/* Type distribution */}
                      <div className="flex gap-2 mb-2">
                        {Object.entries(c.type_distribution).map(([type, count]) => (
                          <span
                            key={type}
                            className={`px-2 py-0.5 rounded text-xs font-medium ${typeColor(type)}`}
                          >
                            {type}: {count}
                          </span>
                        ))}
                      </div>

                      {/* Key entities */}
                      {c.key_entities.length > 0 && (
                        <div className="text-xs text-slate-500">
                          <span className="font-medium">Key members:</span>{' '}
                          {c.key_entities.join(', ')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-slate-500">
                No community data available. Populate the knowledge graph first.
              </div>
            )}
          </>
        )}

        {/* ── HIDDEN GEMS ────────────────────── */}
        {tab === 'gems' && (
          <>
            <p className="text-sm text-slate-500">
              Contacts with high graph centrality but low official tier — potentially undervalued relationships.
            </p>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
              </div>
            ) : gems.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {gems.map((g) => (
                  <div
                    key={g.entity_id}
                    className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Gem className="h-4 w-4 text-amber-500" />
                      <span className="font-semibold text-slate-900 dark:text-white text-sm">
                        {g.name}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 space-y-1">
                      {g.title && <div>{g.title}</div>}
                      {g.company && <div className="text-slate-400">{g.company}</div>}
                      <div className="flex gap-3 mt-2">
                        <span>Tier: <strong>{g.tier || '?'}</strong></span>
                        <span>Composite: <strong>{g.composite.toFixed(3)}</strong></span>
                        <span>Degree: <strong>{g.degree}</strong></span>
                      </div>
                      <div className="flex gap-3">
                        <span>PageRank: {g.pagerank.toFixed(3)}</span>
                        <span>Betweenness: {g.betweenness.toFixed(3)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500">
                No hidden gems detected. This usually means there are no high-tier contacts with low centrality mismatch.
              </div>
            )}
          </>
        )}

        {/* ── SMART QUERY ──────────────────────── */}
        {tab === 'smart' && (
          <>
            {/* Query input */}
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={smartInput}
                  onChange={(e) => setSmartInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSmartQuery()}
                  placeholder="Ask anything about programs, contacts, contractors..."
                  className="flex-1 px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleSmartQuery}
                  disabled={smartQuery.loading || !smartInput.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5"
                >
                  {smartQuery.loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Brain className="h-4 w-4" />}
                  Ask
                </button>
              </div>
              <p className="text-xs text-slate-400 mt-2">
                Smart Query automatically selects the best search strategy (vector, graph, SQL, or hybrid).
              </p>
            </div>

            {/* Suggested prompts */}
            {!smartQuery.data && !smartQuery.loading && (
              <div className="flex flex-wrap gap-2">
                {SMART_QUERY_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => { setSmartInput(prompt); }}
                    className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-600 text-xs text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}

            {/* Error */}
            {smartQuery.error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 text-sm text-red-700 dark:text-red-300">
                {smartQuery.error}
              </div>
            )}

            {/* Result */}
            {smartQuery.data && (
              <div className="space-y-4">
                {/* Strategy + confidence badges */}
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300">
                    <Zap className="h-3 w-3" />
                    {smartQuery.data.strategy_used}
                  </span>
                  {smartQuery.data.confidence > 0 && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300">
                      {(smartQuery.data.confidence * 100).toFixed(0)}% confidence
                    </span>
                  )}
                  {smartQuery.data.query_analysis?.intent && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                      {smartQuery.data.query_analysis.intent}
                    </span>
                  )}
                </div>

                {/* Answer */}
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-semibold text-slate-900 dark:text-white">Answer</span>
                  </div>
                  <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{smartQuery.data.answer}</p>
                </div>

                {/* Sources */}
                {smartQuery.data.sources && smartQuery.data.sources.length > 0 && (
                  <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-2 flex items-center gap-1.5">
                      <Database className="h-4 w-4 text-blue-500" />
                      Sources ({smartQuery.data.sources.length})
                    </h3>
                    <div className="space-y-2">
                      {smartQuery.data.sources.slice(0, 8).map((s, i) => (
                        <div key={i} className="text-xs border-l-2 border-blue-300 pl-3 py-1">
                          <span className="text-slate-400">[{s.collection}]</span>{' '}
                          <span className="text-slate-700 dark:text-slate-300">
                            {s.content?.slice(0, 200)}
                          </span>
                          {s.score > 0 && (
                            <span className="ml-2 text-slate-400">({(s.score * 100).toFixed(0)}%)</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Detected entities */}
                {smartQuery.data.query_analysis?.entities && smartQuery.data.query_analysis.entities.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    <span className="text-xs text-slate-500 mr-1">Entities:</span>
                    {smartQuery.data.query_analysis.entities.map((ent) => (
                      <span key={ent} className="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                        {ent}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* ── DATA QUALITY ──────────────────────── */}
        {tab === 'quality' && (
          <>
            {qualityStats.loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                <span className="ml-2 text-sm text-slate-500">Loading quality metrics...</span>
              </div>
            ) : qualityStats.data ? (
              <>
                {/* Overall summary cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                    <div className="text-xs text-slate-500 uppercase">Mean Score</div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                      {qualityStats.data.overall.mean.toFixed(1)}
                    </div>
                  </div>
                  <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                    <div className="text-xs text-slate-500 uppercase">Median Score</div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                      {qualityStats.data.overall.median.toFixed(1)}
                    </div>
                  </div>
                  <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                    <div className="text-xs text-slate-500 uppercase">25th Percentile</div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                      {qualityStats.data.overall.p25.toFixed(1)}
                    </div>
                  </div>
                  <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                    <div className="text-xs text-slate-500 uppercase">Total Scored</div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                      {qualityStats.data.overall.total.toLocaleString()}
                    </div>
                  </div>
                </div>

                {/* Histogram */}
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-1.5">
                    <BarChart3 className="h-4 w-4 text-blue-500" />
                    Score Distribution
                  </h3>
                  <div className="space-y-3">
                    {qualityStats.data.buckets.map((bucket) => (
                      <div key={bucket.range} className="flex items-center gap-3">
                        <span className="text-xs text-slate-500 w-16 text-right font-mono">{bucket.range}</span>
                        <div className="flex-1 bg-slate-200 dark:bg-slate-700 rounded-full h-5 relative">
                          <div
                            className={`bg-gradient-to-r ${getQualityBarColor(bucket.range)} h-5 rounded-full transition-all`}
                            style={{ width: `${Math.max(bucket.pct, 1)}%` }}
                          />
                          <span className="absolute inset-0 flex items-center justify-center text-[10px] font-medium text-slate-700 dark:text-slate-200">
                            {bucket.count.toLocaleString()} ({bucket.pct.toFixed(1)}%)
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Per-type breakdown */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Object.entries(qualityStats.data.by_type).map(([entityType, stats]) => (
                    <div
                      key={entityType}
                      className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4"
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${typeColor(entityType)}`}>
                          {entityType}
                        </span>
                        <span className="text-xs text-slate-400">{stats.count.toLocaleString()} entities</span>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-xs">
                        <div>
                          <div className="text-slate-500">Mean</div>
                          <div className="font-bold text-slate-900 dark:text-white text-lg">{stats.mean.toFixed(1)}</div>
                        </div>
                        <div>
                          <div className="text-slate-500">Median</div>
                          <div className="font-bold text-slate-900 dark:text-white text-lg">{stats.median.toFixed(1)}</div>
                        </div>
                        <div>
                          <div className="text-slate-500">P25</div>
                          <div className="font-semibold text-slate-700 dark:text-slate-300">{stats.p25.toFixed(1)}</div>
                        </div>
                        <div>
                          <div className="text-slate-500">P75</div>
                          <div className="font-semibold text-slate-700 dark:text-slate-300">{stats.p75.toFixed(1)}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : qualityStats.error ? (
              <div className="text-center py-12 text-red-500">
                Failed to load quality stats: {qualityStats.error}
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500">
                No quality score data available. Run the Intelligent DB Enhancement Pipeline first.
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
