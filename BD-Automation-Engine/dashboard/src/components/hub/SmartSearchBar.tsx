/**
 * Smart Search Bar Component
 *
 * Enhanced search input with strategy dropdown and example query suggestions.
 */

import { useState } from 'react';
import { Search, ChevronDown, Sparkles, Loader2, Zap, Brain, Database, Network } from 'lucide-react';
import type { SearchStrategy } from '../../services/hubApi';

interface SmartSearchBarProps {
  onSearch: (query: string, strategy: SearchStrategy) => void;
  loading?: boolean;
  placeholder?: string;
}

const STRATEGIES: Array<{
  value: SearchStrategy;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}> = [
  {
    value: 'auto',
    label: 'Auto',
    description: 'Automatically choose the best strategy',
    icon: Sparkles,
  },
  {
    value: 'semantic',
    label: 'Semantic',
    description: 'Meaning-based search using embeddings',
    icon: Brain,
  },
  {
    value: 'keyword',
    label: 'Keyword',
    description: 'Traditional keyword matching',
    icon: Search,
  },
  {
    value: 'hybrid',
    label: 'Hybrid',
    description: 'Combine semantic and keyword search',
    icon: Zap,
  },
  {
    value: 'lightrag',
    label: 'LightRAG',
    description: 'Graph-enhanced retrieval',
    icon: Network,
  },
];

const EXAMPLE_QUERIES = [
  'Find Tier 1 contacts at Leidos working on DCGS',
  'What programs does Northrop Grumman prime?',
  'Who are the key decision makers for GBSD?',
  'What past performance does GDIT have on ISR programs?',
  'Show me Air Force programs recompeting in 2025',
  'Find analysts with TS/SCI clearance in San Antonio',
];

export function SmartSearchBar({
  onSearch,
  loading = false,
  placeholder = 'Ask anything about your BD intelligence...',
}: SmartSearchBarProps) {
  const [query, setQuery] = useState('');
  const [strategy, setStrategy] = useState<SearchStrategy>('auto');
  const [showStrategies, setShowStrategies] = useState(false);
  const [showExamples, setShowExamples] = useState(false);

  const selectedStrategy = STRATEGIES.find((s) => s.value === strategy) || STRATEGIES[0];
  const StrategyIcon = selectedStrategy.icon;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;
    onSearch(query.trim(), strategy);
    setShowExamples(false);
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
    setShowExamples(false);
    onSearch(example, strategy);
  };

  return (
    <div className="relative">
      <form onSubmit={handleSubmit}>
        <div className="flex items-stretch bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
          {/* Search Input */}
          <div className="flex-1 flex items-center">
            <Search className="h-5 w-5 text-slate-400 ml-4" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setShowExamples(true)}
              onBlur={() => setTimeout(() => setShowExamples(false), 200)}
              placeholder={placeholder}
              disabled={loading}
              className="flex-1 px-3 py-4 text-lg border-none outline-none bg-transparent disabled:cursor-not-allowed"
            />
          </div>

          {/* Strategy Dropdown */}
          <div className="relative border-l border-slate-200">
            <button
              type="button"
              onClick={() => setShowStrategies(!showStrategies)}
              className="h-full px-4 flex items-center gap-2 hover:bg-slate-50 transition-colors"
            >
              <StrategyIcon className="h-4 w-4 text-slate-500" />
              <span className="text-sm font-medium text-slate-700">{selectedStrategy.label}</span>
              <ChevronDown className="h-4 w-4 text-slate-400" />
            </button>

            {showStrategies && (
              <div className="absolute right-0 top-full mt-1 w-64 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-20">
                {STRATEGIES.map((s) => {
                  const Icon = s.icon;
                  return (
                    <button
                      key={s.value}
                      type="button"
                      onClick={() => {
                        setStrategy(s.value);
                        setShowStrategies(false);
                      }}
                      className={`w-full px-4 py-2 flex items-start gap-3 hover:bg-slate-50 transition-colors ${
                        strategy === s.value ? 'bg-blue-50' : ''
                      }`}
                    >
                      <Icon className={`h-4 w-4 mt-0.5 ${strategy === s.value ? 'text-blue-600' : 'text-slate-400'}`} />
                      <div className="text-left">
                        <p className={`text-sm font-medium ${strategy === s.value ? 'text-blue-600' : 'text-slate-700'}`}>
                          {s.label}
                        </p>
                        <p className="text-xs text-slate-500">{s.description}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 bg-blue-600 text-white hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Sparkles className="h-5 w-5" />
            )}
            <span className="font-medium">{loading ? 'Searching...' : 'Search'}</span>
          </button>
        </div>
      </form>

      {/* Example Queries */}
      {showExamples && !query && (
        <div className="absolute left-0 right-0 top-full mt-2 bg-white rounded-xl shadow-lg border border-slate-200 p-4 z-10">
          <p className="text-sm font-medium text-slate-500 mb-3 flex items-center gap-2">
            <Database className="h-4 w-4" />
            Example queries
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {EXAMPLE_QUERIES.map((example, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleExampleClick(example)}
                className="text-left px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 rounded-lg transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default SmartSearchBar;
