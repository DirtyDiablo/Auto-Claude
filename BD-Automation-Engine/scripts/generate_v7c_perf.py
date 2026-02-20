#!/usr/bin/env python3
"""Generate PTS Data Architecture Explorer V7C — Vercel React best practices for maximum performance.

Performance optimizations over V6.4:
- O(1) Map/Set lookups instead of Array.find()/.filter()
- State-driven visual classes (no DOM manipulation)
- Debounced search input (150ms)
- Layout caching with cache key
- Debounced layout computation (150ms)
- Memoized components with custom comparators
- Combined iterations (for...of instead of chained .filter().map())
- content-visibility: auto on detail panel sections and dashboard cards
- Functional setState everywhere
- Performance overlay (Ctrl+P toggle)
- Pre-computed lowercase labels at module level
"""
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

/* Focus mode — state-driven via node className prop */
.react-flow.focus-active .react-flow__node.dimmed{opacity:.12!important;filter:saturate(0.2)!important;transition:opacity .3s,filter .3s}
.react-flow.focus-active .react-flow__edge.dimmed path{stroke:rgba(148,163,184,0.04)!important;transition:stroke .3s}
.react-flow.focus-active .react-flow__edge.dimmed .react-flow__edge-text{fill:transparent!important}
.react-flow.focus-active .react-flow__node.highlighted{opacity:1!important;filter:none!important;transition:opacity .3s}
.react-flow.focus-active .react-flow__edge.highlighted path{stroke:rgba(34,211,238,0.5)!important;stroke-width:2!important;transition:stroke .3s}
.react-flow.focus-active .react-flow__edge.highlighted .react-flow__edge-text{fill:var(--cyan)!important}
.react-flow.focus-active .react-flow__edge.highlighted .react-flow__edge-textbg{fill:var(--bg-0)!important;fill-opacity:0.9!important}

/* Search highlight — state-driven via node className prop */
.react-flow.search-active .react-flow__node.search-match{box-shadow:0 0 0 2px var(--cyan),0 0 20px rgba(34,211,238,.25)!important;border-radius:5px}
.react-flow.search-active .react-flow__node:not(.search-match){opacity:.2!important;filter:saturate(0.15)!important;transition:opacity .3s,filter .3s}
.react-flow.search-active .react-flow__edge path{stroke:rgba(148,163,184,0.05)!important}

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
.dash-card{background:var(--bg-1);border:1px solid var(--border-0);border-radius:8px;padding:20px;transition:border-color .2s;content-visibility:auto;contain-intrinsic-size:0 200px}
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
.detail-sec{padding:14px 20px;border-bottom:1px solid var(--border-0);content-visibility:auto;contain-intrinsic-size:0 80px}
.detail-sec-title{font-size:9px;font-weight:600;color:var(--text-3);text-transform:uppercase;letter-spacing:.12em;margin-bottom:10px;font-family:'JetBrains Mono',monospace}
.detail-badge{display:inline-block;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:500;margin:2px;color:#fff;font-family:'JetBrains Mono',monospace}
.detail-prop-row{display:grid;grid-template-columns:1fr auto 1fr;gap:8px;align-items:center;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.03);font-size:11px}
.detail-prop-name{color:var(--cyan);font-weight:500}
.detail-prop-type{color:var(--text-3);font-family:'JetBrains Mono',monospace;font-size:10px;text-align:center}
.detail-prop-note{color:var(--text-3);font-size:9px;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

.cat-sidebar{width:240px;background:var(--bg-1);border-right:1px solid var(--border-0);overflow-y:auto;flex-shrink:0;padding:12px 0}
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

/* Search results dropdown */
.search-results{margin-top:6px;max-height:200px;overflow-y:auto;border:1px solid var(--border-0);border-radius:4px;background:var(--bg-0)}
.search-result-item{display:flex;align-items:center;gap:8px;padding:6px 10px;cursor:pointer;transition:background .15s;border-bottom:1px solid var(--border-0)}
.search-result-item:last-child{border-bottom:none}
.search-result-item:hover{background:rgba(34,211,238,.06)}
.search-result-item .sr-dot{width:6px;height:6px;border-radius:2px;flex-shrink:0}
.search-result-item .sr-name{font-size:11px;color:var(--text-0);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.search-result-item .sr-cat{font-size:9px;color:var(--text-3);font-family:'JetBrains Mono',monospace}
.search-result-item .sr-rels{font-size:9px;color:var(--text-3);font-family:'JetBrains Mono',monospace}

/* Nav history breadcrumb */
.nav-history{display:flex;align-items:center;gap:4px;padding:8px 20px;background:var(--bg-2);border-bottom:1px solid var(--border-0);font-size:10px}
.nav-history-btn{background:none;border:none;color:var(--text-3);cursor:pointer;font-family:'JetBrains Mono',monospace;font-size:10px;padding:2px 6px;border-radius:3px;transition:all .15s}
.nav-history-btn:hover{color:var(--cyan);background:rgba(34,211,238,.06)}
.nav-crumb{color:var(--text-3);cursor:pointer;padding:1px 6px;border-radius:3px;transition:all .15s}
.nav-crumb:hover{color:var(--cyan);background:rgba(34,211,238,.06)}
.nav-crumb.current{color:var(--text-0);font-weight:500}
.nav-sep{color:var(--border-2);font-size:9px}

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
.rel-group{margin-bottom:10px}
.rel-group-header{display:flex;align-items:center;gap:6px;cursor:pointer;padding:4px 0;user-select:none}
.rel-group-header:hover{color:var(--text-0)}
.rel-group-chevron{font-size:10px;color:var(--text-3);transition:transform .2s;display:inline-block;width:12px}
.rel-group-chevron.open{transform:rotate(90deg)}
.rel-group-count{font-size:9px;color:var(--text-3);font-family:'JetBrains Mono',monospace}

.loading{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:var(--text-3);font-size:13px;gap:12px}
.loading::before{content:'';width:20px;height:20px;border:2px solid var(--border-0);border-top-color:var(--cyan);border-radius:50%;animation:spin .8s linear infinite}
.loading-sub{font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace}
@keyframes spin{to{transform:rotate(360deg)}}
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border-0);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--border-1)}

.kb-hint{position:fixed;bottom:12px;left:50%;transform:translateX(-50%);background:var(--bg-2);border:1px solid var(--border-0);border-radius:6px;padding:6px 14px;font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace;z-index:100;display:flex;gap:12px;opacity:.6;transition:opacity .3s}
.kb-hint:hover{opacity:1}
.kb-key{background:var(--bg-0);padding:1px 6px;border-radius:3px;color:var(--text-2);border:1px solid var(--border-1)}

