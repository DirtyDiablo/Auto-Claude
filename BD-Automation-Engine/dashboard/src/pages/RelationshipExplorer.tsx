import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import {
  Search, Loader2, GitMerge, User, Building2, Briefcase,
  MapPin, Cpu, X, ArrowRight, Info,
} from 'lucide-react';
import ForceGraph2D from 'react-force-graph-2d';

// ─── Types ─────────────────────────────────────────────────────────────────

interface GraphNode {
  id: string;
  name: string;
  type: string;
  val?: number;
  color?: string;
  [key: string]: unknown;
}

interface GraphLink {
  source: string;
  target: string;
  type: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

type SearchMode = 'contact' | 'program';

// ─── Node Colors by Type ───────────────────────────────────────────────────

const NODE_COLORS: Record<string, string> = {
  contact: '#3b82f6',
  person: '#3b82f6',
  contractor: '#22c55e',
  company: '#22c55e',
  program: '#f97316',
  location: '#a855f7',
  job: '#ef4444',
  skill: '#06b6d4',
  meeting: '#f59e0b',
  placement: '#ec4899',
};

function getNodeColor(type: string): string {
  return NODE_COLORS[type.toLowerCase()] || '#6b7280';
}

const NODE_ICONS: Record<string, typeof User> = {
  contact: User,
  person: User,
  contractor: Building2,
  company: Building2,
  program: Briefcase,
  location: MapPin,
  job: Briefcase,
  skill: Cpu,
};

// ─── Props ─────────────────────────────────────────────────────────────────

interface RelationshipExplorerProps {
  onNavigateToContact?: (name: string) => void;
  onNavigateToProgram?: (name: string) => void;
}

// ─── Main Component ────────────────────────────────────────────────────────

export function RelationshipExplorer({ onNavigateToContact, onNavigateToProgram }: RelationshipExplorerProps) {
  const [searchMode, setSearchMode] = useState<SearchMode>('contact');
  const [searchQuery, setSearchQuery] = useState('');
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Introduction path state
  const [introFrom, setIntroFrom] = useState('');
  const [introTo, setIntroTo] = useState('');
  const [introPath, setIntroPath] = useState<unknown[] | null>(null);
  const [introLoading, setIntroLoading] = useState(false);
  const [introError, setIntroError] = useState<string | null>(null);
  const [highlightedNodeIds, setHighlightedNodeIds] = useState<Set<string>>(new Set());

  const graphRef = useRef<unknown>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Responsive dimensions
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };
    updateDimensions();
    const resizeObserver = new ResizeObserver(updateDimensions);
    if (containerRef.current) resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  // Search for entity network
  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);
    setSelectedNode(null);
    setIntroPath(null);
    setHighlightedNodeIds(new Set());

    try {
      const endpoint = searchMode === 'contact'
        ? `/bdgraph/contact/${encodeURIComponent(searchQuery)}`
        : `/bdgraph/program/${encodeURIComponent(searchQuery)}`;

      const resp = await fetch(endpoint);
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: 'Not found' }));
        throw new Error(err.detail || 'Failed to fetch');
      }

      const data = await resp.json();
      const nodes: GraphNode[] = [];
      const links: GraphLink[] = [];
      const nodeIds = new Set<string>();

      if (searchMode === 'contact' && data.contact) {
        // Center node
        const contact = data.contact;
        nodes.push({ id: contact.id, name: contact.name, type: 'contact', val: 12, ...contact.properties });
        nodeIds.add(contact.id);

        // Employer
        if (data.employer) {
          nodes.push({ id: data.employer.id, name: data.employer.name, type: 'contractor', val: 8, ...data.employer.properties });
          nodeIds.add(data.employer.id);
          links.push({ source: contact.id, target: data.employer.id, type: 'WORKS_FOR' });
        }

        // Programs
        for (const p of data.programs || []) {
          if (!nodeIds.has(p.id)) {
            nodes.push({ id: p.id, name: p.name, type: 'program', val: 8, ...p.properties });
            nodeIds.add(p.id);
          }
          links.push({ source: contact.id, target: p.id, type: 'WORKS_ON' });
        }

        // Manages / Managed by
        for (const m of data.manages || []) {
          if (!nodeIds.has(m.id)) {
            nodes.push({ id: m.id, name: m.name, type: 'contact', val: 6, ...m.properties });
            nodeIds.add(m.id);
          }
          links.push({ source: contact.id, target: m.id, type: 'MANAGES' });
        }
        for (const m of data.managed_by || []) {
          if (!nodeIds.has(m.id)) {
            nodes.push({ id: m.id, name: m.name, type: 'contact', val: 6, ...m.properties });
            nodeIds.add(m.id);
          }
          links.push({ source: m.id, target: contact.id, type: 'MANAGES' });
        }

        // Connections
        for (const c of data.connections || []) {
          if (!nodeIds.has(c.id)) {
            nodes.push({ id: c.id, name: c.name, type: 'contact', val: 5, ...c.properties });
            nodeIds.add(c.id);
          }
          links.push({ source: contact.id, target: c.id, type: 'KNOWS' });
        }

        // Skills
        for (const s of data.skills || []) {
          if (!nodeIds.has(s.id)) {
            nodes.push({ id: s.id, name: s.name, type: 'skill', val: 4, ...s.properties });
            nodeIds.add(s.id);
          }
          links.push({ source: contact.id, target: s.id, type: 'HAS_SKILL' });
        }
      } else if (searchMode === 'program' && data.program) {
        // Program ecosystem
        const program = data.program;
        nodes.push({ id: program.id, name: program.name, type: 'program', val: 14, ...program.properties });
        nodeIds.add(program.id);

        for (const p of data.primes || []) {
          if (!nodeIds.has(p.id)) {
            nodes.push({ id: p.id, name: p.name, type: 'contractor', val: 8, ...p.properties });
            nodeIds.add(p.id);
          }
          links.push({ source: p.id, target: program.id, type: 'PRIMES_ON' });
        }

        for (const s of data.subcontractors || []) {
          if (!nodeIds.has(s.id)) {
            nodes.push({ id: s.id, name: s.name, type: 'contractor', val: 6, ...s.properties });
            nodeIds.add(s.id);
          }
          links.push({ source: s.id, target: program.id, type: 'HAS_PAST_PERF' });
        }

        for (const c of data.contacts || []) {
          const contact = c.contact || c;
          if (!nodeIds.has(contact.id)) {
            nodes.push({ id: contact.id, name: contact.name, type: 'contact', val: 5, ...contact.properties });
            nodeIds.add(contact.id);
          }
          links.push({ source: contact.id, target: program.id, type: 'WORKS_ON' });
        }

        for (const j of data.jobs || []) {
          if (!nodeIds.has(j.id)) {
            nodes.push({ id: j.id, name: j.name, type: 'job', val: 4, ...j.properties });
            nodeIds.add(j.id);
          }
          links.push({ source: program.id, target: j.id, type: 'HAS_OPENING' });
        }

        for (const l of data.locations || []) {
          if (!nodeIds.has(l.id)) {
            nodes.push({ id: l.id, name: l.name, type: 'location', val: 5, ...l.properties });
            nodeIds.add(l.id);
          }
          links.push({ source: program.id, target: l.id, type: 'LOCATED_AT' });
        }
      }

      // Apply colors
      for (const n of nodes) {
        n.color = getNodeColor(n.type);
      }

      setGraphData({ nodes, links });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load network');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, searchMode]);

  // Find introduction path
  const handleFindPath = useCallback(async () => {
    if (!introFrom.trim() || !introTo.trim()) return;

    setIntroLoading(true);
    setIntroError(null);
    setIntroPath(null);
    setHighlightedNodeIds(new Set());

    try {
      const resp = await fetch(`/bdgraph/introduction-path/${encodeURIComponent(introFrom)}/${encodeURIComponent(introTo)}`);
      if (!resp.ok) throw new Error('Failed to find path');

      const data = await resp.json();
      if (data.error) {
        setIntroError(data.error);
        return;
      }

      setIntroPath(data.path);

      // Highlight path nodes
      const ids = new Set<string>();
      for (const step of data.path) {
        const entity = step.entity || step;
        if (entity.id) ids.add(entity.id);
      }
      setHighlightedNodeIds(ids);
    } catch (err) {
      setIntroError(err instanceof Error ? err.message : 'Failed to find path');
    } finally {
      setIntroLoading(false);
    }
  }, [introFrom, introTo]);

  // Node click handler
  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(node);
  }, []);

  // Node canvas renderer
  const paintNode = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const x = (node as unknown as { x: number }).x;
    const y = (node as unknown as { y: number }).y;
    const size = (node.val || 6) / 2;
    const isHighlighted = highlightedNodeIds.has(node.id);
    const fontSize = Math.max(10 / globalScale, 2);

    // Node circle
    ctx.beginPath();
    ctx.arc(x, y, size, 0, 2 * Math.PI);
    ctx.fillStyle = node.color || '#6b7280';
    ctx.fill();

    if (isHighlighted) {
      ctx.strokeStyle = '#facc15';
      ctx.lineWidth = 3 / globalScale;
      ctx.stroke();
    } else {
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1 / globalScale;
      ctx.stroke();
    }

    // Label
    if (globalScale > 0.8) {
      ctx.font = `${fontSize}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = isHighlighted ? '#facc15' : '#e2e8f0';
      ctx.fillText(node.name, x, y + size + 2);
    }
  }, [highlightedNodeIds]);

  return (
    <div className="h-full flex">
      {/* Left Panel — Search & Intro Path */}
      <div className="w-80 flex-shrink-0 border-r border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex flex-col overflow-y-auto">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2 mb-3">
            <GitMerge className="w-5 h-5 text-purple-500" />
            <h1 className="text-lg font-bold text-slate-900 dark:text-white">Relationship Explorer</h1>
          </div>

          {/* Mode Toggle */}
          <div className="flex rounded-lg bg-slate-100 dark:bg-slate-700 p-0.5 mb-3">
            <button
              onClick={() => setSearchMode('contact')}
              className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${
                searchMode === 'contact'
                  ? 'bg-white dark:bg-slate-600 text-blue-600 dark:text-blue-400 shadow-sm'
                  : 'text-slate-500 dark:text-slate-400'
              }`}
            >
              Contact Network
            </button>
            <button
              onClick={() => setSearchMode('program')}
              className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${
                searchMode === 'program'
                  ? 'bg-white dark:bg-slate-600 text-orange-600 dark:text-orange-400 shadow-sm'
                  : 'text-slate-500 dark:text-slate-400'
              }`}
            >
              Program Network
            </button>
          </div>

          {/* Search */}
          <form
            onSubmit={(e) => { e.preventDefault(); handleSearch(); }}
            className="flex gap-2"
          >
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 w-3.5 h-3.5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={searchMode === 'contact' ? 'Enter contact name...' : 'Enter program name...'}
                className="w-full pl-8 pr-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !searchQuery.trim()}
              className="px-3 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            </button>
          </form>

          {error && (
            <p className="mt-2 text-xs text-red-500">{error}</p>
          )}
        </div>

        {/* Introduction Path Finder */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
            <ArrowRight className="w-4 h-4 text-amber-500" />
            Find Introduction Path
          </h2>
          <div className="space-y-2">
            <input
              type="text"
              value={introFrom}
              onChange={(e) => setIntroFrom(e.target.value)}
              placeholder="From contact..."
              className="w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
            <input
              type="text"
              value={introTo}
              onChange={(e) => setIntroTo(e.target.value)}
              placeholder="To contact..."
              className="w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
            <button
              onClick={handleFindPath}
              disabled={introLoading || !introFrom.trim() || !introTo.trim()}
              className="w-full py-2 text-sm font-medium rounded-lg bg-amber-500 text-white hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {introLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitMerge className="w-4 h-4" />}
              Find Path
            </button>
          </div>

          {introError && (
            <p className="mt-2 text-xs text-red-500">{introError}</p>
          )}

          {introPath && introPath.length > 0 && (
            <div className="mt-3 space-y-1">
              <p className="text-xs font-semibold text-slate-600 dark:text-slate-400">
                Path ({introPath.length - 1} hop{introPath.length - 1 !== 1 ? 's' : ''}):
              </p>
              {introPath.map((step: unknown, idx: number) => {
                const s = step as Record<string, unknown>;
                const entity = (s.entity || s) as Record<string, unknown>;
                const relType = s.relationship as string | undefined;
                return (
                  <div key={idx} className="flex items-center gap-2">
                    {idx > 0 && relType && (
                      <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded">
                        {relType}
                      </span>
                    )}
                    <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                      {entity.name as string}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      ({entity.type as string})
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Graph Stats */}
        {graphData.nodes.length > 0 && (
          <div className="p-4 border-b border-slate-200 dark:border-slate-700">
            <p className="text-xs text-slate-500">
              <span className="font-semibold">{graphData.nodes.length}</span> nodes, <span className="font-semibold">{graphData.links.length}</span> edges
            </p>
          </div>
        )}

        {/* Legend */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-700">
          <p className="text-xs font-semibold text-slate-600 dark:text-slate-400 mb-2">Legend</p>
          <div className="grid grid-cols-2 gap-1.5">
            {Object.entries(NODE_COLORS).filter(([k]) => !['person', 'company'].includes(k)).map(([type, color]) => (
              <div key={type} className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-[11px] text-slate-500 dark:text-slate-400 capitalize">{type}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Node Detail */}
        {selectedNode && (
          <div className="p-4 flex-1">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
                <Info className="w-4 h-4" />
                Entity Details
              </h3>
              <button onClick={() => setSelectedNode(null)} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded">
                <X className="w-3.5 h-3.5 text-slate-400" />
              </button>
            </div>

            <div className="space-y-1.5">
              <div>
                <span className="text-[10px] text-slate-400 uppercase">Name</span>
                <p className="text-sm font-medium text-slate-900 dark:text-white">{selectedNode.name}</p>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase">Type</span>
                <p className="text-xs capitalize" style={{ color: getNodeColor(selectedNode.type) }}>{selectedNode.type}</p>
              </div>
              {Object.entries(selectedNode)
                .filter(([k]) => !['id', 'name', 'type', 'val', 'color', 'x', 'y', 'vx', 'vy', 'fx', 'fy', 'index', '__indexColor'].includes(k))
                .filter(([, v]) => v !== undefined && v !== null && v !== '')
                .slice(0, 10)
                .map(([key, value]) => (
                  <div key={key}>
                    <span className="text-[10px] text-slate-400 uppercase">{key.replace(/_/g, ' ')}</span>
                    <p className="text-xs text-slate-700 dark:text-slate-300">{String(value)}</p>
                  </div>
                ))}

              {/* Navigate buttons */}
              <div className="flex gap-2 mt-3">
                {selectedNode.type === 'contact' && onNavigateToContact && (
                  <button
                    onClick={() => onNavigateToContact(selectedNode.name)}
                    className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded hover:bg-blue-200"
                  >
                    View Contact
                  </button>
                )}
                {selectedNode.type === 'program' && onNavigateToProgram && (
                  <button
                    onClick={() => onNavigateToProgram(selectedNode.name)}
                    className="text-xs px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded hover:bg-orange-200"
                  >
                    View Program
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Graph Canvas */}
      <div ref={containerRef} className="flex-1 bg-slate-950 relative">
        {graphData.nodes.length > 0 ? (
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            width={dimensions.width}
            height={dimensions.height}
            nodeCanvasObject={paintNode}
            nodePointerAreaPaint={(node: GraphNode, color: string, ctx: CanvasRenderingContext2D) => {
              const x = (node as unknown as { x: number }).x;
              const y = (node as unknown as { y: number }).y;
              const size = (node.val || 6) / 2;
              ctx.beginPath();
              ctx.arc(x, y, size + 2, 0, 2 * Math.PI);
              ctx.fillStyle = color;
              ctx.fill();
            }}
            onNodeClick={handleNodeClick}
            linkColor={() => 'rgba(100, 116, 139, 0.4)'}
            linkWidth={1}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            linkLabel={(link: GraphLink) => link.type}
            backgroundColor="#0f172a"
            cooldownTicks={100}
            warmupTicks={50}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <GitMerge className="w-16 h-16 text-slate-700 mx-auto mb-4" />
              <p className="text-slate-500 font-medium">Search for a contact or program</p>
              <p className="text-sm text-slate-600 mt-1">to explore their relationship network</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
