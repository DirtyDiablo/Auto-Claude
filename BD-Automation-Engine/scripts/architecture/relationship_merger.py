"""Relationship consolidation and cross-repo discovery.

Merges relationships from 3 JSONs + curated V2 data, deduplicates,
and optionally discovers missing cross-repo FK connections.
"""

import re

from .name_map import get_canonical_name
from .curated_data import V2_ONLY_RELATIONSHIPS


def normalize_cardinality(raw: str) -> str:
    """Normalize relationship cardinality to canonical form."""
    norm = raw.strip().lower().replace(' ', '-')
    mapping = {
        'many-to-one': 'FK', 'many-one': 'FK', 'm:1': 'FK', 'fk': 'FK',
        'one-to-many': 'one-many', 'one-many': 'one-many', '1:m': 'one-many',
        'many-to-many': 'many', 'many-many': 'many', 'm:m': 'many', 'many': 'many',
        'one-to-one': 'one-one', 'one-one': 'one-one', '1:1': 'one-one',
        'derived': 'derived',
    }
    return mapping.get(norm, 'FK')


def normalize_label(raw: str) -> str:
    """Normalize relationship labels to lowercase_underscored."""
    return raw.strip().upper().replace(' ', '_').lower()


def extract_relationships(data: dict, project_id: str) -> list[dict]:
    """Extract and normalize relationships from a JSON architecture file."""
    rels = []
    for r in data.get('relationships', []):
        src = r.get('from', '') or r.get('source', '')
        tgt = r.get('to', '') or r.get('target', '')
        label = r.get('label', '') or r.get('type', '')
        rtype = r.get('type', 'FK') or r.get('cardinality', 'FK')
        desc = r.get('description', '') or r.get('note', '')

        canonical_src = get_canonical_name(project_id, src)
        canonical_tgt = get_canonical_name(project_id, tgt)

        if canonical_src and canonical_tgt and label:
            rels.append({
                'from': canonical_src,
                'to': canonical_tgt,
                'label': normalize_label(label),
                'type': normalize_cardinality(rtype),
                'description': desc,
                'contributed_by': [project_id],
            })
    return rels


def discover_fk_relationships(entities: dict, existing_rels: list[dict]) -> list[dict]:
    """Auto-discover relationships by analyzing FK property names.

    If entity A has a property like 'program_id' or 'contractor_id',
    and a matching entity exists, create a relationship.
    """
    # Build lookup: lowercase entity name -> canonical name
    entity_lookup = {}
    for name in entities:
        entity_lookup[name.lower()] = name
        entity_lookup[name.lower().replace(' ', '_')] = name
        # Also try singular forms
        if name.lower().endswith('s'):
            entity_lookup[name.lower()[:-1]] = name

    # Existing relationship keys to avoid duplicates
    existing_keys = {(r['from'], r['to']) for r in existing_rels}

    discovered = []
    fk_pattern = re.compile(r'^(\w+?)_(?:id|name|code)$', re.I)

    for entity_name, entity_data in entities.items():
        for prop in entity_data.get('properties', []):
            pname = prop.get('name', '')
            m = fk_pattern.match(pname)
            if not m:
                continue

            ref_hint = m.group(1).lower()
            target = entity_lookup.get(ref_hint)
            if not target or target == entity_name:
                continue

            key = (entity_name, target)
            if key in existing_keys:
                continue

            existing_keys.add(key)
            discovered.append({
                'from': entity_name,
                'to': target,
                'label': f'has_{ref_hint}',
                'type': 'FK',
                'description': f'Auto-discovered from {entity_name}.{pname}',
                'contributed_by': ['AUTO_DISCOVERED'],
            })

    return discovered


def build_merged_relationships(
    *project_datasets: tuple[str, dict],
    entities: dict,
    discover: bool = False,
) -> list[dict]:
    """Full relationship merge pipeline.

    Args:
        project_datasets: tuples of (project_id, json_data)
        entities: merged entity dict (to validate references)
        discover: whether to auto-discover FK relationships
    """
    all_rels = []

    # Extract from each JSON
    for project_id, data in project_datasets:
        all_rels.extend(extract_relationships(data, project_id))

    # Add curated V2 relationships
    for r in V2_ONLY_RELATIONSHIPS:
        all_rels.append({
            'from': r['from'],
            'to': r['to'],
            'label': r['label'],
            'type': r['type'],
            'description': '',
            'contributed_by': ['V2_CURATED'],
        })

    # Deduplicate by (from, to, label), keeping first occurrence
    seen = {}
    deduped = []
    for r in all_rels:
        key = (r['from'], r['to'], r['label'])
        if key in seen:
            # Merge contributed_by
            for c in r.get('contributed_by', []):
                if c not in seen[key]['contributed_by']:
                    seen[key]['contributed_by'].append(c)
        elif r['from'] in entities and r['to'] in entities:
            seen[key] = r
            deduped.append(r)

    # Auto-discover cross-repo FK relationships
    if discover:
        discovered = discover_fk_relationships(entities, deduped)
        deduped.extend(discovered)

    return deduped
