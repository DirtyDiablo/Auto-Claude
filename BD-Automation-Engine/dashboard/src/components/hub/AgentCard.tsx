/**
 * Agent Card Component
 *
 * Reusable card for executing BD agents with query input,
 * execution button, response area, and confidence meter.
 */

import { useState } from 'react';
import { Bot, Send, Loader2, AlertCircle, CheckCircle2, Clock, FileText, Sparkles, Zap } from 'lucide-react';
import type { AgentResponse } from '../../services/hubApi';

interface AgentCardProps {
  title: string;
  description: string;
  placeholder?: string;
  icon?: React.ComponentType<{ className?: string }>;
  onExecute: (query: string) => Promise<AgentResponse | null>;
  loading?: boolean;
  result?: AgentResponse | null;
  error?: string | null;
}

export function AgentCard({
  title,
  description,
  placeholder = 'Enter your query...',
  icon: Icon = Bot,
  onExecute,
  loading = false,
  result,
  error,
}: AgentCardProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;
    await onExecute(query.trim());
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-500';
    if (confidence >= 0.6) return 'bg-yellow-500';
    if (confidence >= 0.4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    if (confidence >= 0.4) return 'Low';
    return 'Very Low';
  };

  return (
    <div className={`bg-white rounded-xl shadow-sm border overflow-hidden transition-all duration-300 ${
      loading ? 'border-blue-300 ring-2 ring-blue-100' : 'border-slate-200 hover:shadow-md'
    }`}>
      {/* Header */}
      <div className={`p-4 border-b transition-colors duration-300 ${
        loading ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-100' : 'bg-slate-50 border-slate-100'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg transition-colors duration-300 ${
              loading ? 'bg-blue-200 animate-pulse' : 'bg-blue-100'
            }`}>
              <Icon className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">{title}</h3>
              <p className="text-sm text-slate-500">{description}</p>
            </div>
          </div>
          {loading && (
            <div className="flex items-center gap-1.5">
              <span className="flex h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
              <span className="text-xs text-blue-600 font-medium">Processing</span>
            </div>
          )}
        </div>
      </div>

      {/* Query Input */}
      <form onSubmit={handleSubmit} className="p-4 border-b border-slate-100">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            disabled={loading}
            className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-slate-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            {loading ? 'Running...' : 'Execute'}
          </button>
        </div>
      </form>

      {/* Results Area */}
      <div className="p-4 min-h-[120px]">
        {loading && (
          <div className="space-y-4">
            {/* Progress Steps Animation */}
            <div className="flex items-center justify-center gap-8 py-4">
              {[
                { icon: Sparkles, label: 'Analyzing', delay: '0ms' },
                { icon: Zap, label: 'Reasoning', delay: '300ms' },
                { icon: FileText, label: 'Generating', delay: '600ms' },
              ].map((step, i) => {
                const StepIcon = step.icon;
                return (
                  <div key={i} className="flex flex-col items-center gap-1">
                    <div
                      className="p-2 rounded-full bg-blue-50 animate-pulse"
                      style={{ animationDelay: step.delay }}
                    >
                      <StepIcon className="h-4 w-4 text-blue-500" />
                    </div>
                    <span className="text-xs text-slate-500">{step.label}</span>
                  </div>
                );
              })}
            </div>
            {/* Progress Bar */}
            <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-500 rounded-full animate-progress" />
            </div>
            <p className="text-center text-sm text-slate-500">AI agent is processing your query...</p>
          </div>
        )}

        {error && !loading && (
          <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg">
            <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-800">Error</p>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
        )}

        {result && !loading && !error && (
          <div className="space-y-4">
            {/* Response */}
            <div className="prose prose-sm max-w-none">
              <p className="text-slate-700 whitespace-pre-wrap">{result.response}</p>
            </div>

            {/* Metadata */}
            <div className="flex flex-wrap gap-4 pt-3 border-t border-slate-100">
              {/* Confidence */}
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-slate-400" />
                <span className="text-sm text-slate-500">Confidence:</span>
                <div className="flex items-center gap-1">
                  <div className="w-16 h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getConfidenceColor(result.confidence)} transition-all`}
                      style={{ width: `${result.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-700">
                    {getConfidenceLabel(result.confidence)} ({(result.confidence * 100).toFixed(0)}%)
                  </span>
                </div>
              </div>

              {/* Execution Time */}
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-slate-400" />
                <span className="text-sm text-slate-500">Time:</span>
                <span className="text-sm font-medium text-slate-700">
                  {result.execution_time.toFixed(2)}s
                </span>
              </div>

              {/* Sources */}
              {result.sources && result.sources.length > 0 && (
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-slate-400" />
                  <span className="text-sm text-slate-500">Sources:</span>
                  <span className="text-sm font-medium text-slate-700">
                    {result.sources.length}
                  </span>
                </div>
              )}
            </div>

            {/* Sources List */}
            {result.sources && result.sources.length > 0 && (
              <div className="pt-2">
                <p className="text-xs font-medium text-slate-500 mb-2">Sources:</p>
                <div className="flex flex-wrap gap-1">
                  {result.sources.slice(0, 5).map((source, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded"
                    >
                      {source}
                    </span>
                  ))}
                  {result.sources.length > 5 && (
                    <span className="px-2 py-1 text-slate-400 text-xs">
                      +{result.sources.length - 5} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {!loading && !error && !result && (
          <div className="flex flex-col items-center justify-center h-24 text-slate-400">
            <Icon className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">Enter a query and click Execute to run the agent</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default AgentCard;
