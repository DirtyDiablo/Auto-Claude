#!/usr/bin/env python3
"""Generate PTS Data Architecture Explorer V7D — UI/UX Enhancement iteration.

Adds: smooth transitions, animated data flow, command palette (Ctrl+K),
enhanced detail panel with collapsible sections and copy buttons,
accessibility (focus rings, aria-labels, landmark roles, high-contrast mode,
reduced-motion support), status bar, enhanced search with keyboard nav and
recent history, loading skeletons, micro-interactions, toast notifications,
gradient node headers, animated stat count-up on dashboard.
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

# ---------- CSS ----------
CSS = r"""
:root{--bg-0:#080c16;--bg-1:#0f1629;--bg-2:#161d33;--bg-3:#1c2540;--border-0:#1a2236;--border-1:#263049;--border-2:#334155;--text-0:#f1f5f9;--text-1:#cbd5e1;--text-2:#94a3b8;--text-3:#64748b;--cyan:#22d3ee;--blue:#3b82f6;--transition-fast:150ms;--transition-normal:200ms;--transition-slow:300ms;--transition-slower:400ms}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Space Grotesk',sans-serif;background:var(--bg-0);color:var(--text-0);overflow:hidden}
.mono{font-family:'JetBrains Mono',monospace}
#root{width:100vw;height:100vh}

/* ===== Accessibility ===== */
:focus-visible{outline:2px solid var(--cyan);outline-offset:2px;border-radius:2px}
[role="button"]:focus-visible,.toolbar-btn:focus-visible,.tab-btn:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}
@media (prefers-reduced-motion: reduce){
  *,*::before,*::after{animation-duration:0.01ms !important;animation-iteration-count:1 !important;transition-duration:0.01ms !important;scroll-behavior:auto !important}
}
.high-contrast{--bg-0:#000;--bg-1:#0a0a0a;--bg-2:#141414;--bg-3:#1e1e1e;--border-0:#333;--border-1:#555;--border-2:#777;--text-0:#fff;--text-1:#eee;--text-2:#ccc;--text-3:#aaa;--cyan:#00ffff;--blue:#5599ff}

/* ===== Keyframe Animations ===== */
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

/* Focus mode with smooth transitions */
.react-flow.focus-active .react-flow__node.dimmed{opacity:.12!important;filter:saturate(0.2)!important;transition:opacity var(--transition-slower),filter var(--transition-slower)}
.react-flow.focus-active .react-flow__edge.dimmed path{stroke:rgba(148,163,184,0.04)!important;transition:stroke var(--transition-slower)}
.react-flow.focus-active .react-flow__edge.dimmed .react-flow__edge-text{fill:transparent!important}
.react-flow.focus-active .react-flow__node.highlighted{opacity:1!important;filter:none!important;transition:opacity var(--transition-slower)}
.react-flow.focus-active .react-flow__edge.highlighted path{stroke:rgba(34,211,238,0.5)!important;stroke-width:2!important;transition:stroke var(--transition-slower)}
.react-flow.focus-active .react-flow__edge.highlighted .react-flow__edge-text{fill:var(--cyan)!important}
.react-flow.focus-active .react-flow__edge.highlighted .react-flow__edge-textbg{fill:var(--bg-0)!important;fill-opacity:0.9!important}

/* Search highlight */
.react-flow.search-active .react-flow__node.search-match{box-shadow:0 0 0 2px var(--cyan),0 0 20px rgba(34,211,238,.25)!important;border-radius:5px}
.react-flow.search-active .react-flow__node:not(.search-match){opacity:.2!important;filter:saturate(0.15)!important;transition:opacity var(--transition-slow),filter var(--transition-slow)}
.react-flow.search-active .react-flow__edge path{stroke:rgba(148,163,184,0.05)!important}

/* ===== Entity Node (gradient headers, glow, selection ring) ===== */
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

/* Inner shadow for depth */
.entity-node::after{content:'';position:absolute;inset:0;border-radius:5px;box-shadow:inset 0 1px 0 rgba(255,255,255,.04),inset 0 -1px 0 rgba(0,0,0,.15);pointer-events:none}

/* ===== Flow / Integration Nodes ===== */
.flow-node{border-radius:5px;overflow:hidden;font-size:11px;border:1px solid rgba(255,255,255,.06);transition:box-shadow var(--transition-normal)}
.flow-inner{padding:10px 14px;text-align:center}
.flow-label{color:var(--text-0);font-weight:600;font-size:11px}
.flow-sub{color:var(--text-3);font-size:9px;margin-top:3px}
.integ-node{padding:12px 16px;text-align:center;font-size:11px;border:1px solid rgba(255,255,255,.06);border-radius:5px;transition:box-shadow var(--transition-normal)}
.integ-node.pulse-active{animation:pulse-connection 2s ease-in-out infinite}

/* ===== Data flow animated edges ===== */
.react-flow__edge.animated-flow path{stroke-dasharray:8 4;animation:particle-flow 1.2s linear infinite}

/* ===== Dashboard ===== */
.dash-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;padding:24px;overflow-y:auto;align-content:start;height:100%}
.dash-card{background:var(--bg-1);border:1px solid var(--border-0);border-radius:8px;padding:20px;transition:border-color var(--transition-normal);animation:fade-in .4s ease-out;animation-fill-mode:both}
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

/* ===== Detail Panel (slide-in) ===== */
.detail-panel{width:400px;background:var(--bg-1);border-left:1px solid var(--border-0);overflow-y:auto;flex-shrink:0;animation:slide-in-right var(--transition-slow) ease-out}
.detail-hdr{padding:16px 20px;border-bottom:1px solid var(--border-0);position:sticky;top:0;background:var(--bg-1);z-index:10}
.detail-sec{border-bottom:1px solid var(--border-0);overflow:hidden;transition:max-height var(--transition-slow) ease,padding var(--transition-slow) ease}
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

