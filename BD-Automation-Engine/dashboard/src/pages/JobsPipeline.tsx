import { useState, useMemo, useCallback } from 'react';
import {
  Search, Filter, ExternalLink, MapPin, Shield, Building2,
  Network, Briefcase, Tag, LayoutGrid, Columns3, GripVertical,
} from 'lucide-react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  PointerSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import { useDroppable } from '@dnd-kit/core';
import type { Job } from '../types';
import type { NativeNodeType } from '../configs/nativeNodeConfigs';

interface JobsPipelineProps {
  jobs: Job[];
  loading: boolean;
  onNavigateToProgram?: (programName: string) => void;
  onNavigateToLocation?: (location: string) => void;
  onNavigateToMindMap?: (entityType: NativeNodeType, entityId: string, entityLabel: string) => void;
}

// ─── BD Workflow Stages ──────────────────────────────────────────────────────

const BD_STAGES = [
  { id: 'scraped', label: 'Scraped', color: 'bg-slate-100 border-slate-300 text-slate-700' },
  { id: 'enriched', label: 'Enriched', color: 'bg-blue-50 border-blue-300 text-blue-700' },
  { id: 'mapped', label: 'Mapped', color: 'bg-cyan-50 border-cyan-300 text-cyan-700' },
  { id: 'contact_found', label: 'Contact Found', color: 'bg-purple-50 border-purple-300 text-purple-700' },
  { id: 'outreach_active', label: 'Outreach Active', color: 'bg-orange-50 border-orange-300 text-orange-700' },
  { id: 'meeting_set', label: 'Meeting Set', color: 'bg-amber-50 border-amber-300 text-amber-700' },
  { id: 'closed_won', label: 'Closed/Won', color: 'bg-green-50 border-green-300 text-green-700' },
] as const;

type StageId = (typeof BD_STAGES)[number]['id'];

