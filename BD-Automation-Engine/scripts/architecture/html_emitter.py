"""V4 React Flow HTML visualization emitter.

Generates a single-file HTML application with React 18 + @xyflow/react
for interactive architecture visualization. Four tabbed views:
1. Entity Relationship Graph
2. Data Flow Pipeline
3. Repository Integration Map
4. Storage & Infrastructure Dashboard
"""

import json
from pathlib import Path

from .name_map import CATEGORY_DEFS, PROJECT_LABELS, assign_category


def _build_graph_nodes(entities: dict) -> list[dict]:
    """Build React Flow nodes from merged entities."""
    nodes = []
    for i, (name, ent) in enumerate(sorted(entities.items())):
        category = ent.get('category', 'Meta/Ops')
        color = CATEGORY_DEFS.get(category, {}).get('color', '#64748b')
        projects = ent.get('projects', [])
        prop_count = len(ent.get('properties', []))

        nodes.append({
            'id': name,
            'type': 'entityNode',
            'data': {
                'label': name,
                'category': category,
                'color': color,
                'records': ent.get('records', '?'),
                'propCount': prop_count,
                'projects': projects,
                'pk': ent.get('pk', 'id'),
                'description': ent.get('description', ''),
                'sources': ent.get('sources', []),
                'storage': ent.get('storage', []),
                'properties': [
                    {'name': p.get('name', ''), 'type': p.get('type', ''), 'note': p.get('note', '')}
                    for p in ent.get('properties', [])[:30]  # Limit for size
                ],
            },
            'position': {'x': 0, 'y': 0},
        })
    return nodes


def _build_graph_edges(relationships: list[dict]) -> list[dict]:
    """Build React Flow edges from relationships."""
    edges = []
    for i, r in enumerate(relationships):
        edge_type = r.get('type', 'FK')
        animated = edge_type in ('derived', 'many')
        edges.append({
            'id': f"e-{i}",
            'source': r['from'],
            'target': r['to'],
            'label': r.get('label', ''),
            'type': 'smoothstep',
            'animated': animated,
            'style': {'stroke': '#475569', 'strokeWidth': 1.5},
            'labelStyle': {'fontSize': 9, 'fill': '#94a3b8'},
            'data': {
                'cardinality': edge_type,
                'description': r.get('description', ''),
            },
        })
    return edges


def _build_flow_nodes(infrastructure: dict) -> list[dict]:
    """Build data flow pipeline nodes (sources -> transforms -> destinations)."""
    nodes = []
    y_src = 0
    y_transform = 0
    y_dest = 0

    # Source nodes (left column)
    source_systems = [
        ('Bullhorn CRM', 'External API', '#f97316'),
        ('Apify Scraper', 'External Service', '#f97316'),
        ('SAM.gov', 'Government API', '#3b82f6'),
        ('USASpending', 'Government API', '#3b82f6'),
        ('Tango API', 'Government API', '#3b82f6'),
        ('CSV Imports', 'File System', '#64748b'),
    ]
    for name, stype, color in source_systems:
        nodes.append({
            'id': f'src-{name}',
            'type': 'flowNode',
            'data': {'label': name, 'subLabel': stype, 'color': color, 'nodeType': 'source'},
            'position': {'x': 0, 'y': y_src},
        })
        y_src += 80

    # Transform nodes (middle column)
    transforms = [
        ('Engine 1: Scraper', '#8b5cf6'),
        ('Engine 2: Program Map', '#8b5cf6'),
        ('Engine 3: OrgChart', '#8b5cf6'),
        ('Engine 4: Playbook', '#8b5cf6'),
        ('Engine 5: Scoring', '#8b5cf6'),
        ('Engine 6: QA', '#8b5cf6'),
        ('Engine 7: Bullhorn ETL', '#8b5cf6'),
        ('Engine 8: Knowledge', '#8b5cf6'),
        ('N8N Workflows', '#10b981'),
        ('Hub Sync Pipeline', '#10b981'),
    ]
    for name, color in transforms:
        nodes.append({
            'id': f'xfm-{name}',
            'type': 'flowNode',
            'data': {'label': name, 'subLabel': 'Transform', 'color': color, 'nodeType': 'transform'},
            'position': {'x': 350, 'y': y_transform},
        })
        y_transform += 70

    # Destination nodes (right column)
    destinations = [
        ('Qdrant Vectors', f"{len(infrastructure.get('qdrant_collections', []))} collections", '#06b6d4'),
        ('SQLite DBs', f"{len(infrastructure.get('sqlite_databases', []))} databases", '#06b6d4'),
        ('Neo4j Graph', f"{infrastructure.get('neo4j_graph', {}).get('total_node_types', 0)} node types", '#06b6d4'),
        ('Notion DBs', f"{len(infrastructure.get('notion_databases', []))} databases", '#06b6d4'),
        ('REST APIs', f"{infrastructure.get('api_endpoints', {}).get('total_endpoints', 0)} endpoints", '#f43f5e'),
        ('Dashboard', 'Vite + React', '#f43f5e'),
    ]
    for name, sub, color in destinations:
        nodes.append({
            'id': f'dest-{name}',
            'type': 'flowNode',
            'data': {'label': name, 'subLabel': sub, 'color': color, 'nodeType': 'destination'},
            'position': {'x': 700, 'y': y_dest},
        })
        y_dest += 80

    return nodes


def _build_flow_edges() -> list[dict]:
    """Build data flow pipeline edges."""
    edges = []
    flow_connections = [
        ('src-Apify Scraper', 'xfm-Engine 1: Scraper', 'JSON'),
        ('src-Bullhorn CRM', 'xfm-Engine 7: Bullhorn ETL', 'API/CSV'),
        ('src-SAM.gov', 'xfm-N8N Workflows', 'API'),
        ('src-USASpending', 'xfm-N8N Workflows', 'API'),
        ('src-Tango API', 'xfm-N8N Workflows', 'SQL/API'),
        ('src-CSV Imports', 'xfm-Hub Sync Pipeline', 'CSV'),
        ('xfm-Engine 1: Scraper', 'xfm-Engine 2: Program Map', 'Jobs'),
        ('xfm-Engine 2: Program Map', 'xfm-Engine 3: OrgChart', 'Programs'),
        ('xfm-Engine 3: OrgChart', 'xfm-Engine 4: Playbook', 'Contacts'),
        ('xfm-Engine 4: Playbook', 'xfm-Engine 5: Scoring', 'Playbooks'),
        ('xfm-Engine 5: Scoring', 'xfm-Engine 6: QA', 'Scores'),
        ('xfm-Engine 7: Bullhorn ETL', 'xfm-Engine 8: Knowledge', 'CRM Data'),
        ('xfm-Engine 8: Knowledge', 'dest-Qdrant Vectors', 'Embeddings'),
        ('xfm-Engine 7: Bullhorn ETL', 'dest-SQLite DBs', 'Tables'),
        ('xfm-N8N Workflows', 'dest-SQLite DBs', 'Federal Data'),
        ('xfm-N8N Workflows', 'dest-Neo4j Graph', 'Entities'),
        ('xfm-Hub Sync Pipeline', 'dest-REST APIs', 'Sync'),
        ('xfm-Engine 5: Scoring', 'dest-Notion DBs', 'BD Data'),
        ('dest-REST APIs', 'dest-Dashboard', 'JSON'),
        ('dest-Qdrant Vectors', 'dest-REST APIs', 'Search'),
    ]
    for i, (src, tgt, label) in enumerate(flow_connections):
        edges.append({
            'id': f'fe-{i}',
            'source': src,
            'target': tgt,
            'label': label,
            'type': 'smoothstep',
            'animated': True,
            'style': {'stroke': '#475569', 'strokeWidth': 1.5},
            'labelStyle': {'fontSize': 9, 'fill': '#94a3b8'},
        })
    return edges


def _build_integration_nodes() -> list[dict]:
    """Build repository integration map nodes."""
    nodes = []

    # Center: shared infrastructure
    shared = [
        ('Qdrant Server', ':6333', '#06b6d4', 0, 0),
        ('BD Hub API', ':8100', '#f43f5e', 200, 0),
        ('Neo4j Graph', ':7687', '#10b981', 100, -100),
        ('N8N Cloud', 'n8n.io', '#8b5cf6', 100, 100),
    ]
    for name, port, color, x, y in shared:
        nodes.append({
            'id': f'infra-{name}',
            'type': 'integrationNode',
            'data': {'label': name, 'subLabel': port, 'color': color, 'nodeType': 'infrastructure'},
            'position': {'x': 300 + x, 'y': 300 + y},
        })

    # Spokes: repositories
    repos = [
        ('BD-Automation-Engine', '8 engines, 340 APIs', '#3b82f6', -200, -150),
        ('Data-Scraper', '33 domains, 250 APIs', '#10b981', -200, 150),
        ('N8N-Builder', '40 workflows, 267 APIs', '#f97316', 500, 0),
    ]
    for name, sub, color, x, y in repos:
        nodes.append({
            'id': f'repo-{name}',
            'type': 'integrationNode',
            'data': {'label': name, 'subLabel': sub, 'color': color, 'nodeType': 'repository'},
            'position': {'x': 300 + x, 'y': 300 + y},
        })

    return nodes


