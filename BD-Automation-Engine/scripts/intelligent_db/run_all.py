"""
Master Orchestrator - Runs all intelligent database enhancement phases in order.

Usage:
    python -m scripts.intelligent_db.run_all [--phase N] [--db PATH] [--skip-embeddings]

Phases:
    1: Data Quality & Cleanup (scoring fix, FPDS drop, normalize, dedup, quality scores)
    2: AI Labeling & Classification (contacts, programs, activities, orphan linking)
    3: Knowledge Graph Population (entities, relationships, influence, communities)
    4: Intelligence Layer (re-index Qdrant, smart query, summaries)
    5: Continuous Enrichment (incremental updates, freshness view)
"""
import argparse
import sqlite3
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data" / "unified_federal_contracts.db"


def phase_1(db_path):
    """Phase 1: Data Quality & Cleanup."""
    print("\n" + "=" * 60)
    print("PHASE 1: Data Quality & Cleanup")
    print("=" * 60)

    # 1.1 Fix scoring overflow
    print("\n--- 1.1 Fix Scoring Overflow ---")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("UPDATE scoring SET composite_score = 100.0 WHERE composite_score > 100")
    fixed_scoring = cursor.rowcount
    cursor.execute("UPDATE intelligence SET bd_score = 100.0 WHERE bd_score > 100")
    fixed_intel = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"  Fixed {fixed_scoring} scoring + {fixed_intel} intelligence overflow records")

    # 1.2 Drop FPDS null columns
    print("\n--- 1.2 Drop FPDS NULL Columns ---")
    from scripts.master_db.migrations.m001_drop_fpds_nulls import run as drop_fpds
    drop_fpds(db_path)

    # 1.4 Normalize company names (before dedup)
    print("\n--- 1.4 Normalize Company Names ---")
    from scripts.intelligent_db.normalize_companies import run as normalize
    normalize(db_path)

    # 1.5 Contact deduplication
    print("\n--- 1.5 Contact Deduplication ---")
    from scripts.intelligent_db.dedup_contacts import run as dedup
    dedup(db_path)

    # 1.6 Populate priority_level
    print("\n--- 1.6 Populate Priority Level ---")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # From scoring table
    cursor.execute("""
        UPDATE programs SET priority_level = (
            SELECT s.priority_tier FROM scoring s
            WHERE s.entity_id = programs.id AND s.entity_type = 'program'
            AND s.priority_tier IS NOT NULL
        ) WHERE priority_level IS NULL OR TRIM(priority_level) = ''
    """)
    from_scoring = cursor.rowcount

    # Fallback by contract value
    cursor.execute("""
        UPDATE programs SET priority_level = CASE
            WHEN total_contract_value >= 100000000 THEN 'Hot'
            WHEN total_contract_value >= 10000000 THEN 'Warm'
            WHEN total_contract_value > 0 THEN 'Cold'
            ELSE 'Unscored'
        END
        WHERE priority_level IS NULL OR TRIM(priority_level) = ''
    """)
    from_value = cursor.rowcount

    conn.commit()
    conn.close()
    print(f"  Priority from scoring: {from_scoring}, from value: {from_value}")

    # 1.3 Backfill source_tracking
    print("\n--- 1.3 Backfill Source Tracking ---")
    from scripts.master_db.migrations.m002_backfill_source_tracking import run as backfill
    backfill(db_path)

    # 1.7 Data quality scores
    print("\n--- 1.7 Data Quality Scores ---")
    from scripts.intelligent_db.data_quality_scores import run as quality
    quality(db_path)


def phase_2(db_path):
    """Phase 2: AI Labeling & Classification."""
    print("\n" + "=" * 60)
    print("PHASE 2: AI Labeling & Classification")
    print("=" * 60)

    # 2.1 Contact classification
    print("\n--- 2.1 Contact Classification ---")
    from scripts.intelligent_db.classify_contacts import run as classify
    classify(db_path)

    # 2.2 Program domain tagging
    print("\n--- 2.2 Program Domain Tagging ---")
    from scripts.intelligent_db.tag_programs import run as tag
    tag(db_path)

    # 2.3 Activity scoring
    print("\n--- 2.3 Activity Scoring ---")
    from scripts.intelligent_db.score_activities import run as score
    score(db_path)

    # 2.4 Orphan contact linking
    print("\n--- 2.4 Orphan Contact Linking ---")
    from scripts.intelligent_db.link_orphans import run as link
    link(db_path)


