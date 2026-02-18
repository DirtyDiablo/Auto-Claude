"""
Domain Corpus Builder — Assembles training data from all BD platform sources.

Sources:
  - Bullhorn call notes (50K+ records from SQLite)
  - Job descriptions (Qdrant jobs collection + CSV)
  - Federal program descriptions (388 records)
  - Contact profiles (titles, functional areas, programs)
  - Meeting notes (master_notes.csv, 2,687 records)
  - BD playbook documents (.docx)

Output: data/embeddings/domain_corpus.jsonl
"""

import os
import sys
import csv
import json
import sqlite3
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent
E7_DATA = BASE_DIR / "Engine7_BullhornETL" / "data"
E7_ANALYSIS = BASE_DIR / "Engine7_BullhornETL" / "colton_scurry_analysis"
DATA_DIR = BASE_DIR / "data"
E8_DATA = Path(__file__).parent.parent / "data"
OUTPUT_DIR = E8_DATA / "embeddings"


@dataclass
class CorpusStats:
    """Statistics about the built corpus."""

    total_documents: int = 0
    total_tokens_approx: int = 0
    category_distribution: Dict[str, int] = field(default_factory=dict)
    sources_processed: List[str] = field(default_factory=list)
    built_at: str = ""
    output_path: str = ""