function inferStage(job: Job): StageId {
  const status = (job.status || '').toLowerCase();
  if (status === 'closed' || status === 'won' || status === 'closed/won') return 'closed_won';
  if (status === 'meeting' || status === 'meeting set') return 'meeting_set';
  if (status === 'outreach' || status === 'outreach active' || status === 'contacted') return 'outreach_active';
  if (status === 'contact found' || status === 'pursuing') return 'contact_found';
  if (job.program && job.program !== 'Unknown') return 'mapped';
  if (job.bd_priority !== null && job.bd_priority !== undefined) return 'enriched';
  return 'scraped';
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function getPriorityBadge(priority: number | string | null): { color: string; label: string } {
  if (priority === null || priority === undefined) {
    return { color: 'bg-gray-100 text-gray-600', label: 'Unrated' };
  }
  if (typeof priority === 'number') {
    if (priority >= 80) return { color: 'bg-red-100 text-red-700', label: 'Critical' };
    if (priority >= 60) return { color: 'bg-orange-100 text-orange-700', label: 'High' };
    if (priority >= 40) return { color: 'bg-yellow-100 text-yellow-700', label: 'Medium' };
    if (priority >= 0) return { color: 'bg-green-100 text-green-700', label: 'Low' };
    return { color: 'bg-gray-100 text-gray-600', label: 'Unrated' };
  }
  const str = String(priority).toLowerCase();
  if (str.includes('critical') || str.includes('🔴')) return { color: 'bg-red-100 text-red-700', label: 'Critical' };
  if (str.includes('high') || str.includes('🟠')) return { color: 'bg-orange-100 text-orange-700', label: 'High' };
  if (str.includes('medium') || str.includes('🟡')) return { color: 'bg-yellow-100 text-yellow-700', label: 'Medium' };
  if (str.includes('low') || str.includes('🟢')) return { color: 'bg-green-100 text-green-700', label: 'Low' };
  return { color: 'bg-gray-100 text-gray-600', label: 'Unrated' };
}

function getStatusBadge(status: string): { color: string } {
  const s = status?.toLowerCase() || '';
  if (s === 'new') return { color: 'bg-blue-100 text-blue-700' };
  if (s === 'reviewing') return { color: 'bg-yellow-100 text-yellow-700' };
  if (s === 'pursuing') return { color: 'bg-green-100 text-green-700' };
  if (s === 'contacted') return { color: 'bg-orange-100 text-orange-700' };
  if (s === 'closed') return { color: 'bg-gray-100 text-gray-600' };
  return { color: 'bg-slate-100 text-slate-600' };
}

// ─── Job Card ────────────────────────────────────────────────────────────────

function JobCard({
  job,
  compact = false,
  onNavigateToProgram,
  onNavigateToLocation,
  onNavigateToMindMap,
}: {
  job: Job;
  compact?: boolean;
  onNavigateToProgram?: (programName: string) => void;
  onNavigateToLocation?: (location: string) => void;
  onNavigateToMindMap?: (entityType: NativeNodeType, entityId: string, entityLabel: string) => void;
}) {
  const priority = getPriorityBadge(job.bd_priority);
  const statusBadge = getStatusBadge(job.status);
  const programName = job.program || job.program_name;

  if (compact) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-3 hover:shadow-md transition-shadow cursor-grab active:cursor-grabbing">
        <div className="flex items-center gap-2 mb-1.5">
          <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${priority.color}`}>
            {priority.label}
          </span>
          {job.clearance && (
            <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 flex items-center gap-0.5">
              <Shield className="h-2.5 w-2.5" />
              {job.clearance}
            </span>
          )}
        </div>
        <h4 className="text-sm font-medium text-slate-800 line-clamp-2">{job.title || 'Untitled'}</h4>
        {job.company && (
          <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            <Building2 className="h-3 w-3" />
            {job.company}
          </p>
        )}
        {programName && (
          <button
            onClick={(e) => { e.stopPropagation(); onNavigateToProgram?.(programName); }}
            className="text-xs text-blue-600 hover:underline mt-1"
          >
            {programName}
          </button>
        )}
        {typeof job.bd_priority === 'number' && (
          <p className="text-[10px] text-slate-400 mt-1">Score: {job.bd_priority}</p>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className={`text-xs font-medium px-2 py-0.5 rounded ${priority.color}`}>
              {priority.label}
            </span>
            {job.clearance && (
              <span className="text-xs font-medium px-2 py-0.5 rounded bg-purple-100 text-purple-700 flex items-center gap-1">
                <Shield className="h-3 w-3" />
                {job.clearance}
              </span>
            )}
            {job.status && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded ${statusBadge.color}`}>
                {job.status}
              </span>
            )}
            {job.dcgs_relevance && (
              <span className="text-xs font-medium px-2 py-0.5 rounded bg-red-50 text-red-600">
                DCGS
              </span>
            )}
          </div>
          <h3 className="font-semibold text-slate-900 line-clamp-2">{job.title || 'Untitled Job'}</h3>
          <div className="mt-2 space-y-1.5">
            {job.company && (
              <p className="text-sm text-slate-600 flex items-center gap-1.5">
                <Building2 className="h-3.5 w-3.5 text-slate-400" />
                {job.company}
              </p>
            )}
            {(job.location || job.city) && (
              <button
                onClick={() => onNavigateToLocation?.(job.location || job.city)}
                className="text-sm text-slate-500 hover:text-blue-600 flex items-center gap-1.5 transition-colors"
              >
                <MapPin className="h-3.5 w-3.5 text-slate-400" />
                <span className="hover:underline">
                  {job.city && job.location ? `${job.city}, ${job.location}` : job.location || job.city}
                </span>
              </button>
            )}
            {job.agency && (
              <p className="text-sm text-slate-500 flex items-center gap-1.5">
                <Briefcase className="h-3.5 w-3.5 text-slate-400" />
                {job.agency}
              </p>
            )}
            {job.functional_area && (
              <p className="text-sm text-slate-500 flex items-center gap-1.5">
                <Tag className="h-3.5 w-3.5 text-slate-400" />
                {job.functional_area}
              </p>
            )}
          </div>
          {programName && (
            <button
              onClick={() => onNavigateToProgram?.(programName)}
              className="mt-2 text-sm text-blue-600 font-medium hover:text-blue-800 hover:underline transition-colors"
            >
              {programName}
            </button>
          )}
          {job.task_order && (
            <p className="mt-1 text-xs text-slate-400">Task Order: {job.task_order}</p>
          )}
        </div>
        <div className="flex items-start gap-1">
          {onNavigateToMindMap && (
            <button
              onClick={() => onNavigateToMindMap('JOB', job.id, job.title)}
              className="p-2 text-slate-400 hover:text-purple-600 transition-colors"
              title="Explore in Mind Map"
            >
              <Network className="h-4 w-4" />
            </button>
          )}
          {job.source_url && (
            <a
              href={job.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-slate-400 hover:text-blue-600 transition-colors"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          )}
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
        <span className="text-xs text-slate-400">{job.source || 'Insight Global'}</span>
        <div className="flex items-center gap-3">
          {job.scraped_at && (
            <span className="text-xs text-slate-400">{new Date(job.scraped_at).toLocaleDateString()}</span>
          )}
          {typeof job.bd_priority === 'number' && job.bd_priority >= 0 && (
            <span className="text-xs font-medium text-slate-500">Score: {job.bd_priority}</span>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Kanban Column ───────────────────────────────────────────────────────────

function KanbanColumn({
  stage,
  jobs,
  onNavigateToProgram,
}: {
  stage: (typeof BD_STAGES)[number];
  jobs: Job[];
  onNavigateToProgram?: (programName: string) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: stage.id });

  return (
    <div
      ref={setNodeRef}
      className={`flex flex-col min-w-[220px] w-[220px] transition-colors rounded-xl ${
        isOver ? 'bg-blue-50' : ''
      }`}
    >
      <div className={`rounded-t-xl px-3 py-2 border ${stage.color} flex items-center justify-between`}>
        <span className="text-xs font-semibold truncate">{stage.label}</span>
        <span className="text-xs font-bold ml-1">{jobs.length}</span>
      </div>
      <div className="flex-1 space-y-2 p-2 overflow-y-auto max-h-[calc(100vh-300px)] bg-slate-50/50 rounded-b-xl border border-t-0 border-slate-200">
        {jobs.map(job => (
          <div key={job.id} data-job-id={job.id}>
            <JobCard job={job} compact onNavigateToProgram={onNavigateToProgram} />
          </div>
        ))}
        {jobs.length === 0 && (
          <div className="text-center py-6 text-xs text-slate-400">
            <GripVertical className="h-5 w-5 mx-auto mb-1 opacity-40" />
            Drop here
          </div>
        )}
      </div>
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
}: JobsPipelineProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [clearanceFilter, setClearanceFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [agencyFilter, setAgencyFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'kanban'>('grid');
  const [stageOverrides, setStageOverrides] = useState<Record<string, StageId>>({});
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
  );

  const clearances = useMemo(() => {
    const unique = new Set(jobs.map(j => j.clearance).filter(Boolean));
    return Array.from(unique).sort();
  }, [jobs]);

  const agencies = useMemo(() => {
    const unique = new Set(jobs.map(j => j.agency).filter(Boolean));
    return Array.from(unique).sort();
  }, [jobs]);

  const statuses = useMemo(() => {
    const unique = new Set(jobs.map(j => j.status).filter(Boolean));
    return Array.from(unique).sort();
  }, [jobs]);

  const filteredJobs = useMemo(() => {
    return jobs.filter(job => {
      if (!job.title) return false;
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const programName = job.program || job.program_name || '';
        const matchesSearch =
          job.title?.toLowerCase().includes(query) ||
          job.company?.toLowerCase().includes(query) ||
          job.location?.toLowerCase().includes(query) ||
          job.city?.toLowerCase().includes(query) ||
          programName.toLowerCase().includes(query) ||
          job.agency?.toLowerCase().includes(query) ||
          job.functional_area?.toLowerCase().includes(query);
        if (!matchesSearch) return false;
      }
      if (clearanceFilter !== 'all' && job.clearance !== clearanceFilter) return false;
      if (priorityFilter !== 'all') {
        const priority = getPriorityBadge(job.bd_priority).label.toLowerCase();
        if (priority !== priorityFilter) return false;
      }
      if (agencyFilter !== 'all' && job.agency !== agencyFilter) return false;
      if (statusFilter !== 'all' && job.status !== statusFilter) return false;
      return true;
    });
  }, [jobs, searchQuery, clearanceFilter, priorityFilter, agencyFilter, statusFilter]);

  // Group jobs by kanban stage
  const jobsByStage = useMemo(() => {
    const groups: Record<StageId, Job[]> = {
      scraped: [], enriched: [], mapped: [],
      contact_found: [], outreach_active: [], meeting_set: [], closed_won: [],
    };
    filteredJobs.forEach(job => {
      const stage = stageOverrides[job.id] || inferStage(job);
      groups[stage].push(job);
    });
    return groups;
  }, [filteredJobs, stageOverrides]);

  const activeJob = useMemo(
    () => (activeJobId ? filteredJobs.find(j => j.id === activeJobId) || null : null),
    [activeJobId, filteredJobs]
  );

  const handleDragStart = useCallback((event: DragStartEvent) => {
    setActiveJobId(String(event.active.id));
  }, []);

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    setActiveJobId(null);
    const { active, over } = event;
    if (!over) return;
    const jobId = String(active.id);
    const targetStage = String(over.id) as StageId;
    if (BD_STAGES.some(s => s.id === targetStage)) {
      setStageOverrides(prev => ({ ...prev, [jobId]: targetStage }));
    }
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Jobs Pipeline</h1>
          <p className="text-slate-500">{jobs.length} total jobs &bull; {filteredJobs.length} shown</p>
        </div>
        <div className="flex gap-1 bg-slate-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode('grid')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'grid' ? 'bg-white shadow text-slate-800' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <LayoutGrid className="h-4 w-4" /> Grid
          </button>
          <button
            onClick={() => setViewMode('kanban')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'kanban' ? 'bg-white shadow text-slate-800' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <Columns3 className="h-4 w-4" /> Kanban
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="flex-1 min-w-64">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search jobs, companies, programs, locations..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <select
            value={clearanceFilter}
            onChange={e => setClearanceFilter(e.target.value)}
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Clearances</option>
            {clearances.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <select
          value={agencyFilter}
          onChange={e => setAgencyFilter(e.target.value)}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Agencies</option>
          {agencies.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Statuses</option>
          {statuses.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select
          value={priorityFilter}
          onChange={e => setPriorityFilter(e.target.value)}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="unrated">Unrated</option>
        </select>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {filteredJobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <Search className="h-12 w-12 mb-4 text-slate-300" />
            <p>No jobs match your filters</p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredJobs.map(job => (
              <JobCard
                key={job.id}
                job={job}
                onNavigateToProgram={onNavigateToProgram}
                onNavigateToLocation={onNavigateToLocation}
                onNavigateToMindMap={onNavigateToMindMap}
              />
            ))}
          </div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <div className="flex gap-3 overflow-x-auto pb-4">
              {BD_STAGES.map(stage => (
                <KanbanColumn
                  key={stage.id}
                  stage={stage}
                  jobs={jobsByStage[stage.id]}
                  onNavigateToProgram={onNavigateToProgram}
                />
              ))}
            </div>
            <DragOverlay>
              {activeJob && (
                <div className="opacity-80 rotate-2 scale-105">
                  <JobCard job={activeJob} compact onNavigateToProgram={onNavigateToProgram} />
                </div>
              )}
            </DragOverlay>
          </DndContext>
        )}
      </div>
    </div>
  );
}
