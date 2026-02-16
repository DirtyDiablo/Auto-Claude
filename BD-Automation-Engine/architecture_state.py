#!/usr/bin/env python3
"""
BD-Automation-Engine — Master Architecture State Report

Run:  python architecture_state.py
      python architecture_state.py --json       (raw JSON dump)
      python architecture_state.py --section engines
      python architecture_state.py --live       (include live service checks)

Reads data_architecture_bd_engine.json + scans the live filesystem/services
to produce a single-screen master view of the entire project.
"""

import sys
import os
import json
import argparse
import textwrap
from pathlib import Path
from datetime import datetime
from collections import Counter

# ---------------------------------------------------------------------------
# Windows encoding fix
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
ARCH_FILE = PROJECT_ROOT / "data_architecture_bd_engine.json"

# Box-drawing characters
H, V, TL, TR, BL, BR, LT, RT, TT, BT, CROSS = (
    "\u2500",
    "\u2502",
    "\u250c",
    "\u2510",
    "\u2514",
    "\u2518",
    "\u251c",
    "\u2524",
    "\u252c",
    "\u2534",
    "\u253c",
)

# ---------------------------------------------------------------------------
# Color helpers (ANSI — works in Windows Terminal / modern consoles)
# ---------------------------------------------------------------------------
NO_COLOR = os.environ.get("NO_COLOR")


def _c(code, text):
    if NO_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(t):
    return _c("1", t)


def dim(t):
    return _c("2", t)


def green(t):
    return _c("32", t)


def red(t):
    return _c("31", t)


def yellow(t):
    return _c("33", t)


def cyan(t):
    return _c("36", t)


def magenta(t):
    return _c("35", t)


def blue(t):
    return _c("34", t)


def white(t):
    return _c("97", t)


STATUS_ICONS = {
    "complete": green("[OK]"),
    "configured": cyan("[CFG]"),
    "in_progress": yellow("[WIP]"),
    "planned": dim("[--]"),
    "error": red("[ERR]"),
}


