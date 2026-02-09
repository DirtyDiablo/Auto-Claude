import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import { DollarSign, Zap, TrendingUp, Loader2, Database } from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

interface CostData {
  daily: Array<{ date: string; input_tokens: number; output_tokens: number; cost_usd: number; queries: number }>;
  by_endpoint: Array<{ endpoint: string; cost_usd: number }>;
  recent_queries: Array<{
    timestamp: string;
    endpoint: string;
    model: string;
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
  }>;
  summary: {
    total_cost_usd: number;
    total_input_tokens: number;
    total_output_tokens: number;
    total_queries: number;
    projected_30d_usd: number;
    period_days: number;
  };
}

const PIE_COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4', '#f59e0b', '#ef4444', '#22c55e', '#ec4899', '#6366f1'];

function CostStatCard({ title, value, subtitle, icon: Icon }: {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-900/30">
          <Icon className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400">{title}</p>
          <p className="text-lg font-bold text-slate-900 dark:text-slate-100">{value}</p>
          <p className="text-[10px] text-slate-400">{subtitle}</p>
        </div>
      </div>
    </div>
  );
}

export function LLMCostsTab() {
  const [data, setData] = useState<CostData | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    let mounted = true;
    async function fetch() {
      setLoading(true);
      try {
        const result = await hubApiClient.getLLMCosts(days);
        if (mounted) setData(result);
      } catch {
        // API not available
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetch();
    return () => { mounted = false; };
  }, [days]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-12 text-slate-400">
        <DollarSign className="h-10 w-10 mx-auto mb-2 opacity-30" />
        <p className="text-sm">No cost data available</p>
        <p className="text-xs mt-1">LLM usage will be tracked as queries are made</p>
      </div>
    );
  }

  const { summary } = data;

  return (
    <div className="space-y-6">
      {/* Period selector */}
      <div className="flex items-center gap-2">
        {[7, 14, 30, 90].map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={`px-3 py-1 text-xs rounded-lg transition-colors ${
              days === d
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'
            }`}
          >
            {d}d
          </button>
        ))}
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <CostStatCard
          title="Total Cost"
          value={`$${summary.total_cost_usd.toFixed(2)}`}
          subtitle={`Last ${summary.period_days} days`}
          icon={DollarSign}
        />
        <CostStatCard
          title="Total Queries"
          value={summary.total_queries.toLocaleString()}
          subtitle={`${(summary.total_queries / Math.max(summary.period_days, 1)).toFixed(1)}/day avg`}
          icon={Zap}
        />
        <CostStatCard
          title="Total Tokens"
          value={((summary.total_input_tokens + summary.total_output_tokens) / 1000).toFixed(0) + 'K'}
          subtitle={`In: ${(summary.total_input_tokens / 1000).toFixed(0)}K / Out: ${(summary.total_output_tokens / 1000).toFixed(0)}K`}
          icon={Database}
        />
        <CostStatCard
          title="30-Day Projected"
          value={`$${summary.projected_30d_usd.toFixed(2)}`}
          subtitle="Based on recent usage"
          icon={TrendingUp}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Daily token consumption */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">Daily Token Usage</h4>
          {data.daily.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data.daily}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(v) => v.slice(5)} />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`} />
                <Tooltip
                  formatter={(value) => [`${(Number(value) / 1000).toFixed(1)}K`]}
                  labelStyle={{ fontSize: 11 }}
                  contentStyle={{ fontSize: 11 }}
                />
                <Bar dataKey="input_tokens" name="Input" fill="#3b82f6" stackId="a" />
                <Bar dataKey="output_tokens" name="Output" fill="#8b5cf6" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-slate-400 text-sm">No data</div>
          )}
        </div>

        {/* Cost by endpoint */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">Cost by Endpoint</h4>
          {data.by_endpoint.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={data.by_endpoint}
                  dataKey="cost_usd"
                  nameKey="endpoint"
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={75}
                  label={({ name, percent }) => `${name ?? ''} (${((percent ?? 0) * 100).toFixed(0)}%)`}
                  labelLine={false}
                >
                  {data.by_endpoint.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Tooltip formatter={(value) => `$${Number(value).toFixed(4)}`} contentStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-slate-400 text-sm">No data</div>
          )}
        </div>
      </div>

      {/* Recent queries table */}
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
        <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">
          Recent Queries (Last 50)
        </h4>
        {data.recent_queries.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left py-2 px-2 text-slate-500 font-medium">Time</th>
                  <th className="text-left py-2 px-2 text-slate-500 font-medium">Endpoint</th>
                  <th className="text-left py-2 px-2 text-slate-500 font-medium">Model</th>
                  <th className="text-right py-2 px-2 text-slate-500 font-medium">Input</th>
                  <th className="text-right py-2 px-2 text-slate-500 font-medium">Output</th>
                  <th className="text-right py-2 px-2 text-slate-500 font-medium">Cost</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_queries.slice().reverse().map((q, i) => (
                  <tr key={i} className="border-b border-slate-100 dark:border-slate-700/50">
                    <td className="py-1.5 px-2 text-slate-400">{new Date(q.timestamp).toLocaleString()}</td>
                    <td className="py-1.5 px-2 text-slate-700 dark:text-slate-300 font-mono">{q.endpoint}</td>
                    <td className="py-1.5 px-2 text-slate-500">{q.model}</td>
                    <td className="py-1.5 px-2 text-right text-slate-600 dark:text-slate-400">{q.input_tokens.toLocaleString()}</td>
                    <td className="py-1.5 px-2 text-right text-slate-600 dark:text-slate-400">{q.output_tokens.toLocaleString()}</td>
                    <td className="py-1.5 px-2 text-right text-slate-800 dark:text-slate-200 font-medium">${q.cost_usd.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-400 text-center py-6">No queries recorded yet</p>
        )}
      </div>
    </div>
  );
}
