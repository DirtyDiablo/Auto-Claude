"""Entity consolidation pipeline.

Merges entities from 3 architecture JSONs + curated V2 data into
a unified entity registry with cross-project lineage tracking.
"""

from collections import OrderedDict

from .name_map import get_canonical_name, assign_category
from .curated_data import V2_ONLY_ENTITIES
from .property_standardizer import standardize_property, merge_properties


def extract_entity(ent: dict, project_id: str) -> tuple[str | None, dict | None]:
    """Convert a JSON entity to canonical form.

    Returns (canonical_name, entity_data) or (None, None) if skipped.
    """
    name = ent.get("name", "")
    canonical = get_canonical_name(project_id, name)
    if canonical is None:
        return None, None

    # Standardize properties
    raw_props = ent.get("properties", [])
    properties = []
    seen_props = set()
    for p in raw_props:
        pname = p.get("name", "")
        if pname and pname not in seen_props:
            seen_props.add(pname)
            properties.append(standardize_property(p, project_id))

    # Extract aliases
    raw_aliases = ent.get("aliases", [])
    aliases = []
    for a in raw_aliases:
        alias_from = a.get("alias", "") or a.get("from", "")
        alias_to = a.get("canonical", "") or a.get("to", "")
        if alias_from and alias_to:
            aliases.append({"from": alias_from, "to": alias_to})

    # Normalize sources
    sources = ent.get("sources", [])
    if isinstance(sources, str):
        sources = [sources]

    # Normalize storage
    storage = ent.get("storage", [])
    if isinstance(storage, str):
        storage = [s.strip() for s in storage.split("|") if s.strip()]
    elif not isinstance(storage, list):
        storage = []

    return canonical, {
        "pk": ent.get("pk", "id"),
        "records": str(ent.get("records", "unknown")),
        "category": ent.get("category", "Meta/Ops"),
        "description": ent.get("desc", "")
        or ent.get("description", "")
        or f"{canonical} entity",
        "sources": sources,
        "storage": storage,
        "properties": properties,
        "aliases": aliases,
        "projects": [project_id],
        "original_names": {project_id: name},
    }


def merge_entity(existing: dict, new_data: dict) -> None:
    """Merge a new entity occurrence into an existing one."""
    # Track project lineage
    for p in new_data.get("projects", []):
        if p not in existing["projects"]:
            existing["projects"].append(p)

    # Track original names
    for proj, orig_name in new_data.get("original_names", {}).items():
        existing.setdefault("original_names", {})[proj] = orig_name

    # Merge sources (dedup)
    for s in new_data.get("sources", []):
        if s not in existing["sources"]:
            existing["sources"].append(s)

    # Merge storage (dedup)
    existing.setdefault("storage", [])
    for s in new_data.get("storage", []):
        if s not in existing["storage"]:
            existing["storage"].append(s)

    # Merge properties
    existing["properties"] = merge_properties(
        existing["properties"], new_data.get("properties", [])
    )

    # Merge aliases (dedup by from/to pair)
    existing_alias_keys = {(a["from"], a["to"]) for a in existing["aliases"]}
    for a in new_data.get("aliases", []):
        key = (a["from"], a["to"])
        if key not in existing_alias_keys:
            existing["aliases"].append(a)
            existing_alias_keys.add(key)

    # Pick richest description
    new_desc = new_data.get("description", "")
    if len(new_desc) > len(existing.get("description", "")):
        existing["description"] = new_desc


def _prepare_curated_entity(name: str, data: dict) -> dict:
    """Convert a V2_ONLY_ENTITY to the internal merge format."""
    properties = []
    for p in data.get("properties", []):
        properties.append(standardize_property(p, "V2_CURATED"))

    return {
        "pk": data.get("pk", "id"),
        "records": data.get("records", "unknown"),
        "category": data.get("category", "Meta/Ops"),
        "description": data.get("desc", "") or data.get("description", ""),
        "sources": list(data.get("sources", [])),
        "storage": [],
        "properties": properties,
        "aliases": list(data.get("aliases", [])),
        "projects": ["V2_CURATED"],
        "original_names": {"V2_CURATED": name},
    }


def build_merged_entities(
    *project_datasets: tuple[str, dict],
) -> OrderedDict:
    """Full entity merge pipeline.

    Args:
        project_datasets: tuples of (project_id, json_data) for each repo

    Returns:
        OrderedDict of canonical_name -> entity_data, sorted alphabetically
    """
    merged = OrderedDict()

    # Process each JSON
    for project_id, data in project_datasets:
        for ent in data.get("entities", []):
            canonical, entity_data = extract_entity(ent, project_id)
            if canonical is None:
                continue
            if canonical in merged:
                merge_entity(merged[canonical], entity_data)
            else:
                merged[canonical] = entity_data

    # Add V2-only curated entities
    for name, data in V2_ONLY_ENTITIES.items():
        if name not in merged:
            merged[name] = _prepare_curated_entity(name, data)

    # Assign categories and sort
    for name, ent in merged.items():
        ent["category"] = assign_category(name)

    return OrderedDict(sorted(merged.items()))
