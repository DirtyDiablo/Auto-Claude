/**
 * System Health Page
 *
 * System monitoring dashboard for Hub API connection status,
 * collection stats, cache metrics, and service health.
 */

import { useState, useEffect } from 'react';
import {
  Activity,
  Server,
  Database,
  Zap,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  HardDrive,
  Cpu,
  Users,
  Building2,
  FileText,
  Phone,
  Briefcase,
  Network,
  Brain,
  Loader2,
} from 'lucide-react';
import { SystemStatsCard } from '../components/hub/SystemStatsCard';
import {
  useHubHealth,
  useHubStats,
  useHubCacheStats,
  useHubGraphStats,
} from '../hooks/useHubApi';
import { getHubApiUrl } from '../services/hubApi';

const REFRESH_INTERVALS = [
  { value: 0, label: 'Manual' },
  { value: 10, label: '10 seconds' },
  { value: 30, label: '30 seconds' },
  { value: 60, label: '1 minute' },
  { value: 300, label: '5 minutes' },
];

export function SystemHealth() {
  const [refreshInterval, setRefreshInterval] = useState(30);

  const { data: health, loading: healthLoading, error: healthError, refetch: refetchHealth } = useHubHealth(
    refreshInterval * 1000
  );
  const { data: stats, loading: statsLoading, error: statsError, refetch: refetchStats } = useHubStats(
    refreshInterval * 1000
  );
  const { data: cacheStats, loading: cacheLoading, error: cacheError, refetch: refetchCache } = useHubCacheStats();
  const { data: graphStats, loading: graphLoading, error: graphError, refetch: refetchGraph } = useHubGraphStats();

  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Update last refresh time
  useEffect(() => {
    if (!healthLoading && !statsLoading) {
      setLastRefresh(new Date());
    }
  }, [healthLoading, statsLoading]);

  const handleRefreshAll = () => {
    refetchHealth();
    refetchStats();
    refetchCache();
    refetchGraph();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600';
      case 'degraded':
        return 'text-yellow-600';
      default:
        return 'text-red-600';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100';
      case 'degraded':
        return 'bg-yellow-100';
      default:
        return 'bg-red-100';
    }
  };

  const isConnected = health?.status === 'healthy' || health?.status === 'degraded';

  return (
    <div className="p-6 h-full overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-slate-700 to-slate-900">
              <Activity className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">System Health</h1>
              <p className="text-slate-500">
                Monitor Hub API status and performance
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Refresh Interval */}
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-slate-400" />
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                className="text-sm border border-slate-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500"
              >
                {REFRESH_INTERVALS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Refresh Button */}
            <button
              onClick={handleRefreshAll}
              disabled={healthLoading || statsLoading}
              className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 disabled:opacity-50 transition-colors"
            >
              <RefreshCw className={`h-4 w-4 ${healthLoading || statsLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Last Updated */}
        <p className="text-xs text-slate-400 mt-2">
          Last updated: {lastRefresh.toLocaleTimeString()}
        </p>
      </div>

      {/* Connection Status Banner */}
      <div
        className={`mb-6 p-4 rounded-xl flex items-center justify-between ${
          isConnected ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}
      >
        <div className="flex items-center gap-3">
          {isConnected ? (
            <CheckCircle2 className="h-6 w-6 text-green-600" />
          ) : (
            <XCircle className="h-6 w-6 text-red-600" />
          )}
          <div>
            <p className={`font-medium ${isConnected ? 'text-green-800' : 'text-red-800'}`}>
              {isConnected ? 'Hub API Connected' : 'Hub API Disconnected'}
            </p>
            <p className={`text-sm ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
              {getHubApiUrl()}
            </p>
          </div>
        </div>
        {health && isConnected && (
          <div className={`px-3 py-1.5 rounded-lg ${getStatusBg(health.status)}`}>
            <span className={`font-medium capitalize ${getStatusColor(health.status)}`}>
              {health.status}
            </span>
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Collection Stats */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-600" />
              <span className="font-semibold text-slate-900">Collection Stats</span>
            </div>
          </div>
          <div className="p-4">
            {statsLoading && !stats ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
              </div>
            ) : statsError ? (
              <div className="text-center py-8 text-red-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                <p className="text-sm">{statsError}</p>
              </div>
            ) : stats ? (
              <div className="space-y-3">
                <CollectionStat icon={Users} label="Contacts" value={stats.collections.contacts} />
                <CollectionStat icon={Building2} label="Programs" value={stats.collections.programs} />
                <CollectionStat icon={FileText} label="Documents" value={stats.collections.documents} />
                <CollectionStat icon={Phone} label="Activities" value={stats.collections.activities} />
                <CollectionStat icon={Briefcase} label="Jobs" value={stats.collections.jobs} />
                <div className="pt-3 border-t border-slate-100">
                  <CollectionStat icon={Database} label="Total Records" value={stats.total_records} highlight />
                </div>
              </div>
            ) : null}
          </div>
        </div>

        {/* Service Status */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50">
            <div className="flex items-center gap-2">
              <Server className="h-5 w-5 text-purple-600" />
              <span className="font-semibold text-slate-900">Services</span>
            </div>
          </div>
          <div className="p-4">
            {healthLoading && !health ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
              </div>
            ) : healthError ? (
              <div className="text-center py-8 text-red-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                <p className="text-sm">{healthError}</p>
              </div>
            ) : health?.services ? (
              <div className="space-y-3">
                <ServiceStatus
                  icon={Database}
                  label="Qdrant Vector DB"
                  active={health.services.qdrant}
                />
                <ServiceStatus
                  icon={Brain}
                  label="Memory System"
                  active={health.services.memory}
                />
                <ServiceStatus
                  icon={Network}
                  label="Knowledge Graph"
                  active={health.services.graph}
                />
                <ServiceStatus
                  icon={Cpu}
                  label="BD Agents"
                  active={health.services.agents}
                />
                <div className="pt-3 border-t border-slate-100">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-500">Version</span>
                    <span className="text-sm font-medium text-slate-900">{health.version}</span>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-sm text-slate-500">Uptime</span>
                    <span className="text-sm font-medium text-slate-900">
                      {formatUptime(health.uptime)}
                    </span>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>

        {/* Cache Stats */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50">
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-amber-600" />
              <span className="font-semibold text-slate-900">Cache Performance</span>
            </div>
          </div>
          <div className="p-4">
            {cacheLoading && !cacheStats ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
              </div>
            ) : cacheError ? (
              <div className="text-center py-8 text-red-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                <p className="text-sm">{cacheError}</p>
              </div>
            ) : cacheStats ? (
              <div className="space-y-4">
                {/* Hit Rate */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-600">Hit Rate</span>
                    <span className="text-sm font-medium text-slate-900">
                      {(cacheStats.hit_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        cacheStats.hit_rate >= 0.8
                          ? 'bg-green-500'
                          : cacheStats.hit_rate >= 0.5
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${cacheStats.hit_rate * 100}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-xs text-slate-500">Total Requests</p>
                    <p className="text-lg font-semibold text-slate-900">
                      {cacheStats.total_requests.toLocaleString()}
                    </p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-xs text-slate-500">Cache Entries</p>
                    <p className="text-lg font-semibold text-slate-900">
                      {cacheStats.entries.toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <HardDrive className="h-4 w-4 text-slate-400" />
                    <span className="text-sm text-slate-600">Cache Size</span>
                  </div>
                  <span className="text-sm font-medium text-slate-900">
                    {formatBytes(cacheStats.cache_size)}
                  </span>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* Graph Stats */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-slate-50">
          <div className="flex items-center gap-2">
            <Network className="h-5 w-5 text-cyan-600" />
            <span className="font-semibold text-slate-900">Knowledge Graph Stats</span>
          </div>
        </div>
        <div className="p-4">
          {graphLoading && !graphStats ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
            </div>
          ) : graphError ? (
            <div className="text-center py-8 text-red-500">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              <p className="text-sm">{graphError}</p>
            </div>
          ) : graphStats ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-slate-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-slate-900">
                  {graphStats.total_nodes.toLocaleString()}
                </p>
                <p className="text-sm text-slate-500">Total Nodes</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-slate-900">
                  {graphStats.total_edges.toLocaleString()}
                </p>
                <p className="text-sm text-slate-500">Total Edges</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg">
                <p className="text-xs font-medium text-slate-500 mb-2">Node Types</p>
                <div className="space-y-1">
                  {Object.entries(graphStats.node_types).slice(0, 4).map(([type, count]) => (
                    <div key={type} className="flex justify-between text-sm">
                      <span className="text-slate-600 capitalize">{type}</span>
                      <span className="font-medium text-slate-900">{(count as number).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg">
                <p className="text-xs font-medium text-slate-500 mb-2">Edge Types</p>
                <div className="space-y-1">
                  {Object.entries(graphStats.edge_types).slice(0, 4).map(([type, count]) => (
                    <div key={type} className="flex justify-between text-sm">
                      <span className="text-slate-600 capitalize">{type}</span>
                      <span className="font-medium text-slate-900">{(count as number).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

// Helper Components
function CollectionStat({
  icon: Icon,
  label,
  value,
  highlight = false,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
  highlight?: boolean;
}) {
  return (
    <div className={`flex items-center justify-between p-2 rounded-lg ${highlight ? 'bg-blue-50' : ''}`}>
      <div className="flex items-center gap-2">
        <Icon className={`h-4 w-4 ${highlight ? 'text-blue-600' : 'text-slate-400'}`} />
        <span className={`text-sm ${highlight ? 'font-medium text-blue-800' : 'text-slate-600'}`}>
          {label}
        </span>
      </div>
      <span className={`font-semibold ${highlight ? 'text-blue-900' : 'text-slate-900'}`}>
        {value.toLocaleString()}
      </span>
    </div>
  );
}

function ServiceStatus({
  icon: Icon,
  label,
  active,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  active: boolean;
}) {
  return (
    <div className="flex items-center justify-between p-2">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-slate-400" />
        <span className="text-sm text-slate-600">{label}</span>
      </div>
      <div className="flex items-center gap-1.5">
        {active ? (
          <>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <span className="text-sm text-green-600">Active</span>
          </>
        ) : (
          <>
            <XCircle className="h-4 w-4 text-red-500" />
            <span className="text-sm text-red-600">Inactive</span>
          </>
        )}
      </div>
    </div>
  );
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export default SystemHealth;
