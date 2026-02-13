/**
 * Graph Viewer — Interactive knowledge graph visualization
 *
 * Renders Neo4j graph data with interactive zoom/pan/filter.
 * Uses reagraph (already in the project) for 3D-capable graph rendering.
 *
 * Data source: /api/neo4j/full-graph or /api/bdgraph/full-graph endpoint
 */

import { useState, useCallback, useMemo, useEffect } from 'react'
import { GraphCanvas, type GraphNode, type GraphEdge } from 'reagraph'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface GraphEntity {
  id: string
  name: string
  type: string
  properties?: Record<string, unknown>
}

interface GraphRelationship {
  source: string
  target: string
  type: string
  properties?: Record<string, unknown>
}

interface GraphData {
  nodes: GraphEntity[]
  edges: GraphRelationship[]
}

interface GraphViewerProps {
  /** Pre-loaded graph data (if available) */
  data?: GraphData
  /** API endpoint to fetch graph data from */
  endpoint?: string
  /** Graph title */
  title?: string
  /** Container height in px */
  height?: number
  /** Node types to show (empty = all) */
  visibleTypes?: string[]
  /** Enable 3D mode */
  is3D?: boolean
}

// ---------------------------------------------------------------------------
// Node type → color mapping
// ---------------------------------------------------------------------------

const NODE_TYPE_COLORS: Record<string, string> = {
  Person:      '#3b82f6', // blue
  Company:     '#8b5cf6', // violet
  Program:     '#ef4444', // red
  Job:         '#f59e0b', // amber
  Contract:    '#10b981', // emerald
  Location:    '#06b6d4', // cyan
  Interaction: '#f97316', // orange
  File:        '#6b7280', // gray
  Process:     '#ec4899', // pink
}

const NODE_TYPE_SIZES: Record<string, number> = {
  Person:   3,
  Company:  5,
  Program:  6,
  Job:      2,
  Contract: 4,
  Location: 3,
  Interaction: 2,
  File:     2,
  Process:  3,
}

