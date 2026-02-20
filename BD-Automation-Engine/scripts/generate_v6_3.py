#!/usr/bin/env python3
"""Generate PTS Data Architecture Explorer V6.3 — search highlight, export, improved detail panel."""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE, 'outputs', 'v6.1_arch_data.json'), 'r') as f:
    v6 = json.load(f)

# Pre-compute relationship counts per node
rel_counts = {}
for e in v6['graph']['edges']:
    rel_counts[e['source']] = rel_counts.get(e['source'], 0) + 1
    rel_counts[e['target']] = rel_counts.get(e['target'], 0) + 1

for node in v6['graph']['nodes']:
    node['data']['relCount'] = rel_counts.get(node['id'], 0)

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
.react-flow__edge-text{fill:transparent!important;font-size:8px!important;font-family:'JetBrains Mono',monospace!important;transition:fill .2s}
.react-flow__edge-textbg{fill:transparent!important;transition:fill .2s}
.react-flow__edge:hover .react-flow__edge-text{fill:var(--cyan)!important}
.react-flow__edge:hover .react-flow__edge-textbg{fill:var(--bg-0)!important;fill-opacity:0.95!important}
.react-flow__edge path{transition:stroke .2s,stroke-width .2s}
.react-flow__edge:hover path{stroke:rgba(34,211,238,0.55)!important;stroke-width:2.5!important}

/* Focus mode: dim non-connected nodes/edges */
.react-flow.focus-active .react-flow__node.dimmed{opacity:.12!important;filter:saturate(0.2)!important;transition:opacity .3s,filter .3s}
.react-flow.focus-active .react-flow__edge.dimmed path{stroke:rgba(148,163,184,0.04)!important;transition:stroke .3s}
.react-flow.focus-active .react-flow__edge.dimmed .react-flow__edge-text{fill:transparent!important}
.react-flow.focus-active .react-flow__node.highlighted{opacity:1!important;filter:none!important;transition:opacity .3s}
.react-flow.focus-active .react-flow__edge.highlighted path{stroke:rgba(34,211,238,0.5)!important;stroke-width:2!important;transition:stroke .3s}
.react-flow.focus-active .react-flow__edge.highlighted .react-flow__edge-text{fill:var(--cyan)!important}
.react-flow.focus-active .react-flow__edge.highlighted .react-flow__edge-textbg{fill:var(--bg-0)!important;fill-opacity:0.9!important}

/* Search highlight: glow matching nodes */
.react-flow.search-active .react-flow__node.search-match{box-shadow:0 0 0 2px var(--cyan),0 0 20px rgba(34,211,238,.25)!important;border-radius:5px}
.react-flow.search-active .react-flow__node:not(.search-match){opacity:.2!important;filter:saturate(0.15)!important;transition:opacity .3s,filter .3s}
.react-flow.search-active .react-flow__edge path{stroke:rgba(148,163,184,0.05)!important}
.react-flow.search-active .react-flow__node.search-match .react-flow__edge path{stroke:rgba(34,211,238,0.3)!important}

