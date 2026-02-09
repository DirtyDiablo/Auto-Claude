/**
 * Jobs Pipeline — Grid + Kanban views
 *
 * Kanban board with 6 BD workflow stages, drag-and-drop via @dnd-kit,
 * Hub API data loading, and localStorage pipeline state persistence.
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Search, Filter, ExternalLink, MapPin, Shield, Building2,
  Network, Briefcase, Tag, LayoutGrid, Columns3, GripVertical,
  Clock, User,
} from 'lucide-react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  PointerSensor,
  useSensor,
  useSensors,
  useDroppable,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import { hubApiClient } from '../services/hubApi';
import type { Job } from '../types';
import type { NativeNodeType } from '../configs/nativeNodeConfigs';
import { SkeletonCard } from '../components/ui/Skeleton';

interface JobsPipelineProps {
  jobs: Job[];
  loading: boolean;
  onNavigateToProgram?: (programName: string) => void;
  onNavigateToLocation?: (location: string) => void;
  onNavigateToMindMap?: (entityType: NativeNodeType, entityId: string, entityLabel: string) => void;
  onNavigateToContact?: (contactName: string) => void;
}

// ─── BD Workflow Stages (6 columns per spec) ─────────────────────────────────

const BD_STAGES = [
  { id: 'scraped', label: 'Scraped', color: 'bg-slate-100 border-slate-300 text-slate-700', dot: 'bg-slate-400' },
  { id: 'mapped', label: 'Mapped to Program', color: 'bg-blue-50 border-blue-300 text-blue-700', dot: 'bg-blue-500' },
  { id: 'contacts_found', label: 'Contacts Found', color: 'bg-purple-50 border-purple-300 text-purple-700', dot: 'bg-purple-500' },
  { id: 'outreach_active', label: 'Outreach Active', color: 'bg-orange-50 border-orange-300 text-orange-700', dot: 'bg-orange-500' },
  { id: 'meeting_set', label: 'Meeting Set', color: 'bg-amber-50 border-amber-300 text-amber-700', dot: 'bg-amber-500' },
  { id: 'job_req', label: 'Job Req Obtained', color: 'bg-green-50 border-green-300 text-green-700', dot: 'bg-green-500' },
] as const;

type StageId = (typeof BD_STAGES)[number]['id'];

const STORAGE_KEY = 'bd_pipeline_stages';

function loadPersistedStages(): Record<string, StageId> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch { return {}; }
}

function persistStages(stages: Record<string, StageId>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(stages));
}

function inferStage(job: Job): StageId {
  const status = (job.status || '').toLowerCase();
  if (status.includes('req') || status === 'won' || status === 'closed/won') return 'job_req';
  if (status.includes('meeting')) return 'meeting_set';
  if (status.includes('outreach') || status === 'contacted') return 'outreach_active';
  if (status.includes('contact') || status === 'pursuing') return 'contacts_found';
  if (job.program && job.program !== 'Unknown' && job.program !== '') return 'mapped';
  return 'scraped';
}

function daysInStage(job: Job): number {
  const created = job.scraped_at || job.created_at;
  if (!created) return 0;
  return Math.floor((Date.now() - new Date(created).getTime()) / (1000 * 60 * 60 * 24));
}

// ─── Clearance badge helper ──────────────────────────────────────────────────

function getClearanceBadge(clearance: string): { bg: string; text: string } {
  const c = (clearance || '').toLowerCase();
  if (c.includes('ts/sci') || c.includes('ts')) return { bg: 'bg-red-100', text: 'text-red-700' };
  if (c.includes('secret')) return { bg: 'bg-orange-100', text: 'text-orange-700' };
  return { bg: 'bg-gray-100', text: 'text-gray-600' };
}

function getPriorityBadge(priority: number | string | null): { color: string; label: string } {
  if (priority === null || priority === undefined) return { color: 'bg-gray-100 text-gray-600', label: 'Unrated' };
  if (typeof priority === 'number') {
    if (priority >= 80) return { color: 'bg-red-100 text-red-700', label: 'Critical' };
    if (priority >= 60) return { color: 'bg-orange-100 text-orange-700', label: 'High' };
    if (priority >= 40) return { color: 'bg-yellow-100 text-yellow-700', label: 'Medium' };
    return { color: 'bg-green-100 text-green-700', label: 'Low' };
  }
  const str = String(priority).toLowerCase();
  if (str.includes('critical')) return { color: 'bg-red-100 text-red-700', label: 'Critical' };
  if (str.includes('high')) return { color: 'bg-orange-100 text-orange-700', label: 'High' };
  if (str.includes('medium')) return { color: 'bg-yellow-100 text-yellow-700', label: 'Medium' };
  if (str.includes('low')) return { color: 'bg-green-100 text-green-700', label: 'Low' };
  return { color: 'bg-gray-100 text-gray-600', label: 'Unrated' };
}

// ─── Kanban Card ─────────────────────────────────────────────────────────────

function KanbanCard({
  job,
  onNavigateToProgram,
  onNavigateToContact,
}: {
  job: Job;
  onNavigateToProgram?: (name: string) => void;
  onNavigateToContact?: (name: string) => void;
}) {
  const priority = getPriorityBadge(job.bd_priority);
  const clearance = getClearanceBadge(job.clearance);
  const programName = job.program || job.program_name;
  const days = daysInStage(job);
  // Extract contact from matched_contacts if available
  const keyContact = job.matched_contacts?.[0];

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-3 hover:shadow-md transition-shadow cursor-grab active:cursor-grabbing">
      {/* Title */}
      <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100 line-clamp-2 mb-1.5">
        {job.title || 'Untitled'}
      </h4>

      {/* Company + Location */}
      {job.company && (
        <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1 mb-0.5">
          <Building2 className="h-3 w-3 flex-shrink-0" /> {job.company}
        </p>
      )}
      {(job.location || job.city) && (
        <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1 mb-1.5">
          <MapPin className="h-3 w-3 flex-shrink-0" />
          {job.city && job.location ? `${job.city}, ${job.location}` : job.location || job.city}
        </p>
      )}

      {/* Badges row */}
      <div className="flex flex-wrap gap-1 mb-1.5">
        {job.clearance && (
          <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded flex items-center gap-0.5 ${clearance.bg} ${clearance.text}`}>
            <Shield className="h-2.5 w-2.5" /> {job.clearance}
          </span>
        )}
        {typeof job.bd_priority === 'number' && (
          <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${priority.color}`}>
            {job.bd_priority}
          </span>
        )}
      </div>

      {/* Program link */}
      {programName && programName !== 'Unknown' && (
        <button
          onClick={e => { e.stopPropagation(); onNavigateToProgram?.(programName); }}
          className="text-xs text-blue-600 dark:text-blue-400 hover:underline block mb-0.5 truncate max-w-full text-left"
        >
          {programName}
        </button>
      )}

      {/* Key contact */}
      {keyContact && (
        <button
          onClick={e => { e.stopPropagation(); onNavigateToContact?.(keyContact); }}
          className="text-xs text-purple-600 dark:text-purple-400 hover:underline flex items-center gap-1 mb-1"
        >
          <User className="h-3 w-3" /> {keyContact}
        </button>
      )}

      {/* Footer: days in stage */}
      <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-slate-100 dark:border-slate-700">
        <span className="text-[10px] text-slate-400 flex items-center gap-1">
          <Clock className="h-3 w-3" /> {days}d in stage
        </span>
        {job.source_url && (
          <a href={job.source_url} target="_blank" rel="noopener noreferrer"
            className="text-slate-400 hover:text-blue-600" onClick={e => e.stopPropagation()}>
            <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
    </div>
  );
}

