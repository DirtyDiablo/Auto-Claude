"""Architecture data loaders.

Reads architecture JSON files and normalizes their structures.
Optionally extracts embedded data from HTML Cytoscape.js files.
"""

import json
import re
from pathlib import Path


def load_architecture_json(path: Path) -> dict:
    """Load and normalize an architecture JSON file.

    Normalizes:
    - Relationship keys: source/from -> from, target/to -> to
    - Storage fields: pipe-delimited strings -> lists
    - Ensures entities/relationships are lists
    """
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)

    # Ensure required top-level keys
    data.setdefault("entities", [])
    data.setdefault("relationships", [])
    data.setdefault("project_id", path.stem.upper())

    # Normalize relationships
    normalized_rels = []
    for r in data.get("relationships", []):
        normalized_rels.append(_normalize_rel_keys(r))
    data["relationships"] = normalized_rels

    # Normalize entity storage fields
    for ent in data.get("entities", []):
        storage = ent.get("storage", [])
        if isinstance(storage, str):
            ent["storage"] = _parse_pipe_delimited(storage)
        elif not isinstance(storage, list):
            ent["storage"] = []

    return data


def _normalize_rel_keys(rel: dict) -> dict:
    """Normalize relationship keys to canonical {from, to, label, type}."""
    return {
        "from": rel.get("from", "") or rel.get("source", ""),
        "to": rel.get("to", "") or rel.get("target", ""),
        "label": rel.get("label", "") or rel.get("type", ""),
        "type": rel.get("cardinality", "") or rel.get("type", "FK"),
        "description": rel.get("description", "") or rel.get("note", ""),
    }


def _parse_pipe_delimited(s: str) -> list[str]:
    """Parse 'csv:foo.csv | api:bar' into ['csv:foo.csv', 'api:bar']."""
    return [part.strip() for part in s.split("|") if part.strip()]


def extract_data_from_html(path: Path) -> dict:
    """Extract embedded JS data from a Cytoscape.js HTML explorer.

    Parses const NODES = {...}; and const RELATIONSHIPS = [...]; blocks.
    Returns {'entities': [...], 'relationships': [...]}.
    """
    html = path.read_text(encoding="utf-8")
    result = {"entities": [], "relationships": []}

    # Extract NODES block
    nodes_match = re.search(r"const\s+NODES\s*=\s*\{(.+?)\n\};", html, re.DOTALL)
    if nodes_match:
        result["entities"] = _parse_js_nodes(nodes_match.group(0))

    # Extract RELATIONSHIPS block
    rels_match = re.search(r"const\s+RELATIONSHIPS\s*=\s*\[(.+?)\n\];", html, re.DOTALL)
    if rels_match:
        result["relationships"] = _parse_js_relationships(rels_match.group(0))

    return result


def _parse_js_nodes(js_block: str) -> list[dict]:
    """Best-effort parse of JS NODES object into entity list.

    Uses regex to extract entity names and property counts.
    Not a full JS parser -- extracts what we can.
    """
    entities = []
    # Match each top-level entity key
    entity_pattern = re.compile(
        r'"([^"]+)":\s*\{[^}]*?'
        r'pk:\s*"([^"]*)".*?'
        r'records:\s*"([^"]*)".*?'
        r'category:\s*"([^"]*)".*?'
        r'desc:\s*"([^"]*)".*?'
        r"propCount:\s*(\d+)",
        re.DOTALL,
    )
    for m in entity_pattern.finditer(js_block):
        entities.append(
            {
                "name": m.group(1),
                "pk": m.group(2),
                "records": m.group(3),
                "category": m.group(4),
                "description": m.group(5),
                "property_count": int(m.group(6)),
            }
        )
    return entities


def _parse_js_relationships(js_block: str) -> list[dict]:
    """Best-effort parse of JS RELATIONSHIPS array."""
    rels = []
    rel_pattern = re.compile(
        r'from:\s*"([^"]*)".*?'
        r'to:\s*"([^"]*)".*?'
        r'label:\s*"([^"]*)".*?'
        r'type:\s*"([^"]*)"',
        re.DOTALL,
    )
    for m in rel_pattern.finditer(js_block):
        rels.append(
            {
                "from": m.group(1),
                "to": m.group(2),
                "label": m.group(3),
                "type": m.group(4),
            }
        )
    return rels
