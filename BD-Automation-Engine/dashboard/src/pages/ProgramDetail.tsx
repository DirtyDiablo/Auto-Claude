import { useState, useEffect, useCallback } from 'react';
import {
  Building2, ArrowLeft, Users, Briefcase, Shield, Target, Star,
  FileText, RefreshCw, MapPin, Calendar, DollarSign, TrendingUp,
} from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

interface ProgramDetailProps {
  programName: string;
  onBack: () => void;
  onNavigateToContact?: (contactName: string) => void;
}

type DetailTab = 'overview' | 'contacts' | 'laborgaps' | 'competitive' | 'intelligence';

const TABS: Array<{ id: DetailTab; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { id: 'overview', label: 'Overview', icon: Building2 },
  { id: 'contacts', label: 'Contacts', icon: Users },
  { id: 'laborgaps', label: 'Labor Gaps', icon: Briefcase },
  { id: 'competitive', label: 'Competitive', icon: Target },
  { id: 'intelligence', label: 'Intelligence', icon: Star },
];

interface ProgramData {
  id: string;
  name: string;
  acronym?: string;
  agency?: string;
  prime_contractor?: string;
  bd_priority?: string;
  program_type?: string;
  contract_vehicle?: string;
  contract_value?: string;
  location?: string;
  clearance?: string;
  period_of_performance?: string;
  recompete_date?: string;
  hiring_velocity?: string;
  pts_involvement?: string;
  notes?: string;
  score?: number;
  [key: string]: unknown;
}

interface ProgramContact {
  id: string;
  name: string;
  title?: string;
  company?: string;
  tier?: number;
}

interface JobGap {
  id: string;
  title: string;
  company?: string;
  location?: string;
  clearance?: string;
  score: number;
}

interface IntelResult {
  answer: string;
  sources: Array<{ collection: string; id: string; content: string; score: number }>;
}

interface ProgramMemoryContext {
  program: { name: string; agency: string; prime: string };
  intel_history: Array<{ date: string; type: string; content: string }>;
  patterns: string[];
  opportunities: string[];
}

const PRIORITY_COLORS: Record<string, string> = {
  'Critical': 'bg-red-600 text-white',
  'High': 'bg-orange-500 text-white',
  'Medium': 'bg-yellow-500 text-white',
  'Low': 'bg-green-500 text-white',
  'Tier 1': 'bg-red-600 text-white',
  'Tier 2': 'bg-orange-500 text-white',
  'Tier 3': 'bg-yellow-500 text-white',
};

