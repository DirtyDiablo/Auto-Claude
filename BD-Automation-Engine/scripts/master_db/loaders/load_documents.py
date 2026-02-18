"""
Documents ETL Loader
Sources: outputs/BD_Briefings/*.md files, bd_graph.db document entities
"""

import sqlite3
from pathlib import Path

from ..utils import (
    Deduplicator,
    generate_id,
    safe_str,
)

BASE_DIR = Path(__file__).parent.parent.parent.parent


def load_documents(conn: sqlite3.Connection, verbose: bool = False) -> int:
    """Load documents from briefings and graph db."""
    cursor = conn.cursor()
    dedup = Deduplicator()
    loaded = 0

    # Source 1: BD Briefings markdown files
    briefings_dir = BASE_DIR / "data" / "deliverables" / "briefings"
    if briefings_dir.exists():
        loaded += _load_briefings(cursor, briefings_dir, dedup, verbose)

    # Source 2: bd_graph.db document entities
    graph_db = BASE_DIR / "Engine8_Knowledge" / "data" / "bd_graph.db"
    if graph_db.exists():
        loaded += _load_graph_docs(cursor, graph_db, dedup, verbose)

    conn.commit()
    if verbose:
        print(f"  Documents loaded: {loaded} ({dedup.stats})")
    return loaded


def _load_briefings(cursor, briefings_dir: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load BD briefing markdown files."""
    count = 0
    for md_file in sorted(briefings_dir.glob("*.md")):
        if not dedup.is_new(md_file.name):
            continue

        # Parse program name from filename
        # e.g. "AF DCGS - Langley_Intelligence Analyst_Playbook.md"
        stem = md_file.stem
        parts = stem.split("_")
        program_name = parts[0] if parts else stem

        # Determine doc type from filename
        doc_type = "briefing"
        lower = stem.lower()
        if "callscript" in lower:
            doc_type = "call_script"
        elif "email" in lower:
            doc_type = "email_template"
        elif "playbook" in lower:
            doc_type = "playbook"
        elif "talkingpoints" in lower:
            doc_type = "talking_points"

        content = md_file.read_text(encoding="utf-8", errors="replace")

        did = generate_id(md_file.name)
        cursor.execute("""
            INSERT OR IGNORE INTO documents (
                id, doc_type, title, file_path, content,
                program_name, source
            ) VALUES (?, ?, ?, ?, ?, ?, 'bd_briefings')
        """, (
            did, doc_type, stem, str(md_file), content,
            program_name,
        ))
        count += 1

    # Also load .txt files (email templates)
    for txt_file in sorted(briefings_dir.glob("*.txt")):
        if not dedup.is_new(txt_file.name):
            continue
        stem = txt_file.stem
        parts = stem.split("_")
        program_name = parts[0] if parts else stem
        content = txt_file.read_text(encoding="utf-8", errors="replace")

        did = generate_id(txt_file.name)
        cursor.execute("""
            INSERT OR IGNORE INTO documents (
                id, doc_type, title, file_path, content,
                program_name, source
            ) VALUES (?, 'email_template', ?, ?, ?, ?, 'bd_briefings')
        """, (did, stem, str(txt_file), content, program_name))
        count += 1

    if verbose:
        print(f"    BD Briefings: {count} documents")
    return count


def _load_graph_docs(cursor, db_path: Path, dedup: Deduplicator, verbose: bool) -> int:
    """Load document entities from bd_graph.db."""
    count = 0
    graph_conn = sqlite3.connect(str(db_path))
    graph_conn.row_factory = sqlite3.Row
    graph_cursor = graph_conn.cursor()

    graph_cursor.execute("SELECT * FROM entities WHERE type = 'document'")
    for row in graph_cursor.fetchall():
        name = row["name"]
        if not name or not dedup.is_new(name, "graph_doc"):
            continue

        did = generate_id(str(row["id"]), "graph_doc")
        cursor.execute("""
            INSERT OR IGNORE INTO documents (
                id, doc_type, title,
                entity_type, entity_properties,
                source
            ) VALUES (?, 'graph_document', ?, ?, ?, 'bd_graph')
        """, (
            did, name, row["type"], row["properties"],
        ))
        count += 1

    graph_conn.close()
    if verbose:
        print(f"    Graph documents: {count}")
    return count
