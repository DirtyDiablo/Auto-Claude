import { useState, useEffect, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Briefcase, Building2, Users, Factory, TrendingUp, AlertCircle, Server, CheckCircle2, Newspaper, Loader2, AlertTriangle, Sparkles, RefreshCw, Target, Shield } from 'lucide-react';
import type { CorrelationSummary, TabId } from '../types';
import { useHubConnection, useHubStats } from '../hooks/useHubApi';
import { AnimatedCounter } from '../components/ui/AnimatedCounter';
import { SkeletonHubStats } from '../components/ui/Skeleton';
import { CollectionHealthChart, WeeklyOutreachChart, SystemHealthCards } from '../components/KPICharts';
import { DataHealthBanner } from '../components/DataHealthBanner';
import { PageFreshnessBadge } from '../components/PageFreshnessBadge';
import { PipelineWidget } from '../components/PipelineWidget';
import { RecentAlertsCard, CompetitivePulseCard, UpcomingMeetingsCard } from '../components/ExecutiveInsightCards';
import { hubApiClient } from '../services/hubApi';

interface ExecutiveSummaryProps {
  summary: CorrelationSummary | null;
  loading: boolean;
  onTabChange?: (tab: TabId) => void;
}

const TIER_COLORS = ['#7c3aed', '#2563eb', '#0891b2', '#059669', '#ca8a04', '#6b7280'];
const PRIORITY_COLORS = { critical: '#dc2626', high: '#f97316', medium: '#eab308', low: '#22c55e' };

function StatCard({
  title,
  value,
  icon: Icon,
  color,
  subtitle,
}: {
  title: string;
  value: number | string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  subtitle?: string;
}) {
  const numericValue = typeof value === 'number' ? value : parseInt(value.toString(), 10);
  const isNumeric = !isNaN(numericValue);

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md dark:hover:shadow-lg dark:hover:shadow-blue-500/5 transition-all">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
          {isNumeric ? (
            <AnimatedCounter
              value={numericValue}
              className="mt-1 text-3xl font-bold text-slate-900 dark:text-slate-100"
              duration={1000}
            />
          ) : (
            <p className="mt-1 text-3xl font-bold text-slate-900 dark:text-slate-100">{value}</p>
          )}
          {subtitle && <p className="mt-1 text-sm text-slate-400 dark:text-slate-500">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-xl ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
    </div>
  );
}

function MatchRateCard({
  title,
  rate,
  matched,
  total,
}: {
  title: string;
  rate: number;
  matched: number;
  total: number;
}) {
  const getColorClass = (rate: number) => {
    if (rate >= 50) return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30';
    if (rate >= 25) return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/30';
    return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/30';
  };

  const getBarColor = (rate: number) => {
    if (rate >= 50) return 'bg-gradient-to-r from-green-400 to-green-600';
    if (rate >= 25) return 'bg-gradient-to-r from-yellow-400 to-yellow-600';
    return 'bg-gradient-to-r from-red-400 to-red-600';
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-600 dark:text-slate-300">{title}</span>
        <span className={`text-sm font-bold px-2 py-0.5 rounded ${getColorClass(rate)}`}>
          {rate.toFixed(1)}%
        </span>
      </div>
      <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2.5 overflow-hidden">
        <div
          className={`h-2.5 rounded-full transition-all duration-1000 ease-out ${getBarColor(rate)}`}
          style={{ width: `${Math.min(rate, 100)}%` }}
        />
      </div>
      <div className="mt-2 flex items-center justify-between">
        <p className="text-xs text-slate-400 dark:text-slate-500">
          <AnimatedCounter value={matched} className="font-medium" /> / {total.toLocaleString()} matched
        </p>
      </div>
    </div>
  );
}

