import { useState, useEffect, useCallback } from 'react';
import { Brain, RefreshCw, Trash2, Plus, X, Loader2 } from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

interface Memory {
  id: string;
  entity_type: string;
  entity_name: string;
  summary: string;
  confidence: number;
  last_updated: string;
  source_interaction: string;
}

interface AIMemoryPanelProps {
  entityType: 'contact' | 'program';
  entityName: string;
}

function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80 ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' :
    pct >= 50 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300' :
    'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300';
  return <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${color}`}>{pct}%</span>;
}

export function AIMemoryPanel({ entityType, entityName }: AIMemoryPanelProps) {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newSummary, setNewSummary] = useState('');
  const [newConfidence, setNewConfidence] = useState(0.8);
  const [saving, setSaving] = useState(false);

  const fetchMemories = useCallback(async () => {
    setLoading(true);
    try {
      const data = await hubApiClient.getEntityMemories(entityType, entityName);
      setMemories(data.memories);
    } catch {
      setMemories([]);
    } finally {
      setLoading(false);
    }
  }, [entityType, entityName]);

  useEffect(() => {
    fetchMemories();
  }, [fetchMemories]);

  const handleAdd = async () => {
    if (!newSummary.trim()) return;
    setSaving(true);
    try {
      await hubApiClient.storeMemory({
        entity_type: entityType,
        entity_name: entityName,
        summary: newSummary.trim(),
        confidence: newConfidence,
      });
      setNewSummary('');
      setShowAdd(false);
      fetchMemories();
    } catch {
      // Failed
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await hubApiClient.deleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
    } catch {
      // Failed
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-purple-500" />
          <h3 className="font-semibold text-slate-800 dark:text-slate-200">AI Memory</h3>
          <span className="text-xs text-slate-400">({memories.length})</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchMemories}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            title="Refresh memories"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors"
          >
            <Plus className="h-3 w-3" />
            Add Memory
          </button>
        </div>
      </div>

      {/* Add form */}
      {showAdd && (
        <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-purple-800 dark:text-purple-300">New Memory</span>
            <button onClick={() => setShowAdd(false)} className="text-purple-400 hover:text-purple-600">
              <X className="h-4 w-4" />
            </button>
          </div>
          <textarea
            value={newSummary}
            onChange={(e) => setNewSummary(e.target.value)}
            placeholder={`What should the AI remember about ${entityName}?`}
            className="w-full px-3 py-2 text-sm border border-purple-200 dark:border-purple-700 rounded-lg bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-purple-500 resize-none"
            rows={3}
          />
          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-2">
              <label className="text-xs text-purple-600 dark:text-purple-400">Confidence:</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={newConfidence}
                onChange={(e) => setNewConfidence(parseFloat(e.target.value))}
                className="w-24 h-1.5 accent-purple-600"
              />
              <span className="text-xs text-purple-700 dark:text-purple-300 font-medium">
                {Math.round(newConfidence * 100)}%
              </span>
            </div>
            <button
              onClick={handleAdd}
              disabled={!newSummary.trim() || saving}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
            >
              {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
              Save
            </button>
          </div>
        </div>
      )}

      {/* Memory list */}
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-purple-400" />
        </div>
      ) : memories.length === 0 ? (
        <div className="text-center py-8 text-slate-400 dark:text-slate-500">
          <Brain className="h-10 w-10 mx-auto mb-2 opacity-30" />
          <p className="text-sm">No AI memories for {entityName}</p>
          <p className="text-xs mt-1">Add memories to help the AI remember key insights</p>
        </div>
      ) : (
        <div className="space-y-2">
          {memories.map((m) => (
            <div
              key={m.id}
              className="bg-white dark:bg-slate-800 rounded-lg p-3 border border-slate-200 dark:border-slate-700 group hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm text-slate-700 dark:text-slate-300 flex-1">{m.summary}</p>
                <button
                  onClick={() => handleDelete(m.id)}
                  className="p-1 rounded text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                  title="Delete memory"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
              <div className="flex items-center gap-3 mt-2">
                <ConfidenceBadge value={m.confidence} />
                <span className="text-[10px] text-slate-400">
                  {m.last_updated ? new Date(m.last_updated).toLocaleDateString() : ''}
                </span>
                {m.source_interaction && (
                  <span className="text-[10px] text-slate-400 capitalize">{m.source_interaction}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
