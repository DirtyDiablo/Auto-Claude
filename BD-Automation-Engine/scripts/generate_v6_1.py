#!/usr/bin/env python3
"""Generate PTS Data Architecture Explorer V6.1 — cleaned up version."""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE, 'outputs', 'v6.1_arch_data.json'), 'r') as f:
    v6 = json.load(f)

arch_json = json.dumps(v6, separators=(',', ':'))

CSS = r"""
:root{--bg-0:#080c16;--bg-1:#0f1629;--bg-2:#161d33;--bg-3:#1c2540;--border-0:#1a2236;--border-1:#263049;--border-2:#334155;--text-0:#f1f5f9;--text-1:#cbd5e1;--text-2:#94a3b8;--text-3:#64748b;--cyan:#22d3ee;--blue:#3b82f6}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Space Grotesk',sans-serif;background:var(--bg-0);color:var(--text-0);overflow:hidden}
.mono{font-family:'JetBrains Mono',monospace}
#root{width:100vw;height:100vh}
.react-flow{background:var(--bg-0)!important}
.react-flow__minimap{background:var(--bg-1)!important;border:1px solid var(--border-0)!important;border-radius:6px!important}
.react-flow__controls{border:1px solid var(--border-0)!important;border-radius:6px!important;overflow:hidden}
.react-flow__controls-button{background:var(--bg-1)!important;border-bottom:1px solid var(--border-0)!important;fill:var(--text-3)!important}
.react-flow__controls-button:hover{background:var(--bg-2)!important;fill:var(--text-0)!important}
.react-flow__attribution{display:none!important}
/* Hide edge labels by default, show on hover */
.react-flow__edge-text{fill:transparent!important;font-size:8px!important;font-family:'JetBrains Mono',monospace!important;transition:fill .2s}
.react-flow__edge-textbg{fill:transparent!important;transition:fill .2s}
.react-flow__edge:hover .react-flow__edge-text{fill:var(--cyan)!important}
.react-flow__edge:hover .react-flow__edge-textbg{fill:var(--bg-0)!important;fill-opacity:0.95!important}
.react-flow__edge path{transition:stroke .2s,stroke-width .2s}
.react-flow__edge:hover path{stroke:rgba(34,211,238,0.5)!important;stroke-width:2.5!important}

.entity-node{border-radius:5px;overflow:hidden;font-size:11px;cursor:pointer;transition:all .2s;border:1px solid transparent;min-width:185px;background:var(--bg-2)}
.entity-node:hover{transform:translateY(-1px);border-color:rgba(34,211,238,.25);box-shadow:0 4px 24px rgba(0,0,0,.5),0 0 30px rgba(34,211,238,.08)}
.entity-header{padding:7px 10px;display:flex;justify-content:space-between;align-items:center}
.entity-header .name{color:#fff;font-weight:600;font-size:11.5px;letter-spacing:.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:130px}
.record-badge{background:rgba(0,0,0,.35);color:rgba(255,255,255,.75);padding:2px 7px;border-radius:3px;font-size:9px;font-family:'JetBrains Mono',monospace;font-weight:500}
.entity-body{padding:4px 10px 6px;display:flex;align-items:center;gap:6px;background:rgba(0,0,0,.12)}
.cat-ind{width:3px;height:14px;border-radius:1px;flex-shrink:0;opacity:.65}
.entity-cat{color:var(--text-3);font-size:9px;letter-spacing:.05em;text-transform:uppercase;flex:1}
.prop-ct{color:var(--text-3);font-size:9px;font-family:'JetBrains Mono',monospace}

.flow-node{border-radius:5px;overflow:hidden;font-size:11px;border:1px solid rgba(255,255,255,.06)}
.flow-inner{padding:10px 14px;text-align:center}
.flow-label{color:var(--text-0);font-weight:600;font-size:11px}
.flow-sub{color:var(--text-3);font-size:9px;margin-top:3px}
.integ-node{padding:12px 16px;text-align:center;font-size:11px;border:1px solid rgba(255,255,255,.06);border-radius:5px}

.dash-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;padding:24px;overflow-y:auto;align-content:start;height:100%}
.dash-card{background:var(--bg-1);border:1px solid var(--border-0);border-radius:8px;padding:20px;transition:border-color .2s}
.dash-card:hover{border-color:var(--border-1)}
.dash-card h3{font-size:10px;font-weight:600;color:var(--text-3);margin-bottom:14px;text-transform:uppercase;letter-spacing:.12em;font-family:'JetBrains Mono',monospace}
.stat-big{font-size:40px;font-weight:300;font-family:'Space Grotesk',sans-serif;color:var(--cyan);line-height:1}
.stat-label{font-size:12px;color:var(--text-2);margin-top:4px}
.stat-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border-0)}
.stat-row:last-child{border-bottom:none}
.stat-value{font-size:16px;font-weight:600;font-family:'JetBrains Mono',monospace}
.cat-bar{display:flex;align-items:center;gap:8px;padding:5px 0}
.cat-bar-fill{height:6px;border-radius:1px;transition:width .3s}
.cat-bar-label{font-size:11px;color:var(--text-1);min-width:120px}
.cat-bar-count{font-size:11px;color:var(--text-3);font-family:'JetBrains Mono',monospace;min-width:24px;text-align:right}

.detail-panel{width:380px;background:var(--bg-1);border-left:1px solid var(--border-0);overflow-y:auto;flex-shrink:0}
.detail-hdr{padding:16px 20px;border-bottom:1px solid var(--border-0);position:sticky;top:0;background:var(--bg-1);z-index:10}
.detail-sec{padding:14px 20px;border-bottom:1px solid var(--border-0)}
.detail-sec-title{font-size:9px;font-weight:600;color:var(--text-3);text-transform:uppercase;letter-spacing:.12em;margin-bottom:10px;font-family:'JetBrains Mono',monospace}
.detail-badge{display:inline-block;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:500;margin:2px;color:#fff;font-family:'JetBrains Mono',monospace}
.detail-prop-row{display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid rgba(255,255,255,.03);font-size:11px}
.detail-prop-name{color:var(--cyan);font-weight:500}
.detail-prop-type{color:var(--text-3);font-family:'JetBrains Mono',monospace;font-size:10px}

.cat-sidebar{width:220px;background:var(--bg-1);border-right:1px solid var(--border-0);overflow-y:auto;flex-shrink:0;padding:12px 0}
.cat-sidebar-hdr{padding:8px 16px 12px;border-bottom:1px solid var(--border-0);margin-bottom:8px}
.cat-sidebar-title{font-size:9px;font-weight:600;color:var(--text-3);text-transform:uppercase;letter-spacing:.12em;font-family:'JetBrains Mono',monospace}
.cat-toggle{display:flex;align-items:center;gap:8px;padding:6px 16px;cursor:pointer;transition:background .15s;user-select:none}
.cat-toggle:hover{background:rgba(255,255,255,.03)}
.cat-toggle-dot{width:8px;height:8px;border-radius:2px;flex-shrink:0;transition:opacity .2s}
.cat-toggle-label{font-size:12px;color:var(--text-1);flex:1}
.cat-toggle-count{font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace}
.cat-toggle.off .cat-toggle-dot{opacity:.15}
.cat-toggle.off .cat-toggle-label{opacity:.35}
.cat-toggle.off .cat-toggle-count{opacity:.25}

.search-input{background:var(--bg-0);border:1px solid var(--border-0);color:var(--text-0);padding:7px 12px;border-radius:4px;font-size:12px;width:100%;outline:none;font-family:'Space Grotesk',sans-serif;transition:border-color .2s}
.search-input:focus{border-color:var(--cyan)}
.search-input::placeholder{color:var(--text-3)}
.toolbar-btn{padding:3px 10px;border-radius:3px;font-size:10px;cursor:pointer;border:1px solid var(--border-0);background:var(--bg-0);color:var(--text-3);font-family:'JetBrains Mono',monospace;transition:all .15s}
.toolbar-btn:hover{border-color:var(--border-1);color:var(--text-2)}
.toolbar-btn.active{border-color:var(--cyan);color:var(--cyan);background:rgba(34,211,238,.06)}

.top-bar{height:48px;background:var(--bg-1);border-bottom:1px solid var(--border-0);display:flex;align-items:center;padding:0 20px;gap:16px;flex-shrink:0}
.top-bar-title{font-size:13px;font-weight:600;letter-spacing:.04em}
.top-bar-ver{font-size:10px;color:var(--cyan);font-family:'JetBrains Mono',monospace;background:rgba(34,211,238,.06);padding:2px 8px;border-radius:3px;border:1px solid rgba(34,211,238,.12)}
.tab-btn{padding:6px 14px;font-size:11px;cursor:pointer;border:none;background:0 0;color:var(--text-3);font-family:'Space Grotesk',sans-serif;font-weight:500;letter-spacing:.02em;border-bottom:2px solid transparent;transition:all .2s;height:48px;display:flex;align-items:center}
.tab-btn:hover{color:var(--text-2)}
.tab-btn.active{color:var(--cyan);border-bottom-color:var(--cyan)}

.rel-item{display:flex;align-items:center;gap:6px;padding:3px 0;font-size:11px}
.rel-arrow{color:var(--text-3);font-size:10px}
.rel-label{color:var(--cyan);font-family:'JetBrains Mono',monospace;font-size:10px}
.rel-target{color:var(--text-1)}

.loading{display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-3);font-size:13px;gap:10px}
.loading::before{content:'';width:16px;height:16px;border:2px solid var(--border-0);border-top-color:var(--cyan);border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border-0);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--border-1)}

/* Category region backgrounds for grouped layout */
.category-region{position:absolute;border-radius:8px;border:1px solid;opacity:.6;pointer-events:none;z-index:-1}
.category-region-label{position:absolute;top:6px;left:10px;font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.1em;font-family:'JetBrains Mono',monospace;opacity:.5}
"""

