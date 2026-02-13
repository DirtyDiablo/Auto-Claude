"""
Phase 27A — D3.js Renderers

3 rendering modes: hierarchical tree, force-directed network, matrix cross-reference.
Each returns standalone HTML with embedded D3.js.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Render Options
# ---------------------------------------------------------------------------

TIER_COLORS = {
    1: "#dc2626",  # red
    2: "#ea580c",  # orange
    3: "#eab308",  # yellow
    4: "#16a34a",  # green
    5: "#2563eb",  # blue
    6: "#6b7280",  # gray
}


@dataclass
class RenderOptions:
    """Configuration for rendering."""
    width: int = 1200
    height: int = 800
    show_photos: bool = False
    show_emails: bool = True
    show_phones: bool = False
    color_by: str = "tier"  # tier, program, priority, location
    highlight_contacts: List[str] = field(default_factory=list)
    filter_program: Optional[str] = None
    filter_tier: Optional[str] = None
    title: str = "Org Chart"


# ---------------------------------------------------------------------------
# Tree Renderer
# ---------------------------------------------------------------------------


class TreeRenderer:
    """Hierarchical tree layout using D3.js."""

    async def render(self, org_chart, options: Optional[RenderOptions] = None) -> str:
        """Returns HTML with embedded D3.js tree layout."""
        opts = options or RenderOptions()

        # Build tree data
        nodes_data = []
        for person in org_chart.nodes:
            color = TIER_COLORS.get(person.tier, "#6b7280")
            nodes_data.append({
                "id": person.name,
                "name": person.name,
                "title": person.title,
                "tier": person.tier,
                "company": person.company,
                "email": person.email if opts.show_emails else "",
                "color": color,
                "parent": person.reports_to or "",
            })

        html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>{opts.title}</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f8fafc; }}
  .node rect {{ fill: #fff; stroke: #e2e8f0; stroke-width: 2; rx: 8; }}
  .node text {{ font-size: 12px; fill: #334155; }}
  .node .name {{ font-weight: bold; font-size: 13px; }}
  .link {{ fill: none; stroke: #94a3b8; stroke-width: 1.5; }}
  .tier-badge {{ font-size: 10px; fill: white; }}
  .tooltip {{ position: absolute; background: #1e293b; color: white; padding: 8px 12px;
              border-radius: 6px; font-size: 12px; pointer-events: none; opacity: 0; }}
  h2 {{ color: #1e293b; margin-bottom: 16px; }}
</style>
</head><body>
<h2>{opts.title}</h2>
<div id="chart"></div>
<div class="tooltip" id="tooltip"></div>
<script>
const data = {json.dumps(nodes_data)};
const width = {opts.width}, height = {opts.height};

// Build hierarchy
const root_nodes = data.filter(d => !d.parent);
const stratify = d3.stratify().id(d => d.id).parentId(d => d.parent || null);

let hierarchy;
try {{
  if (root_nodes.length === 0 && data.length > 0) {{
    data[0].parent = "";
  }}
  hierarchy = stratify(data.map(d => ({{...d, parent: d.parent || null}})));
}} catch(e) {{
  // Fallback: just display nodes
  const svg = d3.select("#chart").append("svg").attr("width", width).attr("height", height);
  data.forEach((d, i) => {{
    const g = svg.append("g").attr("transform", `translate(${{100 + (i % 4) * 280}}, ${{60 + Math.floor(i / 4) * 100}})`);
    g.append("rect").attr("width", 240).attr("height", 60).attr("rx", 8).style("fill", "#fff").style("stroke", d.color);
    g.append("text").attr("x", 12).attr("y", 24).attr("class", "name").text(d.name);
    g.append("text").attr("x", 12).attr("y", 44).text(d.title);
  }});
  throw e;
}}

const treeLayout = d3.tree().size([width - 100, height - 100]);
treeLayout(hierarchy);

const svg = d3.select("#chart").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", "translate(50, 50)");

// Links
g.selectAll(".link").data(hierarchy.links()).enter().append("path")
  .attr("class", "link")
  .attr("d", d3.linkVertical().x(d => d.x).y(d => d.y));

// Nodes
const node = g.selectAll(".node").data(hierarchy.descendants()).enter().append("g")
  .attr("class", "node")
  .attr("transform", d => `translate(${{d.x - 100}}, ${{d.y - 25}})`);

node.append("rect").attr("width", 200).attr("height", 50)
  .style("stroke", d => d.data.color);
node.append("circle").attr("cx", 14).attr("cy", 14).attr("r", 8)
  .style("fill", d => d.data.color);
node.append("text").attr("class", "tier-badge")
  .attr("x", 14).attr("y", 18).attr("text-anchor", "middle")
  .text(d => "T" + d.data.tier);
node.append("text").attr("class", "name")
  .attr("x", 30).attr("y", 20).text(d => d.data.name);
node.append("text").attr("x", 30).attr("y", 38)
  .text(d => d.data.title);
</script></body></html>"""

        return html


