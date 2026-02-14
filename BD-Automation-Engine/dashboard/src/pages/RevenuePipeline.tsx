/**
 * Revenue Pipeline — BD Funnel Kanban Board
 *
 * 6-stage funnel: Identified → Outreach Active → Meeting Set → Engaged
 *                 → Placement Made → Revenue Realized
 *
 * Drag-drop via @dnd-kit, localStorage persistence for deal stages.
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  DollarSign, Plus, X, Clock,
  GripVertical, Search, Target, Handshake, CheckCircle2, Banknote,
  Mail, TrendingUp, ArrowRight,
} from 'lucide-react';
import { hubApiClient } from '../services/hubApi';
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

// ─── Types ───────────────────────────────────────────────────────────────────

type RevenueStage =
  | 'identified'
  | 'outreach_active'
  | 'meeting_set'
  | 'engaged'
  | 'placement_made'
  | 'revenue_realized';

interface RevenueDeal {
  id: string;
  contact_name: string;
  program: string;
  company: string;
  stage: RevenueStage;
  estimated_value: number;
  created_at: string;
  last_moved: string;
  notes?: string;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const REVENUE_STAGES = [
  { id: 'identified' as const, label: 'Identified', icon: Search, color: 'bg-slate-100 border-slate-300 text-slate-700', dot: 'bg-slate-400' },
  { id: 'outreach_active' as const, label: 'Outreach Active', icon: Mail, color: 'bg-blue-50 border-blue-300 text-blue-700', dot: 'bg-blue-500' },
  { id: 'meeting_set' as const, label: 'Meeting Set', icon: Target, color: 'bg-purple-50 border-purple-300 text-purple-700', dot: 'bg-purple-500' },
  { id: 'engaged' as const, label: 'Engaged', icon: Handshake, color: 'bg-orange-50 border-orange-300 text-orange-700', dot: 'bg-orange-500' },
  { id: 'placement_made' as const, label: 'Placement Made', icon: CheckCircle2, color: 'bg-emerald-50 border-emerald-300 text-emerald-700', dot: 'bg-emerald-500' },
  { id: 'revenue_realized' as const, label: 'Revenue Realized', icon: Banknote, color: 'bg-green-50 border-green-300 text-green-700', dot: 'bg-green-600' },
] as const;

const STORAGE_KEY = 'revenue_pipeline_deals';

// ─── Mock Data ───────────────────────────────────────────────────────────────

function generateMockDeals(): RevenueDeal[] {
  const now = Date.now();
  return [
    { id: 'deal-1', contact_name: 'J. Miller', program: 'AF DCGS Block 5', company: 'GDIT', stage: 'engaged', estimated_value: 450_000, created_at: new Date(now - 45 * 86400000).toISOString(), last_moved: new Date(now - 3 * 86400000).toISOString() },
    { id: 'deal-2', contact_name: 'R. Chen', program: 'Army DCGS-A', company: 'Leidos', stage: 'meeting_set', estimated_value: 380_000, created_at: new Date(now - 30 * 86400000).toISOString(), last_moved: new Date(now - 5 * 86400000).toISOString() },
    { id: 'deal-3', contact_name: 'M. Torres', program: 'SOCOM DCGS-SOF', company: 'CACI', stage: 'outreach_active', estimated_value: 320_000, created_at: new Date(now - 20 * 86400000).toISOString(), last_moved: new Date(now - 2 * 86400000).toISOString() },
    { id: 'deal-4', contact_name: 'K. Ero', program: 'Navy DCGS-N', company: 'BAE Systems', stage: 'identified', estimated_value: 275_000, created_at: new Date(now - 10 * 86400000).toISOString(), last_moved: new Date(now - 10 * 86400000).toISOString() },
    { id: 'deal-5', contact_name: 'S. Yamamoto', program: 'GBSD', company: 'Peraton', stage: 'outreach_active', estimated_value: 250_000, created_at: new Date(now - 25 * 86400000).toISOString(), last_moved: new Date(now - 7 * 86400000).toISOString() },
    { id: 'deal-6', contact_name: 'A. Patel', program: 'JSTARS Recap', company: 'SAIC', stage: 'placement_made', estimated_value: 520_000, created_at: new Date(now - 60 * 86400000).toISOString(), last_moved: new Date(now - 8 * 86400000).toISOString() },
    { id: 'deal-7', contact_name: 'D. Washington', program: 'PACAF ISR', company: 'GDIT', stage: 'revenue_realized', estimated_value: 340_000, created_at: new Date(now - 90 * 86400000).toISOString(), last_moved: new Date(now - 15 * 86400000).toISOString() },
    { id: 'deal-8', contact_name: 'L. Kim', program: 'AF DCGS Block 5', company: 'Leidos', stage: 'identified', estimated_value: 290_000, created_at: new Date(now - 5 * 86400000).toISOString(), last_moved: new Date(now - 5 * 86400000).toISOString() },
    { id: 'deal-9', contact_name: 'T. Jackson', program: 'Army DCGS-A', company: 'CACI', stage: 'engaged', estimated_value: 410_000, created_at: new Date(now - 35 * 86400000).toISOString(), last_moved: new Date(now - 4 * 86400000).toISOString() },
    { id: 'deal-10', contact_name: 'B. Martinez', program: 'SOCOM DCGS-SOF', company: 'Peraton', stage: 'meeting_set', estimated_value: 360_000, created_at: new Date(now - 18 * 86400000).toISOString(), last_moved: new Date(now - 6 * 86400000).toISOString() },
    { id: 'deal-11', contact_name: 'C. Hughes', program: 'Enterprise Security', company: 'BAE Systems', stage: 'identified', estimated_value: 195_000, created_at: new Date(now - 3 * 86400000).toISOString(), last_moved: new Date(now - 3 * 86400000).toISOString() },
    { id: 'deal-12', contact_name: 'N. Robinson', program: 'Navy DCGS-N', company: 'SAIC', stage: 'outreach_active', estimated_value: 310_000, created_at: new Date(now - 12 * 86400000).toISOString(), last_moved: new Date(now - 1 * 86400000).toISOString() },
  ];
}

// ─── Persistence ─────────────────────────────────────────────────────────────

function loadDeals(): RevenueDeal[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  const deals = generateMockDeals();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(deals));
  return deals;
}

function persistDeals(deals: RevenueDeal[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(deals));
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatUSD(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value}`;
}

function daysInStage(deal: RevenueDeal): number {
  return Math.max(0, Math.floor((Date.now() - new Date(deal.last_moved).getTime()) / 86400000));
}

const COMPANY_COLORS: Record<string, string> = {
  'GDIT': '#3b82f6',
  'Leidos': '#8b5cf6',
  'SAIC': '#06b6d4',
  'CACI': '#f59e0b',
  'Peraton': '#ef4444',
  'BAE Systems': '#22c55e',
};

// ─── Deal Card ───────────────────────────────────────────────────────────────

function DealCard({ deal }: { deal: RevenueDeal }) {
  const color = COMPANY_COLORS[deal.company] || '#6b7280';
  const days = daysInStage(deal);

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-3 hover:shadow-md transition-shadow cursor-grab active:cursor-grabbing">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-bold truncate" style={{ color }}>{deal.company}</span>
        <span className="text-sm font-bold text-slate-900 dark:text-slate-100">{formatUSD(deal.estimated_value)}</span>
      </div>
      <p className="text-sm font-medium text-slate-800 dark:text-slate-100 truncate mb-0.5">
        {deal.contact_name}
      </p>
      <p className="text-xs text-slate-500 dark:text-slate-400 truncate mb-2">
        {deal.program}
      </p>
      <div className="flex items-center justify-between pt-1.5 border-t border-slate-100 dark:border-slate-700">
        <span className="text-[10px] text-slate-400 flex items-center gap-1">
          <Clock className="h-3 w-3" /> {days}d in stage
        </span>
        {days > 14 && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 font-medium">
            Stale
          </span>
        )}
      </div>
    </div>
  );
}

// ─── Kanban Column ───────────────────────────────────────────────────────────

function RevenueColumn({
  stage,
  deals,
  stageValue,
}: {
  stage: (typeof REVENUE_STAGES)[number];
  deals: RevenueDeal[];
  stageValue: number;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: stage.id });
  const Icon = stage.icon;

  return (
    <div ref={setNodeRef}
      className={`flex flex-col min-w-[240px] w-[240px] transition-colors rounded-xl ${isOver ? 'ring-2 ring-blue-400 bg-blue-50/50 dark:bg-blue-900/20' : ''}`}>
      <div className={`rounded-t-xl px-3 py-2.5 border ${stage.color} flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <Icon className="h-3.5 w-3.5" />
          <span className="text-xs font-semibold">{stage.label}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-medium opacity-70">{formatUSD(stageValue)}</span>
          <span className="text-xs font-bold bg-white/60 dark:bg-slate-900/40 px-1.5 py-0.5 rounded">{deals.length}</span>
        </div>
      </div>
      <div className="flex-1 space-y-2 p-2 overflow-y-auto max-h-[calc(100vh-320px)] bg-slate-50/50 dark:bg-slate-900/30 rounded-b-xl border border-t-0 border-slate-200 dark:border-slate-700">
        {deals.map(deal => (
          <div key={deal.id} data-deal-id={deal.id}>
            <DealCard deal={deal} />
          </div>
        ))}
        {deals.length === 0 && (
          <div className="text-center py-8 text-xs text-slate-400 dark:text-slate-500">
            <GripVertical className="h-5 w-5 mx-auto mb-1 opacity-40" />
            Drop here
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Add Deal Form ───────────────────────────────────────────────────────────

function AddDealForm({ onAdd, onCancel }: { onAdd: (deal: RevenueDeal) => void; onCancel: () => void }) {
  const [name, setName] = useState('');
  const [program, setProgram] = useState('');
  const [company, setCompany] = useState('GDIT');
  const [value, setValue] = useState('100000');

  const handleSubmit = () => {
    if (!name.trim() || !program.trim()) return;
    const now = new Date().toISOString();
    onAdd({
      id: `deal-${Date.now()}`,
      contact_name: name.trim(),
      program: program.trim(),
      company,
      stage: 'identified',
      estimated_value: parseInt(value) || 100_000,
      created_at: now,
      last_moved: now,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">Add Deal</h3>
          <button onClick={onCancel} className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Contact Name</label>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="J. Smith"
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm text-slate-900 dark:text-slate-100" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Program</label>
            <input value={program} onChange={e => setProgram(e.target.value)} placeholder="AF DCGS Block 5"
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm text-slate-900 dark:text-slate-100" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Company</label>
            <select value={company} onChange={e => setCompany(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm text-slate-900 dark:text-slate-100">
              {Object.keys(COMPANY_COLORS).map(c => <option key={c} value={c}>{c}</option>)}
              <option value="Other">Other</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Estimated Value ($)</label>
            <input type="number" value={value} onChange={e => setValue(e.target.value)} min="0" step="10000"
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm text-slate-900 dark:text-slate-100" />
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onCancel}
            className="px-4 py-2 text-sm rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600">
            Cancel
          </button>
          <button onClick={handleSubmit} disabled={!name.trim() || !program.trim()}
            className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
            Add to Pipeline
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

interface FunnelStage {
  stage: string;
  count: number;
  value: number;
}

export function RevenuePipeline() {
  const [deals, setDeals] = useState<RevenueDeal[]>(loadDeals);
  const [activeDealId, setActiveDealId] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [funnelData, setFunnelData] = useState<FunnelStage[]>([]);
  const [funnelRates, setFunnelRates] = useState<Record<string, number>>({});

  // Fetch real funnel data from backend
  useEffect(() => {
    hubApiClient.getAnalyticsFunnel()
      .then(data => {
        setFunnelData(data.funnel || []);
        setFunnelRates(data.conversion_rates || {});
      })
      .catch(() => {/* funnel endpoint not available yet */});
  }, []);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
  );

  // Persist on change
  useEffect(() => { persistDeals(deals); }, [deals]);

  // Filter by search
  const filteredDeals = useMemo(() => {
    if (!searchQuery) return deals;
    const q = searchQuery.toLowerCase();
    return deals.filter(d =>
      d.contact_name.toLowerCase().includes(q) ||
      d.program.toLowerCase().includes(q) ||
      d.company.toLowerCase().includes(q)
    );
  }, [deals, searchQuery]);

  // Group by stage
  const dealsByStage = useMemo(() => {
    const groups: Record<RevenueStage, RevenueDeal[]> = {
      identified: [], outreach_active: [], meeting_set: [],
      engaged: [], placement_made: [], revenue_realized: [],
    };
    filteredDeals.forEach(d => {
      if (groups[d.stage]) groups[d.stage].push(d);
      else groups.identified.push(d);
    });
    return groups;
  }, [filteredDeals]);

  // Totals
  const totalPipelineValue = useMemo(() => deals.reduce((sum, d) => sum + d.estimated_value, 0), [deals]);
  const stageValues = useMemo(() => {
    const vals: Record<RevenueStage, number> = {
      identified: 0, outreach_active: 0, meeting_set: 0,
      engaged: 0, placement_made: 0, revenue_realized: 0,
    };
    filteredDeals.forEach(d => { vals[d.stage] += d.estimated_value; });
    return vals;
  }, [filteredDeals]);

  const activeDeal = useMemo(
    () => activeDealId ? filteredDeals.find(d => d.id === activeDealId) || null : null,
    [activeDealId, filteredDeals]
  );

  const handleDragStart = useCallback((e: DragStartEvent) => setActiveDealId(String(e.active.id)), []);

  const handleDragEnd = useCallback((e: DragEndEvent) => {
    setActiveDealId(null);
    const { active, over } = e;
    if (!over) return;
    const dealId = String(active.id);
    const targetStage = String(over.id) as RevenueStage;
    if (REVENUE_STAGES.some(s => s.id === targetStage)) {
      setDeals(prev => prev.map(d =>
        d.id === dealId ? { ...d, stage: targetStage, last_moved: new Date().toISOString() } : d
      ));
    }
  }, []);

  const handleAddDeal = useCallback((deal: RevenueDeal) => {
    setDeals(prev => [...prev, deal]);
    setShowAddForm(false);
  }, []);

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <DollarSign className="h-7 w-7 text-green-600" /> Revenue Pipeline
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {deals.length} deals &bull; Pipeline Value: <span className="font-bold text-green-600">{formatUSD(totalPipelineValue)}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="h-4 w-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search deals..."
              className="pl-8 pr-3 py-2 w-52 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm text-slate-900 dark:text-slate-100"
            />
          </div>
          <button onClick={() => setShowAddForm(true)}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
            <Plus className="h-4 w-4" /> Add Deal
          </button>
        </div>
      </div>

      {/* Backend Funnel (real data) */}
      {funnelData.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="h-4 w-4 text-indigo-500" />
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">Intelligence Funnel</span>
          </div>
          <div className="flex items-center justify-between">
            {funnelData.map((stage, i) => {
              const maxCount = Math.max(...funnelData.map(s => s.count), 1);
              const widthPct = Math.max(20, (stage.count / maxCount) * 100);
              return (
                <div key={stage.stage} className="flex items-center flex-1">
                  <div className="flex-1 text-center">
                    <div
                      className="mx-auto rounded-lg bg-gradient-to-b from-indigo-500 to-indigo-600 text-white py-2 px-3 transition-all"
                      style={{ width: `${widthPct}%`, minWidth: '80px' }}
                    >
                      <p className="text-lg font-bold">{stage.count}</p>
                      <p className="text-[10px] opacity-80 capitalize">{stage.stage.replace(/_/g, ' ')}</p>
                    </div>
                    {stage.value > 0 && (
                      <p className="text-[10px] text-slate-400 mt-1">{formatUSD(stage.value)}</p>
                    )}
                  </div>
                  {i < funnelData.length - 1 && (
                    <div className="flex flex-col items-center px-1">
                      <ArrowRight className="h-4 w-4 text-slate-300" />
                      {Object.keys(funnelRates).length > 0 && (
                        <span className="text-[9px] text-slate-400">
                          {Math.round((funnelRates[`${funnelData[i].stage}_to_${funnelData[i + 1].stage}`] || 0) * 100)}%
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Stage Summary Bar */}
      <div className="grid grid-cols-6 gap-2 mb-4">
        {REVENUE_STAGES.map(stage => {
          const Icon = stage.icon;
          const count = dealsByStage[stage.id].length;
          const val = stageValues[stage.id];
          return (
            <div key={stage.id} className={`rounded-lg border px-3 py-2 ${stage.color}`}>
              <div className="flex items-center gap-1.5 mb-0.5">
                <Icon className="h-3.5 w-3.5" />
                <span className="text-[10px] font-semibold">{stage.label}</span>
              </div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-lg font-bold">{count}</span>
                <span className="text-[10px] opacity-70">{formatUSD(val)}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Kanban Board */}
      <div className="flex-1 overflow-hidden">
        <DndContext sensors={sensors} collisionDetection={closestCorners}
          onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
          <div className="flex gap-3 overflow-x-auto pb-4 h-full">
            {REVENUE_STAGES.map(stage => (
              <RevenueColumn key={stage.id} stage={stage}
                deals={dealsByStage[stage.id]}
                stageValue={stageValues[stage.id]} />
            ))}
          </div>
          <DragOverlay>
            {activeDeal && (
              <div className="opacity-90 rotate-1 scale-105 shadow-xl">
                <DealCard deal={activeDeal} />
              </div>
            )}
          </DragOverlay>
        </DndContext>
      </div>

      {/* Add Deal Modal */}
      {showAddForm && (
        <AddDealForm onAdd={handleAddDeal} onCancel={() => setShowAddForm(false)} />
      )}
    </div>
  );
}