.entity-node{border-radius:5px;overflow:hidden;font-size:11px;cursor:pointer;transition:all .25s;border:1px solid transparent;min-width:190px;background:var(--bg-2)}
.entity-node:hover{transform:translateY(-1px);border-color:rgba(34,211,238,.25);box-shadow:0 4px 24px rgba(0,0,0,.5),0 0 30px rgba(34,211,238,.08)}
.entity-node.selected{border-color:var(--cyan)!important;box-shadow:0 0 0 1px var(--cyan),0 4px 30px rgba(34,211,238,.15)!important}
.entity-header{padding:7px 10px;display:flex;justify-content:space-between;align-items:center;gap:6px}
.entity-header .name{color:#fff;font-weight:600;font-size:11.5px;letter-spacing:.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1}
.record-badge{background:rgba(0,0,0,.35);color:rgba(255,255,255,.75);padding:2px 7px;border-radius:3px;font-size:9px;font-family:'JetBrains Mono',monospace;font-weight:500;flex-shrink:0}
.entity-body{padding:4px 10px 6px;display:flex;align-items:center;gap:6px;background:rgba(0,0,0,.12)}
.cat-ind{width:3px;height:14px;border-radius:1px;flex-shrink:0;opacity:.65}
.entity-cat{color:var(--text-3);font-size:9px;letter-spacing:.05em;text-transform:uppercase;flex:1}
.prop-ct{color:var(--text-3);font-size:9px;font-family:'JetBrains Mono',monospace}
.rel-ct{color:var(--text-3);font-size:8px;font-family:'JetBrains Mono',monospace;background:rgba(34,211,238,.08);padding:1px 4px;border-radius:2px;margin-left:2px}

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

.detail-panel{width:400px;background:var(--bg-1);border-left:1px solid var(--border-0);overflow-y:auto;flex-shrink:0}
.detail-hdr{padding:16px 20px;border-bottom:1px solid var(--border-0);position:sticky;top:0;background:var(--bg-1);z-index:10}
.detail-sec{padding:14px 20px;border-bottom:1px solid var(--border-0)}
.detail-sec-title{font-size:9px;font-weight:600;color:var(--text-3);text-transform:uppercase;letter-spacing:.12em;margin-bottom:10px;font-family:'JetBrains Mono',monospace}
.detail-badge{display:inline-block;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:500;margin:2px;color:#fff;font-family:'JetBrains Mono',monospace}
.detail-prop-row{display:grid;grid-template-columns:1fr auto 1fr;gap:8px;align-items:center;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.03);font-size:11px}
.detail-prop-name{color:var(--cyan);font-weight:500}
.detail-prop-type{color:var(--text-3);font-family:'JetBrains Mono',monospace;font-size:10px;text-align:center}
.detail-prop-note{color:var(--text-3);font-size:9px;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

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

/* Relationship group toggle */
.rel-group{margin-bottom:10px}
.rel-group-header{display:flex;align-items:center;gap:6px;cursor:pointer;padding:4px 0;user-select:none}
.rel-group-header:hover{color:var(--text-0)}
.rel-group-chevron{font-size:10px;color:var(--text-3);transition:transform .2s;display:inline-block;width:12px}
.rel-group-chevron.open{transform:rotate(90deg)}
.rel-group-name{font-size:10px;color:var(--cyan);font-family:'JetBrains Mono',monospace;font-weight:500}
.rel-group-count{font-size:9px;color:var(--text-3);font-family:'JetBrains Mono',monospace}

.loading{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:var(--text-3);font-size:13px;gap:12px}
.loading::before{content:'';width:20px;height:20px;border:2px solid var(--border-0);border-top-color:var(--cyan);border-radius:50%;animation:spin .8s linear infinite}
.loading-sub{font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace}
@keyframes spin{to{transform:rotate(360deg)}}
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border-0);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--border-1)}

/* Keyboard shortcut hint */
.kb-hint{position:fixed;bottom:12px;left:50%;transform:translateX(-50%);background:var(--bg-2);border:1px solid var(--border-0);border-radius:6px;padding:6px 14px;font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace;z-index:100;display:flex;gap:12px;opacity:.6;transition:opacity .3s}
.kb-hint:hover{opacity:1}
.kb-key{background:var(--bg-0);padding:1px 6px;border-radius:3px;color:var(--text-2);border:1px solid var(--border-1)}

/* Tooltip */
.node-tooltip{position:absolute;background:var(--bg-2);border:1px solid var(--border-1);border-radius:5px;padding:8px 12px;font-size:10px;color:var(--text-1);max-width:260px;line-height:1.5;pointer-events:none;z-index:1000;box-shadow:0 8px 32px rgba(0,0,0,.6);white-space:normal}
.node-tooltip::before{content:'';position:absolute;top:-5px;left:20px;width:8px;height:8px;background:var(--bg-2);border-left:1px solid var(--border-1);border-top:1px solid var(--border-1);transform:rotate(45deg)}

/* Search match count */
.search-count{font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace;padding:2px 8px;background:rgba(34,211,238,.06);border-radius:3px}
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
const CAT_COLORS = {};
Object.entries(CATEGORIES).forEach(([k, v]) => { CAT_COLORS[k] = v.color; });

// Pre-build adjacency for focus mode
const ADJ = {};
ARCH.graph.edges.forEach(e => {
  if (!ADJ[e.source]) ADJ[e.source] = new Set();
  if (!ADJ[e.target]) ADJ[e.target] = new Set();
  ADJ[e.source].add(e.target);
  ADJ[e.target].add(e.source);
});

// Build node ID-to-label map for relationship display
const ID_TO_LABEL = {};
ARCH.graph.nodes.forEach(n => { ID_TO_LABEL[n.id] = n.data.label; });