def phase_3(db_path):
    """Phase 3: Knowledge Graph Population."""
    print("\n" + "=" * 60)
    print("PHASE 3: Knowledge Graph Population")
    print("=" * 60)

    # 3.1 Populate knowledge graph
    print("\n--- 3.1 Knowledge Graph Ingestion ---")
    from scripts.intelligent_db.populate_knowledge_graph import run as populate
    populate(db_path)

    # 3.2 & 3.3 Influence scoring and community detection
    # These depend on Engine8 graph modules being fully operational
    print("\n--- 3.2 Influence Scoring ---")
    try:
        from Engine8_Knowledge.graph.influence_scoring import InfluenceScorer
        graph_path = PROJECT_ROOT / "Engine8_Knowledge" / "data" / "bd_graph.db"
        scorer = InfluenceScorer(str(graph_path))
        scores = scorer.compute_scores()
        print(f"  Computed influence scores for {len(scores)} entities")

        # Store back into scoring table
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        for entity_id, score_data in scores.items():
            from scripts.master_db.utils import generate_id
            sid = generate_id(entity_id, "influence_score")
            cursor.execute("""
                INSERT OR REPLACE INTO scoring
                (id, entity_type, entity_id, composite_score, source)
                VALUES (?, 'influence', ?, ?, 'influence_graph')
            """, (sid, entity_id, score_data.get("score", 0)))
        conn.commit()
        conn.close()
    except (ImportError, Exception) as e:
        print(f"  Skipped: {e}")

    print("\n--- 3.3 Community Detection ---")
    try:
        from Engine8_Knowledge.graph.community_detection import CommunityDetector
        graph_path = PROJECT_ROOT / "Engine8_Knowledge" / "data" / "bd_graph.db"
        detector = CommunityDetector(str(graph_path))
        communities = detector.detect()
        print(f"  Detected {len(set(communities.values()))} communities across {len(communities)} entities")

        # Store community_id back
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        for col in ["contacts", "programs", "companies"]:
            cursor.execute(f"PRAGMA table_info({col})")
            cols = [r[1] for r in cursor.fetchall()]
            if "community_id" not in cols:
                cursor.execute(f"ALTER TABLE {col} ADD COLUMN community_id INTEGER")
        for entity_id, comm_id in communities.items():
            for table in ["contacts", "programs", "companies"]:
                cursor.execute(
                    f"UPDATE {table} SET community_id = ? WHERE id = ?",
                    (comm_id, entity_id)
                )
        conn.commit()
        conn.close()
    except (ImportError, Exception) as e:
        print(f"  Skipped: {e}")


def phase_4(db_path, skip_embeddings=False):
    """Phase 4: Intelligence Layer."""
    print("\n" + "=" * 60)
    print("PHASE 4: Intelligence Layer")
    print("=" * 60)

    # 4.1 Qdrant re-index (embeddings)
    if not skip_embeddings:
        print("\n--- 4.1 Qdrant Embedding ---")
        from scripts.intelligent_db.embed_unified_db import run as embed
        embed(db_path)
    else:
        print("\n--- 4.1 Qdrant Embedding: SKIPPED (--skip-embeddings) ---")

    # 4.2 Smart query engine (just verify it loads)
    print("\n--- 4.2 Smart Query Engine ---")
    try:
        from scripts.intelligent_db.smart_query import SmartQueryEngine
        engine = SmartQueryEngine(db_path=db_path)
        result = engine.query("how many programs", limit=1)
        print(f"  Smart query test: {result.get('count', 0)} results via {result.get('systems_used', [])}")
    except Exception as e:
        print(f"  Smart query test: {e}")

    # 4.3 Program summaries
    print("\n--- 4.3 Program Summaries ---")
    from scripts.intelligent_db.generate_summaries import run as summarize
    summarize(db_path)


