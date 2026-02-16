#!/usr/bin/env python3
"""PTS Data Architecture Consolidation CLI.

Merges architecture data from BD-Automation-Engine, data-scraper, and N8N-Builder
into a unified JSON and React Flow HTML visualization.

Usage:
    python -m scripts.architecture.consolidate
    python -m scripts.architecture.consolidate --json-only
    python -m scripts.architecture.consolidate --html-only
    python -m scripts.architecture.consolidate --discover-rels
"""

import argparse
import sys
from pathlib import Path

# Resolve project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Source architecture JSON paths
BD_PATH = PROJECT_ROOT / "data_architecture_bd_engine.json"
DS_PATH = Path(r"C:\Auto-Claud\data-scraper\data_architecture_data_scraper.json")
N8N_PATH = Path(r"C:\Auto-Claud\N8N-Builder\data_architecture_n8n_builder.json")

# Output paths
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "architecture"


def main():
    parser = argparse.ArgumentParser(
        description="Consolidate 3-project PTS data architecture"
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only generate unified_architecture.json",
    )
    parser.add_argument(
        "--html-only", action="store_true", help="Only generate V4 HTML visualization"
    )
    parser.add_argument(
        "--discover-rels",
        action="store_true",
        help="Auto-discover cross-repo FK relationships",
    )
    parser.add_argument(
        "--v5",
        action="store_true",
        help="Generate V5 React Flow HTML (instead of V4 SVG)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("PTS Data Architecture Consolidation v4.0")
    print("=" * 60)

    # 1. Load architecture JSONs
    from .loaders import load_architecture_json

    print("\n[1/6] Loading architecture JSONs...")

    sources = []
    for label, path in [
        ("BD-Engine", BD_PATH),
        ("Data-Scraper", DS_PATH),
        ("N8N-Builder", N8N_PATH),
    ]:
        if not path.exists():
            print(f"  WARNING: {label} not found at {path}")
            continue
        data = load_architecture_json(path)
        pid = data.get("project_id", label.upper().replace("-", "_"))
        ent_count = len(data.get("entities", []))
        rel_count = len(data.get("relationships", []))
        print(f"  {label}: {ent_count} entities, {rel_count} relationships")
        sources.append((pid, data))

    if not sources:
        print("ERROR: No architecture JSONs found. Aborting.")
        sys.exit(1)

    # 2. Merge entities
    from .entity_merger import build_merged_entities

    print("\n[2/6] Merging entities...")
    entities = build_merged_entities(*sources)
    total_props = sum(len(e.get("properties", [])) for e in entities.values())
    multi_project = sum(1 for e in entities.values() if len(e.get("projects", [])) > 1)
    print(f"  Merged entities: {len(entities)}")
    print(f"  Total properties: {total_props}")
    print(f"  Multi-project entities: {multi_project}")

    # 3. Merge relationships
    from .relationship_merger import build_merged_relationships

    print("\n[3/6] Merging relationships...")
    relationships = build_merged_relationships(
        *sources,
        entities=entities,
        discover=args.discover_rels,
    )
    print(f"  Total relationships: {len(relationships)}")
    if args.discover_rels:
        auto_count = sum(
            1 for r in relationships if "AUTO_DISCOVERED" in r.get("contributed_by", [])
        )
        print(f"  Auto-discovered: {auto_count}")

    # 4. Merge infrastructure
    from .infrastructure_merger import build_infrastructure_section

    print("\n[4/6] Merging infrastructure metadata...")
    infrastructure = build_infrastructure_section(*sources)

    infra_counts = []
    if infrastructure.get("qdrant_collections"):
        infra_counts.append(
            f"Qdrant: {len(infrastructure['qdrant_collections'])} collections"
        )
    if infrastructure.get("sqlite_databases"):
        infra_counts.append(
            f"SQLite: {len(infrastructure['sqlite_databases'])} databases"
        )
    neo4j = infrastructure.get("neo4j_graph", {})
    if neo4j.get("total_node_types"):
        infra_counts.append(f"Neo4j: {neo4j['total_node_types']} node types")
    api = infrastructure.get("api_endpoints", {})
    if api.get("total_endpoints"):
        infra_counts.append(f"API: {api['total_endpoints']} endpoints")
    if infrastructure.get("data_flows"):
        infra_counts.append(f"Flows: {len(infrastructure['data_flows'])}")
    print(f"  {', '.join(infra_counts)}")

    # 5. Emit JSON
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not args.html_only:
        from .json_emitter import generate_unified_json, write_unified_json

        print("\n[5/6] Generating unified_architecture.json...")
        unified = generate_unified_json(
            entities, relationships, infrastructure, sources
        )
        json_path = args.output_dir / "unified_architecture.json"
        write_unified_json(unified, json_path)

    # 6. Emit HTML
    if not args.json_only:
        from .html_emitter import generate_v4_html, write_html

        if args.v5:
            from .html_emitter import generate_v5_html

            print("\n[6/6] Generating V5 React Flow HTML visualization...")
            html = generate_v5_html(entities, relationships, infrastructure)
            html_path = args.output_dir / "PTS_DATA_ARCHITECTURE_EXPLORER_V5.html"
        else:
            print("\n[6/6] Generating V4 HTML visualization...")
            html = generate_v4_html(entities, relationships, infrastructure)
            html_path = args.output_dir / "PTS_DATA_ARCHITECTURE_EXPLORER_V4.html"
        write_html(html, html_path)

    # Summary
    print("\n" + "=" * 60)
    print("CONSOLIDATION COMPLETE")
    print("=" * 60)
    print(f"  Entities:       {len(entities)}")
    print(f"  Properties:     {total_props}")
    print(f"  Relationships:  {len(relationships)}")
    print(f"  Multi-project:  {multi_project} entities span multiple repos")

    # Category breakdown
    from .name_map import CATEGORY_DEFS

    print("\n  Category breakdown:")
    for cat_name in CATEGORY_DEFS:
        count = sum(1 for e in entities.values() if e.get("category") == cat_name)
        if count:
            print(f"    {cat_name}: {count}")

    print(f"\n  Output: {args.output_dir}")


if __name__ == "__main__":
    main()
