import { useState, useEffect, useCallback } from 'react';
import { ShieldCheck, AlertTriangle, CheckCircle, Clock, RefreshCw } from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

interface QAStats {
  total_items: number;
  pending: number;
  reviewed: number;
}

interface ReviewItem {
  job_id: string;
  added_at: string;
  status: string;
  confidence: number;
  review_reasons: string[];
  original_program: string;
  reviewed: boolean;
  review_action?: string;
  root_cause?: {
    type: string;
    severity: string;
    description: string;
    recommended_fix: string;
    auto_fixable: boolean;
  };
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  high: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  low: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
};

export function QADashboard() {
  const [stats, setStats] = useState<QAStats | null>(null);
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'pending'>('pending');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, queueRes] = await Promise.all([
        hubApiClient.getQAStats(),
        hubApiClient.getQAReviewQueue({ limit: 50, status: filter === 'pending' ? 'pending' : undefined }),
      ]);
      setStats(statsRes);
      setItems(queueRes.items as ReviewItem[]);
      setTotal(queueRes.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load QA data');
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleResolve = async (itemId: string, action: 'approve' | 'reject' | 'fix') => {
    setActionLoading(itemId);
    try {
      await hubApiClient.resolveQAItem(itemId, action);
      await fetchData();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Action failed');
    } finally {
      setActionLoading(null);
    }
  };

  const approvalRate = stats && stats.total_items > 0
    ? ((stats.reviewed / stats.total_items) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="h-full overflow-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ShieldCheck className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">QA Dashboard</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">Engine 6 quality assurance review queue</p>
          </div>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-800 rounded-lg p-5 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <ShieldCheck className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Total Items</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{stats?.total_items ?? '-'}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg p-5 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
              <Clock className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Pending Review</p>
              <p className="text-2xl font-bold text-yellow-600">{stats?.pending ?? '-'}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg p-5 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Reviewed</p>
              <p className="text-2xl font-bold text-green-600">{stats?.reviewed ?? '-'}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg p-5 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Review Rate</p>
              <p className="text-2xl font-bold text-purple-600">{approvalRate}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setFilter('pending')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            filter === 'pending'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600'
          }`}
        >
          Pending ({stats?.pending ?? 0})
        </button>
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            filter === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600'
          }`}
        >
          All ({stats?.total_items ?? 0})
        </button>
      </div>

      {/* Review Queue Table */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900/50">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Job ID</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Program</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Confidence</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Severity</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Issue</th>
                <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {items.length === 0 && !loading && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500 dark:text-slate-400">
                    {filter === 'pending' ? 'No pending items' : 'No items in queue'}
                  </td>
                </tr>
              )}
              {items.map((item) => (
                <tr key={item.job_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                  <td className="px-4 py-3 font-mono text-xs text-slate-700 dark:text-slate-300 max-w-[200px] truncate">
                    {item.job_id}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{item.original_program || '-'}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`font-medium ${item.confidence >= 0.7 ? 'text-green-600' : item.confidence >= 0.5 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {(item.confidence * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {item.root_cause && (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${SEVERITY_COLORS[item.root_cause.severity] || ''}`}>
                        {item.root_cause.severity}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600 dark:text-slate-400 max-w-[250px] truncate">
                    {item.root_cause?.description || item.review_reasons?.join(', ') || '-'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {item.reviewed ? (
                      <span className="text-xs text-green-600 font-medium">{item.review_action}</span>
                    ) : (
                      <div className="flex gap-1 justify-center">
                        <button
                          onClick={() => handleResolve(item.job_id, 'approve')}
                          disabled={actionLoading === item.job_id}
                          className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 disabled:opacity-50"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleResolve(item.job_id, 'reject')}
                          disabled={actionLoading === item.job_id}
                          className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
                        >
                          Reject
                        </button>
                        {item.root_cause?.auto_fixable && (
                          <button
                            onClick={() => handleResolve(item.job_id, 'fix')}
                            disabled={actionLoading === item.job_id}
                            className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
                          >
                            Auto-Fix
                          </button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {total > items.length && (
          <div className="px-4 py-3 border-t border-slate-100 dark:border-slate-700 text-sm text-slate-500">
            Showing {items.length} of {total} items
          </div>
        )}
      </div>
    </div>
  );
}
