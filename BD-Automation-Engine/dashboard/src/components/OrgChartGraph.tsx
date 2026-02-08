/**
 * Reagraph-based Org Chart Visualization
 *
 * Renders contacts or primes as a hierarchical graph with
 * tier-based coloring and node collapse/expand.
 */

import { useMemo, useState, useCallback } from 'react'
import { GraphCanvas, type GraphNode, type GraphEdge } from 'reagraph'

interface OrgNode {
  id: string
  label: string
  tier: string
  score?: number
  group?: string
  children?: string[]
}

interface OrgChartGraphProps {
  nodes: OrgNode[]
  title?: string
  height?: number
}

const TIER_COLORS: Record<string, string> = {
  'A - Strategic': '#9333ea',
  'B - High Value': '#2563eb',
  'C - Engaged': '#16a34a',
  'D - Developing': '#ca8a04',
  'E - New/Inactive': '#6b7280',
  'Strategic': '#9333ea',
  'Key Account': '#2563eb',
  'Established': '#16a34a',
  'Growing': '#ca8a04',
  'Emerging': '#6b7280',
}

export function OrgChartGraph({ nodes, title = 'Org Chart', height = 500 }: OrgChartGraphProps) {
  const [collapsedNodes, setCollapsedNodes] = useState<Set<string>>(new Set())

  const toggleCollapse = useCallback((nodeId: string) => {
    setCollapsedNodes(prev => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }, [])

  const { graphNodes, graphEdges } = useMemo(() => {
    // Build tier root nodes
    const tiers = [...new Set(nodes.map(n => n.tier))]
    const rootNode: GraphNode = {
      id: 'root',
      label: title,
      fill: '#1e293b',
      size: 20,
    }

    const tierNodes: GraphNode[] = tiers.map(tier => ({
      id: `tier-${tier}`,
      label: `${tier} (${nodes.filter(n => n.tier === tier).length})`,
      fill: TIER_COLORS[tier] || '#6b7280',
      size: 15,
    }))

    const rootEdges: GraphEdge[] = tiers.map(tier => ({
      id: `root-to-${tier}`,
      source: 'root',
      target: `tier-${tier}`,
    }))

    // Build leaf nodes (skip if tier is collapsed)
    const leafNodes: GraphNode[] = []
    const leafEdges: GraphEdge[] = []

    for (const node of nodes) {
      const tierId = `tier-${node.tier}`
      if (collapsedNodes.has(tierId)) continue

      leafNodes.push({
        id: node.id,
        label: node.label,
        fill: TIER_COLORS[node.tier] || '#6b7280',
        size: node.score ? Math.max(5, Math.min(12, node.score / 10)) : 8,
      })
      leafEdges.push({
        id: `${tierId}-to-${node.id}`,
        source: tierId,
        target: node.id,
      })
    }

    return {
      graphNodes: [rootNode, ...tierNodes, ...leafNodes],
      graphEdges: [...rootEdges, ...leafEdges],
    }
  }, [nodes, title, collapsedNodes])

  if (nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        No data available for graph view
      </div>
    )
  }

  return (
    <div style={{ height }} className="border border-slate-200 rounded-xl overflow-hidden bg-slate-950">
      <GraphCanvas
        nodes={graphNodes}
        edges={graphEdges}
        layoutType="hierarchicalTd"
        labelType="auto"
        draggable
        onNodeClick={(node: { id: string }) => {
          if (node.id.startsWith('tier-')) {
            toggleCollapse(node.id)
          }
        }}
      />
    </div>
  )
}