def _build_integration_edges() -> list[dict]:
    """Build integration map edges."""
    connections = [
        ('repo-BD-Automation-Engine', 'infra-Qdrant Server', '9 collections'),
        ('repo-BD-Automation-Engine', 'infra-BD Hub API', '340 endpoints'),
        ('repo-BD-Automation-Engine', 'infra-Neo4j Graph', '9 node types'),
        ('repo-Data-Scraper', 'infra-Qdrant Server', '2 collections'),
        ('repo-Data-Scraper', 'infra-BD Hub API', 'Hub sync'),
        ('repo-N8N-Builder', 'infra-Qdrant Server', '3 collections'),
        ('repo-N8N-Builder', 'infra-N8N Cloud', '40 workflows'),
        ('repo-N8N-Builder', 'infra-Neo4j Graph', '6 node types'),
        ('repo-N8N-Builder', 'infra-BD Hub API', '267 endpoints'),
    ]
    edges = []
    for i, (src, tgt, label) in enumerate(connections):
        edges.append({
            'id': f'ie-{i}',
            'source': src,
            'target': tgt,
            'label': label,
            'type': 'smoothstep',
            'style': {'stroke': '#475569', 'strokeWidth': 2},
            'labelStyle': {'fontSize': 10, 'fill': '#94a3b8'},
        })
    return edges


def _build_dashboard_data(entities: dict, relationships: list, infrastructure: dict) -> dict:
    """Build dashboard statistics for View 4."""
    # Category breakdown
    categories = {}
    for cat_name, cat_data in CATEGORY_DEFS.items():
        count = sum(1 for e in entities.values() if e.get('category') == cat_name)
        if count:
            categories[cat_name] = {'count': count, 'color': cat_data['color']}

    # Storage summary
    qdrant = infrastructure.get('qdrant_collections', [])
    sqlite = infrastructure.get('sqlite_databases', [])
    neo4j = infrastructure.get('neo4j_graph', {})
    api = infrastructure.get('api_endpoints', {})

    return {
        'totalEntities': len(entities),
        'totalProperties': sum(len(e.get('properties', [])) for e in entities.values()),
        'totalRelationships': len(relationships),
        'multiProjectEntities': sum(1 for e in entities.values() if len(e.get('projects', [])) > 1),
        'categories': categories,
        'qdrantCollections': len(qdrant),
        'sqliteDatabases': len(sqlite),
        'neo4jNodeTypes': neo4j.get('total_node_types', 0),
        'neo4jRelTypes': neo4j.get('total_relationship_types', 0),
        'apiEndpoints': api.get('total_endpoints', 0),
        'dataFlows': len(infrastructure.get('data_flows', [])),
        'engines': len(infrastructure.get('engines', [])),
        'n8nWorkflows': (
            len(infrastructure.get('n8n_workflows', {}).get('cloud', []))
            if isinstance(infrastructure.get('n8n_workflows'), dict)
            else 0
        ),
    }


def generate_v4_html(
    entities: dict,
    relationships: list[dict],
    infrastructure: dict,
) -> str:
    """Generate the complete V4 HTML with React Flow visualization."""

    # Prepare data for all 4 views
    graph_nodes = _build_graph_nodes(entities)
    graph_edges = _build_graph_edges(relationships)
    flow_nodes = _build_flow_nodes(infrastructure)
    flow_edges = _build_flow_edges()
    integration_nodes = _build_integration_nodes()
    integration_edges = _build_integration_edges()
    dashboard = _build_dashboard_data(entities, relationships, infrastructure)

    # Inline all data
    arch_data = json.dumps({
        'graph': {'nodes': graph_nodes, 'edges': graph_edges},
        'flow': {'nodes': flow_nodes, 'edges': flow_edges},
        'integration': {'nodes': integration_nodes, 'edges': integration_edges},
        'dashboard': dashboard,
        'categories': {k: {'color': v['color'], 'count': len([
            n for n in graph_nodes if n['data']['category'] == k
        ])} for k, v in CATEGORY_DEFS.items()},
    }, indent=None, ensure_ascii=False)

    return _HTML_TEMPLATE.replace('__ARCHITECTURE_DATA__', arch_data)


