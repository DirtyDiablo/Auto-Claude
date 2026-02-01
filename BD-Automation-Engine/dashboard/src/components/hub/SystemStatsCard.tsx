/**
 * System Stats Card Component
 *
 * Real-time stats display with auto-refresh and health indicator.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  RefreshCw,
  Database,
  Users,
  Building2,
  FileText,
  Phone,
  Briefcase,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { hubApiClient, type HubStats, type HubHealth } from '../../services/hubApi';

interface SystemStatsCardProps {
  autoRefreshInterval?: number; // in seconds, 0 to disable
  showHealth?: boolean;
  compact?: boolean;
}

export function SystemStatsCard({
  autoRefreshInterval = 30,
  showHealth = true,
  compact = false,
}: SystemStatsCardProps) {
  const [stats, setStats] = useState<HubStats | null>(null);
  const [health, setHealth] = useState<HubHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsData, healthData] = await Promise.all([
        hubApiClient.getStats(),
        showHealth ? hubApiClient.getHealth() : Promise.resolve(null),
      ]);

      setStats(statsData);
      setHealth(healthData);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stats');
    } finally {
      setLoading(false);
    }
  }, [showHealth]);

  useEffect(() => {
    fetchData();

    if (autoRefreshInterval > 0) {
      const interval = setInterval(fetchData, autoRefreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [fetchData, autoRefreshInterval]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'degraded':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <XCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-red-100 text-red-800';
    }
  };

  if (compact) {
    return (
      <div className="flex items-center gap-4 px-4 py-2 bg-white rounded-lg shadow-sm border border-slate-200">
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
        ) : error ? (
          <div className="flex items-center gap-2 text-red-500">
            <XCircle className="h-4 w-4" />
            <span className="text-sm">Hub offline</span>
          </div>
        ) : (
          <>
            {health && (
              <div className="flex items-center gap-1">
                {getStatusIcon(health.status)}
                <span className="text-sm font-medium capitalize">{health.status}</span>
              </div>
            )}
            <div className="h-4 w-px bg-slate-200" />
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <span className="flex items-center gap-1">
                <Users className="h-3.5 w-3.5" />
                {stats?.collections.contacts.toLocaleString()}
              </span>
              <span className="flex items-center gap-1">
                <Building2 className="h-3.5 w-3.5" />
                {stats?.collections.programs.toLocaleString()}
              </span>
              <span className="flex items-center gap-1">
                <Database className="h-3.5 w-3.5" />
                {stats?.total_records.toLocaleString()}
              </span>
            </div>
            <button
              onClick={fetchData}
              disabled={loading}
              className="p-1 hover:bg-slate-100 rounded transition-colors"
            >
              <RefreshCw className={`h-3.5 w-3.5 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-100">
            <Activity className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">Hub Status</h3>
            <p className="text-sm text-slate-500">Real-time system statistics</p>
          </div>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="p-2 hover:bg-white rounded-lg transition-colors"
        >
          <RefreshCw className={`h-4 w-4 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        {loading && !stats ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <XCircle className="h-8 w-8 text-red-400 mb-2" />
            <p className="text-sm text-slate-600">Hub API not available</p>
            <p className="text-xs text-slate-400 mt-1">{error}</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Health Status */}
            {health && showHealth && (
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <span className="text-sm text-slate-500">Status</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${getStatusColor(health.status)}`}>
                  {getStatusIcon(health.status)}
                  {health.status.charAt(0).toUpperCase() + health.status.slice(1)}
                </span>
              </div>
            )}

            {/* Collection Stats */}
            {stats && (
              <div className="grid grid-cols-2 gap-3">
                <StatItem
                  icon={Users}
                  label="Contacts"
                  value={stats.collections.contacts}
                  color="blue"
                />
                <StatItem
                  icon={Building2}
                  label="Programs"
                  value={stats.collections.programs}
                  color="purple"
                />
                <StatItem
                  icon={FileText}
                  label="Documents"
                  value={stats.collections.documents}
                  color="cyan"
                />
                <StatItem
                  icon={Phone}
                  label="Activities"
                  value={stats.collections.activities}
                  color="green"
                />
                <StatItem
                  icon={Briefcase}
                  label="Jobs"
                  value={stats.collections.jobs}
                  color="orange"
                />
                <StatItem
                  icon={Database}
                  label="Total"
                  value={stats.total_records}
                  color="slate"
                />
              </div>
            )}

            {/* Services Status */}
            {health && health.services && (
              <div className="pt-3 border-t border-slate-100">
                <p className="text-xs font-medium text-slate-500 mb-2">Services</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(health.services).map(([service, active]) => (
                    <span
                      key={service}
                      className={`px-2 py-1 rounded text-xs flex items-center gap-1 ${
                        active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {active ? (
                        <CheckCircle2 className="h-3 w-3" />
                      ) : (
                        <XCircle className="h-3 w-3" />
                      )}
                      {service}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Last Refresh */}
            {lastRefresh && (
              <div className="pt-3 border-t border-slate-100 text-xs text-slate-400 text-center">
                Last updated: {lastRefresh.toLocaleTimeString()}
                {autoRefreshInterval > 0 && ` (auto-refresh: ${autoRefreshInterval}s)`}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StatItem({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
  color: string;
}) {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-600',
    purple: 'bg-purple-100 text-purple-600',
    cyan: 'bg-cyan-100 text-cyan-600',
    green: 'bg-green-100 text-green-600',
    orange: 'bg-orange-100 text-orange-600',
    slate: 'bg-slate-100 text-slate-600',
  };

  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-slate-50">
      <div className={`p-1.5 rounded ${colorClasses[color] || colorClasses.slate}`}>
        <Icon className="h-3.5 w-3.5" />
      </div>
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-sm font-semibold text-slate-900">{value.toLocaleString()}</p>
      </div>
    </div>
  );
}

export default SystemStatsCard;