.search-count{font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace;padding:2px 8px;background:rgba(34,211,238,.06);border-radius:3px}

/* Hover tooltip */
.hover-tooltip{position:fixed;background:var(--bg-2);border:1px solid var(--border-1);border-radius:6px;padding:10px 14px;max-width:280px;z-index:1000;pointer-events:none;box-shadow:0 8px 32px rgba(0,0,0,.6)}
.hover-tooltip .ht-title{font-size:12px;font-weight:600;color:var(--text-0);margin-bottom:4px}
.hover-tooltip .ht-cat{font-size:9px;color:var(--text-3);text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;font-family:'JetBrains Mono',monospace}
.hover-tooltip .ht-desc{font-size:10px;color:var(--text-2);line-height:1.5;margin-bottom:6px}
.hover-tooltip .ht-stats{display:flex;gap:12px;font-size:9px;font-family:'JetBrains Mono',monospace;color:var(--text-3)}
.hover-tooltip .ht-stats span{color:var(--cyan)}

/* Performance overlay */
.perf-overlay{position:fixed;top:52px;right:12px;background:rgba(8,12,22,.92);border:1px solid var(--border-1);border-radius:6px;padding:8px 12px;font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text-2);z-index:200;display:flex;flex-direction:column;gap:3px;min-width:160px;backdrop-filter:blur(8px)}
.perf-overlay .perf-title{font-size:9px;color:var(--cyan);text-transform:uppercase;letter-spacing:.1em;margin-bottom:2px;font-weight:600}
.perf-overlay .perf-row{display:flex;justify-content:space-between;gap:12px}
.perf-overlay .perf-val{color:var(--text-0);font-weight:500}
"""

JS_APP = r"""
import { useState, useCallback, useMemo, useEffect, useRef, memo, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import { ReactFlow, ReactFlowProvider, useReactFlow, useNodesState, useEdgesState, Background, Controls, MiniMap, Handle, Position, MarkerType } from '@xyflow/react';
import ELK from 'elkjs/lib/elk.bundled.js';
import htm from 'htm';
const html = htm.bind(createElement);
const elk = new ELK();

// ============================================================
// MODULE-LEVEL PRE-COMPUTED DATA — O(1) lookups (Map/Set)
// ============================================================
const CATEGORIES = ARCH.categories;
const CAT_COLORS = new Map();
for (const [k, v] of Object.entries(CATEGORIES)) { CAT_COLORS.set(k, v.color); }
const CAT_KEYS = Object.keys(CATEGORIES);

// O(1) node lookups by ID
const NODES_BY_ID = new Map();
for (const n of ARCH.graph.nodes) { NODES_BY_ID.set(n.id, n); }

// O(1) nodes grouped by category
const NODES_BY_CATEGORY = new Map();
for (const n of ARCH.graph.nodes) {
  const cat = n.data.category;
  if (!NODES_BY_CATEGORY.has(cat)) NODES_BY_CATEGORY.set(cat, new Set());
  NODES_BY_CATEGORY.get(cat).add(n.id);
}

// O(1) edge index by source and target
const EDGE_INDEX = { bySource: new Map(), byTarget: new Map() };
for (const e of ARCH.graph.edges) {
  if (!EDGE_INDEX.bySource.has(e.source)) EDGE_INDEX.bySource.set(e.source, []);
  EDGE_INDEX.bySource.get(e.source).push(e);
  if (!EDGE_INDEX.byTarget.has(e.target)) EDGE_INDEX.byTarget.set(e.target, []);
  EDGE_INDEX.byTarget.get(e.target).push(e);
}

// O(1) adjacency map
const ADJ = new Map();
for (const e of ARCH.graph.edges) {
  if (!ADJ.has(e.source)) ADJ.set(e.source, new Set());
  if (!ADJ.has(e.target)) ADJ.set(e.target, new Set());
  ADJ.get(e.source).add(e.target);
  ADJ.get(e.target).add(e.source);
}

// O(1) label and data lookups
const LABEL_BY_ID = new Map();
const DATA_BY_ID = new Map();
for (const n of ARCH.graph.nodes) {
  LABEL_BY_ID.set(n.id, n.data.label);
  DATA_BY_ID.set(n.id, n.data);
}

// Pre-computed lowercase labels for fast search
const SEARCH_INDEX = [];
for (const n of ARCH.graph.nodes) {
  SEARCH_INDEX.push({
    id: n.id,
    node: n,
    labelLower: n.data.label.toLowerCase(),
    categoryLower: n.data.category.toLowerCase(),
    descLower: (n.data.description || '').toLowerCase(),
  });
}

// Pre-computed node category map for grouped layout edge filtering
const NODE_CATEGORY = new Map();
for (const n of ARCH.graph.nodes) { NODE_CATEGORY.set(n.id, n.data.category); }

// ============================================================
// LAYOUT CACHING
// ============================================================
const layoutCache = new Map();
function getCacheKey(nodeIds, edgeCount, dir, grouped) {
  // Sort node IDs for consistent keys
  const sorted = [...nodeIds].sort();
  return sorted.join(',') + '|' + edgeCount + '|' + dir + '|' + (grouped ? '1' : '0');
}

// ============================================================
// PERFORMANCE MONITORING
// ============================================================
let _layoutTime = 0;
let _layoutCount = 0;

// ============================================================
// HOVER TOOLTIP (unchanged logic, memo-optimized)
// ============================================================
function HoverTooltipComponent({ nodeData, position }) {
  if (!nodeData || !position) return null;
  return html`<div className="hover-tooltip" style=${{ left: position.x + 12, top: position.y - 10 }}>
    <div className="ht-title">${nodeData.label}</div>
    <div className="ht-cat">${nodeData.category}</div>
    ${nodeData.description ? html`<div className="ht-desc">${nodeData.description.length > 120 ? nodeData.description.slice(0, 120) + '\u2026' : nodeData.description}</div>` : null}
    <div className="ht-stats">
      ${nodeData.records && nodeData.records !== '\u2014' ? html`<span>${nodeData.records} records</span>` : null}
      <span>${nodeData.propCount}p</span>
      <span>${nodeData.relCount}r</span>
    </div>
  </div>`;
}
const HoverTooltip = memo(HoverTooltipComponent, (prev, next) => {
  return prev.nodeData === next.nodeData && prev.position === next.position;
});

// ============================================================
// CUSTOM NODES — memo with custom comparators
// ============================================================
function EntityNodeComponent({ data, selected }) {
  const c = data.color || '#64748b';
  return html`
    <div className=${'entity-node' + (selected ? ' selected' : '')} style=${{ borderLeft: '3px solid ' + c }}>
      <${Handle} type="target" position=${Position.Top} style=${{ background: c, width: 6, height: 6, border: 'none' }} />
      <div className="entity-header" style=${{ background: c + '15' }}>
        <span className="name">${data.label}</span>
        ${data.records && data.records !== '\u2014' ? html`<span className="record-badge">${data.records}</span>` : null}
      </div>
      <div className="entity-body">
        <div className="cat-ind" style=${{ background: c }}></div>
        <span className="entity-cat">${data.category}</span>
        <span className="prop-ct">${data.propCount}p</span>
        ${data.relCount > 0 ? html`<span className="rel-ct">${data.relCount}r</span>` : null}
      </div>
      <${Handle} type="source" position=${Position.Bottom} style=${{ background: c, width: 6, height: 6, border: 'none' }} />
    </div>`;
}
const EntityNode = memo(EntityNodeComponent, (prev, next) => {
  return prev.data.label === next.data.label &&
         prev.selected === next.selected &&
         prev.data.dimmed === next.data.dimmed &&
         prev.data.highlighted === next.data.highlighted &&
         prev.data.searchMatch === next.data.searchMatch;
});

function FlowNodeComponent({ data }) {
  const c = data.color || '#3b82f6';
  return html`
    <div className="flow-node" style=${{ background: c + '12', borderColor: c + '25' }}>
      <${Handle} type="target" position=${Position.Left} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
      <div className="flow-inner"><div className="flow-label">${data.label}</div>${data.sublabel ? html`<div className="flow-sub">${data.sublabel}</div>` : null}</div>
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
      ${data.sublabel ? html`<div style=${{ color: 'var(--text-3)', fontSize: '10px', marginTop: '3px' }}>${data.sublabel}</div>` : null}
      <${Handle} type="source" position=${Position.Right} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
    </div>`;
}
const IntegNode = memo(IntegNodeComponent);

const nodeTypes = { entityNode: EntityNode, flowNode: FlowNode, integNode: IntegNode };

// ============================================================
// ELK LAYOUT (with caching)
// ============================================================
async function layoutNodes(nodes, edges, dir, grouped) {
  const t0 = performance.now();

  // Check cache
  const nodeIds = nodes.map(n => n.id);
  const cacheKey = getCacheKey(nodeIds, edges.length, dir, grouped);
  const cached = layoutCache.get(cacheKey);
  if (cached) {
    _layoutTime = Math.round(performance.now() - t0);
    _layoutCount++;
    return cached;
  }

  let result;
  if (grouped && nodes.length > 0 && nodes[0].type === 'entityNode') {
    // Build category groups using pre-computed category map — single pass
    const catGroups = new Map();
    const catNodeIdSets = new Map();
    for (const n of nodes) {
      const cat = n.data.category || 'Other';
      if (!catGroups.has(cat)) {
        catGroups.set(cat, []);
        catNodeIdSets.set(cat, new Set());
      }
      catGroups.get(cat).push(n);
      catNodeIdSets.get(cat).add(n.id);
    }

    const nodeIdSet = new Set(nodeIds);

    // Build grouped ELK graph — combined iteration for inter/intra edges
    const groupChildren = [];
    for (const [cat, catNodes] of catGroups) {
      const groupId = 'group_' + cat.replace(/[^a-zA-Z0-9]/g, '_');
      const idSet = catNodeIdSets.get(cat);
      const innerEdges = [];
      for (const e of edges) {
        if (idSet.has(e.source) && idSet.has(e.target)) {
          innerEdges.push({ id: e.id + '_inner', sources: [e.source], targets: [e.target] });
        }
      }
      groupChildren.push({
        id: groupId,
        layoutOptions: {
          'elk.algorithm': 'layered', 'elk.direction': 'RIGHT',
          'elk.spacing.nodeNode': '30', 'elk.layered.spacing.nodeNodeBetweenLayers': '50',
          'elk.padding': '[top=40,left=20,bottom=20,right=20]',
        },
        children: catNodes.map(n => ({ id: n.id, width: 195, height: 56 })),
        edges: innerEdges,
      });
    }

    // Cross-group edges — single pass
    const crossEdges = [];
    for (const e of edges) {
      if (NODE_CATEGORY.get(e.source) !== NODE_CATEGORY.get(e.target)) {
        if (nodeIdSet.has(e.source) && nodeIdSet.has(e.target)) {
          crossEdges.push({ id: e.id, sources: [e.source], targets: [e.target] });
        }
      }
    }

    const graph = {
      id: 'root',
      layoutOptions: {
        'elk.algorithm': 'layered', 'elk.direction': dir,
        'elk.spacing.nodeNode': '40', 'elk.layered.spacing.nodeNodeBetweenLayers': '65',
        'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
        'elk.padding': '[top=50,left=50,bottom=50,right=50]',
        'elk.separateConnectedComponents': 'false',
      },
      children: groupChildren,
      edges: crossEdges,
    };

    const layouted = await elk.layout(graph);
    const positions = new Map();
    const groupBounds = {};
    if (layouted.children) {
      for (const group of layouted.children) {
        const gx = group.x || 0, gy = group.y || 0;
        // Find category name from group id
        let catName = '';
        for (const [c] of catGroups) {
          if ('group_' + c.replace(/[^a-zA-Z0-9]/g, '_') === group.id) { catName = c; break; }
        }
        groupBounds[catName] = { x: gx, y: gy, w: group.width || 400, h: group.height || 200 };
        if (group.children) {
          for (const child of group.children) {
            positions.set(child.id, { x: gx + (child.x || 0), y: gy + (child.y || 0) });
          }
        }
      }
    }
    result = {
      nodes: nodes.map(n => ({ ...n, position: positions.get(n.id) || { x: 0, y: 0 } })),
      groupBounds,
    };
  } else {
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
    // Build position map from layouted children for O(1) lookup
    const posMap = new Map();
    for (const c of layouted.children) { posMap.set(c.id, { x: c.x || 0, y: c.y || 0 }); }
    result = {
      nodes: nodes.map(n => ({ ...n, position: posMap.get(n.id) || { x: 0, y: 0 } })),
      groupBounds: null,
    };
  }

  _layoutTime = Math.round(performance.now() - t0);
  _layoutCount++;
  layoutCache.set(cacheKey, result);
  return result;
}

// ============================================================
// PERFORMANCE OVERLAY (toggle with Ctrl+P)
// ============================================================
function PerfOverlayComponent({ visible, nodeCount, edgeCount }) {
  const renderCount = useRef(0);
  renderCount.current++;
  if (!visible) return null;
  return html`<div className="perf-overlay">
    <div className="perf-title">Performance</div>
    <div className="perf-row"><span>Renders:</span><span className="perf-val">${renderCount.current}</span></div>
    <div className="perf-row"><span>Layout:</span><span className="perf-val">${_layoutTime}ms</span></div>
    <div className="perf-row"><span>Layouts:</span><span className="perf-val">${_layoutCount}</span></div>
    <div className="perf-row"><span>Cache:</span><span className="perf-val">${layoutCache.size}</span></div>
    <div className="perf-row"><span>Nodes:</span><span className="perf-val">${nodeCount}</span></div>
    <div className="perf-row"><span>Edges:</span><span className="perf-val">${edgeCount}</span></div>
  </div>`;
}
const PerfOverlay = memo(PerfOverlayComponent);

// ============================================================
// ENTITY GRAPH VIEW — state-driven classes, debounced layout
// ============================================================
function EntityGraphView({ onSelectNode, activeCategories, debouncedSearch, useGrouped, focusNodeId, onFocusChange, onHoverNode, onHoverEnd }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [groupBounds, setGroupBounds] = useState(null);
  const { fitView } = useReactFlow();
  const layoutTimeoutRef = useRef(null);

  // Filter nodes and edges using Map-based lookups — combined iteration
  const filtered = useMemo(() => {
    const resultNodes = [];
    const idSet = new Set();
    for (const entry of SEARCH_INDEX) {
      if (activeCategories.has(entry.node.data.category)) {
        resultNodes.push(entry.node);
        idSet.add(entry.id);
      }
    }
    const resultEdges = [];
    for (const e of ARCH.graph.edges) {
      if (idSet.has(e.source) && idSet.has(e.target)) {
        resultEdges.push(e);
      }
    }
    return { nodes: resultNodes, edges: resultEdges, idSet };
  }, [activeCategories]);

  // Search match IDs using pre-computed lowercase index
  const searchMatchIds = useMemo(() => {
    if (!debouncedSearch) return new Set();
    const q = debouncedSearch.toLowerCase();
    const matches = new Set();
    for (const entry of SEARCH_INDEX) {
      if (!filtered.idSet.has(entry.id)) continue;
      if (entry.labelLower.includes(q) || entry.categoryLower.includes(q) || entry.descLower.includes(q)) {
        matches.add(entry.id);
      }
    }
    return matches;
  }, [filtered.idSet, debouncedSearch]);

  // Compute CSS class names for nodes (state-driven, no DOM manipulation)
  const nodeClassNames = useMemo(() => {
    const classMap = new Map();
    const hasFocus = !!focusNodeId;
    const hasSearch = debouncedSearch && searchMatchIds.size > 0 && !hasFocus;
    const connected = hasFocus ? (ADJ.get(focusNodeId) || new Set()) : null;

    for (const n of filtered.nodes) {
      let cls = '';
      if (hasFocus) {
        if (n.id === focusNodeId || connected.has(n.id)) {
          cls = 'highlighted';
        } else {
          cls = 'dimmed';
        }
      } else if (hasSearch) {
        if (searchMatchIds.has(n.id)) {
          cls = 'search-match';
        }
      }
      classMap.set(n.id, cls);
    }
    return classMap;
  }, [filtered.nodes, focusNodeId, debouncedSearch, searchMatchIds]);

  // Compute edge class names (state-driven)
  const edgeClassNames = useMemo(() => {
    const classMap = new Map();
    if (!focusNodeId) return classMap;
    for (const e of filtered.edges) {
      if (e.source === focusNodeId || e.target === focusNodeId) {
        classMap.set(e.id, 'highlighted');
      } else {
        classMap.set(e.id, 'dimmed');
      }
    }
    return classMap;
  }, [filtered.edges, focusNodeId]);

  // ReactFlow wrapper class
  const flowClassName = useMemo(() => {
    if (focusNodeId) return 'focus-active';
    if (debouncedSearch && searchMatchIds.size > 0) return 'search-active';
    return '';
  }, [focusNodeId, debouncedSearch, searchMatchIds]);

  // Debounced layout computation
  useEffect(() => {
    setLoading(true);

    // Build styled edges — single combined iteration
    const styledEdges = [];
    for (const e of filtered.edges) {
      const cls = edgeClassNames.get(e.id) || '';
      styledEdges.push({
        ...e, type: 'smoothstep',
        className: cls,
        style: { stroke: 'rgba(148,163,184,0.15)', strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(148,163,184,0.2)', width: 10, height: 10 },
        label: e.label || (e.data && e.data.label) || '',
        labelStyle: { fill: 'transparent', fontSize: 8, fontFamily: 'JetBrains Mono' },
        labelBgStyle: { fill: 'transparent' }, labelBgPadding: [4, 2],
      });
    }

    // Build nodes with className for state-driven visual classes
    const styledNodes = [];
    for (const n of filtered.nodes) {
      styledNodes.push({ ...n, className: nodeClassNames.get(n.id) || '' });
    }

    // Debounce the layout computation
    if (layoutTimeoutRef.current) clearTimeout(layoutTimeoutRef.current);
    layoutTimeoutRef.current = setTimeout(async () => {
      const result = await layoutNodes(styledNodes, styledEdges, 'DOWN', useGrouped);
      setNodes(result.nodes);
      setEdges(styledEdges);
      setGroupBounds(result.groupBounds || null);
      setLoading(false);
      setTimeout(() => fitView({ padding: 0.08, duration: 500 }), 150);
    }, 150);

    return () => { if (layoutTimeoutRef.current) clearTimeout(layoutTimeoutRef.current); };
  }, [filtered, useGrouped, nodeClassNames, edgeClassNames]);

  const onNodeClick = useCallback((_, node) => {
    onSelectNode(node.data);
    onFocusChange(node.id);
    onHoverEnd();
  }, [onSelectNode, onFocusChange, onHoverEnd]);

  const onNodeMouseEnter = useCallback((event, node) => {
    onHoverNode(node.data, { x: event.clientX, y: event.clientY });
  }, [onHoverNode]);

  const onNodeMouseLeave = useCallback(() => { onHoverEnd(); }, [onHoverEnd]);

  const onPaneClick = useCallback(() => { onFocusChange(null); }, [onFocusChange]);

  if (loading) return html`<div className="loading">Computing layout\u2026<div className="loading-sub">${filtered.nodes.length} nodes \u00B7 ${filtered.edges.length} edges</div></div>`;
  return html`
    <${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNodesChange} onEdgesChange=${onEdgesChange}
      onNodeClick=${onNodeClick} onNodeMouseEnter=${onNodeMouseEnter} onNodeMouseLeave=${onNodeMouseLeave}
      onPaneClick=${onPaneClick} nodeTypes=${nodeTypes} className=${flowClassName}
      fitView fitViewOptions=${{ padding: 0.08 }} minZoom=${0.06} maxZoom=${2.5}
      proOptions=${{ hideAttribution: true }}>
      <${Background} gap=${24} size=${1} color=${'#0f1629'} />
      <${Controls} />
      <${MiniMap} nodeColor=${n => n.data?.color || '#64748b'} maskColor=${'rgba(8,12,22,0.85)'} style=${{ borderRadius: 6 }} />
    </${ReactFlow}>`;
}

// ============================================================
// DATA FLOW VIEW
// ============================================================
function DataFlowView() {
  const [nodes, setNodes, onNC] = useNodesState([]);
  const [edges, setEdges, onEC] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const { fitView } = useReactFlow();
  useEffect(() => {
    const fn = ARCH.flow.nodes.map(n => ({ ...n, type: 'flowNode' }));
    const fe = ARCH.flow.edges.map(e => ({ ...e, type: 'smoothstep', animated: true, style: { stroke: 'rgba(59,130,246,0.35)', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(59,130,246,0.45)', width: 14, height: 14 } }));
    layoutNodes(fn, fe, 'RIGHT', false).then(r => { setNodes(r.nodes); setEdges(fe); setLoading(false); setTimeout(() => fitView({ padding: 0.15, duration: 400 }), 100); });
  }, []);
  if (loading) return html`<div className="loading">Computing layout\u2026</div>`;
  return html`<${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNC} onEdgesChange=${onEC} nodeTypes=${nodeTypes} fitView fitViewOptions=${{ padding: 0.15 }} minZoom=${0.2} maxZoom=${2} proOptions=${{ hideAttribution: true }}><${Background} gap=${24} size=${1} color=${'#0f1629'} /><${Controls} /></${ReactFlow}>`;
}

// ============================================================
// INTEGRATION VIEW
// ============================================================
function IntegrationView() {
  const [nodes, setNodes, onNC] = useNodesState([]);
  const [edges, setEdges, onEC] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const { fitView } = useReactFlow();
  useEffect(() => {
    const fn = ARCH.integration.nodes.map(n => ({ ...n, type: 'integNode' }));
    const fe = ARCH.integration.edges.map(e => ({ ...e, type: 'smoothstep', style: { stroke: 'rgba(139,92,246,0.3)', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(139,92,246,0.35)', width: 14, height: 14 } }));
    layoutNodes(fn, fe, 'RIGHT', false).then(r => { setNodes(r.nodes); setEdges(fe); setLoading(false); setTimeout(() => fitView({ padding: 0.2, duration: 400 }), 100); });
  }, []);
  if (loading) return html`<div className="loading">Computing layout\u2026</div>`;
  return html`<${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNC} onEdgesChange=${onEC} nodeTypes=${nodeTypes} fitView fitViewOptions=${{ padding: 0.2 }} minZoom=${0.3} maxZoom=${2} proOptions=${{ hideAttribution: true }}><${Background} gap=${24} size=${1} color=${'#0f1629'} /><${Controls} /></${ReactFlow}>`;
}

// ============================================================
// DASHBOARD VIEW (static content hoisted, content-visibility via CSS)
// ============================================================
const DASHBOARD_DATA = (() => {
  const d = ARCH.dashboard;
  const cats = Object.entries(d.categories).sort((a, b) => b[1].count - a[1].count);
  const mx = Math.max(...cats.map(c => c[1].count));
  let withRecords = 0;
  let totalRecordNum = 0;
  for (const n of ARCH.graph.nodes) {
    const r = n.data.records;
    if (r && r !== '\u2014') {
      withRecords++;
      const num = parseInt(r.replace(/[^0-9]/g, ''));
      if (!isNaN(num)) totalRecordNum += num;
    }
  }
  const totalRecordStr = totalRecordNum > 1000000
    ? (totalRecordNum / 1000000).toFixed(1) + 'M'
    : totalRecordNum > 1000
      ? Math.round(totalRecordNum / 1000) + 'K'
      : String(totalRecordNum);
  const topRels = [...ARCH.graph.nodes].sort((a, b) => (b.data.relCount || 0) - (a.data.relCount || 0)).slice(0, 8);
  const relTypes = new Map();
  for (const e of ARCH.graph.edges) {
    const lbl = e.label || (e.data && e.data.label) || 'unlabeled';
    relTypes.set(lbl, (relTypes.get(lbl) || 0) + 1);
  }
  const topRelTypes = [...relTypes.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10);
  return { d, cats, mx, withRecords, totalRecordStr, topRels, topRelTypes };
})();

function DashboardView() {
  const { d, cats, mx, withRecords, totalRecordStr, topRels, topRelTypes } = DASHBOARD_DATA;

  return html`<div className="dash-grid">
    <div className="dash-card"><h3>System Overview</h3>
      <div style=${{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div><div className="stat-big">${d.totalEntities}</div><div className="stat-label">Entities</div></div>
        <div><div className="stat-big">${d.totalProperties}</div><div className="stat-label">Properties</div></div>
        <div><div className="stat-big">${d.totalRelationships}</div><div className="stat-label">Relationships</div></div>
        <div><div className="stat-big">${totalRecordStr}</div><div className="stat-label">Total Records</div></div>
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

// ============================================================
// DETAIL PANEL with nav history (O(1) edge lookups)
// ============================================================
function DetailPanel({ data, onClose, onNavigateToEntity, navHistory, onBack }) {
  const panelRef = useRef(null);

  // O(1) lookup by label -> id
  const nodeId = useMemo(() => {
    for (const [id, d] of DATA_BY_ID) {
      if (d.label === data.label) return id;
    }
    return data.label;
  }, [data.label]);

  // O(1) edge lookups from pre-built index
  const outE = useMemo(() => EDGE_INDEX.bySource.get(nodeId) || [], [nodeId]);
  const inE = useMemo(() => EDGE_INDEX.byTarget.get(nodeId) || [], [nodeId]);
  const [openGroups, setOpenGroups] = useState(new Set(['outgoing', 'incoming']));

  useEffect(() => { if (panelRef.current) panelRef.current.scrollTop = 0; }, [data.label]);

  const toggleGroup = useCallback(g => {
    setOpenGroups(prev => { const n = new Set(prev); if (n.has(g)) n.delete(g); else n.add(g); return n; });
  }, []);

  // Group edges by label — combined iteration
  const groupByLabel = useCallback((edges, isOutgoing) => {
    const groups = new Map();
    for (const e of edges) {
      const lbl = e.label || (e.data && e.data.label) || 'related';
      if (!groups.has(lbl)) groups.set(lbl, []);
      groups.get(lbl).push(isOutgoing ? e.target : e.source);
    }
    return [...groups.entries()].sort((a, b) => b[1].length - a[1].length);
  }, []);

  const outGroups = useMemo(() => groupByLabel(outE, true), [outE, groupByLabel]);
  const inGroups = useMemo(() => groupByLabel(inE, false), [inE, groupByLabel]);

  return html`<div className="detail-panel" ref=${panelRef}>
    ${navHistory.length > 1 ? html`<div className="nav-history">
      <button className="nav-history-btn" onClick=${onBack} title="Go back">${'\u2190'}</button>
      ${navHistory.map((h, i) => html`<${React_Fragment} key=${i}>
        ${i > 0 ? html`<span className="nav-sep">${'\u203A'}</span>` : null}
        <span className=${'nav-crumb' + (i === navHistory.length - 1 ? ' current' : '')}
          onClick=${() => i < navHistory.length - 1 && onNavigateToEntity(h.id)}>${h.label}</span>
      </${React_Fragment}>`)}
    </div>` : null}
    <div className="detail-hdr">
      <div style=${{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div>
          <div style=${{ fontSize: '16px', fontWeight: 600, marginBottom: '4px' }}>${data.label}</div>
          <div style=${{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <div style=${{ width: 8, height: 8, borderRadius: 2, background: data.color }}></div>
            <span style=${{ fontSize: '11px', color: 'var(--text-3)' }}>${data.category}</span>
            ${data.relCount > 0 ? html`<span style=${{ fontSize: '10px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', marginLeft: '4px' }}>${data.relCount} rels</span>` : null}
          </div>
        </div>
        <button onClick=${onClose} style=${{ background: 'none', border: 'none', color: 'var(--text-3)', cursor: 'pointer', fontSize: '18px', lineHeight: 1 }}>${'\u00D7'}</button>
      </div>
      ${data.description ? html`<p style=${{ fontSize: '11px', color: 'var(--text-2)', marginTop: '10px', lineHeight: 1.5 }}>${data.description}</p>` : null}
    </div>
    <div className="detail-sec"><div className="detail-sec-title">Overview</div>
      <div style=${{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Records</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.records || '\u2014'}</div></div>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Properties</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.propCount}</div></div>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Connections</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.relCount || 0}</div></div>
      </div>
    </div>
    ${data.sources && data.sources.length > 0 ? html`<div className="detail-sec"><div className="detail-sec-title">Sources</div><div style=${{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>${data.sources.map(s => html`<span className="detail-badge" style=${{ background: 'rgba(59,130,246,.12)', color: '#93c5fd' }} key=${s}>${s}</span>`)}</div></div>` : null}
    ${data.storage && data.storage.length > 0 ? html`<div className="detail-sec"><div className="detail-sec-title">Storage</div><div style=${{ display: 'flex', flexDirection: 'column', gap: '3px' }}>${data.storage.map(s => html`<div className="mono" style=${{ fontSize: '10px', color: 'var(--text-2)' }} key=${s}>${s}</div>`)}</div></div>` : null}
    ${(outE.length > 0 || inE.length > 0) ? html`<div className="detail-sec"><div className="detail-sec-title">Relationships (${outE.length + inE.length})</div>
      ${outGroups.length > 0 ? html`<div className="rel-group">
        <div className="rel-group-header" onClick=${() => toggleGroup('outgoing')}>
          <span className=${'rel-group-chevron' + (openGroups.has('outgoing') ? ' open' : '')}>${'\u25B6'}</span>
          <span style=${{ fontSize: '9px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', letterSpacing: '.1em' }}>OUTGOING (${outE.length})</span>
        </div>
        ${openGroups.has('outgoing') ? outGroups.map(([lbl, targets]) => html`<div key=${lbl} style=${{ marginLeft: '12px', marginBottom: '6px' }}>
          <div style=${{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}><span className="rel-label">${lbl}</span><span className="rel-group-count">${targets.length}</span></div>
          ${targets.map(t => html`<div className="rel-item" key=${t} style=${{ marginLeft: '8px', cursor: 'pointer' }} onClick=${() => onNavigateToEntity(t)}><span className="rel-arrow">${'\u2192'}</span><span className="rel-target" style=${{ borderBottom: '1px dotted var(--border-1)' }}>${LABEL_BY_ID.get(t) || t}</span></div>`)}
        </div>`) : null}
      </div>` : null}
      ${inGroups.length > 0 ? html`<div className="rel-group">
        <div className="rel-group-header" onClick=${() => toggleGroup('incoming')}>
          <span className=${'rel-group-chevron' + (openGroups.has('incoming') ? ' open' : '')}>${'\u25B6'}</span>
          <span style=${{ fontSize: '9px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', letterSpacing: '.1em' }}>INCOMING (${inE.length})</span>
        </div>
        ${openGroups.has('incoming') ? inGroups.map(([lbl, sources]) => html`<div key=${lbl} style=${{ marginLeft: '12px', marginBottom: '6px' }}>
          <div style=${{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}><span className="rel-label">${lbl}</span><span className="rel-group-count">${sources.length}</span></div>
          ${sources.map(s => html`<div className="rel-item" key=${s} style=${{ marginLeft: '8px', cursor: 'pointer' }} onClick=${() => onNavigateToEntity(s)}><span className="rel-arrow">${'\u2190'}</span><span className="rel-target" style=${{ borderBottom: '1px dotted var(--border-1)' }}>${LABEL_BY_ID.get(s) || s}</span></div>`)}
        </div>`) : null}
      </div>` : null}
    </div>` : null}
    ${data.properties && data.properties.length > 0 ? html`<div className="detail-sec"><div className="detail-sec-title">Schema (${data.properties.length})</div>
      <div style=${{ maxHeight: '350px', overflowY: 'auto' }}>
        ${data.properties.map(p => html`<div className="detail-prop-row" key=${p.name}>
          <span className="detail-prop-name">${p.name}</span>
          <span className="detail-prop-type">${p.type}</span>
          <span className="detail-prop-note" title=${p.note || ''}>${p.note || ''}</span>
        </div>`)}
      </div>
    </div>` : null}
  </div>`;
}

// ============================================================
// CATEGORY SIDEBAR with search results
// ============================================================
function CategorySidebar({ activeCategories, onToggle, searchQuery, onSearchChange, useGrouped, onToggleGrouped, searchMatches, onSearchResultClick }) {
  const allOn = activeCategories.size === CAT_KEYS.length;
  return html`<div className="cat-sidebar">
    <div className="cat-sidebar-hdr">
      <div className="cat-sidebar-title">Filter</div>
      <div style=${{ marginTop: '8px', position: 'relative' }}>
        <input className="search-input" placeholder=${'Search entities\u2026'} value=${searchQuery} onInput=${e => onSearchChange(e.target.value)} />
        ${searchQuery ? html`<span className="search-count" style=${{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)' }}>${searchMatches.length}</span>` : null}
      </div>
      ${searchQuery && searchMatches.length > 0 ? html`<div className="search-results">
        ${searchMatches.slice(0, 12).map(n => html`<div className="search-result-item" key=${n.id} onClick=${() => onSearchResultClick(n.id)}>
          <div className="sr-dot" style=${{ background: n.data.color }}></div>
          <span className="sr-name">${n.data.label}</span>
          <span className="sr-cat">${n.data.category.split(' ')[0]}</span>
          <span className="sr-rels">${n.data.relCount}r</span>
        </div>`)}
        ${searchMatches.length > 12 ? html`<div style=${{ padding: '6px 10px', fontSize: '10px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', textAlign: 'center' }}>+${searchMatches.length - 12} more</div>` : null}
      </div>` : null}
      <div style=${{ display: 'flex', gap: '6px', marginTop: '8px' }}>
        <button className="toolbar-btn" onClick=${() => onToggle('__ALL__')}>${allOn ? 'Hide All' : 'Show All'}</button>
        <button className=${'toolbar-btn' + (useGrouped ? ' active' : '')} onClick=${onToggleGrouped}>Grouped</button>
      </div>
    </div>
    ${Object.entries(CATEGORIES).map(([n, i]) => html`<div className=${'cat-toggle' + (activeCategories.has(n) ? '' : ' off')} key=${n} onClick=${() => onToggle(n)}><div className="cat-toggle-dot" style=${{ background: i.color }}></div><span className="cat-toggle-label">${n}</span><span className="cat-toggle-count">${i.count}</span></div>`)}
  </div>`;
}

// ============================================================
// EXPORT UTILITY
// ============================================================
function exportArchData() {
  const blob = new Blob([JSON.stringify(ARCH, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = 'pts_architecture_data.json'; a.click();
  URL.revokeObjectURL(url);
}

// Fake React.Fragment for htm
const React_Fragment = ({ children }) => children;

// ============================================================
// DEBOUNCE HOOK
// ============================================================
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => { setDebouncedValue(value); }, delay);
    return () => { clearTimeout(timer); };
  }, [value, delay]);
  return debouncedValue;
}

// ============================================================
// MAIN APP
// ============================================================
function App() {
  const [tab, setTab] = useState('graph');
  const [sel, setSel] = useState(null);
  const [sq, setSq] = useState('');
  const [ac, setAc] = useState(() => new Set(CAT_KEYS));
  const [grouped, setGrouped] = useState(true);
  const [focusId, setFocusId] = useState(null);
  const [navHistory, setNavHistory] = useState([]);
  const [hoverData, setHoverData] = useState(null);
  const [hoverPos, setHoverPos] = useState(null);
  const [showPerf, setShowPerf] = useState(false);

  // Debounce search by 150ms to avoid re-layout during typing
  const debouncedSq = useDebounce(sq, 150);

  const toggleCat = useCallback(cat => {
    setAc(prev => {
      if (cat === '__ALL__') {
        return prev.size === CAT_KEYS.length ? new Set() : new Set(CAT_KEYS);
      }
      const n = new Set(prev);
      if (n.has(cat)) { n.delete(cat); } else { n.add(cat); }
      return n;
    });
  }, []);

  // Search matches using pre-computed search index — combined iteration
  const searchMatches = useMemo(() => {
    if (!debouncedSq) return [];
    const q = debouncedSq.toLowerCase();
    const results = [];
    for (const entry of SEARCH_INDEX) {
      if (!ac.has(entry.node.data.category)) continue;
      if (entry.labelLower.includes(q) || entry.categoryLower.includes(q) || entry.descLower.includes(q)) {
        results.push(entry.node);
      }
    }
    results.sort((a, b) => (b.data.relCount || 0) - (a.data.relCount || 0));
    return results;
  }, [debouncedSq, ac]);

  // Navigate to entity — functional setState
  const navigateToEntity = useCallback(entityId => {
    const node = NODES_BY_ID.get(entityId);
    if (node) {
      setSel(node.data);
      setFocusId(entityId);
      setNavHistory(prev => {
        const existingIdx = prev.findIndex(h => h.id === entityId);
        if (existingIdx >= 0) return prev.slice(0, existingIdx + 1);
        return [...prev, { id: entityId, label: node.data.label }];
      });
    }
  }, []);

  // Back button — functional setState
  const goBack = useCallback(() => {
    setNavHistory(prev => {
      if (prev.length <= 1) return prev;
      const newHist = prev.slice(0, -1);
      const target = newHist[newHist.length - 1];
      const node = NODES_BY_ID.get(target.id);
      if (node) { setSel(node.data); setFocusId(target.id); }
      return newHist;
    });
  }, []);

  // Handle initial node selection from graph click — functional setState
  const handleSelectNode = useCallback((data) => {
    setSel(data);
    // O(1) lookup for node ID by label
    let nodeId = null;
    for (const [id, d] of DATA_BY_ID) {
      if (d.label === data.label) { nodeId = id; break; }
    }
    if (nodeId) {
      setNavHistory(prev => {
        if (prev.length > 0 && prev[prev.length - 1].id === nodeId) return prev;
        return [{ id: nodeId, label: data.label }];
      });
    }
  }, []);

  // Search result click
  const handleSearchResultClick = useCallback(entityId => {
    navigateToEntity(entityId);
    setSq('');
  }, [navigateToEntity]);

  // Hover handlers — stable callbacks
  const handleHoverNode = useCallback((data, pos) => {
    setSel(prev => {
      if (!prev) { setHoverData(data); setHoverPos(pos); }
      return prev;
    });
  }, []);
  const handleHoverEnd = useCallback(() => { setHoverData(null); setHoverPos(null); }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      // Ctrl+P toggles performance overlay
      if (e.key === 'p' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        setShowPerf(prev => !prev);
        return;
      }
      if (e.key === 'Escape') {
        setSel(null); setFocusId(null); setSq(''); setNavHistory([]); setHoverData(null);
      }
      if (e.key === '/' && !e.ctrlKey && !e.metaKey && document.activeElement?.tagName !== 'INPUT') {
        e.preventDefault(); document.querySelector('.search-input')?.focus();
      }
      if (e.key === 'Backspace' && document.activeElement?.tagName !== 'INPUT') {
        setNavHistory(prev => {
          if (prev.length <= 1) return prev;
          e.preventDefault();
          const newHist = prev.slice(0, -1);
          const target = newHist[newHist.length - 1];
          const node = NODES_BY_ID.get(target.id);
          if (node) { setSel(node.data); setFocusId(target.id); }
          return newHist;
        });
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // Static tabs array hoisted out of render
  const tabs = useMemo(() => [
    { id: 'graph', label: 'Entity Graph' },
    { id: 'flow', label: 'Data Flow' },
    { id: 'integration', label: 'Integrations' },
    { id: 'dashboard', label: 'Dashboard' }
  ], []);

  // Stable tab click handler
  const handleTabClick = useCallback(tabId => {
    setTab(tabId);
    setSel(null);
    setFocusId(null);
    setNavHistory([]);
  }, []);

  // Stable focus change handler
  const handleFocusChange = useCallback(id => {
    setFocusId(id);
    if (!id) { setSel(null); setNavHistory([]); }
  }, []);

  // Stable grouped toggle
  const handleToggleGrouped = useCallback(() => {
    setGrouped(prev => !prev);
  }, []);

  // Stable close handler
  const handleCloseDetail = useCallback(() => {
    setSel(null); setFocusId(null); setNavHistory([]);
  }, []);

  return html`<div style=${{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
    <div className="top-bar">
      <span className="top-bar-title">PTS Data Architecture</span>
      <span className="top-bar-ver">V7C</span>
      <div style=${{ width: 1, height: 20, background: 'var(--border-0)' }}></div>
      <div style=${{ display: 'flex', gap: 0 }}>${tabs.map(t => html`<button key=${t.id} className=${'tab-btn' + (tab === t.id ? ' active' : '')} onClick=${() => handleTabClick(t.id)}>${t.label}</button>`)}</div>
      <div style=${{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '12px' }}>
        ${focusId ? html`<span className="mono" style=${{ fontSize: '10px', color: 'var(--cyan)', background: 'rgba(34,211,238,.08)', padding: '2px 8px', borderRadius: '3px' }}>Focus: ${LABEL_BY_ID.get(focusId) || focusId}</span>` : null}
        <button className="toolbar-btn" onClick=${exportArchData} title="Export architecture data as JSON" style=${{ fontSize: '9px' }}>${'\u2B07'} Export</button>
        <span className="mono" style=${{ fontSize: '10px', color: 'var(--text-3)' }}>${ARCH.dashboard.totalEntities} entities ${'\u00B7'} ${ARCH.dashboard.totalRelationships} rels ${'\u00B7'} ${ARCH.dashboard.totalProperties} props</span>
      </div>
    </div>
    <div style=${{ display: 'flex', flex: 1, overflow: 'hidden' }}>
      ${tab === 'graph' ? html`<${CategorySidebar} activeCategories=${ac} onToggle=${toggleCat} searchQuery=${sq} onSearchChange=${setSq} useGrouped=${grouped} onToggleGrouped=${handleToggleGrouped} searchMatches=${searchMatches} onSearchResultClick=${handleSearchResultClick} />` : null}
      <div style=${{ flex: 1, position: 'relative' }}>
        ${tab === 'graph' ? html`<${ReactFlowProvider}><${EntityGraphView} onSelectNode=${handleSelectNode} activeCategories=${ac} debouncedSearch=${debouncedSq} useGrouped=${grouped} focusNodeId=${focusId} onFocusChange=${handleFocusChange} onHoverNode=${handleHoverNode} onHoverEnd=${handleHoverEnd} /></${ReactFlowProvider}>` : null}
        ${tab === 'flow' ? html`<${ReactFlowProvider}><${DataFlowView} /></${ReactFlowProvider}>` : null}
        ${tab === 'integration' ? html`<${ReactFlowProvider}><${IntegrationView} /></${ReactFlowProvider}>` : null}
        ${tab === 'dashboard' ? html`<${DashboardView} />` : null}
      </div>
      ${sel && tab === 'graph' ? html`<${DetailPanel} data=${sel} onClose=${handleCloseDetail} onNavigateToEntity=${navigateToEntity} navHistory=${navHistory} onBack=${goBack} />` : null}
    </div>
    ${hoverData && !sel ? html`<${HoverTooltip} nodeData=${hoverData} position=${hoverPos} />` : null}
    ${tab === 'graph' ? html`<div className="kb-hint"><span><span className="kb-key">Esc</span> Clear</span><span><span className="kb-key">/</span> Search</span><span><span className="kb-key">Click</span> Focus</span>${navHistory.length > 1 ? html`<span><span className="kb-key">${'\u232B'}</span> Back</span>` : null}<span><span className="kb-key">Ctrl+P</span> Perf</span><span><span className="kb-key">Scroll</span> Zoom</span></div>` : null}
    <${PerfOverlay} visible=${showPerf} nodeCount=${ARCH.graph.nodes.length} edgeCount=${ARCH.graph.edges.length} />
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
<title>PTS Data Architecture Explorer V7C</title>
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

outpath = os.path.join(BASE, 'PTS_DATA_ARCHITECTURE_EXPLORER_V7C.html')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"V7C written: {len(output):,} chars ({len(output)//1024}KB)")
