#!/usr/bin/env python3
"""Generate PTS Data Architecture Explorer V8 — Hybrid combining Zustand store, undo/redo,
performance optimizations, and UI/UX polish from V7A-V7D."""
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

# ============================================================
# CSS — merged from V6.4 base + V7C perf + V7D UX enhancements
# ============================================================
CSS = r"""
:root{--bg-0:#080c16;--bg-1:#0f1629;--bg-2:#161d33;--bg-3:#1c2540;--border-0:#1a2236;--border-1:#263049;--border-2:#334155;--text-0:#f1f5f9;--text-1:#cbd5e1;--text-2:#94a3b8;--text-3:#64748b;--cyan:#22d3ee;--blue:#3b82f6;--transition-fast:150ms;--transition-normal:200ms;--transition-slow:300ms;--transition-slower:400ms}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Space Grotesk',sans-serif;background:var(--bg-0);color:var(--text-0);overflow:hidden}
.mono{font-family:'JetBrains Mono',monospace}
#root{width:100vw;height:100vh}

/* ===== Accessibility (V7D) ===== */
:focus-visible{outline:2px solid var(--cyan);outline-offset:2px;border-radius:2px}
[role="button"]:focus-visible,.toolbar-btn:focus-visible,.tab-btn:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}
@media (prefers-reduced-motion: reduce){
  *,*::before,*::after{animation-duration:0.01ms !important;animation-iteration-count:1 !important;transition-duration:0.01ms !important;scroll-behavior:auto !important}
}
.high-contrast{--bg-0:#000;--bg-1:#0a0a0a;--bg-2:#141414;--bg-3:#1e1e1e;--border-0:#333;--border-1:#555;--border-2:#777;--text-0:#fff;--text-1:#eee;--text-2:#ccc;--text-3:#aaa;--cyan:#00ffff;--blue:#5599ff}

/* ===== Keyframe Animations (V7D — all 21) ===== */
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes pulse-glow{0%,100%{box-shadow:0 0 0 rgba(34,211,238,0)}50%{box-shadow:0 0 20px rgba(34,211,238,.15)}}
@keyframes slide-in-right{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}
@keyframes slide-out-right{from{transform:translateX(0);opacity:1}to{transform:translateX(100%);opacity:0}}
@keyframes fade-in{from{opacity:0}to{opacity:1}}
@keyframes fade-out{from{opacity:1}to{opacity:0}}
@keyframes count-up{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
@keyframes selection-ring{0%{border-color:var(--cyan)}50%{border-color:rgba(34,211,238,.3)}100%{border-color:var(--cyan)}}
@keyframes stagger-in{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}
@keyframes node-select-pulse{0%{transform:scale(1)}50%{transform:scale(1.03)}100%{transform:scale(1)}}
@keyframes skeleton-shimmer{0%{background-position:-200% 0}100%{background-position:200% 0}}
@keyframes slide-down{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}
@keyframes check-draw{0%{stroke-dashoffset:20}100%{stroke-dashoffset:0}}
@keyframes bounce-once{0%,100%{transform:translateY(0)}30%{transform:translateY(-4px)}60%{transform:translateY(2px)}}
@keyframes particle-flow{0%{stroke-dashoffset:24}100%{stroke-dashoffset:0}}
@keyframes pulse-connection{0%,100%{box-shadow:0 0 0 rgba(139,92,246,0)}50%{box-shadow:0 0 16px rgba(139,92,246,.3)}}
@keyframes cmd-overlay-in{from{opacity:0}to{opacity:1}}
@keyframes cmd-panel-in{from{opacity:0;transform:translateY(-20px) scale(0.97)}to{opacity:1;transform:translateY(0) scale(1)}}
@keyframes toast-in{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}
@keyframes toast-out{from{transform:translateX(0);opacity:1}to{transform:translateX(100%);opacity:0}}
@keyframes breadcrumb-slide{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:translateX(0)}}

/* ===== React Flow ===== */
.react-flow{background:var(--bg-0)!important}
.react-flow__minimap{background:var(--bg-1)!important;border:1px solid var(--border-0)!important;border-radius:6px!important}
.react-flow__controls{border:1px solid var(--border-0)!important;border-radius:6px!important;overflow:hidden}
.react-flow__controls-button{background:var(--bg-1)!important;border-bottom:1px solid var(--border-0)!important;fill:var(--text-3)!important;transition:background var(--transition-fast),fill var(--transition-fast)}
.react-flow__controls-button:hover{background:var(--bg-2)!important;fill:var(--text-0)!important}
.react-flow__attribution{display:none!important}
.react-flow__edge-text{fill:transparent!important;font-size:8px!important;font-family:'JetBrains Mono',monospace!important;transition:fill var(--transition-normal)}
.react-flow__edge-textbg{fill:transparent!important;transition:fill var(--transition-normal)}
.react-flow__edge:hover .react-flow__edge-text{fill:var(--cyan)!important}
.react-flow__edge:hover .react-flow__edge-textbg{fill:var(--bg-0)!important;fill-opacity:0.95!important}
.react-flow__edge path{transition:stroke var(--transition-normal),stroke-width var(--transition-normal)}
.react-flow__edge:hover path{stroke:rgba(34,211,238,0.55)!important;stroke-width:2.5!important}

/* Focus mode — state-driven via node className prop (V7C smooth transitions via V7D vars) */
.react-flow.focus-active .react-flow__node.dimmed{opacity:.12!important;filter:saturate(0.2)!important;transition:opacity var(--transition-slower),filter var(--transition-slower)}
.react-flow.focus-active .react-flow__edge.dimmed path{stroke:rgba(148,163,184,0.04)!important;transition:stroke var(--transition-slower)}
.react-flow.focus-active .react-flow__edge.dimmed .react-flow__edge-text{fill:transparent!important}
.react-flow.focus-active .react-flow__node.highlighted{opacity:1!important;filter:none!important;transition:opacity var(--transition-slower)}
.react-flow.focus-active .react-flow__edge.highlighted path{stroke:rgba(34,211,238,0.5)!important;stroke-width:2!important;transition:stroke var(--transition-slower)}
.react-flow.focus-active .react-flow__edge.highlighted .react-flow__edge-text{fill:var(--cyan)!important}
.react-flow.focus-active .react-flow__edge.highlighted .react-flow__edge-textbg{fill:var(--bg-0)!important;fill-opacity:0.9!important}

/* Search highlight — state-driven via node className prop */
.react-flow.search-active .react-flow__node.search-match{box-shadow:0 0 0 2px var(--cyan),0 0 20px rgba(34,211,238,.25)!important;border-radius:5px}
.react-flow.search-active .react-flow__node:not(.search-match){opacity:.2!important;filter:saturate(0.15)!important;transition:opacity var(--transition-slow),filter var(--transition-slow)}
.react-flow.search-active .react-flow__edge path{stroke:rgba(148,163,184,0.05)!important}

/* ===== Entity Node (V7D: gradient headers, glow, selection ring) ===== */
.entity-node{border-radius:5px;overflow:hidden;font-size:11px;cursor:pointer;transition:all .25s ease;border:1px solid transparent;min-width:190px;background:var(--bg-2)}
.entity-node:hover{transform:translateY(-1px);border-color:rgba(34,211,238,.25);box-shadow:0 4px 24px rgba(0,0,0,.5),0 0 30px rgba(34,211,238,.08);animation:pulse-glow 2s ease-in-out infinite}
.entity-node.selected{border-color:var(--cyan)!important;box-shadow:0 0 0 1px var(--cyan),0 4px 30px rgba(34,211,238,.15)!important;animation:node-select-pulse .3s ease-out,selection-ring 1.5s ease-in-out infinite}
.entity-header{padding:7px 10px;display:flex;justify-content:space-between;align-items:center;gap:6px}
.entity-header .name{color:#fff;font-weight:600;font-size:11.5px;letter-spacing:.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1}
.entity-header .cat-emoji{font-size:12px;flex-shrink:0;margin-right:2px}
.record-badge{background:rgba(0,0,0,.35);color:rgba(255,255,255,.75);padding:2px 7px;border-radius:3px;font-size:9px;font-family:'JetBrains Mono',monospace;font-weight:500;flex-shrink:0}
.entity-body{padding:4px 10px 6px;display:flex;align-items:center;gap:6px;background:rgba(0,0,0,.12)}
.cat-ind{width:3px;height:14px;border-radius:1px;flex-shrink:0;opacity:.65}
.entity-cat{color:var(--text-3);font-size:9px;letter-spacing:.05em;text-transform:uppercase;flex:1}
.prop-ct{color:var(--text-3);font-size:9px;font-family:'JetBrains Mono',monospace}
.rel-ct{color:var(--text-3);font-size:8px;font-family:'JetBrains Mono',monospace;background:rgba(34,211,238,.08);padding:1px 4px;border-radius:2px;margin-left:2px}

/* Inner shadow for depth (V7D) */
.entity-node::after{content:'';position:absolute;inset:0;border-radius:5px;box-shadow:inset 0 1px 0 rgba(255,255,255,.04),inset 0 -1px 0 rgba(0,0,0,.15);pointer-events:none}

/* ===== Flow / Integration Nodes (V7D transitions) ===== */
.flow-node{border-radius:5px;overflow:hidden;font-size:11px;border:1px solid rgba(255,255,255,.06);transition:box-shadow var(--transition-normal)}
.flow-inner{padding:10px 14px;text-align:center}
.flow-label{color:var(--text-0);font-weight:600;font-size:11px}
.flow-sub{color:var(--text-3);font-size:9px;margin-top:3px}
.integ-node{padding:12px 16px;text-align:center;font-size:11px;border:1px solid rgba(255,255,255,.06);border-radius:5px;transition:box-shadow var(--transition-normal)}
.integ-node.pulse-active{animation:pulse-connection 2s ease-in-out infinite}

/* Data flow animated edges (V7D) */
.react-flow__edge.animated-flow path{stroke-dasharray:8 4;animation:particle-flow 1.2s linear infinite}

/* ===== Dashboard (V7C content-visibility + V7D fade-in stagger) ===== */
.dash-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;padding:24px;overflow-y:auto;align-content:start;height:100%}
.dash-card{background:var(--bg-1);border:1px solid var(--border-0);border-radius:8px;padding:20px;transition:border-color var(--transition-normal);content-visibility:auto;contain-intrinsic-size:0 200px;animation:fade-in .4s ease-out;animation-fill-mode:both}
.dash-card:nth-child(1){animation-delay:0ms}.dash-card:nth-child(2){animation-delay:60ms}.dash-card:nth-child(3){animation-delay:120ms}
.dash-card:nth-child(4){animation-delay:180ms}.dash-card:nth-child(5){animation-delay:240ms}.dash-card:nth-child(6){animation-delay:300ms}.dash-card:nth-child(7){animation-delay:360ms}
.dash-card:hover{border-color:var(--border-1)}
.dash-card h3{font-size:10px;font-weight:600;color:var(--text-3);margin-bottom:14px;text-transform:uppercase;letter-spacing:.12em;font-family:'JetBrains Mono',monospace}
.stat-big{font-size:40px;font-weight:300;font-family:'Space Grotesk',sans-serif;color:var(--cyan);line-height:1}
.stat-big.animate-count{animation:count-up .8s ease-out;animation-fill-mode:both}
.stat-label{font-size:12px;color:var(--text-2);margin-top:4px}
.stat-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border-0);transition:background var(--transition-fast)}
.stat-row:last-child{border-bottom:none}
.stat-row:hover{background:rgba(255,255,255,.02)}
.stat-value{font-size:16px;font-weight:600;font-family:'JetBrains Mono',monospace}
.cat-bar{display:flex;align-items:center;gap:8px;padding:5px 0}
.cat-bar-fill{height:6px;border-radius:1px;transition:width .6s ease-out}
.cat-bar-label{font-size:11px;color:var(--text-1);min-width:120px}
.cat-bar-count{font-size:11px;color:var(--text-3);font-family:'JetBrains Mono',monospace;min-width:24px;text-align:right}

/* ===== Detail Panel (V7D slide-in + V7C content-visibility) ===== */
.detail-panel{width:400px;background:var(--bg-1);border-left:1px solid var(--border-0);overflow-y:auto;flex-shrink:0;animation:slide-in-right var(--transition-slow) ease-out}
.detail-hdr{padding:16px 20px;border-bottom:1px solid var(--border-0);position:sticky;top:0;background:var(--bg-1);z-index:10}
.detail-sec{border-bottom:1px solid var(--border-0);content-visibility:auto;contain-intrinsic-size:0 80px;overflow:hidden;transition:max-height var(--transition-slow) ease,padding var(--transition-slow) ease}
.detail-sec.open{max-height:2000px;padding:14px 20px}
.detail-sec.closed{max-height:0;padding:0 20px}
.detail-sec-title{font-size:9px;font-weight:600;color:var(--text-3);text-transform:uppercase;letter-spacing:.12em;margin-bottom:10px;font-family:'JetBrains Mono',monospace;display:flex;align-items:center;gap:6px;cursor:pointer;user-select:none}
.detail-sec-title:hover{color:var(--text-2)}
.detail-sec-title .sec-chevron{font-size:10px;transition:transform var(--transition-normal);display:inline-block;width:12px}
.detail-sec-title .sec-chevron.open{transform:rotate(90deg)}
.detail-badge{display:inline-block;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:500;margin:2px;color:#fff;font-family:'JetBrains Mono',monospace}
.detail-prop-row{display:grid;grid-template-columns:1fr auto 1fr;gap:8px;align-items:center;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.03);font-size:11px;transition:background var(--transition-fast)}
.detail-prop-row:nth-child(even){background:rgba(255,255,255,.015)}
.detail-prop-row:hover{background:rgba(34,211,238,.04)}
.detail-prop-name{color:var(--cyan);font-weight:500}
.detail-prop-type{color:var(--text-3);font-family:'JetBrains Mono',monospace;font-size:10px;text-align:center}
.detail-prop-note{color:var(--text-3);font-size:9px;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

/* Copy button (V7D) */
.copy-btn{background:none;border:1px solid var(--border-0);color:var(--text-3);cursor:pointer;font-size:10px;padding:2px 6px;border-radius:3px;font-family:'JetBrains Mono',monospace;transition:all var(--transition-fast)}
.copy-btn:hover{border-color:var(--cyan);color:var(--cyan);background:rgba(34,211,238,.06)}
.copy-btn.copied{border-color:#10b981;color:#10b981;background:rgba(16,185,129,.06)}

/* ===== Category Sidebar (V7D transitions + animated checkbox) ===== */
.cat-sidebar{width:240px;background:var(--bg-1);border-right:1px solid var(--border-0);overflow-y:auto;flex-shrink:0;padding:12px 0}
.cat-sidebar-hdr{padding:8px 16px 12px;border-bottom:1px solid var(--border-0);margin-bottom:8px}
.cat-sidebar-title{font-size:9px;font-weight:600;color:var(--text-3);text-transform:uppercase;letter-spacing:.12em;font-family:'JetBrains Mono',monospace}
.cat-toggle{display:flex;align-items:center;gap:8px;padding:6px 16px;cursor:pointer;transition:background var(--transition-fast),opacity var(--transition-normal);user-select:none}
.cat-toggle:hover{background:rgba(255,255,255,.03)}
.cat-toggle-dot{width:8px;height:8px;border-radius:2px;flex-shrink:0;transition:opacity var(--transition-normal),transform var(--transition-fast)}
.cat-toggle-label{font-size:12px;color:var(--text-1);flex:1;transition:opacity var(--transition-normal)}
.cat-toggle-count{font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace;transition:opacity var(--transition-normal)}
.cat-toggle.off .cat-toggle-dot{opacity:.15;transform:scale(0.8)}
.cat-toggle.off .cat-toggle-label{opacity:.35}
.cat-toggle.off .cat-toggle-count{opacity:.25}
.cat-check{width:14px;height:14px;border:1.5px solid var(--border-2);border-radius:3px;flex-shrink:0;display:flex;align-items:center;justify-content:center;transition:all var(--transition-fast)}
.cat-check.on{border-color:var(--cyan);background:rgba(34,211,238,.12)}
.cat-check.on svg{stroke-dasharray:20;animation:check-draw .25s ease-out forwards}

/* ===== Search (V7D enhanced with stagger + keyboard nav) ===== */
.search-input{background:var(--bg-0);border:1px solid var(--border-0);color:var(--text-0);padding:7px 12px;border-radius:4px;font-size:12px;width:100%;outline:none;font-family:'Space Grotesk',sans-serif;transition:border-color var(--transition-normal),box-shadow var(--transition-normal)}
.search-input:focus{border-color:var(--cyan);box-shadow:0 0 0 3px rgba(34,211,238,.08)}
.search-input::placeholder{color:var(--text-3)}

.search-results{margin-top:6px;max-height:260px;overflow-y:auto;border:1px solid var(--border-0);border-radius:4px;background:var(--bg-0);animation:slide-down var(--transition-normal) ease-out}
.search-result-item{display:flex;align-items:center;gap:8px;padding:6px 10px;cursor:pointer;transition:background var(--transition-fast);border-bottom:1px solid var(--border-0);animation:stagger-in var(--transition-normal) ease-out;animation-fill-mode:both}
.search-result-item:nth-child(1){animation-delay:0ms}.search-result-item:nth-child(2){animation-delay:30ms}
.search-result-item:nth-child(3){animation-delay:60ms}.search-result-item:nth-child(4){animation-delay:90ms}
.search-result-item:nth-child(5){animation-delay:120ms}.search-result-item:nth-child(6){animation-delay:150ms}
.search-result-item:nth-child(7){animation-delay:180ms}.search-result-item:nth-child(8){animation-delay:210ms}
.search-result-item:nth-child(9){animation-delay:240ms}.search-result-item:nth-child(10){animation-delay:270ms}
.search-result-item:nth-child(11){animation-delay:300ms}.search-result-item:nth-child(12){animation-delay:330ms}
.search-result-item:last-child{border-bottom:none}
.search-result-item:hover,.search-result-item.kb-active{background:rgba(34,211,238,.06)}
.search-result-item .sr-dot{width:6px;height:6px;border-radius:2px;flex-shrink:0}
.search-result-item .sr-name{font-size:11px;color:var(--text-0);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.search-result-item .sr-cat{font-size:9px;color:var(--text-3);font-family:'JetBrains Mono',monospace}
.search-result-item .sr-rels{font-size:9px;color:var(--text-3);font-family:'JetBrains Mono',monospace}
.search-result-item .sr-preview{display:none;position:absolute;left:100%;top:0;width:220px;padding:8px 12px;background:var(--bg-2);border:1px solid var(--border-1);border-radius:4px;font-size:10px;color:var(--text-2);z-index:10}
.search-result-item:hover .sr-preview{display:block}

/* Recent searches (V7D) */
.recent-searches{margin-top:6px;border:1px solid var(--border-0);border-radius:4px;background:var(--bg-0);animation:slide-down var(--transition-normal) ease-out}
.recent-search-label{font-size:9px;color:var(--text-3);padding:6px 10px 2px;font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.1em}
.recent-search-item{padding:5px 10px;font-size:11px;color:var(--text-2);cursor:pointer;transition:background var(--transition-fast);display:flex;align-items:center;gap:6px}
.recent-search-item:hover{background:rgba(34,211,238,.06);color:var(--text-0)}
.recent-search-item .rs-icon{color:var(--text-3);font-size:10px}

/* ===== Nav History / Breadcrumbs (V7D animated) ===== */
.nav-history{display:flex;align-items:center;gap:4px;padding:8px 20px;background:var(--bg-2);border-bottom:1px solid var(--border-0);font-size:10px}
.nav-history-btn{background:none;border:none;color:var(--text-3);cursor:pointer;font-family:'JetBrains Mono',monospace;font-size:10px;padding:2px 6px;border-radius:3px;transition:all var(--transition-fast)}
.nav-history-btn:hover{color:var(--cyan);background:rgba(34,211,238,.06)}
.nav-crumb{color:var(--text-3);cursor:pointer;padding:1px 6px;border-radius:3px;transition:all var(--transition-fast);animation:breadcrumb-slide var(--transition-normal) ease-out}
.nav-crumb:hover{color:var(--cyan);background:rgba(34,211,238,.06)}
.nav-crumb.current{color:var(--text-0);font-weight:500}
.nav-sep{color:var(--border-2);font-size:9px}

/* ===== Top Bar ===== */
.top-bar{height:48px;background:var(--bg-1);border-bottom:1px solid var(--border-0);display:flex;align-items:center;padding:0 20px;gap:16px;flex-shrink:0}
.top-bar-title{font-size:13px;font-weight:600;letter-spacing:.04em}
.top-bar-ver{font-size:10px;color:var(--cyan);font-family:'JetBrains Mono',monospace;background:rgba(34,211,238,.06);padding:2px 8px;border-radius:3px;border:1px solid rgba(34,211,238,.12)}

/* Tab buttons (V7D crossfade indicator) */
.tab-btn{padding:6px 14px;font-size:11px;cursor:pointer;border:none;background:0 0;color:var(--text-3);font-family:'Space Grotesk',sans-serif;font-weight:500;letter-spacing:.02em;border-bottom:2px solid transparent;transition:all var(--transition-normal);height:48px;display:flex;align-items:center}
.tab-btn:hover{color:var(--text-2);background:rgba(255,255,255,.02)}
.tab-btn.active{color:var(--cyan);border-bottom-color:var(--cyan)}

/* Tab content crossfade (V7D) */
.tab-content{animation:fade-in var(--transition-normal) ease-out}

/* ===== Micro-interactions (V7D) ===== */
.toolbar-btn{padding:3px 10px;border-radius:3px;font-size:10px;cursor:pointer;border:1px solid var(--border-0);background:var(--bg-0);color:var(--text-3);font-family:'JetBrains Mono',monospace;transition:all var(--transition-fast);position:relative;overflow:hidden}
.toolbar-btn::before{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,.03),transparent);transform:translateX(-100%);transition:transform var(--transition-normal)}
.toolbar-btn:hover{border-color:var(--border-1);color:var(--text-2)}
.toolbar-btn:hover::before{transform:translateX(100%)}
.toolbar-btn:active{transform:scale(0.97)}
.toolbar-btn.active{border-color:var(--cyan);color:var(--cyan);background:rgba(34,211,238,.06)}
.toolbar-btn.bounce-icon .btn-icon{animation:bounce-once .5s ease-out}

.search-count{font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace;padding:2px 8px;background:rgba(34,211,238,.06);border-radius:3px}

/* ===== Relationship items (V7D hover) ===== */
.rel-item{display:flex;align-items:center;gap:6px;padding:3px 4px;font-size:11px;transition:background var(--transition-fast);border-radius:3px}
.rel-item:hover{background:rgba(34,211,238,.04)}
.rel-arrow{color:var(--text-3);font-size:10px}
.rel-label{color:var(--cyan);font-family:'JetBrains Mono',monospace;font-size:10px}
.rel-target{color:var(--text-1)}
.rel-group{margin-bottom:10px}
.rel-group-header{display:flex;align-items:center;gap:6px;cursor:pointer;padding:4px 0;user-select:none;transition:color var(--transition-fast)}
.rel-group-header:hover{color:var(--text-0)}
.rel-group-chevron{font-size:10px;color:var(--text-3);transition:transform var(--transition-normal);display:inline-block;width:12px}
.rel-group-chevron.open{transform:rotate(90deg)}
.rel-group-count{font-size:9px;color:var(--text-3);font-family:'JetBrains Mono',monospace}

/* ===== Command Palette (V7D) ===== */
.cmd-palette-overlay{position:fixed;inset:0;background:rgba(0,0,0,.65);backdrop-filter:blur(8px);z-index:1000;display:flex;align-items:flex-start;justify-content:center;padding-top:min(20vh,160px);animation:cmd-overlay-in .15s ease-out}
.cmd-palette{width:100%;max-width:560px;background:var(--bg-1);border:1px solid var(--border-1);border-radius:12px;box-shadow:0 24px 80px rgba(0,0,0,.6);overflow:hidden;animation:cmd-panel-in .2s ease-out}
.cmd-input{width:100%;padding:16px 20px;font-size:15px;background:transparent;border:none;border-bottom:1px solid var(--border-0);color:var(--text-0);font-family:'Space Grotesk',sans-serif;outline:none}
.cmd-input::placeholder{color:var(--text-3)}
.cmd-results{max-height:340px;overflow-y:auto;padding:8px 0}
.cmd-group-label{font-size:9px;color:var(--text-3);text-transform:uppercase;letter-spacing:.12em;padding:8px 16px 4px;font-family:'JetBrains Mono',monospace}
.cmd-item{display:flex;align-items:center;gap:10px;padding:8px 16px;cursor:pointer;transition:background var(--transition-fast)}
.cmd-item:hover,.cmd-item.active{background:rgba(34,211,238,.06)}
.cmd-item .cmd-icon{width:24px;text-align:center;font-size:14px;flex-shrink:0}
.cmd-item .cmd-label{font-size:13px;color:var(--text-0);flex:1}
.cmd-item .cmd-hint{font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace}
.cmd-item .cmd-cat{font-size:9px;color:var(--text-3);font-family:'JetBrains Mono',monospace;background:rgba(255,255,255,.04);padding:1px 6px;border-radius:3px}
.cmd-footer{padding:8px 16px;border-top:1px solid var(--border-0);display:flex;gap:16px;font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace}
.cmd-footer .cmd-key{background:var(--bg-0);padding:1px 5px;border-radius:3px;border:1px solid var(--border-1);color:var(--text-2);font-size:9px}

/* ===== Toast Notification (V7D) ===== */
.toast{position:fixed;bottom:48px;right:20px;background:var(--bg-2);border:1px solid var(--border-1);border-radius:8px;padding:12px 18px;font-size:12px;color:var(--text-0);display:flex;align-items:center;gap:10px;z-index:1000;box-shadow:0 8px 32px rgba(0,0,0,.4);animation:toast-in .3s ease-out}
.toast.hiding{animation:toast-out .3s ease-in forwards}
.toast .toast-icon{font-size:16px}
.toast .toast-msg{flex:1}

/* ===== Status Bar (V7D) ===== */
.status-bar{height:28px;background:var(--bg-1);border-top:1px solid var(--border-0);display:flex;align-items:center;padding:0 16px;gap:16px;font-size:10px;font-family:'JetBrains Mono',monospace;color:var(--text-3);flex-shrink:0}
.status-bar .sb-item{display:flex;align-items:center;gap:4px;transition:color var(--transition-fast)}
.status-bar .sb-item:hover{color:var(--text-2)}
.status-bar .sb-dot{width:5px;height:5px;border-radius:50%;background:var(--cyan)}
.status-bar .sb-sep{width:1px;height:14px;background:var(--border-0)}

/* ===== Loading Skeleton (V7D) ===== */
.skeleton-container{display:flex;flex:1;overflow:hidden;position:relative}
.skeleton-node{position:absolute;width:190px;height:56px;background:linear-gradient(90deg,var(--bg-2) 25%,var(--bg-3) 50%,var(--bg-2) 75%);background-size:400% 100%;animation:skeleton-shimmer 1.5s ease-in-out infinite;border-radius:5px;border:1px solid var(--border-0)}
.skeleton-edge{position:absolute;height:2px;background:linear-gradient(90deg,var(--bg-2) 25%,var(--bg-3) 50%,var(--bg-2) 75%);background-size:400% 100%;animation:skeleton-shimmer 1.5s ease-in-out infinite;border-radius:1px}
.loading{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:var(--text-3);font-size:13px;gap:12px}
.loading::before{content:'';width:20px;height:20px;border:2px solid var(--border-0);border-top-color:var(--cyan);border-radius:50%;animation:spin .8s linear infinite}
.loading-sub{font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace}
.loading-bar{width:200px;height:3px;background:var(--border-0);border-radius:2px;overflow:hidden;margin-top:4px}
.loading-bar-fill{height:100%;background:var(--cyan);border-radius:2px;transition:width .3s ease-out}

/* ===== Hover Tooltip (V7D fade-in) ===== */
.hover-tooltip{position:fixed;background:var(--bg-2);border:1px solid var(--border-1);border-radius:6px;padding:10px 14px;max-width:280px;z-index:1000;pointer-events:none;box-shadow:0 8px 32px rgba(0,0,0,.6);animation:fade-in .15s ease-out}
.hover-tooltip .ht-title{font-size:12px;font-weight:600;color:var(--text-0);margin-bottom:4px}
.hover-tooltip .ht-cat{font-size:9px;color:var(--text-3);text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;font-family:'JetBrains Mono',monospace}
.hover-tooltip .ht-desc{font-size:10px;color:var(--text-2);line-height:1.5;margin-bottom:6px}
.hover-tooltip .ht-stats{display:flex;gap:12px;font-size:9px;font-family:'JetBrains Mono',monospace;color:var(--text-3)}
.hover-tooltip .ht-stats span{color:var(--cyan)}

/* ===== Performance Overlay (V7C) ===== */
.perf-overlay{position:fixed;top:52px;right:12px;background:rgba(8,12,22,.92);border:1px solid var(--border-1);border-radius:6px;padding:8px 12px;font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text-2);z-index:200;display:flex;flex-direction:column;gap:3px;min-width:160px;backdrop-filter:blur(8px)}
.perf-overlay .perf-title{font-size:9px;color:var(--cyan);text-transform:uppercase;letter-spacing:.1em;margin-bottom:2px;font-weight:600}
.perf-overlay .perf-row{display:flex;justify-content:space-between;gap:12px}
.perf-overlay .perf-val{color:var(--text-0);font-weight:500}

/* ===== Undo/Redo (V7B) ===== */
.undo-redo-group{display:flex;gap:2px;align-items:center}
.undo-redo-group .toolbar-btn{padding:3px 8px;font-size:11px;line-height:1}
.undo-redo-sep{width:1px;height:16px;background:var(--border-0);margin:0 4px}

/* ===== Keyboard Hint (V7D bottom offset for status bar) ===== */
.kb-hint{position:fixed;bottom:40px;left:50%;transform:translateX(-50%);background:var(--bg-2);border:1px solid var(--border-0);border-radius:6px;padding:6px 14px;font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace;z-index:100;display:flex;gap:12px;opacity:.6;transition:opacity var(--transition-slow)}
.kb-hint:hover{opacity:1}
.kb-key{background:var(--bg-0);padding:1px 6px;border-radius:3px;color:var(--text-2);border:1px solid var(--border-1)}

/* ===== Scrollbar ===== */
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border-0);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--border-1)}
"""

