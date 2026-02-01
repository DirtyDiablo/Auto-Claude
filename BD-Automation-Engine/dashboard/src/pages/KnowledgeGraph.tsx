/**
 * Knowledge Graph Page
 *
 * Visual graph explorer for program ecosystems, contact networks,
 * and teaming path finder using force-directed graph visualization.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import {
  Network,
  Search,
  Building2,
  Users,
  GitMerge,
  Loader2,
  AlertCircle,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  Sparkles,
  ArrowRight,
  X,
} from 'lucide-react';
import ForceGraph2D from 'react-force-graph-2d';
import { useProgramEcosystem, useContactNetwork, useTeamingPath } from '../hooks/useHubApi';

type ViewMode = 'program' | 'contact' | 'teaming';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  size?: number;
  color?: string;
  x?: number;
  y?: number;
}

interface GraphLink {
  source: string;
  target: string;
  label?: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

const NODE_COLORS: Record<string, string> = {
  program: '#8b5cf6', // purple
  contact: '#06b6d4', // cyan
  company: '#f97316', // orange
  contractor: '#f97316', // orange
  prime: '#ef4444', // red
  subcontractor: '#22c55e', // green
  job: '#3b82f6', // blue
  default: '#64748b', // slate
};

export function KnowledgeGraph() {
  const [viewMode, setViewMode] = useState<ViewMode>('program');
  const [searchQuery, setSearchQuery] = useState('');
  const [teamingFrom, setTeamingFrom] = useState('');
  const [teamingTo, setTeamingTo] = useState('');
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const programEcosystem = useProgramEcosystem();
  const contactNetwork = useContactNetwork();
  const teamingPath = useTeamingPath();

  const loading = programEcosystem.loading || contactNetwork.loading || teamingPath.loading;
  const error = programEcosystem.error || contactNetwork.error || teamingPath.error;

  // Handle search
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    if (viewMode === 'program') {
      const result = await programEcosystem.execute(searchQuery);
      if (result?.graph_data) {
        setGraphData({
          nodes: result.graph_data.nodes.map((n) => ({
            ...n,
            color: NODE_COLORS[n.type] || NODE_COLORS.default,
          })),
          links: result.graph_data.edges.map((e) => ({
            source: e.source,
            target: e.target,
            label: e.label,
          })),
        });
      }
    } else if (viewMode === 'contact') {
      const result = await contactNetwork.execute(searchQuery);
      if (result?.graph_data) {
        setGraphData({
          nodes: result.graph_data.nodes.map((n) => ({
            ...n,
            color: NODE_COLORS[n.type] || NODE_COLORS.default,
          })),
          links: result.graph_data.edges.map((e) => ({
            source: e.source,
            target: e.target,
            label: e.label,
          })),
        });
      }
    }
  };

  const handleTeamingSearch = async () => {
    if (!teamingFrom.trim() || !teamingTo.trim()) return;

    const result = await teamingPath.execute(teamingFrom, teamingTo);
    if (result) {
      // Build graph from path
      const nodes: GraphNode[] = result.path.map((p, i) => ({
        id: `node-${i}`,
        label: p.entity,
        type: p.type,
        color: NODE_COLORS[p.type] || NODE_COLORS.default,
        size: i === 0 || i === result.path.length - 1 ? 12 : 8,
      }));

      const links: GraphLink[] = result.path.slice(0, -1).map((_, i) => ({
        source: `node-${i}`,
        target: `node-${i + 1}`,
        label: result.path[i + 1]?.relationship,
      }));

      setGraphData({ nodes, links });
    }
  };

  // Node click handler
  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(node);
    if (graphRef.current) {
      graphRef.current.centerAt(node.x, node.y, 500);
      graphRef.current.zoom(2, 500);
    }
  }, []);

  // Zoom controls
  const handleZoomIn = () => graphRef.current?.zoom(graphRef.current.zoom() * 1.5, 300);
  const handleZoomOut = () => graphRef.current?.zoom(graphRef.current.zoom() / 1.5, 300);
  const handleFitView = () => graphRef.current?.zoomToFit(400, 50);
  const handleRefresh = () => {
    setGraphData({ nodes: [], links: [] });
    setSelectedNode(null);
    programEcosystem.reset();
    contactNetwork.reset();
    teamingPath.reset();
  };

  // Container dimensions
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

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
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-slate-200 bg-white">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-500">
              <Network className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Knowledge Graph</h1>
              <p className="text-slate-500">Explore BD relationships visually</p>
            </div>
          </div>

          {/* View Mode Tabs */}
          <div className="flex bg-slate-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('program')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                viewMode === 'program'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Building2 className="h-4 w-4" />
              Program Ecosystem
            </button>
            <button
              onClick={() => setViewMode('contact')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                viewMode === 'contact'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Users className="h-4 w-4" />
              Contact Network
            </button>
            <button
              onClick={() => setViewMode('teaming')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                viewMode === 'teaming'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <GitMerge className="h-4 w-4" />
              Teaming Path
            </button>
          </div>
        </div>

        {/* Search */}
        {viewMode !== 'teaming' ? (
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder={
                  viewMode === 'program'
                    ? 'Enter program name (e.g., AF DCGS, GBSD)...'
                    : 'Enter contact name...'
                }
                className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={loading || !searchQuery.trim()}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Explore
            </button>
          </div>
        ) : (
          <div className="flex gap-2 items-center">
            <div className="flex-1">
              <input
                type="text"
                value={teamingFrom}
                onChange={(e) => setTeamingFrom(e.target.value)}
                placeholder="From contractor (e.g., Leidos)..."
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <GitMerge className="h-5 w-5 text-slate-400" />
            <div className="flex-1">
              <input
                type="text"
                value={teamingTo}
                onChange={(e) => setTeamingTo(e.target.value)}
                placeholder="To contractor (e.g., Northrop Grumman)..."
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <button
              onClick={handleTeamingSearch}
              disabled={loading || !teamingFrom.trim() || !teamingTo.trim()}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <GitMerge className="h-4 w-4" />}
              Find Path
            </button>
          </div>
        )}
      </div>

      {/* Graph Area */}
      <div className="flex-1 relative bg-slate-50" ref={containerRef}>
        {/* Error */}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
              <p className="text-slate-600">{error}</p>
            </div>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-slate-50/95 to-blue-50/95 z-10">
            <div className="text-center">
              <div className="relative mb-4">
                <div className="w-16 h-16 border-4 border-blue-200 rounded-full animate-pulse" />
                <div className="absolute inset-0 w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
                <Network className="absolute inset-0 m-auto h-6 w-6 text-blue-600" />
              </div>
              <p className="text-slate-700 font-medium mb-1">Building Knowledge Graph...</p>
              <p className="text-sm text-slate-500">Analyzing relationships and connections</p>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && graphData.nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center max-w-lg">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-500 mb-6 shadow-lg">
                <Network className="h-10 w-10 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">Explore Your Data Visually</h3>
              <p className="text-slate-500 mb-6">
                {viewMode === 'teaming'
                  ? 'Enter two contractors to find the relationship path between them.'
                  : `Enter a ${viewMode} name to explore its ecosystem and relationships.`}
              </p>

              {/* Quick Examples */}
              <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
                <p className="text-sm font-medium text-slate-500 mb-3 flex items-center justify-center gap-2">
                  <Sparkles className="h-4 w-4 text-amber-500" />
                  Try these examples
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {viewMode === 'program' && (
                    <>
                      <button
                        onClick={() => { setSearchQuery('AF DCGS'); handleSearch(); }}
                        className="px-3 py-1.5 bg-purple-50 text-purple-700 rounded-lg text-sm hover:bg-purple-100 transition-colors"
                      >
                        AF DCGS
                      </button>
                      <button
                        onClick={() => { setSearchQuery('GBSD'); handleSearch(); }}
                        className="px-3 py-1.5 bg-purple-50 text-purple-700 rounded-lg text-sm hover:bg-purple-100 transition-colors"
                      >
                        GBSD
                      </button>
                      <button
                        onClick={() => { setSearchQuery('JADC2'); handleSearch(); }}
                        className="px-3 py-1.5 bg-purple-50 text-purple-700 rounded-lg text-sm hover:bg-purple-100 transition-colors"
                      >
                        JADC2
                      </button>
                    </>
                  )}
                  {viewMode === 'contact' && (
                    <>
                      <button
                        onClick={() => { setSearchQuery('John Smith'); }}
                        className="px-3 py-1.5 bg-cyan-50 text-cyan-700 rounded-lg text-sm hover:bg-cyan-100 transition-colors"
                      >
                        John Smith
                      </button>
                      <button
                        onClick={() => { setSearchQuery('Program Manager'); }}
                        className="px-3 py-1.5 bg-cyan-50 text-cyan-700 rounded-lg text-sm hover:bg-cyan-100 transition-colors"
                      >
                        Program Manager
                      </button>
                    </>
                  )}
                  {viewMode === 'teaming' && (
                    <>
                      <button
                        onClick={() => { setTeamingFrom('Leidos'); setTeamingTo('Northrop Grumman'); }}
                        className="px-3 py-1.5 bg-orange-50 text-orange-700 rounded-lg text-sm hover:bg-orange-100 transition-colors flex items-center gap-1"
                      >
                        Leidos <ArrowRight className="h-3 w-3" /> Northrop
                      </button>
                      <button
                        onClick={() => { setTeamingFrom('GDIT'); setTeamingTo('Raytheon'); }}
                        className="px-3 py-1.5 bg-orange-50 text-orange-700 rounded-lg text-sm hover:bg-orange-100 transition-colors flex items-center gap-1"
                      >
                        GDIT <ArrowRight className="h-3 w-3" /> Raytheon
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Graph */}
        {graphData.nodes.length > 0 && (
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            width={dimensions.width}
            height={dimensions.height}
            nodeLabel="label"
            nodeColor={(node: GraphNode) => node.color || '#64748b'}
            nodeVal={(node: GraphNode) => node.size || 5}
            linkLabel="label"
            linkColor={() => '#cbd5e1'}
            linkWidth={1.5}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            onNodeClick={handleNodeClick}
            nodeCanvasObject={(node: GraphNode, ctx, globalScale) => {
              const label = node.label;
              const fontSize = 12 / globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;
              ctx.fillStyle = node.color || '#64748b';
              ctx.beginPath();
              ctx.arc(node.x!, node.y!, node.size || 5, 0, 2 * Math.PI);
              ctx.fill();

              // Label
              ctx.textAlign = 'center';
              ctx.textBaseline = 'top';
              ctx.fillStyle = '#1e293b';
              ctx.fillText(label, node.x!, node.y! + (node.size || 5) + 2);
            }}
          />
        )}

        {/* Controls */}
        <div className="absolute bottom-4 right-4 flex flex-col gap-1 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-slate-200 p-1">
          <button
            onClick={handleZoomIn}
            className="p-2.5 hover:bg-slate-100 rounded-lg transition-colors group"
            title="Zoom In"
          >
            <ZoomIn className="h-5 w-5 text-slate-500 group-hover:text-slate-700" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2.5 hover:bg-slate-100 rounded-lg transition-colors group"
            title="Zoom Out"
          >
            <ZoomOut className="h-5 w-5 text-slate-500 group-hover:text-slate-700" />
          </button>
          <div className="h-px bg-slate-200 mx-2" />
          <button
            onClick={handleFitView}
            className="p-2.5 hover:bg-slate-100 rounded-lg transition-colors group"
            title="Fit to View"
          >
            <Maximize2 className="h-5 w-5 text-slate-500 group-hover:text-slate-700" />
          </button>
          <button
            onClick={handleRefresh}
            className="p-2.5 hover:bg-red-50 rounded-lg transition-colors group"
            title="Reset"
          >
            <RefreshCw className="h-5 w-5 text-slate-500 group-hover:text-red-500" />
          </button>
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-slate-200 p-4">
          <p className="text-xs font-semibold text-slate-700 mb-3">Node Types</p>
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
            {Object.entries(NODE_COLORS).slice(0, -1).map(([type, color]) => (
              <div key={type} className="flex items-center gap-2 group">
                <div
                  className="w-3 h-3 rounded-full shadow-sm transition-transform group-hover:scale-125"
                  style={{ backgroundColor: color }}
                />
                <span className="capitalize text-slate-600 group-hover:text-slate-900">{type}</span>
              </div>
            ))}
          </div>
          {graphData.nodes.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-100">
              <p className="text-xs text-slate-500">
                {graphData.nodes.length} nodes • {graphData.links.length} connections
              </p>
            </div>
          )}
        </div>

        {/* Selected Node Info */}
        {selectedNode && (
          <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-slate-200 p-4 max-w-xs animate-in slide-in-from-right duration-300">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center shadow-sm"
                  style={{ backgroundColor: `${selectedNode.color}20` }}
                >
                  <div
                    className="w-5 h-5 rounded-full"
                    style={{ backgroundColor: selectedNode.color }}
                  />
                </div>
                <div>
                  <span className="font-semibold text-slate-900 block">{selectedNode.label}</span>
                  <span className="text-sm text-slate-500 capitalize">{selectedNode.type}</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X className="h-4 w-4 text-slate-400" />
              </button>
            </div>
            <div className="mt-3 pt-3 border-t border-slate-100 flex gap-2">
              <button
                onClick={() => {
                  setSearchQuery(selectedNode.label);
                  if (selectedNode.type === 'contact') setViewMode('contact');
                  else if (selectedNode.type === 'program') setViewMode('program');
                }}
                className="flex-1 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium hover:bg-blue-100 transition-colors"
              >
                Explore
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default KnowledgeGraph;
