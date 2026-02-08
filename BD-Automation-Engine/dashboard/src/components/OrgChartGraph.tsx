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
  colorMode?: 'tier' | 'bdpriority'
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

function getBDPriorityColor(score: number): string {
  if (score >= 80) return '#dc2626' // red-600 - critical
  if (score >= 60) return '#ea580c' // orange-600 - high
  if (score >= 40) return '#ca8a04' // yellow-600 - medium
  if (score >= 20) return '#16a34a' // green-600 - moderate
  return '#6b7280' // gray-500 - low
}

export function OrgChartGraph({ nodes, title = 'Org Chart', height = 500, colorMode = 'tier' }: OrgChartGraphProps) {
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

      const fill = colorMode === 'bdpriority' && node.score !== undefined
        ? getBDPriorityColor(node.score)
        : TIER_COLORS[node.tier] || '#6b7280'

      leafNodes.push({
        id: node.id,
        label: colorMode === 'bdpriority' && node.score !== undefined
          ? `${node.label} (${node.score})`
          : node.label,
        fill,
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
  }, [nodes, title, collapsedNodes, colorMode])

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