# ============================================================
# JS_APP Part 1 — Imports, data structures, Zustand store, hooks, layout
# ============================================================
JS_APP = r"""
import { useState, useCallback, useMemo, useEffect, useRef, memo, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import { ReactFlow, ReactFlowProvider, useReactFlow, useNodesState, useEdgesState, Background, Controls, MiniMap, Handle, Position, MarkerType } from '@xyflow/react';
import ELK from 'elkjs/lib/elk.bundled.js';
import htm from 'htm';
import { create } from 'zustand';

const html = htm.bind(createElement);
const elk = new ELK();

// Fake React.Fragment for htm
const React_Fragment = ({ children }) => children;

// ============================================================
// MODULE-LEVEL PRE-COMPUTED DATA — O(1) lookups (Map/Set) [V7C]
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

// Pre-computed lowercase labels for fast search [V7C]
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

// Pre-computed node category map for grouped layout edge filtering [V7C]
const NODE_CATEGORY = new Map();
for (const n of ARCH.graph.nodes) { NODE_CATEGORY.set(n.id, n.data.category); }

// ============================================================
// LAYOUT CACHING [V7C]
// ============================================================
const layoutCache = new Map();
function getCacheKey(nodeIds, edgeCount, dir, grouped) {
  const sorted = [...nodeIds].sort();
  return sorted.join(',') + '|' + edgeCount + '|' + dir + '|' + (grouped ? '1' : '0');
}

// ============================================================
// PERFORMANCE MONITORING [V7C]
// ============================================================
let _layoutTime = 0;
let _layoutCount = 0;

// ============================================================
// DASHBOARD PRE-COMPUTATION (static IIFE) [V7C]
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

// ============================================================
// TOAST NOTIFICATION [V7D]
// ============================================================
let _toastEl = null;
let _toastTimer = null;
function showToast(message, icon) {
  if (_toastEl) { _toastEl.remove(); clearTimeout(_toastTimer); }
  _toastEl = document.createElement('div');
  _toastEl.className = 'toast';
  _toastEl.innerHTML = '<span class="toast-icon">' + (icon || '\u2713') + '</span><span class="toast-msg">' + message + '</span>';
  document.body.appendChild(_toastEl);
  _toastTimer = setTimeout(() => {
    if (_toastEl) { _toastEl.classList.add('hiding'); setTimeout(() => { if (_toastEl) { _toastEl.remove(); _toastEl = null; } }, 300); }
  }, 2500);
}

// ============================================================
// ZUSTAND STORE — V7A store shape + V7B undo/redo history
// ============================================================
const useStore = create((set, get) => ({
  // === Graph Slice ===
  activeCategories: new Set(CAT_KEYS),
  grouped: true,

  toggleCategory: (cat) => set(state => {
    if (cat === '__ALL__') {
      const allOn = state.activeCategories.size === CAT_KEYS.length;
      return { activeCategories: allOn ? new Set() : new Set(CAT_KEYS) };
    }
    const next = new Set(state.activeCategories);
    if (next.has(cat)) next.delete(cat); else next.add(cat);
    return { activeCategories: next };
  }),

  toggleGrouped: () => set(state => ({ grouped: !state.grouped })),

  // === Selection Slice (with undo/redo push) ===
  selectedNode: null,
  focusId: null,
  navHistory: [],

  selectNode: (data) => {
    const state = get();
    // Push current state to history before changing
    const snapshot = { selectedNode: state.selectedNode, focusId: state.focusId, navHistory: [...state.navHistory], tab: state.tab };
    const newPast = state.history.slice(0, state.historyIndex + 1);
    newPast.push(snapshot);

    // Find node ID via O(1) lookup
    let nodeId = null;
    for (const [id, d] of DATA_BY_ID) {
      if (d.label === data.label) { nodeId = id; break; }
    }
    set({
      selectedNode: data,
      navHistory: nodeId ? [{ id: nodeId, label: data.label }] : [],
      history: newPast,
      historyIndex: newPast.length - 1,
    });
  },

  navigateToEntity: (entityId) => {
    const node = NODES_BY_ID.get(entityId);
    if (!node) return;
    const state = get();
    // Push current state to history
    const snapshot = { selectedNode: state.selectedNode, focusId: state.focusId, navHistory: [...state.navHistory], tab: state.tab };
    const newPast = state.history.slice(0, state.historyIndex + 1);
    newPast.push(snapshot);

    const existingIdx = state.navHistory.findIndex(h => h.id === entityId);
    const newNav = existingIdx >= 0
      ? state.navHistory.slice(0, existingIdx + 1)
      : [...state.navHistory, { id: entityId, label: node.data.label }];
    set({
      selectedNode: node.data,
      focusId: entityId,
      navHistory: newNav,
      history: newPast,
      historyIndex: newPast.length - 1,
    });
  },

  goBack: () => set(state => {
    if (state.navHistory.length <= 1) return state;
    const newHist = state.navHistory.slice(0, -1);
    const prev = newHist[newHist.length - 1];
    const node = NODES_BY_ID.get(prev.id);
    if (!node) return { navHistory: newHist };
    return { navHistory: newHist, selectedNode: node.data, focusId: prev.id };
  }),

  clearSelection: () => {
    const state = get();
    // Push current state to history
    const snapshot = { selectedNode: state.selectedNode, focusId: state.focusId, navHistory: [...state.navHistory], tab: state.tab };
    const newPast = state.history.slice(0, state.historyIndex + 1);
    newPast.push(snapshot);
    set({
      selectedNode: null, focusId: null, navHistory: [],
      history: newPast, historyIndex: newPast.length - 1,
    });
  },

  setFocusId: (id) => {
    if (!id) {
      set({ focusId: null, selectedNode: null, navHistory: [] });
    } else {
      set({ focusId: id });
    }
  },

  // === Search Slice ===
  searchQuery: '',
  setSearchQuery: (q) => set({ searchQuery: q }),

  // === UI Slice ===
  tab: 'graph',
  setTab: (tab) => {
    const state = get();
    // Push current state to history
    const snapshot = { selectedNode: state.selectedNode, focusId: state.focusId, navHistory: [...state.navHistory], tab: state.tab };
    const newPast = state.history.slice(0, state.historyIndex + 1);
    newPast.push(snapshot);
    set({
      tab, selectedNode: null, focusId: null, navHistory: [], searchQuery: '',
      history: newPast, historyIndex: newPast.length - 1,
    });
  },

  hoverData: null,
  hoverPos: null,
  setHover: (data, pos) => set({ hoverData: data, hoverPos: pos }),
  clearHover: () => set({ hoverData: null, hoverPos: null }),

  showPerfOverlay: false,
  togglePerfOverlay: () => set(s => ({ showPerfOverlay: !s.showPerfOverlay })),

  showCommandPalette: false,
  toggleCommandPalette: () => set(s => ({ showCommandPalette: !s.showCommandPalette })),

  highContrast: false,
  toggleHighContrast: () => set(s => ({ highContrast: !s.highContrast })),

  // === History (undo/redo) [V7B] ===
  history: [{ selectedNode: null, focusId: null, navHistory: [], tab: 'graph' }],
  historyIndex: 0,

  undo: () => set(state => {
    if (state.historyIndex <= 0) return {};
    const newIndex = state.historyIndex - 1;
    const s = state.history[newIndex];
    showToast('Undo', '\u21A9');
    return { selectedNode: s.selectedNode, focusId: s.focusId, navHistory: [...s.navHistory], tab: s.tab, historyIndex: newIndex };
  }),

  redo: () => set(state => {
    if (state.historyIndex >= state.history.length - 1) return {};
    const newIndex = state.historyIndex + 1;
    const s = state.history[newIndex];
    showToast('Redo', '\u21AA');
    return { selectedNode: s.selectedNode, focusId: s.focusId, navHistory: [...s.navHistory], tab: s.tab, historyIndex: newIndex };
  }),
}));

// ============================================================
// DEBOUNCE HOOK [V7C]
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
// ELK LAYOUT with caching [V7C]
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

// === COMPONENTS START HERE (Part 2) ===
"""