# ---------------------------------------------------------------------------
# Load architecture JSON
# ---------------------------------------------------------------------------
def load_arch() -> dict:
    if not ARCH_FILE.exists():
        print(red(f"ERROR: {ARCH_FILE} not found."))
        print("Run the data architecture extraction first.")
        sys.exit(1)
    with open(ARCH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Live service probes
# ---------------------------------------------------------------------------
def probe_service(url: str, timeout: float = 3.0) -> tuple:
    """Returns (ok: bool, body: str). Full body for JSON parsing."""
    try:
        import urllib.request

        resp = urllib.request.urlopen(url, timeout=timeout)
        data = resp.read().decode("utf-8", errors="replace")
        return True, data
    except Exception as e:
        return False, str(e)[:120]


def probe_qdrant() -> dict:
    try:
        ok, body = probe_service("http://localhost:6333/collections")
        if not ok:
            return {"online": False, "error": body}
        data = json.loads(body)
        collections = data.get("result", {}).get("collections", [])
        result = {"online": True, "collections": {}}
        for c in collections:
            name = c["name"]
            try:
                ok2, body2 = probe_service(f"http://localhost:6333/collections/{name}")
                if ok2:
                    info = json.loads(body2)
                    result["collections"][name] = info["result"]["points_count"]
            except Exception:
                result["collections"][name] = -1
        return result
    except Exception as e:
        return {"online": False, "error": str(e)[:120]}


def probe_api() -> dict:
    ok, body = probe_service("http://localhost:8100/health")
    if not ok:
        return {"online": False, "error": body}
    try:
        return {"online": True, "health": json.loads(body)}
    except Exception:
        return {"online": True, "health": body[:200]}


def probe_dashboard() -> dict:
    ok, body = probe_service("http://localhost:5173")
    return {"online": ok}


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------
def section(title: str):
    w = 78
    print()
    print(f"  {bold(cyan(f'{H * 3} {title} {H * (w - len(title) - 5)}'))}")


def kv(label: str, value, indent: int = 4):
    pad = " " * indent
    print(f"{pad}{dim(label + ':'):<30} {value}")


def render_header(arch: dict):
    pi = arch.get("project_info", {})
    ss = arch.get("scan_stats", {})
    w = 78
    print()
    print(f"  {bold(white(f'{TL}{H * (w - 2)}{TR}'))}")
    print(
        f"  {bold(white(V))}  {bold(magenta('BD-AUTOMATION-ENGINE   MASTER ARCHITECTURE STATE')):<{w + 7}}{bold(white(V))}"
    )
    print(
        f"  {bold(white(V))}  {dim(pi.get('description', '')[: w - 6]):<{w - 2}}{bold(white(V))}"
    )
    print(f"  {bold(white(f'{BL}{H * (w - 2)}{BR}'))}")
    print()
    kv("Scan date", arch.get("scan_date", "?"))
    kv("Scan version", arch.get("scan_version", "?"))
    kv("Files scanned", f"{ss.get('files_scanned', 0):,}")
    ft = pi.get("file_types_found", {})
    if ft:
        parts = [f"{k}: {v:,}" for k, v in ft.items()]
        kv("File types", " | ".join(parts))
    kv("Report generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def render_scan_stats(arch: dict):
    section("SCAN STATISTICS")
    ss = arch.get("scan_stats", {})
    cols = [
        ("Entities", "entities_found"),
        ("Properties", "properties_found"),
        ("Relationships", "relationships_found"),
        ("Data flows", "data_flows_found"),
    ]
    for label, key in cols:
        kv(label, f"{ss.get(key, 0):,}")
    print()
    cols2 = [
        ("Qdrant collections", "qdrant_collections_documented"),
        ("SQLite databases", "sqlite_databases_documented"),
        ("SQLite tables", "sqlite_tables_documented"),
        ("Neo4j node types", "neo4j_node_types"),
        ("Neo4j rel types", "neo4j_relationship_types"),
        ("Notion databases", "notion_databases_documented"),
        ("Dashboard feeds", "dashboard_feeds_documented"),
        ("API endpoints", "api_endpoints_documented"),
        ("API models", "api_models_documented"),
        ("Engines", "engines_documented"),
        ("AI agents", "ai_agents_documented"),
        ("AI crews", "ai_crews_documented"),
        ("MCP tools", "mcp_tools_documented"),
        ("Dify tools", "dify_tools_documented"),
    ]
    for label, key in cols2:
        v = ss.get(key, 0)
        if v:
            kv(label, f"{v:,}")


def render_engines(arch: dict):
    section("8-ENGINE PIPELINE")
    engines = arch.get("engines", [])
    if not engines:
        print("    (no engine data)")
        return
    print(f"    {'#':<4} {'Engine':<35} {'Status':<8} {'Input':<18} {'Output'}")
    print(f"    {H * 4} {H * 35} {H * 8} {H * 18} {H * 25}")
    for i, e in enumerate(engines, 1):
        name = e.get("name", "?")[:35]
        status = e.get("status", "?")
        icon = STATUS_ICONS.get(status, dim(f"[{status}]"))
        inp = e.get("input_format", e.get("input", ""))
        if isinstance(inp, list):
            inp = ", ".join(str(x) for x in inp[:2])
        inp = str(inp)[:18]
        out = e.get("output_format", e.get("output", ""))
        if isinstance(out, list):
            out = ", ".join(str(x) for x in out[:2])
        out = str(out)[:25]
        print(f"    {i:<4} {name:<35} {icon:<16} {dim(inp):<26} {dim(out)}")


def render_entities(arch: dict):
    section("DATA ENTITIES (40)")
    entities = arch.get("entities", [])
    if not entities:
        print("    (no entity data)")
        return
    # Group by category
    by_cat = {}
    for e in entities:
        cat = e.get("category", "Other")
        by_cat.setdefault(cat, []).append(e)
    for cat in sorted(by_cat.keys()):
        items = by_cat[cat]
        print(f"\n    {bold(cat)} ({len(items)})")
        for e in sorted(items, key=lambda x: x["name"]):
            name = e["name"]
            records = e.get("records", "?")
            props = len(e.get("properties", []))
            storage = e.get("storage", [])
            storage_str = ", ".join(str(s)[:20] for s in storage[:3]) if storage else ""
            print(
                f"      {cyan(name):<30} {dim(f'{records:>8} records')}  {dim(f'{props:>3} props')}  {dim(storage_str)}"
            )


def render_databases(arch: dict):
    dbs = arch.get("databases", {})

    # Qdrant
    section("QDRANT VECTOR COLLECTIONS")
    qc = dbs.get("qdrant_collections", [])
    if qc:
        print(
            f"    {'Collection':<25} {'Vectors':<12} {'Dim':<6} {'Distance':<10} {'Hybrid'}"
        )
        print(f"    {H * 25} {H * 12} {H * 6} {H * 10} {H * 8}")
        total_v = 0
        for c in qc:
            name = c.get("name", "?")
            count = c.get("points_count", c.get("record_count", 0))
            total_v += count if isinstance(count, int) else 0
            dim_val = c.get("vector_size", c.get("dimension", "?"))
            dist = c.get("distance", "?")
            hybrid = (
                green("Yes")
                if c.get("hybrid_enabled") or c.get("bm25_index")
                else dim("No")
            )
            print(
                f"    {name:<25} {str(count):>10}   {str(dim_val):<6} {str(dist):<10} {hybrid}"
            )
        print(f"    {H * 25} {H * 12}")
        print(f"    {'TOTAL':<25} {bold(f'{total_v:>10,}')}")
    else:
        print("    (no Qdrant data)")

    # Neo4j
    section("NEO4J KNOWLEDGE GRAPH")
    neo = dbs.get("neo4j_graph", {})
    node_types = neo.get("node_types", [])
    rel_types = neo.get("relationship_types", [])
    if node_types:
        names = [
            n.get("type", n.get("label", str(n))) if isinstance(n, dict) else str(n)
            for n in node_types
        ]
        kv("Node types", f"{len(names)} — {', '.join(names)}")
    if rel_types:
        names = [
            r.get("type", str(r)) if isinstance(r, dict) else str(r) for r in rel_types
        ]
        kv(
            "Rel types",
            f"{len(names)} — {', '.join(names[:12])}{'...' if len(names) > 12 else ''}",
        )

    # SQLite
    section("SQLITE DATABASES")
    sq = dbs.get("sqlite_databases", [])
    if sq:
        for db in sq:
            name = db.get("name", db.get("file", "?"))
            size = db.get("size", db.get("size_mb", "?"))
            tables = db.get("tables", [])
            row_count = db.get("total_rows", db.get("row_count", 0))
            table_names = []
            for t in tables:
                if isinstance(t, dict):
                    table_names.append(t.get("name", t.get("table", "?")))
                    rows = t.get("row_count", t.get("rows", 0))
                    if isinstance(rows, (int, float)):
                        row_count += int(rows)
                else:
                    table_names.append(str(t))
            size_str = f"{size}" if size != "?" else ""
            row_str = f"{row_count:,} rows" if row_count else ""
            print(
                f"    {bold(name)} {dim(size_str)}  {dim(row_str)}  {dim(f'{len(tables)} tables')}"
            )
            if table_names:
                line = ", ".join(table_names)
                for chunk in textwrap.wrap(line, width=68):
                    print(f"      {dim(chunk)}")
    else:
        print("    (no SQLite data)")

    # Notion
    notion = dbs.get("notion_databases", [])
    if notion:
        section("NOTION DATABASES")
        for n in notion:
            name = n.get("name", "?")
            nid = n.get("id", "?")[:12]
            print(f"    {name:<40} {dim(nid)}")

    # CSV sources
    csv_src = dbs.get("csv_sources", [])
    if csv_src:
        section("CSV DATA SOURCES")
        for c in csv_src:
            if isinstance(c, dict):
                path = c.get("path", c.get("name", c.get("file", "?")))
                cols = c.get("columns", [])
                col_count = len(cols) if isinstance(cols, list) else 0
                short_path = path.split("/")[-1] if "/" in path else path
                print(f"    {short_path:<45} {dim(f'{col_count} columns')}")
            else:
                print(f"    {dim(str(c))}")


def render_api(arch: dict):
    section("API ENDPOINTS")
    api = arch.get("databases", {}).get("api_endpoints", {})
    if not api:
        print("    (no API data)")
        return
    total = api.get("total_estimated", "?")
    kv("Total endpoints", f"~{total}")

    # Core API
    core = api.get("core_api", {})
    if isinstance(core, dict):
        f_name = core.get("file", "")
        prefix = core.get("prefix", "/")
        ep_count = core.get("endpoints", 0)
        if isinstance(ep_count, int):
            kv("Core API", f"{ep_count} endpoints at {prefix} ({f_name})")
        elif isinstance(ep_count, (list, dict)):
            kv("Core API", f"{len(ep_count)} endpoints at {prefix}")

    # V2 API
    v2 = api.get("unified_v2", {})
    if isinstance(v2, dict):
        f_name = v2.get("file", "")
        prefix = v2.get("prefix", "/api/v2")
        ep_count = v2.get("endpoints", 0)
        if isinstance(ep_count, int):
            kv("Unified V2 API", f"{ep_count} endpoints at {prefix} ({f_name})")
        elif isinstance(ep_count, (list, dict)):
            kv("Unified V2 API", f"{len(ep_count)} endpoints at {prefix}")

    # Sub-routers
    subs = api.get("engine8_sub_routers", [])
    if subs:
        total_ep = sum(r.get("endpoints", 0) for r in subs if isinstance(r, dict))
        print(
            f"\n    {bold(f'Engine8 sub-routers: {len(subs)} files, ~{total_ep} endpoints')}"
        )
        print(f"    {'Router file':<42} {'Endpoints':>9}")
        print(f"    {H * 42} {H * 9}")
        for r in sorted(
            subs,
            key=lambda x: x.get("endpoints", 0) if isinstance(x, dict) else 0,
            reverse=True,
        ):
            if isinstance(r, dict):
                fname = r.get("file", "?")
                count = r.get("endpoints", 0)
                print(f"    {dim(fname):<42} {count:>9}")

    # Src routers
    src_routers = api.get("src_api_routers", [])
    if src_routers:
        total_ep2 = sum(
            r.get("endpoints", 0) for r in src_routers if isinstance(r, dict)
        )
        print(
            f"\n    {bold(f'src/ API routers: {len(src_routers)} files, ~{total_ep2} endpoints')}"
        )


def render_relationships(arch: dict):
    section("ENTITY RELATIONSHIPS (65)")
    rels = arch.get("relationships", [])
    if not rels:
        print("    (no relationship data)")
        return
    # Group by type
    by_type = Counter()
    for r in rels:
        by_type[r.get("type", r.get("label", "?"))] += 1
    # Show relationships
    print(f"    {'Relationship':<25} {'Count':<6} {'Example':<35} {'Card.'}")
    print(f"    {H * 25} {H * 6} {H * 35} {H * 12}")
    for rtype, count in by_type.most_common(25):
        example = ""
        card = ""
        for r in rels:
            if r.get("type", r.get("label")) == rtype:
                src = r.get("source", r.get("from", ""))
                tgt = r.get("target", r.get("to", ""))
                example = f"{src} -> {tgt}"
                card = r.get("cardinality", "")
                break
        print(f"    {cyan(rtype):<33} {count:<6} {dim(example[:35]):<43} {dim(card)}")
    if len(by_type) > 25:
        print(f"    {dim(f'... and {len(by_type) - 25} more')}")


def render_data_flows(arch: dict):
    section("DATA FLOWS (18)")
    flows = arch.get("data_flows", [])
    if not flows:
        print("    (no data flow data)")
        return
    for f in flows:
        src = f.get("from", f.get("source", "?"))
        dst = f.get("to", f.get("target", "?"))
        fmt = f.get("format", f.get("type", ""))
        desc = f.get("description", f.get("note", ""))[:50]
        print(f"    {src:<22} {dim('->')} {dst:<22} {dim(fmt):<10} {dim(desc)}")


def render_ai_agents(arch: dict):
    section("AI AGENTS & CREWS")
    # Check for agents in entities or a dedicated key
    # They might be in engines[7] (Engine 8) or a top-level key
    engines = arch.get("engines", [])
    for e in engines:
        agents = e.get("agents", e.get("ai_agents", []))
        if agents and isinstance(agents, list) and len(agents) > 2:
            print(f"\n    {bold(e.get('name', '?'))} agents:")
            for a in agents:
                if isinstance(a, dict):
                    name = a.get("name", "?")
                    desc = a.get("description", "")[:50]
                    print(f"      {cyan(name):<30} {dim(desc)}")
                else:
                    print(f"      {cyan(str(a))}")

    # Dify tools
    dify = arch.get("dify_tools", [])
    if dify:
        print(f"\n    {bold('Dify Tools:')} {len(dify)}")
        by_cat = {}
        for t in dify:
            cat = t.get("category", "Other") if isinstance(t, dict) else "Other"
            name = t.get("name", str(t)) if isinstance(t, dict) else str(t)
            by_cat.setdefault(cat, []).append(name)
        for cat in sorted(by_cat.keys()):
            names = by_cat[cat]
            print(f"      {cat}: {', '.join(names)}")


def render_live_services(include_live: bool):
    if not include_live:
        return

    section("LIVE SERVICE STATUS")

    # Qdrant
    qdrant = probe_qdrant()
    if qdrant["online"]:
        total = sum(qdrant["collections"].values())
        print(
            f"    Qdrant (6333)      {green('[RUNNING]')}  {total:,} vectors across {len(qdrant['collections'])} collections"
        )
        for name, count in sorted(qdrant["collections"].items()):
            print(f"      {name:<25} {count:>10,}")
    else:
        print(
            f"    Qdrant (6333)      {red('[OFFLINE]')}  {dim(qdrant.get('error', ''))}"
        )

    # API
    api = probe_api()
    if api["online"]:
        print(f"    Knowledge API (8100) {green('[RUNNING]')}")
    else:
        print(
            f"    Knowledge API (8100) {red('[OFFLINE]')}  {dim(api.get('error', ''))}"
        )

    # Dashboard
    dash = probe_dashboard()
    if dash["online"]:
        print(f"    Dashboard (5173)   {green('[RUNNING]')}")
    else:
        print(f"    Dashboard (5173)   {red('[OFFLINE]')}")


def render_filesystem_snapshot():
    section("FILESYSTEM SNAPSHOT")
    # Count files by engine directory
    engine_dirs = [
        "Engine1_Scraper",
        "Engine2_ProgramMapping",
        "Engine3_OrgChart",
        "Engine4_Playbook",
        "Engine5_Scoring",
        "Engine6_QA",
        "Engine7_BullhornETL",
        "Engine8_Knowledge",
    ]
    for d in engine_dirs:
        dp = PROJECT_ROOT / d
        if dp.exists():
            py_count = len(list(dp.rglob("*.py")))
            all_count = sum(1 for _ in dp.rglob("*") if _.is_file())
            print(f"    {d:<30} {py_count:>5} .py   {all_count:>6} total")
        else:
            print(f"    {d:<30} {dim('(not found)')}")

    # Dashboard
    dash = PROJECT_ROOT / "dashboard" / "src"
    if dash.exists():
        tsx = len(list(dash.rglob("*.tsx")))
        ts = len(list(dash.rglob("*.ts")))
        print(f"    {'dashboard/src':<30} {tsx:>5} .tsx  {ts:>5} .ts")

    # Key data files
    print()
    key_files = [
        ("bullhorn_master.db", "Engine7_BullhornETL/data/bullhorn_master.db"),
        ("data_architecture.json", "data_architecture_bd_engine.json"),
        (".env", ".env"),
        (".mcp.json", ".mcp.json"),
    ]
    for label, rel in key_files:
        fp = PROJECT_ROOT / rel
        if fp.exists():
            size_mb = fp.stat().st_size / (1024 * 1024)
            mod = datetime.fromtimestamp(fp.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"    {label:<30} {size_mb:>8.1f} MB   {dim(mod)}")
        else:
            print(f"    {label:<30} {dim('(missing)')}")


def render_git_status():
    section("GIT STATUS")
    try:
        import subprocess

        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        branch = result.stdout.strip()
        kv("Branch", bold(branch))

        result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        if result.stdout.strip():
            print(f"\n    {bold('Recent commits:')}")
            for line in result.stdout.strip().split("\n"):
                print(f"      {dim(line)}")

        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        changes = [l for l in result.stdout.strip().split("\n") if l.strip()]
        staged = sum(1 for l in changes if l[0] in "MADR")
        modified = sum(1 for l in changes if l[0] == " " and l[1] == "M")
        untracked = sum(1 for l in changes if l.startswith("??"))
        print()
        kv("Staged", str(staged))
        kv("Modified", str(modified))
        kv("Untracked", str(untracked))
    except Exception as e:
        print(f"    {dim(f'Git not available: {e}')}")


def render_stack_upgrades(arch: dict = None):
    section("STACK UPGRADE STATUS")
    upgrades = [
        (
            "LightRAG Neo4j backend",
            "Engine8_Knowledge/bd_lightrag/graph_rag.py",
            "2.1a",
        ),
        ("Datasette SQL explorer", "Engine8_Knowledge/datasette_config.py", "2.1b"),
        (
            "tree-sitter parser",
            "Engine8_Knowledge/scripts/treesitter_parser.py",
            "2.1c",
        ),
        (
            "Docling doc extractor",
            "Engine8_Knowledge/scripts/docling_extractor.py",
            "2.1d",
        ),
        ("LanceDB hybrid search", "Engine8_Knowledge/scripts/lancedb_hybrid.py", "2.2"),
        ("Neo4j file lineage", "Engine8_Knowledge/graph/lineage.py", "2.3"),
        (
            "Classification pipeline",
            "Engine8_Knowledge/scripts/classifier_pipeline.py",
            "2.4",
        ),
        ("FastMCP Python server", "mcp/knowledge-mcp-server/server.py", "2.5"),
        ("GraphViewer component", "dashboard/src/components/GraphViewer.tsx", "2.6"),
    ]
    for label, path, step in upgrades:
        fp = PROJECT_ROOT / path
        if fp.exists():
            size_kb = fp.stat().st_size / 1024
            print(
                f"    {green('[DONE]')}  Step {step}  {label:<30}  {dim(f'{size_kb:.0f} KB')}"
            )
        else:
            print(f"    {red('[MISS]')}  Step {step}  {label:<30}  {dim(path)}")


def render_quick_commands():
    section("QUICK COMMANDS")
    cmds = [
        ("Start API server", "python Engine8_Knowledge/api.py"),
        ("Start dashboard", "cd dashboard && npm run dev"),
        ("Run status check", "python status_check.py"),
        ("Architecture state", "python architecture_state.py --live"),
        (
            "Search knowledge",
            'python Engine8_Knowledge/scripts/vector_store.py --search "DCGS" --collection contacts',
        ),
        (
            "Validate arch JSON",
            "python -m json.tool data_architecture_bd_engine.json > NUL",
        ),
    ]
    for label, cmd in cmds:
        print(f"    {label:<25} {dim(cmd)}")


# ---------------------------------------------------------------------------
# Section-only mode
# ---------------------------------------------------------------------------
SECTION_MAP = {
    "header": render_header,
    "stats": render_scan_stats,
    "engines": render_engines,
    "entities": render_entities,
    "databases": render_databases,
    "api": render_api,
    "relationships": render_relationships,
    "flows": render_data_flows,
    "agents": render_ai_agents,
    "filesystem": render_filesystem_snapshot,
    "git": render_git_status,
    "upgrades": render_stack_upgrades,
    "commands": render_quick_commands,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="BD-Automation-Engine Master Architecture State"
    )
    parser.add_argument(
        "--json", action="store_true", help="Dump raw architecture JSON"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Include live service probes (Qdrant, API, dashboard)",
    )
    parser.add_argument(
        "--section",
        type=str,
        help=f"Show only one section: {', '.join(SECTION_MAP.keys())}",
    )
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    args = parser.parse_args()

    if args.no_color:
        global NO_COLOR
        NO_COLOR = True

    arch = load_arch()

    if args.json:
        print(json.dumps(arch, indent=2))
        return

    if args.section:
        if args.section not in SECTION_MAP:
            print(f"Unknown section: {args.section}")
            print(f"Available: {', '.join(SECTION_MAP.keys())}")
            sys.exit(1)
        SECTION_MAP[args.section](arch)
        if args.section == "databases" and args.live:
            render_live_services(True)
        print()
        return

    # Full report
    render_header(arch)
    render_scan_stats(arch)
    render_engines(arch)
    render_databases(arch)
    render_api(arch)
    render_entities(arch)
    render_relationships(arch)
    render_data_flows(arch)
    render_ai_agents(arch)
    render_stack_upgrades(arch)
    render_filesystem_snapshot()
    render_git_status()
    render_live_services(args.live)
    render_quick_commands()

    print(
        f"\n  {dim(f'Source: {ARCH_FILE.name} ({ARCH_FILE.stat().st_size / 1024:.0f} KB)')}"
    )
    print(
        f"  {dim(f'Run with --live for service health checks, --section <name> for one section')}"
    )
    print()


if __name__ == "__main__":
    main()
