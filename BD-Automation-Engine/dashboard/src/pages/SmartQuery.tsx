/**
 * Smart Query Page
 *
 * Natural language search interface with strategy selection,
 * results display with sources, and query analysis.
 */

import { useState } from 'react';
import {
  Search,
  Sparkles,
  Brain,
  FileText,
  AlertCircle,
  Clock,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Lightbulb,
  Users,
  Building2,
  Briefcase,
  FileQuestion,
  Zap,
  RotateCcw,
} from 'lucide-react';
import { SmartSearchBar } from '../components/hub/SmartSearchBar';
import { useSmartQuery } from '../hooks/useHubApi';
import type { SearchStrategy } from '../services/hubApi';
import { Skeleton } from '../components/ui/Skeleton';

interface SmartQueryProps {
  loading?: boolean;
}

export function SmartQuery({ loading: pageLoading }: SmartQueryProps) {
  const { data: result, loading, error, execute, reset } = useSmartQuery();
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [queryHistory, setQueryHistory] = useState<Array<{ query: string; strategy: string; timestamp: Date }>>([]);

  const handleSearch = async (query: string, strategy: SearchStrategy) => {
    await execute(query, strategy);
    setQueryHistory((prev) => [
      { query, strategy, timestamp: new Date() },
      ...prev.slice(0, 9), // Keep last 10 queries
    ]);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/30';
    if (confidence >= 0.4) return 'text-orange-600 bg-orange-100 dark:text-orange-400 dark:bg-orange-900/30';
    return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/30';
  };

  if (pageLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 h-full overflow-y-auto bg-slate-50 dark:bg-slate-900 transition-colors">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Smart Query</h1>
            <p className="text-slate-500 dark:text-slate-400">
              Natural language search across 8,447+ BD intelligence records
            </p>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-8">
        <SmartSearchBar onSearch={handleSearch} loading={loading} />
      </div>

      {/* Loading State */}
      {loading && (
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Loading skeleton for answer */}
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
            <div className="p-4 border-b border-slate-100 dark:border-slate-700 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
              <div className="flex items-center gap-2">
                <div className="h-5 w-5 rounded bg-purple-200 dark:bg-purple-800 animate-pulse" />
                <Skeleton className="h-5 w-24" />
              </div>
            </div>
            <div className="p-6 space-y-3">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          </div>
          {/* Loading indicator */}
          <div className="flex items-center justify-center gap-3 py-4">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="h-2 w-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="h-2 w-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-sm text-slate-500 dark:text-slate-400">Analyzing your query across 8,447+ records...</span>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-200 dark:border-red-800 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-medium text-red-800 dark:text-red-300">Search Failed</p>
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
          <button
            onClick={reset}
            className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
            title="Try again"
          >
            <RotateCcw className="h-4 w-4 text-red-600 dark:text-red-400" />
          </button>
        </div>
      )}

      {/* Results */}
      {result && !error && !loading && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Answer Card */}
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
            <div className="p-4 border-b border-slate-100 dark:border-slate-700 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-purple-600" />
                  <span className="font-medium text-slate-900">AI Response</span>
                </div>
                <div className="flex items-center gap-4">
                  {/* Confidence Meter */}
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-1000 ${
                          result.confidence >= 0.8 ? 'bg-gradient-to-r from-green-400 to-green-600' :
                          result.confidence >= 0.6 ? 'bg-gradient-to-r from-yellow-400 to-yellow-600' :
                          result.confidence >= 0.4 ? 'bg-gradient-to-r from-orange-400 to-orange-600' :
                          'bg-gradient-to-r from-red-400 to-red-600'
                        }`}
                        style={{ width: `${result.confidence * 100}%` }}
                      />
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(result.confidence)}`}>
                      {(result.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <span className="text-xs text-slate-500 flex items-center gap-1 px-2 py-1 bg-white/60 rounded-lg">
                    <Zap className="h-3 w-3" />
                    {result.strategy_used}
                  </span>
                </div>
              </div>
            </div>
            <div className="p-6">
              <div className="prose prose-slate max-w-none">
                <p className="text-slate-700 whitespace-pre-wrap leading-relaxed">{result.answer}</p>
              </div>
            </div>
          </div>

          {/* Query Analysis */}
          {result.query_analysis && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <button
                onClick={() => setShowAnalysis(!showAnalysis)}
                className="w-full p-4 flex items-center justify-between hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5 text-amber-500" />
                  <span className="font-medium text-slate-900">Query Analysis</span>
                </div>
                {showAnalysis ? (
                  <ChevronUp className="h-5 w-5 text-slate-400" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-slate-400" />
                )}
              </button>
              {showAnalysis && (
                <div className="px-4 pb-4 space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs font-medium text-slate-500 mb-1">Intent</p>
                      <p className="text-sm text-slate-700">{result.query_analysis.intent}</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs font-medium text-slate-500 mb-1">Strategy Used</p>
                      <p className="text-sm text-slate-700 capitalize">{result.strategy_used}</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs font-medium text-slate-500 mb-1">Suggested Strategy</p>
                      <p className="text-sm text-slate-700 capitalize">{result.query_analysis.suggested_strategy}</p>
                    </div>
                  </div>
                  {result.query_analysis.entities.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-slate-500 mb-2">Entities Detected</p>
                      <div className="flex flex-wrap gap-2">
                        {result.query_analysis.entities.map((entity, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 bg-blue-100 text-blue-700 text-sm rounded"
                          >
                            {entity}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Sources */}
          {result.sources && result.sources.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="p-4 border-b border-slate-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-slate-600" />
                    <span className="font-medium text-slate-900">Sources</span>
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                      {result.sources.length}
                    </span>
                  </div>
                </div>
              </div>
              <div className="divide-y divide-slate-100">
                {result.sources.map((source, i) => {
                  const collectionConfig: Record<string, { icon: typeof Users; color: string; bg: string }> = {
                    contacts: { icon: Users, color: 'text-cyan-600', bg: 'bg-cyan-50' },
                    programs: { icon: Building2, color: 'text-purple-600', bg: 'bg-purple-50' },
                    documents: { icon: FileText, color: 'text-amber-600', bg: 'bg-amber-50' },
                    activities: { icon: Clock, color: 'text-green-600', bg: 'bg-green-50' },
                    jobs: { icon: Briefcase, color: 'text-blue-600', bg: 'bg-blue-50' },
                  };
                  const config = collectionConfig[source.collection] || { icon: FileQuestion, color: 'text-slate-600', bg: 'bg-slate-50' };
                  const SourceIcon = config.icon;

                  return (
                    <div key={i} className="p-4 hover:bg-slate-50 transition-colors group">
                      <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-lg ${config.bg} flex-shrink-0`}>
                          <SourceIcon className={`h-4 w-4 ${config.color}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`px-2 py-0.5 text-xs rounded capitalize ${config.bg} ${config.color}`}>
                              {source.collection}
                            </span>
                            <div className="flex items-center gap-1">
                              <div className="w-12 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-blue-500 rounded-full"
                                  style={{ width: `${source.score * 100}%` }}
                                />
                              </div>
                              <span className="text-xs text-slate-400">
                                {(source.score * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                          <p className="text-sm text-slate-700 line-clamp-2">{source.content}</p>
                        </div>
                        <button className="p-2 hover:bg-slate-200 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity">
                          <ExternalLink className="h-4 w-4 text-slate-400" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!result && !error && !loading && (
        <div className="py-12">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-500 mb-4 shadow-lg">
              <Search className="h-10 w-10 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-slate-900 mb-2">Start Searching</h3>
            <p className="text-slate-500 max-w-md mx-auto">
              Ask any question about your BD intelligence data. The smart query system will
              automatically choose the best search strategy.
            </p>
          </div>

          {/* Quick Query Suggestions */}
          <div className="max-w-3xl mx-auto">
            <p className="text-sm font-medium text-slate-500 mb-3 flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-amber-500" />
              Try these example queries
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                { icon: Users, text: 'Find Tier 1 contacts at Leidos on DCGS', color: 'cyan' },
                { icon: Building2, text: 'What programs does Northrop Grumman prime?', color: 'purple' },
                { icon: Briefcase, text: 'Show AF programs recompeting in 2025', color: 'blue' },
                { icon: FileText, text: 'GDIT past performance on ISR programs', color: 'amber' },
              ].map((item, i) => {
                const Icon = item.icon;
                return (
                  <button
                    key={i}
                    onClick={() => handleSearch(item.text, 'auto')}
                    className={`flex items-center gap-3 p-4 text-left bg-white rounded-xl border border-slate-200 hover:border-${item.color}-300 hover:shadow-md transition-all group`}
                  >
                    <div className={`p-2 rounded-lg bg-${item.color}-50 group-hover:bg-${item.color}-100 transition-colors`}>
                      <Icon className={`h-5 w-5 text-${item.color}-600`} />
                    </div>
                    <span className="text-sm text-slate-700 group-hover:text-slate-900">{item.text}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Query History */}
      {queryHistory.length > 0 && !result && (
        <div className="mt-8">
          <h3 className="text-sm font-medium text-slate-500 mb-3">Recent Queries</h3>
          <div className="space-y-2">
            {queryHistory.map((item, i) => (
              <button
                key={i}
                onClick={() => handleSearch(item.query, item.strategy as SearchStrategy)}
                className="w-full text-left p-3 bg-white rounded-lg border border-slate-200 hover:border-blue-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-700">{item.query}</span>
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <span className="capitalize">{item.strategy}</span>
                    <span>{item.timestamp.toLocaleTimeString()}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default SmartQuery;
