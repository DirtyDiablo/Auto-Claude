"""Unified architecture JSON emitter.

Generates the unified_architecture.json output with full schema v4.0.
"""

import json
from datetime import datetime
from pathlib import Path

from .name_map import CATEGORY_DEFS, PROJECT_LABELS, assign_category


def _parse_storage(storage_list: list[str]) -> dict:
    """Parse storage strings into categorized dict.

    Input: ['qdrant:contacts', 'sqlite:bullhorn.db/candidates', 'neo4j:Person']
    Output: {'qdrant': ['contacts'], 'sqlite': ['bullhorn.db/candidates'], 'neo4j': ['Person']}
    """
    result = {'qdrant': [], 'sqlite': [], 'neo4j': [], 'notion': [], 'csv': [], 'api': []}
    for s in storage_list:
        if ':' in s:
            prefix, value = s.split(':', 1)
            prefix = prefix.strip().lower()
            result.setdefault(prefix, []).append(value.strip())
        else:
            result.setdefault('other', []).append(s)
    # Remove empty keys
    return {k: v for k, v in result.items() if v}


def _build_entity_output(name: str, ent: dict) -> dict:
    """Convert internal entity format to output JSON."""
    return {
        'canonical_name': name,
        'pk': ent.get('pk', 'id'),
        'records': ent.get('records', 'unknown'),
        'category': ent.get('category', assign_category(name)),
        'description': ent.get('description', ''),
        'lineage': {
            'projects': ent.get('projects', []),
            'original_names': ent.get('original_names', {}),
        },
        'sources': ent.get('sources', []),
        'storage': _parse_storage(ent.get('storage', [])),
        'properties': [
            {
                'name': p.get('name', ''),
                'type': p.get('type', 'string'),
                'raw_type': p.get('raw_type', p.get('type', '')),
                'nullable': p.get('nullable', False),
                'source': p.get('source', ''),
                'note': p.get('note', ''),
                'contributed_by': p.get('contributed_by', []),
                **({k: p[k] for k in ('fk_target', 'enum_values', 'vector_dim') if k in p}),
            }
            for p in ent.get('properties', [])
        ],
        'aliases': ent.get('aliases', []),
    }


def _build_category_summary(entities: dict) -> dict:
    """Build category breakdown with counts and colors."""
    summary = {}
    for cat_name, cat_data in CATEGORY_DEFS.items():
        count = sum(1 for e in entities.values()
                    if e.get('category') == cat_name)
        if count > 0:
            summary[cat_name] = {
                'count': count,
                'color': cat_data['color'],
            }
    return summary


def _build_project_stats(
    entities: dict,
    relationships: list[dict],
    project_datasets: list[tuple[str, dict]],
) -> list[dict]:
    """Build per-project statistics."""
    stats = []
    for project_id, data in project_datasets:
        scan_stats = data.get('scan_stats', {})
        stats.append({
            'id': project_id,
            'label': PROJECT_LABELS.get(project_id, project_id),
            'entities': scan_stats.get('entities_found', 0),
            'properties': scan_stats.get('properties_found', 0),
            'relationships': scan_stats.get('relationships_found', 0),
            'files_scanned': scan_stats.get('files_scanned',
                                            data.get('project_info', {}).get('files_scanned', 0)),
        })

    # Add curated data stats
    from .curated_data import V2_ONLY_ENTITIES, V2_ONLY_RELATIONSHIPS
    stats.append({
        'id': 'V2_CURATED',
        'label': 'V2-Curated',
        'entities': len(V2_ONLY_ENTITIES),
        'properties': sum(len(e.get('properties', [])) for e in V2_ONLY_ENTITIES.values()),
        'relationships': len(V2_ONLY_RELATIONSHIPS),
        'files_scanned': 0,
    })

    return stats


def generate_unified_json(
    entities: dict,
    relationships: list[dict],
    infrastructure: dict,
    project_datasets: list[tuple[str, dict]],
) -> dict:
    """Generate the complete unified_architecture.json structure."""
    total_props = sum(len(e.get('properties', [])) for e in entities.values())

    return {
        'schema_version': '4.0',
        'generated_date': datetime.now().strftime('%Y-%m-%d'),
        'generated_time': datetime.now().strftime('%H:%M:%S'),
        'generator': 'BD-Automation-Engine/scripts/architecture/consolidate.py',

        'summary': {
            'total_entities': len(entities),
            'total_properties': total_props,
            'total_relationships': len(relationships),
            'source_projects': _build_project_stats(
                entities, relationships, project_datasets
            ),
            'categories': _build_category_summary(entities),
        },

        'entities': [
            _build_entity_output(name, ent)
            for name, ent in sorted(entities.items())
        ],

        'relationships': [
            {
                'from': r['from'],
                'to': r['to'],
                'label': r['label'],
                'cardinality': r.get('type', 'FK'),
                'description': r.get('description', ''),
                'contributed_by': r.get('contributed_by', []),
            }
            for r in relationships
        ],

        'infrastructure': infrastructure,
    }


def write_unified_json(data: dict, output_path: Path) -> None:
    """Write the unified architecture JSON to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    size = output_path.stat().st_size
    print(f"  Written: {output_path} ({size:,} bytes)")