export function ProgramDetail({ programName, onBack, onNavigateToContact }: ProgramDetailProps) {
  const [activeTab, setActiveTab] = useState<DetailTab>('overview');
  const [program, setProgram] = useState<ProgramData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tab-specific data
  const [contacts, setContacts] = useState<ProgramContact[]>([]);
  const [contactsLoading, setContactsLoading] = useState(false);
  const [jobs, setJobs] = useState<JobGap[]>([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [intel, setIntel] = useState<IntelResult | null>(null);
  const [intelLoading, setIntelLoading] = useState(false);
  const [memoryCtx, setMemoryCtx] = useState<ProgramMemoryContext | null>(null);
  const [competitors, setCompetitors] = useState<Array<{ name: string; score: number; content: string }>>([]);
  const [competitorsLoading, setCompetitorsLoading] = useState(false);

  // Load program data
  const fetchProgram = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await hubApiClient.filterPrograms({ query: programName, limit: 5 });
      if (res.programs.length > 0) {
        const match = res.programs.find(
          (p) => String(p['Program Name'] || p.name || '').toLowerCase() === programName.toLowerCase()
        ) || res.programs[0];
        setProgram({
          id: String(match.id || ''),
          name: String(match['Program Name'] || match.name || programName),
          acronym: String(match.Acronym || match.acronym || ''),
          agency: String(match.Agency || match.agency || ''),
          prime_contractor: String(match['Prime Contractor'] || match.prime_contractor || ''),
          bd_priority: String(match['BD Priority'] || match.bd_priority || ''),
          program_type: String(match['Program Type'] || match.program_type || ''),
          contract_vehicle: String(match['Contract Vehicle'] || match.contract_vehicle || ''),
          contract_value: String(match['Contract Value'] || match.contract_value || ''),
          location: String(match.Location || match.location || ''),
          clearance: String(match['Clearance Requirements'] || match.clearance || ''),
          period_of_performance: String(match['Period of Performance'] || match.period_of_performance || ''),
          recompete_date: String(match['Recompete Date'] || match.recompete_date || ''),
          hiring_velocity: String(match['Hiring Velocity'] || match.hiring_velocity || ''),
          pts_involvement: String(match['PTS Involvement'] || match.pts_involvement || ''),
          notes: String(match.Notes || match.notes || ''),
          score: Number(match.score || 0),
        });
      } else {
        setError(`No program found matching "${programName}"`);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load program');
    } finally {
      setLoading(false);
    }
  }, [programName]);

  useEffect(() => { fetchProgram(); }, [fetchProgram]);

  // Load contacts for this program
  useEffect(() => {
    if (activeTab === 'contacts' && contacts.length === 0 && !contactsLoading) {
      setContactsLoading(true);
      hubApiClient.filterContacts({ program: programName, limit: 50 })
        .then(res => {
          setContacts(res.contacts.map(c => ({
            id: String(c.id || ''),
            name: String(c.name || c.Name || ''),
            title: String(c.title || c.Title || c['Job Title'] || ''),
            company: String(c.company || c.Primes || ''),
            tier: Number(c.tier || c.Tier || 0),
          })));
        })
        .catch(() => setContacts([]))
        .finally(() => setContactsLoading(false));
    }
  }, [activeTab, programName, contacts.length, contactsLoading]);

  // Load labor gaps (jobs associated with program)
  useEffect(() => {
    if (activeTab === 'laborgaps' && jobs.length === 0 && !jobsLoading) {
      setJobsLoading(true);
      hubApiClient.search(programName, 'jobs', 20)
        .then(res => {
          setJobs(res.map(r => ({
            id: r.id,
            title: r.content || String(r.metadata?.title || r.metadata?.Title || ''),
            company: String(r.metadata?.company || r.metadata?.Company || ''),
            location: String(r.metadata?.location || r.metadata?.Location || ''),
            clearance: String(r.metadata?.clearance || r.metadata?.Clearance || ''),
            score: r.score,
          })));
        })
        .catch(() => setJobs([]))
        .finally(() => setJobsLoading(false));
    }
  }, [activeTab, programName, jobs.length, jobsLoading]);

  // Load competitive landscape
  useEffect(() => {
    if (activeTab === 'competitive' && competitors.length === 0 && !competitorsLoading) {
      setCompetitorsLoading(true);
      hubApiClient.search(`${programName} competitor prime contractor subcontractor`, undefined, 15)
        .then(res => {
          setCompetitors(res.map(r => ({
            name: r.content,
            score: r.score,
            content: String(r.metadata?.description || r.metadata?.notes || r.metadata?.Notes || ''),
          })));
        })
        .catch(() => setCompetitors([]))
        .finally(() => setCompetitorsLoading(false));
    }
  }, [activeTab, programName, competitors.length, competitorsLoading]);

  // Load AI intelligence
  useEffect(() => {
    if (activeTab === 'intelligence' && !intel && !intelLoading) {
      setIntelLoading(true);
      Promise.all([
        hubApiClient.askSmart(`Give me a complete intelligence brief on the ${programName} program. Include contractors, contacts, opportunities, and risks.`),
        hubApiClient.getProgramContext(programName).catch(() => null),
      ])
        .then(([smartRes, ctx]) => {
          setIntel({ answer: smartRes.answer, sources: smartRes.sources });
          if (ctx) setMemoryCtx(ctx);
        })
        .catch(() => setIntel({ answer: 'Intelligence not available', sources: [] }))
        .finally(() => setIntelLoading(false));
    }
  }, [activeTab, programName, intel, intelLoading]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error || !program) {
    return (
      <div className="h-full overflow-auto p-6">
        <button onClick={onBack} className="flex items-center gap-2 text-blue-600 hover:text-blue-800 mb-4">
          <ArrowLeft className="w-4 h-4" /> Back to Programs
        </button>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error || 'Program not found'}
        </div>
      </div>
    );
  }

  const priorityBadge = PRIORITY_COLORS[program.bd_priority || ''] || 'bg-slate-500 text-white';

  return (
    <div className="h-full overflow-auto p-6 space-y-6">
      {/* Back Button */}
      <button onClick={onBack} className="flex items-center gap-2 text-blue-600 hover:text-blue-800 text-sm">
        <ArrowLeft className="w-4 h-4" /> Back to Programs
      </button>

      {/* Header Card */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-16 h-16 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xl font-bold">
            {program.acronym && program.acronym !== 'undefined' ? program.acronym.slice(0, 4) : program.name.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{program.name}</h1>
              {program.acronym && program.acronym !== 'undefined' && (
                <span className="text-lg text-slate-500 dark:text-slate-400">({program.acronym})</span>
              )}
              {program.bd_priority && program.bd_priority !== 'undefined' && (
                <span className={`text-xs font-bold px-2 py-1 rounded ${priorityBadge}`}>
                  {program.bd_priority}
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-4 mt-3 text-sm text-slate-500 dark:text-slate-400">
              {program.agency && program.agency !== 'undefined' && (
                <span className="flex items-center gap-1.5">
                  <Building2 className="w-4 h-4" /> {program.agency}
                </span>
              )}
              {program.prime_contractor && program.prime_contractor !== 'undefined' && (
                <span className="flex items-center gap-1.5">
                  <Target className="w-4 h-4" /> Prime: {program.prime_contractor}
                </span>
              )}
              {program.location && program.location !== 'undefined' && (
                <span className="flex items-center gap-1.5">
                  <MapPin className="w-4 h-4" /> {program.location}
                </span>
              )}
              {program.clearance && program.clearance !== 'undefined' && (
                <span className="flex items-center gap-1.5">
                  <Shield className="w-4 h-4" /> {program.clearance}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 border-b border-slate-200 dark:border-slate-700">
        {TABS.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'overview' && <ProgramOverviewTab program={program} />}
        {activeTab === 'contacts' && (
          <ProgramContactsTab contacts={contacts} loading={contactsLoading} onNavigateToContact={onNavigateToContact} />
        )}
        {activeTab === 'laborgaps' && <LaborGapsTab jobs={jobs} loading={jobsLoading} />}
        {activeTab === 'competitive' && <CompetitiveTab competitors={competitors} loading={competitorsLoading} program={program} />}
        {activeTab === 'intelligence' && <ProgramIntelligenceTab intel={intel} memoryCtx={memoryCtx} loading={intelLoading} />}
      </div>
    </div>
  );
}

// =============================================================================
// OVERVIEW TAB
// =============================================================================

function ProgramOverviewTab({ program }: { program: ProgramData }) {
  const fields = [
    { label: 'Agency', value: program.agency, icon: Building2 },
    { label: 'Prime Contractor', value: program.prime_contractor, icon: Target },
    { label: 'Program Type', value: program.program_type, icon: FileText },
    { label: 'Contract Vehicle', value: program.contract_vehicle, icon: FileText },
    { label: 'Contract Value', value: program.contract_value, icon: DollarSign },
    { label: 'Period of Performance', value: program.period_of_performance, icon: Calendar },
    { label: 'Recompete Date', value: program.recompete_date, icon: Calendar },
    { label: 'Location', value: program.location, icon: MapPin },
    { label: 'Clearance', value: program.clearance, icon: Shield },
    { label: 'Hiring Velocity', value: program.hiring_velocity, icon: TrendingUp },
    { label: 'PTS Involvement', value: program.pts_involvement, icon: Users },
  ].filter(f => f.value && f.value !== 'undefined');

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-5">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Program Details</h3>
        <dl className="space-y-3">
          {fields.map(f => {
            const Icon = f.icon;
            return (
              <div key={f.label} className="flex items-center justify-between">
                <dt className="text-sm text-slate-500 dark:text-slate-400 flex items-center gap-2">
                  <Icon className="w-3.5 h-3.5" /> {f.label}
                </dt>
                <dd className="text-sm font-medium text-slate-900 dark:text-slate-100 text-right max-w-[60%]">
                  {f.value}
                </dd>
              </div>
            );
          })}
        </dl>
      </div>

      {program.notes && program.notes !== 'undefined' && (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-5">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Notes</h3>
          <p className="text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap">{program.notes}</p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// CONTACTS TAB
// =============================================================================

const TIER_BADGE: Record<number, string> = {
  1: 'bg-purple-600 text-white',
  2: 'bg-blue-600 text-white',
  3: 'bg-cyan-600 text-white',
  4: 'bg-emerald-600 text-white',
  5: 'bg-amber-600 text-white',
  6: 'bg-slate-500 text-white',
};

function ProgramContactsTab({
  contacts, loading, onNavigateToContact,
}: {
  contacts: ProgramContact[];
  loading: boolean;
  onNavigateToContact?: (name: string) => void;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mr-3" />
        <span className="text-slate-600 dark:text-slate-400">Loading contacts...</span>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Program Contacts</h3>
        <p className="text-sm text-slate-500">{contacts.length} contacts associated</p>
      </div>
      {contacts.length === 0 ? (
        <div className="px-5 py-8 text-center text-slate-500">
          <Users className="w-8 h-8 mx-auto mb-3 text-slate-400" />
          <p>No contacts found for this program</p>
        </div>
      ) : (
        <table className="w-full text-sm">
          <thead className="bg-slate-50 dark:bg-slate-900/50">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Name</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Title</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Company</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Tier</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {contacts.map(c => (
              <tr key={c.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                <td className="px-4 py-3">
                  {onNavigateToContact ? (
                    <button
                      onClick={() => onNavigateToContact(c.name)}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      {c.name}
                    </button>
                  ) : (
                    <span className="text-slate-900 dark:text-slate-100 font-medium">{c.name}</span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{c.title || '-'}</td>
                <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{c.company || '-'}</td>
                <td className="px-4 py-3 text-center">
                  {c.tier && c.tier > 0 ? (
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${TIER_BADGE[c.tier] || TIER_BADGE[6]}`}>
                      T{c.tier}
                    </span>
                  ) : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// =============================================================================
// LABOR GAPS TAB
// =============================================================================

function LaborGapsTab({ jobs, loading }: { jobs: JobGap[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mr-3" />
        <span className="text-slate-600 dark:text-slate-400">Searching job openings...</span>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Open Positions / Labor Gaps</h3>
        <p className="text-sm text-slate-500">{jobs.length} related positions found</p>
      </div>
      {jobs.length === 0 ? (
        <div className="px-5 py-8 text-center text-slate-500">
          <Briefcase className="w-8 h-8 mx-auto mb-3 text-slate-400" />
          <p>No open positions found for this program</p>
        </div>
      ) : (
        <table className="w-full text-sm">
          <thead className="bg-slate-50 dark:bg-slate-900/50">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Title</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Company</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Location</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Clearance</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Match</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {jobs.map(job => (
              <tr key={job.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                <td className="px-4 py-3 text-slate-900 dark:text-slate-100 font-medium">{job.title || '-'}</td>
                <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{job.company || '-'}</td>
                <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{job.location || '-'}</td>
                <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{job.clearance || '-'}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`font-medium ${job.score >= 0.7 ? 'text-green-600' : job.score >= 0.5 ? 'text-yellow-600' : 'text-slate-500'}`}>
                    {(job.score * 100).toFixed(0)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// =============================================================================
// COMPETITIVE LANDSCAPE TAB
// =============================================================================

function CompetitiveTab({
  competitors, loading, program,
}: {
  competitors: Array<{ name: string; score: number; content: string }>;
  loading: boolean;
  program: ProgramData;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mr-3" />
        <span className="text-slate-600 dark:text-slate-400">Analyzing competitive landscape...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Prime Info */}
      {program.prime_contractor && program.prime_contractor !== 'undefined' && (
        <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-indigo-800 dark:text-indigo-400 mb-2">Current Prime Contractor</h3>
          <p className="text-lg font-bold text-indigo-900 dark:text-indigo-300">{program.prime_contractor}</p>
        </div>
      )}

      {/* Competitive Intel */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Related Entities</h3>
          <p className="text-sm text-slate-500">{competitors.length} relevant matches from knowledge base</p>
        </div>
        {competitors.length === 0 ? (
          <div className="px-5 py-8 text-center text-slate-500">
            <Target className="w-8 h-8 mx-auto mb-3 text-slate-400" />
            <p>No competitive intelligence found</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-700">
            {competitors.map((comp, i) => (
              <div key={i} className="px-5 py-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-100">{comp.name}</span>
                  <span className="text-xs text-slate-400">{(comp.score * 100).toFixed(0)}% relevance</span>
                </div>
                {comp.content && (
                  <p className="text-sm text-slate-600 dark:text-slate-400 truncate">{comp.content}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// INTELLIGENCE TAB
// =============================================================================

function ProgramIntelligenceTab({
  intel, memoryCtx, loading,
}: {
  intel: IntelResult | null;
  memoryCtx: ProgramMemoryContext | null;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mr-3" />
        <span className="text-slate-600 dark:text-slate-400">Generating intelligence brief...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* AI Summary */}
      {intel && (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-5">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
            <Star className="w-5 h-5 text-yellow-500" /> AI Intelligence Brief
          </h3>
          <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{intel.answer}</p>

          {intel.sources.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
              <h4 className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-2">Sources ({intel.sources.length})</h4>
              <div className="space-y-1">
                {intel.sources.map((s, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-slate-500">
                    <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700">{s.collection}</span>
                    <span className="truncate">{s.content}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Memory Patterns & Opportunities */}
      {memoryCtx && (
        <>
          {memoryCtx.patterns.length > 0 && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-5">
              <h3 className="text-sm font-semibold text-blue-800 dark:text-blue-400 mb-2">Observed Patterns</h3>
              <ul className="list-disc list-inside space-y-1">
                {memoryCtx.patterns.map((p, i) => (
                  <li key={i} className="text-sm text-blue-700 dark:text-blue-500">{p}</li>
                ))}
              </ul>
            </div>
          )}
          {memoryCtx.opportunities.length > 0 && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-5">
              <h3 className="text-sm font-semibold text-green-800 dark:text-green-400 mb-2">Opportunities</h3>
              <ul className="list-disc list-inside space-y-1">
                {memoryCtx.opportunities.map((o, i) => (
                  <li key={i} className="text-sm text-green-700 dark:text-green-500">{o}</li>
                ))}
              </ul>
            </div>
          )}
          {memoryCtx.intel_history.length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Intel History</h3>
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-700">
                {memoryCtx.intel_history.map((entry, i) => (
                  <div key={i} className="px-5 py-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400">
                        {entry.type}
                      </span>
                      <span className="text-xs text-slate-500">{entry.date}</span>
                    </div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{entry.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
