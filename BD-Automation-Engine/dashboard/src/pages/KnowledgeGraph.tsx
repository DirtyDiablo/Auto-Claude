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
} from 'lucide-react';
import ForceGraph2D, { ForceGraphMethods } from 'react-force-graph-2d';
import { useProgramEcosystem, useContactNetwork, useTeamingPath } from '../hooks/useHubApi';

type ViewMode = 'program' | 'contact' | 'teaming';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  size?: number;
  color?: string;
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

  const graphRef = useRef<ForceGraphMethods>();
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

      const links: GraphLink[] = result.path.slice(0, -1).map((p, i) => ({
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
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
              <p className="text-slate-500">Building graph...</p>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && graphData.nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <Network className="h-16 w-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-700 mb-2">No Graph Data</h3>
              <p className="text-slate-500 max-w-md">
                {viewMode === 'teaming'
                  ? 'Enter two contractors to find the relationship path between them.'
                  : `Enter a ${viewMode} name to explore its ecosystem and relationships.`}
              </p>
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
        <div className="absolute bottom-4 right-4 flex flex-col gap-2">
          <button
            onClick={handleZoomIn}
            className="p-2 bg-white rounded-lg shadow-md hover:bg-slate-50 transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="h-5 w-5 text-slate-600" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 bg-white rounded-lg shadow-md hover:bg-slate-50 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="h-5 w-5 text-slate-600" />
          </button>
          <button
            onClick={handleFitView}
            className="p-2 bg-white rounded-lg shadow-md hover:bg-slate-50 transition-colors"
            title="Fit to View"
          >
            <Maximize2 className="h-5 w-5 text-slate-600" />
          </button>
          <button
            onClick={handleRefresh}
            className="p-2 bg-white rounded-lg shadow-md hover:bg-slate-50 transition-colors"
            title="Reset"
          >
            <RefreshCw className="h-5 w-5 text-slate-600" />
          </button>
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-md p-3">
          <p className="text-xs font-medium text-slate-500 mb-2">Legend</p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(NODE_COLORS).slice(0, -1).map(([type, color]) => (
              <div key={type} className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                <span className="capitalize text-slate-600">{type}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Node Info */}
        {selectedNode && (
          <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-4 max-w-xs">
            <div className="flex items-center gap-2 mb-2">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: selectedNode.color }}
              />
              <span className="font-medium text-slate-900">{selectedNode.label}</span>
            </div>
            <p className="text-sm text-slate-500 capitalize">Type: {selectedNode.type}</p>
            <button
              onClick={() => setSelectedNode(null)}
              className="mt-2 text-xs text-blue-600 hover:underline"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default KnowledgeGraph;
