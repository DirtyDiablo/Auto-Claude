import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Network, Search, RotateCcw, Loader2,
  User, Building2, Briefcase, Mail, Phone, Linkedin,
  ExternalLink, Send, Filter, X, Swords, MapPin,
} from 'lucide-react';

// ─── Types (V6 — 4 node types, enriched fields) ────────────────────────────

type NodeType = 'contact' | 'program' | 'contractor' | 'job';

interface GraphNode {
  id: string;
  type: NodeType;
  name: string;
  // Contact fields
  title?: string;
  tier?: string;
  priority?: string;
  program?: string;
  company?: string;
  location?: string;
  email?: string;
  phone?: string;
  linkedin?: string;
  // Program fields
  prime?: string;
  value?: string;
  agency?: string;
  acronym?: string;
  // Contractor fields
  headquarters?: string;
  company_type?: string;
  program_count?: number;
  // Job fields
  bd_score?: number;
  clearance?: string;
  // Intelligent DB fields
  data_quality_score?: number;
  domain_tags?: string[];
}

interface GraphEdge {
  source: string;
  target: string;
  type?: string;
  shared_programs?: number;
  programs?: string[];
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
}

type LayoutType = 'force' | 'radial' | 'concentric';
type ColorBy = 'type' | 'priority' | 'tier' | 'program' | 'domain' | 'quality';
type ViewMode = 'explore' | 'competition';

interface GraphExplorerProps {
  onNavigateToContact?: (name: string) => void;
  onNavigateToProgram?: (name: string) => void;
  onNavigateToOutreach?: () => void;
}

// ─── Color Maps ──────────────────────────────────────────────────────────────

const PRIORITY_COLORS: Record<string, string> = {
  Critical: '#ef4444', critical: '#ef4444',
  High: '#f97316', high: '#f97316',
  Medium: '#eab308', medium: '#eab308',
  Standard: '#94a3b8', standard: '#94a3b8',
  Low: '#22c55e', low: '#22c55e',
  '': '#94a3b8',
};

const TIER_COLORS: Record<string, string> = {
  '1': '#7c3aed', '2': '#2563eb', '3': '#0891b2',
  '4': '#059669', '5': '#d97706', '6': '#6b7280',
  '': '#94a3b8',
};

const PROGRAM_PALETTE = [
  '#ef4444', '#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16',
];

const TYPE_COLORS: Record<string, string> = {
  contact: '#3b82f6',
  program: '#8b5cf6',
  contractor: '#22c55e',
  job: '#ef4444',
};

const DOMAIN_COLORS: Record<string, string> = {
  ISR: '#06b6d4', C4ISR: '#3b82f6', Cyber: '#ef4444', Space: '#8b5cf6',
  Logistics: '#f59e0b', EW: '#f97316', Training: '#22c55e', Aviation: '#64748b',
  Navy: '#0ea5e9', Army: '#84cc16', Air_Force: '#6366f1', Intel: '#a855f7',
  Missile_Defense: '#ec4899',
};

function getQualityColor(score: number | undefined): string {
  if (score === undefined) return '#94a3b8';
  if (score >= 80) return '#22c55e';
  if (score >= 60) return '#84cc16';
  if (score >= 40) return '#f59e0b';
  if (score >= 20) return '#f97316';
  return '#ef4444';
}

// ─── G6 Graph Hook ──────────────────────────────────────────────────────────