const EDGE_TYPE_COLORS: Record<string, string> = {
  WORKS_AT:        '#3b82f680',
  MANAGES:         '#ef444480',
  PRIMES_ON:       '#8b5cf680',
  POSTED_BY:       '#f59e0b80',
  LOCATED_IN:      '#06b6d480',
  MAPPED_TO:       '#10b98180',
  HAS_CONTRACT:    '#f9731680',
  DERIVED_FROM:    '#6b728080',
  DEPENDS_ON:      '#ec489980',
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function GraphViewer({
  data,
  endpoint = '/api/bdgraph/full-graph',
  title = 'Knowledge Graph',
  height = 600,
  visibleTypes = [],
  is3D = false,
}: GraphViewerProps) {
  const [graphData, setGraphData] = useState<GraphData | null>(data || null)
  const [loading, setLoading] = useState(!data)
  const [error, setError] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [filterTypes, setFilterTypes] = useState<Set<string>>(
    new Set(visibleTypes.length > 0 ? visibleTypes : Object.keys(NODE_TYPE_COLORS))
  )
  const [searchQuery, setSearchQuery] = useState('')

  // Fetch graph data from API
  useEffect(() => {
    if (data) {
      setGraphData(data)
      setLoading(false)
      return
    }

    let cancelled = false
    const fetchData = async () => {
      try {
        setLoading(true)
        const resp = await fetch(endpoint)
        if (!resp.ok) throw new Error(`API error: ${resp.status}`)
        const json = await resp.json()

        if (!cancelled) {
          // Normalize API response
          const normalized: GraphData = {
            nodes: json.nodes || json.entities || [],
            edges: json.edges || json.relationships || json.links || [],
          }
          setGraphData(normalized)
          setError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load graph')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchData()
    return () => { cancelled = true }
  }, [data, endpoint])

  // Convert to reagraph format
  const { graphNodes, graphEdges, nodeTypes } = useMemo(() => {
    if (!graphData) return { graphNodes: [], graphEdges: [], nodeTypes: new Set<string>() }

    const types = new Set<string>()
    const searchLower = searchQuery.toLowerCase()

    const filteredNodes = graphData.nodes.filter(n => {
      types.add(n.type)
      if (!filterTypes.has(n.type)) return false
      if (searchQuery && !n.name.toLowerCase().includes(searchLower)) return false
      return true
    })

    const nodeIdSet = new Set(filteredNodes.map(n => n.id))

    const nodes: GraphNode[] = filteredNodes.map(n => ({
      id: n.id,
      label: n.name || n.id,
      fill: NODE_TYPE_COLORS[n.type] || '#6b7280',
      size: NODE_TYPE_SIZES[n.type] || 3,
      data: { type: n.type, ...n.properties },
    }))

    const edges: GraphEdge[] = graphData.edges
      .filter(e => nodeIdSet.has(e.source) && nodeIdSet.has(e.target))
      .map((e, i) => ({
        id: `edge-${i}`,
        source: e.source,
        target: e.target,
        label: e.type,
        fill: EDGE_TYPE_COLORS[e.type] || '#9ca3af60',
      }))

    return { graphNodes: nodes, graphEdges: edges, nodeTypes: types }
  }, [graphData, filterTypes, searchQuery])

  const toggleType = useCallback((type: string) => {
    setFilterTypes(prev => {
      const next = new Set(prev)
      if (next.has(type)) {
        next.delete(type)
      } else {
        next.add(type)
      }
      return next
    })
  }, [])

  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(prev => prev === node.id ? null : node.id)
  }, [])

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900" style={{ height }}>
        <div className="text-center">
          <div className="mb-2 h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent mx-auto" />
          <p className="text-sm text-gray-500">Loading graph data...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950" style={{ height }}>
        <div className="text-center">
          <p className="text-sm font-medium text-red-600 dark:text-red-400">Failed to load graph</p>
          <p className="text-xs text-red-500 mt-1">{error}</p>
          <p className="text-xs text-gray-500 mt-2">Ensure the API is running at {endpoint}</p>
        </div>
      </div>
    )
  }

  // Empty state
  if (!graphData || graphNodes.length === 0) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900" style={{ height }}>
        <p className="text-sm text-gray-500">No graph data available</p>
      </div>
    )
  }

  // Selected node details
  const selectedEntity = selectedNode
    ? graphData.nodes.find(n => n.id === selectedNode)
    : null

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-2 dark:border-gray-700 dark:bg-gray-800">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{title}</h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">
            {graphNodes.length} nodes / {graphEdges.length} edges
          </span>
          <input
            type="text"
            placeholder="Filter nodes..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-40 rounded border border-gray-300 px-2 py-1 text-xs dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>
      </div>

      {/* Type filter chips */}
      <div className="flex flex-wrap gap-1 border-b border-gray-200 bg-gray-50 px-4 py-2 dark:border-gray-700 dark:bg-gray-900">
        {Array.from(nodeTypes).sort().map(type => (
          <button
            key={type}
            onClick={() => toggleType(type)}
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium transition-opacity ${
              filterTypes.has(type) ? 'opacity-100' : 'opacity-40'
            }`}
            style={{
              backgroundColor: `${NODE_TYPE_COLORS[type] || '#6b7280'}20`,
              color: NODE_TYPE_COLORS[type] || '#6b7280',
              border: `1px solid ${NODE_TYPE_COLORS[type] || '#6b7280'}40`,
            }}
          >
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: NODE_TYPE_COLORS[type] || '#6b7280' }}
            />
            {type}
          </button>
        ))}
      </div>

      {/* Graph canvas + detail panel */}
      <div className="flex" style={{ height }}>
        {/* Main graph */}
        <div className={`flex-1 bg-gray-950 ${selectedEntity ? 'w-2/3' : 'w-full'}`}>
          <GraphCanvas
            nodes={graphNodes}
            edges={graphEdges}
            edgeArrowPosition="end"
            labelType="auto"
            layoutType="forceDirected2d"
            theme={{
              canvas: { background: '#0a0a0a' },
              node: {
                fill: '#3b82f6',
                activeFill: '#60a5fa',
                label: { color: '#e5e7eb', fontSize: 4 },
              },
              edge: {
                fill: '#374151',
                activeFill: '#60a5fa',
                label: { color: '#9ca3af', fontSize: 3 },
              },
            }}
            onNodeClick={handleNodeClick}
          />
        </div>

        {/* Detail sidebar */}
        {selectedEntity && (
          <div className="w-1/3 border-l border-gray-700 bg-gray-900 p-4 overflow-auto">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-white">{selectedEntity.name}</h4>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-gray-400 hover:text-white text-xs"
              >
                Close
              </button>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: NODE_TYPE_COLORS[selectedEntity.type] || '#6b7280' }}
                />
                <span className="text-xs text-gray-400">{selectedEntity.type}</span>
              </div>
              {selectedEntity.properties && Object.entries(selectedEntity.properties).map(([key, val]) => (
                <div key={key} className="text-xs">
                  <span className="text-gray-500">{key}:</span>{' '}
                  <span className="text-gray-300">{String(val)}</span>
                </div>
              ))}
              {/* Connected edges */}
              <div className="mt-4">
                <p className="text-xs font-medium text-gray-400 mb-1">Relationships:</p>
                {graphData.edges
                  .filter(e => e.source === selectedEntity.id || e.target === selectedEntity.id)
                  .slice(0, 20)
                  .map((e, i) => {
                    const other = e.source === selectedEntity.id ? e.target : e.source
                    const otherNode = graphData.nodes.find(n => n.id === other)
                    const direction = e.source === selectedEntity.id ? '->' : '<-'
                    return (
                      <div key={i} className="text-xs text-gray-400 py-0.5">
                        {direction} <span className="text-blue-400">{e.type}</span> {otherNode?.name || other}
                      </div>
                    )
                  })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default GraphViewer