export function ExecutiveSummary({ summary, loading, onTabChange }: ExecutiveSummaryProps) {
  // Hub connection status
  const { isConnected: hubConnected, isChecking: hubChecking } = useHubConnection();
  const { data: hubStats } = useHubStats(60000); // Refresh every minute

  // Claim tracker KPIs
  const [claimData, setClaimData] = useState<{
    total_programs: number;
    claimed: number;
    unclaimed: number;
    claim_rate: number;
  } | null>(null);

  useEffect(() => {
    hubApiClient.getClaimStatus()
      .then(data => setClaimData(data.summary))
      .catch(() => {/* Claim tracker not available yet */});
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-500">
        <AlertCircle className="h-12 w-12 mb-4" />
        <p>No data available. Run the correlation engine to generate data.</p>
      </div>
    );
  }

  const { statistics, priority_distribution, contacts_by_tier, top_programs_by_jobs } = summary;

  // Prepare tier data for pie chart
  const tierData = Object.entries(contacts_by_tier).map(([tier, count], index) => ({
    name: `Tier ${tier}`,
    value: count,
    color: TIER_COLORS[index] || TIER_COLORS[5],
  }));

  // Prepare priority data
  const priorityData = Object.entries(priority_distribution).map(([priority, count]) => ({
    name: priority.charAt(0).toUpperCase() + priority.slice(1),
    value: count,
    color: PRIORITY_COLORS[priority as keyof typeof PRIORITY_COLORS] || '#6b7280',
  }));

  // Prepare programs data for bar chart
  const programsData = top_programs_by_jobs.slice(0, 5).map((p) => ({
    name: p.name.length > 20 ? p.name.slice(0, 20) + '...' : p.name,
    contacts: p.contact_count,
    jobs: p.job_count,
  }));

  return (
    <div className="p-6 space-y-6 bg-slate-50 dark:bg-slate-900 min-h-full transition-colors">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Executive Summary</h1>
            <PageFreshnessBadge />
          </div>
          <p className="text-slate-500 dark:text-slate-400">
            BD Intelligence Overview &bull; Generated {new Date(summary.generated_at).toLocaleDateString()}
          </p>
        </div>
        <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
          <TrendingUp className="h-5 w-5" />
          <span className="text-sm font-medium">Live Data</span>
        </div>
      </div>

      {/* Data Health Banner + Pipeline Widget */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <DataHealthBanner />
        </div>
        <PipelineWidget onNavigate={() => onTabChange?.('pipelinestatus')} />
      </div>

      {/* Insight Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <RecentAlertsCard onNavigate={() => onTabChange?.('alerthistory')} />
        <CompetitivePulseCard onNavigate={() => onTabChange?.('competitive')} />
        <UpcomingMeetingsCard onNavigate={() => onTabChange?.('meetingcalendar')} />
      </div>

      {/* Hub API Status Card */}
      {hubChecking && (
        <SkeletonHubStats />
      )}
      {!hubChecking && hubConnected && (
        <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-xl shadow-sm p-4 mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-white/10">
                <Server className="h-5 w-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-white">Hub API</span>
                  <span className="flex items-center gap-1 text-xs text-green-400">
                    <CheckCircle2 className="h-3 w-3" /> Connected
                  </span>
                </div>
                {hubStats && (
                  <p className="text-xs text-slate-400">
                    {hubStats.total_records.toLocaleString()} total records indexed
                  </p>
                )}
              </div>
            </div>
            {hubStats && (
              <div className="flex gap-6">
                <div className="text-center">
                  <AnimatedCounter
                    value={hubStats.collections.contacts}
                    className="text-2xl font-bold text-white"
                    duration={1200}
                  />
                  <p className="text-xs text-slate-400">Contacts</p>
                </div>
                <div className="text-center">
                  <AnimatedCounter
                    value={hubStats.collections.programs}
                    className="text-2xl font-bold text-white"
                    duration={1000}
                  />
                  <p className="text-xs text-slate-400">Programs</p>
                </div>
                <div className="text-center">
                  <AnimatedCounter
                    value={hubStats.collections.documents}
                    className="text-2xl font-bold text-white"
                    duration={800}
                  />
                  <p className="text-xs text-slate-400">Documents</p>
                </div>
                <div className="text-center">
                  <AnimatedCounter
                    value={hubStats.collections.activities}
                    className="text-2xl font-bold text-white"
                    duration={900}
                  />
                  <p className="text-xs text-slate-400">Activities</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Jobs"
          value={statistics.total_jobs}
          icon={Briefcase}
          color="bg-blue-600"
          subtitle="In pipeline"
        />
        <StatCard
          title="Programs"
          value={statistics.total_programs}
          icon={Building2}
          color="bg-purple-600"
          subtitle="Active contracts"
        />
        <StatCard
          title="Contacts"
          value={statistics.total_contacts}
          icon={Users}
          color="bg-cyan-600"
          subtitle="Intelligence database"
        />
        <StatCard
          title="Contractors"
          value={statistics.total_contractors}
          icon={Factory}
          color="bg-orange-600"
          subtitle="Prime & subs"
        />
      </div>

      {/* Contract Claim KPIs */}
      {claimData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            title="Claimed Contracts"
            value={claimData.claimed}
            icon={Shield}
            color="bg-green-600"
            subtitle={`${Math.round(claimData.claim_rate * 100)}% claim rate`}
          />
          <StatCard
            title="Unclaimed"
            value={claimData.unclaimed}
            icon={Target}
            color="bg-red-600"
            subtitle="Needs outreach"
          />
          <StatCard
            title="Total Programs"
            value={claimData.total_programs}
            icon={Building2}
            color="bg-slate-600"
            subtitle="Tracked"
          />
          <StatCard
            title="Claim Rate"
            value={`${Math.round(claimData.claim_rate * 100)}%`}
            icon={TrendingUp}
            color="bg-blue-600"
            subtitle="Coverage"
          />
        </div>
      )}

      {/* Match Rates */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MatchRateCard
          title="Jobs → Programs"
          rate={statistics.match_rates.jobs_to_programs}
          matched={statistics.jobs_matched_to_programs}
          total={statistics.total_jobs}
        />
        <MatchRateCard
          title="Jobs → Contacts"
          rate={statistics.match_rates.jobs_to_contacts}
          matched={statistics.jobs_matched_to_contacts}
          total={statistics.total_jobs}
        />
        <MatchRateCard
          title="Contacts → Programs"
          rate={statistics.match_rates.contacts_to_programs}
          matched={statistics.contacts_matched_to_programs}
          total={statistics.total_contacts}
        />
      </div>

      {/* Weekly Intelligence Brief */}
      <WeeklyIntelBrief summary={summary} />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Contact Tiers Pie Chart */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Contacts by Tier</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={tierData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {tierData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--color-gray-200)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-2 mt-4 justify-center">
            {tierData.map((tier, index) => (
              <div key={index} className="flex items-center gap-1.5 text-sm">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: tier.color }} />
                <span className="text-slate-600 dark:text-slate-400">{tier.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Priority Distribution */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Jobs by Priority</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={priorityData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {priorityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--color-gray-200)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-4 mt-4 justify-center">
            {priorityData.map((item, index) => (
              <div key={index} className="flex items-center gap-1.5 text-sm">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: item.color }} />
                <span className="text-slate-600 dark:text-slate-400">{item.name}: {item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Programs Bar Chart */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Top Programs by Contact Count</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={programsData} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
              <XAxis type="number" tick={{ fill: 'var(--color-gray-500)', fontSize: 12 }} />
              <YAxis dataKey="name" type="category" width={150} tick={{ fill: 'var(--color-gray-500)', fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--color-gray-200)' }} />
              <Bar dataKey="contacts" fill="#2563eb" radius={[0, 4, 4, 0]} name="Contacts" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* KPI Charts Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <CollectionHealthChart />
        <WeeklyOutreachChart />
        <SystemHealthCards />
      </div>
    </div>
  );
}

// ─── Weekly Intelligence Brief ───────────────────────────────────────────────

const BRIEF_CACHE_KEY = 'bd_weekly_intel_brief';
const BRIEF_CACHE_TTL = 24 * 60 * 60 * 1000; // 24 hours

interface CachedBrief {
  brief: string;
  sections: BriefSection[];
  generatedAt: number;
  stalePrograms: string[];
}

interface BriefSection {
  title: string;
  icon: string;
  content: string;
}

function loadCachedBrief(): CachedBrief | null {
  try {
    const raw = localStorage.getItem(BRIEF_CACHE_KEY);
    if (!raw) return null;
    const cached: CachedBrief = JSON.parse(raw);
    if (Date.now() - cached.generatedAt > BRIEF_CACHE_TTL) {
      localStorage.removeItem(BRIEF_CACHE_KEY);
      return null;
    }
    return cached;
  } catch { return null; }
}

function parseBriefSections(text: string): BriefSection[] {
  const sections: BriefSection[] = [];
  const sectionDefs = [
    { pattern: /(?:new\s+opportunities|opportunities)/i, title: 'New Opportunities', icon: '🎯' },
    { pattern: /(?:program\s+updates|program\s+changes)/i, title: 'Program Updates', icon: '📋' },
    { pattern: /(?:contact\s+activity|contact\s+updates|key\s+contacts)/i, title: 'Contact Activity', icon: '👥' },
    { pattern: /(?:competitive\s+moves|competitor|competitive)/i, title: 'Competitive Moves', icon: '⚔️' },
  ];

  // Try to extract sections from the text
  const lines = text.split('\n');
  let currentSection: BriefSection | null = null;
  const contentLines: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    const matchedDef = sectionDefs.find(d => d.pattern.test(trimmed));
    if (matchedDef || /^#{1,3}\s/.test(trimmed) || /^\*\*[^*]+\*\*$/.test(trimmed)) {
      if (currentSection && contentLines.length > 0) {
        currentSection.content = contentLines.join('\n');
        sections.push(currentSection);
        contentLines.length = 0;
      }
      const def = matchedDef || { title: trimmed.replace(/^#{1,3}\s*|\*\*/g, ''), icon: '📌' };
      currentSection = { title: def.title, icon: def.icon, content: '' };
    } else if (currentSection) {
      contentLines.push(trimmed);
    } else {
      contentLines.push(trimmed);
    }
  }
  if (currentSection && contentLines.length > 0) {
    currentSection.content = contentLines.join('\n');
    sections.push(currentSection);
  }

  // Fallback: if no sections were parsed, create one from the whole text
  if (sections.length === 0 && text.trim()) {
    sections.push({ title: 'Intelligence Summary', icon: '📊', content: text.trim() });
  }

  return sections;
}

function WeeklyIntelBrief({ summary }: { summary: CorrelationSummary }) {
  const [brief, setBrief] = useState<string | null>(null);
  const [sections, setSections] = useState<BriefSection[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stalePrograms, setStalePrograms] = useState<string[]>([]);

  // Load cached brief on mount
  useEffect(() => {
    const cached = loadCachedBrief();
    if (cached) {
      setBrief(cached.brief);
      setSections(cached.sections);
      setStalePrograms(cached.stalePrograms);
    }
  }, []);

  // Per-program stale intel check
  useEffect(() => {
    async function checkStalePrograms() {
      try {
        const topPrograms = summary.top_programs_by_jobs.slice(0, 5).map(p => p.name);
        const stale: string[] = [];
        for (const prog of topPrograms) {
          try {
            const results = await hubApiClient.search(prog, 'programs', 1);
            if (results.length === 0) {
              stale.push(prog);
            } else {
              const lastUpdated = results[0].metadata?.updated_at as string || results[0].metadata?.last_updated as string;
              if (lastUpdated) {
                const daysSince = Math.floor((Date.now() - new Date(lastUpdated).getTime()) / (1000 * 60 * 60 * 24));
                if (daysSince > 14) stale.push(prog);
              }
            }
          } catch { /* skip */ }
        }
        setStalePrograms(stale);
      } catch { /* skip */ }
    }
    checkStalePrograms();
  }, [summary]);

  const generateBrief = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await hubApiClient.generateWeeklyIntel();
      if (result.status === 'completed' && result.result) {
        const briefText =
          typeof result.result === 'string'
            ? result.result
            : (result.result as Record<string, unknown>).brief as string ||
              (result.result as Record<string, unknown>).summary as string ||
              JSON.stringify(result.result);
        const parsedSections = parseBriefSections(briefText);
        setBrief(briefText);
        setSections(parsedSections);
        // Cache the brief
        const cached: CachedBrief = {
          brief: briefText,
          sections: parsedSections,
          generatedAt: Date.now(),
          stalePrograms,
        };
        localStorage.setItem(BRIEF_CACHE_KEY, JSON.stringify(cached));
      } else {
        setError('Brief generation returned incomplete results.');
      }
    } catch {
      setError('Weekly Intel API unavailable. Start the Knowledge API on port 8100.');
    } finally {
      setLoading(false);
    }
  }, [stalePrograms]);

  // Stale intel detection
  const generatedDate = new Date(summary.generated_at);
  const daysSinceGeneration = Math.floor((Date.now() - generatedDate.getTime()) / (1000 * 60 * 60 * 24));
  const isStale = daysSinceGeneration > 7;

  // Quick comparison stats (current vs baseline)
  const stats = summary.statistics;
  const quickStats = [
    { label: 'Pipeline Jobs', value: stats.total_jobs, baseline: Math.round(stats.total_jobs * 0.9), unit: '' },
    { label: 'Contact Coverage', value: Math.round(stats.match_rates.contacts_to_programs), baseline: 25, unit: '%' },
    { label: 'Job Match Rate', value: Math.round(stats.match_rates.jobs_to_programs), baseline: 30, unit: '%' },
  ];

  const cachedBrief = loadCachedBrief();
  const cachedAgeHours = cachedBrief ? Math.round((Date.now() - cachedBrief.generatedAt) / (1000 * 60 * 60)) : null;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-900/30">
            <Newspaper className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Weekly Intelligence Brief</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Data generated {daysSinceGeneration === 0 ? 'today' : `${daysSinceGeneration}d ago`}
              {cachedAgeHours !== null && (
                <span className="ml-2 text-xs text-slate-400">• Cached {cachedAgeHours}h ago</span>
              )}
            </p>
          </div>
        </div>
        <button
          onClick={generateBrief}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium bg-indigo-50 text-indigo-700 hover:bg-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-400 dark:hover:bg-indigo-900/50 transition-colors disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          {loading ? 'Generating...' : brief ? 'Regenerate Brief' : 'Generate AI Brief'}
        </button>
      </div>

      {/* Stale Warning */}
      {isStale && (
        <div className="mb-4 flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
          <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0" />
          <p className="text-sm text-amber-700 dark:text-amber-300">
            Data is {daysSinceGeneration} days old. Consider refreshing your pipeline for latest intelligence.
          </p>
        </div>
      )}

      {/* Per-program stale alerts */}
      {stalePrograms.length > 0 && (
        <div className="mb-4 flex items-start gap-2 px-3 py-2 rounded-lg bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800">
          <RefreshCw className="h-4 w-4 text-orange-600 dark:text-orange-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-orange-700 dark:text-orange-300">
            <span className="font-medium">Stale intel on {stalePrograms.length} program{stalePrograms.length > 1 ? 's' : ''}:</span>{' '}
            {stalePrograms.join(', ')}
          </div>
        </div>
      )}

      {/* Quick Stats Comparison */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        {quickStats.map(s => {
          const delta = s.value - s.baseline;
          const isUp = delta > 0;
          return (
            <div key={s.label} className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-3">
              <p className="text-xs text-slate-500 dark:text-slate-400">{s.label}</p>
              <div className="flex items-baseline gap-2">
                <span className="text-xl font-bold text-slate-800 dark:text-slate-100">
                  {s.value.toLocaleString()}{s.unit}
                </span>
                <span className={`text-xs font-medium ${isUp ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {isUp ? '+' : ''}{delta}{s.unit}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* AI Brief Content — Sectioned Output */}
      {error && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-sm text-red-600 dark:text-red-400">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}
      {sections.length > 0 && (
        <div className="space-y-3">
          {sections.map((section, i) => (
            <div key={i} className="bg-indigo-50/50 dark:bg-indigo-900/20 rounded-lg p-4 border border-indigo-100 dark:border-indigo-800">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-base">{section.icon}</span>
                <span className="text-sm font-semibold text-indigo-700 dark:text-indigo-300">{section.title}</span>
              </div>
              <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-line leading-relaxed">{section.content}</p>
            </div>
          ))}
        </div>
      )}
      {!brief && !error && !loading && (
        <p className="text-sm text-slate-400 dark:text-slate-500 text-center py-3">
          Click "Generate AI Brief" to create a weekly intelligence summary using the Knowledge API.
        </p>
      )}
    </div>
  );
}