function useG6Graph(
  containerRef: React.RefObject<HTMLDivElement | null>,
  graphData: GraphData | null,
  layout: LayoutType,
  colorBy: ColorBy,
  onNodeClick: (node: GraphNode) => void,
  onNodeDblClick: (node: GraphNode) => void,
  searchTerm: string,
  filters: { programs: string[]; tiers: string[]; companies: string[] },
) {
  const graphRef = useRef<unknown>(null);
  const programColorMap = useRef<Map<string, string>>(new Map());

  useEffect(() => {
    if (!graphData) return;
    const programs = new Set<string>();
    graphData.nodes.forEach(n => {
      if (n.type === 'contact' && n.program) programs.add(n.program.split(',')[0].trim());
      if (n.type === 'program' && n.name) programs.add(n.name);
    });
    let idx = 0;
    programs.forEach(p => {
      if (!programColorMap.current.has(p)) {
        programColorMap.current.set(p, PROGRAM_PALETTE[idx % PROGRAM_PALETTE.length]);
        idx++;
      }
    });
  }, [graphData]);

  const filteredData = useMemo(() => {
    if (!graphData) return null;

    let nodes = graphData.nodes;
    const activeFilters = filters.programs.length > 0 || filters.tiers.length > 0 || filters.companies.length > 0;

    if (activeFilters) {
      nodes = nodes.filter(n => {
        if (n.type === 'program') {
          return filters.programs.length === 0 || filters.programs.includes(n.name);
        }
        if (n.type === 'contractor' || n.type === 'job') {
          return filters.companies.length === 0 || filters.companies.includes(n.company || n.name);
        }
        const matchProg = filters.programs.length === 0 || filters.programs.some(p => (n.program || '').includes(p));
        const matchTier = filters.tiers.length === 0 || filters.tiers.includes(String(n.tier));
        const matchComp = filters.companies.length === 0 || filters.companies.includes(n.company || '');
        return matchProg && matchTier && matchComp;
      });
    }

    if (searchTerm) {
      const lower = searchTerm.toLowerCase();
      nodes = nodes.filter(n =>
        n.name.toLowerCase().includes(lower) ||
        (n.program || '').toLowerCase().includes(lower) ||
        (n.company || '').toLowerCase().includes(lower)
      );
    }

    const nodeIds = new Set(nodes.map(n => n.id));
    const edges = graphData.edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target));

    return { nodes, edges };
  }, [graphData, filters, searchTerm]);

  const getNodeColor = useCallback((node: GraphNode): string => {
    switch (colorBy) {
      case 'priority': return PRIORITY_COLORS[node.priority || ''] || '#94a3b8';
      case 'tier': return TIER_COLORS[String(node.tier) || ''] || '#94a3b8';
      case 'program': {
        const prog = (node.program || '').split(',')[0].trim();
        return programColorMap.current.get(prog) || '#94a3b8';
      }
      case 'domain': {
        const firstTag = (node.domain_tags || [])[0] || '';
        return DOMAIN_COLORS[firstTag] || '#94a3b8';
      }
      case 'quality':
        return getQualityColor(node.data_quality_score);
      default:
        return TYPE_COLORS[node.type] || '#94a3b8';
    }
  }, [colorBy]);

  const getNodeSize = useCallback((node: GraphNode): number => {
    if (node.type === 'program') return 32;
    if (node.type === 'contractor') return 28;
    if (node.type === 'job') return 14;
    const tier = parseInt(String(node.tier)) || 6;
    return Math.max(16, 44 - tier * 5);
  }, []);

  const getNodeShape = useCallback((node: GraphNode): string => {
    if (node.type === 'program') return 'diamond';
    if (node.type === 'contractor') return 'rect';
    return 'circle';
  }, []);

  useEffect(() => {
    if (!containerRef.current || !filteredData || filteredData.nodes.length === 0) return;

    const loadG6 = async () => {
      const G6 = await import('@antv/g6');

      if (graphRef.current) {
        try { (graphRef.current as { destroy: () => void }).destroy(); } catch { /* ok */ }
        graphRef.current = null;
      }

      const container = containerRef.current;
      if (!container) return;
      const width = container.clientWidth;
      const height = container.clientHeight;

      const layoutConfigs: Record<LayoutType, unknown> = {
        force: {
          type: 'd3-force',
          preventOverlap: true,
          nodeStrength: -120,
          edgeStrength: 0.3,
          collideStrength: 0.8,
          alphaDecay: 0.02,
        },
        radial: { type: 'radial', unitRadius: 100, preventOverlap: true, nodeSpacing: 20 },
        concentric: { type: 'concentric', preventOverlap: true, nodeSpacing: 15, sortBy: 'degree' },
      };

      const g6Nodes = filteredData.nodes.map(n => ({
        id: n.id,
        data: { ...n },
        style: {
          size: getNodeSize(n),
          fill: getNodeColor(n),
          stroke: '#fff',
          lineWidth: 2,
          type: getNodeShape(n),
          labelText: n.name.length > 18 ? n.name.slice(0, 16) + '...' : n.name,
          labelFontSize: 9,
          labelFill: '#64748b',
          labelOffsetY: getNodeSize(n) / 2 + 10,
        },
      }));

      const g6Edges = filteredData.edges.map((e, i) => {
        const isCompete = e.type === 'COMPETES_WITH';
        return {
          id: `edge-${i}`,
          source: e.source,
          target: e.target,
          style: {
            stroke: isCompete ? '#f97316' : '#cbd5e1',
            lineWidth: isCompete ? Math.max(1, (e.shared_programs || 1) * 0.8) : 0.8,
            opacity: isCompete ? 0.8 : 0.5,
          },
        };
      });

      const graph = new G6.Graph({
        container,
        width,
        height,
        data: { nodes: g6Nodes, edges: g6Edges },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        layout: layoutConfigs[layout] as any,
        behaviors: ['drag-canvas', 'zoom-canvas', 'drag-element'],
        animation: true,
        autoFit: 'view',
        padding: 40,
      });

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      graph.on('node:click', (evt: any) => {
        const nodeId = evt?.target?.id;
        if (!nodeId) return;
        const original = filteredData.nodes.find(n => n.id === nodeId);
        if (original) onNodeClick(original);
      });

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      graph.on('node:dblclick', (evt: any) => {
        const nodeId = evt?.target?.id;
        if (!nodeId) return;
        const original = filteredData.nodes.find(n => n.id === nodeId);
        if (original) onNodeDblClick(original);
      });

      await graph.render();
      graphRef.current = graph;
    };

    loadG6();

    return () => {
      if (graphRef.current) {
        try { (graphRef.current as { destroy: () => void }).destroy(); } catch { /* ok */ }
        graphRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filteredData, layout, colorBy]);

  return { filteredData };
}

// ─── Quality Badge ──────────────────────────────────────────────────────────

function QualityBadge({ score }: { score: number }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-slate-400">Quality:</span>
      <div className="flex-1 bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
        <div className="h-1.5 rounded-full transition-all"
          style={{ width: `${score}%`, backgroundColor: getQualityColor(score) }} />
      </div>
      <span className="font-mono text-slate-600 dark:text-slate-400">{Math.round(score)}</span>
    </div>
  );
}