JS_APP = r"""
import { useState, useCallback, useMemo, useEffect, useRef, memo, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import { ReactFlow, ReactFlowProvider, useReactFlow, useNodesState, useEdgesState, Background, Controls, MiniMap, Handle, Position, MarkerType } from '@xyflow/react';
import ELK from 'elkjs/lib/elk.bundled.js';
import htm from 'htm';
const html = htm.bind(createElement);
const elk = new ELK();
const CATEGORIES = ARCH.categories;

// Category colors for easy lookup
const CAT_COLORS = {};
Object.entries(CATEGORIES).forEach(([k, v]) => { CAT_COLORS[k] = v.color; });

// === Custom Nodes ===
function EntityNodeComponent({ data }) {
  const c = data.color || '#64748b';
  return html`
    <div className="entity-node" style=${{ borderLeft: '3px solid ' + c }}>
      <${Handle} type="target" position=${Position.Top} style=${{ background: c, width: 6, height: 6, border: 'none' }} />
      <div className="entity-header" style=${{ background: c + '15' }}>
        <span className="name">${data.label}</span>
        ${data.records && data.records !== '\u2014' && html`<span className="record-badge">${data.records}</span>`}
      </div>
      <div className="entity-body">
        <div className="cat-ind" style=${{ background: c }}></div>
        <span className="entity-cat">${data.category}</span>
        <span className="prop-ct">${data.propCount}p</span>
      </div>
      <${Handle} type="source" position=${Position.Bottom} style=${{ background: c, width: 6, height: 6, border: 'none' }} />
    </div>`;
}
const EntityNode = memo(EntityNodeComponent);

function FlowNodeComponent({ data }) {
  const c = data.color || '#3b82f6';
  return html`
    <div className="flow-node" style=${{ background: c + '12', borderColor: c + '25' }}>
      <${Handle} type="target" position=${Position.Left} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
      <div className="flow-inner"><div className="flow-label">${data.label}</div>${data.sublabel && html`<div className="flow-sub">${data.sublabel}</div>`}</div>
      <${Handle} type="source" position=${Position.Right} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
    </div>`;
}
const FlowNode = memo(FlowNodeComponent);

function IntegNodeComponent({ data }) {
  const c = data.color || '#8b5cf6';
  return html`
    <div className="integ-node" style=${{ background: c + '10', borderColor: c + '20' }}>
      <${Handle} type="target" position=${Position.Left} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
      <div style=${{ fontWeight: 600, color: 'var(--text-0)', fontSize: '12px' }}>${data.label}</div>
      ${data.sublabel && html`<div style=${{ color: 'var(--text-3)', fontSize: '10px', marginTop: '3px' }}>${data.sublabel}</div>`}
      <${Handle} type="source" position=${Position.Right} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
    </div>`;
}
const IntegNode = memo(IntegNodeComponent);

const nodeTypes = { entityNode: EntityNode, flowNode: FlowNode, integNode: IntegNode };

// === ELK Layout with category grouping ===
async function layoutNodes(nodes, edges, dir = 'DOWN', grouped = false) {
  if (grouped && nodes.length > 0 && nodes[0].type === 'entityNode') {
    // Group nodes by category into ELK sub-graphs
    const catGroups = {};
    nodes.forEach(n => {
      const cat = n.data.category || 'Other';
      if (!catGroups[cat]) catGroups[cat] = [];
      catGroups[cat].push(n);
    });

    const graph = {
      id: 'root',
      layoutOptions: {
        'elk.algorithm': 'layered',
        'elk.direction': dir,
        'elk.spacing.nodeNode': '40',
        'elk.layered.spacing.nodeNodeBetweenLayers': '65',
        'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
        'elk.padding': '[top=50,left=50,bottom=50,right=50]',
        'elk.separateConnectedComponents': 'false',
      },
      children: Object.entries(catGroups).map(([cat, catNodes]) => ({
        id: 'group_' + cat.replace(/[^a-zA-Z0-9]/g, '_'),
        layoutOptions: {
          'elk.algorithm': 'layered',
          'elk.direction': 'RIGHT',
          'elk.spacing.nodeNode': '30',
          'elk.layered.spacing.nodeNodeBetweenLayers': '50',
          'elk.padding': '[top=35,left=20,bottom=20,right=20]',
        },
        children: catNodes.map(n => ({
          id: n.id,
          width: 190,
          height: 54,
        })),
        edges: edges.filter(e => {
          const srcIn = catNodes.some(n => n.id === e.source);
          const tgtIn = catNodes.some(n => n.id === e.target);
          return srcIn && tgtIn;
        }).map(e => ({ id: e.id + '_inner', sources: [e.source], targets: [e.target] })),
      })),
      edges: edges.filter(e => {
        // Cross-group edges
        const srcCat = nodes.find(n => n.id === e.source)?.data.category;
        const tgtCat = nodes.find(n => n.id === e.target)?.data.category;
        return srcCat !== tgtCat;
      }).map(e => ({ id: e.id, sources: [e.source], targets: [e.target] })),
    };

    const layouted = await elk.layout(graph);

    // Extract positions from grouped layout
    const positions = {};
    const groupBounds = {};
    if (layouted.children) {
      layouted.children.forEach(group => {
        const gx = group.x || 0;
        const gy = group.y || 0;
        const catName = Object.entries(catGroups).find(([c]) =>
          'group_' + c.replace(/[^a-zA-Z0-9]/g, '_') === group.id
        )?.[0] || '';
        groupBounds[catName] = { x: gx, y: gy, w: group.width || 400, h: group.height || 200 };
        if (group.children) {
          group.children.forEach(child => {
            positions[child.id] = { x: gx + (child.x || 0), y: gy + (child.y || 0) };
          });
        }
      });
    }

    const result = nodes.map(n => ({
      ...n,
      position: positions[n.id] || { x: 0, y: 0 },
    }));
    return { nodes: result, groupBounds };
  }

  // Non-grouped fallback
  const graph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': dir,
      'elk.spacing.nodeNode': '55',
      'elk.layered.spacing.nodeNodeBetweenLayers': '75',
      'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
      'elk.padding': '[top=40,left=40,bottom=40,right=40]',
    },
    children: nodes.map(n => ({ id: n.id, width: n.type === 'entityNode' ? 190 : 160, height: n.type === 'entityNode' ? 54 : 50 })),
    edges: edges.map(e => ({ id: e.id, sources: [e.source], targets: [e.target] })),
  };
  const layouted = await elk.layout(graph);
  return {
    nodes: nodes.map(n => {
      const ln = layouted.children.find(c => c.id === n.id);
      return { ...n, position: { x: ln?.x || 0, y: ln?.y || 0 } };
    }),
    groupBounds: null,
  };
}

// === Entity Graph View ===
function EntityGraphView({ onSelectNode, activeCategories, searchQuery, useGrouped }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [groupBounds, setGroupBounds] = useState(null);
  const [loading, setLoading] = useState(true);
  const { fitView } = useReactFlow();

  const filtered = useMemo(() => {
    let fn = ARCH.graph.nodes.filter(n => activeCategories.has(n.data.category));
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      fn = fn.filter(n =>
        n.data.label.toLowerCase().includes(q) ||
        n.data.category.toLowerCase().includes(q) ||
        (n.data.description && n.data.description.toLowerCase().includes(q))
      );
    }
    const ids = new Set(fn.map(n => n.id));
    return { nodes: fn, edges: ARCH.graph.edges.filter(e => ids.has(e.source) && ids.has(e.target)) };
  }, [activeCategories, searchQuery]);

  useEffect(() => {
    setLoading(true);
    const se = filtered.edges.map(e => ({
      ...e, type: 'smoothstep',
      style: { stroke: 'rgba(148,163,184,0.15)', strokeWidth: 1.5 },
      markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(148,163,184,0.2)', width: 10, height: 10 },
      label: e.label || (e.data && e.data.label) || '',
      labelStyle: { fill: 'transparent', fontSize: 8, fontFamily: 'JetBrains Mono' },
      labelBgStyle: { fill: 'transparent' },
      labelBgPadding: [4, 2],
    }));
    layoutNodes(filtered.nodes, se, 'DOWN', useGrouped).then(result => {
      setNodes(result.nodes);
      setEdges(se);
      setGroupBounds(result.groupBounds);
      setLoading(false);
      setTimeout(() => fitView({ padding: 0.08, duration: 500 }), 150);
    });
  }, [filtered, useGrouped]);

  const onNodeClick = useCallback((_, node) => onSelectNode(node.data), [onSelectNode]);
  if (loading) return html`<div className="loading">Computing layout\u2026</div>`;
  return html`
    <${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNodesChange} onEdgesChange=${onEdgesChange}
      onNodeClick=${onNodeClick} nodeTypes=${nodeTypes} fitView fitViewOptions=${{ padding: 0.08 }}
      minZoom=${0.06} maxZoom=${2.5} proOptions=${{ hideAttribution: true }}>
      <${Background} gap=${24} size=${1} color=${'#0f1629'} />
      <${Controls} />
      <${MiniMap} nodeColor=${n => n.data?.color || '#64748b'} maskColor=${'rgba(8,12,22,0.85)'} style=${{ borderRadius: 6 }} />
    </${ReactFlow}>`;
}

// === Data Flow View ===
function DataFlowView() {
  const [nodes, setNodes, onNC] = useNodesState([]);
  const [edges, setEdges, onEC] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const { fitView } = useReactFlow();
  useEffect(() => {
    const fn = ARCH.flow.nodes.map(n => ({ ...n, type: 'flowNode' }));
    const fe = ARCH.flow.edges.map(e => ({
      ...e, type: 'smoothstep', animated: true,
      style: { stroke: 'rgba(59,130,246,0.35)', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(59,130,246,0.45)', width: 14, height: 14 }
    }));
    layoutNodes(fn, fe, 'RIGHT').then(result => {
      setNodes(result.nodes); setEdges(fe); setLoading(false);
      setTimeout(() => fitView({ padding: 0.15, duration: 400 }), 100);
    });
  }, []);
  if (loading) return html`<div className="loading">Computing layout\u2026</div>`;
  return html`
    <${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNC} onEdgesChange=${onEC}
      nodeTypes=${nodeTypes} fitView fitViewOptions=${{ padding: 0.15 }}
      minZoom=${0.2} maxZoom=${2} proOptions=${{ hideAttribution: true }}>
      <${Background} gap=${24} size=${1} color=${'#0f1629'} />
      <${Controls} />
    </${ReactFlow}>`;
}

// === Integration View ===
function IntegrationView() {
  const [nodes, setNodes, onNC] = useNodesState([]);
  const [edges, setEdges, onEC] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const { fitView } = useReactFlow();
  useEffect(() => {
    const fn = ARCH.integration.nodes.map(n => ({ ...n, type: 'integNode' }));
    const fe = ARCH.integration.edges.map(e => ({
      ...e, type: 'smoothstep',
      style: { stroke: 'rgba(139,92,246,0.3)', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(139,92,246,0.35)', width: 14, height: 14 }
    }));
    layoutNodes(fn, fe, 'RIGHT').then(result => {
      setNodes(result.nodes); setEdges(fe); setLoading(false);
      setTimeout(() => fitView({ padding: 0.2, duration: 400 }), 100);
    });
  }, []);
  if (loading) return html`<div className="loading">Computing layout\u2026</div>`;
  return html`
    <${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNC} onEdgesChange=${onEC}
      nodeTypes=${nodeTypes} fitView fitViewOptions=${{ padding: 0.2 }}
      minZoom=${0.3} maxZoom=${2} proOptions=${{ hideAttribution: true }}>
      <${Background} gap=${24} size=${1} color=${'#0f1629'} />
      <${Controls} />
    </${ReactFlow}>`;
}

// === Dashboard View ===
function DashboardView() {
  const d = ARCH.dashboard;
  const cats = Object.entries(d.categories).sort((a, b) => b[1].count - a[1].count);
  const mx = Math.max(...cats.map(c => c[1].count));

  // Count entities with known record counts
  const withRecords = ARCH.graph.nodes.filter(n => n.data.records && n.data.records !== '\u2014').length;
  const totalRecordStr = ARCH.graph.nodes.reduce((acc, n) => {
    const r = n.data.records;
    if (!r || r === '\u2014') return acc;
    const num = parseInt(r.replace(/[^0-9]/g, ''));
    return isNaN(num) ? acc : acc + num;
  }, 0);

  return html`<div className="dash-grid">
    <div className="dash-card"><h3>System Overview</h3>
      <div style=${{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div><div className="stat-big">${d.totalEntities}</div><div className="stat-label">Entities</div></div>
        <div><div className="stat-big">${d.totalProperties}</div><div className="stat-label">Properties</div></div>
        <div><div className="stat-big">${d.totalRelationships}</div><div className="stat-label">Relationships</div></div>
        <div><div className="stat-big">${totalRecordStr > 0 ? (totalRecordStr > 1000000 ? (totalRecordStr/1000000).toFixed(1)+'M' : totalRecordStr > 1000 ? (totalRecordStr/1000).toFixed(0)+'K' : totalRecordStr) : d.multiProjectEntities}</div><div className="stat-label">${totalRecordStr > 0 ? 'Total Records' : 'Multi-Project'}</div></div>
      </div>
    </div>
    <div className="dash-card"><h3>Domains</h3>
      ${cats.map(([n, i]) => html`<div className="cat-bar" key=${n}>
        <span className="cat-bar-label">${n}</span>
        <div style=${{ flex: 1, background: 'rgba(255,255,255,.03)', borderRadius: '2px', overflow: 'hidden' }}>
          <div className="cat-bar-fill" style=${{ width: (i.count / mx * 100) + '%', background: i.color }}></div>
        </div>
        <span className="cat-bar-count">${i.count}</span>
      </div>`)}
    </div>
    <div className="dash-card"><h3>Storage</h3>
      <div className="stat-row"><span className="stat-label">Qdrant Collections</span><span className="stat-value" style=${{ color: '#22d3ee' }}>${d.qdrantCollections}</span></div>
      <div className="stat-row"><span className="stat-label">SQLite Databases</span><span className="stat-value" style=${{ color: '#f59e0b' }}>${d.sqliteDatabases}</span></div>
      <div className="stat-row"><span className="stat-label">Neo4j Node Types</span><span className="stat-value" style=${{ color: '#10b981' }}>${d.neo4jNodeTypes}</span></div>
      <div className="stat-row"><span className="stat-label">Neo4j Rel Types</span><span className="stat-value" style=${{ color: '#10b981' }}>${d.neo4jRelTypes}</span></div>
    </div>
    <div className="dash-card"><h3>Infrastructure</h3>
      <div className="stat-row"><span className="stat-label">API Endpoints</span><span className="stat-value" style=${{ color: '#3b82f6' }}>${d.apiEndpoints}</span></div>
      <div className="stat-row"><span className="stat-label">Data Flows</span><span className="stat-value" style=${{ color: '#8b5cf6' }}>${d.dataFlows}</span></div>
      <div className="stat-row"><span className="stat-label">Engines</span><span className="stat-value" style=${{ color: '#f43f5e' }}>${d.engines}</span></div>
      <div className="stat-row"><span className="stat-label">Entities w/ Data</span><span className="stat-value" style=${{ color: '#22d3ee' }}>${withRecords}/${d.totalEntities}</span></div>
    </div>
    <div className="dash-card" style=${{ gridColumn: 'span 2' }}><h3>Density Metrics</h3>
      <div style=${{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '16px' }}>
        <div style=${{ textAlign: 'center' }}><div className="stat-big" style=${{ fontSize: '28px' }}>${(d.totalRelationships / d.totalEntities).toFixed(1)}</div><div className="stat-label">Rels / Entity</div></div>
        <div style=${{ textAlign: 'center' }}><div className="stat-big" style=${{ fontSize: '28px' }}>${(d.totalProperties / d.totalEntities).toFixed(0)}</div><div className="stat-label">Props / Entity</div></div>
        <div style=${{ textAlign: 'center' }}><div className="stat-big" style=${{ fontSize: '28px' }}>${Object.keys(d.categories).length}</div><div className="stat-label">Domains</div></div>
        <div style=${{ textAlign: 'center' }}><div className="stat-big" style=${{ fontSize: '28px' }}>${d.qdrantCollections + d.sqliteDatabases + d.neo4jNodeTypes}</div><div className="stat-label">Stores</div></div>
      </div>
    </div>
  </div>`;
}

// === Detail Panel ===
function DetailPanel({ data, onClose }) {
  const nodeId = ARCH.graph.nodes.find(n => n.data.label === data.label)?.id || data.label;
  const outE = ARCH.graph.edges.filter(e => e.source === nodeId);
  const inE = ARCH.graph.edges.filter(e => e.target === nodeId);
  return html`<div className="detail-panel">
    <div className="detail-hdr">
      <div style=${{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div>
          <div style=${{ fontSize: '16px', fontWeight: 600, marginBottom: '4px' }}>${data.label}</div>
          <div style=${{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <div style=${{ width: 8, height: 8, borderRadius: 2, background: data.color }}></div>
            <span style=${{ fontSize: '11px', color: 'var(--text-3)' }}>${data.category}</span>
          </div>
        </div>
        <button onClick=${onClose} style=${{ background: 'none', border: 'none', color: 'var(--text-3)', cursor: 'pointer', fontSize: '18px', lineHeight: 1 }}>${'\u00D7'}</button>
      </div>
      ${data.description && html`<p style=${{ fontSize: '11px', color: 'var(--text-2)', marginTop: '10px', lineHeight: 1.5 }}>${data.description}</p>`}
    </div>
    <div className="detail-sec"><div className="detail-sec-title">Overview</div>
      <div style=${{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Records</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.records || '\u2014'}</div></div>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Properties</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.propCount}</div></div>
      </div>
    </div>
    ${data.sources && data.sources.length > 0 && html`
      <div className="detail-sec"><div className="detail-sec-title">Sources</div>
        <div style=${{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
          ${data.sources.map(s => html`<span className="detail-badge" style=${{ background: 'rgba(59,130,246,.12)', color: '#93c5fd' }} key=${s}>${s}</span>`)}
        </div>
      </div>`}
    ${data.storage && data.storage.length > 0 && html`
      <div className="detail-sec"><div className="detail-sec-title">Storage</div>
        <div style=${{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
          ${data.storage.map(s => html`<div className="mono" style=${{ fontSize: '10px', color: 'var(--text-2)' }} key=${s}>${s}</div>`)}
        </div>
      </div>`}
    ${(outE.length > 0 || inE.length > 0) && html`
      <div className="detail-sec"><div className="detail-sec-title">Relationships (${outE.length + inE.length})</div>
        ${outE.length > 0 && html`<div style=${{ marginBottom: '8px' }}>
          <div style=${{ fontSize: '9px', color: 'var(--text-3)', marginBottom: '4px', fontFamily: 'JetBrains Mono', letterSpacing: '.1em' }}>OUTGOING (${outE.length})</div>
          ${outE.map(e => html`<div className="rel-item" key=${e.id}><span className="rel-arrow">${'\u2192'}</span><span className="rel-label">${e.label || (e.data && e.data.label) || ''}</span><span className="rel-target">${e.target}</span></div>`)}
        </div>`}
        ${inE.length > 0 && html`<div>
          <div style=${{ fontSize: '9px', color: 'var(--text-3)', marginBottom: '4px', fontFamily: 'JetBrains Mono', letterSpacing: '.1em' }}>INCOMING (${inE.length})</div>
          ${inE.map(e => html`<div className="rel-item" key=${e.id}><span className="rel-arrow">${'\u2190'}</span><span className="rel-label">${e.label || (e.data && e.data.label) || ''}</span><span className="rel-target">${e.source}</span></div>`)}
        </div>`}
      </div>`}
    ${data.properties && data.properties.length > 0 && html`
      <div className="detail-sec"><div className="detail-sec-title">Schema (${data.properties.length})</div>
        <div style=${{ maxHeight: '300px', overflowY: 'auto' }}>
          ${data.properties.map(p => html`<div className="detail-prop-row" key=${p.name}><span className="detail-prop-name">${p.name}</span><span className="detail-prop-type">${p.type}</span></div>`)}
        </div>
      </div>`}
  </div>`;
}

// === Category Sidebar ===
function CategorySidebar({ activeCategories, onToggle, searchQuery, onSearchChange, useGrouped, onToggleGrouped }) {
  const allOn = activeCategories.size === Object.keys(CATEGORIES).length;
  return html`<div className="cat-sidebar">
    <div className="cat-sidebar-hdr">
      <div className="cat-sidebar-title">Filter</div>
      <div style=${{ marginTop: '8px' }}><input className="search-input" placeholder=${'Search entities\u2026'} value=${searchQuery} onInput=${e => onSearchChange(e.target.value)} /></div>
      <div style=${{ display: 'flex', gap: '6px', marginTop: '8px' }}>
        <button className="toolbar-btn" onClick=${() => onToggle('__ALL__')}>${allOn ? 'Hide All' : 'Show All'}</button>
        <button className=${'toolbar-btn' + (useGrouped ? ' active' : '')} onClick=${onToggleGrouped}>Grouped</button>
      </div>
    </div>
    ${Object.entries(CATEGORIES).map(([n, i]) => html`
      <div className=${'cat-toggle' + (activeCategories.has(n) ? '' : ' off')} key=${n} onClick=${() => onToggle(n)}>
        <div className="cat-toggle-dot" style=${{ background: i.color }}></div>
        <span className="cat-toggle-label">${n}</span>
        <span className="cat-toggle-count">${i.count}</span>
      </div>`)}
  </div>`;
}

// === Main App ===
function App() {
  const [tab, setTab] = useState('graph');
  const [sel, setSel] = useState(null);
  const [sq, setSq] = useState('');
  const [ac, setAc] = useState(new Set(Object.keys(CATEGORIES)));
  const [grouped, setGrouped] = useState(true);

  const toggleCat = useCallback(cat => {
    setAc(prev => {
      if (cat === '__ALL__') return prev.size === Object.keys(CATEGORIES).length ? new Set() : new Set(Object.keys(CATEGORIES));
      const n = new Set(prev);
      if (n.has(cat)) n.delete(cat); else n.add(cat);
      return n;
    });
  }, []);

  const tabs = [
    { id: 'graph', label: 'Entity Graph' },
    { id: 'flow', label: 'Data Flow' },
    { id: 'integration', label: 'Integrations' },
    { id: 'dashboard', label: 'Dashboard' }
  ];

  return html`<div style=${{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
    <div className="top-bar">
      <span className="top-bar-title">PTS Data Architecture</span>
      <span className="top-bar-ver">V6.1</span>
      <div style=${{ width: 1, height: 20, background: 'var(--border-0)' }}></div>
      <div style=${{ display: 'flex', gap: 0 }}>
        ${tabs.map(t => html`<button key=${t.id} className=${'tab-btn' + (tab === t.id ? ' active' : '')} onClick=${() => { setTab(t.id); setSel(null); }}>${t.label}</button>`)}
      </div>
      <div style=${{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span className="mono" style=${{ fontSize: '10px', color: 'var(--text-3)' }}>${ARCH.dashboard.totalEntities} entities ${'\u00B7'} ${ARCH.dashboard.totalRelationships} rels ${'\u00B7'} ${ARCH.dashboard.totalProperties} props</span>
      </div>
    </div>
    <div style=${{ display: 'flex', flex: 1, overflow: 'hidden' }}>
      ${tab === 'graph' && html`<${CategorySidebar} activeCategories=${ac} onToggle=${toggleCat} searchQuery=${sq} onSearchChange=${setSq} useGrouped=${grouped} onToggleGrouped=${() => setGrouped(g => !g)} />`}
      <div style=${{ flex: 1, position: 'relative' }}>
        ${tab === 'graph' && html`<${ReactFlowProvider}><${EntityGraphView} onSelectNode=${setSel} activeCategories=${ac} searchQuery=${sq} useGrouped=${grouped} /></${ReactFlowProvider}>`}
        ${tab === 'flow' && html`<${ReactFlowProvider}><${DataFlowView} /></${ReactFlowProvider}>`}
        ${tab === 'integration' && html`<${ReactFlowProvider}><${IntegrationView} /></${ReactFlowProvider}>`}
        ${tab === 'dashboard' && html`<${DashboardView} />`}
      </div>
      ${sel && tab === 'graph' && html`<${DetailPanel} data=${sel} onClose=${() => setSel(null)} />`}
    </div>
  </div>`;
}

createRoot(document.getElementById('root')).render(html`<${App} />`);
"""