# ---------------------------------------------------------------------------
# Network Renderer
# ---------------------------------------------------------------------------


class NetworkRenderer:
    """Force-directed network layout."""

    async def render(self, org_chart, options: Optional[RenderOptions] = None) -> str:
        opts = options or RenderOptions()

        nodes_data = [
            {
                "id": p.name,
                "name": p.name,
                "title": p.title,
                "tier": p.tier,
                "company": p.company,
                "color": TIER_COLORS.get(p.tier, "#6b7280"),
                "radius": max(8, 20 - p.tier * 2),
            }
            for p in org_chart.nodes
        ]

        edges_data = [
            {"source": e["source"], "target": e["target"], "type": e.get("type", "")}
            for e in org_chart.edges
        ]

        html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>{opts.title} - Network</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f8fafc; }}
  .link {{ stroke: #94a3b8; stroke-width: 1.5; }}
  .node-label {{ font-size: 11px; fill: #334155; pointer-events: none; }}
  h2 {{ color: #1e293b; }}
</style>
</head><body>
<h2>{opts.title} - Network View</h2>
<div id="chart"></div>
<script>
const nodes = {json.dumps(nodes_data)};
const links = {json.dumps(edges_data)};
const width = {opts.width}, height = {opts.height};

const svg = d3.select("#chart").append("svg").attr("width", width).attr("height", height);

const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id).distance(100))
  .force("charge", d3.forceManyBody().strength(-200))
  .force("center", d3.forceCenter(width / 2, height / 2));

const link = svg.selectAll(".link").data(links).enter().append("line").attr("class", "link");
const node = svg.selectAll(".node").data(nodes).enter().append("circle")
  .attr("r", d => d.radius).style("fill", d => d.color).style("cursor", "pointer")
  .call(d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended));
const label = svg.selectAll(".node-label").data(nodes).enter().append("text")
  .attr("class", "node-label").attr("text-anchor", "middle").attr("dy", -12).text(d => d.name);

simulation.on("tick", () => {{
  link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  node.attr("cx", d => d.x).attr("cy", d => d.y);
  label.attr("x", d => d.x).attr("y", d => d.y);
}});

function dragstarted(event, d) {{ simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }}
function dragged(event, d) {{ d.fx = event.x; d.fy = event.y; }}
function dragended(event, d) {{ simulation.alphaTarget(0); d.fx = null; d.fy = null; }}
</script></body></html>"""

        return html


# ---------------------------------------------------------------------------
# Matrix Renderer
# ---------------------------------------------------------------------------


class MatrixRenderer:
    """Cross-reference matrix table."""

    async def render(
        self,
        dimension1: str = "person",
        dimension2: str = "program",
        data: Optional[List[Dict]] = None,
        options: Optional[RenderOptions] = None,
    ) -> str:
        opts = options or RenderOptions()
        items = data or []

        # Extract unique values for each dimension
        dim1_values = sorted(set(item.get(dimension1, "") for item in items if item.get(dimension1)))
        dim2_values = sorted(set(item.get(dimension2, "") for item in items if item.get(dimension2)))

        # Build matrix
        matrix: Dict[str, Dict[str, int]] = {}
        for item in items:
            d1 = item.get(dimension1, "")
            d2 = item.get(dimension2, "")
            if d1 and d2:
                matrix.setdefault(d1, {})
                matrix[d1][d2] = matrix[d1].get(d2, 0) + 1

        # Render as HTML table
        rows_html = ""
        for d1 in dim1_values[:50]:
            cells = ""
            for d2 in dim2_values[:30]:
                val = matrix.get(d1, {}).get(d2, 0)
                bg = f"rgba(37, 99, 235, {min(val / 5, 1) * 0.8})" if val > 0 else "#f8fafc"
                color = "white" if val >= 3 else "#334155"
                cells += f'<td style="background:{bg};color:{color};text-align:center;padding:6px">{val if val else ""}</td>'
            rows_html += f'<tr><td style="font-weight:bold;padding:6px;white-space:nowrap">{d1}</td>{cells}</tr>'

        header_cells = "".join(
            f'<th style="padding:6px;font-size:11px;writing-mode:vertical-rl;text-align:left">{d2}</th>'
            for d2 in dim2_values[:30]
        )

        html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>{opts.title} - Matrix</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f8fafc; }}
  table {{ border-collapse: collapse; font-size: 12px; }}
  th, td {{ border: 1px solid #e2e8f0; }}
  h2 {{ color: #1e293b; }}
</style>
</head><body>
<h2>{opts.title} - {dimension1.title()} x {dimension2.title()} Matrix</h2>
<table>
<thead><tr><th></th>{header_cells}</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</body></html>"""

        return html