// ─── Domain Tags ────────────────────────────────────────────────────────────

function DomainTagChips({ tags }: { tags: string[] }) {
  return (
    <div className="flex flex-wrap gap-1">
      {tags.map(tag => (
        <span key={tag} className="px-1.5 py-0.5 rounded text-[10px] font-medium"
          style={{ backgroundColor: `${DOMAIN_COLORS[tag] || '#94a3b8'}20`, color: DOMAIN_COLORS[tag] || '#94a3b8' }}>
          {tag}
        </span>
      ))}
    </div>
  );
}

// ─── Node Detail Panel (V6) ─────────────────────────────────────────────────

function NodeDetailPanel({
  node, onClose, onNavigateToContact, onNavigateToProgram, onNavigateToOutreach,
}: {
  node: GraphNode;
  onClose: () => void;
  onNavigateToContact?: (name: string) => void;
  onNavigateToProgram?: (name: string) => void;
  onNavigateToOutreach?: () => void;
}) {
  const iconBg = {
    contact: 'bg-blue-100 dark:bg-blue-900/40',
    program: 'bg-purple-100 dark:bg-purple-900/40',
    contractor: 'bg-green-100 dark:bg-green-900/40',
    job: 'bg-red-100 dark:bg-red-900/40',
  }[node.type];

  const iconColor = {
    contact: 'text-blue-600 dark:text-blue-400',
    program: 'text-purple-600 dark:text-purple-400',
    contractor: 'text-green-600 dark:text-green-400',
    job: 'text-red-600 dark:text-red-400',
  }[node.type];

  const Icon = {
    contact: User, program: Building2, contractor: Briefcase, job: MapPin,
  }[node.type];

  return (
    <div className="w-80 border-l border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 overflow-y-auto p-4 space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-10 h-10 rounded-full ${iconBg} flex items-center justify-center`}>
            <Icon className={`h-5 w-5 ${iconColor}`} />
          </div>
          <div>
            <h3 className="font-semibold text-slate-800 dark:text-slate-100 text-sm">{node.name}</h3>
            {node.title && <p className="text-xs text-slate-500">{node.title}</p>}
            {node.acronym && <p className="text-xs text-slate-500">{node.acronym}</p>}
            <span className="text-[10px] px-1.5 py-0.5 rounded font-medium"
              style={{ backgroundColor: `${TYPE_COLORS[node.type]}20`, color: TYPE_COLORS[node.type] }}>
              {node.type}
            </span>
          </div>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded">
          <X className="h-4 w-4 text-slate-400" />
        </button>
      </div>

      {/* Tier badge for contacts */}
      {node.type === 'contact' && parseInt(String(node.tier)) > 0 && (
        <span className="inline-block text-xs font-medium px-2 py-0.5 rounded text-white"
          style={{ backgroundColor: TIER_COLORS[String(node.tier)] || '#6b7280' }}>
          Tier {node.tier}
        </span>
      )}

      {/* Quality score */}
      {node.data_quality_score !== undefined && (
        <QualityBadge score={node.data_quality_score} />
      )}

      {/* Domain tags */}
      {node.domain_tags && node.domain_tags.length > 0 && (
        <DomainTagChips tags={node.domain_tags} />
      )}

      <div className="space-y-2 text-sm">
        {node.program && <DetailRow icon={Building2} label="Program" value={node.program} />}
        {node.company && <DetailRow icon={Briefcase} label="Company" value={node.company} />}
        {node.prime && <DetailRow icon={Briefcase} label="Prime" value={node.prime} />}
        {node.agency && <DetailRow icon={Network} label="Agency" value={node.agency} />}
        {node.value && <DetailRow icon={Building2} label="Value" value={node.value} />}
        {node.location && <DetailRow icon={MapPin} label="Location" value={node.location} />}
        {node.headquarters && <DetailRow icon={MapPin} label="HQ" value={node.headquarters} />}
        {node.clearance && <DetailRow icon={Briefcase} label="Clearance" value={node.clearance} />}
        {node.email && <DetailRow icon={Mail} label="Email" value={node.email} />}
        {node.phone && <DetailRow icon={Phone} label="Phone" value={node.phone} />}
        {node.bd_score !== undefined && <DetailRow icon={Network} label="BD Score" value={String(node.bd_score)} />}
        {node.linkedin && (
          <a href={node.linkedin} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-blue-600 hover:underline text-xs">
            <Linkedin className="h-3.5 w-3.5" /> LinkedIn Profile
          </a>
        )}
      </div>

      <div className="flex flex-col gap-2 pt-2 border-t border-slate-200 dark:border-slate-700">
        {node.type === 'contact' && onNavigateToContact && (
          <button onClick={() => onNavigateToContact(node.name)}
            className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700">
            <ExternalLink className="h-3.5 w-3.5" /> View Full Profile
          </button>
        )}
        {node.type === 'program' && onNavigateToProgram && (
          <button onClick={() => onNavigateToProgram(node.name)}
            className="flex items-center gap-2 px-3 py-2 bg-purple-600 text-white rounded-lg text-xs font-medium hover:bg-purple-700 w-full justify-center">
            <ExternalLink className="h-3.5 w-3.5" /> View Program
          </button>
        )}
        {node.type === 'contact' && onNavigateToOutreach && (
          <button onClick={onNavigateToOutreach}
            className="flex items-center gap-2 px-3 py-2 bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 rounded-lg text-xs font-medium hover:bg-indigo-100">
            <Send className="h-3.5 w-3.5" /> Start Outreach
          </button>
        )}
      </div>
    </div>
  );
}