/* Copy button */
.copy-btn{background:none;border:1px solid var(--border-0);color:var(--text-3);cursor:pointer;font-size:10px;padding:2px 6px;border-radius:3px;font-family:'JetBrains Mono',monospace;transition:all var(--transition-fast)}
.copy-btn:hover{border-color:var(--cyan);color:var(--cyan);background:rgba(34,211,238,.06)}
.copy-btn.copied{border-color:#10b981;color:#10b981;background:rgba(16,185,129,.06)}

/* ===== Category Sidebar ===== */
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
/* Animated checkbox */
.cat-check{width:14px;height:14px;border:1.5px solid var(--border-2);border-radius:3px;flex-shrink:0;display:flex;align-items:center;justify-content:center;transition:all var(--transition-fast)}
.cat-check.on{border-color:var(--cyan);background:rgba(34,211,238,.12)}
.cat-check.on svg{stroke-dasharray:20;animation:check-draw .25s ease-out forwards}

/* ===== Search ===== */
.search-input{background:var(--bg-0);border:1px solid var(--border-0);color:var(--text-0);padding:7px 12px;border-radius:4px;font-size:12px;width:100%;outline:none;font-family:'Space Grotesk',sans-serif;transition:border-color var(--transition-normal),box-shadow var(--transition-normal)}
.search-input:focus{border-color:var(--cyan);box-shadow:0 0 0 3px rgba(34,211,238,.08)}
.search-input::placeholder{color:var(--text-3)}

/* Search results with stagger animation */
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

/* Recent searches */
.recent-searches{margin-top:6px;border:1px solid var(--border-0);border-radius:4px;background:var(--bg-0);animation:slide-down var(--transition-normal) ease-out}
.recent-search-label{font-size:9px;color:var(--text-3);padding:6px 10px 2px;font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.1em}
.recent-search-item{padding:5px 10px;font-size:11px;color:var(--text-2);cursor:pointer;transition:background var(--transition-fast);display:flex;align-items:center;gap:6px}
.recent-search-item:hover{background:rgba(34,211,238,.06);color:var(--text-0)}
.recent-search-item .rs-icon{color:var(--text-3);font-size:10px}

/* ===== Nav History / Breadcrumbs ===== */
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

/* Tab buttons with crossfade indicator */
.tab-btn{padding:6px 14px;font-size:11px;cursor:pointer;border:none;background:0 0;color:var(--text-3);font-family:'Space Grotesk',sans-serif;font-weight:500;letter-spacing:.02em;border-bottom:2px solid transparent;transition:all var(--transition-normal);height:48px;display:flex;align-items:center}
.tab-btn:hover{color:var(--text-2);background:rgba(255,255,255,.02)}
.tab-btn.active{color:var(--cyan);border-bottom-color:var(--cyan)}

/* Tab content crossfade */
.tab-content{animation:fade-in var(--transition-normal) ease-out}

/* ===== Micro-interactions ===== */
.toolbar-btn{padding:3px 10px;border-radius:3px;font-size:10px;cursor:pointer;border:1px solid var(--border-0);background:var(--bg-0);color:var(--text-3);font-family:'JetBrains Mono',monospace;transition:all var(--transition-fast);position:relative;overflow:hidden}
.toolbar-btn::before{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,.03),transparent);transform:translateX(-100%);transition:transform var(--transition-normal)}
.toolbar-btn:hover{border-color:var(--border-1);color:var(--text-2)}
.toolbar-btn:hover::before{transform:translateX(100%)}
.toolbar-btn:active{transform:scale(0.97)}
.toolbar-btn.active{border-color:var(--cyan);color:var(--cyan);background:rgba(34,211,238,.06)}
.toolbar-btn.bounce-icon .btn-icon{animation:bounce-once .5s ease-out}

.search-count{font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace;padding:2px 8px;background:rgba(34,211,238,.06);border-radius:3px}

/* ===== Relationship items ===== */
.rel-item{display:flex;align-items:center;gap:6px;padding:3px 0;font-size:11px;transition:background var(--transition-fast);border-radius:3px;padding:3px 4px}
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

/* ===== Command Palette ===== */
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

/* ===== Toast Notification ===== */
.toast{position:fixed;bottom:48px;right:20px;background:var(--bg-2);border:1px solid var(--border-1);border-radius:8px;padding:12px 18px;font-size:12px;color:var(--text-0);display:flex;align-items:center;gap:10px;z-index:1000;box-shadow:0 8px 32px rgba(0,0,0,.4);animation:toast-in .3s ease-out}
.toast.hiding{animation:toast-out .3s ease-in forwards}
.toast .toast-icon{font-size:16px}
.toast .toast-msg{flex:1}

/* ===== Status Bar ===== */
.status-bar{height:28px;background:var(--bg-1);border-top:1px solid var(--border-0);display:flex;align-items:center;padding:0 16px;gap:16px;font-size:10px;font-family:'JetBrains Mono',monospace;color:var(--text-3);flex-shrink:0}
.status-bar .sb-item{display:flex;align-items:center;gap:4px;transition:color var(--transition-fast)}
.status-bar .sb-item:hover{color:var(--text-2)}
.status-bar .sb-dot{width:5px;height:5px;border-radius:50%;background:var(--cyan)}
.status-bar .sb-sep{width:1px;height:14px;background:var(--border-0)}

/* ===== Loading Skeleton ===== */
.skeleton-container{display:flex;flex:1;overflow:hidden;position:relative}
.skeleton-node{position:absolute;width:190px;height:56px;background:linear-gradient(90deg,var(--bg-2) 25%,var(--bg-3) 50%,var(--bg-2) 75%);background-size:400% 100%;animation:skeleton-shimmer 1.5s ease-in-out infinite;border-radius:5px;border:1px solid var(--border-0)}
.skeleton-edge{position:absolute;height:2px;background:linear-gradient(90deg,var(--bg-2) 25%,var(--bg-3) 50%,var(--bg-2) 75%);background-size:400% 100%;animation:skeleton-shimmer 1.5s ease-in-out infinite;border-radius:1px}
.loading{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:var(--text-3);font-size:13px;gap:12px}
.loading::before{content:'';width:20px;height:20px;border:2px solid var(--border-0);border-top-color:var(--cyan);border-radius:50%;animation:spin .8s linear infinite}
.loading-sub{font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace}
.loading-bar{width:200px;height:3px;background:var(--border-0);border-radius:2px;overflow:hidden;margin-top:4px}
.loading-bar-fill{height:100%;background:var(--cyan);border-radius:2px;transition:width .3s ease-out}

/* ===== Hover Tooltip ===== */
.hover-tooltip{position:fixed;background:var(--bg-2);border:1px solid var(--border-1);border-radius:6px;padding:10px 14px;max-width:280px;z-index:1000;pointer-events:none;box-shadow:0 8px 32px rgba(0,0,0,.6);animation:fade-in .15s ease-out}
.hover-tooltip .ht-title{font-size:12px;font-weight:600;color:var(--text-0);margin-bottom:4px}
.hover-tooltip .ht-cat{font-size:9px;color:var(--text-3);text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;font-family:'JetBrains Mono',monospace}
.hover-tooltip .ht-desc{font-size:10px;color:var(--text-2);line-height:1.5;margin-bottom:6px}
.hover-tooltip .ht-stats{display:flex;gap:12px;font-size:9px;font-family:'JetBrains Mono',monospace;color:var(--text-3)}
.hover-tooltip .ht-stats span{color:var(--cyan)}

/* ===== Keyboard Hint ===== */
.kb-hint{position:fixed;bottom:40px;left:50%;transform:translateX(-50%);background:var(--bg-2);border:1px solid var(--border-0);border-radius:6px;padding:6px 14px;font-size:10px;color:var(--text-3);font-family:'JetBrains Mono',monospace;z-index:100;display:flex;gap:12px;opacity:.6;transition:opacity var(--transition-slow)}
.kb-hint:hover{opacity:1}
.kb-key{background:var(--bg-0);padding:1px 6px;border-radius:3px;color:var(--text-2);border:1px solid var(--border-1)}