# ============================================================
# JS_APP Part 2 — Components (placeholder for second pass)
# ============================================================
JS_APP_PART2 = r"""
// ============================================================
// EXPORT UTILITY [V7D — with toast]
// ============================================================
function exportArchData() {
  const blob = new Blob([JSON.stringify(ARCH, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = 'pts_architecture_data.json'; a.click();
  URL.revokeObjectURL(url);
  showToast('Architecture data exported', '\u2B07');
}

// ============================================================
// CLIPBOARD HELPER [V7D]
// ============================================================
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => showToast('Copied: ' + text, '\u{1F4CB}'));
}

// ============================================================
// 1. HOVER TOOLTIP [V7A store + V7D aria]
// ============================================================
function HoverTooltip() {
  const hoverData = useStore(s => s.hoverData);
  const hoverPos = useStore(s => s.hoverPos);
  const selectedNode = useStore(s => s.selectedNode);

  if (!hoverData || !hoverPos || selectedNode) return null;
  return html`<div className="hover-tooltip" role="tooltip" aria-live="polite"
    style=${{ left: hoverPos.x + 12, top: hoverPos.y - 10 }}>
    <div className="ht-title">${hoverData.label}</div>
    <div className="ht-cat">${hoverData.category}</div>
    ${hoverData.description ? html`<div className="ht-desc">${hoverData.description.length > 120 ? hoverData.description.slice(0, 120) + '\u2026' : hoverData.description}</div>` : null}
    <div className="ht-stats">
      ${hoverData.records && hoverData.records !== '\u2014' ? html`<span>${hoverData.records} records</span>` : null}
      <span>${hoverData.propCount}p</span>
      <span>${hoverData.relCount}r</span>
    </div>
  </div>`;
}

// ============================================================
// 2. CUSTOM NODE COMPONENTS [V7C memo + custom comparators + V7D animations]
// ============================================================
function EntityNodeComponent({ data, selected }) {
  const c = data.color || '#64748b';
  const headerBg = 'linear-gradient(135deg, ' + c + '20, ' + c + '08)';
  return html`
    <div className=${'entity-node' + (selected ? ' selected' : '')}
      style=${{ borderLeft: '3px solid ' + c }}
      aria-label=${'Entity: ' + data.label}>
      <${Handle} type="target" position=${Position.Top} style=${{ background: c, width: 6, height: 6, border: 'none' }} />
      <div className="entity-header" style=${{ background: headerBg }}>
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
const EntityNode = memo(EntityNodeComponent, (prev, next) =>
  prev.data.label === next.data.label &&
  prev.selected === next.selected &&
  prev.data.className === next.data.className
);

function FlowNodeComponent({ data }) {
  const c = data.color || '#3b82f6';
  return html`
    <div className="flow-node" style=${{ background: 'linear-gradient(135deg, ' + c + '15, ' + c + '08)', borderColor: c + '25' }}>
      <${Handle} type="target" position=${Position.Left} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
      <div className="flow-inner"><div className="flow-label">${data.label}</div>${data.sublabel ? html`<div className="flow-sub">${data.sublabel}</div>` : null}</div>
      <${Handle} type="source" position=${Position.Right} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
    </div>`;
}
const FlowNode = memo(FlowNodeComponent, (prev, next) =>
  prev.data.label === next.data.label &&
  prev.data.className === next.data.className
);

function IntegNodeComponent({ data }) {
  const c = data.color || '#8b5cf6';
  return html`
    <div className=${'integ-node pulse-active'} style=${{ background: 'linear-gradient(135deg, ' + c + '12, ' + c + '06)', borderColor: c + '20' }}>
      <${Handle} type="target" position=${Position.Left} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
      <div style=${{ fontWeight: 600, color: 'var(--text-0)', fontSize: '12px' }}>${data.label}</div>
      ${data.sublabel ? html`<div style=${{ color: 'var(--text-3)', fontSize: '10px', marginTop: '3px' }}>${data.sublabel}</div>` : null}
      <${Handle} type="source" position=${Position.Right} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
    </div>`;
}
const IntegNode = memo(IntegNodeComponent, (prev, next) =>
  prev.data.label === next.data.label &&
  prev.data.className === next.data.className
);

const nodeTypes = { entityNode: EntityNode, flowNode: FlowNode, integNode: IntegNode };

// ============================================================
// 3. SKELETON LOADER [V7D]
// ============================================================
function SkeletonLoader({ nodeCount, edgeCount }) {
  const skeletonNodes = useMemo(() => {
    const items = [];
    for (let i = 0; i < Math.min(nodeCount, 12); i++) {
      items.push({ x: 80 + (i % 4) * 220, y: 60 + Math.floor(i / 4) * 90, w: 190, h: 56 });
    }
    return items;
  }, [nodeCount]);
  const skeletonEdges = useMemo(() => {
    const items = [];
    for (let i = 0; i < Math.min(edgeCount, 8); i++) {
      items.push({ x: 100 + (i % 3) * 200, y: 100 + Math.floor(i / 3) * 80, w: 140 + Math.random() * 60 });
    }
    return items;
  }, [edgeCount]);
  return html`<div className="skeleton-container" style=${{ position: 'relative', width: '100%', height: '100%' }} aria-label="Loading graph layout" role="progressbar">
    ${skeletonNodes.map((n, i) => html`<div key=${'sn' + i} className="skeleton-node" style=${{ left: n.x + 'px', top: n.y + 'px', animationDelay: (i * 100) + 'ms' }}></div>`)}
    ${skeletonEdges.map((e, i) => html`<div key=${'se' + i} className="skeleton-edge" style=${{ left: e.x + 'px', top: e.y + 'px', width: e.w + 'px', animationDelay: (i * 150 + 200) + 'ms' }}></div>`)}
    <div style=${{ position: 'absolute', bottom: '40%', left: '50%', transform: 'translateX(-50%)', textAlign: 'center' }}>
      <div style=${{ color: 'var(--text-3)', fontSize: '13px', marginBottom: '8px' }}>Computing layout\u2026</div>
      <div className="loading-sub">${nodeCount} nodes \u00B7 ${edgeCount} edges</div>
      <div className="loading-bar" style=${{ marginTop: '12px' }}><div className="loading-bar-fill" style=${{ width: '60%', animation: 'skeleton-shimmer 1.5s ease-in-out infinite' }}></div></div>
    </div>
  </div>`;
}

// ============================================================
// 4. PERF OVERLAY [V7C — reads showPerfOverlay from store]
// ============================================================
function PerfOverlay() {
  const showPerfOverlay = useStore(s => s.showPerfOverlay);
  const renderCount = useRef(0);
  renderCount.current++;
  if (!showPerfOverlay) return null;
  return html`<div className="perf-overlay" role="status" aria-label="Performance metrics">
    <div className="perf-title">Performance</div>
    <div className="perf-row"><span>Renders:</span><span className="perf-val">${renderCount.current}</span></div>
    <div className="perf-row"><span>Layout:</span><span className="perf-val">${_layoutTime}ms</span></div>
    <div className="perf-row"><span>Layouts:</span><span className="perf-val">${_layoutCount}</span></div>
    <div className="perf-row"><span>Cache:</span><span className="perf-val">${layoutCache.size}</span></div>
    <div className="perf-row"><span>Nodes:</span><span className="perf-val">${ARCH.graph.nodes.length}</span></div>
    <div className="perf-row"><span>Edges:</span><span className="perf-val">${ARCH.graph.edges.length}</span></div>
  </div>`;
}

// ============================================================
// 5. ENTITY GRAPH VIEW [V7C state-driven + V7A store + V7D skeleton]
// ============================================================
function EntityGraphView() {
  const activeCategories = useStore(s => s.activeCategories);
  const searchQuery = useStore(s => s.searchQuery);
  const grouped = useStore(s => s.grouped);
  const focusId = useStore(s => s.focusId);
  const selectNode = useStore(s => s.selectNode);
  const navigateToEntity = useStore(s => s.navigateToEntity);
  const setHover = useStore(s => s.setHover);
  const clearHover = useStore(s => s.clearHover);

  const debouncedSearch = useDebounce(searchQuery, 150);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const { fitView } = useReactFlow();
  const layoutTimeoutRef = useRef(null);

  // Filter nodes and edges using pre-computed search index
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

  // Compute CSS class names for nodes (state-driven, NO DOM manipulation) [V7C]
  const nodeClassNames = useMemo(() => {
    const classMap = new Map();
    const hasFocus = !!focusId;
    const hasSearch = debouncedSearch && searchMatchIds.size > 0 && !hasFocus;
    const connected = hasFocus ? (ADJ.get(focusId) || new Set()) : null;

    for (const n of filtered.nodes) {
      let cls = '';
      if (hasFocus) {
        cls = (n.id === focusId || connected.has(n.id)) ? 'highlighted' : 'dimmed';
      } else if (hasSearch) {
        if (searchMatchIds.has(n.id)) cls = 'search-match';
      }
      classMap.set(n.id, cls);
    }
    return classMap;
  }, [filtered.nodes, focusId, debouncedSearch, searchMatchIds]);

  // Compute edge class names (state-driven) [V7C]
  const edgeClassNames = useMemo(() => {
    const classMap = new Map();
    if (!focusId) return classMap;
    for (const e of filtered.edges) {
      if (e.source === focusId || e.target === focusId) {
        classMap.set(e.id, 'highlighted');
      } else {
        classMap.set(e.id, 'dimmed');
      }
    }
    return classMap;
  }, [filtered.edges, focusId]);

  // ReactFlow wrapper class
  const flowClassName = useMemo(() => {
    if (focusId) return 'focus-active';
    if (debouncedSearch && searchMatchIds.size > 0) return 'search-active';
    return '';
  }, [focusId, debouncedSearch, searchMatchIds]);

  // Debounced layout computation [V7C]
  useEffect(() => {
    setLoading(true);

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

    const styledNodes = [];
    for (const n of filtered.nodes) {
      styledNodes.push({ ...n, className: nodeClassNames.get(n.id) || '' });
    }

    if (layoutTimeoutRef.current) clearTimeout(layoutTimeoutRef.current);
    layoutTimeoutRef.current = setTimeout(async () => {
      const result = await layoutNodes(styledNodes, styledEdges, 'DOWN', grouped);
      setNodes(result.nodes);
      setEdges(styledEdges);
      setLoading(false);
      setTimeout(() => fitView({ padding: 0.08, duration: 500 }), 150);
    }, 150);

    return () => { if (layoutTimeoutRef.current) clearTimeout(layoutTimeoutRef.current); };
  }, [filtered, grouped, nodeClassNames, edgeClassNames]);

  const onNodeClick = useCallback((_, node) => {
    selectNode(node.data);
    navigateToEntity(node.id);
    clearHover();
  }, [selectNode, navigateToEntity, clearHover]);

  const onNodeMouseEnter = useCallback((event, node) => {
    if (!useStore.getState().selectedNode) {
      setHover(node.data, { x: event.clientX, y: event.clientY });
    }
  }, [setHover]);

  const onNodeMouseLeave = useCallback(() => { clearHover(); }, [clearHover]);

  const onPaneClick = useCallback(() => {
    useStore.getState().setFocusId(null);
  }, []);

  if (loading) return html`<${SkeletonLoader} nodeCount=${filtered.nodes.length} edgeCount=${filtered.edges.length} />`;

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
// 6. DATA FLOW VIEW [V7D — particle-flow animation]
// ============================================================
function DataFlowView() {
  const [nodes, setNodes, onNC] = useNodesState([]);
  const [edges, setEdges, onEC] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const { fitView } = useReactFlow();
  useEffect(() => {
    const fn = ARCH.flow.nodes.map(n => ({ ...n, type: 'flowNode' }));
    const fe = ARCH.flow.edges.map(e => ({
      ...e, type: 'smoothstep', animated: true,
      className: 'animated-flow',
      style: { stroke: 'rgba(59,130,246,0.35)', strokeWidth: 2, strokeDasharray: '8 4' },
      markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(59,130,246,0.45)', width: 14, height: 14 }
    }));
    layoutNodes(fn, fe, 'RIGHT', false).then(r => { setNodes(r.nodes); setEdges(fe); setLoading(false); setTimeout(() => fitView({ padding: 0.15, duration: 400 }), 100); });
  }, []);
  if (loading) return html`<${SkeletonLoader} nodeCount=${ARCH.flow.nodes.length} edgeCount=${ARCH.flow.edges.length} />`;
  return html`<div className="tab-content"><${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNC} onEdgesChange=${onEC} nodeTypes=${nodeTypes} fitView fitViewOptions=${{ padding: 0.15 }} minZoom=${0.2} maxZoom=${2} proOptions=${{ hideAttribution: true }}><${Background} gap=${24} size=${1} color=${'#0f1629'} /><${Controls} /></${ReactFlow}></div>`;
}

// ============================================================
// 7. INTEGRATION VIEW [V7D — pulse-connection animation]
// ============================================================
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
    layoutNodes(fn, fe, 'RIGHT', false).then(r => { setNodes(r.nodes); setEdges(fe); setLoading(false); setTimeout(() => fitView({ padding: 0.2, duration: 400 }), 100); });
  }, []);
  if (loading) return html`<${SkeletonLoader} nodeCount=${ARCH.integration.nodes.length} edgeCount=${ARCH.integration.edges.length} />`;
  return html`<div className="tab-content"><${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNC} onEdgesChange=${onEC} nodeTypes=${nodeTypes} fitView fitViewOptions=${{ padding: 0.2 }} minZoom=${0.3} maxZoom=${2} proOptions=${{ hideAttribution: true }}><${Background} gap=${24} size=${1} color=${'#0f1629'} /><${Controls} /></${ReactFlow}></div>`;
}

// ============================================================
// 8. ANIMATED STAT + DASHBOARD VIEW [V7D count-up + V7C DASHBOARD_DATA]
// ============================================================
function AnimatedStat({ value, label, color, fontSize }) {
  const [display, setDisplay] = useState('0');
  useEffect(() => {
    const numStr = String(value);
    const numVal = parseInt(numStr.replace(/[^0-9]/g, ''));
    if (isNaN(numVal) || numVal === 0) { setDisplay(String(value)); return; }
    const suffix = numStr.replace(/[0-9,]/g, '');
    const duration = 800;
    const start = performance.now();
    function tick(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(numVal * eased);
      setDisplay(current.toLocaleString() + suffix);
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }, [value]);
  return html`<div aria-label=${label ? label + ': ' + value : String(value)}>
    <div className="stat-big animate-count" style=${{ fontSize: fontSize || '40px', color: color || 'var(--cyan)' }}>${display}</div>
    ${label ? html`<div className="stat-label">${label}</div>` : null}
  </div>`;
}

function DashboardView() {
  const { d, cats, mx, withRecords, totalRecordStr, topRels, topRelTypes } = DASHBOARD_DATA;

  return html`<div className="dash-grid tab-content" role="region" aria-label="Dashboard statistics">
    <div className="dash-card"><h3>System Overview</h3>
      <div style=${{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <${AnimatedStat} value=${d.totalEntities} label="Entities" />
        <${AnimatedStat} value=${d.totalProperties} label="Properties" />
        <${AnimatedStat} value=${d.totalRelationships} label="Relationships" />
        <${AnimatedStat} value=${totalRecordStr} label="Total Records" />
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
        <${AnimatedStat} value=${(d.totalRelationships / d.totalEntities).toFixed(1)} label="Rels / Entity" fontSize="28px" />
        <${AnimatedStat} value=${(d.totalProperties / d.totalEntities).toFixed(0)} label="Props / Entity" fontSize="28px" />
        <${AnimatedStat} value=${Object.keys(d.categories).length} label="Domains" fontSize="28px" />
        <${AnimatedStat} value=${d.qdrantCollections + d.sqliteDatabases + d.neo4jNodeTypes} label="Stores" fontSize="28px" />
      </div>
    </div>
  </div>`;
}

// ============================================================
// 9. DETAIL PANEL [V7A store + V7D collapsible + copy + related]
// ============================================================
function DetailSection({ title, defaultOpen, children }) {
  const [open, setOpen] = useState(defaultOpen !== false);
  return html`<div className=${'detail-sec ' + (open ? 'open' : 'closed')}>
    <div className="detail-sec-title" onClick=${() => setOpen(o => !o)} role="button" aria-expanded=${open} tabIndex="0"
      onKeyDown=${e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(o => !o); } }}>
      <span className=${'sec-chevron' + (open ? ' open' : '')}>${'\u25B6'}</span>
      ${title}
    </div>
    ${open ? children : null}
  </div>`;
}

function DetailPanel() {
  const selectedNode = useStore(s => s.selectedNode);
  const navHistory = useStore(s => s.navHistory);
  const navigateToEntity = useStore(s => s.navigateToEntity);
  const goBack = useStore(s => s.goBack);
  const clearSelection = useStore(s => s.clearSelection);

  const panelRef = useRef(null);
  const [copiedField, setCopiedField] = useState(null);
  const data = selectedNode;
  if (!data) return null;

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

  const handleCopy = useCallback((text, field) => {
    copyToClipboard(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 1500);
  }, []);

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

  // Related entities (1-hop neighbors)
  const relatedEntities = useMemo(() => {
    const relatedIds = ADJ.get(nodeId) || new Set();
    return [...relatedIds].slice(0, 5).map(id => ({ id, label: LABEL_BY_ID.get(id), data: DATA_BY_ID.get(id) })).filter(e => e.data);
  }, [nodeId]);

  return html`<aside className="detail-panel" ref=${panelRef} role="complementary" aria-label="Entity details">
    ${navHistory.length > 1 ? html`<nav className="nav-history" aria-label="Navigation breadcrumb">
      <button className="nav-history-btn" onClick=${goBack} title="Go back" aria-label="Go back">${'\u2190'}</button>
      ${navHistory.map((h, i) => html`<${React_Fragment} key=${i}>
        ${i > 0 ? html`<span className="nav-sep" aria-hidden="true">${'\u203A'}</span>` : null}
        <span className=${'nav-crumb' + (i === navHistory.length - 1 ? ' current' : '')}
          onClick=${() => i < navHistory.length - 1 && navigateToEntity(h.id)}
          role="button" tabIndex="0" aria-current=${i === navHistory.length - 1 ? 'page' : undefined}
          onKeyDown=${e => { if (e.key === 'Enter' && i < navHistory.length - 1) navigateToEntity(h.id); }}>${h.label}</span>
      </${React_Fragment}>`)}
    </nav>` : null}
    <div className="detail-hdr">
      <div style=${{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div>
          <div style=${{ fontSize: '16px', fontWeight: 600, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            ${data.label}
            <button className=${'copy-btn' + (copiedField === 'name' ? ' copied' : '')} onClick=${() => handleCopy(data.label, 'name')} aria-label="Copy entity name">${copiedField === 'name' ? '\u2713' : '\u{1F4CB}'}</button>
          </div>
          <div style=${{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <div style=${{ width: 8, height: 8, borderRadius: 2, background: data.color }}></div>
            <span style=${{ fontSize: '11px', color: 'var(--text-3)' }}>${data.category}</span>
            ${data.relCount > 0 ? html`<span style=${{ fontSize: '10px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', marginLeft: '4px' }}>${data.relCount} rels</span>` : null}
          </div>
        </div>
        <button onClick=${clearSelection} style=${{ background: 'none', border: 'none', color: 'var(--text-3)', cursor: 'pointer', fontSize: '18px', lineHeight: 1 }} aria-label="Close detail panel">${'\u00D7'}</button>
      </div>
      ${data.description ? html`<p style=${{ fontSize: '11px', color: 'var(--text-2)', marginTop: '10px', lineHeight: 1.5 }}>${data.description}</p>` : null}
    </div>

    <${DetailSection} title="Overview">
      <div style=${{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Records</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.records || '\u2014'}</div></div>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Properties</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.propCount}</div></div>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Connections</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.relCount || 0}</div></div>
      </div>
    </${DetailSection}>

    ${data.sources && data.sources.length > 0 ? html`<${DetailSection} title="Sources">
      <div style=${{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>${data.sources.map(s => html`<span className="detail-badge" style=${{ background: 'rgba(59,130,246,.12)', color: '#93c5fd' }} key=${s}>${s}</span>`)}</div>
    </${DetailSection}>` : null}

    ${data.storage && data.storage.length > 0 ? html`<${DetailSection} title="Storage">
      <div style=${{ display: 'flex', flexDirection: 'column', gap: '3px' }}>${data.storage.map(s => html`<div className="mono" style=${{ fontSize: '10px', color: 'var(--text-2)' }} key=${s}>${s}</div>`)}</div>
    </${DetailSection}>` : null}

    ${(outE.length > 0 || inE.length > 0) ? html`<${DetailSection} title=${'Relationships (' + (outE.length + inE.length) + ')'}>
      ${outGroups.length > 0 ? html`<div className="rel-group">
        <div className="rel-group-header" onClick=${() => toggleGroup('outgoing')} role="button" tabIndex="0"
          onKeyDown=${e => { if (e.key === 'Enter') toggleGroup('outgoing'); }}>
          <span className=${'rel-group-chevron' + (openGroups.has('outgoing') ? ' open' : '')}>${'\u25B6'}</span>
          <span style=${{ fontSize: '9px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', letterSpacing: '.1em' }}>OUTGOING (${outE.length})</span>
        </div>
        ${openGroups.has('outgoing') ? outGroups.map(([lbl, targets]) => html`<div key=${lbl} style=${{ marginLeft: '12px', marginBottom: '6px' }}>
          <div style=${{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}><span className="rel-label">${lbl}</span><span className="rel-group-count">${targets.length}</span></div>
          ${targets.map(t => html`<div className="rel-item" key=${t} style=${{ marginLeft: '8px', cursor: 'pointer' }} onClick=${() => navigateToEntity(t)} role="button" tabIndex="0"
            onKeyDown=${e => { if (e.key === 'Enter') navigateToEntity(t); }}><span className="rel-arrow">${'\u2192'}</span><span className="rel-target" style=${{ borderBottom: '1px dotted var(--border-1)' }}>${LABEL_BY_ID.get(t) || t}</span></div>`)}
        </div>`) : null}
      </div>` : null}
      ${inGroups.length > 0 ? html`<div className="rel-group">
        <div className="rel-group-header" onClick=${() => toggleGroup('incoming')} role="button" tabIndex="0"
          onKeyDown=${e => { if (e.key === 'Enter') toggleGroup('incoming'); }}>
          <span className=${'rel-group-chevron' + (openGroups.has('incoming') ? ' open' : '')}>${'\u25B6'}</span>
          <span style=${{ fontSize: '9px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', letterSpacing: '.1em' }}>INCOMING (${inE.length})</span>
        </div>
        ${openGroups.has('incoming') ? inGroups.map(([lbl, sources]) => html`<div key=${lbl} style=${{ marginLeft: '12px', marginBottom: '6px' }}>
          <div style=${{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}><span className="rel-label">${lbl}</span><span className="rel-group-count">${sources.length}</span></div>
          ${sources.map(s => html`<div className="rel-item" key=${s} style=${{ marginLeft: '8px', cursor: 'pointer' }} onClick=${() => navigateToEntity(s)} role="button" tabIndex="0"
            onKeyDown=${e => { if (e.key === 'Enter') navigateToEntity(s); }}><span className="rel-arrow">${'\u2190'}</span><span className="rel-target" style=${{ borderBottom: '1px dotted var(--border-1)' }}>${LABEL_BY_ID.get(s) || s}</span></div>`)}
        </div>`) : null}
      </div>` : null}
    </${DetailSection}>` : null}

    ${data.properties && data.properties.length > 0 ? html`<${DetailSection} title=${'Schema (' + data.properties.length + ')'} defaultOpen=${false}>
      <div style=${{ maxHeight: '350px', overflowY: 'auto' }}>
        ${data.properties.map(p => html`<div className="detail-prop-row" key=${p.name}>
          <span className="detail-prop-name">${p.name}</span>
          <span className="detail-prop-type">${p.type}</span>
          <span className="detail-prop-note" title=${p.note || ''}>${p.note || ''}</span>
        </div>`)}
      </div>
    </${DetailSection}>` : null}

    ${relatedEntities.length > 0 ? html`<${DetailSection} title="Related Entities" defaultOpen=${false}>
      <div style=${{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        ${relatedEntities.map(e => html`<div key=${e.id} style=${{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 0', cursor: 'pointer', fontSize: '11px' }}
          onClick=${() => navigateToEntity(e.id)} role="button" tabIndex="0"
          onKeyDown=${ev => { if (ev.key === 'Enter') navigateToEntity(e.id); }}>
          <span style=${{ width: 6, height: 6, borderRadius: 2, background: e.data.color, flexShrink: 0 }}></span>
          <span style=${{ color: 'var(--text-1)', flex: 1 }}>${e.label}</span>
          <span style=${{ color: 'var(--text-3)', fontSize: '9px', fontFamily: 'JetBrains Mono' }}>${e.data.category.split(' ')[0]}</span>
        </div>`)}
      </div>
    </${DetailSection}>` : null}
  </aside>`;
}

// ============================================================
// 10. CATEGORY SIDEBAR [V7A store + V7D checkmarks + search keyboard nav + recent]
// ============================================================
function CategorySidebar() {
  const activeCategories = useStore(s => s.activeCategories);
  const toggleCategory = useStore(s => s.toggleCategory);
  const searchQuery = useStore(s => s.searchQuery);
  const setSearchQuery = useStore(s => s.setSearchQuery);
  const grouped = useStore(s => s.grouped);
  const toggleGrouped = useStore(s => s.toggleGrouped);
  const navigateToEntity = useStore(s => s.navigateToEntity);

  const [searchFocused, setSearchFocused] = useState(false);
  const [searchIndex, setSearchIndex] = useState(-1);
  const inputRef = useRef(null);

  const [recentSearches, setRecentSearches] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem('pts_recent_searches') || '[]'); } catch { return []; }
  });

  const showRecent = searchFocused && !searchQuery && recentSearches.length > 0;

  // Compute search matches locally (derived state)
  const searchMatches = useMemo(() => {
    if (!searchQuery) return [];
    const q = searchQuery.toLowerCase();
    const results = [];
    for (const entry of SEARCH_INDEX) {
      if (!activeCategories.has(entry.node.data.category)) continue;
      if (entry.labelLower.includes(q) || entry.categoryLower.includes(q) || entry.descLower.includes(q)) {
        results.push(entry.node);
      }
    }
    results.sort((a, b) => (b.data.relCount || 0) - (a.data.relCount || 0));
    return results;
  }, [searchQuery, activeCategories]);

  // Reset search index when query changes
  useEffect(() => { setSearchIndex(-1); }, [searchQuery]);

  const handleSearchResultClick = useCallback(entityId => {
    // Save to recent searches
    if (searchQuery) {
      try {
        const recent = JSON.parse(sessionStorage.getItem('pts_recent_searches') || '[]');
        const updated = [searchQuery, ...recent.filter(r => r !== searchQuery)].slice(0, 10);
        sessionStorage.setItem('pts_recent_searches', JSON.stringify(updated));
        setRecentSearches(updated);
      } catch {}
    }
    navigateToEntity(entityId);
    setSearchQuery('');
    setSearchIndex(-1);
  }, [navigateToEntity, setSearchQuery, searchQuery]);

  const handleSearchKeyDown = useCallback(e => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter') {
      e.preventDefault();
      const maxIdx = Math.min(searchMatches.length, 12) - 1;
      if (e.key === 'ArrowDown') {
        setSearchIndex(i => Math.min(i + 1, maxIdx));
      } else if (e.key === 'ArrowUp') {
        setSearchIndex(i => Math.max(i - 1, -1));
      } else if (e.key === 'Enter') {
        setSearchIndex(i => {
          if (i >= 0 && searchMatches[i]) handleSearchResultClick(searchMatches[i].id);
          return i;
        });
      }
    }
  }, [searchMatches, handleSearchResultClick]);

  const handleRecentClick = useCallback(q => {
    setSearchQuery(q);
  }, [setSearchQuery]);

  const allOn = activeCategories.size === CAT_KEYS.length;

  return html`<nav className="cat-sidebar" role="navigation" aria-label="Category filters">
    <div className="cat-sidebar-hdr">
      <div className="cat-sidebar-title" id="filter-label">Filter</div>
      <div style=${{ marginTop: '8px', position: 'relative' }}>
        <input ref=${inputRef} className="search-input" placeholder=${'Search entities\u2026'}
          value=${searchQuery} onInput=${e => setSearchQuery(e.target.value)}
          onKeyDown=${handleSearchKeyDown}
          onFocus=${() => setSearchFocused(true)} onBlur=${() => setTimeout(() => setSearchFocused(false), 200)}
          role="combobox" aria-expanded=${(searchQuery && searchMatches.length > 0) || showRecent}
          aria-controls="search-results-list" aria-label="Search entities"
          aria-activedescendant=${searchIndex >= 0 ? 'sr-' + searchIndex : undefined} />
        ${searchQuery ? html`<span className="search-count" aria-live="polite" style=${{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)' }}>${searchMatches.length} results</span>` : null}
      </div>
      ${showRecent ? html`<div className="recent-searches" role="listbox">
        <div className="recent-search-label">Recent</div>
        ${recentSearches.slice(0, 5).map((q, i) => html`<div className="recent-search-item" key=${i} onClick=${() => handleRecentClick(q)} role="option">
          <span className="rs-icon">${'\u{1F50D}'}</span> ${q}
        </div>`)}
      </div>` : null}
      ${searchQuery && searchMatches.length > 0 ? html`<div className="search-results" id="search-results-list" role="listbox">
        ${searchMatches.slice(0, 12).map((n, i) => html`<div className=${'search-result-item' + (i === searchIndex ? ' kb-active' : '')} key=${n.id} id=${'sr-' + i}
          onClick=${() => handleSearchResultClick(n.id)} role="option" aria-selected=${i === searchIndex}
          style=${{ position: 'relative' }}>
          <div className="sr-dot" style=${{ background: n.data.color }}></div>
          <span className="sr-name">${n.data.label}</span>
          <span className="sr-cat">${n.data.category.split(' ')[0]}</span>
          <span className="sr-rels">${n.data.relCount}r</span>
          ${n.data.description ? html`<div className="sr-preview">${n.data.description.length > 100 ? n.data.description.slice(0, 100) + '\u2026' : n.data.description}</div>` : null}
        </div>`)}
        ${searchMatches.length > 12 ? html`<div style=${{ padding: '6px 10px', fontSize: '10px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', textAlign: 'center' }}>+${searchMatches.length - 12} more</div>` : null}
      </div>` : null}
      <div style=${{ display: 'flex', gap: '6px', marginTop: '8px' }}>
        <button className="toolbar-btn" onClick=${() => toggleCategory('__ALL__')} aria-label=${allOn ? 'Hide all categories' : 'Show all categories'}>${allOn ? 'Hide All' : 'Show All'}</button>
        <button className=${'toolbar-btn' + (grouped ? ' active' : '')} onClick=${toggleGrouped} aria-pressed=${grouped} aria-label="Toggle grouped layout">Grouped</button>
      </div>
    </div>
    ${Object.entries(CATEGORIES).map(([n, i]) => html`<div className=${'cat-toggle' + (activeCategories.has(n) ? '' : ' off')} key=${n} onClick=${() => toggleCategory(n)}
      role="checkbox" aria-checked=${activeCategories.has(n)} tabIndex="0"
      onKeyDown=${e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleCategory(n); } }}>
      <div className=${'cat-check' + (activeCategories.has(n) ? ' on' : '')}>
        ${activeCategories.has(n) ? html`<svg width="10" height="10" viewBox="0 0 10 10"><polyline points="2,5 4,7 8,3" fill="none" stroke="var(--cyan)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style=${{ strokeDasharray: 20, strokeDashoffset: 0 }} /></svg>` : null}
      </div>
      <div className="cat-toggle-dot" style=${{ background: i.color }}></div>
      <span className="cat-toggle-label">${n}</span>
      <span className="cat-toggle-count">${i.count}</span>
    </div>`)}
  </nav>`;
}

// ============================================================
// 11. COMMAND PALETTE [V7D — enhanced with undo/redo/perf actions]
// ============================================================
function CommandPalette() {
  const showCommandPalette = useStore(s => s.showCommandPalette);
  const toggleCommandPalette = useStore(s => s.toggleCommandPalette);
  const navigateToEntity = useStore(s => s.navigateToEntity);
  const setTab = useStore(s => s.setTab);
  const toggleHighContrast = useStore(s => s.toggleHighContrast);
  const togglePerfOverlay = useStore(s => s.togglePerfOverlay);
  const undo = useStore(s => s.undo);
  const redo = useStore(s => s.redo);

  const [query, setQuery] = useState('');
  const [activeIdx, setActiveIdx] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    if (showCommandPalette && inputRef.current) {
      setQuery('');
      setActiveIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [showCommandPalette]);

  const results = useMemo(() => {
    const items = [];
    const q = query.toLowerCase();

    // Category filter syntax: "in:Category"
    let categoryFilter = null;
    let searchTerm = q;
    const inMatch = q.match(/^in:(\S+)\s*(.*)/);
    if (inMatch) {
      categoryFilter = inMatch[1].toLowerCase();
      searchTerm = inMatch[2];
    }

    // Entities
    let entityMatches = ARCH.graph.nodes;
    if (categoryFilter) {
      entityMatches = entityMatches.filter(n => n.data.category.toLowerCase().includes(categoryFilter));
    }
    if (searchTerm) {
      entityMatches = entityMatches.filter(n =>
        n.data.label.toLowerCase().includes(searchTerm) ||
        n.data.category.toLowerCase().includes(searchTerm) ||
        (n.data.description && n.data.description.toLowerCase().includes(searchTerm))
      );
    }
    entityMatches.slice(0, 8).forEach(n => {
      items.push({ type: 'entity', id: n.id, label: n.data.label, hint: n.data.category, icon: '\u{1F4E6}', color: n.data.color });
    });

    // Navigation
    const tabs = [
      { id: 'graph', label: 'Entity Graph', icon: '\u{1F578}' },
      { id: 'flow', label: 'Data Flow', icon: '\u{1F500}' },
      { id: 'integration', label: 'Integrations', icon: '\u{1F517}' },
      { id: 'dashboard', label: 'Dashboard', icon: '\u{1F4CA}' },
    ];
    tabs.filter(t => !q || t.label.toLowerCase().includes(q)).forEach(t => {
      items.push({ type: 'nav', id: t.id, label: t.label, hint: 'Navigation', icon: t.icon });
    });

    // Actions
    const actions = [
      { id: 'export', label: 'Export Architecture Data', icon: '\u2B07', hint: 'Action' },
      { id: 'contrast', label: 'Toggle High Contrast', icon: '\u{1F506}', hint: 'Accessibility' },
      { id: 'perf', label: 'Toggle Performance Overlay', icon: '\u{1F4CA}', hint: 'Debug' },
      { id: 'undo', label: 'Undo', icon: '\u21A9', hint: 'Ctrl+Z' },
      { id: 'redo', label: 'Redo', icon: '\u21AA', hint: 'Ctrl+Shift+Z' },
    ];
    actions.filter(a => !q || a.label.toLowerCase().includes(q)).forEach(a => {
      items.push({ type: 'action', ...a });
    });

    return items;
  }, [query]);

  const handleSelect = useCallback((item) => {
    if (item.type === 'entity') {
      navigateToEntity(item.id);
    } else if (item.type === 'nav') {
      setTab(item.id);
    } else if (item.type === 'action') {
      if (item.id === 'export') exportArchData();
      if (item.id === 'contrast') { toggleHighContrast(); document.getElementById('root').classList.toggle('high-contrast'); }
      if (item.id === 'perf') togglePerfOverlay();
      if (item.id === 'undo') undo();
      if (item.id === 'redo') redo();
    }
    toggleCommandPalette();
  }, [navigateToEntity, setTab, toggleHighContrast, togglePerfOverlay, undo, redo, toggleCommandPalette]);

  const handleKeyDown = useCallback(e => {
    if (e.key === 'Escape') { toggleCommandPalette(); return; }
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx(i => Math.min(i + 1, results.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIdx(i => Math.max(i - 1, 0)); }
    if (e.key === 'Enter' && results[activeIdx]) { e.preventDefault(); handleSelect(results[activeIdx]); }
  }, [results, activeIdx, handleSelect, toggleCommandPalette]);

  if (!showCommandPalette) return null;

  // Group results
  const groups = {};
  results.forEach(r => {
    const g = r.type === 'entity' ? 'Entities' : r.type === 'nav' ? 'Navigation' : 'Actions';
    if (!groups[g]) groups[g] = [];
    groups[g].push(r);
  });

  let flatIdx = 0;

  return html`<div className="cmd-palette-overlay" onClick=${e => { if (e.target === e.currentTarget) toggleCommandPalette(); }} role="dialog" aria-label="Command palette" aria-modal="true">
    <div className="cmd-palette">
      <input ref=${inputRef} className="cmd-input" placeholder=${'Search entities, navigate, actions\u2026'}
        value=${query} onInput=${e => { setQuery(e.target.value); setActiveIdx(0); }}
        onKeyDown=${handleKeyDown} aria-label="Command palette search" />
      <div className="cmd-results" role="listbox">
        ${Object.entries(groups).map(([group, items]) => html`<${React_Fragment} key=${group}>
          <div className="cmd-group-label">${group}</div>
          ${items.map(item => {
            const idx = flatIdx++;
            return html`<div key=${item.id + item.type} className=${'cmd-item' + (idx === activeIdx ? ' active' : '')}
              onClick=${() => handleSelect(item)} role="option" aria-selected=${idx === activeIdx}
              onMouseEnter=${() => setActiveIdx(idx)}>
              <span className="cmd-icon">${item.icon}</span>
              <span className="cmd-label">${item.label}</span>
              ${item.color ? html`<span style=${{ width: 8, height: 8, borderRadius: 2, background: item.color, flexShrink: 0 }}></span>` : null}
              <span className="cmd-cat">${item.hint}</span>
            </div>`;
          })}
        </${React_Fragment}>`)}
        ${results.length === 0 ? html`<div style=${{ padding: '20px', textAlign: 'center', color: 'var(--text-3)', fontSize: '12px' }}>No results found</div>` : null}
      </div>
      <div className="cmd-footer">
        <span><span className="cmd-key">${'\u2191\u2193'}</span> Navigate</span>
        <span><span className="cmd-key">${'\u23CE'}</span> Select</span>
        <span><span className="cmd-key">Esc</span> Close</span>
        <span style=${{ marginLeft: 'auto', color: 'var(--text-3)' }}>Try <span style=${{ color: 'var(--cyan)' }}>in:BD</span> to filter</span>
      </div>
    </div>
  </div>`;
}

// ============================================================
// 12. TOP BAR [V7A store + V7B undo/redo buttons]
// ============================================================
function TopBar() {
  const tab = useStore(s => s.tab);
  const setTab = useStore(s => s.setTab);
  const focusId = useStore(s => s.focusId);
  const historyIndex = useStore(s => s.historyIndex);
  const historyLength = useStore(s => s.history).length;
  const undo = useStore(s => s.undo);
  const redo = useStore(s => s.redo);
  const toggleCommandPalette = useStore(s => s.toggleCommandPalette);

  const [exportBounce, setExportBounce] = useState(false);
  const handleExport = useCallback(() => {
    exportArchData();
    setExportBounce(true);
    setTimeout(() => setExportBounce(false), 600);
  }, []);

  const tabs = [
    { id: 'graph', label: 'Entity Graph' },
    { id: 'flow', label: 'Data Flow' },
    { id: 'integration', label: 'Integrations' },
    { id: 'dashboard', label: 'Dashboard' }
  ];

  const isMac = navigator.platform.indexOf('Mac') > -1;
  const cmdKey = isMac ? '\u2318' : 'Ctrl';

  return html`<header className="top-bar" role="banner">
    <span className="top-bar-title">PTS Data Architecture</span>
    <span className="top-bar-ver">V8</span>
    <div style=${{ width: 1, height: 20, background: 'var(--border-0)' }} aria-hidden="true"></div>
    <div style=${{ display: 'flex', gap: 0 }} role="tablist" aria-label="View tabs">
      ${tabs.map(t => html`<button key=${t.id} className=${'tab-btn' + (tab === t.id ? ' active' : '')}
        onClick=${() => setTab(t.id)} role="tab" aria-selected=${tab === t.id}
        aria-controls=${'panel-' + t.id}>${t.label}</button>`)}
    </div>
    <div style=${{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '12px' }}>
      ${focusId ? html`<span className="mono" style=${{ fontSize: '10px', color: 'var(--cyan)', background: 'rgba(34,211,238,.08)', padding: '2px 8px', borderRadius: '3px' }}>Focus: ${LABEL_BY_ID.get(focusId) || focusId}</span>` : null}
      <div className="undo-redo-group">
        <button className="toolbar-btn" onClick=${undo} disabled=${historyIndex <= 0}
          title="Undo (Ctrl+Z)" aria-label="Undo"
          style=${{ opacity: historyIndex <= 0 ? 0.3 : 1 }}>${'\u21A9'}</button>
        <button className="toolbar-btn" onClick=${redo} disabled=${historyIndex >= historyLength - 1}
          title="Redo (Ctrl+Shift+Z)" aria-label="Redo"
          style=${{ opacity: historyIndex >= historyLength - 1 ? 0.3 : 1 }}>${'\u21AA'}</button>
      </div>
      <span className="undo-redo-sep" aria-hidden="true"></span>
      <button className=${'toolbar-btn' + (exportBounce ? ' bounce-icon' : '')} onClick=${handleExport}
        title="Export architecture data as JSON" aria-label="Export architecture data" style=${{ fontSize: '9px' }}>
        <span className="btn-icon">${'\u2B07'}</span> Export</button>
      <button className="toolbar-btn" onClick=${toggleCommandPalette}
        title=${'Command palette (' + cmdKey + '+K)'} aria-label="Open command palette" style=${{ fontSize: '9px' }}>${cmdKey}+K</button>
      <span className="mono" style=${{ fontSize: '10px', color: 'var(--text-3)' }}>${ARCH.dashboard.totalEntities} entities ${'\u00B7'} ${ARCH.dashboard.totalRelationships} rels ${'\u00B7'} ${ARCH.dashboard.totalProperties} props</span>
    </div>
  </header>`;
}

// ============================================================
// 13. STATUS BAR [V7D]
// ============================================================
function StatusBar() {
  const tab = useStore(s => s.tab);
  const selectedNode = useStore(s => s.selectedNode);

  const tabLabels = { graph: 'Entity Graph', flow: 'Data Flow', integration: 'Integrations', dashboard: 'Dashboard' };

  return html`<footer className="status-bar" role="contentinfo">
    <span className="sb-item"><span className="sb-dot"></span> ${tabLabels[tab] || tab}</span>
    <span className="sb-sep" aria-hidden="true"></span>
    ${selectedNode ? html`<${React_Fragment}><span className="sb-item" style=${{ color: 'var(--cyan)' }}>${selectedNode.label}</span><span className="sb-sep" aria-hidden="true"></span></${React_Fragment}>` : null}
    <span className="sb-item">${ARCH.dashboard.totalEntities} nodes</span>
    <span className="sb-sep" aria-hidden="true"></span>
    <span className="sb-item">${ARCH.dashboard.totalRelationships} edges</span>
    <span className="sb-sep" aria-hidden="true"></span>
    <span className="sb-item">${ARCH.dashboard.totalProperties} props</span>
    <span style=${{ marginLeft: 'auto' }} className="sb-item">V8</span>
  </footer>`;
}

// ============================================================
// 14. APP LAYOUT [V7A template + keyboard shortcuts]
// ============================================================
function AppLayout() {
  const tab = useStore(s => s.tab);
  const selectedNode = useStore(s => s.selectedNode);
  const navHistory = useStore(s => s.navHistory);
  const highContrast = useStore(s => s.highContrast);

  // Keyboard shortcuts — reads store via getState to avoid re-renders
  useEffect(() => {
    const handler = (e) => {
      const state = useStore.getState();

      // Ctrl+K: Command palette
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        state.toggleCommandPalette();
        return;
      }

      // Ctrl+P: Perf overlay
      if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        state.togglePerfOverlay();
        return;
      }

      // Ctrl+Z: Undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        state.undo();
        return;
      }

      // Ctrl+Shift+Z: Redo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) {
        e.preventDefault();
        state.redo();
        return;
      }

      if (e.key === 'Escape') {
        if (state.showCommandPalette) { state.toggleCommandPalette(); return; }
        state.clearSelection();
        state.setSearchQuery('');
        state.clearHover();
      }

      if (e.key === '/' && !e.ctrlKey && !e.metaKey && document.activeElement?.tagName !== 'INPUT') {
        e.preventDefault();
        document.querySelector('.search-input')?.focus();
      }

      if (e.key === 'Backspace' && document.activeElement?.tagName !== 'INPUT' && state.navHistory.length > 1) {
        e.preventDefault();
        state.goBack();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const isMac = navigator.platform.indexOf('Mac') > -1;
  const cmdKey = isMac ? '\u2318' : 'Ctrl';

  return html`<div style=${{ display: 'flex', flexDirection: 'column', height: '100vh' }}
    className=${highContrast ? 'high-contrast' : ''}>
    <${TopBar} />
    <div style=${{ display: 'flex', flex: 1, overflow: 'hidden' }} role="main">
      ${tab === 'graph' ? html`<${CategorySidebar} />` : null}
      <div style=${{ flex: 1, position: 'relative' }} id=${'panel-' + tab} role="tabpanel">
        ${tab === 'graph' ? html`<${ReactFlowProvider}><${EntityGraphView} /></${ReactFlowProvider}>` : null}
        ${tab === 'flow' ? html`<${ReactFlowProvider}><${DataFlowView} /></${ReactFlowProvider}>` : null}
        ${tab === 'integration' ? html`<${ReactFlowProvider}><${IntegrationView} /></${ReactFlowProvider}>` : null}
        ${tab === 'dashboard' ? html`<${DashboardView} />` : null}
      </div>
      ${selectedNode && tab === 'graph' ? html`<${DetailPanel} />` : null}
    </div>
    <${StatusBar} />
    <${HoverTooltip} />
    <${CommandPalette} />
    <${PerfOverlay} />
    ${tab === 'graph' ? html`<div className="kb-hint" role="note" aria-label="Keyboard shortcuts">
      <span><span className="kb-key">Esc</span> Clear</span>
      <span><span className="kb-key">/</span> Search</span>
      <span><span className="kb-key">${cmdKey}+K</span> Commands</span>
      <span><span className="kb-key">${cmdKey}+Z</span> Undo</span>
      <span><span className="kb-key">Click</span> Focus</span>
      ${navHistory.length > 1 ? html`<span><span className="kb-key">${'\u232B'}</span> Back</span>` : null}
      <span><span className="kb-key">${cmdKey}+P</span> Perf</span>
      <span><span className="kb-key">Scroll</span> Zoom</span>
    </div>` : null}
  </div>`;
}

// ============================================================
// 15. APP (minimal entry point)
// ============================================================
function App() {
  return html`<${AppLayout} />`;
}

createRoot(document.getElementById('root')).render(html`<${App} />`);
"""

# ============================================================
# Assembly
# ============================================================
output = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PTS Data Architecture Explorer V8</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@xyflow/react@12.3.2/dist/style.css">
<script type="importmap">
{{
  "imports": {{
    "react": "https://esm.sh/react@18.2.0",
    "react/jsx-runtime": "https://esm.sh/react@18.2.0/jsx-runtime",
    "react-dom": "https://esm.sh/react-dom@18.2.0?external=react",
    "react-dom/client": "https://esm.sh/react-dom@18.2.0/client?external=react",
    "@xyflow/react": "https://esm.sh/@xyflow/react@12.3.2?external=react,react-dom",
    "elkjs/lib/elk.bundled.js": "https://esm.sh/elkjs@0.9.3/lib/elk.bundled.js",
    "htm": "https://esm.sh/htm@3.1.1",
    "zustand": "https://esm.sh/zustand@4.5.2?external=react"
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
{JS_APP_PART2}
</script>
</body>
</html>"""

outpath = os.path.join(BASE, 'PTS_DATA_ARCHITECTURE_EXPLORER_V8.html')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"V8 written: {len(output):,} chars ({len(output)//1024}KB)")