function DetailRow({ icon: Icon, label, value }: { icon: typeof User; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      <Icon className="h-3.5 w-3.5 text-slate-400 mt-0.5 shrink-0" />
      <div>
        <span className="text-[10px] text-slate-400 uppercase">{label}</span>
        <p className="text-slate-700 dark:text-slate-300 text-xs">{value}</p>
      </div>
    </div>
  );
}

// ─── Filter Panel ────────────────────────────────────────────────────────────

function FilterPanel({
  graphData, filters, onFiltersChange, onClose,
}: {
  graphData: GraphData;
  filters: { programs: string[]; tiers: string[]; companies: string[] };
  onFiltersChange: (f: typeof filters) => void;
  onClose: () => void;
}) {
  const programs = useMemo(() => {
    const set = new Set<string>();
    graphData.nodes.forEach(n => {
      if (n.type === 'program') set.add(n.name);
    });
    return [...set].sort();
  }, [graphData]);

  const companies = useMemo(() => {
    const set = new Set<string>();
    graphData.nodes.forEach(n => {
      if ((n.type === 'contact' || n.type === 'contractor') && (n.company || n.name)) {
        set.add(n.type === 'contractor' ? n.name : (n.company || ''));
      }
    });
    return [...set].filter(Boolean).sort().slice(0, 25);
  }, [graphData]);

  const toggle = (arr: string[], val: string) =>
    arr.includes(val) ? arr.filter(v => v !== val) : [...arr, val];

  return (
    <div className="absolute top-12 left-4 z-20 w-72 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 p-4 max-h-[70vh] overflow-y-auto">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-sm text-slate-800 dark:text-slate-100">Filters</h4>
        <button onClick={onClose} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded"><X className="h-4 w-4 text-slate-400" /></button>
      </div>

      <div className="space-y-4">
        <div>
          <p className="text-xs font-medium text-slate-500 mb-1.5">Tiers</p>
          <div className="flex flex-wrap gap-1.5">
            {['1','2','3','4','5','6'].map(t => (
              <button key={t} onClick={() => onFiltersChange({ ...filters, tiers: toggle(filters.tiers, t) })}
                className={`px-2 py-0.5 rounded text-xs font-medium border transition-colors ${filters.tiers.includes(t) ? 'bg-blue-600 text-white border-blue-600' : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-600'}`}>
                T{t}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs font-medium text-slate-500 mb-1.5">Programs ({programs.length})</p>
          <div className="max-h-32 overflow-y-auto space-y-1">
            {programs.slice(0, 15).map(p => (
              <label key={p} className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 cursor-pointer">
                <input type="checkbox" checked={filters.programs.includes(p)}
                  onChange={() => onFiltersChange({ ...filters, programs: toggle(filters.programs, p) })}
                  className="rounded border-slate-300" />
                <span className="truncate">{p}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs font-medium text-slate-500 mb-1.5">Companies ({companies.length})</p>
          <div className="max-h-32 overflow-y-auto space-y-1">
            {companies.map(c => (
              <label key={c} className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 cursor-pointer">
                <input type="checkbox" checked={filters.companies.includes(c)}
                  onChange={() => onFiltersChange({ ...filters, companies: toggle(filters.companies, c) })}
                  className="rounded border-slate-300" />
                <span className="truncate">{c}</span>
              </label>
            ))}
          </div>
        </div>

        <button onClick={() => onFiltersChange({ programs: [], tiers: [], companies: [] })}
          className="w-full text-xs text-slate-500 hover:text-red-600 py-1">Clear All Filters</button>
      </div>
    </div>
  );
}

// ─── Dynamic Legend ──────────────────────────────────────────────────────────

function GraphLegend({ colorBy }: { colorBy: ColorBy }) {
  if (colorBy === 'quality') {
    return (
      <div className="absolute bottom-4 left-4 bg-white/90 dark:bg-slate-800/90 rounded-lg border border-slate-200 dark:border-slate-700 px-3 py-2 text-[10px] space-y-1 backdrop-blur">
        <p className="font-semibold text-slate-600 dark:text-slate-400 mb-1">Quality Score</p>
        <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: '#22c55e' }} /> 80-100</div>
        <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: '#84cc16' }} /> 60-79</div>
        <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: '#f59e0b' }} /> 40-59</div>
        <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: '#f97316' }} /> 20-39</div>
        <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: '#ef4444' }} /> 0-19</div>
      </div>
    );
  }

  if (colorBy === 'domain') {
    return (
      <div className="absolute bottom-4 left-4 bg-white/90 dark:bg-slate-800/90 rounded-lg border border-slate-200 dark:border-slate-700 px-3 py-2 text-[10px] backdrop-blur">
        <p className="font-semibold text-slate-600 dark:text-slate-400 mb-1">Defense Domains</p>
        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
          {Object.entries(DOMAIN_COLORS).slice(0, 10).map(([tag, color]) => (
            <div key={tag} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: color }} />
              <span className="text-slate-600 dark:text-slate-400">{tag.replace(/_/g, ' ')}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Default: type legend
  return (
    <div className="absolute bottom-4 left-4 bg-white/90 dark:bg-slate-800/90 rounded-lg border border-slate-200 dark:border-slate-700 px-3 py-2 text-[10px] space-y-1 backdrop-blur">
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-blue-500 inline-block" /> Contact</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded inline-block rotate-45 bg-purple-500" style={{ borderRadius: '2px' }} /> Program</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-green-500 inline-block" /> Contractor</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-500 inline-block" /> Job</span>
      </div>
      <p className="text-slate-400">Click: details · Double-click: navigate · Scroll: zoom</p>
    </div>
  );
}

// ─── Main Component (V6) ────────────────────────────────────────────────────

export function GraphExplorer({ onNavigateToContact, onNavigateToProgram, onNavigateToOutreach }: GraphExplorerProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('explore');
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [competitionData, setCompetitionData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [competitionLoading, setCompetitionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [layout, setLayout] = useState<LayoutType>('force');
  const [colorBy, setColorBy] = useState<ColorBy>('type');
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<{ programs: string[]; tiers: string[]; companies: string[] }>({ programs: [], tiers: [], companies: [] });
  const [competitionFilter, setCompetitionFilter] = useState('');

  // V6: Node type toggles and domain filter
  const [activeNodeTypes, setActiveNodeTypes] = useState<Set<NodeType>>(new Set(['contact', 'program', 'contractor', 'job']));
  const [domainTags, setDomainTags] = useState<Array<{ tag: string; count: number }>>([]);
  const [activeDomain, setActiveDomain] = useState('');

  const containerRef = useRef<HTMLDivElement>(null);

  // Fetch domain tags
  useEffect(() => {
    fetch('/graph/domain-tags').then(r => r.json()).then(data => {
      setDomainTags(data.tags || []);
    }).catch(() => {});
  }, []);

  // Fetch graph data (V6 enriched)
  useEffect(() => {
    if (viewMode !== 'explore') return;
    setLoading(true);
    const params = new URLSearchParams({
      limit: '800',
      include_quality: 'true',
      include_domain_tags: 'true',
      node_types: Array.from(activeNodeTypes).join(','),
    });
    if (activeDomain) params.set('domain_filter', activeDomain);

    fetch(`/graph/data?${params}`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(data => setGraphData(data))
      .catch(err => setError(err instanceof Error ? err.message : 'Failed to load graph data'))
      .finally(() => setLoading(false));
  }, [viewMode, activeNodeTypes, activeDomain]);

  // Fetch competition data
  const loadCompetition = useCallback(() => {
    setCompetitionLoading(true);
    const params = new URLSearchParams({ limit: '200' });
    if (competitionFilter) params.set('program_filter', competitionFilter);

    fetch(`/graph/competition?${params}`)
      .then(r => r.json())
      .then(data => setCompetitionData(data))
      .catch(() => {})
      .finally(() => setCompetitionLoading(false));
  }, [competitionFilter]);

  useEffect(() => {
    if (viewMode === 'competition') loadCompetition();
  }, [viewMode, loadCompetition]);

  const activeData = viewMode === 'explore' ? graphData : competitionData;

  const handleNodeClick = useCallback((node: GraphNode) => setSelectedNode(node), []);
  const handleNodeDblClick = useCallback((node: GraphNode) => {
    if (node.type === 'contact' && onNavigateToContact) onNavigateToContact(node.name);
    if (node.type === 'program' && onNavigateToProgram) onNavigateToProgram(node.name);
  }, [onNavigateToContact, onNavigateToProgram]);

  const { filteredData } = useG6Graph(
    containerRef, activeData, layout, colorBy,
    handleNodeClick, handleNodeDblClick, searchTerm, filters,
  );

  const toggleNodeType = (t: NodeType) => {
    setActiveNodeTypes(prev => {
      const next = new Set(prev);
      if (next.has(t) && next.size > 1) next.delete(t);
      else next.add(t);
      return next;
    });
  };

  const activeFilterCount = filters.programs.length + filters.tiers.length + filters.companies.length;
  const isLoading = viewMode === 'explore' ? loading : competitionLoading;

  if (isLoading && !activeData) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-3" />
          <p className="text-slate-500">Loading graph data...</p>
        </div>
      </div>
    );
  }

  if (error && viewMode === 'explore') {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Network className="h-8 w-8 text-red-400 mx-auto mb-3" />
          <p className="text-red-600 font-medium">Failed to load graph</p>
          <p className="text-sm text-slate-500 mt-1">{error}</p>
          <p className="text-xs text-slate-400 mt-2">Ensure Hub API is running on :8100</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shrink-0">
        <div className="flex items-center gap-2">
          <Network className="h-5 w-5 text-blue-500" />
          <h1 className="text-lg font-bold text-slate-800 dark:text-slate-100">Graph Explorer</h1>
          <span className="text-xs text-slate-500">
            {filteredData ? `${filteredData.nodes.length} nodes · ${filteredData.edges.length} edges` : ''}
          </span>

          {/* View mode toggle */}
          <div className="flex gap-0.5 bg-slate-100 dark:bg-slate-900 rounded-lg p-0.5 ml-2">
            <button onClick={() => setViewMode('explore')}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors flex items-center gap-1 ${viewMode === 'explore' ? 'bg-white dark:bg-slate-700 shadow text-slate-800 dark:text-slate-100' : 'text-slate-500 hover:text-slate-700'}`}>
              <Network className="h-3 w-3" /> Explore
            </button>
            <button onClick={() => setViewMode('competition')}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors flex items-center gap-1 ${viewMode === 'competition' ? 'bg-white dark:bg-slate-700 shadow text-orange-600 dark:text-orange-400' : 'text-slate-500 hover:text-slate-700'}`}>
              <Swords className="h-3 w-3" /> Competition
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Competition filter */}
          {viewMode === 'competition' && (
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text" value={competitionFilter}
                onChange={e => setCompetitionFilter(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && loadCompetition()}
                placeholder="Filter by program..."
                className="pl-8 pr-3 py-1.5 w-44 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              />
            </div>
          )}

          {/* Search (explore mode) */}
          {viewMode === 'explore' && (
            <>
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text" value={searchTerm}
                  onChange={e => setSearchTerm(e.target.value)}
                  placeholder="Search nodes..."
                  className="pl-8 pr-3 py-1.5 w-40 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Node type toggles */}
              <div className="flex gap-0.5">
                {(['contact', 'program', 'contractor', 'job'] as const).map(t => (
                  <button key={t} onClick={() => toggleNodeType(t)}
                    className={`px-1.5 py-1 rounded text-[10px] font-medium transition-colors ${
                      activeNodeTypes.has(t) ? 'text-white' : 'bg-slate-100 dark:bg-slate-900 text-slate-400'
                    }`}
                    style={activeNodeTypes.has(t) ? { backgroundColor: TYPE_COLORS[t] } : undefined}>
                    {t.slice(0, 4)}
                  </button>
                ))}
              </div>

              {/* Domain filter */}
              {domainTags.length > 0 && (
                <select value={activeDomain} onChange={e => setActiveDomain(e.target.value)}
                  className="px-2 py-1.5 rounded-lg text-xs border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300">
                  <option value="">Domain: All</option>
                  {domainTags.map(d => <option key={d.tag} value={d.tag}>{d.tag} ({d.count})</option>)}
                </select>
              )}

              {/* Filter button */}
              <button onClick={() => setShowFilters(!showFilters)}
                className={`flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs font-medium border transition-colors ${activeFilterCount > 0 ? 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-700' : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700'}`}>
                <Filter className="h-3.5 w-3.5" />
                {activeFilterCount > 0 ? activeFilterCount : ''}
              </button>
            </>
          )}

          {/* Layout toggle */}
          <div className="flex gap-0.5 bg-slate-100 dark:bg-slate-900 rounded-lg p-0.5">
            {(['force', 'radial', 'concentric'] as const).map(l => (
              <button key={l} onClick={() => setLayout(l)}
                className={`px-2 py-1 rounded-md text-xs font-medium transition-colors ${layout === l ? 'bg-white dark:bg-slate-700 shadow text-slate-800 dark:text-slate-100' : 'text-slate-500 hover:text-slate-700'}`}>
                {l.charAt(0).toUpperCase() + l.slice(1)}
              </button>
            ))}
          </div>

          {/* Color by */}
          <select value={colorBy} onChange={e => setColorBy(e.target.value as ColorBy)}
            className="px-2 py-1.5 rounded-lg text-xs border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300">
            <option value="type">Color: Type</option>
            <option value="priority">Color: Priority</option>
            <option value="tier">Color: Tier</option>
            <option value="program">Color: Program</option>
            <option value="domain">Color: Domain</option>
            <option value="quality">Color: Quality</option>
          </select>

          {/* Reset */}
          <button onClick={() => { setSearchTerm(''); setFilters({ programs: [], tiers: [], companies: [] }); setSelectedNode(null); setActiveDomain(''); }}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700" title="Reset view">
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Graph + sidebar */}
      <div className="flex-1 flex overflow-hidden relative">
        {showFilters && graphData && viewMode === 'explore' && (
          <FilterPanel graphData={graphData} filters={filters} onFiltersChange={setFilters} onClose={() => setShowFilters(false)} />
        )}

        {/* G6 container */}
        <div ref={containerRef} className="flex-1 bg-slate-50 dark:bg-slate-900" />

        {/* Legend */}
        <GraphLegend colorBy={viewMode === 'competition' ? 'type' : colorBy} />

        {/* Competition mode info */}
        {viewMode === 'competition' && (
          <div className="absolute top-4 left-4 bg-orange-50/90 dark:bg-orange-900/30 rounded-lg border border-orange-200 dark:border-orange-800 px-3 py-2 text-[11px] text-orange-700 dark:text-orange-300 backdrop-blur">
            Orange edges = competitors on shared programs · Node size = program count
          </div>
        )}

        {/* Detail panel */}
        {selectedNode && (
          <NodeDetailPanel
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
            onNavigateToContact={onNavigateToContact}
            onNavigateToProgram={onNavigateToProgram}
            onNavigateToOutreach={onNavigateToOutreach}
          />
        )}
      </div>
    </div>
  );
}