def phase_5(db_path):
    """Phase 5: Continuous Enrichment Pipeline."""
    print("\n" + "=" * 60)
    print("PHASE 5: Continuous Enrichment Pipeline")
    print("=" * 60)

    # 5.1 Incremental update detection
    print("\n--- 5.1 Incremental Update Detection ---")
    from scripts.intelligent_db.incremental_update import run as incremental
    incremental(db_path)

    # 5.3 Data freshness view
    print("\n--- 5.3 Data Freshness View ---")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("DROP VIEW IF EXISTS data_freshness_view")
    cursor.execute("""
        CREATE VIEW data_freshness_view AS
        SELECT
            table_name,
            COUNT(*) AS total_records,
            SUM(CASE WHEN julianday('now') - julianday(last_updated) <= 30 THEN 1 ELSE 0 END) AS fresh_30d,
            SUM(CASE WHEN julianday('now') - julianday(last_updated) BETWEEN 30 AND 90 THEN 1 ELSE 0 END) AS aging_90d,
            SUM(CASE WHEN julianday('now') - julianday(last_updated) BETWEEN 90 AND 365 THEN 1 ELSE 0 END) AS stale_1y,
            SUM(CASE WHEN julianday('now') - julianday(last_updated) > 365 THEN 1 ELSE 0 END) AS ancient,
            ROUND(AVG(julianday('now') - julianday(last_updated)), 1) AS avg_age_days
        FROM source_tracking
        GROUP BY table_name
    """)
    conn.commit()

    # Show freshness
    cursor.execute("SELECT * FROM data_freshness_view")
    rows = cursor.fetchall()
    if rows:
        print(f"  {'Table':<20} {'Total':>8} {'Fresh':>8} {'Aging':>8} {'Stale':>8} {'Avg Age':>8}")
        for row in rows:
            print(f"  {row[0]:<20} {row[1]:>8} {row[2]:>8} {row[3]:>8} {row[4]:>8} {row[6]:>8}")
    else:
        print("  No source_tracking data yet for freshness view")

    conn.close()


def run_verification(db_path):
    """Run verification checks."""
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    checks = [
        ("Scoring max", "SELECT MAX(composite_score) FROM scoring", lambda v: v is None or v <= 100),
        ("Quality scores (contacts)", "SELECT AVG(data_quality_score) FROM contacts", lambda v: v is not None),
        ("Domain tags", "SELECT COUNT(*) FROM programs WHERE domain_tags IS NOT NULL", lambda v: v > 0),
        ("Contact classification", "SELECT COUNT(*) FROM contacts WHERE tier IS NOT NULL", lambda v: v > 0),
        ("Activity scoring", "SELECT COUNT(*) FROM activities WHERE sentiment_score IS NOT NULL", lambda v: v > 0),
        ("Source tracking", "SELECT COUNT(*) FROM source_tracking", lambda v: v > 0),
        ("Program summaries", "SELECT COUNT(*) FROM documents WHERE doc_type = 'program_summary'", lambda v: v > 0),
    ]

    all_pass = True
    for name, query, check_fn in checks:
        try:
            cursor.execute(query)
            value = cursor.fetchone()[0]
            passed = check_fn(value)
            status = "PASS" if passed else "FAIL"
            if not passed:
                all_pass = False
            print(f"  [{status}] {name}: {value}")
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            all_pass = False

    conn.close()
    return all_pass


def main():
    parser = argparse.ArgumentParser(description="Intelligent Database Enhancement Pipeline")
    parser.add_argument("--phase", type=int, help="Run only a specific phase (1-5)")
    parser.add_argument("--db", type=str, help="Database path")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip Qdrant embedding (Phase 4.1)")
    parser.add_argument("--verify-only", action="store_true", help="Only run verification")
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else DB_PATH

    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        sys.exit(1)

    print(f"Intelligent Database Enhancement Pipeline")
    print(f"Database: {db_path}")
    print(f"Size: {db_path.stat().st_size / 1024 / 1024:.1f} MB")

    if args.verify_only:
        run_verification(db_path)
        return

    start = time.time()

    phases = {
        1: lambda: phase_1(db_path),
        2: lambda: phase_2(db_path),
        3: lambda: phase_3(db_path),
        4: lambda: phase_4(db_path, args.skip_embeddings),
        5: lambda: phase_5(db_path),
    }

    if args.phase:
        if args.phase in phases:
            phases[args.phase]()
        else:
            print(f"Invalid phase: {args.phase}. Must be 1-5.")
            sys.exit(1)
    else:
        for phase_num in sorted(phases.keys()):
            phases[phase_num]()

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"Pipeline complete in {elapsed:.1f}s")
    print(f"{'=' * 60}")

    run_verification(db_path)


if __name__ == "__main__":
    main()