class DomainCorpusBuilder:
    """
    Assembles domain training data from all BD platform sources
    into a unified JSONL corpus for embedding fine-tuning.
    """

    MAX_CHUNK_TOKENS = 512  # approximate, using word-count heuristic

    def __init__(self):
        self.sources: List[Dict[str, str]] = [
            {
                "name": "bullhorn_notes",
                "type": "sqlite",
                "path": str(E7_DATA / "bullhorn_master.db"),
            },
            {
                "name": "master_notes",
                "type": "csv",
                "path": str(E7_ANALYSIS / "master_notes.csv"),
            },
            {
                "name": "federal_programs",
                "type": "csv",
                "path": str(
                    DATA_DIR / "archive" / "federal_programs_versions" / "Federal_Programs_Enriched.csv"
                ),
            },
            {
                "name": "contacts",
                "type": "csv",
                "path": str(E7_ANALYSIS / "contacts.csv"),
            },
            {
                "name": "acronyms",
                "type": "csv",
                "path": str(E7_ANALYSIS / "acronyms.csv"),
            },
        ]
        self._seen_hashes: set = set()

    def _approx_tokens(self, text: str) -> int:
        """Approximate token count using word-based heuristic."""
        return len(text.split())

    def _chunk_text(self, text: str, max_tokens: int = None) -> List[str]:
        """Split text into chunks of approximate max_tokens."""
        max_tokens = max_tokens or self.MAX_CHUNK_TOKENS
        words = text.split()
        if len(words) <= max_tokens:
            return [text]

        chunks = []
        for i in range(0, len(words), max_tokens):
            chunk = " ".join(words[i : i + max_tokens])
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    def _deduplicate(self, text: str) -> bool:
        """Return True if text is new (not a duplicate). Adds to seen set."""
        h = hashlib.md5(text.strip().lower().encode()).hexdigest()
        if h in self._seen_hashes:
            return False
        self._seen_hashes.add(h)
        return True

    def _extract_bullhorn_notes(self) -> List[Dict]:
        """Extract call notes from Bullhorn SQLite database."""
        docs = []
        db_path = E7_DATA / "bullhorn_master.db"
        if not db_path.exists():
            # Try alternate location
            db_path = DATA_DIR / "bullhorn_master.db"
        if not db_path.exists():
            logger.warning("Bullhorn DB not found, skipping call notes")
            return docs

        try:
            conn = sqlite3.connect(str(db_path))
            # Try call_notes table first, then activities
            for table in ["call_notes", "activities"]:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    if count == 0:
                        continue

                    # Get text columns
                    cols_cursor = conn.execute(f"PRAGMA table_info({table})")
                    cols = [row[1] for row in cols_cursor]

                    text_cols = [
                        c
                        for c in cols
                        if c.lower()
                        in (
                            "comments",
                            "notes",
                            "note",
                            "description",
                            "action",
                            "about",
                            "subject",
                            "body",
                            "text",
                            "comment",
                        )
                    ]

                    if not text_cols:
                        continue

                    select = ", ".join(text_cols)
                    rows = conn.execute(f"SELECT {select} FROM {table} LIMIT 50000")

                    for row in rows:
                        parts = [
                            str(v).strip()
                            for v in row
                            if v and str(v).strip() and str(v) != "None"
                        ]
                        text = " | ".join(parts)
                        if len(text) < 20:
                            continue

                        for chunk in self._chunk_text(text):
                            if self._deduplicate(chunk):
                                docs.append(
                                    {
                                        "text": chunk,
                                        "source": "bullhorn",
                                        "category": "call_notes",
                                    }
                                )
                    logger.info(f"Extracted {len(docs)} docs from {table}")
                    break  # Use first table that works
                except sqlite3.OperationalError:
                    continue

            conn.close()
        except Exception as e:
            logger.warning(f"Error extracting Bullhorn notes: {e}")

        return docs

    def _extract_master_notes(self) -> List[Dict]:
        """Extract from master_notes.csv."""
        docs = []
        path = E7_ANALYSIS / "master_notes.csv"
        if not path.exists():
            logger.warning("master_notes.csv not found, skipping")
            return docs

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    parts = []
                    for key in [
                        "about",
                        "notes",
                        "note",
                        "action",
                        "subject",
                        "description",
                        "comments",
                    ]:
                        val = row.get(key, "")
                        if val and val.strip() and val != "None":
                            parts.append(val.strip())

                    text = " | ".join(parts)
                    if len(text) < 20:
                        continue

                    for chunk in self._chunk_text(text):
                        if self._deduplicate(chunk):
                            docs.append(
                                {
                                    "text": chunk,
                                    "source": "master_notes",
                                    "category": "meeting_notes",
                                }
                            )
        except Exception as e:
            logger.warning(f"Error extracting master notes: {e}")

        return docs

    def _extract_federal_programs(self) -> List[Dict]:
        """Extract program descriptions from Federal Programs CSV."""
        docs = []
        candidates = [
            DATA_DIR / "archive" / "federal_programs_versions" / "Federal_Programs_Enriched.csv",
            DATA_DIR / "enriched" / "programs" / "Federal_Programs_MASTER_V4.csv",
        ]

        path = None
        for p in candidates:
            if p.exists():
                path = p
                break

        if not path:
            logger.warning("Federal Programs CSV not found, skipping")
            return docs

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    parts = []
                    for key in row:
                        val = row.get(key, "")
                        if val and val.strip() and val != "None" and len(val) > 2:
                            parts.append(f"{key}: {val.strip()}")

                    text = " | ".join(parts)
                    if len(text) < 30:
                        continue

                    for chunk in self._chunk_text(text):
                        if self._deduplicate(chunk):
                            docs.append(
                                {
                                    "text": chunk,
                                    "source": "federal_programs",
                                    "category": "programs",
                                }
                            )
        except Exception as e:
            logger.warning(f"Error extracting federal programs: {e}")

        return docs

    def _extract_contacts(self) -> List[Dict]:
        """Extract contact profiles from contacts CSV."""
        docs = []
        path = E7_ANALYSIS / "contacts.csv"
        if not path.exists():
            logger.warning("contacts.csv not found, skipping")
            return docs

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("name", row.get("Name", ""))
                    title = row.get("title", row.get("Title", ""))
                    company = row.get("company", row.get("Company", ""))
                    program = row.get("program", row.get("Program", ""))

                    parts = [
                        p
                        for p in [name, title, company, program]
                        if p and p.strip() and p != "None"
                    ]
                    text = " | ".join(parts)
                    if len(text) < 15:
                        continue

                    if self._deduplicate(text):
                        docs.append(
                            {
                                "text": text,
                                "source": "contacts",
                                "category": "contacts",
                            }
                        )
        except Exception as e:
            logger.warning(f"Error extracting contacts: {e}")

        return docs

    def _extract_qdrant_collections(self) -> List[Dict]:
        """Extract documents from Qdrant vector store collections."""
        docs = []
        try:
            from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore

            store = BDKnowledgeStore()

            for collection in ["jobs", "programs", "contacts", "documents"]:
                try:
                    results = store.get_all(collection, limit=2000)
                    for r in results:
                        payload = r.payload if hasattr(r, "payload") else r
                        text_fields = [
                            "text",
                            "content",
                            "description",
                            "name",
                            "title",
                        ]
                        parts = []
                        for field in text_fields:
                            val = payload.get(field, "")
                            if val and str(val).strip() and str(val) != "None":
                                parts.append(str(val).strip())

                        text = " | ".join(parts)
                        if len(text) < 20:
                            continue

                        for chunk in self._chunk_text(text):
                            if self._deduplicate(chunk):
                                docs.append(
                                    {
                                        "text": chunk,
                                        "source": f"qdrant_{collection}",
                                        "category": collection,
                                    }
                                )
                except Exception:
                    continue
        except ImportError:
            logger.warning("Vector store not available, skipping Qdrant extraction")
        except Exception as e:
            logger.warning(f"Error extracting from Qdrant: {e}")

        return docs

    def build_corpus(self) -> CorpusStats:
        """
        Build the full domain corpus from all sources.
        Writes to data/embeddings/domain_corpus.jsonl.
        """
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / "domain_corpus.jsonl"

        self._seen_hashes.clear()
        all_docs: List[Dict] = []
        stats = CorpusStats(built_at=datetime.now().isoformat())

        # Extract from each source
        extractors = [
            ("bullhorn_notes", self._extract_bullhorn_notes),
            ("master_notes", self._extract_master_notes),
            ("federal_programs", self._extract_federal_programs),
            ("contacts", self._extract_contacts),
            ("qdrant_collections", self._extract_qdrant_collections),
        ]

        for name, extractor in extractors:
            try:
                docs = extractor()
                all_docs.extend(docs)
                stats.sources_processed.append(f"{name}: {len(docs)}")
                logger.info(f"  {name}: {len(docs)} documents")
            except Exception as e:
                logger.warning(f"  {name}: error - {e}")
                stats.sources_processed.append(f"{name}: error")

        # Write JSONL
        with open(output_path, "w", encoding="utf-8") as f:
            for doc in all_docs:
                f.write(json.dumps(doc) + "\n")

        # Compute stats
        category_dist: Dict[str, int] = {}
        total_tokens = 0
        for doc in all_docs:
            cat = doc.get("category", "other")
            category_dist[cat] = category_dist.get(cat, 0) + 1
            total_tokens += self._approx_tokens(doc["text"])

        stats.total_documents = len(all_docs)
        stats.total_tokens_approx = total_tokens
        stats.category_distribution = category_dist
        stats.output_path = str(output_path)

        # Save stats
        stats_path = OUTPUT_DIR / "corpus_stats.json"
        with open(stats_path, "w") as f:
            json.dump(asdict(stats), f, indent=2)

        logger.info(
            f"Corpus built: {stats.total_documents} documents, ~{stats.total_tokens_approx} tokens"
        )
        return stats

    def get_corpus_sample(self, n: int = 10) -> List[Dict]:
        """Get a random sample from the corpus."""
        corpus_path = OUTPUT_DIR / "domain_corpus.jsonl"
        if not corpus_path.exists():
            return []

        import random

        docs = []
        with open(corpus_path, "r", encoding="utf-8") as f:
            for line in f:
                docs.append(json.loads(line))

        return random.sample(docs, min(n, len(docs)))

    def get_stats(self) -> Optional[Dict]:
        """Load saved corpus stats."""
        stats_path = OUTPUT_DIR / "corpus_stats.json"
        if stats_path.exists():
            with open(stats_path, "r") as f:
                return json.load(f)
        return None