# Assemble
output = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PTS Data Architecture Explorer V6.1</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@xyflow/react@12.3.2/dist/style.css">
<script src="https://cdn.tailwindcss.com"></script>
<script type="importmap">
{{
  "imports": {{
    "react": "https://esm.sh/react@18.2.0",
    "react/jsx-runtime": "https://esm.sh/react@18.2.0/jsx-runtime",
    "react-dom": "https://esm.sh/react-dom@18.2.0?external=react",
    "react-dom/client": "https://esm.sh/react-dom@18.2.0/client?external=react",
    "@xyflow/react": "https://esm.sh/@xyflow/react@12.3.2?external=react,react-dom",
    "elkjs/lib/elk.bundled.js": "https://esm.sh/elkjs@0.9.3/lib/elk.bundled.js",
    "htm": "https://esm.sh/htm@3.1.1"
  }}
}}
</script>
<style>{CSS}</style>
</head>
<body>
<div id="root"></div>
<script type="module">
const ARCH = {arch_json};
{JS_APP}
</script>
</body>
</html>"""

outpath = os.path.join(BASE, 'PTS_DATA_ARCHITECTURE_EXPLORER_V6.1.html')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"V6.1 written: {len(output):,} chars ({len(output)//1024}KB)")
print(f"Output: {outpath}")
