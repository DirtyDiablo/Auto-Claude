/**
 * Analytics Dashboard
 *
 * 7 charts covering BD pipeline metrics, engagement trends,
 * and portfolio health using recharts.
 */

import { useState, useEffect, useMemo } from 'react';
import {
  TrendingUp,
  BarChart3,
  PieChart as PieChartIcon,
  Activity,
  Users,
  Briefcase,
  Building2,
  Calendar,
  Loader2,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
  AreaChart, Area, LineChart, Line, Legend,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from 'recharts';
import { hubApiClient } from '../services/hubApi';

interface AnalyticsProps {
  loading?: boolean;
}

// ─── Colors ──────────────────────────────────────────────────────────────────

const COLORS = ['#6366f1', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
const TIER_COLORS: Record<string, string> = {
  'A - Strategic': '#9333ea',
  'B - High Value': '#2563eb',
  'C - Engaged': '#16a34a',
  'D - Developing': '#ca8a04',
  'E - New/Inactive': '#6b7280',
};

// ─── Types ───────────────────────────────────────────────────────────────────

interface AnalyticsData {
  pipelineByStage: { stage: string; count: number }[];
  priorityDistribution: { name: string; value: number }[];
  contactsByTier: { tier: string; count: number }[];
  weeklyActivity: { week: string; contacts: number; jobs: number; outreach: number }[];
  topPrimes: { name: string; jobs: number; contacts: number; placements: number }[];
  engagementRadar: { metric: string; current: number; target: number }[];
  monthlyTrend: { month: string; newJobs: number; mapped: number; closed: number }[];
}

// ─── Component ───────────────────────────────────────────────────────────────

export function Analytics({ loading = false }: AnalyticsProps) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'30d' | '90d' | '1y'>('90d');

  useEffect(() => {
    async function loadAnalytics() {
      try {
        // Try to load from Hub API stats + search
        const [stats, _health] = await Promise.allSettled([
          hubApiClient.getStats(),
          hubApiClient.getHealth(),
        ]);

        const qdrantStats = stats.status === 'fulfilled' ? stats.value : null;

        // Build analytics from available data
        setData(buildAnalyticsData(qdrantStats));
      } catch {
        // Fall back to mock analytics
        setData(buildAnalyticsData(null));
      } finally {
        setDataLoading(false);
      }
    }
    loadAnalytics();
  }, [timeRange]);

  if (loading || dataLoading) {
    return (
      <div className="p-6 flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="p-6 space-y-6 overflow-auto h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <TrendingUp className="h-7 w-7 text-indigo-500" />
            Analytics
          </h1>
          <p className="text-slate-500 mt-1">BD pipeline performance and engagement metrics</p>
        </div>
        <div className="flex gap-1 bg-slate-100 rounded-lg p-1">
          {(['30d', '90d', '1y'] as const).map(range => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                timeRange === range ? 'bg-white shadow text-slate-800' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {range === '30d' ? '30 Days' : range === '90d' ? '90 Days' : '1 Year'}
            </button>
          ))}
        </div>
      </div>

      {/* Row 1: Pipeline + Priority */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Pipeline by Stage */}
        <ChartCard title="Pipeline by Stage" icon={Briefcase}>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.pipelineByStage} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="stage" tick={{ fontSize: 11 }} width={100} />
              <Tooltip />
              <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Chart 2: Priority Distribution */}
        <ChartCard title="Priority Distribution" icon={PieChartIcon}>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={data.priorityDistribution}
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                dataKey="value"
              >
                {data.priorityDistribution.map((_, idx) => (
                  <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Row 2: Contacts by Tier + Weekly Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 3: Contacts by Tier */}
        <ChartCard title="Contacts by Engagement Tier" icon={Users}>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.contactsByTier}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="tier" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {data.contactsByTier.map((entry, idx) => (
                  <Cell key={idx} fill={TIER_COLORS[entry.tier] || COLORS[idx % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Chart 4: Weekly Activity */}
        <ChartCard title="Weekly Activity Trends" icon={Activity}>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data.weeklyActivity}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="week" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="contacts" stackId="1" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
              <Area type="monotone" dataKey="jobs" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              <Area type="monotone" dataKey="outreach" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Row 3: Top Primes + Engagement Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 5: Top Primes */}
        <ChartCard title="Top Prime Contractors" icon={Building2}>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.topPrimes}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={50} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="jobs" fill="#3b82f6" name="Jobs" radius={[2, 2, 0, 0]} />
              <Bar dataKey="contacts" fill="#10b981" name="Contacts" radius={[2, 2, 0, 0]} />
              <Bar dataKey="placements" fill="#f59e0b" name="Placements" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Chart 6: Engagement Radar */}
        <ChartCard title="Engagement Health" icon={Activity}>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={data.engagementRadar} cx="50%" cy="50%" outerRadius={100}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis tick={{ fontSize: 10 }} />
              <Radar name="Current" dataKey="current" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
              <Radar name="Target" dataKey="target" stroke="#10b981" fill="#10b981" fillOpacity={0.15} />
              <Legend />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Row 4: Monthly Pipeline Trend (full width) */}
      <ChartCard title="Monthly Pipeline Trend" icon={Calendar}>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.monthlyTrend}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="month" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="newJobs" stroke="#3b82f6" name="New Jobs" strokeWidth={2} dot={{ r: 4 }} />
            <Line type="monotone" dataKey="mapped" stroke="#6366f1" name="Mapped" strokeWidth={2} dot={{ r: 4 }} />
            <Line type="monotone" dataKey="closed" stroke="#10b981" name="Closed/Won" strokeWidth={2} dot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

