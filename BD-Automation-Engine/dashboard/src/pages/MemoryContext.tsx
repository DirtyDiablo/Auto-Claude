/**
 * Memory Context Page
 *
 * Memory browser for entity facts, BD insights, contact context,
 * and program context exploration.
 */

import { useState } from 'react';
import {
  Brain,
  Search,
  Users,
  Building2,
  Lightbulb,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  AlertCircle,
  FileText,
  Clock,
  ChevronRight,
  Sparkles,
  RotateCcw,
} from 'lucide-react';
import {
  useMemorySearch,
  useEntityFacts,
  useBDInsights,
} from '../hooks/useHubApi';
import { hubApiClient } from '../services/hubApi';
import { Skeleton, SkeletonText } from '../components/ui/Skeleton';

type TabType = 'search' | 'entity' | 'insights' | 'contact' | 'program';

const INSIGHT_ICONS: Record<string, typeof Lightbulb> = {
  pattern: TrendingUp,
  opportunity: CheckCircle2,
  risk: AlertTriangle,
  recommendation: Lightbulb,
};

const INSIGHT_COLORS: Record<string, string> = {
  pattern: 'text-blue-600 bg-blue-100',
  opportunity: 'text-green-600 bg-green-100',
  risk: 'text-red-600 bg-red-100',
  recommendation: 'text-amber-600 bg-amber-100',
};

