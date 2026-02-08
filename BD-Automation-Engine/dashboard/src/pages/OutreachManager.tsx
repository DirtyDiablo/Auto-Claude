/**
 * Outreach Sequence Manager
 *
 * Connects to the outreach sequence engine on Terminal C (port 8300).
 * Falls back to mock data when the service is unavailable.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Mail,
  Plus,
  Calendar,
  Clock,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  Send,
  X,
  LayoutGrid,
  List,
  Phone,
  User,
  Building2,
  Loader2,
  PauseCircle,
  PlayCircle,
  Trash2,
} from 'lucide-react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface OutreachStep {
  id: string;
  type: 'email' | 'call' | 'linkedin' | 'meeting';
  subject: string;
  scheduled_date: string;
  status: 'pending' | 'sent' | 'completed' | 'skipped';
  notes?: string;
}

interface OutreachSequence {
  id: string;
  contact_name: string;
  company: string;
  program: string;
  status: 'active' | 'paused' | 'completed' | 'draft';
  created_at: string;
  steps: OutreachStep[];
  current_step: number;
  priority: 'high' | 'medium' | 'low';
}

interface OutreachManagerProps {
  loading?: boolean;
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const MOCK_SEQUENCES: OutreachSequence[] = [
  {
    id: 'seq-001',
    contact_name: 'Sarah Mitchell',
    company: 'Leidos',
    program: 'DCGS-A',
    status: 'active',
    created_at: '2025-01-15',
    current_step: 1,
    priority: 'high',
    steps: [
      { id: 's1', type: 'email', subject: 'Introduction - PTS capabilities on DCGS', scheduled_date: '2025-01-15', status: 'completed' },
      { id: 's2', type: 'call', subject: 'Follow-up call re: staffing needs', scheduled_date: '2025-01-22', status: 'pending' },
      { id: 's3', type: 'email', subject: 'Case study: ISR analysts placed at Ft. Liberty', scheduled_date: '2025-01-29', status: 'pending' },
      { id: 's4', type: 'meeting', subject: 'In-person intro at Leidos HQ', scheduled_date: '2025-02-05', status: 'pending' },
    ],
  },
  {
    id: 'seq-002',
    contact_name: 'James Rodriguez',
    company: 'Northrop Grumman',
    program: 'GBSD',
    status: 'active',
    created_at: '2025-01-18',
    current_step: 0,
    priority: 'high',
    steps: [
      { id: 's1', type: 'email', subject: 'PTS intro for GBSD cleared talent', scheduled_date: '2025-01-18', status: 'pending' },
      { id: 's2', type: 'linkedin', subject: 'LinkedIn connection request + message', scheduled_date: '2025-01-20', status: 'pending' },
      { id: 's3', type: 'call', subject: 'Warm call - reference shared connection', scheduled_date: '2025-01-25', status: 'pending' },
    ],
  },
  {
    id: 'seq-003',
    contact_name: 'Maria Chen',
    company: 'GDIT',
    program: 'DCGS-N',
    status: 'paused',
    created_at: '2025-01-10',
    current_step: 2,
    priority: 'medium',
    steps: [
      { id: 's1', type: 'email', subject: 'Intro to PTS Navy ISR capabilities', scheduled_date: '2025-01-10', status: 'completed' },
      { id: 's2', type: 'call', subject: 'Discovery call', scheduled_date: '2025-01-14', status: 'completed' },
      { id: 's3', type: 'email', subject: 'Proposal: 5 SIGINT analysts', scheduled_date: '2025-01-21', status: 'pending' },
    ],
  },
  {
    id: 'seq-004',
    contact_name: 'David Park',
    company: 'Raytheon',
    program: 'JSTARS',
    status: 'completed',
    created_at: '2024-12-20',
    current_step: 3,
    priority: 'low',
    steps: [
      { id: 's1', type: 'email', subject: 'Cold intro - JSTARS staffing', scheduled_date: '2024-12-20', status: 'completed' },
      { id: 's2', type: 'call', subject: 'Follow-up call', scheduled_date: '2024-12-27', status: 'completed' },
      { id: 's3', type: 'meeting', subject: 'Meeting at Robins AFB', scheduled_date: '2025-01-08', status: 'completed' },
    ],
  },
  {
    id: 'seq-005',
    contact_name: 'Karen Williams',
    company: 'BAE Systems',
    program: 'DCGS-AF',
    status: 'draft',
    created_at: '2025-01-20',
    current_step: 0,
    priority: 'medium',
    steps: [
      { id: 's1', type: 'email', subject: 'Introduction email', scheduled_date: '2025-01-25', status: 'pending' },
      { id: 's2', type: 'call', subject: 'Qualification call', scheduled_date: '2025-02-01', status: 'pending' },
    ],
  },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────

const STATUS_STYLES: Record<string, { bg: string; text: string; icon: typeof CheckCircle2 }> = {
  active: { bg: 'bg-green-50 border-green-200', text: 'text-green-700', icon: PlayCircle },
  paused: { bg: 'bg-yellow-50 border-yellow-200', text: 'text-yellow-700', icon: PauseCircle },
  completed: { bg: 'bg-blue-50 border-blue-200', text: 'text-blue-700', icon: CheckCircle2 },
  draft: { bg: 'bg-slate-50 border-slate-200', text: 'text-slate-600', icon: Clock },
};

const PRIORITY_STYLES: Record<string, string> = {
  high: 'bg-red-100 text-red-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-slate-100 text-slate-600',
};

const STEP_TYPE_ICON: Record<string, typeof Mail> = {
  email: Mail,
  call: Phone,
  linkedin: User,
  meeting: Calendar,
};

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// ─── Component ───────────────────────────────────────────────────────────────

export function OutreachManager({ loading = false }: OutreachManagerProps) {
  const [sequences, setSequences] = useState<OutreachSequence[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [serviceOnline, setServiceOnline] = useState(false);
  const [viewMode, setViewMode] = useState<'timeline' | 'portfolio'>('timeline');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedSequence, setSelectedSequence] = useState<OutreachSequence | null>(null);

  // Try to connect to Terminal C (port 8300), fall back to mock data
  useEffect(() => {
    async function loadSequences() {
      try {
        const res = await fetch('/sequences', { signal: AbortSignal.timeout(3000) });
        if (res.ok) {
          const data = await res.json();
          setSequences(data.sequences || data);
          setServiceOnline(true);
        } else {
          throw new Error('Service returned non-OK');
        }
      } catch {
        // Fall back to mock data
        setSequences(MOCK_SEQUENCES);
        setServiceOnline(false);
      } finally {
        setDataLoading(false);
      }
    }
    loadSequences();
  }, []);

  const filteredSequences = useMemo(() => {
    if (statusFilter === 'all') return sequences;
    return sequences.filter(s => s.status === statusFilter);
  }, [sequences, statusFilter]);

  const dueToday = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    const items: { sequence: OutreachSequence; step: OutreachStep }[] = [];
    sequences.forEach(seq => {
      if (seq.status !== 'active') return;
      seq.steps.forEach(step => {
        if (step.status === 'pending' && step.scheduled_date <= today) {
          items.push({ sequence: seq, step });
        }
      });
    });
    return items;
  }, [sequences]);

  const stats = useMemo(() => ({
    active: sequences.filter(s => s.status === 'active').length,
    paused: sequences.filter(s => s.status === 'paused').length,
    completed: sequences.filter(s => s.status === 'completed').length,
    draft: sequences.filter(s => s.status === 'draft').length,
    totalSteps: sequences.reduce((sum, s) => sum + s.steps.length, 0),
    completedSteps: sequences.reduce((sum, s) => sum + s.steps.filter(st => st.status === 'completed').length, 0),
  }), [sequences]);

  const handleCreateSequence = useCallback((newSeq: Partial<OutreachSequence>) => {
    const seq: OutreachSequence = {
      id: `seq-${Date.now()}`,
      contact_name: newSeq.contact_name || '',
      company: newSeq.company || '',
      program: newSeq.program || '',
      status: 'draft',
      created_at: new Date().toISOString().slice(0, 10),
      current_step: 0,
      priority: (newSeq.priority as 'high' | 'medium' | 'low') || 'medium',
      steps: [
        { id: `s-${Date.now()}`, type: 'email', subject: 'Introduction email', scheduled_date: new Date().toISOString().slice(0, 10), status: 'pending' },
      ],
    };
    setSequences(prev => [seq, ...prev]);
    setShowCreateModal(false);
  }, []);

  const handleDeleteSequence = useCallback((id: string) => {
    setSequences(prev => prev.filter(s => s.id !== id));
    if (selectedSequence?.id === id) setSelectedSequence(null);
  }, [selectedSequence]);

  const handleTogglePause = useCallback((id: string) => {
    setSequences(prev => prev.map(s =>
      s.id === id ? { ...s, status: s.status === 'paused' ? 'active' : 'paused' } as OutreachSequence : s
    ));
  }, []);

  if (loading || dataLoading) {
    return (
      <div className="p-6 flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 overflow-auto h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Send className="h-7 w-7 text-blue-500" />
            Outreach Manager
          </h1>
          <p className="text-slate-500 mt-1">
            {sequences.length} sequences &middot; {stats.completedSteps}/{stats.totalSteps} steps completed
            {!serviceOnline && (
              <span className="ml-2 text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded">
                Offline mode (mock data)
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-3">
          {/* View Toggle */}
          <div className="flex gap-1 bg-slate-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('timeline')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'timeline' ? 'bg-white shadow text-slate-800' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <List className="h-4 w-4" /> Timeline
            </button>
            <button
              onClick={() => setViewMode('portfolio')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'portfolio' ? 'bg-white shadow text-slate-800' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <LayoutGrid className="h-4 w-4" /> Portfolio
            </button>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
          >
            <Plus className="h-4 w-4" /> New Sequence
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Active', value: stats.active, color: 'text-green-600', bg: 'bg-green-50' },
          { label: 'Paused', value: stats.paused, color: 'text-yellow-600', bg: 'bg-yellow-50' },
          { label: 'Completed', value: stats.completed, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: 'Draft', value: stats.draft, color: 'text-slate-600', bg: 'bg-slate-50' },
        ].map(s => (
          <div key={s.label} className={`${s.bg} rounded-xl p-4 border border-slate-200`}>
            <p className="text-sm text-slate-500">{s.label}</p>
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Due Today */}
      {dueToday.length > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
          <h3 className="font-semibold text-orange-800 flex items-center gap-2 mb-3">
            <AlertCircle className="h-5 w-5" />
            Due Today ({dueToday.length})
          </h3>
          <div className="space-y-2">
            {dueToday.map(({ sequence, step }) => {
              const StepIcon = STEP_TYPE_ICON[step.type] || Mail;
              return (
                <div
                  key={`${sequence.id}-${step.id}`}
                  className="flex items-center justify-between bg-white rounded-lg p-3 border border-orange-100 cursor-pointer hover:shadow-sm transition-shadow"
                  onClick={() => setSelectedSequence(sequence)}
                >
                  <div className="flex items-center gap-3">
                    <StepIcon className="h-4 w-4 text-orange-600" />
                    <div>
                      <p className="font-medium text-slate-800">{step.subject}</p>
                      <p className="text-sm text-slate-500">{sequence.contact_name} &middot; {sequence.company}</p>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-400" />
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Filter Row */}
      <div className="flex gap-2">
        {['all', 'active', 'paused', 'completed', 'draft'].map(f => (
          <button
            key={f}
            onClick={() => setStatusFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              statusFilter === f
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Main Content */}
      <div className="flex gap-6">
        <div className="flex-1">
          {viewMode === 'timeline' ? (
            <TimelineView
              sequences={filteredSequences}
              selectedId={selectedSequence?.id || null}
              onSelect={setSelectedSequence}
              onTogglePause={handleTogglePause}
              onDelete={handleDeleteSequence}
            />
          ) : (
            <PortfolioView
              sequences={filteredSequences}
              selectedId={selectedSequence?.id || null}
              onSelect={setSelectedSequence}
            />
          )}
        </div>

        {/* Detail Panel */}
        {selectedSequence && (
          <SequenceDetail
            sequence={selectedSequence}
            onClose={() => setSelectedSequence(null)}
            onTogglePause={handleTogglePause}
          />
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <CreateSequenceModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateSequence}
        />
      )}
    </div>
  );
}

// ─── Timeline View ───────────────────────────────────────────────────────────

function TimelineView({
  sequences,
  selectedId,
  onSelect,
  onTogglePause,
  onDelete,
}: {
  sequences: OutreachSequence[];
  selectedId: string | null;
  onSelect: (s: OutreachSequence) => void;
  onTogglePause: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <div className="space-y-3">
      {sequences.length === 0 && (
        <div className="text-center py-12 text-slate-500">
          <Mail className="h-12 w-12 mx-auto mb-3 text-slate-300" />
          <p className="font-medium">No sequences found</p>
          <p className="text-sm">Create a new outreach sequence to get started.</p>
        </div>
      )}
      {sequences.map(seq => {
        const style = STATUS_STYLES[seq.status] || STATUS_STYLES.draft;
        const StatusIcon = style.icon;
        const progress = seq.steps.length > 0
          ? Math.round((seq.steps.filter(s => s.status === 'completed').length / seq.steps.length) * 100)
          : 0;

        return (
          <div
            key={seq.id}
            onClick={() => onSelect(seq)}
            className={`bg-white rounded-xl border p-4 cursor-pointer transition-all hover:shadow-md ${
              selectedId === seq.id ? 'ring-2 ring-blue-500 shadow-md' : 'border-slate-200'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg ${style.bg} border`}>
                  <StatusIcon className={`h-5 w-5 ${style.text}`} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-slate-800">{seq.contact_name}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${PRIORITY_STYLES[seq.priority]}`}>
                      {seq.priority}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-500 mt-0.5">
                    <Building2 className="h-3.5 w-3.5" />
                    <span>{seq.company}</span>
                    <span>&middot;</span>
                    <span>{seq.program}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
                <button
                  onClick={() => onTogglePause(seq.id)}
                  className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
                  title={seq.status === 'paused' ? 'Resume' : 'Pause'}
                >
                  {seq.status === 'paused' ? (
                    <PlayCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <PauseCircle className="h-4 w-4 text-yellow-600" />
                  )}
                </button>
                <button
                  onClick={() => onDelete(seq.id)}
                  className="p-1.5 rounded-lg hover:bg-red-50 transition-colors"
                  title="Delete"
                >
                  <Trash2 className="h-4 w-4 text-red-400 hover:text-red-600" />
                </button>
              </div>
            </div>

            {/* Progress + Steps Timeline */}
            <div className="mt-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-500">
                  Step {seq.steps.filter(s => s.status === 'completed').length} of {seq.steps.length}
                </span>
                <span className="text-xs font-medium text-slate-600">{progress}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-1.5">
                <div
                  className="bg-blue-500 h-1.5 rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="flex gap-1 mt-2">
                {seq.steps.map(step => {
                  const StepIcon = STEP_TYPE_ICON[step.type] || Mail;
                  return (
                    <div
                      key={step.id}
                      className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${
                        step.status === 'completed'
                          ? 'bg-green-50 text-green-700'
                          : step.status === 'pending'
                          ? 'bg-slate-50 text-slate-600'
                          : 'bg-slate-50 text-slate-400'
                      }`}
                      title={`${step.type}: ${step.subject}`}
                    >
                      <StepIcon className="h-3 w-3" />
                      <span>{formatDate(step.scheduled_date)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Portfolio View ──────────────────────────────────────────────────────────

function PortfolioView({
  sequences,
  selectedId,
  onSelect,
}: {
  sequences: OutreachSequence[];
  selectedId: string | null;
  onSelect: (s: OutreachSequence) => void;
}) {
  const columns: { status: string; label: string }[] = [
    { status: 'draft', label: 'Draft' },
    { status: 'active', label: 'Active' },
    { status: 'paused', label: 'Paused' },
    { status: 'completed', label: 'Completed' },
  ];

  return (
    <div className="grid grid-cols-4 gap-4">
      {columns.map(col => {
        const colSeqs = sequences.filter(s => s.status === col.status);
        const style = STATUS_STYLES[col.status] || STATUS_STYLES.draft;

        return (
          <div key={col.status} className="space-y-3">
            <div className={`rounded-lg px-3 py-2 border ${style.bg} flex items-center justify-between`}>
              <span className={`font-semibold text-sm ${style.text}`}>{col.label}</span>
              <span className={`text-xs font-bold ${style.text}`}>{colSeqs.length}</span>
            </div>
            {colSeqs.map(seq => (
              <div
                key={seq.id}
                onClick={() => onSelect(seq)}
                className={`bg-white rounded-lg border p-3 cursor-pointer transition-all hover:shadow-md ${
                  selectedId === seq.id ? 'ring-2 ring-blue-500' : 'border-slate-200'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium text-sm text-slate-800 truncate">{seq.contact_name}</h4>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${PRIORITY_STYLES[seq.priority]}`}>
                    {seq.priority}
                  </span>
                </div>
                <p className="text-xs text-slate-500 truncate">{seq.company} &middot; {seq.program}</p>
                <div className="mt-2 flex gap-0.5">
                  {seq.steps.map(step => (
                    <div
                      key={step.id}
                      className={`flex-1 h-1.5 rounded-full ${
                        step.status === 'completed' ? 'bg-green-400' : 'bg-slate-200'
                      }`}
                    />
                  ))}
                </div>
              </div>
            ))}
            {colSeqs.length === 0 && (
              <div className="text-center py-8 text-xs text-slate-400">No sequences</div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Sequence Detail Panel ───────────────────────────────────────────────────

function SequenceDetail({
  sequence,
  onClose,
  onTogglePause,
}: {
  sequence: OutreachSequence;
  onClose: () => void;
  onTogglePause: (id: string) => void;
}) {
  const style = STATUS_STYLES[sequence.status] || STATUS_STYLES.draft;

  return (
    <div className="w-96 bg-white rounded-xl shadow-sm border border-slate-200 p-6 h-fit sticky top-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-slate-800">{sequence.contact_name}</h3>
          <div className="flex items-center gap-2 mt-1 text-sm text-slate-500">
            <Building2 className="h-4 w-4" />
            <span>{sequence.company}</span>
          </div>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded-lg transition-colors">
          <X className="h-5 w-5 text-slate-400" />
        </button>
      </div>

      <div className="flex gap-2 mb-4">
        <span className={`px-2 py-1 rounded text-xs font-medium border ${style.bg} ${style.text}`}>
          {sequence.status}
        </span>
        <span className={`px-2 py-1 rounded text-xs font-medium ${PRIORITY_STYLES[sequence.priority]}`}>
          {sequence.priority} priority
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-slate-50 rounded-lg p-3">
          <p className="text-xs text-slate-500">Program</p>
          <p className="font-semibold text-slate-800 text-sm">{sequence.program}</p>
        </div>
        <div className="bg-slate-50 rounded-lg p-3">
          <p className="text-xs text-slate-500">Created</p>
          <p className="font-semibold text-slate-800 text-sm">{formatDate(sequence.created_at)}</p>
        </div>
      </div>

      {/* Steps */}
      <h4 className="font-semibold text-slate-700 text-sm mb-3">Sequence Steps</h4>
      <div className="space-y-2">
        {sequence.steps.map((step, idx) => {
          const StepIcon = STEP_TYPE_ICON[step.type] || Mail;
          const isCurrent = idx === sequence.current_step && sequence.status === 'active';

          return (
            <div
              key={step.id}
              className={`flex items-start gap-3 p-3 rounded-lg border transition-colors ${
                isCurrent
                  ? 'bg-blue-50 border-blue-200'
                  : step.status === 'completed'
                  ? 'bg-green-50 border-green-100'
                  : 'bg-slate-50 border-slate-100'
              }`}
            >
              <div className={`mt-0.5 p-1.5 rounded ${
                step.status === 'completed' ? 'bg-green-100' : isCurrent ? 'bg-blue-100' : 'bg-slate-100'
              }`}>
                {step.status === 'completed' ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <StepIcon className={`h-4 w-4 ${isCurrent ? 'text-blue-600' : 'text-slate-400'}`} />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${step.status === 'completed' ? 'text-green-800' : 'text-slate-800'}`}>
                  {step.subject}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-slate-500">{step.type}</span>
                  <span className="text-xs text-slate-400">&middot;</span>
                  <span className="text-xs text-slate-500">{formatDate(step.scheduled_date)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Actions */}
      <div className="mt-4 flex gap-2">
        <button
          onClick={() => onTogglePause(sequence.id)}
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
            sequence.status === 'paused'
              ? 'bg-green-50 text-green-700 hover:bg-green-100'
              : 'bg-yellow-50 text-yellow-700 hover:bg-yellow-100'
          }`}
        >
          {sequence.status === 'paused' ? 'Resume' : 'Pause'}
        </button>
        <button
          onClick={onClose}
          className="flex-1 py-2 text-sm text-slate-500 hover:text-slate-700 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  );
}

// ─── Create Sequence Modal ───────────────────────────────────────────────────

function CreateSequenceModal({
  onClose,
  onCreate,
}: {
  onClose: () => void;
  onCreate: (seq: Partial<OutreachSequence>) => void;
}) {
  const [formData, setFormData] = useState({
    contact_name: '',
    company: '',
    program: '',
    priority: 'medium',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.contact_name || !formData.company) return;
    setSubmitting(true);

    // Try posting to Terminal C, fall back to local creation
    try {
      const res = await fetch('/sequences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
        signal: AbortSignal.timeout(3000),
      });
      if (res.ok) {
        const data = await res.json();
        onCreate(data);
        return;
      }
    } catch {
      // Fall through to local creation
    }

    onCreate(formData);
    setSubmitting(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-800">Create New Sequence</h2>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded-lg transition-colors">
            <X className="h-5 w-5 text-slate-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Contact Name *</label>
            <input
              type="text"
              required
              value={formData.contact_name}
              onChange={e => setFormData(prev => ({ ...prev, contact_name: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Sarah Mitchell"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Company *</label>
            <input
              type="text"
              required
              value={formData.company}
              onChange={e => setFormData(prev => ({ ...prev, company: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Leidos"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Program</label>
            <input
              type="text"
              value={formData.program}
              onChange={e => setFormData(prev => ({ ...prev, program: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., DCGS-A"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Priority</label>
            <select
              value={formData.priority}
              onChange={e => setFormData(prev => ({ ...prev, priority: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={submitting || !formData.contact_name || !formData.company}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              Create Sequence
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 text-slate-600 hover:text-slate-800 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default OutreachManager;
