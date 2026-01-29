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
  CheckCircle2,
  Clock,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Lightbulb,
} from 'lucide-react';
import { SmartSearchBar } from '../components/hub/SmartSearchBar';
import { useSmartQuery } from '../hooks/useHubApi';
import type { SearchStrategy } from '../services/hubApi';

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
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    if (confidence >= 0.4) return 'text-orange-600 bg-orange-100';
    return 'text-red-600 bg-red-100';
  };

  if (pageLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 h-full overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Smart Query</h1>
            <p className="text-slate-500">
              Natural language search across 8,447+ BD intelligence records
            </p>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-8">
        <SmartSearchBar onSearch={handleSearch} loading={loading} />
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 rounded-xl border border-red-200 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-800">Search Failed</p>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !error && (
        <div className="space-y-6">
          {/* Answer Card */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-100 bg-gradient-to-r from-blue-50 to-purple-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-purple-600" />
                  <span className="font-medium text-slate-900">AI Response</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(result.confidence)}`}>
                    {(result.confidence * 100).toFixed(0)}% confidence
                  </span>
                  <span className="text-xs text-slate-500 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
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
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-slate-600" />
                  <span className="font-medium text-slate-900">Sources ({result.sources.length})</span>
                </div>
              </div>
              <div className="divide-y divide-slate-100">
                {result.sources.map((source, i) => (
                  <div key={i} className="p-4 hover:bg-slate-50 transition-colors">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="px-2 py-0.5 bg-slate-100 text-slate-600 text-xs rounded">
                            {source.collection}
                          </span>
                          <span className="text-xs text-slate-400">
                            Score: {(source.score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-sm text-slate-700 line-clamp-2">{source.content}</p>
                      </div>
                      <button className="p-1 hover:bg-slate-200 rounded">
                        <ExternalLink className="h-4 w-4 text-slate-400" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!result && !error && !loading && (
        <div className="text-center py-16">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
            <Search className="h-8 w-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Start Searching</h3>
          <p className="text-slate-500 max-w-md mx-auto">
            Ask any question about your BD intelligence data. The smart query system will
            automatically choose the best search strategy for your query.
          </p>
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