// ─── Full Job Card (Grid view) ───────────────────────────────────────────────

function JobCard({
  job,
  onNavigateToProgram,
  onNavigateToLocation,
  onNavigateToMindMap,
  onNavigateToContact: _onNavigateToContact,
}: {
  job: Job;
  onNavigateToProgram?: (name: string) => void;
  onNavigateToLocation?: (location: string) => void;
  onNavigateToMindMap?: (entityType: NativeNodeType, entityId: string, entityLabel: string) => void;
  onNavigateToContact?: (name: string) => void;
}) {
  const priority = getPriorityBadge(job.bd_priority);
  const clearance = getClearanceBadge(job.clearance);
  const programName = job.program || job.program_name;
  const days = daysInStage(job);

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className={`text-xs font-medium px-2 py-0.5 rounded ${priority.color}`}>{priority.label}</span>
            {job.clearance && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded flex items-center gap-1 ${clearance.bg} ${clearance.text}`}>
                <Shield className="h-3 w-3" /> {job.clearance}
              </span>
            )}
            {job.status && (
              <span className="text-xs font-medium px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                {job.status}
              </span>
            )}
            {job.dcgs_relevance && (
              <span className="text-xs font-medium px-2 py-0.5 rounded bg-red-50 text-red-600">DCGS</span>
            )}
          </div>
          <h3 className="font-semibold text-slate-900 dark:text-slate-100 line-clamp-2">{job.title || 'Untitled Job'}</h3>
          <div className="mt-2 space-y-1.5">
            {job.company && (
              <p className="text-sm text-slate-600 dark:text-slate-300 flex items-center gap-1.5">
                <Building2 className="h-3.5 w-3.5 text-slate-400" /> {job.company}
              </p>
            )}
            {(job.location || job.city) && (
              <button onClick={() => onNavigateToLocation?.(job.location || job.city)}
                className="text-sm text-slate-500 hover:text-blue-600 flex items-center gap-1.5 transition-colors">
                <MapPin className="h-3.5 w-3.5 text-slate-400" />
                <span className="hover:underline">{job.city && job.location ? `${job.city}, ${job.location}` : job.location || job.city}</span>
              </button>
            )}
            {job.agency && (
              <p className="text-sm text-slate-500 flex items-center gap-1.5">
                <Briefcase className="h-3.5 w-3.5 text-slate-400" /> {job.agency}
              </p>
            )}
            {job.functional_area && (
              <p className="text-sm text-slate-500 flex items-center gap-1.5">
                <Tag className="h-3.5 w-3.5 text-slate-400" /> {job.functional_area}
              </p>
            )}
          </div>
          {programName && (
            <button onClick={() => onNavigateToProgram?.(programName)}
              className="mt-2 text-sm text-blue-600 font-medium hover:underline transition-colors">{programName}</button>
          )}
        </div>
        <div className="flex items-start gap-1">
          {onNavigateToMindMap && (
            <button onClick={() => onNavigateToMindMap('JOB', job.id, job.title)}
              className="p-2 text-slate-400 hover:text-purple-600 transition-colors" title="Mind Map">
              <Network className="h-4 w-4" />
            </button>
          )}
          {job.source_url && (
            <a href={job.source_url} target="_blank" rel="noopener noreferrer"
              className="p-2 text-slate-400 hover:text-blue-600 transition-colors">
              <ExternalLink className="h-4 w-4" />
            </a>
          )}
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-700 flex items-center justify-between">
        <span className="text-xs text-slate-400 flex items-center gap-1">
          <Clock className="h-3 w-3" /> {days}d
        </span>
        <div className="flex items-center gap-3">
          {job.scraped_at && <span className="text-xs text-slate-400">{new Date(job.scraped_at).toLocaleDateString()}</span>}
          {typeof job.bd_priority === 'number' && <span className="text-xs font-medium text-slate-500">Score: {job.bd_priority}</span>}
        </div>
      </div>
    </div>
  );
}

// ─── Kanban Column ───────────────────────────────────────────────────────────

function KanbanColumn({
  stage, jobs, onNavigateToProgram, onNavigateToContact,
}: {
  stage: (typeof BD_STAGES)[number];
  jobs: Job[];
  onNavigateToProgram?: (name: string) => void;
  onNavigateToContact?: (name: string) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: stage.id });

  return (
    <div ref={setNodeRef}
      className={`flex flex-col min-w-[240px] w-[240px] transition-colors rounded-xl ${isOver ? 'ring-2 ring-blue-400 bg-blue-50/50 dark:bg-blue-900/20' : ''}`}>
      <div className={`rounded-t-xl px-3 py-2.5 border ${stage.color} flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${stage.dot}`} />
          <span className="text-xs font-semibold">{stage.label}</span>
        </div>
        <span className="text-xs font-bold bg-white/60 dark:bg-slate-900/40 px-1.5 py-0.5 rounded">{jobs.length}</span>
      </div>
      <div className="flex-1 space-y-2 p-2 overflow-y-auto max-h-[calc(100vh-320px)] bg-slate-50/50 dark:bg-slate-900/30 rounded-b-xl border border-t-0 border-slate-200 dark:border-slate-700">
        {jobs.map(job => (
          <div key={job.id} data-job-id={job.id}>
            <KanbanCard job={job} onNavigateToProgram={onNavigateToProgram} onNavigateToContact={onNavigateToContact} />
          </div>
        ))}
        {jobs.length === 0 && (
          <div className="text-center py-8 text-xs text-slate-400 dark:text-slate-500">
            <GripVertical className="h-5 w-5 mx-auto mb-1 opacity-40" />
            Drop here
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Loading Skeleton ────────────────────────────────────────────────────────

function KanbanSkeleton() {
  return (
    <div className="flex gap-3 overflow-hidden">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="min-w-[240px] w-[240px]">
          <div className="h-10 bg-slate-200 dark:bg-slate-700 rounded-t-xl animate-pulse" />
          <div className="space-y-2 p-2 bg-slate-50 dark:bg-slate-900/30 rounded-b-xl border border-t-0 border-slate-200">
            {Array.from({ length: 3 - i % 2 }).map((_, j) => (
              <SkeletonCard key={j} className="!p-3 !rounded-lg" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export function JobsPipeline({
  jobs,
  loading,
  onNavigateToProgram,
  onNavigateToLocation,
  onNavigateToMindMap,
  onNavigateToContact,
}: JobsPipelineProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [companyFilter, setCompanyFilter] = useState<string>('all');
  const [locationFilter, setLocationFilter] = useState<string>('all');
  const [clearanceFilter, setClearanceFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'kanban'>('kanban');
  const [stageOverrides, setStageOverrides] = useState<Record<string, StageId>>(loadPersistedStages);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [hubJobs, setHubJobs] = useState<Job[]>([]);
  const [hubLoading, setHubLoading] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
  );

  // Load additional jobs from Hub API (Qdrant)
  useEffect(() => {
    async function loadHubJobs() {
      setHubLoading(true);
      try {
        const results = await hubApiClient.search('*', 'jobs', 200);
        const parsed: Job[] = results.map(r => ({
          id: r.id,
          title: String(r.metadata?.title || r.content || ''),
          program: String(r.metadata?.program || r.metadata?.['Program Name'] || ''),
          agency: String(r.metadata?.agency || r.metadata?.Agency || ''),
          bd_priority: typeof r.metadata?.bd_priority === 'number' ? r.metadata.bd_priority : null,
          clearance: String(r.metadata?.clearance || r.metadata?.Clearance || ''),
          functional_area: String(r.metadata?.functional_area || ''),
          status: String(r.metadata?.status || ''),
          location: String(r.metadata?.location || r.metadata?.Location || ''),
          city: String(r.metadata?.city || ''),
          company: String(r.metadata?.company || r.metadata?.Company || ''),
          task_order: String(r.metadata?.task_order || ''),
          source_url: String(r.metadata?.source_url || ''),
          scraped_at: String(r.metadata?.scraped_at || r.metadata?.created_at || ''),
          dcgs_relevance: Boolean(r.metadata?.dcgs_relevance),
          matched_contacts: Array.isArray(r.metadata?.matched_contacts) ? r.metadata.matched_contacts as string[] : [],
        }));
        setHubJobs(parsed);
      } catch {
        // Hub unavailable, use props jobs only
      } finally {
        setHubLoading(false);
      }
    }
    loadHubJobs();
  }, []);

  // Merge prop jobs with hub jobs (deduplicate by id)
  const allJobs = useMemo(() => {
    const map = new Map<string, Job>();
    jobs.forEach(j => map.set(j.id, j));
    hubJobs.forEach(j => { if (!map.has(j.id)) map.set(j.id, j); });
    return Array.from(map.values());
  }, [jobs, hubJobs]);

  // Filter options
  const companies = useMemo(() => [...new Set(allJobs.map(j => j.company).filter(Boolean))].sort(), [allJobs]);
  const locations = useMemo(() => [...new Set(allJobs.map(j => j.location || j.city).filter(Boolean))].sort(), [allJobs]);
  const clearances = useMemo(() => [...new Set(allJobs.map(j => j.clearance).filter(Boolean))].sort(), [allJobs]);

  // Apply filters
  const filteredJobs = useMemo(() => {
    return allJobs.filter(job => {
      if (!job.title) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        if (!([job.title, job.company, job.location, job.city, job.program, job.program_name, job.agency, job.functional_area]
          .some(f => f?.toLowerCase().includes(q)))) return false;
      }
      if (companyFilter !== 'all' && job.company !== companyFilter) return false;
      if (locationFilter !== 'all' && (job.location !== locationFilter && job.city !== locationFilter)) return false;
      if (clearanceFilter !== 'all' && job.clearance !== clearanceFilter) return false;
      if (priorityFilter !== 'all') {
        const p = getPriorityBadge(job.bd_priority).label.toLowerCase();
        if (p !== priorityFilter) return false;
      }
      return true;
    });
  }, [allJobs, searchQuery, companyFilter, locationFilter, clearanceFilter, priorityFilter]);

  // Group by kanban stage
  const jobsByStage = useMemo(() => {
    const groups: Record<StageId, Job[]> = {
      scraped: [], mapped: [], contacts_found: [],
      outreach_active: [], meeting_set: [], job_req: [],
    };
    filteredJobs.forEach(job => {
      const stage = stageOverrides[job.id] || inferStage(job);
      if (groups[stage]) groups[stage].push(job);
      else groups.scraped.push(job);
    });
    return groups;
  }, [filteredJobs, stageOverrides]);

  const activeJob = useMemo(
    () => activeJobId ? filteredJobs.find(j => j.id === activeJobId) || null : null,
    [activeJobId, filteredJobs]
  );

  const handleDragStart = useCallback((e: DragStartEvent) => setActiveJobId(String(e.active.id)), []);

  const handleDragEnd = useCallback((e: DragEndEvent) => {
    setActiveJobId(null);
    const { active, over } = e;
    if (!over) return;
    const jobId = String(active.id);
    const targetStage = String(over.id) as StageId;
    if (BD_STAGES.some(s => s.id === targetStage)) {
      setStageOverrides(prev => {
        const next = { ...prev, [jobId]: targetStage };
        persistStages(next);
        return next;
      });
    }
  }, []);

  const isLoading = loading || hubLoading;

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Briefcase className="h-7 w-7 text-blue-500" /> Jobs Pipeline
          </h1>
          <p className="text-slate-500 dark:text-slate-400">
            {allJobs.length} total jobs &bull; {filteredJobs.length} shown
            {hubJobs.length > 0 && <span className="ml-1 text-xs text-blue-500">(+{hubJobs.length} from Qdrant)</span>}
          </p>
        </div>
        <div className="flex gap-1 bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
          <button onClick={() => setViewMode('grid')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${viewMode === 'grid' ? 'bg-white dark:bg-slate-700 shadow text-slate-800 dark:text-slate-100' : 'text-slate-500 hover:text-slate-700'}`}>
            <LayoutGrid className="h-4 w-4" /> Grid
          </button>
          <button onClick={() => setViewMode('kanban')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${viewMode === 'kanban' ? 'bg-white dark:bg-slate-700 shadow text-slate-800 dark:text-slate-100' : 'text-slate-500 hover:text-slate-700'}`}>
            <Columns3 className="h-4 w-4" /> Kanban
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <div className="flex-1 min-w-64">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input type="text" placeholder="Search jobs, companies, programs..." value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <select value={companyFilter} onChange={e => setCompanyFilter(e.target.value)}
            className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-slate-100">
            <option value="all">All Companies</option>
            {companies.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <select value={locationFilter} onChange={e => setLocationFilter(e.target.value)}
          className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-slate-100">
          <option value="all">All Locations</option>
          {locations.map(l => <option key={l} value={l}>{l}</option>)}
        </select>
        <select value={clearanceFilter} onChange={e => setClearanceFilter(e.target.value)}
          className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-slate-100">
          <option value="all">All Clearances</option>
          {clearances.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={priorityFilter} onChange={e => setPriorityFilter(e.target.value)}
          className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-slate-100">
          <option value="all">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          viewMode === 'kanban' ? <KanbanSkeleton /> : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
            </div>
          )
        ) : filteredJobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <Search className="h-12 w-12 mb-4 text-slate-300" />
            <p>No jobs match your filters</p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredJobs.map(job => (
              <JobCard key={job.id} job={job}
                onNavigateToProgram={onNavigateToProgram}
                onNavigateToLocation={onNavigateToLocation}
                onNavigateToMindMap={onNavigateToMindMap}
                onNavigateToContact={onNavigateToContact} />
            ))}
          </div>
        ) : (
          <DndContext sensors={sensors} collisionDetection={closestCorners}
            onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
            <div className="flex gap-3 overflow-x-auto pb-4">
              {BD_STAGES.map(stage => (
                <KanbanColumn key={stage.id} stage={stage} jobs={jobsByStage[stage.id]}
                  onNavigateToProgram={onNavigateToProgram} onNavigateToContact={onNavigateToContact} />
              ))}
            </div>
            <DragOverlay>
              {activeJob && (
                <div className="opacity-90 rotate-1 scale-105 shadow-xl">
                  <KanbanCard job={activeJob} onNavigateToProgram={onNavigateToProgram} />
                </div>
              )}
            </DragOverlay>
          </DndContext>
        )}
      </div>
    </div>
  );
}