// === Custom Nodes ===
function EntityNodeComponent({ data, selected }) {
  const c = data.color || '#64748b';
  return html`
    <div className=${'entity-node' + (selected ? ' selected' : '')} style=${{ borderLeft: '3px solid ' + c }}>
      <${Handle} type="target" position=${Position.Top} style=${{ background: c, width: 6, height: 6, border: 'none' }} />
      <div className="entity-header" style=${{ background: c + '15' }}>
        <span className="name">${data.label}</span>
        ${data.records && data.records !== '\u2014' && html`<span className="record-badge">${data.records}</span>`}
      </div>
      <div className="entity-body">
        <div className="cat-ind" style=${{ background: c }}></div>
        <span className="entity-cat">${data.category}</span>
        <span className="prop-ct">${data.propCount}p</span>
        ${data.relCount > 0 && html`<span className="rel-ct">${data.relCount}r</span>`}
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

// === ELK Layout ===
async function layoutNodes(nodes, edges, dir = 'DOWN', grouped = false) {
  if (grouped && nodes.length > 0 && nodes[0].type === 'entityNode') {
    const catGroups = {};
    nodes.forEach(n => {
      const cat = n.data.category || 'Other';
      if (!catGroups[cat]) catGroups[cat] = [];
      catGroups[cat].push(n);
    });
    const graph = {
      id: 'root',
      layoutOptions: {
        'elk.algorithm': 'layered', 'elk.direction': dir,
        'elk.spacing.nodeNode': '40',
        'elk.layered.spacing.nodeNodeBetweenLayers': '65',
        'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
        'elk.padding': '[top=50,left=50,bottom=50,right=50]',
        'elk.separateConnectedComponents': 'false',
      },
      children: Object.entries(catGroups).map(([cat, catNodes]) => ({
        id: 'group_' + cat.replace(/[^a-zA-Z0-9]/g, '_'),
        layoutOptions: {
          'elk.algorithm': 'layered', 'elk.direction': 'RIGHT',
          'elk.spacing.nodeNode': '30',
          'elk.layered.spacing.nodeNodeBetweenLayers': '50',
          'elk.padding': '[top=35,left=20,bottom=20,right=20]',
        },
        children: catNodes.map(n => ({ id: n.id, width: 195, height: 56 })),
        edges: edges.filter(e => catNodes.some(n => n.id === e.source) && catNodes.some(n => n.id === e.target))
          .map(e => ({ id: e.id + '_inner', sources: [e.source], targets: [e.target] })),
      })),
      edges: edges.filter(e => {
        const sc = nodes.find(n => n.id === e.source)?.data.category;
        const tc = nodes.find(n => n.id === e.target)?.data.category;
        return sc !== tc;
      }).map(e => ({ id: e.id, sources: [e.source], targets: [e.target] })),
    };
    const layouted = await elk.layout(graph);
    const positions = {};
    if (layouted.children) {
      layouted.children.forEach(group => {
        const gx = group.x || 0, gy = group.y || 0;
        if (group.children) group.children.forEach(child => {
          positions[child.id] = { x: gx + (child.x || 0), y: gy + (child.y || 0) };
        });
      });
    }
    return { nodes: nodes.map(n => ({ ...n, position: positions[n.id] || { x: 0, y: 0 } })) };
  }
  const graph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'layered', 'elk.direction': dir,
      'elk.spacing.nodeNode': '55', 'elk.layered.spacing.nodeNodeBetweenLayers': '75',
      'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
      'elk.padding': '[top=40,left=40,bottom=40,right=40]',
    },
    children: nodes.map(n => ({ id: n.id, width: n.type === 'entityNode' ? 195 : 160, height: n.type === 'entityNode' ? 56 : 50 })),
    edges: edges.map(e => ({ id: e.id, sources: [e.source], targets: [e.target] })),
  };
  const layouted = await elk.layout(graph);
  return { nodes: nodes.map(n => { const ln = layouted.children.find(c => c.id === n.id); return { ...n, position: { x: ln?.x || 0, y: ln?.y || 0 } }; }) };
}

// === Entity Graph View with Focus + Search Highlight ===
function EntityGraphView({ onSelectNode, activeCategories, searchQuery, useGrouped, focusNodeId, onFocusChange }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const { fitView } = useReactFlow();

  const filtered = useMemo(() => {
    let fn = ARCH.graph.nodes.filter(n => activeCategories.has(n.data.category));
    const ids = new Set(fn.map(n => n.id));
    return { nodes: fn, edges: ARCH.graph.edges.filter(e => ids.has(e.source) && ids.has(e.target)) };
  }, [activeCategories]);

  // Compute search matches separately (don't filter nodes out, just mark them)
  const searchMatchIds = useMemo(() => {
    if (!searchQuery) return new Set();
    const q = searchQuery.toLowerCase();
    return new Set(filtered.nodes.filter(n =>
      n.data.label.toLowerCase().includes(q) ||
      n.data.category.toLowerCase().includes(q) ||
      (n.data.description && n.data.description.toLowerCase().includes(q))
    ).map(n => n.id));
  }, [filtered.nodes, searchQuery]);

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
      setNodes(result.nodes); setEdges(se); setLoading(false);
      setTimeout(() => fitView({ padding: 0.08, duration: 500 }), 150);
    });
  }, [filtered, useGrouped]);

  // Apply focus mode classes
  useEffect(() => {
    if (!focusNodeId) {
      document.querySelectorAll('.react-flow__node').forEach(el => { el.classList.remove('dimmed', 'highlighted'); });
      document.querySelectorAll('.react-flow__edge').forEach(el => { el.classList.remove('dimmed', 'highlighted'); });
      document.querySelectorAll('.react-flow').forEach(el => el.classList.remove('focus-active'));
      return;
    }
    document.querySelectorAll('.react-flow').forEach(el => el.classList.add('focus-active'));
    const connected = ADJ[focusNodeId] || new Set();
    document.querySelectorAll('.react-flow__node').forEach(el => {
      const nid = el.getAttribute('data-id');
      if (nid === focusNodeId || connected.has(nid)) {
        el.classList.add('highlighted'); el.classList.remove('dimmed');
      } else {
        el.classList.add('dimmed'); el.classList.remove('highlighted');
      }
    });
    document.querySelectorAll('.react-flow__edge').forEach(el => {
      const src = el.getAttribute('data-source') || '';
      const tgt = el.getAttribute('data-target') || '';
      if (src === focusNodeId || tgt === focusNodeId) {
        el.classList.add('highlighted'); el.classList.remove('dimmed');
      } else {
        el.classList.add('dimmed'); el.classList.remove('highlighted');
      }
    });
  }, [focusNodeId, nodes]);

  // Apply search highlight classes
  useEffect(() => {
    if (!searchQuery || searchMatchIds.size === 0) {
      document.querySelectorAll('.react-flow').forEach(el => el.classList.remove('search-active'));
      document.querySelectorAll('.react-flow__node').forEach(el => el.classList.remove('search-match'));
      return;
    }
    // Only apply if no focus is active
    if (focusNodeId) return;
    document.querySelectorAll('.react-flow').forEach(el => el.classList.add('search-active'));
    document.querySelectorAll('.react-flow__node').forEach(el => {
      const nid = el.getAttribute('data-id');
      if (searchMatchIds.has(nid)) { el.classList.add('search-match'); } else { el.classList.remove('search-match'); }
    });
  }, [searchQuery, searchMatchIds, focusNodeId, nodes]);

  const onNodeClick = useCallback((_, node) => {
    onSelectNode(node.data);
    onFocusChange(node.id);
  }, [onSelectNode, onFocusChange]);

  const onPaneClick = useCallback(() => { onFocusChange(null); }, [onFocusChange]);

  if (loading) return html`<div className="loading">Computing layout\u2026<div className="loading-sub">${filtered.nodes.length} nodes \u00B7 ${filtered.edges.length} edges</div></div>`;
  return html`
    <${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNodesChange} onEdgesChange=${onEdgesChange}
      onNodeClick=${onNodeClick} onPaneClick=${onPaneClick} nodeTypes=${nodeTypes}
      fitView fitViewOptions=${{ padding: 0.08 }} minZoom=${0.06} maxZoom=${2.5}
      proOptions=${{ hideAttribution: true }}>
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
    const fe = ARCH.flow.edges.map(e => ({ ...e, type: 'smoothstep', animated: true, style: { stroke: 'rgba(59,130,246,0.35)', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(59,130,246,0.45)', width: 14, height: 14 } }));
    layoutNodes(fn, fe, 'RIGHT').then(r => { setNodes(r.nodes); setEdges(fe); setLoading(false); setTimeout(() => fitView({ padding: 0.15, duration: 400 }), 100); });
  }, []);
  if (loading) return html`<div className="loading">Computing layout\u2026</div>`;
  return html`<${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNC} onEdgesChange=${onEC} nodeTypes=${nodeTypes} fitView fitViewOptions=${{ padding: 0.15 }} minZoom=${0.2} maxZoom=${2} proOptions=${{ hideAttribution: true }}><${Background} gap=${24} size=${1} color=${'#0f1629'} /><${Controls} /></${ReactFlow}>`;
}

// === Integration View ===
function IntegrationView() {
  const [nodes, setNodes, onNC] = useNodesState([]);
  const [edges, setEdges, onEC] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const { fitView } = useReactFlow();
  useEffect(() => {
    const fn = ARCH.integration.nodes.map(n => ({ ...n, type: 'integNode' }));
    const fe = ARCH.integration.edges.map(e => ({ ...e, type: 'smoothstep', style: { stroke: 'rgba(139,92,246,0.3)', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(139,92,246,0.35)', width: 14, height: 14 } }));
    layoutNodes(fn, fe, 'RIGHT').then(r => { setNodes(r.nodes); setEdges(fe); setLoading(false); setTimeout(() => fitView({ padding: 0.2, duration: 400 }), 100); });
  }, []);
  if (loading) return html`<div className="loading">Computing layout\u2026</div>`;
  return html`<${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNC} onEdgesChange=${onEC} nodeTypes=${nodeTypes} fitView fitViewOptions=${{ padding: 0.2 }} minZoom=${0.3} maxZoom=${2} proOptions=${{ hideAttribution: true }}><${Background} gap=${24} size=${1} color=${'#0f1629'} /><${Controls} /></${ReactFlow}>`;
}

// === Dashboard View ===
function DashboardView() {
  const d = ARCH.dashboard;
  const cats = Object.entries(d.categories).sort((a, b) => b[1].count - a[1].count);
  const mx = Math.max(...cats.map(c => c[1].count));
  const withRecords = ARCH.graph.nodes.filter(n => n.data.records && n.data.records !== '\u2014').length;
  const totalRecordStr = ARCH.graph.nodes.reduce((acc, n) => { const r = n.data.records; if (!r || r === '\u2014') return acc; const num = parseInt(r.replace(/[^0-9]/g, '')); return isNaN(num) ? acc : acc + num; }, 0);
  const topRels = [...ARCH.graph.nodes].sort((a, b) => (b.data.relCount || 0) - (a.data.relCount || 0)).slice(0, 8);

  // Relationship type distribution
  const relTypes = {};
  ARCH.graph.edges.forEach(e => {
    const lbl = e.label || (e.data && e.data.label) || 'unlabeled';
    relTypes[lbl] = (relTypes[lbl] || 0) + 1;
  });
  const topRelTypes = Object.entries(relTypes).sort((a, b) => b[1] - a[1]).slice(0, 10);

  return html`<div className="dash-grid">
    <div className="dash-card"><h3>System Overview</h3>
      <div style=${{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div><div className="stat-big">${d.totalEntities}</div><div className="stat-label">Entities</div></div>
        <div><div className="stat-big">${d.totalProperties}</div><div className="stat-label">Properties</div></div>
        <div><div className="stat-big">${d.totalRelationships}</div><div className="stat-label">Relationships</div></div>
        <div><div className="stat-big">${totalRecordStr > 1000000 ? (totalRecordStr/1000000).toFixed(1)+'M' : totalRecordStr > 1000 ? Math.round(totalRecordStr/1000)+'K' : totalRecordStr}</div><div className="stat-label">Total Records</div></div>
      </div>
    </div>
    <div className="dash-card"><h3>Domains</h3>
      ${cats.map(([n, i]) => html`<div className="cat-bar" key=${n}><span className="cat-bar-label">${n}</span><div style=${{ flex: 1, background: 'rgba(255,255,255,.03)', borderRadius: '2px', overflow: 'hidden' }}><div className="cat-bar-fill" style=${{ width: (i.count / mx * 100) + '%', background: i.color }}></div></div><span className="cat-bar-count">${i.count}</span></div>`)}
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
      <div className="stat-row"><span className="stat-label">Data Coverage</span><span className="stat-value" style=${{ color: '#22d3ee' }}>${withRecords}/${d.totalEntities}</span></div>
    </div>
    <div className="dash-card"><h3>Most Connected Entities</h3>
      ${topRels.map(n => html`<div className="stat-row" key=${n.id}><span className="stat-label" style=${{ display: 'flex', alignItems: 'center', gap: '6px' }}><span style=${{ width: 6, height: 6, borderRadius: 2, background: n.data.color, display: 'inline-block' }}></span>${n.data.label}</span><span className="stat-value" style=${{ color: n.data.color }}>${n.data.relCount}</span></div>`)}
    </div>
    <div className="dash-card"><h3>Top Relationship Types</h3>
      ${topRelTypes.map(([lbl, cnt]) => html`<div className="stat-row" key=${lbl}><span className="mono" style=${{ fontSize: '11px', color: 'var(--cyan)' }}>${lbl}</span><span className="stat-value" style=${{ color: 'var(--text-2)', fontSize: '14px' }}>${cnt}</span></div>`)}
    </div>
    <div className="dash-card"><h3>Density Metrics</h3>
      <div style=${{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '16px' }}>
        <div style=${{ textAlign: 'center' }}><div className="stat-big" style=${{ fontSize: '28px' }}>${(d.totalRelationships / d.totalEntities).toFixed(1)}</div><div className="stat-label">Rels / Entity</div></div>
        <div style=${{ textAlign: 'center' }}><div className="stat-big" style=${{ fontSize: '28px' }}>${(d.totalProperties / d.totalEntities).toFixed(0)}</div><div className="stat-label">Props / Entity</div></div>
        <div style=${{ textAlign: 'center' }}><div className="stat-big" style=${{ fontSize: '28px' }}>${Object.keys(d.categories).length}</div><div className="stat-label">Domains</div></div>
        <div style=${{ textAlign: 'center' }}><div className="stat-big" style=${{ fontSize: '28px' }}>${d.qdrantCollections + d.sqliteDatabases + d.neo4jNodeTypes}</div><div className="stat-label">Stores</div></div>
      </div>
    </div>
  </div>`;
}

// === Detail Panel with grouped relationships ===
function DetailPanel({ data, onClose, onNavigateToEntity }) {
  const nodeId = ARCH.graph.nodes.find(n => n.data.label === data.label)?.id || data.label;
  const outE = ARCH.graph.edges.filter(e => e.source === nodeId);
  const inE = ARCH.graph.edges.filter(e => e.target === nodeId);
  const [openGroups, setOpenGroups] = useState(new Set(['outgoing', 'incoming']));

  const toggleGroup = useCallback(g => {
    setOpenGroups(prev => { const n = new Set(prev); if (n.has(g)) n.delete(g); else n.add(g); return n; });
  }, []);

  // Group relationships by label
  const groupByLabel = (edges, isOutgoing) => {
    const groups = {};
    edges.forEach(e => {
      const lbl = e.label || (e.data && e.data.label) || 'related';
      if (!groups[lbl]) groups[lbl] = [];
      groups[lbl].push(isOutgoing ? e.target : e.source);
    });
    return Object.entries(groups).sort((a, b) => b[1].length - a[1].length);
  };

  const outGroups = groupByLabel(outE, true);
  const inGroups = groupByLabel(inE, false);

  return html`<div className="detail-panel">
    <div className="detail-hdr">
      <div style=${{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div>
          <div style=${{ fontSize: '16px', fontWeight: 600, marginBottom: '4px' }}>${data.label}</div>
          <div style=${{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <div style=${{ width: 8, height: 8, borderRadius: 2, background: data.color }}></div>
            <span style=${{ fontSize: '11px', color: 'var(--text-3)' }}>${data.category}</span>
            ${data.relCount > 0 && html`<span style=${{ fontSize: '10px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', marginLeft: '4px' }}>${data.relCount} rels</span>`}
          </div>
        </div>
        <button onClick=${onClose} style=${{ background: 'none', border: 'none', color: 'var(--text-3)', cursor: 'pointer', fontSize: '18px', lineHeight: 1 }}>${'\u00D7'}</button>
      </div>
      ${data.description && html`<p style=${{ fontSize: '11px', color: 'var(--text-2)', marginTop: '10px', lineHeight: 1.5 }}>${data.description}</p>`}
    </div>
    <div className="detail-sec"><div className="detail-sec-title">Overview</div>
      <div style=${{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Records</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.records || '\u2014'}</div></div>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Properties</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.propCount}</div></div>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Connections</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.relCount || 0}</div></div>
      </div>
    </div>
    ${data.sources && data.sources.length > 0 && html`<div className="detail-sec"><div className="detail-sec-title">Sources</div><div style=${{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>${data.sources.map(s => html`<span className="detail-badge" style=${{ background: 'rgba(59,130,246,.12)', color: '#93c5fd' }} key=${s}>${s}</span>`)}</div></div>`}
    ${data.storage && data.storage.length > 0 && html`<div className="detail-sec"><div className="detail-sec-title">Storage</div><div style=${{ display: 'flex', flexDirection: 'column', gap: '3px' }}>${data.storage.map(s => html`<div className="mono" style=${{ fontSize: '10px', color: 'var(--text-2)' }} key=${s}>${s}</div>`)}</div></div>`}
    ${(outE.length > 0 || inE.length > 0) && html`<div className="detail-sec"><div className="detail-sec-title">Relationships (${outE.length + inE.length})</div>
      ${outGroups.length > 0 && html`<div className="rel-group">
        <div className="rel-group-header" onClick=${() => toggleGroup('outgoing')}>
          <span className=${'rel-group-chevron' + (openGroups.has('outgoing') ? ' open' : '')}>${'\u25B6'}</span>
          <span style=${{ fontSize: '9px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', letterSpacing: '.1em' }}>OUTGOING (${outE.length})</span>
        </div>
        ${openGroups.has('outgoing') && outGroups.map(([lbl, targets]) => html`<div key=${lbl} style=${{ marginLeft: '12px', marginBottom: '6px' }}>
          <div style=${{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}><span className="rel-label">${lbl}</span><span className="rel-group-count">${targets.length}</span></div>
          ${targets.map(t => html`<div className="rel-item" key=${t} style=${{ marginLeft: '8px', cursor: 'pointer' }} onClick=${() => onNavigateToEntity(t)}><span className="rel-arrow">${'\u2192'}</span><span className="rel-target" style=${{ borderBottom: '1px dotted var(--border-1)' }}>${ID_TO_LABEL[t] || t}</span></div>`)}
        </div>`)}
      </div>`}
      ${inGroups.length > 0 && html`<div className="rel-group">
        <div className="rel-group-header" onClick=${() => toggleGroup('incoming')}>
          <span className=${'rel-group-chevron' + (openGroups.has('incoming') ? ' open' : '')}>${'\u25B6'}</span>
          <span style=${{ fontSize: '9px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', letterSpacing: '.1em' }}>INCOMING (${inE.length})</span>
        </div>
        ${openGroups.has('incoming') && inGroups.map(([lbl, sources]) => html`<div key=${lbl} style=${{ marginLeft: '12px', marginBottom: '6px' }}>
          <div style=${{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}><span className="rel-label">${lbl}</span><span className="rel-group-count">${sources.length}</span></div>
          ${sources.map(s => html`<div className="rel-item" key=${s} style=${{ marginLeft: '8px', cursor: 'pointer' }} onClick=${() => onNavigateToEntity(s)}><span className="rel-arrow">${'\u2190'}</span><span className="rel-target" style=${{ borderBottom: '1px dotted var(--border-1)' }}>${ID_TO_LABEL[s] || s}</span></div>`)}
        </div>`)}
      </div>`}
    </div>`}
    ${data.properties && data.properties.length > 0 && html`<div className="detail-sec"><div className="detail-sec-title">Schema (${data.properties.length})</div>
      <div style=${{ maxHeight: '350px', overflowY: 'auto' }}>
        ${data.properties.map(p => html`<div className="detail-prop-row" key=${p.name}>
          <span className="detail-prop-name">${p.name}</span>
          <span className="detail-prop-type">${p.type}</span>
          <span className="detail-prop-note" title=${p.note || ''}>${p.note || ''}</span>
        </div>`)}
      </div>
    </div>`}
  </div>`;
}

// === Category Sidebar ===
function CategorySidebar({ activeCategories, onToggle, searchQuery, onSearchChange, useGrouped, onToggleGrouped, searchMatchCount }) {
  const allOn = activeCategories.size === Object.keys(CATEGORIES).length;
  return html`<div className="cat-sidebar">
    <div className="cat-sidebar-hdr">
      <div className="cat-sidebar-title">Filter</div>
      <div style=${{ marginTop: '8px', position: 'relative' }}>
        <input className="search-input" placeholder=${'Search entities\u2026'} value=${searchQuery} onInput=${e => onSearchChange(e.target.value)} />
        ${searchQuery && html`<span className="search-count" style=${{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)' }}>${searchMatchCount}</span>`}
      </div>
      <div style=${{ display: 'flex', gap: '6px', marginTop: '8px' }}>
        <button className="toolbar-btn" onClick=${() => onToggle('__ALL__')}>${allOn ? 'Hide All' : 'Show All'}</button>
        <button className=${'toolbar-btn' + (useGrouped ? ' active' : '')} onClick=${onToggleGrouped}>Grouped</button>
      </div>
    </div>
    ${Object.entries(CATEGORIES).map(([n, i]) => html`<div className=${'cat-toggle' + (activeCategories.has(n) ? '' : ' off')} key=${n} onClick=${() => onToggle(n)}><div className="cat-toggle-dot" style=${{ background: i.color }}></div><span className="cat-toggle-label">${n}</span><span className="cat-toggle-count">${i.count}</span></div>`)}
  </div>`;
}

// === Export utility ===
function exportArchData() {
  const blob = new Blob([JSON.stringify(ARCH, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'pts_architecture_data.json'; a.click();
  URL.revokeObjectURL(url);
}

// === Main App ===
function App() {
  const [tab, setTab] = useState('graph');
  const [sel, setSel] = useState(null);
  const [sq, setSq] = useState('');
  const [ac, setAc] = useState(new Set(Object.keys(CATEGORIES)));
  const [grouped, setGrouped] = useState(true);
  const [focusId, setFocusId] = useState(null);

  const toggleCat = useCallback(cat => {
    setAc(prev => {
      if (cat === '__ALL__') return prev.size === Object.keys(CATEGORIES).length ? new Set() : new Set(Object.keys(CATEGORIES));
      const n = new Set(prev); if (n.has(cat)) n.delete(cat); else n.add(cat); return n;
    });
  }, []);

  // Search match count
  const searchMatchCount = useMemo(() => {
    if (!sq) return 0;
    const q = sq.toLowerCase();
    return ARCH.graph.nodes.filter(n =>
      ac.has(n.data.category) && (
        n.data.label.toLowerCase().includes(q) ||
        n.data.category.toLowerCase().includes(q) ||
        (n.data.description && n.data.description.toLowerCase().includes(q))
      )
    ).length;
  }, [sq, ac]);

  // Navigate to entity from detail panel relationship click
  const navigateToEntity = useCallback(entityId => {
    const node = ARCH.graph.nodes.find(n => n.id === entityId);
    if (node) {
      setSel(node.data);
      setFocusId(entityId);
    }
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') { setSel(null); setFocusId(null); setSq(''); }
      if (e.key === '/' && !e.ctrlKey && !e.metaKey && document.activeElement?.tagName !== 'INPUT') {
        e.preventDefault();
        document.querySelector('.search-input')?.focus();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
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
      <span className="top-bar-ver">V6.3</span>
      <div style=${{ width: 1, height: 20, background: 'var(--border-0)' }}></div>
      <div style=${{ display: 'flex', gap: 0 }}>${tabs.map(t => html`<button key=${t.id} className=${'tab-btn' + (tab === t.id ? ' active' : '')} onClick=${() => { setTab(t.id); setSel(null); setFocusId(null); }}>${t.label}</button>`)}</div>
      <div style=${{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '12px' }}>
        ${focusId && html`<span className="mono" style=${{ fontSize: '10px', color: 'var(--cyan)', background: 'rgba(34,211,238,.08)', padding: '2px 8px', borderRadius: '3px' }}>Focus: ${ID_TO_LABEL[focusId] || focusId}</span>`}
        <button className="toolbar-btn" onClick=${exportArchData} title="Export architecture data as JSON" style=${{ fontSize: '9px' }}>${'\u2B07'} Export</button>
        <span className="mono" style=${{ fontSize: '10px', color: 'var(--text-3)' }}>${ARCH.dashboard.totalEntities} entities ${'\u00B7'} ${ARCH.dashboard.totalRelationships} rels ${'\u00B7'} ${ARCH.dashboard.totalProperties} props</span>
      </div>
    </div>
    <div style=${{ display: 'flex', flex: 1, overflow: 'hidden' }}>
      ${tab === 'graph' && html`<${CategorySidebar} activeCategories=${ac} onToggle=${toggleCat} searchQuery=${sq} onSearchChange=${setSq} useGrouped=${grouped} onToggleGrouped=${() => setGrouped(g => !g)} searchMatchCount=${searchMatchCount} />`}
      <div style=${{ flex: 1, position: 'relative' }}>
        ${tab === 'graph' && html`<${ReactFlowProvider}><${EntityGraphView} onSelectNode=${setSel} activeCategories=${ac} searchQuery=${sq} useGrouped=${grouped} focusNodeId=${focusId} onFocusChange=${setFocusId} /></${ReactFlowProvider}>`}
        ${tab === 'flow' && html`<${ReactFlowProvider}><${DataFlowView} /></${ReactFlowProvider}>`}
        ${tab === 'integration' && html`<${ReactFlowProvider}><${IntegrationView} /></${ReactFlowProvider}>`}
        ${tab === 'dashboard' && html`<${DashboardView} />`}
      </div>
      ${sel && tab === 'graph' && html`<${DetailPanel} data=${sel} onClose=${() => { setSel(null); setFocusId(null); }} onNavigateToEntity=${navigateToEntity} />`}
    </div>
    ${tab === 'graph' && html`<div className="kb-hint"><span><span className="kb-key">Esc</span> Clear</span><span><span className="kb-key">/</span> Search</span><span><span className="kb-key">Click</span> Focus</span><span><span className="kb-key">Scroll</span> Zoom</span></div>`}
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
<title>PTS Data Architecture Explorer V6.3</title>
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

outpath = os.path.join(BASE, 'PTS_DATA_ARCHITECTURE_EXPLORER_V6.3.html')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"V6.3 written: {len(output):,} chars ({len(output)//1024}KB)")