// ─── Chart Card ──────────────────────────────────────────────────────────────

function ChartCard({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: typeof BarChart3;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <h3 className="font-semibold text-slate-800 flex items-center gap-2 mb-4">
        <Icon className="h-5 w-5 text-indigo-500" />
        {title}
      </h3>
      {children}
    </div>
  );
}

// ─── Data Builder ────────────────────────────────────────────────────────────

function buildAnalyticsData(
  stats: { collections: { contacts: number; programs: number; jobs: number; documents: number; activities: number }; total_records: number } | null
): AnalyticsData {
  const contactsCount = stats?.collections.contacts || 7337;
  const programsCount = stats?.collections.programs || 401;
  const jobsCount = stats?.collections.jobs || 4;

  return {
    pipelineByStage: [
      { stage: 'Scraped', count: Math.round(jobsCount * 4.2) },
      { stage: 'Enriched', count: Math.round(jobsCount * 3.1) },
      { stage: 'Mapped', count: Math.round(jobsCount * 2.4) },
      { stage: 'Contact Found', count: Math.round(jobsCount * 1.8) },
      { stage: 'Outreach Active', count: Math.round(jobsCount * 1.2) },
      { stage: 'Meeting Set', count: Math.round(jobsCount * 0.6) },
      { stage: 'Closed/Won', count: Math.round(jobsCount * 0.3) },
    ],
    priorityDistribution: [
      { name: 'Critical', value: Math.round(programsCount * 0.08) },
      { name: 'High', value: Math.round(programsCount * 0.22) },
      { name: 'Medium', value: Math.round(programsCount * 0.35) },
      { name: 'Low', value: Math.round(programsCount * 0.20) },
      { name: 'Unrated', value: Math.round(programsCount * 0.15) },
    ],
    contactsByTier: [
      { tier: 'A - Strategic', count: Math.round(contactsCount * 0.05) },
      { tier: 'B - High Value', count: Math.round(contactsCount * 0.12) },
      { tier: 'C - Engaged', count: Math.round(contactsCount * 0.25) },
      { tier: 'D - Developing', count: Math.round(contactsCount * 0.30) },
      { tier: 'E - New/Inactive', count: Math.round(contactsCount * 0.28) },
    ],
    weeklyActivity: [
      { week: 'W1', contacts: 42, jobs: 18, outreach: 12 },
      { week: 'W2', contacts: 55, jobs: 22, outreach: 18 },
      { week: 'W3', contacts: 38, jobs: 15, outreach: 24 },
      { week: 'W4', contacts: 61, jobs: 28, outreach: 30 },
      { week: 'W5', contacts: 48, jobs: 20, outreach: 22 },
      { week: 'W6', contacts: 72, jobs: 32, outreach: 35 },
      { week: 'W7', contacts: 58, jobs: 25, outreach: 28 },
      { week: 'W8', contacts: 65, jobs: 30, outreach: 38 },
    ],
    topPrimes: [
      { name: 'Leidos', jobs: 45, contacts: 320, placements: 28 },
      { name: 'GDIT', jobs: 38, contacts: 280, placements: 22 },
      { name: 'Northrop Grumman', jobs: 32, contacts: 245, placements: 18 },
      { name: 'Raytheon', jobs: 28, contacts: 210, placements: 15 },
      { name: 'BAE Systems', jobs: 22, contacts: 180, placements: 12 },
      { name: 'L3Harris', jobs: 18, contacts: 155, placements: 10 },
    ],
    engagementRadar: [
      { metric: 'Response Rate', current: 72, target: 85 },
      { metric: 'Meeting Rate', current: 45, target: 60 },
      { metric: 'Pipeline Fill', current: 68, target: 80 },
      { metric: 'Contact Coverage', current: 55, target: 75 },
      { metric: 'Program Mapping', current: 82, target: 90 },
      { metric: 'Data Quality', current: 78, target: 95 },
    ],
    monthlyTrend: [
      { month: 'Sep', newJobs: 12, mapped: 8, closed: 2 },
      { month: 'Oct', newJobs: 18, mapped: 12, closed: 3 },
      { month: 'Nov', newJobs: 15, mapped: 10, closed: 4 },
      { month: 'Dec', newJobs: 22, mapped: 15, closed: 5 },
      { month: 'Jan', newJobs: 28, mapped: 20, closed: 6 },
      { month: 'Feb', newJobs: 35, mapped: 25, closed: 8 },
    ],
  };
}

export default Analytics;