/* ===== Scrollbar ===== */
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border-0);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--border-1)}
"""

# ---------- JS ----------
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

// Category emoji map
const CAT_EMOJI = {
  'Core CRM': '\u{1F4CA}', 'Organizations': '\u{1F3E2}', 'Federal Programs': '\u{1F3DB}',
  'Federal Awards': '\u{1F3C6}', 'Procurement': '\u{1F4DD}', 'BD Operations': '\u{1F4BC}',
  'Knowledge & Intel': '\u{1F9E0}', 'System & Ops': '\u2699\uFE0F', 'Reference': '\u{1F4D6}'
};

// Pre-build adjacency
const ADJ = {};
ARCH.graph.edges.forEach(e => {
  if (!ADJ[e.source]) ADJ[e.source] = new Set();
  if (!ADJ[e.target]) ADJ[e.target] = new Set();
  ADJ[e.source].add(e.target);
  ADJ[e.target].add(e.source);
});

// ID-to-label and ID-to-data maps
const ID_TO_LABEL = {};
const ID_TO_DATA = {};
ARCH.graph.nodes.forEach(n => { ID_TO_LABEL[n.id] = n.data.label; ID_TO_DATA[n.id] = n.data; });

// Fake React.Fragment for htm
const React_Fragment = ({ children }) => children;

// ===== Toast System =====
let toastTimeout = null;
function showToast(msg, icon) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  const t = document.createElement('div');
  t.className = 'toast';
  t.innerHTML = '<span class="toast-icon">' + (icon || '\u2705') + '</span><span class="toast-msg">' + msg + '</span>';
  document.body.appendChild(t);
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => { t.classList.add('hiding'); setTimeout(() => t.remove(), 300); }, 2500);
}

// ===== Clipboard helper =====
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => showToast('Copied: ' + text, '\u{1F4CB}'));
}

// ===== Animated Counter Component =====
function AnimatedStat({ value, label, color, fontSize }) {
  const ref = useRef(null);
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
  return html`<div>
    <div className="stat-big animate-count" style=${{ fontSize: fontSize || '40px', color: color || 'var(--cyan)' }}>${display}</div>
    ${label && html`<div className="stat-label">${label}</div>`}
  </div>`;
}

// ===== Hover Tooltip =====
function HoverTooltip({ nodeData, position }) {
  if (!nodeData || !position) return null;
  return html`<div className="hover-tooltip" style=${{ left: position.x + 12, top: position.y - 10 }}>
    <div className="ht-title">${CAT_EMOJI[nodeData.category] || ''} ${nodeData.label}</div>
    <div className="ht-cat">${nodeData.category}</div>
    ${nodeData.description && html`<div className="ht-desc">${nodeData.description.length > 120 ? nodeData.description.slice(0, 120) + '\u2026' : nodeData.description}</div>`}
    <div className="ht-stats">
      ${nodeData.records && nodeData.records !== '\u2014' && html`<span>${nodeData.records} records</span>`}
      <span>${nodeData.propCount}p</span>
      <span>${nodeData.relCount}r</span>
    </div>
  </div>`;
}

// ===== Custom Nodes =====
function EntityNodeComponent({ data, selected }) {
  const c = data.color || '#64748b';
  const emoji = CAT_EMOJI[data.category] || '';
  // Gradient background for header
  const headerBg = 'linear-gradient(135deg, ' + c + '20, ' + c + '08)';
  return html`
    <div className=${'entity-node' + (selected ? ' selected' : '')} style=${{ borderLeft: '3px solid ' + c, boxShadow: 'inset 0 1px 0 rgba(255,255,255,.04), inset 0 -1px 0 rgba(0,0,0,.15)' }}>
      <${Handle} type="target" position=${Position.Top} style=${{ background: c, width: 6, height: 6, border: 'none' }} />
      <div className="entity-header" style=${{ background: headerBg }}>
        ${emoji && html`<span className="cat-emoji">${emoji}</span>`}
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
    <div className="flow-node" style=${{ background: 'linear-gradient(135deg, ' + c + '15, ' + c + '08)', borderColor: c + '25' }}>
      <${Handle} type="target" position=${Position.Left} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
      <div className="flow-inner"><div className="flow-label">${data.label}</div>${data.sublabel && html`<div className="flow-sub">${data.sublabel}</div>`}</div>
      <${Handle} type="source" position=${Position.Right} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
    </div>`;
}
const FlowNode = memo(FlowNodeComponent);

function IntegNodeComponent({ data }) {
  const c = data.color || '#8b5cf6';
  return html`
    <div className=${'integ-node pulse-active'} style=${{ background: 'linear-gradient(135deg, ' + c + '12, ' + c + '06)', borderColor: c + '20' }}>
      <${Handle} type="target" position=${Position.Left} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
      <div style=${{ fontWeight: 600, color: 'var(--text-0)', fontSize: '12px' }}>${data.label}</div>
      ${data.sublabel && html`<div style=${{ color: 'var(--text-3)', fontSize: '10px', marginTop: '3px' }}>${data.sublabel}</div>`}
      <${Handle} type="source" position=${Position.Right} style=${{ background: c, width: 5, height: 5, border: 'none' }} />
    </div>`;
}
const IntegNode = memo(IntegNodeComponent);

const nodeTypes = { entityNode: EntityNode, flowNode: FlowNode, integNode: IntegNode };

// ===== ELK Layout =====
async function layoutNodes(nodes, edges, dir = 'DOWN', grouped = false) {
  if (grouped && nodes.length > 0 && nodes[0].type === 'entityNode') {
    const catGroups = {};
    nodes.forEach(n => { const cat = n.data.category || 'Other'; if (!catGroups[cat]) catGroups[cat] = []; catGroups[cat].push(n); });
    const graph = {
      id: 'root',
      layoutOptions: {
        'elk.algorithm': 'layered', 'elk.direction': dir,
        'elk.spacing.nodeNode': '40', 'elk.layered.spacing.nodeNodeBetweenLayers': '65',
        'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
        'elk.padding': '[top=50,left=50,bottom=50,right=50]',
        'elk.separateConnectedComponents': 'false',
      },
      children: Object.entries(catGroups).map(([cat, catNodes]) => ({
        id: 'group_' + cat.replace(/[^a-zA-Z0-9]/g, '_'),
        layoutOptions: {
          'elk.algorithm': 'layered', 'elk.direction': 'RIGHT',
          'elk.spacing.nodeNode': '30', 'elk.layered.spacing.nodeNodeBetweenLayers': '50',
          'elk.padding': '[top=40,left=20,bottom=20,right=20]',
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
    const groupBounds = {};
    if (layouted.children) {
      layouted.children.forEach(group => {
        const gx = group.x || 0, gy = group.y || 0;
        const catName = Object.entries(catGroups).find(([c]) => 'group_' + c.replace(/[^a-zA-Z0-9]/g, '_') === group.id)?.[0] || '';
        groupBounds[catName] = { x: gx, y: gy, w: group.width || 400, h: group.height || 200 };
        if (group.children) group.children.forEach(child => {
          positions[child.id] = { x: gx + (child.x || 0), y: gy + (child.y || 0) };
        });
      });
    }
    return { nodes: nodes.map(n => ({ ...n, position: positions[n.id] || { x: 0, y: 0 } })), groupBounds };
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
  return { nodes: nodes.map(n => { const ln = layouted.children.find(c => c.id === n.id); return { ...n, position: { x: ln?.x || 0, y: ln?.y || 0 } }; }), groupBounds: null };
}

// ===== Skeleton Loading =====
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
  return html`<div className="skeleton-container" style=${{ position: 'relative', width: '100%', height: '100%' }}>
    ${skeletonNodes.map((n, i) => html`<div key=${'sn' + i} className="skeleton-node" style=${{ left: n.x + 'px', top: n.y + 'px', animationDelay: (i * 100) + 'ms' }}></div>`)}
    ${skeletonEdges.map((e, i) => html`<div key=${'se' + i} className="skeleton-edge" style=${{ left: e.x + 'px', top: e.y + 'px', width: e.w + 'px', animationDelay: (i * 150 + 200) + 'ms' }}></div>`)}
    <div style=${{ position: 'absolute', bottom: '40%', left: '50%', transform: 'translateX(-50%)', textAlign: 'center' }}>
      <div style=${{ color: 'var(--text-3)', fontSize: '13px', marginBottom: '8px' }}>Computing layout\u2026</div>
      <div className="loading-sub">${nodeCount} nodes \u00B7 ${edgeCount} edges</div>
      <div className="loading-bar" style=${{ marginTop: '12px' }}><div className="loading-bar-fill" style=${{ width: '60%', animation: 'skeleton-shimmer 1.5s ease-in-out infinite' }}></div></div>
    </div>
  </div>`;
}

// ===== Entity Graph View =====
function EntityGraphView({ onSelectNode, activeCategories, searchQuery, useGrouped, focusNodeId, onFocusChange, onHoverNode, onHoverEnd }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [groupBounds, setGroupBounds] = useState(null);
  const { fitView } = useReactFlow();

  const filtered = useMemo(() => {
    let fn = ARCH.graph.nodes.filter(n => activeCategories.has(n.data.category));
    const ids = new Set(fn.map(n => n.id));
    return { nodes: fn, edges: ARCH.graph.edges.filter(e => ids.has(e.source) && ids.has(e.target)) };
  }, [activeCategories]);

  const searchMatchIds = useMemo(() => {
    if (!searchQuery) return new Set();
    const q = searchQuery.toLowerCase();
    return new Set(filtered.nodes.filter(n =>
      n.data.label.toLowerCase().includes(q) || n.data.category.toLowerCase().includes(q) ||
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
      labelBgStyle: { fill: 'transparent' }, labelBgPadding: [4, 2],
    }));
    layoutNodes(filtered.nodes, se, 'DOWN', useGrouped).then(result => {
      setNodes(result.nodes); setEdges(se);
      setGroupBounds(result.groupBounds || null);
      setLoading(false);
      setTimeout(() => fitView({ padding: 0.08, duration: 500 }), 150);
    });
  }, [filtered, useGrouped]);

  // Focus mode classes
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
      if (nid === focusNodeId || connected.has(nid)) { el.classList.add('highlighted'); el.classList.remove('dimmed'); }
      else { el.classList.add('dimmed'); el.classList.remove('highlighted'); }
    });
    document.querySelectorAll('.react-flow__edge').forEach(el => {
      const src = el.getAttribute('data-source') || '', tgt = el.getAttribute('data-target') || '';
      if (src === focusNodeId || tgt === focusNodeId) { el.classList.add('highlighted'); el.classList.remove('dimmed'); }
      else { el.classList.add('dimmed'); el.classList.remove('highlighted'); }
    });
  }, [focusNodeId, nodes]);

  // Search highlight classes
  useEffect(() => {
    if (!searchQuery || searchMatchIds.size === 0) {
      document.querySelectorAll('.react-flow').forEach(el => el.classList.remove('search-active'));
      document.querySelectorAll('.react-flow__node').forEach(el => el.classList.remove('search-match'));
      return;
    }
    if (focusNodeId) return;
    document.querySelectorAll('.react-flow').forEach(el => el.classList.add('search-active'));
    document.querySelectorAll('.react-flow__node').forEach(el => {
      const nid = el.getAttribute('data-id');
      if (searchMatchIds.has(nid)) el.classList.add('search-match'); else el.classList.remove('search-match');
    });
  }, [searchQuery, searchMatchIds, focusNodeId, nodes]);

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

  if (loading) return html`<${SkeletonLoader} nodeCount=${filtered.nodes.length} edgeCount=${filtered.edges.length} />`;

  return html`
    <${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNodesChange} onEdgesChange=${onEdgesChange}
      onNodeClick=${onNodeClick} onNodeMouseEnter=${onNodeMouseEnter} onNodeMouseLeave=${onNodeMouseLeave}
      onPaneClick=${onPaneClick} nodeTypes=${nodeTypes}
      fitView fitViewOptions=${{ padding: 0.08 }} minZoom=${0.06} maxZoom=${2.5}
      proOptions=${{ hideAttribution: true }}>
      <${Background} gap=${24} size=${1} color=${'#0f1629'} />
      <${Controls} />
      <${MiniMap} nodeColor=${n => n.data?.color || '#64748b'} maskColor=${'rgba(8,12,22,0.85)'} style=${{ borderRadius: 6 }} />
    </${ReactFlow}>`;
}

// ===== Data Flow View (animated particles) =====
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
    layoutNodes(fn, fe, 'RIGHT').then(r => { setNodes(r.nodes); setEdges(fe); setLoading(false); setTimeout(() => fitView({ padding: 0.15, duration: 400 }), 100); });
  }, []);
  if (loading) return html`<${SkeletonLoader} nodeCount=${ARCH.flow.nodes.length} edgeCount=${ARCH.flow.edges.length} />`;
  return html`<div className="tab-content"><${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNC} onEdgesChange=${onEC} nodeTypes=${nodeTypes} fitView fitViewOptions=${{ padding: 0.15 }} minZoom=${0.2} maxZoom=${2} proOptions=${{ hideAttribution: true }}><${Background} gap=${24} size=${1} color=${'#0f1629'} /><${Controls} /></${ReactFlow}></div>`;
}

// ===== Integration View (pulse animation) =====
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
    layoutNodes(fn, fe, 'RIGHT').then(r => { setNodes(r.nodes); setEdges(fe); setLoading(false); setTimeout(() => fitView({ padding: 0.2, duration: 400 }), 100); });
  }, []);
  if (loading) return html`<${SkeletonLoader} nodeCount=${ARCH.integration.nodes.length} edgeCount=${ARCH.integration.edges.length} />`;
  return html`<div className="tab-content"><${ReactFlow} nodes=${nodes} edges=${edges} onNodesChange=${onNC} onEdgesChange=${onEC} nodeTypes=${nodeTypes} fitView fitViewOptions=${{ padding: 0.2 }} minZoom=${0.3} maxZoom=${2} proOptions=${{ hideAttribution: true }}><${Background} gap=${24} size=${1} color=${'#0f1629'} /><${Controls} /></${ReactFlow}></div>`;
}

// ===== Dashboard View (animated count-up) =====
function DashboardView() {
  const d = ARCH.dashboard;
  const cats = Object.entries(d.categories).sort((a, b) => b[1].count - a[1].count);
  const mx = Math.max(...cats.map(c => c[1].count));
  const withRecords = ARCH.graph.nodes.filter(n => n.data.records && n.data.records !== '\u2014').length;
  const totalRecordStr = ARCH.graph.nodes.reduce((acc, n) => { const r = n.data.records; if (!r || r === '\u2014') return acc; const num = parseInt(r.replace(/[^0-9]/g, '')); return isNaN(num) ? acc : acc + num; }, 0);
  const topRels = [...ARCH.graph.nodes].sort((a, b) => (b.data.relCount || 0) - (a.data.relCount || 0)).slice(0, 8);
  const relTypes = {};
  ARCH.graph.edges.forEach(e => { const lbl = e.label || (e.data && e.data.label) || 'unlabeled'; relTypes[lbl] = (relTypes[lbl] || 0) + 1; });
  const topRelTypes = Object.entries(relTypes).sort((a, b) => b[1] - a[1]).slice(0, 10);
  const totalRecordDisplay = totalRecordStr > 1000000 ? (totalRecordStr/1000000).toFixed(1)+'M' : totalRecordStr > 1000 ? Math.round(totalRecordStr/1000)+'K' : String(totalRecordStr);

  return html`<div className="dash-grid tab-content" role="region" aria-label="Dashboard statistics">
    <div className="dash-card"><h3>System Overview</h3>
      <div style=${{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <${AnimatedStat} value=${d.totalEntities} label="Entities" />
        <${AnimatedStat} value=${d.totalProperties} label="Properties" />
        <${AnimatedStat} value=${d.totalRelationships} label="Relationships" />
        <${AnimatedStat} value=${totalRecordDisplay} label="Total Records" />
      </div>
    </div>
    <div className="dash-card"><h3>Domains</h3>
      ${cats.map(([n, i]) => html`<div className="cat-bar" key=${n}><span className="cat-bar-label">${CAT_EMOJI[n] || ''} ${n}</span><div style=${{ flex: 1, background: 'rgba(255,255,255,.03)', borderRadius: '2px', overflow: 'hidden' }}><div className="cat-bar-fill" style=${{ width: (i.count / mx * 100) + '%', background: i.color }}></div></div><span className="cat-bar-count">${i.count}</span></div>`)}
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

// ===== Collapsible Detail Section =====
function DetailSection({ title, defaultOpen, children }) {
  const [open, setOpen] = useState(defaultOpen !== false);
  return html`<div className=${'detail-sec ' + (open ? 'open' : 'closed')}>
    <div className="detail-sec-title" onClick=${() => setOpen(o => !o)} role="button" aria-expanded=${open} tabIndex="0"
      onKeyDown=${e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(o => !o); } }}>
      <span className=${'sec-chevron' + (open ? ' open' : '')}>${'\u25B6'}</span>
      ${title}
    </div>
    ${open && children}
  </div>`;
}

// ===== Detail Panel =====
function DetailPanel({ data, onClose, onNavigateToEntity, navHistory, onBack }) {
  const panelRef = useRef(null);
  const nodeId = ARCH.graph.nodes.find(n => n.data.label === data.label)?.id || data.label;
  const outE = ARCH.graph.edges.filter(e => e.source === nodeId);
  const inE = ARCH.graph.edges.filter(e => e.target === nodeId);
  const [openGroups, setOpenGroups] = useState(new Set(['outgoing', 'incoming']));
  const [copiedField, setCopiedField] = useState(null);

  useEffect(() => { if (panelRef.current) panelRef.current.scrollTop = 0; }, [data.label]);

  const toggleGroup = useCallback(g => {
    setOpenGroups(prev => { const n = new Set(prev); if (n.has(g)) n.delete(g); else n.add(g); return n; });
  }, []);

  const handleCopy = useCallback((text, field) => {
    copyToClipboard(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 1500);
  }, []);

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

  // Related entities suggestion (1-hop neighbors not already shown)
  const relatedIds = ADJ[nodeId] || new Set();
  const relatedEntities = [...relatedIds].slice(0, 5).map(id => ({ id, label: ID_TO_LABEL[id], data: ID_TO_DATA[id] })).filter(e => e.data);

  return html`<aside className="detail-panel" ref=${panelRef} role="complementary" aria-label="Entity details">
    ${navHistory.length > 1 && html`<nav className="nav-history" aria-label="Navigation breadcrumb">
      <button className="nav-history-btn" onClick=${onBack} title="Go back" aria-label="Go back">${'\u2190'}</button>
      ${navHistory.map((h, i) => html`<${React_Fragment} key=${i}>
        ${i > 0 && html`<span className="nav-sep" aria-hidden="true">${'\u203A'}</span>`}
        <span className=${'nav-crumb' + (i === navHistory.length - 1 ? ' current' : '')}
          onClick=${() => i < navHistory.length - 1 && onNavigateToEntity(h.id)}
          role="button" tabIndex="0" aria-current=${i === navHistory.length - 1 ? 'page' : undefined}
          onKeyDown=${e => { if (e.key === 'Enter' && i < navHistory.length - 1) onNavigateToEntity(h.id); }}>${h.label}</span>
      </${React_Fragment}>`)}
    </nav>`}
    <div className="detail-hdr">
      <div style=${{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div>
          <div style=${{ fontSize: '16px', fontWeight: 600, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            ${CAT_EMOJI[data.category] || ''} ${data.label}
            <button className=${'copy-btn' + (copiedField === 'name' ? ' copied' : '')} onClick=${() => handleCopy(data.label, 'name')} aria-label="Copy entity name">${copiedField === 'name' ? '\u2713' : '\u{1F4CB}'}</button>
          </div>
          <div style=${{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <div style=${{ width: 8, height: 8, borderRadius: 2, background: data.color }}></div>
            <span style=${{ fontSize: '11px', color: 'var(--text-3)' }}>${data.category}</span>
            ${data.relCount > 0 && html`<span style=${{ fontSize: '10px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', marginLeft: '4px' }}>${data.relCount} rels</span>`}
          </div>
        </div>
        <button onClick=${onClose} style=${{ background: 'none', border: 'none', color: 'var(--text-3)', cursor: 'pointer', fontSize: '18px', lineHeight: 1 }} aria-label="Close detail panel">${'\u00D7'}</button>
      </div>
      ${data.description && html`<p style=${{ fontSize: '11px', color: 'var(--text-2)', marginTop: '10px', lineHeight: 1.5 }}>${data.description}</p>`}
    </div>

    <${DetailSection} title="Overview">
      <div style=${{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Records</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.records || '\u2014'}</div></div>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Properties</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.propCount}</div></div>
        <div><span style=${{ fontSize: '10px', color: 'var(--text-3)' }}>Connections</span><div className="mono" style=${{ fontSize: '14px', color: 'var(--cyan)' }}>${data.relCount || 0}</div></div>
      </div>
    </${DetailSection}>

    ${data.sources && data.sources.length > 0 && html`<${DetailSection} title="Sources">
      <div style=${{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>${data.sources.map(s => html`<span className="detail-badge" style=${{ background: 'rgba(59,130,246,.12)', color: '#93c5fd' }} key=${s}>${s}</span>`)}</div>
    </${DetailSection}>`}

    ${data.storage && data.storage.length > 0 && html`<${DetailSection} title="Storage">
      <div style=${{ display: 'flex', flexDirection: 'column', gap: '3px' }}>${data.storage.map(s => html`<div className="mono" style=${{ fontSize: '10px', color: 'var(--text-2)' }} key=${s}>${s}</div>`)}</div>
    </${DetailSection}>`}

    ${(outE.length > 0 || inE.length > 0) && html`<${DetailSection} title=${'Relationships (' + (outE.length + inE.length) + ')'}>
      ${outGroups.length > 0 && html`<div className="rel-group">
        <div className="rel-group-header" onClick=${() => toggleGroup('outgoing')} role="button" tabIndex="0"
          onKeyDown=${e => { if (e.key === 'Enter') toggleGroup('outgoing'); }}>
          <span className=${'rel-group-chevron' + (openGroups.has('outgoing') ? ' open' : '')}>${'\u25B6'}</span>
          <span style=${{ fontSize: '9px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', letterSpacing: '.1em' }}>OUTGOING (${outE.length})</span>
        </div>
        ${openGroups.has('outgoing') && outGroups.map(([lbl, targets]) => html`<div key=${lbl} style=${{ marginLeft: '12px', marginBottom: '6px' }}>
          <div style=${{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}><span className="rel-label">${lbl}</span><span className="rel-group-count">${targets.length}</span></div>
          ${targets.map(t => html`<div className="rel-item" key=${t} style=${{ marginLeft: '8px', cursor: 'pointer' }} onClick=${() => onNavigateToEntity(t)} role="button" tabIndex="0"
            onKeyDown=${e => { if (e.key === 'Enter') onNavigateToEntity(t); }}><span className="rel-arrow">${'\u2192'}</span><span className="rel-target" style=${{ borderBottom: '1px dotted var(--border-1)' }}>${ID_TO_LABEL[t] || t}</span></div>`)}
        </div>`)}
      </div>`}
      ${inGroups.length > 0 && html`<div className="rel-group">
        <div className="rel-group-header" onClick=${() => toggleGroup('incoming')} role="button" tabIndex="0"
          onKeyDown=${e => { if (e.key === 'Enter') toggleGroup('incoming'); }}>
          <span className=${'rel-group-chevron' + (openGroups.has('incoming') ? ' open' : '')}>${'\u25B6'}</span>
          <span style=${{ fontSize: '9px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', letterSpacing: '.1em' }}>INCOMING (${inE.length})</span>
        </div>
        ${openGroups.has('incoming') && inGroups.map(([lbl, sources]) => html`<div key=${lbl} style=${{ marginLeft: '12px', marginBottom: '6px' }}>
          <div style=${{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}><span className="rel-label">${lbl}</span><span className="rel-group-count">${sources.length}</span></div>
          ${sources.map(s => html`<div className="rel-item" key=${s} style=${{ marginLeft: '8px', cursor: 'pointer' }} onClick=${() => onNavigateToEntity(s)} role="button" tabIndex="0"
            onKeyDown=${e => { if (e.key === 'Enter') onNavigateToEntity(s); }}><span className="rel-arrow">${'\u2190'}</span><span className="rel-target" style=${{ borderBottom: '1px dotted var(--border-1)' }}>${ID_TO_LABEL[s] || s}</span></div>`)}
        </div>`)}
      </div>`}
    </${DetailSection}>`}

    ${data.properties && data.properties.length > 0 && html`<${DetailSection} title=${'Schema (' + data.properties.length + ')'} defaultOpen=${false}>
      <div style=${{ maxHeight: '350px', overflowY: 'auto' }}>
        ${data.properties.map(p => html`<div className="detail-prop-row" key=${p.name}>
          <span className="detail-prop-name">${p.name}</span>
          <span className="detail-prop-type">${p.type}</span>
          <span className="detail-prop-note" title=${p.note || ''}>${p.note || ''}</span>
        </div>`)}
      </div>
    </${DetailSection}>`}

    ${relatedEntities.length > 0 && html`<${DetailSection} title="Related Entities" defaultOpen=${false}>
      <div style=${{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        ${relatedEntities.map(e => html`<div key=${e.id} style=${{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 0', cursor: 'pointer', fontSize: '11px' }}
          onClick=${() => onNavigateToEntity(e.id)} role="button" tabIndex="0"
          onKeyDown=${ev => { if (ev.key === 'Enter') onNavigateToEntity(e.id); }}>
          <span style=${{ width: 6, height: 6, borderRadius: 2, background: e.data.color, flexShrink: 0 }}></span>
          <span style=${{ color: 'var(--text-1)', flex: 1 }}>${e.label}</span>
          <span style=${{ color: 'var(--text-3)', fontSize: '9px', fontFamily: 'JetBrains Mono' }}>${e.data.category.split(' ')[0]}</span>
        </div>`)}
      </div>
    </${DetailSection}>`}
  </aside>`;
}

// ===== Category Sidebar with enhanced search =====
function CategorySidebar({ activeCategories, onToggle, searchQuery, onSearchChange, useGrouped, onToggleGrouped, searchMatches, onSearchResultClick, searchFocused, onSearchFocus, onSearchBlur, searchIndex, onSearchKeyNav }) {
  const allOn = activeCategories.size === Object.keys(CATEGORIES).length;
  const inputRef = useRef(null);
  const [recentSearches, setRecentSearches] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem('pts_recent_searches') || '[]'); } catch { return []; }
  });
  const showRecent = searchFocused && !searchQuery && recentSearches.length > 0;

  const handleSearchInput = useCallback(e => {
    onSearchChange(e.target.value);
  }, [onSearchChange]);

  const handleSearchKeyDown = useCallback(e => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter') {
      e.preventDefault();
      onSearchKeyNav(e.key);
    }
  }, [onSearchKeyNav]);

  const handleRecentClick = useCallback(q => {
    onSearchChange(q);
  }, [onSearchChange]);

  return html`<nav className="cat-sidebar" role="navigation" aria-label="Category filters">
    <div className="cat-sidebar-hdr">
      <div className="cat-sidebar-title" id="filter-label">Filter</div>
      <div style=${{ marginTop: '8px', position: 'relative' }}>
        <input ref=${inputRef} className="search-input" placeholder=${'Search entities\u2026'}
          value=${searchQuery} onInput=${handleSearchInput} onKeyDown=${handleSearchKeyDown}
          onFocus=${onSearchFocus} onBlur=${onSearchBlur}
          role="combobox" aria-expanded=${(searchQuery && searchMatches.length > 0) || showRecent}
          aria-controls="search-results-list" aria-label="Search entities"
          aria-activedescendant=${searchIndex >= 0 ? 'sr-' + searchIndex : undefined} />
        ${searchQuery && html`<span className="search-count" aria-live="polite" style=${{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)' }}>${searchMatches.length} results</span>`}
      </div>
      ${showRecent && html`<div className="recent-searches" role="listbox">
        <div className="recent-search-label">Recent</div>
        ${recentSearches.slice(0, 5).map((q, i) => html`<div className="recent-search-item" key=${i} onClick=${() => handleRecentClick(q)} role="option">
          <span className="rs-icon">${'\u{1F50D}'}</span> ${q}
        </div>`)}
      </div>`}
      ${searchQuery && searchMatches.length > 0 && html`<div className="search-results" id="search-results-list" role="listbox">
        ${searchMatches.slice(0, 12).map((n, i) => html`<div className=${'search-result-item' + (i === searchIndex ? ' kb-active' : '')} key=${n.id} id=${'sr-' + i}
          onClick=${() => onSearchResultClick(n.id)} role="option" aria-selected=${i === searchIndex}
          style=${{ position: 'relative' }}>
          <div className="sr-dot" style=${{ background: n.data.color }}></div>
          <span className="sr-name">${n.data.label}</span>
          <span className="sr-cat">${n.data.category.split(' ')[0]}</span>
          <span className="sr-rels">${n.data.relCount}r</span>
          ${n.data.description && html`<div className="sr-preview">${n.data.description.length > 100 ? n.data.description.slice(0, 100) + '\u2026' : n.data.description}</div>`}
        </div>`)}
        ${searchMatches.length > 12 && html`<div style=${{ padding: '6px 10px', fontSize: '10px', color: 'var(--text-3)', fontFamily: 'JetBrains Mono', textAlign: 'center' }}>+${searchMatches.length - 12} more</div>`}
      </div>`}
      <div style=${{ display: 'flex', gap: '6px', marginTop: '8px' }}>
        <button className="toolbar-btn" onClick=${() => onToggle('__ALL__')} aria-label=${allOn ? 'Hide all categories' : 'Show all categories'}>${allOn ? 'Hide All' : 'Show All'}</button>
        <button className=${'toolbar-btn' + (useGrouped ? ' active' : '')} onClick=${onToggleGrouped} aria-pressed=${useGrouped} aria-label="Toggle grouped layout">Grouped</button>
      </div>
    </div>
    ${Object.entries(CATEGORIES).map(([n, i]) => html`<div className=${'cat-toggle' + (activeCategories.has(n) ? '' : ' off')} key=${n} onClick=${() => onToggle(n)}
      role="checkbox" aria-checked=${activeCategories.has(n)} tabIndex="0"
      onKeyDown=${e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onToggle(n); } }}>
      <div className=${'cat-check' + (activeCategories.has(n) ? ' on' : '')}>
        ${activeCategories.has(n) && html`<svg width="10" height="10" viewBox="0 0 10 10"><polyline points="2,5 4,7 8,3" fill="none" stroke="var(--cyan)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style=${{ strokeDasharray: 20, strokeDashoffset: 0 }} /></svg>`}
      </div>
      <div className="cat-toggle-dot" style=${{ background: i.color }}></div>
      <span className="cat-toggle-label">${CAT_EMOJI[n] || ''} ${n}</span>
      <span className="cat-toggle-count">${i.count}</span>
    </div>`)}
  </nav>`;
}

// ===== Command Palette =====
function CommandPalette({ isOpen, onClose, onNavigateToEntity, onTabChange }) {
  const [query, setQuery] = useState('');
  const [activeIdx, setActiveIdx] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      setQuery('');
      setActiveIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

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
      items.push({ type: 'entity', id: n.id, label: n.data.label, hint: n.data.category, icon: CAT_EMOJI[n.data.category] || '\u{1F4E6}', color: n.data.color });
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
    ];
    actions.filter(a => !q || a.label.toLowerCase().includes(q)).forEach(a => {
      items.push({ type: 'action', ...a });
    });

    return items;
  }, [query]);

  const handleSelect = useCallback((item) => {
    if (item.type === 'entity') {
      onNavigateToEntity(item.id);
    } else if (item.type === 'nav') {
      onTabChange(item.id);
    } else if (item.type === 'action') {
      if (item.id === 'export') exportArchData();
      if (item.id === 'contrast') document.body.classList.toggle('high-contrast');
    }
    onClose();
  }, [onNavigateToEntity, onTabChange, onClose]);

  const handleKeyDown = useCallback(e => {
    if (e.key === 'Escape') { onClose(); return; }
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx(i => Math.min(i + 1, results.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIdx(i => Math.max(i - 1, 0)); }
    if (e.key === 'Enter' && results[activeIdx]) { e.preventDefault(); handleSelect(results[activeIdx]); }
  }, [results, activeIdx, handleSelect, onClose]);

  if (!isOpen) return null;

  // Group results
  const groups = {};
  results.forEach(r => {
    const g = r.type === 'entity' ? 'Entities' : r.type === 'nav' ? 'Navigation' : 'Actions';
    if (!groups[g]) groups[g] = [];
    groups[g].push(r);
  });

  let flatIdx = 0;

  return html`<div className="cmd-palette-overlay" onClick=${e => { if (e.target === e.currentTarget) onClose(); }} role="dialog" aria-label="Command palette" aria-modal="true">
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
              ${item.color && html`<span style=${{ width: 8, height: 8, borderRadius: 2, background: item.color, flexShrink: 0 }}></span>`}
              <span className="cmd-cat">${item.hint}</span>
            </div>`;
          })}
        </${React_Fragment}>`)}
        ${results.length === 0 && html`<div style=${{ padding: '20px', textAlign: 'center', color: 'var(--text-3)', fontSize: '12px' }}>No results found</div>`}
      </div>
      <div className="cmd-footer">
        <span><span className="cmd-key">${'\u2191\u2193'}</span> Navigate</span>
        <span><span className="cmd-key">${'\u23CE'}</span> Select</span>
        <span><span className="cmd-key">Esc</span> Close</span>
        <span style=${{ marginLeft: 'auto', color: 'var(--text-3)' }}>Try <span style=${{ color: 'var(--cyan)' }}>in:BD</span> to filter by category</span>
      </div>
    </div>
  </div>`;
}

// ===== Export utility =====
function exportArchData() {
  const blob = new Blob([JSON.stringify(ARCH, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = 'pts_architecture_data.json'; a.click();
  URL.revokeObjectURL(url);
  showToast('Architecture data exported', '\u2B07\uFE0F');
}

// ===== Status Bar =====
function StatusBar({ tab, selectedEntity, nodeCount, edgeCount, propCount }) {
  const tabLabels = { graph: 'Entity Graph', flow: 'Data Flow', integration: 'Integrations', dashboard: 'Dashboard' };
  return html`<footer className="status-bar" role="contentinfo">
    <span className="sb-item"><span className="sb-dot"></span> ${tabLabels[tab] || tab}</span>
    <span className="sb-sep"></span>
    ${selectedEntity && html`<${React_Fragment}><span className="sb-item" style=${{ color: 'var(--cyan)' }}>${selectedEntity}</span><span className="sb-sep"></span></${React_Fragment}>`}
    <span className="sb-item">${nodeCount} nodes</span>
    <span className="sb-sep"></span>
    <span className="sb-item">${edgeCount} edges</span>
    <span className="sb-sep"></span>
    <span className="sb-item">${propCount} props</span>
    <span style=${{ marginLeft: 'auto' }} className="sb-item">V7D</span>
  </footer>`;
}

// ===== Main App =====
function App() {
  const [tab, setTab] = useState('graph');
  const [sel, setSel] = useState(null);
  const [sq, setSq] = useState('');
  const [ac, setAc] = useState(new Set(Object.keys(CATEGORIES)));
  const [grouped, setGrouped] = useState(true);
  const [focusId, setFocusId] = useState(null);
  const [navHistory, setNavHistory] = useState([]);
  const [hoverData, setHoverData] = useState(null);
  const [hoverPos, setHoverPos] = useState(null);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);
  const [searchIndex, setSearchIndex] = useState(-1);

  const toggleCat = useCallback(cat => {
    setAc(prev => {
      if (cat === '__ALL__') return prev.size === Object.keys(CATEGORIES).length ? new Set() : new Set(Object.keys(CATEGORIES));
      const n = new Set(prev); if (n.has(cat)) n.delete(cat); else n.add(cat); return n;
    });
  }, []);

  // Search matches
  const searchMatches = useMemo(() => {
    if (!sq) return [];
    const q = sq.toLowerCase();
    return ARCH.graph.nodes.filter(n =>
      ac.has(n.data.category) && (
        n.data.label.toLowerCase().includes(q) ||
        n.data.category.toLowerCase().includes(q) ||
        (n.data.description && n.data.description.toLowerCase().includes(q))
      )
    ).sort((a, b) => (b.data.relCount || 0) - (a.data.relCount || 0));
  }, [sq, ac]);

  // Navigate to entity
  const navigateToEntity = useCallback(entityId => {
    const node = ARCH.graph.nodes.find(n => n.id === entityId);
    if (node) {
      setSel(node.data);
      setFocusId(entityId);
      setTab('graph');
      setNavHistory(prev => {
        const existingIdx = prev.findIndex(h => h.id === entityId);
        if (existingIdx >= 0) return prev.slice(0, existingIdx + 1);
        return [...prev, { id: entityId, label: node.data.label }];
      });
    }
  }, []);

  const goBack = useCallback(() => {
    if (navHistory.length > 1) {
      const newHist = navHistory.slice(0, -1);
      const prev = newHist[newHist.length - 1];
      setNavHistory(newHist);
      const node = ARCH.graph.nodes.find(n => n.id === prev.id);
      if (node) { setSel(node.data); setFocusId(prev.id); }
    }
  }, [navHistory]);

  const handleSelectNode = useCallback((data) => {
    setSel(data);
    const nodeId = ARCH.graph.nodes.find(n => n.data.label === data.label)?.id;
    if (nodeId) {
      setNavHistory(prev => {
        if (prev.length > 0 && prev[prev.length - 1].id === nodeId) return prev;
        return [{ id: nodeId, label: data.label }];
      });
    }
  }, []);

  const handleSearchResultClick = useCallback(entityId => {
    // Save to recent searches
    if (sq) {
      try {
        const recent = JSON.parse(sessionStorage.getItem('pts_recent_searches') || '[]');
        const updated = [sq, ...recent.filter(r => r !== sq)].slice(0, 10);
        sessionStorage.setItem('pts_recent_searches', JSON.stringify(updated));
      } catch {}
    }
    navigateToEntity(entityId);
    setSq('');
    setSearchIndex(-1);
  }, [navigateToEntity, sq]);

  // Search keyboard navigation
  const handleSearchKeyNav = useCallback(key => {
    const maxIdx = Math.min(searchMatches.length, 12) - 1;
    if (key === 'ArrowDown') {
      setSearchIndex(i => Math.min(i + 1, maxIdx));
    } else if (key === 'ArrowUp') {
      setSearchIndex(i => Math.max(i - 1, -1));
    } else if (key === 'Enter' && searchIndex >= 0 && searchMatches[searchIndex]) {
      handleSearchResultClick(searchMatches[searchIndex].id);
    }
  }, [searchMatches, searchIndex, handleSearchResultClick]);

  // Reset search index when query changes
  useEffect(() => { setSearchIndex(-1); }, [sq]);

  // Hover handlers
  const handleHoverNode = useCallback((data, pos) => {
    if (!sel) { setHoverData(data); setHoverPos(pos); }
  }, [sel]);
  const handleHoverEnd = useCallback(() => { setHoverData(null); setHoverPos(null); }, []);

  // Export button bounce
  const [exportBounce, setExportBounce] = useState(false);
  const handleExport = useCallback(() => {
    exportArchData();
    setExportBounce(true);
    setTimeout(() => setExportBounce(false), 600);
  }, []);

  // Tab change
  const handleTabChange = useCallback(newTab => {
    setTab(newTab);
    setSel(null);
    setFocusId(null);
    setNavHistory([]);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      // Command palette
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setCmdOpen(o => !o);
        return;
      }
      if (e.key === 'Escape') {
        if (cmdOpen) { setCmdOpen(false); return; }
        setSel(null); setFocusId(null); setSq(''); setNavHistory([]); setHoverData(null);
      }
      if (e.key === '/' && !e.ctrlKey && !e.metaKey && document.activeElement?.tagName !== 'INPUT') {
        e.preventDefault(); document.querySelector('.search-input')?.focus();
      }
      if (e.key === 'Backspace' && document.activeElement?.tagName !== 'INPUT' && navHistory.length > 1) {
        e.preventDefault(); goBack();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [goBack, navHistory, cmdOpen]);

  const tabs = [
    { id: 'graph', label: 'Entity Graph' },
    { id: 'flow', label: 'Data Flow' },
    { id: 'integration', label: 'Integrations' },
    { id: 'dashboard', label: 'Dashboard' }
  ];

  const isMac = navigator.platform.indexOf('Mac') > -1;
  const cmdKey = isMac ? '\u2318' : 'Ctrl';

  return html`<div style=${{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
    <header className="top-bar" role="banner">
      <span className="top-bar-title">PTS Data Architecture</span>
      <span className="top-bar-ver">V7D</span>
      <div style=${{ width: 1, height: 20, background: 'var(--border-0)' }} aria-hidden="true"></div>
      <div style=${{ display: 'flex', gap: 0 }} role="tablist" aria-label="View tabs">
        ${tabs.map(t => html`<button key=${t.id} className=${'tab-btn' + (tab === t.id ? ' active' : '')}
          onClick=${() => handleTabChange(t.id)} role="tab" aria-selected=${tab === t.id}
          aria-controls=${'panel-' + t.id}>${t.label}</button>`)}
      </div>
      <div style=${{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '12px' }}>
        ${focusId && html`<span className="mono" style=${{ fontSize: '10px', color: 'var(--cyan)', background: 'rgba(34,211,238,.08)', padding: '2px 8px', borderRadius: '3px' }}>Focus: ${ID_TO_LABEL[focusId] || focusId}</span>`}
        <button className=${'toolbar-btn' + (exportBounce ? ' bounce-icon' : '')} onClick=${handleExport}
          title="Export architecture data as JSON" aria-label="Export architecture data" style=${{ fontSize: '9px' }}>
          <span className="btn-icon">${'\u2B07'}</span> Export</button>
        <button className="toolbar-btn" onClick=${() => document.body.classList.toggle('high-contrast')}
          title="Toggle high contrast mode" aria-label="Toggle high contrast mode" style=${{ fontSize: '9px' }}>${'\u{1F506}'}</button>
        <button className="toolbar-btn" onClick=${() => setCmdOpen(true)}
          title=${'Command palette (' + cmdKey + '+K)'} aria-label="Open command palette" style=${{ fontSize: '9px' }}>${cmdKey}+K</button>
        <span className="mono" style=${{ fontSize: '10px', color: 'var(--text-3)' }}>${ARCH.dashboard.totalEntities} entities ${'\u00B7'} ${ARCH.dashboard.totalRelationships} rels</span>
      </div>
    </header>
    <div style=${{ display: 'flex', flex: 1, overflow: 'hidden' }} role="main">
      ${tab === 'graph' && html`<${CategorySidebar} activeCategories=${ac} onToggle=${toggleCat} searchQuery=${sq} onSearchChange=${setSq}
        useGrouped=${grouped} onToggleGrouped=${() => setGrouped(g => !g)} searchMatches=${searchMatches}
        onSearchResultClick=${handleSearchResultClick} searchFocused=${searchFocused}
        onSearchFocus=${() => setSearchFocused(true)} onSearchBlur=${() => setTimeout(() => setSearchFocused(false), 200)}
        searchIndex=${searchIndex} onSearchKeyNav=${handleSearchKeyNav} />`}
      <div style=${{ flex: 1, position: 'relative' }} id=${'panel-' + tab} role="tabpanel">
        ${tab === 'graph' && html`<${ReactFlowProvider}><${EntityGraphView} onSelectNode=${handleSelectNode} activeCategories=${ac} searchQuery=${sq} useGrouped=${grouped} focusNodeId=${focusId} onFocusChange=${id => { setFocusId(id); if (!id) { setSel(null); setNavHistory([]); } }} onHoverNode=${handleHoverNode} onHoverEnd=${handleHoverEnd} /></${ReactFlowProvider}>`}
        ${tab === 'flow' && html`<${ReactFlowProvider}><${DataFlowView} /></${ReactFlowProvider}>`}
        ${tab === 'integration' && html`<${ReactFlowProvider}><${IntegrationView} /></${ReactFlowProvider}>`}
        ${tab === 'dashboard' && html`<${DashboardView} />`}
      </div>
      ${sel && tab === 'graph' && html`<${DetailPanel} data=${sel} onClose=${() => { setSel(null); setFocusId(null); setNavHistory([]); }} onNavigateToEntity=${navigateToEntity} navHistory=${navHistory} onBack=${goBack} />`}
    </div>
    <${StatusBar} tab=${tab} selectedEntity=${sel ? sel.label : null}
      nodeCount=${ARCH.dashboard.totalEntities} edgeCount=${ARCH.dashboard.totalRelationships}
      propCount=${ARCH.dashboard.totalProperties} />
    ${hoverData && !sel && html`<${HoverTooltip} nodeData=${hoverData} position=${hoverPos} />`}
    ${tab === 'graph' && html`<div className="kb-hint" role="note" aria-label="Keyboard shortcuts">
      <span><span className="kb-key">Esc</span> Clear</span>
      <span><span className="kb-key">/</span> Search</span>
      <span><span className="kb-key">${cmdKey}+K</span> Commands</span>
      <span><span className="kb-key">Click</span> Focus</span>
      ${navHistory.length > 1 && html`<span><span className="kb-key">${'\u232B'}</span> Back</span>`}
      <span><span className="kb-key">Scroll</span> Zoom</span>
    </div>`}
    <${CommandPalette} isOpen=${cmdOpen} onClose=${() => setCmdOpen(false)} onNavigateToEntity=${navigateToEntity} onTabChange=${handleTabChange} />
  </div>`;
}

createRoot(document.getElementById('root')).render(html`<${App} />`);
"""

# ---------- Assemble HTML ----------
output = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PTS Data Architecture Explorer V7D</title>
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

outpath = os.path.join(BASE, 'PTS_DATA_ARCHITECTURE_EXPLORER_V7D.html')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"V7D written: {len(output):,} chars ({len(output)//1024}KB)")
print(f"Output: {outpath}")
