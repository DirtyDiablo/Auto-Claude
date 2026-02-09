/**
 * Outreach Sequence Manager
 *
 * Connects to the N8N-Builder outreach API on :8300.
 * Two views: Sequence Timeline (per contact) and Portfolio Overview.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Mail, Plus, CheckCircle2, AlertCircle,
  Send, X, List, LayoutGrid, Phone, Building2,
  Loader2, ChevronRight, Linkedin,
  Users, Sparkles, ArrowRight, ExternalLink, GanttChart,
} from 'lucide-react';
import { hubApiClient } from '../services/hubApi';
import { SkeletonCard, SkeletonListItem } from '../components/ui/Skeleton';
import { ComposeModal } from '../components/ComposeModal';

// ─── Types ───────────────────────────────────────────────────────────────────

interface OutreachStep {
  step_number: number;
  type: 'email' | 'call' | 'linkedin' | 'case_study' | 'breakup';
  label: string;
  day: number;
  status: 'pending' | 'sent' | 'completed' | 'skipped' | 'bounced';
  sent_at?: string;
  content?: string;
}

interface OutreachSequence {
  id: string;
  contact_name: string;
  contact_email?: string;
  contact_phone?: string;
  program: string;
  tier: number;
  status: 'not_started' | 'active' | 'paused' | 'completed' | 'bounced';
  current_step: number;
  steps: OutreachStep[];
  created_at: string;
  updated_at?: string;
  next_action_due?: string;
}

interface DueAction {
  sequence_id: string;
  contact_name: string;
  program: string;
  step: OutreachStep;
  due_date: string;
}

interface OutreachManagerProps {
  loading?: boolean;
  onNavigateToContact?: (name: string) => void;
}

// ─── BD Formula Steps Template ───────────────────────────────────────────────

const BD_FORMULA_STEPS: Omit<OutreachStep, 'status'>[] = [
  { step_number: 1, type: 'email', label: 'Day 1 Intro Email', day: 1 },
  { step_number: 2, type: 'email', label: 'Day 3 Follow-up', day: 3 },
  { step_number: 3, type: 'call', label: 'Day 5 Call', day: 5 },
  { step_number: 4, type: 'linkedin', label: 'Day 7 LinkedIn', day: 7 },
  { step_number: 5, type: 'case_study', label: 'Day 10 Case Study', day: 10 },
  { step_number: 6, type: 'breakup', label: 'Day 14 Breakup Email', day: 14 },
];

// ─── Style Helpers ───────────────────────────────────────────────────────────

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  not_started: { bg: 'bg-slate-50 border-slate-200', text: 'text-slate-600', label: 'Not Started' },
  active: { bg: 'bg-green-50 border-green-200', text: 'text-green-700', label: 'Active' },
  paused: { bg: 'bg-yellow-50 border-yellow-200', text: 'text-yellow-700', label: 'Paused' },
  completed: { bg: 'bg-blue-50 border-blue-200', text: 'text-blue-700', label: 'Completed' },
  bounced: { bg: 'bg-red-50 border-red-200', text: 'text-red-700', label: 'Bounced' },
};

const STEP_STATUS_STYLES: Record<string, { bg: string; text: string }> = {
  pending: { bg: 'bg-slate-100', text: 'text-slate-600' },
  sent: { bg: 'bg-blue-100', text: 'text-blue-700' },
  completed: { bg: 'bg-green-100', text: 'text-green-700' },
  skipped: { bg: 'bg-gray-100', text: 'text-gray-500' },
  bounced: { bg: 'bg-red-100', text: 'text-red-700' },
};

const STEP_ICONS: Record<string, typeof Mail> = {
  email: Mail, call: Phone, linkedin: Linkedin, case_study: Send, breakup: X,
};

const TIER_COLORS = ['', 'bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-green-500', 'bg-blue-500', 'bg-gray-400'];

// ─── API helpers ─────────────────────────────────────────────────────────────

async function fetchSequences(): Promise<OutreachSequence[]> {
  const res = await fetch('/outreach/sequences', { signal: AbortSignal.timeout(5000) });
  if (!res.ok) throw new Error('Failed to fetch sequences');
  const data = await res.json();
  return data.sequences || data || [];
}

async function fetchDueActions(): Promise<DueAction[]> {
  const res = await fetch('/outreach/sequences/due', { signal: AbortSignal.timeout(5000) });
  if (!res.ok) return [];
  const data = await res.json();
  return data.due || data || [];
}

async function createSequence(body: Record<string, unknown>): Promise<OutreachSequence> {
  const res = await fetch('/outreach/sequences', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('Failed to create sequence');
  return res.json();
}

async function advanceStep(seqId: string, result: string): Promise<OutreachSequence> {
  const res = await fetch(`/outreach/sequences/${seqId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ result }),
  });
  if (!res.ok) throw new Error('Failed to advance step');
  return res.json();
}

// ─── Component ───────────────────────────────────────────────────────────────

export function OutreachManager({ loading = false, onNavigateToContact }: OutreachManagerProps) {
  const [sequences, setSequences] = useState<OutreachSequence[]>([]);
  const [dueActions, setDueActions] = useState<DueAction[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [serviceOnline, setServiceOnline] = useState(false);
  const [viewMode, setViewMode] = useState<'timeline' | 'portfolio' | 'gantt'>('timeline');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [generatingContent, setGeneratingContent] = useState<string | null>(null);
  const [generatedContent, setGeneratedContent] = useState<Record<string, string>>({});
  const [composeTarget, setComposeTarget] = useState<{ seq: OutreachSequence; stepIdx: number } | null>(null);

  // Load data
  useEffect(() => {
    async function load() {
      try {
        // Check outreach health first
        const healthRes = await fetch('/outreach/health', { signal: AbortSignal.timeout(3000) });
        if (!healthRes.ok) throw new Error();
        setServiceOnline(true);

        const [seqs, due] = await Promise.all([fetchSequences(), fetchDueActions()]);
        setSequences(seqs);
        setDueActions(due);
      } catch {
        setServiceOnline(false);
        // Generate mock data so the UI is usable
        setSequences(generateMockSequences());
      } finally {
        setDataLoading(false);
      }
    }
    load();
  }, []);

  const selected = useMemo(
    () => sequences.find(s => s.id === selectedId) || null,
    [sequences, selectedId]
  );

  const handleAdvance = useCallback(async (seqId: string) => {
    if (!serviceOnline) {
      // Optimistic local advance
      setSequences(prev => prev.map(s => {
        if (s.id !== seqId) return s;
        const steps = [...s.steps];
        if (steps[s.current_step]) steps[s.current_step] = { ...steps[s.current_step], status: 'sent' };
        return { ...s, steps, current_step: Math.min(s.current_step + 1, steps.length - 1) };
      }));
      return;
    }
    try {
      const updated = await advanceStep(seqId, 'sent');
      setSequences(prev => prev.map(s => s.id === seqId ? updated : s));
    } catch { /* keep current state */ }
  }, [serviceOnline]);

  const handleGenerateContent = useCallback(async (seqId: string, contactName: string, program: string) => {
    setGeneratingContent(seqId);
    try {
      const result = await hubApiClient.prepareOutreach(contactName, program);
      const content = typeof result.result === 'string' ? result.result :
        (result.result as Record<string, unknown>)?.content as string || JSON.stringify(result.result);
      setGeneratedContent(prev => ({ ...prev, [seqId]: content }));
    } catch {
      setGeneratedContent(prev => ({ ...prev, [seqId]: 'Content generation unavailable. Start the Hub API on :8100.' }));
    } finally {
      setGeneratingContent(null);
    }
  }, []);

  const handleCreate = useCallback(async (body: Record<string, unknown>) => {
    if (serviceOnline) {
      try {
        const seq = await createSequence(body);
        setSequences(prev => [seq, ...prev]);
        setShowCreateModal(false);
        return;
      } catch { /* fall through */ }
    }
    // Local creation
    const seq: OutreachSequence = {
      id: `local-${Date.now()}`,
      contact_name: String(body.contact_name || ''),
      contact_email: String(body.contact_email || ''),
      contact_phone: String(body.contact_phone || ''),
      program: String(body.program || ''),
      tier: Number(body.tier || 3),
      status: 'not_started',
      current_step: 0,
      steps: BD_FORMULA_STEPS.map(s => ({ ...s, status: 'pending' as const })),
      created_at: new Date().toISOString(),
    };
    setSequences(prev => [seq, ...prev]);
    setShowCreateModal(false);
  }, [serviceOnline]);

  if (loading || dataLoading) {
    return (
      <div className="p-6 space-y-4">
        <div className="h-10 w-64 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
        <div className="flex gap-4">
          <div className="w-80 space-y-2">{Array.from({ length: 5 }).map((_, i) => <SkeletonListItem key={i} />)}</div>
          <div className="flex-1"><SkeletonCard /></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-5 overflow-auto h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <Send className="h-7 w-7 text-blue-500" /> Outreach Manager
          </h1>
          <p className="text-slate-500 dark:text-slate-400">
            {sequences.length} sequences &middot; {dueActions.length} due actions
            {!serviceOnline && (
              <span className="ml-2 text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded">
                Offline — mock data
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-3">
          <div className="flex gap-1 bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
            <button onClick={() => setViewMode('timeline')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${viewMode === 'timeline' ? 'bg-white dark:bg-slate-700 shadow text-slate-800 dark:text-slate-100' : 'text-slate-500'}`}>
              <List className="h-4 w-4" /> Timeline
            </button>
            <button onClick={() => setViewMode('portfolio')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${viewMode === 'portfolio' ? 'bg-white dark:bg-slate-700 shadow text-slate-800 dark:text-slate-100' : 'text-slate-500'}`}>
              <LayoutGrid className="h-4 w-4" /> Portfolio
            </button>
            <button onClick={() => setViewMode('gantt')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${viewMode === 'gantt' ? 'bg-white dark:bg-slate-700 shadow text-slate-800 dark:text-slate-100' : 'text-slate-500'}`}>
              <GanttChart className="h-4 w-4" /> Gantt
            </button>
          </div>
          <button onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-sm">
            <Plus className="h-4 w-4" /> New Sequence
          </button>
        </div>
      </div>

      {/* Due Actions Banner */}
      {dueActions.length > 0 && (
        <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-xl p-4">
          <h3 className="font-semibold text-orange-800 dark:text-orange-300 flex items-center gap-2 mb-2">
            <AlertCircle className="h-5 w-5" /> Due Today ({dueActions.length})
          </h3>
          <div className="space-y-1">
            {dueActions.slice(0, 5).map((a, i) => (
              <div key={i} className="flex items-center justify-between bg-white dark:bg-slate-800 rounded-lg p-2 border border-orange-100 dark:border-orange-800 cursor-pointer hover:shadow-sm"
                onClick={() => { setSelectedId(a.sequence_id); setViewMode('timeline'); }}>
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-orange-600" />
                  <span className="text-sm font-medium text-slate-800 dark:text-slate-100">{a.contact_name}</span>
                  <span className="text-xs text-slate-500">{a.step.label}</span>
                </div>
                <ChevronRight className="h-4 w-4 text-slate-400" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Views */}
      {viewMode === 'timeline' ? (
        <TimelineView
          sequences={sequences}
          selected={selected}
          onSelect={setSelectedId}
          onAdvance={handleAdvance}
          onGenerateContent={handleGenerateContent}
          generatingContent={generatingContent}
          generatedContent={generatedContent}
          onNavigateToContact={onNavigateToContact}
          onCompose={(seq, stepIdx) => setComposeTarget({ seq, stepIdx })}
        />
      ) : viewMode === 'gantt' ? (
        <GanttView sequences={sequences} onSelect={id => { setSelectedId(id); setViewMode('timeline'); }} />
      ) : (
        <PortfolioView
          sequences={sequences}
          onSelect={id => { setSelectedId(id); setViewMode('timeline'); }}
          onNavigateToContact={onNavigateToContact}
        />
      )}

      {/* Create Modal */}
      {showCreateModal && <CreateModal onClose={() => setShowCreateModal(false)} onCreate={handleCreate} />}

      {composeTarget && (
        <ComposeModal
          sequence={composeTarget.seq}
          stepIndex={composeTarget.stepIdx}
          onClose={() => setComposeTarget(null)}
          onSent={(seqId) => { handleAdvance(seqId); setComposeTarget(null); }}
          generatedContent={generatedContent[`${composeTarget.seq.id}-${composeTarget.stepIdx}`]}
        />
      )}
    </div>
  );
}

// ─── Timeline View ───────────────────────────────────────────────────────────

function TimelineView({
  sequences, selected, onSelect, onAdvance, onGenerateContent,
  generatingContent, generatedContent, onNavigateToContact, onCompose,
}: {
  sequences: OutreachSequence[];
  selected: OutreachSequence | null;
  onSelect: (id: string | null) => void;
  onAdvance: (id: string) => void;
  onGenerateContent: (id: string, contact: string, program: string) => void;
  generatingContent: string | null;
  generatedContent: Record<string, string>;
  onNavigateToContact?: (name: string) => void;
  onCompose?: (seq: OutreachSequence, stepIdx: number) => void;
}) {
  return (
    <div className="flex gap-6 min-h-[500px]">
      {/* Left: sequence list */}
      <div className="w-80 flex-shrink-0 space-y-2 overflow-y-auto max-h-[calc(100vh-300px)]">
        {sequences.map(seq => {
          const style = STATUS_STYLES[seq.status] || STATUS_STYLES.not_started;
          const isSelected = selected?.id === seq.id;
          return (
            <div key={seq.id} onClick={() => onSelect(seq.id)}
              className={`p-3 rounded-lg border cursor-pointer transition-all ${isSelected ? 'ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-900/20 border-blue-200' : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:shadow-sm'}`}>
              <div className="flex items-center gap-2 mb-1">
                <div className={`w-2 h-2 rounded-full ${TIER_COLORS[seq.tier] || 'bg-gray-400'}`} />
                <span className="font-medium text-sm text-slate-800 dark:text-slate-100 truncate">{seq.contact_name}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span>{seq.program}</span>
                <span>&middot;</span>
                <span className={`px-1.5 py-0.5 rounded ${style.bg} ${style.text} border text-[10px] font-medium`}>{style.label}</span>
              </div>
              <div className="mt-1.5 flex gap-0.5">
                {seq.steps.map((step, i) => (
                  <div key={i} className={`flex-1 h-1 rounded-full ${step.status === 'completed' || step.status === 'sent' ? 'bg-green-400' : i === seq.current_step ? 'bg-blue-400' : 'bg-slate-200 dark:bg-slate-600'}`} />
                ))}
              </div>
            </div>
          );
        })}
        {sequences.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            <Send className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No sequences yet</p>
          </div>
        )}
      </div>

      {/* Right: timeline detail */}
      {selected ? (
        <div className="flex-1 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 overflow-y-auto max-h-[calc(100vh-300px)]">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">{selected.contact_name}</h2>
              <div className="flex items-center gap-3 mt-1 text-sm text-slate-500">
                <span className="flex items-center gap-1"><Building2 className="h-4 w-4" /> {selected.program}</span>
                <span>Tier {selected.tier}</span>
                {selected.contact_email && <span>{selected.contact_email}</span>}
              </div>
            </div>
            <div className="flex gap-2">
              {onNavigateToContact && (
                <button onClick={() => onNavigateToContact(selected.contact_name)}
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                  <ExternalLink className="h-3 w-3" /> View Contact
                </button>
              )}
              <button onClick={() => onSelect(null)}
                className="p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg">
                <X className="h-5 w-5 text-slate-400" />
              </button>
            </div>
          </div>

          {/* Steps timeline */}
          <div className="space-y-0">
            {selected.steps.map((step, idx) => {
              const Icon = STEP_ICONS[step.type] || Mail;
              const stepStyle = STEP_STATUS_STYLES[step.status] || STEP_STATUS_STYLES.pending;
              const isCurrent = idx === selected.current_step && selected.status === 'active';

              return (
                <div key={idx} className="flex gap-4">
                  {/* Timeline line */}
                  <div className="flex flex-col items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${isCurrent ? 'bg-blue-500 text-white' : step.status === 'completed' || step.status === 'sent' ? 'bg-green-500 text-white' : 'bg-slate-200 dark:bg-slate-600 text-slate-500'}`}>
                      {step.status === 'completed' || step.status === 'sent' ? <CheckCircle2 className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                    </div>
                    {idx < selected.steps.length - 1 && <div className="w-0.5 flex-1 bg-slate-200 dark:bg-slate-600 my-1" />}
                  </div>

                  {/* Step content */}
                  <div className={`flex-1 pb-6 ${idx === selected.steps.length - 1 ? 'pb-0' : ''}`}>
                    <div className={`rounded-lg p-4 border ${isCurrent ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' : 'bg-slate-50 dark:bg-slate-900/30 border-slate-200 dark:border-slate-700'}`}>
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-medium text-sm text-slate-800 dark:text-slate-100">{step.label}</h4>
                        <span className={`text-[10px] font-medium px-2 py-0.5 rounded ${stepStyle.bg} ${stepStyle.text}`}>
                          {step.status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mb-2">Day {step.day} &middot; {step.type}</p>

                      {step.content && (
                        <p className="text-sm text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 rounded p-2 mb-2 border border-slate-100 dark:border-slate-700">
                          {step.content}
                        </p>
                      )}

                      {generatedContent[`${selected.id}-${idx}`] && (
                        <div className="text-sm text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-900/20 rounded p-2 mb-2 border border-indigo-100 dark:border-indigo-800">
                          <div className="flex items-center gap-1 mb-1">
                            <Sparkles className="h-3 w-3" /> <span className="text-xs font-medium">AI Generated</span>
                          </div>
                          {generatedContent[`${selected.id}-${idx}`]}
                        </div>
                      )}

                      {isCurrent && (
                        <div className="flex gap-2 mt-2">
                          <button onClick={() => onCompose?.(selected, idx)}
                            className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-medium hover:bg-green-700">
                            <Mail className="h-3 w-3" /> Compose
                          </button>
                          <button onClick={() => onAdvance(selected.id)}
                            className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700">
                            <ArrowRight className="h-3 w-3" /> Advance
                          </button>
                          <button
                            onClick={() => onGenerateContent(`${selected.id}-${idx}`, selected.contact_name, selected.program)}
                            disabled={generatingContent === `${selected.id}-${idx}`}
                            className="flex items-center gap-1 px-3 py-1.5 bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 rounded-lg text-xs font-medium hover:bg-indigo-100 disabled:opacity-50">
                            {generatingContent === `${selected.id}-${idx}` ? <Loader2 className="h-3 w-3 animate-spin" /> : <Sparkles className="h-3 w-3" />}
                            Generate Content
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-slate-400 dark:text-slate-500">
          <div className="text-center">
            <Users className="h-12 w-12 mx-auto mb-3 opacity-40" />
            <p>Select a sequence to view timeline</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Portfolio View ──────────────────────────────────────────────────────────

function PortfolioView({
  sequences, onSelect, onNavigateToContact,
}: {
  sequences: OutreachSequence[];
  onSelect: (id: string) => void;
  onNavigateToContact?: (name: string) => void;
}) {
  const [sortBy, setSortBy] = useState<'program' | 'tier' | 'created' | 'status'>('tier');

  const sorted = useMemo(() => {
    const copy = [...sequences];
    switch (sortBy) {
      case 'tier': return copy.sort((a, b) => a.tier - b.tier);
      case 'program': return copy.sort((a, b) => a.program.localeCompare(b.program));
      case 'created': return copy.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      case 'status': return copy.sort((a, b) => a.status.localeCompare(b.status));
      default: return copy;
    }
  }, [sequences, sortBy]);

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <span className="text-sm text-slate-500">Sort by:</span>
        {(['tier', 'program', 'status', 'created'] as const).map(s => (
          <button key={s} onClick={() => setSortBy(s)}
            className={`px-3 py-1 rounded-lg text-xs font-medium ${sortBy === s ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'}`}>
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 dark:bg-slate-900/50">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-300">Contact</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-300">Program</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600 dark:text-slate-300">Tier</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-300">Step</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-300">Status</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-300">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {sorted.map(seq => {
              const style = STATUS_STYLES[seq.status] || STATUS_STYLES.not_started;
              return (
                <tr key={seq.id} onClick={() => onSelect(seq.id)}
                  className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                  <td className="px-4 py-3">
                    <button onClick={e => { e.stopPropagation(); onNavigateToContact?.(seq.contact_name); }}
                      className="font-medium text-blue-600 dark:text-blue-400 hover:underline">{seq.contact_name}</button>
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{seq.program}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-block w-6 h-6 rounded-full text-white text-xs font-bold leading-6 text-center ${TIER_COLORS[seq.tier] || 'bg-gray-400'}`}>
                      {seq.tier}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                    {seq.steps[seq.current_step]?.label || `Step ${seq.current_step + 1}`}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${style.bg} ${style.text}`}>
                      {style.label}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-xs">{new Date(seq.created_at).toLocaleDateString()}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {sorted.length === 0 && (
          <div className="text-center py-12 text-slate-400">No sequences found</div>
        )}
      </div>
    </div>
  );
}

// ─── Gantt View ─────────────────────────────────────────────────────────────

function GanttView({ sequences, onSelect }: { sequences: OutreachSequence[]; onSelect: (id: string) => void }) {
  const days = useMemo(() => {
    const result: Date[] = [];
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    for (let i = 0; i < 14; i++) {
      const d = new Date(start);
      d.setDate(d.getDate() + i);
      result.push(d);
    }
    return result;
  }, []);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-x-auto">
      <table className="w-full text-xs min-w-[800px]">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700">
            <th className="text-left px-3 py-2 font-medium text-slate-600 dark:text-slate-300 w-48 sticky left-0 bg-white dark:bg-slate-800 z-10">Contact</th>
            {days.map((d, i) => {
              const isToday = d.getTime() === today.getTime();
              return (
                <th key={i} className={`text-center px-1 py-2 font-medium min-w-[48px] ${isToday ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300' : 'text-slate-500'}`}>
                  <div>{d.toLocaleDateString('en-US', { weekday: 'short' })}</div>
                  <div className="text-[10px]">{d.getDate()}</div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {sequences.map(seq => {
            const created = new Date(seq.created_at);
            created.setHours(0, 0, 0, 0);

            const statusBg = seq.status === 'completed' ? 'bg-blue-50/50 dark:bg-blue-900/10'
              : seq.status === 'paused' ? 'bg-yellow-50/50 dark:bg-yellow-900/10'
              : '';

            return (
              <tr key={seq.id} className={`border-b border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/30 cursor-pointer ${statusBg}`}
                onClick={() => onSelect(seq.id)}>
                <td className="px-3 py-2 sticky left-0 bg-white dark:bg-slate-800 z-10">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${TIER_COLORS[seq.tier] || 'bg-gray-400'}`} />
                    <div>
                      <p className="font-medium text-slate-800 dark:text-slate-100 truncate max-w-[160px]">{seq.contact_name}</p>
                      <p className="text-[10px] text-slate-400 truncate max-w-[160px]">{seq.program}</p>
                    </div>
                  </div>
                </td>
                {days.map((day, di) => {
                  const dayOffset = Math.floor((day.getTime() - created.getTime()) / 86400000);
                  const step = seq.steps.find(s => s.day === dayOffset || s.day === dayOffset + 1);
                  const isToday = day.getTime() === today.getTime();

                  let dot = null;
                  if (step) {
                    const color = step.status === 'completed' || step.status === 'sent'
                      ? 'bg-green-500' : step.status === 'pending'
                      ? (dayOffset < 0 ? 'bg-red-500' : 'bg-blue-500')
                      : step.status === 'skipped' ? 'bg-gray-400'
                      : 'bg-yellow-500';
                    const Icon = STEP_ICONS[step.type] || Mail;
                    dot = (
                      <div className="relative group">
                        <div className={`w-5 h-5 rounded-full ${color} flex items-center justify-center mx-auto`}>
                          <Icon className="h-2.5 w-2.5 text-white" />
                        </div>
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block z-20 whitespace-nowrap bg-slate-900 text-white text-[10px] px-2 py-1 rounded shadow-lg">
                          {step.label} — {step.status}
                        </div>
                      </div>
                    );
                  }

                  return (
                    <td key={di} className={`text-center px-1 py-2 ${isToday ? 'bg-blue-50/50 dark:bg-blue-900/10' : ''}`}>
                      {dot}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      {sequences.length === 0 && (
        <div className="text-center py-12 text-slate-400">No sequences to display</div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-4 px-4 py-2 border-t border-slate-200 dark:border-slate-700 text-[10px] text-slate-500">
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-green-500 inline-block" /> Completed</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" /> Scheduled</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" /> Overdue</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-yellow-500 inline-block" /> Pending</span>
      </div>
    </div>
  );
}

// ─── Create Modal ────────────────────────────────────────────────────────────

function CreateModal({ onClose, onCreate }: { onClose: () => void; onCreate: (body: Record<string, unknown>) => void }) {
  const [form, setForm] = useState({ contact_name: '', contact_email: '', contact_phone: '', program: '', tier: '3' });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.contact_name) return;
    setSubmitting(true);
    await onCreate({ ...form, tier: parseInt(form.tier) });
    setSubmitting(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">New Outreach Sequence</h2>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg"><X className="h-5 w-5 text-slate-400" /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Contact Name *</label>
            <input required value={form.contact_name} onChange={e => setForm(p => ({ ...p, contact_name: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 dark:text-slate-100" placeholder="Sarah Mitchell" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Email</label>
            <input type="email" value={form.contact_email} onChange={e => setForm(p => ({ ...p, contact_email: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 dark:text-slate-100" placeholder="sarah@leidos.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Phone</label>
            <input value={form.contact_phone} onChange={e => setForm(p => ({ ...p, contact_phone: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 dark:text-slate-100" placeholder="703-555-0123" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Program *</label>
            <select value={form.program} onChange={e => setForm(p => ({ ...p, program: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 dark:text-slate-100">
              <option value="">Select program...</option>
              {['AF DCGS - Langley', 'AF DCGS - Wright-Patt', 'AF DCGS - PACAF', 'Army DCGS-A', 'Navy DCGS-N', 'GBSD', 'JSTARS', 'Enterprise Security'].map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Tier</label>
            <select value={form.tier} onChange={e => setForm(p => ({ ...p, tier: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 dark:text-slate-100">
              {[1,2,3,4,5,6].map(t => <option key={t} value={t}>Tier {t}</option>)}
            </select>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={submitting || !form.contact_name}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />} Create
            </button>
            <button type="button" onClick={onClose} className="px-4 py-2.5 text-slate-600 dark:text-slate-300">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

function generateMockSequences(): OutreachSequence[] {
  const contacts = [
    { name: 'Sarah Mitchell', email: 'sarah.m@leidos.com', program: 'AF DCGS - Langley', tier: 2 },
    { name: 'James Rodriguez', email: 'j.rodriguez@ng.com', program: 'Army DCGS-A', tier: 1 },
    { name: 'Maria Chen', email: 'maria.chen@gdit.com', program: 'Navy DCGS-N', tier: 3 },
    { name: 'David Park', email: 'd.park@raytheon.com', program: 'GBSD', tier: 2 },
    { name: 'Karen Williams', email: 'k.williams@bae.com', program: 'AF DCGS - PACAF', tier: 4 },
  ];

  return contacts.map((c, i) => ({
    id: `mock-${i + 1}`,
    contact_name: c.name,
    contact_email: c.email,
    program: c.program,
    tier: c.tier,
    status: (['active', 'active', 'paused', 'completed', 'not_started'] as const)[i],
    current_step: [2, 1, 3, 5, 0][i],
    steps: BD_FORMULA_STEPS.map((s, si) => ({
      ...s,
      status: si < [2, 1, 3, 5, 0][i] ? 'completed' as const : si === [2, 1, 3, 5, 0][i] ? 'pending' as const : 'pending' as const,
    })),
    created_at: new Date(Date.now() - (i + 1) * 5 * 86400000).toISOString(),
  }));
}

export default OutreachManager;