def write_html(html: str, output_path: Path) -> None:
    """Write HTML to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding='utf-8')
    size = output_path.stat().st_size
    print(f"  Written: {output_path} ({size:,} bytes, {size/1024:.1f} KB)")


# === HTML TEMPLATE ===
# Single-file React 18 + React Flow app loaded via ESM CDN
_HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PTS Data Architecture Explorer V4</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'DM Sans', sans-serif; background: #0f172a; color: #e2e8f0; overflow: hidden; }
  .mono { font-family: 'JetBrains Mono', monospace; }
  #app { width: 100vw; height: 100vh; display: flex; flex-direction: column; }

  /* Tab bar */
  .tab-bar { display: flex; background: #1e293b; border-bottom: 1px solid #334155; padding: 0 16px; flex-shrink: 0; }
  .tab { padding: 12px 20px; cursor: pointer; font-size: 13px; font-weight: 500; color: #94a3b8;
         border-bottom: 2px solid transparent; transition: all 0.2s; user-select: none; }
  .tab:hover { color: #e2e8f0; background: #1e293b; }
  .tab.active { color: #38bdf8; border-bottom-color: #38bdf8; }
  .tab-icon { margin-right: 6px; }

  /* View container */
  .view { display: none; flex: 1; overflow: hidden; }
  .view.active { display: flex; }

  /* React Flow container */
  .rf-container { width: 100%; height: 100%; position: relative; }

  /* Search bar */
  .search-bar { position: absolute; top: 12px; left: 12px; z-index: 10; display: flex; gap: 8px; }
  .search-bar input { background: #1e293b; border: 1px solid #334155; color: #e2e8f0; padding: 8px 12px;
                       border-radius: 6px; font-size: 13px; width: 240px; outline: none; }
  .search-bar input:focus { border-color: #38bdf8; }
  .search-bar input::placeholder { color: #64748b; }

  /* Legend */
  .legend { position: absolute; bottom: 12px; left: 12px; z-index: 10; background: #1e293bdd;
            border: 1px solid #334155; border-radius: 8px; padding: 12px; backdrop-filter: blur(8px); }
  .legend-item { display: flex; align-items: center; gap: 6px; font-size: 11px; margin: 4px 0; }
  .legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

  /* Detail panel */
  .detail-panel { width: 380px; background: #1e293b; border-left: 1px solid #334155; overflow-y: auto;
                  padding: 16px; flex-shrink: 0; display: none; }
  .detail-panel.open { display: block; }
  .detail-panel h3 { font-size: 16px; font-weight: 600; margin-bottom: 8px; }
  .detail-panel .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px;
                          font-weight: 600; margin: 2px; }
  .detail-panel .prop-row { display: flex; justify-content: space-between; padding: 4px 0;
                             border-bottom: 1px solid #334155; font-size: 12px; }
  .detail-panel .prop-name { color: #38bdf8; }
  .detail-panel .prop-type { color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 11px; }

  /* Dashboard view */
  .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;
               padding: 24px; overflow-y: auto; align-content: start; }
  .dash-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; }
  .dash-card h3 { font-size: 14px; font-weight: 600; color: #94a3b8; margin-bottom: 12px; text-transform: uppercase;
                   letter-spacing: 0.5px; }
  .stat-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0;
              border-bottom: 1px solid #1e293b; }
  .stat-label { font-size: 13px; color: #cbd5e1; }
  .stat-value { font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
  .stat-big { font-size: 36px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #38bdf8; }
  .cat-bar { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
  .cat-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .cat-label { font-size: 12px; flex: 1; }
  .cat-count { font-size: 12px; font-family: 'JetBrains Mono', monospace; color: #64748b; }

  /* Canvas rendering for graph/flow views */
  .canvas-container { width: 100%; height: 100%; position: relative; overflow: hidden; }
  .canvas-container canvas { position: absolute; top: 0; left: 0; }

  /* SVG graph rendering */
  .graph-svg { width: 100%; height: 100%; }
  .node-group { cursor: pointer; }
  .node-group:hover .node-rect { filter: brightness(1.3); }
  .node-rect { rx: 8; ry: 8; stroke-width: 1.5; }
  .node-label { fill: #e2e8f0; font-family: 'DM Sans', sans-serif; font-size: 11px; font-weight: 600;
                text-anchor: middle; dominant-baseline: central; pointer-events: none; }
  .node-badge { font-family: 'JetBrains Mono', monospace; font-size: 8px; fill: white;
                text-anchor: middle; dominant-baseline: central; pointer-events: none; }
  .edge-line { stroke: #475569; stroke-width: 1; fill: none; }
  .edge-label { fill: #64748b; font-size: 8px; font-family: 'DM Sans', sans-serif;
                text-anchor: middle; dominant-baseline: central; }

  /* Minimap */
  .minimap { position: absolute; bottom: 12px; right: 12px; width: 180px; height: 120px;
             background: #1e293bcc; border: 1px solid #334155; border-radius: 8px; overflow: hidden;
             backdrop-filter: blur(4px); }

  /* Controls */
  .controls { position: absolute; top: 12px; right: 12px; z-index: 10; display: flex; gap: 4px; }
  .ctrl-btn { background: #1e293b; border: 1px solid #334155; color: #94a3b8; padding: 6px 10px;
              border-radius: 6px; cursor: pointer; font-size: 13px; }
  .ctrl-btn:hover { background: #334155; color: #e2e8f0; }

  /* Filter chips */
  .filter-bar { position: absolute; top: 52px; left: 12px; z-index: 10; display: flex; flex-wrap: wrap; gap: 4px; }
  .filter-chip { padding: 4px 10px; border-radius: 12px; font-size: 11px; cursor: pointer;
                  border: 1px solid #334155; background: #1e293b; color: #94a3b8; transition: all 0.15s; }
  .filter-chip.active { color: white; }
  .filter-chip:hover { border-color: #475569; }

  /* Header bar */
  .header { background: #1e293b; border-bottom: 1px solid #334155; padding: 8px 16px;
            display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }
  .header h1 { font-size: 15px; font-weight: 700; color: #f1f5f9; }
  .header .stats { display: flex; gap: 16px; font-size: 12px; color: #64748b; }
  .header .stats span { font-family: 'JetBrains Mono', monospace; color: #38bdf8; }
</style>
</head>
<body>
<div id="app">
  <!-- Header -->
  <div class="header">
    <h1>PTS Data Architecture Explorer V4</h1>
    <div class="stats" id="headerStats"></div>
  </div>

  <!-- Tabs -->
  <div class="tab-bar">
    <div class="tab active" data-view="graph"><span class="tab-icon">&#x1F310;</span>Entity Graph</div>
    <div class="tab" data-view="flow"><span class="tab-icon">&#x27A1;</span>Data Flow</div>
    <div class="tab" data-view="integration"><span class="tab-icon">&#x1F517;</span>Integration Map</div>
    <div class="tab" data-view="dashboard"><span class="tab-icon">&#x1F4CA;</span>Dashboard</div>
  </div>

  <!-- View 1: Entity Relationship Graph (SVG-based) -->
  <div class="view active" id="view-graph" style="flex-direction: row;">
    <div class="rf-container" id="graphContainer">
      <div class="search-bar">
        <input type="text" id="graphSearch" placeholder="Search entities..." />
      </div>
      <div class="filter-bar" id="categoryFilters"></div>
      <div class="controls">
        <button class="ctrl-btn" id="zoomIn">+</button>
        <button class="ctrl-btn" id="zoomOut">-</button>
        <button class="ctrl-btn" id="fitView">Fit</button>
      </div>
      <svg class="graph-svg" id="graphSvg"></svg>
      <div class="legend" id="graphLegend"></div>
    </div>
    <div class="detail-panel" id="detailPanel">
      <div id="detailContent"></div>
    </div>
  </div>

  <!-- View 2: Data Flow Pipeline (SVG-based) -->
  <div class="view" id="view-flow">
    <div class="rf-container">
      <svg class="graph-svg" id="flowSvg"></svg>
    </div>
  </div>

  <!-- View 3: Repository Integration Map (SVG-based) -->
  <div class="view" id="view-integration">
    <div class="rf-container">
      <svg class="graph-svg" id="integrationSvg"></svg>
    </div>
  </div>

  <!-- View 4: Dashboard -->
  <div class="view" id="view-dashboard">
    <div class="dashboard" id="dashboardGrid"></div>
  </div>
</div>

<script>
// Architecture data (inlined by Python)
const ARCH = __ARCHITECTURE_DATA__;

// ============================================================
// TAB SWITCHING
// ============================================================
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('view-' + tab.dataset.view).classList.add('active');
  });
});

// ============================================================
// HEADER STATS
// ============================================================
const d = ARCH.dashboard;
document.getElementById('headerStats').innerHTML =
  `Entities: <span>${d.totalEntities}</span> | Properties: <span>${d.totalProperties}</span> | ` +
  `Relationships: <span>${d.totalRelationships}</span> | Multi-project: <span>${d.multiProjectEntities}</span>`;

// ============================================================
// VIEW 1: ENTITY GRAPH (SVG + pan/zoom)
// ============================================================
(function() {
  const nodes = ARCH.graph.nodes;
  const edges = ARCH.graph.edges;
  const svg = document.getElementById('graphSvg');
  const container = document.getElementById('graphContainer');

  // Layout: arrange nodes by category in columns
  const catOrder = Object.keys(ARCH.categories);
  const catGroups = {};
  nodes.forEach(n => {
    const cat = n.data.category;
    if (!catGroups[cat]) catGroups[cat] = [];
    catGroups[cat].push(n);
  });

  const COL_WIDTH = 220;
  const ROW_HEIGHT = 56;
  const NODE_W = 180;
  const NODE_H = 40;
  const PADDING_X = 60;
  const PADDING_Y = 80;

  let col = 0;
  catOrder.forEach(cat => {
    const group = catGroups[cat] || [];
    group.forEach((n, row) => {
      n.position.x = PADDING_X + col * COL_WIDTH;
      n.position.y = PADDING_Y + row * ROW_HEIGHT;
    });
    if (group.length > 0) col++;
  });

  const totalW = PADDING_X * 2 + col * COL_WIDTH;
  const maxRows = Math.max(...Object.values(catGroups).map(g => g.length), 1);
  const totalH = PADDING_Y * 2 + maxRows * ROW_HEIGHT;

  // Build lookup
  const nodeMap = {};
  nodes.forEach(n => { nodeMap[n.id] = n; });

  // Pan/zoom state
  let vx = 0, vy = 0, scale = 1;
  const svgRect = () => svg.getBoundingClientRect();

  function setViewBox() {
    const r = svgRect();
    const w = r.width / scale;
    const h = r.height / scale;
    svg.setAttribute('viewBox', `${vx} ${vy} ${w} ${h}`);
  }

  // Category filter state
  const activeCategories = new Set(catOrder);

  function isVisible(nodeId) {
    const n = nodeMap[nodeId];
    return n && activeCategories.has(n.data.category);
  }

  function render() {
    svg.innerHTML = '';

    // Draw edges first (behind nodes)
    const edgeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    edges.forEach(e => {
      const src = nodeMap[e.source];
      const tgt = nodeMap[e.target];
      if (!src || !tgt || !isVisible(e.source) || !isVisible(e.target)) return;

      const x1 = src.position.x + NODE_W / 2;
      const y1 = src.position.y + NODE_H / 2;
      const x2 = tgt.position.x + NODE_W / 2;
      const y2 = tgt.position.y + NODE_H / 2;

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', x1); line.setAttribute('y1', y1);
      line.setAttribute('x2', x2); line.setAttribute('y2', y2);
      line.setAttribute('class', 'edge-line');
      if (e.animated) line.setAttribute('stroke-dasharray', '4 2');
      edgeGroup.appendChild(line);

      if (e.label) {
        const lbl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        lbl.setAttribute('x', (x1 + x2) / 2);
        lbl.setAttribute('y', (y1 + y2) / 2 - 4);
        lbl.setAttribute('class', 'edge-label');
        lbl.textContent = e.label;
        edgeGroup.appendChild(lbl);
      }
    });
    svg.appendChild(edgeGroup);

    // Draw nodes
    const nodeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    nodes.forEach(n => {
      if (!isVisible(n.id)) return;
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('class', 'node-group');
      g.setAttribute('transform', `translate(${n.position.x}, ${n.position.y})`);

      // Background rect
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('width', NODE_W);
      rect.setAttribute('height', NODE_H);
      rect.setAttribute('class', 'node-rect');
      rect.setAttribute('fill', n.data.color + '33');
      rect.setAttribute('stroke', n.data.color);
      g.appendChild(rect);

      // Label
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', NODE_W / 2);
      text.setAttribute('y', NODE_H / 2 - 4);
      text.setAttribute('class', 'node-label');
      text.textContent = n.data.label;
      g.appendChild(text);

      // Project badges
      const projectColors = { BD_ENGINE: '#3b82f6', DATA_SCRAPER: '#10b981', N8N_BUILDER: '#f97316', V2_CURATED: '#64748b' };
      const badges = n.data.projects || [];
      badges.forEach((p, i) => {
        const cx = 12 + i * 14;
        const cy = NODE_H - 6;
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', cx); circle.setAttribute('cy', cy); circle.setAttribute('r', 4);
        circle.setAttribute('fill', projectColors[p] || '#64748b');
        circle.setAttribute('stroke', '#0f172a'); circle.setAttribute('stroke-width', '1');
        g.appendChild(circle);
      });

      // Records count
      const rec = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      rec.setAttribute('x', NODE_W - 8);
      rec.setAttribute('y', NODE_H - 6);
      rec.setAttribute('class', 'node-badge');
      rec.setAttribute('text-anchor', 'end');
      rec.setAttribute('fill', '#64748b');
      rec.textContent = n.data.records;
      g.appendChild(rec);

      // Click handler
      g.addEventListener('click', () => showDetail(n));
      nodeGroup.appendChild(g);
    });
    svg.appendChild(nodeGroup);

    setViewBox();
  }

  // Category filter chips
  const filterBar = document.getElementById('categoryFilters');
  catOrder.forEach(cat => {
    const color = ARCH.categories[cat]?.color || '#64748b';
    const chip = document.createElement('div');
    chip.className = 'filter-chip active';
    chip.style.borderColor = color;
    chip.style.background = color + '33';
    chip.textContent = cat;
    chip.addEventListener('click', () => {
      if (activeCategories.has(cat)) {
        activeCategories.delete(cat);
        chip.classList.remove('active');
        chip.style.background = '#1e293b';
      } else {
        activeCategories.add(cat);
        chip.classList.add('active');
        chip.style.background = color + '33';
      }
      render();
    });
    filterBar.appendChild(chip);
  });

  // Legend
  const legend = document.getElementById('graphLegend');
  const projectLegend = [
    ['BD-Engine', '#3b82f6'], ['Data-Scraper', '#10b981'], ['N8N-Builder', '#f97316'], ['V2-Curated', '#64748b']
  ];
  projectLegend.forEach(([label, color]) => {
    const item = document.createElement('div');
    item.className = 'legend-item';
    item.innerHTML = `<div class="legend-dot" style="background:${color}"></div>${label}`;
    legend.appendChild(item);
  });

  // Search
  document.getElementById('graphSearch').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    nodes.forEach(n => {
      const match = !q || n.data.label.toLowerCase().includes(q) ||
                    n.data.category.toLowerCase().includes(q);
      // Dim non-matching nodes by reducing opacity through SVG
      const svgNode = svg.querySelector(`g[transform*="translate(${n.position.x}"]`);
      if (svgNode) svgNode.style.opacity = match ? 1 : 0.2;
    });
  });

  // Pan/zoom
  svg.addEventListener('wheel', (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    scale *= delta;
    scale = Math.max(0.2, Math.min(3, scale));
    setViewBox();
  });

  let dragging = false, lastX, lastY;
  svg.addEventListener('mousedown', (e) => { dragging = true; lastX = e.clientX; lastY = e.clientY; });
  svg.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    vx -= (e.clientX - lastX) / scale;
    vy -= (e.clientY - lastY) / scale;
    lastX = e.clientX; lastY = e.clientY;
    setViewBox();
  });
  svg.addEventListener('mouseup', () => { dragging = false; });
  svg.addEventListener('mouseleave', () => { dragging = false; });

  // Zoom controls
  document.getElementById('zoomIn').addEventListener('click', () => { scale *= 1.2; setViewBox(); });
  document.getElementById('zoomOut').addEventListener('click', () => { scale /= 1.2; setViewBox(); });
  document.getElementById('fitView').addEventListener('click', () => {
    vx = 0; vy = 0; scale = 1; setViewBox();
  });

  // Detail panel
  function showDetail(node) {
    const panel = document.getElementById('detailPanel');
    const content = document.getElementById('detailContent');
    panel.classList.add('open');

    const nd = node.data;
    const projectColors = { BD_ENGINE: '#3b82f6', DATA_SCRAPER: '#10b981', N8N_BUILDER: '#f97316', V2_CURATED: '#64748b' };
    const projectLabels = { BD_ENGINE: 'BD', DATA_SCRAPER: 'DS', N8N_BUILDER: 'N8N', V2_CURATED: 'V2' };

    let badges = (nd.projects || []).map(p =>
      `<span class="badge" style="background:${projectColors[p]||'#64748b'}">${projectLabels[p]||p}</span>`
    ).join('');

    let props = (nd.properties || []).map(p =>
      `<div class="prop-row"><span class="prop-name">${p.name}</span><span class="prop-type">${p.type}</span></div>`
    ).join('');

    let sources = (nd.sources || []).map(s => `<span class="badge" style="background:#334155">${s}</span>`).join(' ');

    content.innerHTML = `
      <h3 style="color:${nd.color}">${nd.label}</h3>
      <div style="margin:8px 0">${badges}</div>
      <div style="font-size:12px;color:#94a3b8;margin:8px 0">${nd.description || ''}</div>
      <div style="font-size:11px;color:#64748b;margin:8px 0">
        PK: <span class="mono" style="color:#38bdf8">${nd.pk}</span> |
        Records: <span class="mono" style="color:#38bdf8">${nd.records}</span> |
        Props: <span class="mono" style="color:#38bdf8">${nd.propCount}</span>
      </div>
      <div style="margin:8px 0;font-size:11px;color:#64748b">Sources: ${sources}</div>
      <h4 style="font-size:12px;color:#94a3b8;margin:12px 0 4px">Properties</h4>
      ${props || '<div style="font-size:12px;color:#475569">No properties</div>'}
    `;
  }

  render();
})();

// ============================================================
// VIEW 2: DATA FLOW PIPELINE
// ============================================================
(function() {
  const nodes = ARCH.flow.nodes;
  const edges = ARCH.flow.edges;
  const svg = document.getElementById('flowSvg');

  const NODE_W = 160;
  const NODE_H = 48;

  function render() {
    svg.innerHTML = '';
    const nodeMap = {};
    nodes.forEach(n => { nodeMap[n.id] = n; });

    // Draw edges
    edges.forEach(e => {
      const src = nodeMap[e.source];
      const tgt = nodeMap[e.target];
      if (!src || !tgt) return;

      const x1 = src.position.x + NODE_W;
      const y1 = src.position.y + NODE_H / 2;
      const x2 = tgt.position.x;
      const y2 = tgt.position.y + NODE_H / 2;
      const mx = (x1 + x2) / 2;

      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`);
      path.setAttribute('class', 'edge-line');
      path.setAttribute('stroke-dasharray', '4 2');
      svg.appendChild(path);

      if (e.label) {
        const lbl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        lbl.setAttribute('x', mx);
        lbl.setAttribute('y', (y1 + y2) / 2 - 6);
        lbl.setAttribute('class', 'edge-label');
        lbl.textContent = e.label;
        svg.appendChild(lbl);
      }
    });

    // Draw nodes
    nodes.forEach(n => {
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('transform', `translate(${n.position.x}, ${n.position.y})`);

      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('width', NODE_W);
      rect.setAttribute('height', NODE_H);
      rect.setAttribute('rx', 8);
      rect.setAttribute('fill', (n.data.color || '#475569') + '33');
      rect.setAttribute('stroke', n.data.color || '#475569');
      rect.setAttribute('stroke-width', '1.5');
      g.appendChild(rect);

      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('x', NODE_W / 2);
      label.setAttribute('y', NODE_H / 2 - 4);
      label.setAttribute('class', 'node-label');
      label.setAttribute('font-size', '10');
      label.textContent = n.data.label;
      g.appendChild(label);

      if (n.data.subLabel) {
        const sub = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        sub.setAttribute('x', NODE_W / 2);
        sub.setAttribute('y', NODE_H / 2 + 10);
        sub.setAttribute('class', 'edge-label');
        sub.setAttribute('text-anchor', 'middle');
        sub.textContent = n.data.subLabel;
        g.appendChild(sub);
      }

      svg.appendChild(g);
    });

    // Column headers
    const headers = [
      { x: 40, label: 'DATA SOURCES' },
      { x: 380, label: 'TRANSFORM (8 ENGINES + N8N)' },
      { x: 730, label: 'DESTINATIONS' },
    ];
    headers.forEach(h => {
      const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      t.setAttribute('x', h.x);
      t.setAttribute('y', 20);
      t.setAttribute('fill', '#64748b');
      t.setAttribute('font-size', '11');
      t.setAttribute('font-weight', '600');
      t.setAttribute('letter-spacing', '1');
      t.textContent = h.label;
      svg.appendChild(t);
    });

    svg.setAttribute('viewBox', `-20 -10 900 ${Math.max(nodes.length * 80, 600)}`);
  }

  render();
})();

// ============================================================
// VIEW 3: INTEGRATION MAP
// ============================================================
(function() {
  const nodes = ARCH.integration.nodes;
  const edges = ARCH.integration.edges;
  const svg = document.getElementById('integrationSvg');

  function render() {
    svg.innerHTML = '';
    const nodeMap = {};
    nodes.forEach(n => { nodeMap[n.id] = n; });

    // Draw edges
    edges.forEach(e => {
      const src = nodeMap[e.source];
      const tgt = nodeMap[e.target];
      if (!src || !tgt) return;

      const x1 = src.position.x + 80;
      const y1 = src.position.y + 25;
      const x2 = tgt.position.x + 80;
      const y2 = tgt.position.y + 25;

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', x1); line.setAttribute('y1', y1);
      line.setAttribute('x2', x2); line.setAttribute('y2', y2);
      line.setAttribute('stroke', '#475569'); line.setAttribute('stroke-width', '2');
      svg.appendChild(line);

      if (e.label) {
        const lbl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        lbl.setAttribute('x', (x1 + x2) / 2);
        lbl.setAttribute('y', (y1 + y2) / 2 - 6);
        lbl.setAttribute('class', 'edge-label');
        lbl.textContent = e.label;
        svg.appendChild(lbl);
      }
    });

    // Draw nodes
    nodes.forEach(n => {
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('transform', `translate(${n.position.x}, ${n.position.y})`);

      const isInfra = n.data.nodeType === 'infrastructure';
      const w = isInfra ? 140 : 180;
      const h = 50;

      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('width', w);
      rect.setAttribute('height', h);
      rect.setAttribute('rx', isInfra ? 25 : 8);
      rect.setAttribute('fill', (n.data.color || '#475569') + (isInfra ? '55' : '33'));
      rect.setAttribute('stroke', n.data.color || '#475569');
      rect.setAttribute('stroke-width', isInfra ? '2' : '1.5');
      g.appendChild(rect);

      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('x', w / 2);
      label.setAttribute('y', h / 2 - 4);
      label.setAttribute('class', 'node-label');
      label.setAttribute('font-size', isInfra ? '11' : '12');
      label.textContent = n.data.label;
      g.appendChild(label);

      if (n.data.subLabel) {
        const sub = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        sub.setAttribute('x', w / 2);
        sub.setAttribute('y', h / 2 + 10);
        sub.setAttribute('class', 'edge-label');
        sub.setAttribute('text-anchor', 'middle');
        sub.textContent = n.data.subLabel;
        g.appendChild(sub);
      }

      svg.appendChild(g);
    });

    svg.setAttribute('viewBox', '0 50 800 500');
  }

  render();
})();

// ============================================================
// VIEW 4: DASHBOARD
// ============================================================
(function() {
  const d = ARCH.dashboard;
  const grid = document.getElementById('dashboardGrid');

  // Summary card
  grid.innerHTML = `
    <div class="dash-card" style="grid-column: span 2;">
      <h3>System Overview</h3>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;text-align:center;">
        <div><div class="stat-big">${d.totalEntities}</div><div class="stat-label">Entities</div></div>
        <div><div class="stat-big">${d.totalProperties}</div><div class="stat-label">Properties</div></div>
        <div><div class="stat-big">${d.totalRelationships}</div><div class="stat-label">Relationships</div></div>
        <div><div class="stat-big">${d.multiProjectEntities}</div><div class="stat-label">Cross-Repo</div></div>
      </div>
    </div>

    <div class="dash-card">
      <h3>Categories</h3>
      ${Object.entries(d.categories).map(([name, info]) => `
        <div class="cat-bar">
          <div class="cat-dot" style="background:${info.color}"></div>
          <span class="cat-label">${name}</span>
          <span class="cat-count">${info.count}</span>
        </div>
      `).join('')}
    </div>

    <div class="dash-card">
      <h3>Storage Infrastructure</h3>
      <div class="stat-row"><span class="stat-label">Qdrant Collections</span><span class="stat-value" style="color:#06b6d4">${d.qdrantCollections}</span></div>
      <div class="stat-row"><span class="stat-label">SQLite Databases</span><span class="stat-value" style="color:#06b6d4">${d.sqliteDatabases}</span></div>
      <div class="stat-row"><span class="stat-label">Neo4j Node Types</span><span class="stat-value" style="color:#10b981">${d.neo4jNodeTypes}</span></div>
      <div class="stat-row"><span class="stat-label">Neo4j Relationship Types</span><span class="stat-value" style="color:#10b981">${d.neo4jRelTypes}</span></div>
      <div class="stat-row"><span class="stat-label">API Endpoints</span><span class="stat-value" style="color:#f43f5e">${d.apiEndpoints}</span></div>
    </div>

    <div class="dash-card">
      <h3>Pipeline</h3>
      <div class="stat-row"><span class="stat-label">BD Engines</span><span class="stat-value" style="color:#8b5cf6">${d.engines || 8}</span></div>
      <div class="stat-row"><span class="stat-label">Data Flows</span><span class="stat-value" style="color:#8b5cf6">${d.dataFlows}</span></div>
      <div class="stat-row"><span class="stat-label">N8N Workflows</span><span class="stat-value" style="color:#f97316">${d.n8nWorkflows || 40}</span></div>
    </div>

    <div class="dash-card" style="grid-column: span 2;">
      <h3>Repository Contributions</h3>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;text-align:center;">
        <div style="border-right:1px solid #334155;">
          <div style="font-size:13px;color:#3b82f6;font-weight:600;">BD-Automation-Engine</div>
          <div style="font-size:11px;color:#64748b;margin-top:4px;">40 entities | 506 props | 65 rels</div>
          <div style="font-size:11px;color:#64748b;">8 engines | 340 APIs | 9 Qdrant</div>
        </div>
        <div style="border-right:1px solid #334155;">
          <div style="font-size:13px;color:#10b981;font-weight:600;">Data-Scraper</div>
          <div style="font-size:11px;color:#64748b;margin-top:4px;">23 entities | 410 props | 30 rels</div>
          <div style="font-size:11px;color:#64748b;">33 domains | 250 APIs | 2 Qdrant</div>
        </div>
        <div>
          <div style="font-size:13px;color:#f97316;font-weight:600;">N8N-Builder</div>
          <div style="font-size:11px;color:#64748b;margin-top:4px;">32 entities | 419 props | 22 rels</div>
          <div style="font-size:11px;color:#64748b;">40 workflows | 267 APIs | 3 Qdrant</div>
        </div>
      </div>
    </div>
  `;
})();
</script>
</body>
</html>'''


# ====================================================================
# V5: React Flow + elkjs + htm visualization
# ====================================================================

def generate_v5_html(
    entities: dict,
    relationships: list[dict],
    infrastructure: dict,
) -> str:
    """Generate V5 HTML with React Flow visualization."""

    # Reuse V4 data prep (already in React Flow node/edge format)
    graph_nodes = _build_graph_nodes(entities)
    graph_edges = _build_graph_edges(relationships)
    flow_nodes = _build_flow_nodes(infrastructure)
    flow_edges = _build_flow_edges()
    integration_nodes = _build_integration_nodes()
    integration_edges = _build_integration_edges()
    dashboard = _build_dashboard_data(entities, relationships, infrastructure)

    # Enhance edge styling for V5
    for edge in graph_edges:
        card = edge.get('data', {}).get('cardinality', 'FK')
        if card == 'FK':
            edge['style'] = {'stroke': '#475569', 'strokeWidth': 1.5}
        elif card == 'one-many':
            edge['style'] = {'stroke': '#475569', 'strokeWidth': 1.5, 'strokeDasharray': '8 4'}
        elif card in ('many', 'many-to-many'):
            edge['style'] = {'stroke': '#64748b', 'strokeWidth': 1.5, 'strokeDasharray': '3 3'}
            edge['animated'] = True
        # Add arrow markers
        edge['markerEnd'] = {'type': 'arrowclosed', 'color': '#475569', 'width': 15, 'height': 15}

    arch_data = json.dumps({
        'graph': {'nodes': graph_nodes, 'edges': graph_edges},
        'flow': {'nodes': flow_nodes, 'edges': flow_edges},
        'integration': {'nodes': integration_nodes, 'edges': integration_edges},
        'dashboard': dashboard,
        'categories': {k: {'color': v['color']} for k, v in CATEGORY_DEFS.items()},
    }, indent=None, ensure_ascii=False)

    return _V5_HTML_TEMPLATE.replace('__ARCHITECTURE_DATA__', arch_data)


_V5_HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PTS Data Architecture Explorer V5</title>

<!-- Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">

<!-- React Flow CSS -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@xyflow/react@12.3.2/dist/style.css">

<!-- Tailwind -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Import Map -->
<script type="importmap">
{
  "imports": {
    "react": "https://esm.sh/react@18.2.0",
    "react/jsx-runtime": "https://esm.sh/react@18.2.0/jsx-runtime",
    "react-dom": "https://esm.sh/react-dom@18.2.0?external=react",
    "react-dom/client": "https://esm.sh/react-dom@18.2.0/client?external=react",
    "@xyflow/react": "https://esm.sh/@xyflow/react@12.3.2?external=react,react-dom",
    "elkjs/lib/elk.bundled.js": "https://esm.sh/elkjs@0.9.3/lib/elk.bundled.js",
    "htm": "https://esm.sh/htm@3.1.1"
  }
}
</script>

<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'DM Sans', sans-serif; background: #0f172a; color: #e2e8f0; overflow: hidden; }
  .mono { font-family: 'JetBrains Mono', monospace; }
  #root { width: 100vw; height: 100vh; }

  /* React Flow overrides for dark theme */
  .react-flow { background: #0f172a !important; }
  .react-flow__minimap { background: #1e293b !important; border: 1px solid #334155 !important; border-radius: 8px !important; }
  .react-flow__controls { border: 1px solid #334155 !important; border-radius: 8px !important; overflow: hidden; }
  .react-flow__controls-button { background: #1e293b !important; border-bottom: 1px solid #334155 !important; fill: #94a3b8 !important; }
  .react-flow__controls-button:hover { background: #334155 !important; fill: #e2e8f0 !important; }
  .react-flow__attribution { display: none !important; }
  .react-flow__edge-text { fill: #94a3b8 !important; font-size: 9px !important; }
  .react-flow__edge-textbg { fill: #0f172a !important; }
  .react-flow__background pattern line { stroke: #1e293b !important; }

  /* Entity node styles */
  .entity-node { border-radius: 8px; overflow: hidden; font-size: 12px; cursor: pointer; transition: box-shadow 0.15s; }
  .entity-node:hover { box-shadow: 0 0 20px rgba(56, 189, 248, 0.3); }
  .entity-header { padding: 5px 8px; display: flex; justify-content: space-between; align-items: center; }
  .entity-header span:first-child { color: white; font-weight: 600; font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px; }
  .record-badge { background: rgba(0,0,0,0.3); color: white; padding: 1px 6px; border-radius: 8px; font-size: 9px; font-family: 'JetBrains Mono', monospace; }
  .entity-body { padding: 4px 8px 5px; display: flex; align-items: center; gap: 3px; background: rgba(0,0,0,0.15); }
  .project-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
  .prop-count { margin-left: auto; color: #64748b; font-size: 10px; }

  /* Flow node styles */
  .flow-node { border-radius: 8px; overflow: hidden; font-size: 11px; }
  .flow-node-inner { padding: 8px 10px; text-align: center; }
  .flow-label { color: #e2e8f0; font-weight: 600; }
  .flow-sublabel { color: #94a3b8; font-size: 10px; margin-top: 2px; }

  /* Integration node styles */
  .integ-node { padding: 10px; text-align: center; font-size: 11px; }
  .integ-label { color: #e2e8f0; font-weight: 600; }
  .integ-sublabel { color: #94a3b8; font-size: 10px; margin-top: 2px; }

  /* Dashboard */
  .dash-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; padding: 24px; overflow-y: auto; align-content: start; height: 100%; }
  .dash-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; }
  .dash-card h3 { font-size: 14px; font-weight: 600; color: #94a3b8; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
  .stat-big { font-size: 36px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #38bdf8; }
  .stat-label { font-size: 13px; color: #cbd5e1; }
  .stat-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #1e293b; }
  .stat-value { font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
  .cat-bar { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
  .cat-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

  /* Detail panel */
  .detail-panel { width: 380px; background: #1e293b; border-left: 1px solid #334155; overflow-y: auto; padding: 16px; flex-shrink: 0; }
  .detail-panel .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; margin: 2px; color: white; }
  .detail-panel .prop-row { display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #334155; font-size: 11px; }
  .detail-panel .prop-name { color: #38bdf8; }
  .detail-panel .prop-type { color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 10px; }

  /* Search & filters */
  .search-input { background: #1e293b; border: 1px solid #334155; color: #e2e8f0; padding: 8px 12px; border-radius: 6px; font-size: 13px; width: 240px; outline: none; }
  .search-input:focus { border-color: #38bdf8; }
  .search-input::placeholder { color: #64748b; }
  .filter-chip { padding: 4px 10px; border-radius: 12px; font-size: 11px; cursor: pointer; border: none; transition: all 0.15s; }

  /* Loading spinner */
  .loading { display: flex; align-items: center; justify-content: center; height: 100%; color: #94a3b8; font-size: 14px; }
  .loading::before { content: ''; width: 20px; height: 20px; border: 2px solid #334155; border-top-color: #38bdf8; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 10px; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div id="root"><div class="loading">Loading React Flow...</div></div>

<!-- Architecture Data -->
<script>const ARCH = __ARCHITECTURE_DATA__;</script>

<!-- React App -->
<script type="module">
// ============================================================
// IMPORTS
// ============================================================
import { createElement, useState, useCallback, useMemo, useEffect, useRef, memo } from 'react';
import { createRoot } from 'react-dom/client';
import {
  ReactFlow, MiniMap, Controls, Background,
  Handle, Position, MarkerType,
  useNodesState, useEdgesState,
  ReactFlowProvider
} from '@xyflow/react';
import ELK from 'elkjs/lib/elk.bundled.js';
import htm from 'htm';

const html = htm.bind(createElement);

// ============================================================
// CONSTANTS
// ============================================================
const PROJECT_COLORS = { BD_ENGINE: '#3b82f6', DATA_SCRAPER: '#10b981', N8N_BUILDER: '#f97316', V2_CURATED: '#64748b' };
const PROJECT_LABELS = { BD_ENGINE: 'BD', DATA_SCRAPER: 'DS', N8N_BUILDER: 'N8N', V2_CURATED: 'V2' };
const NODE_W = 200;
const NODE_H = 55;
const FLOW_W = 160;
const FLOW_H = 50;

// ============================================================
// ELK LAYOUT ENGINE
// ============================================================
const elk = new ELK();
const layoutCache = {};

async function elkLayout(nodes, edges, direction, cacheKey) {
  if (cacheKey && layoutCache[cacheKey]) return layoutCache[cacheKey];

  const graph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': direction,
      'elk.spacing.nodeNode': '40',
      'elk.spacing.edgeNode': '25',
      'elk.layered.spacing.nodeNodeBetweenLayers': '80',
      'elk.layered.spacing.edgeEdgeBetweenLayers': '15',
      'elk.edgeRouting': 'ORTHOGONAL',
    },
    children: nodes.map(n => ({
      id: n.id,
      width: n._w || NODE_W,
      height: n._h || NODE_H,
    })),
    edges: edges.map(e => ({
      id: e.id,
      sources: [e.source],
      targets: [e.target],
    })),
  };

  const result = await elk.layout(graph);
  const layouted = {
    nodes: nodes.map(n => {
      const en = result.children.find(c => c.id === n.id);
      return en ? { ...n, position: { x: en.x, y: en.y } } : n;
    }),
    edges,
  };

  if (cacheKey) layoutCache[cacheKey] = layouted;
  return layouted;
}

// ============================================================
// CUSTOM NODES
// ============================================================

// --- View 1: Entity Node ---
const EntityNode = memo(function EntityNode({ data }) {
  return html`
    <div className="entity-node" style=${{ border: '2px solid ' + data.color, background: data.color + '15', width: NODE_W + 'px' }}>
      <${Handle} type="target" position=${Position.Top} style=${{ background: data.color, width: 8, height: 8, border: 'none' }} />
      <div className="entity-header" style=${{ background: data.color }}>
        <span title=${data.label}>${data.label}</span>
        <span className="record-badge">${data.records}</span>
      </div>
      <div className="entity-body">
        ${(data.projects || []).map(p => html`
          <span key=${p} className="project-dot" style=${{ background: PROJECT_COLORS[p] || '#64748b' }} title=${PROJECT_LABELS[p] || p} />
        `)}
        <span className="prop-count">${data.propCount} props</span>
      </div>
      <${Handle} type="source" position=${Position.Bottom} style=${{ background: data.color, width: 8, height: 8, border: 'none' }} />
    </div>
  `;
});

// --- View 2: Flow Node ---
const FlowNode = memo(function FlowNode({ data }) {
  const c = data.color || '#475569';
  return html`
    <div className="flow-node" style=${{ border: '2px solid ' + c, background: c + '15', width: FLOW_W + 'px' }}>
      <${Handle} type="target" position=${Position.Left} style=${{ background: c, width: 8, height: 8, border: 'none' }} />
      <div className="flow-node-inner">
        <div className="flow-label">${data.label}</div>
        ${data.subLabel && html`<div className="flow-sublabel">${data.subLabel}</div>`}
      </div>
      <${Handle} type="source" position=${Position.Right} style=${{ background: c, width: 8, height: 8, border: 'none' }} />
    </div>
  `;
});

// --- View 3: Integration Node ---
const IntegrationNode = memo(function IntegrationNode({ data }) {
  const c = data.color || '#475569';
  const isInfra = data.nodeType === 'infrastructure';
  return html`
    <div className="integ-node" style=${{
      border: (isInfra ? '3px' : '2px') + ' solid ' + c,
      borderRadius: isInfra ? '24px' : '8px',
      background: c + (isInfra ? '30' : '15'),
      width: (isInfra ? 140 : 180) + 'px',
    }}>
      <${Handle} type="target" position=${Position.Left} style=${{ background: c, width: 8, height: 8, border: 'none' }} />
      <div className="integ-label">${data.label}</div>
      ${data.subLabel && html`<div className="integ-sublabel">${data.subLabel}</div>`}
      <${Handle} type="source" position=${Position.Right} style=${{ background: c, width: 8, height: 8, border: 'none' }} />
    </div>
  `;
});

// Node type registries (stable refs - outside components)
const ENTITY_NODE_TYPES = { entityNode: EntityNode };
const FLOW_NODE_TYPES = { flowNode: FlowNode };
const INTEGRATION_NODE_TYPES = { integrationNode: IntegrationNode };

// ============================================================
// VIEW 1: ENTITY RELATIONSHIP GRAPH
// ============================================================
function EntityGraphView({ onSelectNode }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [activeCategories, setActiveCategories] = useState(() => new Set(Object.keys(ARCH.categories)));

  useEffect(() => {
    const raw = ARCH.graph.nodes.map(n => ({ ...n, _w: NODE_W, _h: NODE_H }));
    elkLayout(raw, ARCH.graph.edges, 'DOWN', 'entityGraph').then(result => {
      setNodes(result.nodes);
      setEdges(result.edges);
      setLoading(false);
    });
  }, []);

  const filteredNodes = useMemo(() => {
    const q = search.toLowerCase();
    return nodes.map(n => ({
      ...n,
      hidden: !activeCategories.has(n.data.category) ||
              (q && !n.data.label.toLowerCase().includes(q) &&
               !n.data.category.toLowerCase().includes(q) &&
               !(n.data.properties || []).some(p => p.name.toLowerCase().includes(q))),
    }));
  }, [nodes, activeCategories, search]);

  const filteredEdges = useMemo(() => {
    const visible = new Set(filteredNodes.filter(n => !n.hidden).map(n => n.id));
    return edges.map(e => ({ ...e, hidden: !visible.has(e.source) || !visible.has(e.target) }));
  }, [edges, filteredNodes]);

  const onNodeClick = useCallback((_, node) => onSelectNode(node.data), [onSelectNode]);

  const toggleCategory = useCallback(cat => {
    setActiveCategories(prev => {
      const next = new Set(prev);
      next.has(cat) ? next.delete(cat) : next.add(cat);
      return next;
    });
  }, []);

  if (loading) return html`<div className="loading">Computing entity layout...</div>`;

  return html`
    <div style=${{ width: '100%', height: '100%', position: 'relative' }}>
      <!-- Search -->
      <div style=${{ position: 'absolute', top: 12, left: 12, zIndex: 10 }}>
        <input className="search-input" type="text" placeholder="Search entities... (/ to focus)"
          value=${search} onInput=${e => setSearch(e.target.value)} />
      </div>

      <!-- Category filters -->
      <div style=${{ position: 'absolute', top: 52, left: 12, zIndex: 10, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
        ${Object.entries(ARCH.categories).map(([cat, info]) => html`
          <button key=${cat} className="filter-chip" onClick=${() => toggleCategory(cat)}
            style=${{
              background: activeCategories.has(cat) ? info.color + '33' : '#1e293b',
              color: activeCategories.has(cat) ? 'white' : '#64748b',
              border: '1px solid ' + info.color,
            }}>${cat}</button>
        `)}
      </div>

      <!-- Legend -->
      <div style=${{ position: 'absolute', bottom: 12, left: 12, zIndex: 10, background: '#1e293bdd', border: '1px solid #334155', borderRadius: 8, padding: 10, backdropFilter: 'blur(8px)' }}>
        ${[['BD-Engine','#3b82f6'],['Data-Scraper','#10b981'],['N8N-Builder','#f97316'],['V2-Curated','#64748b']].map(([l,c]) => html`
          <div key=${l} style=${{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, margin: '3px 0' }}>
            <span style=${{ width: 10, height: 10, borderRadius: '50%', background: c, display: 'inline-block' }} />${l}
          </div>
        `)}
      </div>

      <${ReactFlow}
        nodes=${filteredNodes} edges=${filteredEdges}
        onNodesChange=${onNodesChange} onEdgesChange=${onEdgesChange}
        nodeTypes=${ENTITY_NODE_TYPES}
        onNodeClick=${onNodeClick}
        fitView fitViewOptions=${{ padding: 0.15 }}
        minZoom=${0.1} maxZoom=${2}
        proOptions=${{ hideAttribution: true }}
      >
        <${MiniMap} nodeColor=${n => n.data?.color || '#475569'} style=${{ background: '#1e293b' }} />
        <${Controls} />
        <${Background} color="#1e293b" gap=${20} />
      </${ReactFlow}>
    </div>
  `;
}

// ============================================================
// VIEW 2: DATA FLOW PIPELINE
// ============================================================
function DataFlowView() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const raw = ARCH.flow.nodes.map(n => ({ ...n, _w: FLOW_W, _h: FLOW_H }));
    elkLayout(raw, ARCH.flow.edges, 'RIGHT', 'dataFlow').then(result => {
      setNodes(result.nodes);
      setEdges(result.edges);
      setLoading(false);
    });
  }, []);

  if (loading) return html`<div className="loading">Computing pipeline layout...</div>`;

  return html`
    <div style=${{ width: '100%', height: '100%' }}>
      <${ReactFlow}
        nodes=${nodes} edges=${edges}
        onNodesChange=${onNodesChange} onEdgesChange=${onEdgesChange}
        nodeTypes=${FLOW_NODE_TYPES}
        fitView fitViewOptions=${{ padding: 0.2 }}
        minZoom=${0.3} maxZoom=${2}
        proOptions=${{ hideAttribution: true }}
      >
        <${MiniMap} nodeColor=${n => n.data?.color || '#475569'} style=${{ background: '#1e293b' }} />
        <${Controls} />
        <${Background} color="#1e293b" gap=${20} />
      </${ReactFlow}>
    </div>
  `;
}

// ============================================================
// VIEW 3: REPOSITORY INTEGRATION MAP
// ============================================================
function IntegrationView() {
  const [nodes, setNodes, onNodesChange] = useNodesState(ARCH.integration.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(ARCH.integration.edges);

  return html`
    <div style=${{ width: '100%', height: '100%' }}>
      <${ReactFlow}
        nodes=${nodes} edges=${edges}
        onNodesChange=${onNodesChange} onEdgesChange=${onEdgesChange}
        nodeTypes=${INTEGRATION_NODE_TYPES}
        fitView fitViewOptions=${{ padding: 0.3 }}
        minZoom=${0.5} maxZoom=${2}
        proOptions=${{ hideAttribution: true }}
      >
        <${MiniMap} nodeColor=${n => n.data?.color || '#475569'} style=${{ background: '#1e293b' }} />
        <${Controls} />
        <${Background} color="#1e293b" gap=${20} />
      </${ReactFlow}>
    </div>
  `;
}

// ============================================================
// VIEW 4: STORAGE & INFRASTRUCTURE DASHBOARD
// ============================================================
function DashboardView() {
  const d = ARCH.dashboard;
  return html`
    <div className="dash-grid">
      <!-- System Overview -->
      <div className="dash-card" style=${{ gridColumn: 'span 2' }}>
        <h3>System Overview</h3>
        <div style=${{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, textAlign: 'center' }}>
          <div><div className="stat-big">${d.totalEntities}</div><div className="stat-label">Entities</div></div>
          <div><div className="stat-big">${d.totalProperties}</div><div className="stat-label">Properties</div></div>
          <div><div className="stat-big">${d.totalRelationships}</div><div className="stat-label">Relationships</div></div>
          <div><div className="stat-big">${d.multiProjectEntities}</div><div className="stat-label">Cross-Repo</div></div>
        </div>
      </div>

      <!-- Categories -->
      <div className="dash-card">
        <h3>Entity Categories</h3>
        ${Object.entries(d.categories || {}).map(([name, info]) => html`
          <div key=${name} className="cat-bar">
            <span className="cat-dot" style=${{ background: info.color }} />
            <span style=${{ fontSize: 12, flex: 1 }}>${name}</span>
            <span className="mono" style=${{ fontSize: 12, color: '#64748b' }}>${info.count}</span>
          </div>
        `)}
      </div>

      <!-- Storage Infrastructure -->
      <div className="dash-card">
        <h3>Storage Infrastructure</h3>
        <div className="stat-row"><span className="stat-label">Qdrant Collections</span><span className="stat-value" style=${{ color: '#06b6d4' }}>${d.qdrantCollections}</span></div>
        <div className="stat-row"><span className="stat-label">SQLite Databases</span><span className="stat-value" style=${{ color: '#06b6d4' }}>${d.sqliteDatabases}</span></div>
        <div className="stat-row"><span className="stat-label">Neo4j Node Types</span><span className="stat-value" style=${{ color: '#10b981' }}>${d.neo4jNodeTypes}</span></div>
        <div className="stat-row"><span className="stat-label">Neo4j Rel Types</span><span className="stat-value" style=${{ color: '#10b981' }}>${d.neo4jRelTypes}</span></div>
        <div className="stat-row"><span className="stat-label">API Endpoints</span><span className="stat-value" style=${{ color: '#f43f5e' }}>${d.apiEndpoints}</span></div>
      </div>

      <!-- Pipeline -->
      <div className="dash-card">
        <h3>Pipeline</h3>
        <div className="stat-row"><span className="stat-label">BD Engines</span><span className="stat-value" style=${{ color: '#8b5cf6' }}>${d.engines || 8}</span></div>
        <div className="stat-row"><span className="stat-label">Data Flows</span><span className="stat-value" style=${{ color: '#8b5cf6' }}>${d.dataFlows}</span></div>
        <div className="stat-row"><span className="stat-label">N8N Workflows</span><span className="stat-value" style=${{ color: '#f97316' }}>${d.n8nWorkflows || 40}</span></div>
      </div>

      <!-- Repository Contributions -->
      <div className="dash-card" style=${{ gridColumn: 'span 2' }}>
        <h3>Repository Contributions</h3>
        <div style=${{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, textAlign: 'center' }}>
          <div style=${{ borderRight: '1px solid #334155' }}>
            <div style=${{ fontSize: 13, color: '#3b82f6', fontWeight: 600 }}>BD-Automation-Engine</div>
            <div style=${{ fontSize: 11, color: '#64748b', marginTop: 4 }}>40 entities | 506 props | 65 rels</div>
            <div style=${{ fontSize: 11, color: '#64748b' }}>8 engines | 340 APIs | 9 Qdrant</div>
          </div>
          <div style=${{ borderRight: '1px solid #334155' }}>
            <div style=${{ fontSize: 13, color: '#10b981', fontWeight: 600 }}>Data-Scraper</div>
            <div style=${{ fontSize: 11, color: '#64748b', marginTop: 4 }}>23 entities | 410 props | 30 rels</div>
            <div style=${{ fontSize: 11, color: '#64748b' }}>33 domains | 250 APIs | 2 Qdrant</div>
          </div>
          <div>
            <div style=${{ fontSize: 13, color: '#f97316', fontWeight: 600 }}>N8N-Builder</div>
            <div style=${{ fontSize: 11, color: '#64748b', marginTop: 4 }}>32 entities | 419 props | 22 rels</div>
            <div style=${{ fontSize: 11, color: '#64748b' }}>40 workflows | 267 APIs | 3 Qdrant</div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// ============================================================
// DETAIL PANEL
// ============================================================
function DetailPanel({ data, onClose }) {
  if (!data) return null;
  return html`
    <div className="detail-panel">
      <div style=${{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <h3 style=${{ color: data.color, fontSize: 16, fontWeight: 600 }}>${data.label}</h3>
        <button onClick=${onClose} style=${{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: 18, padding: '4px 8px' }}>✕</button>
      </div>

      <div style=${{ display: 'flex', gap: 4, marginBottom: 8, flexWrap: 'wrap' }}>
        ${(data.projects || []).map(p => html`
          <span key=${p} className="badge" style=${{ background: PROJECT_COLORS[p] || '#64748b' }}>${PROJECT_LABELS[p] || p}</span>
        `)}
      </div>

      ${data.description && html`<p style=${{ color: '#94a3b8', fontSize: 12, marginBottom: 8, lineHeight: 1.4 }}>${data.description}</p>`}

      <div className="mono" style=${{ color: '#64748b', fontSize: 11, marginBottom: 12 }}>
        PK: <span style=${{ color: '#38bdf8' }}>${data.pk}</span>${' | '}
        Records: <span style=${{ color: '#38bdf8' }}>${data.records}</span>${' | '}
        Props: <span style=${{ color: '#38bdf8' }}>${data.propCount}</span>
      </div>

      ${(data.sources || []).length > 0 && html`
        <div style=${{ marginBottom: 12 }}>
          <span style=${{ fontSize: 11, color: '#64748b' }}>Sources: </span>
          ${data.sources.map(s => html`<span key=${s} className="badge" style=${{ background: '#334155', color: '#94a3b8', fontSize: 9 }}>${s}</span>`)}
        </div>
      `}

      <h4 style=${{ color: '#94a3b8', fontSize: 12, marginBottom: 4 }}>Properties (${(data.properties || []).length})</h4>
      <div style=${{ maxHeight: 'calc(100vh - 300px)', overflowY: 'auto' }}>
        ${(data.properties || []).length === 0
          ? html`<div style=${{ fontSize: 12, color: '#475569' }}>No properties</div>`
          : (data.properties || []).map(p => html`
              <div key=${p.name} className="prop-row">
                <span className="prop-name">${p.name}</span>
                <span className="prop-type">${p.type}</span>
              </div>
            `)
        }
      </div>
    </div>
  `;
}

// ============================================================
// APP
// ============================================================
function App() {
  const [activeTab, setActiveTab] = useState('graph');
  const [selectedNode, setSelectedNode] = useState(null);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = e => {
      if (e.target.tagName === 'INPUT') return;
      switch(e.key) {
        case '1': setActiveTab('graph'); break;
        case '2': setActiveTab('flow'); break;
        case '3': setActiveTab('integration'); break;
        case '4': setActiveTab('dashboard'); break;
        case 'Escape': setSelectedNode(null); break;
        case '/': e.preventDefault(); document.querySelector('.search-input')?.focus(); break;
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const tabs = [
    { id: 'graph', label: 'Entity Graph', icon: '\u{1F310}' },
    { id: 'flow', label: 'Data Flow', icon: '\u27A1' },
    { id: 'integration', label: 'Integration Map', icon: '\u{1F517}' },
    { id: 'dashboard', label: 'Dashboard', icon: '\u{1F4CA}' },
  ];

  const d = ARCH.dashboard;

  return html`
    <div style=${{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column', background: '#0f172a', color: '#e2e8f0', fontFamily: "'DM Sans', sans-serif" }}>
      <!-- Header -->
      <div style=${{ background: '#1e293b', borderBottom: '1px solid #334155', padding: '8px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
        <h1 style=${{ fontSize: 15, fontWeight: 700, color: '#f1f5f9' }}>PTS Data Architecture Explorer V5</h1>
        <div className="mono" style=${{ display: 'flex', gap: 16, fontSize: 12, color: '#64748b' }}>
          Entities: <span style=${{ color: '#38bdf8' }}>${d.totalEntities}</span>${' | '}
          Properties: <span style=${{ color: '#38bdf8' }}>${d.totalProperties}</span>${' | '}
          Relationships: <span style=${{ color: '#38bdf8' }}>${d.totalRelationships}</span>${' | '}
          Multi-project: <span style=${{ color: '#38bdf8' }}>${d.multiProjectEntities}</span>
        </div>
      </div>

      <!-- Tab bar -->
      <div style=${{ display: 'flex', background: '#1e293b', borderBottom: '1px solid #334155', padding: '0 16px', flexShrink: 0 }}>
        ${tabs.map(t => html`
          <button key=${t.id} onClick=${() => { setActiveTab(t.id); setSelectedNode(null); }}
            style=${{
              padding: '12px 20px', cursor: 'pointer', fontSize: 13, fontWeight: 500,
              color: activeTab === t.id ? '#38bdf8' : '#94a3b8',
              borderBottom: activeTab === t.id ? '2px solid #38bdf8' : '2px solid transparent',
              background: 'none', border: 'none', borderBottomStyle: 'solid',
            }}>
            ${t.icon} ${t.label}
          </button>
        `)}
        <div style=${{ marginLeft: 'auto', display: 'flex', alignItems: 'center', fontSize: 11, color: '#475569' }}>
          Keys: 1-4 switch tabs | / search | Esc close
        </div>
      </div>

      <!-- Content -->
      <div style=${{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <div style=${{ flex: 1, overflow: 'hidden' }}>
          ${activeTab === 'graph' && html`<${ReactFlowProvider}><${EntityGraphView} onSelectNode=${setSelectedNode} /></${ReactFlowProvider}>`}
          ${activeTab === 'flow' && html`<${ReactFlowProvider}><${DataFlowView} /></${ReactFlowProvider}>`}
          ${activeTab === 'integration' && html`<${ReactFlowProvider}><${IntegrationView} /></${ReactFlowProvider}>`}
          ${activeTab === 'dashboard' && html`<${DashboardView} />`}
        </div>
        ${selectedNode && activeTab === 'graph' && html`<${DetailPanel} data=${selectedNode} onClose=${() => setSelectedNode(null)} />`}
      </div>
    </div>
  `;
}

// ============================================================
// MOUNT
// ============================================================
const root = createRoot(document.getElementById('root'));
root.render(html`<${App} />`);
</script>
</body>
</html>'''