export function MemoryContext() {
  const [activeTab, setActiveTab] = useState<TabType>('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [entityName, setEntityName] = useState('');
  const [contactName, setContactName] = useState('');
  const [programName, setProgramName] = useState('');
  const [insightFilter, setInsightFilter] = useState<string>('');

  // Hooks
  const memorySearch = useMemorySearch();
  const entityFacts = useEntityFacts();
  const { data: insights, loading: insightsLoading, error: insightsError, refetch: refetchInsights } = useBDInsights(
    insightFilter as 'pattern' | 'opportunity' | 'risk' | 'recommendation' | undefined
  );

  // Contact and program context state
  const [contactContext, setContactContext] = useState<unknown>(null);
  const [contactLoading, setContactLoading] = useState(false);
  const [contactError, setContactError] = useState<string | null>(null);

  const [programContext, setProgramContext] = useState<unknown>(null);
  const [programLoading, setProgramLoading] = useState(false);
  const [programError, setProgramError] = useState<string | null>(null);

  // Handlers
  const handleMemorySearch = () => {
    if (searchQuery.trim()) {
      memorySearch.execute(searchQuery);
    }
  };

  const handleEntitySearch = () => {
    if (entityName.trim()) {
      entityFacts.execute(entityName);
    }
  };

  const handleContactSearch = async () => {
    if (!contactName.trim()) return;
    setContactLoading(true);
    setContactError(null);
    try {
      const result = await hubApiClient.getContactContext(contactName);
      setContactContext(result);
    } catch (err) {
      setContactError(err instanceof Error ? err.message : 'Failed to fetch contact context');
    } finally {
      setContactLoading(false);
    }
  };

  const handleProgramSearch = async () => {
    if (!programName.trim()) return;
    setProgramLoading(true);
    setProgramError(null);
    try {
      const result = await hubApiClient.getProgramContext(programName);
      setProgramContext(result);
    } catch (err) {
      setProgramError(err instanceof Error ? err.message : 'Failed to fetch program context');
    } finally {
      setProgramLoading(false);
    }
  };

  const tabs = [
    { id: 'search', label: 'Memory Search', icon: Search },
    { id: 'entity', label: 'Entity Facts', icon: FileText },
    { id: 'insights', label: 'BD Insights', icon: Lightbulb },
    { id: 'contact', label: 'Contact Context', icon: Users },
    { id: 'program', label: 'Program Context', icon: Building2 },
  ];

  return (
    <div className="p-6 h-full overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-gradient-to-br from-pink-500 to-purple-500">
            <Brain className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Memory Context</h1>
            <p className="text-slate-500">
              Explore stored knowledge, entity facts, and BD insights
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-100 rounded-xl p-1.5 mb-6 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          const tabColors: Record<string, string> = {
            search: 'from-purple-500 to-pink-500',
            entity: 'from-blue-500 to-cyan-500',
            insights: 'from-amber-500 to-orange-500',
            contact: 'from-cyan-500 to-teal-500',
            program: 'from-violet-500 to-purple-500',
          };
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all duration-200 ${
                isActive
                  ? 'bg-white text-slate-900 shadow-md'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
              }`}
            >
              <div className={`p-1 rounded-md ${isActive ? `bg-gradient-to-br ${tabColors[tab.id]} text-white` : ''}`}>
                <Icon className={`h-4 w-4 ${isActive ? '' : 'text-slate-400'}`} />
              </div>
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {/* Memory Search Tab */}
        {activeTab === 'search' && (
          <div className="p-6">
            <div className="flex gap-2 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleMemorySearch()}
                  placeholder="Search memory (e.g., Leidos DCGS patterns)..."
                  className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <button
                onClick={handleMemorySearch}
                disabled={memorySearch.loading}
                className="px-6 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-slate-300"
              >
                {memorySearch.loading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Search'}
              </button>
            </div>

            {memorySearch.error && (
              <div className="p-4 bg-red-50 rounded-lg flex items-start gap-2 mb-4">
                <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
                <p className="text-red-700">{memorySearch.error}</p>
              </div>
            )}

            {memorySearch.data && (
              <div>
                <p className="text-sm text-slate-500 mb-4">
                  Found {memorySearch.data.total} results
                </p>
                <div className="space-y-3">
                  {memorySearch.data.results.map((result, i) => (
                    <div key={i} className="p-4 bg-slate-50 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded font-medium">
                          {result.fact_type}
                        </span>
                        <span className="text-xs text-slate-400">{result.entity_name}</span>
                        <span className="text-xs text-slate-400">•</span>
                        <span className="text-xs text-slate-400">
                          {(result.confidence * 100).toFixed(0)}% confidence
                        </span>
                      </div>
                      <p className="text-slate-700">{result.content}</p>
                      <p className="text-xs text-slate-400 mt-2">
                        {new Date(result.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Entity Facts Tab */}
        {activeTab === 'entity' && (
          <div className="p-6">
            <div className="flex gap-2 mb-6">
              <input
                type="text"
                value={entityName}
                onChange={(e) => setEntityName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleEntitySearch()}
                placeholder="Enter entity name (e.g., Leidos, AF DCGS)..."
                className="flex-1 px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
              <button
                onClick={handleEntitySearch}
                disabled={entityFacts.loading}
                className="px-6 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-slate-300"
              >
                {entityFacts.loading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Get Facts'}
              </button>
            </div>

            {entityFacts.error && (
              <div className="p-4 bg-red-50 rounded-lg flex items-start gap-2 mb-4">
                <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
                <p className="text-red-700">{entityFacts.error}</p>
              </div>
            )}

            {entityFacts.data && (
              <div>
                <div className="p-4 bg-purple-50 rounded-lg mb-4">
                  <h3 className="font-semibold text-purple-900 mb-1">{entityFacts.data.entity_name}</h3>
                  <p className="text-purple-700">{entityFacts.data.summary}</p>
                </div>
                <div className="space-y-3">
                  {entityFacts.data.facts.map((fact, i) => (
                    <div key={i} className="p-4 bg-slate-50 rounded-lg flex items-start gap-3">
                      <ChevronRight className="h-4 w-4 text-slate-400 mt-1 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-slate-700">{fact.content}</p>
                        <div className="flex items-center gap-2 mt-2 text-xs text-slate-400">
                          <span className="px-2 py-0.5 bg-slate-200 rounded">{fact.fact_type}</span>
                          <span>Source: {fact.source}</span>
                          <span>•</span>
                          <span>{(fact.confidence * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* BD Insights Tab */}
        {activeTab === 'insights' && (
          <div className="p-6">
            <div className="flex gap-2 mb-6">
              <select
                value={insightFilter}
                onChange={(e) => setInsightFilter(e.target.value)}
                className="px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              >
                <option value="">All Types</option>
                <option value="pattern">Patterns</option>
                <option value="opportunity">Opportunities</option>
                <option value="risk">Risks</option>
                <option value="recommendation">Recommendations</option>
              </select>
              <button
                onClick={refetchInsights}
                disabled={insightsLoading}
                className="px-4 py-2.5 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 disabled:opacity-50"
              >
                {insightsLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Refresh'}
              </button>
            </div>

            {insightsError && (
              <div className="p-4 bg-red-50 rounded-lg flex items-start gap-2 mb-4">
                <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
                <p className="text-red-700">{insightsError}</p>
              </div>
            )}

            {insightsLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="p-4 bg-slate-50 rounded-lg animate-pulse">
                    <div className="flex items-start gap-3">
                      <Skeleton className="w-10 h-10 rounded-lg" />
                      <div className="flex-1">
                        <Skeleton className="h-4 w-24 mb-2" />
                        <Skeleton className="h-4 w-full mb-1" />
                        <Skeleton className="h-4 w-3/4" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : insights && insights.length > 0 ? (
              <div className="space-y-3">
                {insights.map((insight, i) => {
                  const Icon = INSIGHT_ICONS[insight.type] || Lightbulb;
                  const colorClass = INSIGHT_COLORS[insight.type] || 'text-slate-600 bg-slate-100';
                  return (
                    <div key={i} className="p-4 bg-slate-50 rounded-lg">
                      <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-lg ${colorClass}`}>
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                              {insight.type}
                            </span>
                            <span className="text-xs text-slate-400">
                              {(insight.confidence * 100).toFixed(0)}% confidence
                            </span>
                          </div>
                          <p className="text-slate-700">{insight.content}</p>
                          {insight.entities.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {insight.entities.map((entity, j) => (
                                <span key={j} className="px-2 py-0.5 bg-white text-slate-600 text-xs rounded border">
                                  {entity}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-100 to-orange-100 mb-4">
                  <Lightbulb className="h-8 w-8 text-amber-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-700 mb-2">No Insights Yet</h3>
                <p className="text-slate-500 max-w-sm mx-auto mb-4">
                  BD insights are generated as you interact with the system. Try searching for contacts or programs to generate insights.
                </p>
                <button
                  onClick={refetchInsights}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-amber-50 text-amber-700 rounded-lg hover:bg-amber-100 transition-colors"
                >
                  <RotateCcw className="h-4 w-4" />
                  Refresh Insights
                </button>
              </div>
            )}
          </div>
        )}

        {/* Contact Context Tab */}
        {activeTab === 'contact' && (
          <div className="p-6">
            <div className="flex gap-2 mb-6">
              <input
                type="text"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleContactSearch()}
                placeholder="Enter contact name..."
                className="flex-1 px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
              <button
                onClick={handleContactSearch}
                disabled={contactLoading}
                className="px-6 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-slate-300"
              >
                {contactLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Get Context'}
              </button>
            </div>

            {contactError && (
              <div className="p-4 bg-red-50 rounded-lg flex items-start gap-2 mb-4">
                <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
                <p className="text-red-700">{contactError}</p>
              </div>
            )}

            {contactContext && (
              <div className="space-y-4">
                {/* Contact Info */}
                <div className="p-4 bg-cyan-50 rounded-lg">
                  <h3 className="font-semibold text-cyan-900 mb-1">
                    {(contactContext as { contact: { name: string } }).contact.name}
                  </h3>
                  <p className="text-cyan-700">
                    {(contactContext as { contact: { title: string } }).contact.title} at{' '}
                    {(contactContext as { contact: { company: string } }).contact.company}
                  </p>
                </div>

                {/* Call History */}
                {(contactContext as { call_history: unknown[] }).call_history?.length > 0 && (
                  <div>
                    <h4 className="font-medium text-slate-900 mb-2 flex items-center gap-2">
                      <Clock className="h-4 w-4" /> Call History
                    </h4>
                    <div className="space-y-2">
                      {(contactContext as { call_history: Array<{ date: string; notes: string; outcome: string }> }).call_history.map((call, i) => (
                        <div key={i} className="p-3 bg-slate-50 rounded-lg text-sm">
                          <div className="flex justify-between mb-1">
                            <span className="text-slate-500">{call.date}</span>
                            <span className="px-2 py-0.5 bg-slate-200 rounded text-xs">{call.outcome}</span>
                          </div>
                          <p className="text-slate-700">{call.notes}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Insights */}
                {(contactContext as { insights: string[] }).insights?.length > 0 && (
                  <div>
                    <h4 className="font-medium text-slate-900 mb-2 flex items-center gap-2">
                      <Lightbulb className="h-4 w-4" /> Insights
                    </h4>
                    <ul className="space-y-1">
                      {(contactContext as { insights: string[] }).insights.map((insight, i) => (
                        <li key={i} className="flex items-start gap-2 text-slate-600">
                          <ChevronRight className="h-4 w-4 text-slate-400 mt-0.5" />
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Program Context Tab */}
        {activeTab === 'program' && (
          <div className="p-6">
            <div className="flex gap-2 mb-6">
              <input
                type="text"
                value={programName}
                onChange={(e) => setProgramName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleProgramSearch()}
                placeholder="Enter program name (e.g., AF DCGS)..."
                className="flex-1 px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
              <button
                onClick={handleProgramSearch}
                disabled={programLoading}
                className="px-6 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-slate-300"
              >
                {programLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Get Context'}
              </button>
            </div>

            {programError && (
              <div className="p-4 bg-red-50 rounded-lg flex items-start gap-2 mb-4">
                <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
                <p className="text-red-700">{programError}</p>
              </div>
            )}

            {programContext && (
              <div className="space-y-4">
                {/* Program Info */}
                <div className="p-4 bg-purple-50 rounded-lg">
                  <h3 className="font-semibold text-purple-900 mb-1">
                    {(programContext as { program: { name: string } }).program.name}
                  </h3>
                  <p className="text-purple-700">
                    {(programContext as { program: { agency: string } }).program.agency} • Prime:{' '}
                    {(programContext as { program: { prime: string } }).program.prime}
                  </p>
                </div>

                {/* Intel History */}
                {(programContext as { intel_history: unknown[] }).intel_history?.length > 0 && (
                  <div>
                    <h4 className="font-medium text-slate-900 mb-2">Intel History</h4>
                    <div className="space-y-2">
                      {(programContext as { intel_history: Array<{ date: string; type: string; content: string }> }).intel_history.map((intel, i) => (
                        <div key={i} className="p-3 bg-slate-50 rounded-lg text-sm">
                          <div className="flex justify-between mb-1">
                            <span className="text-slate-500">{intel.date}</span>
                            <span className="px-2 py-0.5 bg-slate-200 rounded text-xs">{intel.type}</span>
                          </div>
                          <p className="text-slate-700">{intel.content}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Patterns & Opportunities */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(programContext as { patterns: string[] }).patterns?.length > 0 && (
                    <div>
                      <h4 className="font-medium text-slate-900 mb-2 flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" /> Patterns
                      </h4>
                      <ul className="space-y-1">
                        {(programContext as { patterns: string[] }).patterns.map((pattern, i) => (
                          <li key={i} className="flex items-start gap-2 text-slate-600 text-sm">
                            <ChevronRight className="h-4 w-4 text-slate-400 mt-0.5" />
                            {pattern}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {(programContext as { opportunities: string[] }).opportunities?.length > 0 && (
                    <div>
                      <h4 className="font-medium text-slate-900 mb-2 flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4" /> Opportunities
                      </h4>
                      <ul className="space-y-1">
                        {(programContext as { opportunities: string[] }).opportunities.map((opp, i) => (
                          <li key={i} className="flex items-start gap-2 text-slate-600 text-sm">
                            <ChevronRight className="h-4 w-4 text-green-400 mt-0.5" />
                            {opp}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default MemoryContext;
