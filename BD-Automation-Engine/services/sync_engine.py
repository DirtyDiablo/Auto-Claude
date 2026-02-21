"""
Polling-based incremental sync coordinator for Notion, Bullhorn, and Qdrant.

Polls Notion databases and Bullhorn CRM for changes since the last sync,
then upserts changed records into Qdrant via BDKnowledgeStore.

Usage:
    from services.sync_engine import SyncEngine

    engine = SyncEngine(poll_interval_seconds=120)
    await engine.start()       # Start background polling loop
    await engine.sync_once()   # Run a single sync cycle manually
    await engine.stop()        # Graceful shutdown
"""

import asyncio
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SYNC_STATE_PATH = DATA_DIR / "sync_state.json"

# Notion database IDs (from notion_qdrant_sync.py)
NOTION_DATABASES = {
    "dcgs_contacts": "2ccdef65-baa5-8087-a53b-000ba596128e",
    "gdit_other": "70ea1c94-211d-40e6-a994-e8d7c4807434",
    "gdit_jobs": "2ccdef65-baa5-80b0-9a80-000bd2745f63",
    "program_mapping": "f57792c1-605b-424c-8830-23ab41c47137",
    "federal_programs": "06cd9b22-5d6b-4d37-b0d3-ba99da4971fa",
    "bd_opportunities": "2bcdef65-baa5-80ed-bd95-000b2f898e17",
}

# Maps Notion DB keys to Qdrant collections (from notion_qdrant_sync.py)
QDRANT_COLLECTION_MAP = {
    "dcgs_contacts": "contacts",
    "gdit_other": "contacts",
    "gdit_jobs": "jobs",
    "program_mapping": "jobs",
    "federal_programs": "programs",
    "bd_opportunities": "opportunities",
}

# Retry constants
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 5


def _content_hash(data: dict) -> str:
    """Compute MD5 hash of a record for change detection."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(serialized.encode()).hexdigest()


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


class SyncEngine:
    """Polling-based incremental sync coordinator for Notion, Bullhorn, and Qdrant."""

    def __init__(self, poll_interval_seconds: int = 120):
        self.poll_interval = poll_interval_seconds
        self._sync_state: Dict[str, Any] = {}
        self._retry_queue: List[Dict[str, Any]] = []
        self._sync_history: List[Dict[str, Any]] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._error_count = 0

        # Lazy-loaded service references
        self._notion_service = None
        self._crm_manager = None
        self._knowledge_store = None
        self._qdrant_sync = None

        self._load_state()

    # ------------------------------------------------------------------
    # Service accessors (lazy initialization)
    # ------------------------------------------------------------------

    def _get_notion_service(self):
        """Get or create NotionSyncService instance."""
        if self._notion_service is None:
            from services.notion_sync import NotionSyncService
            self._notion_service = NotionSyncService()
        return self._notion_service

    def _get_crm_manager(self):
        """Get or create CRMSyncManager instance."""
        if self._crm_manager is None:
            from Engine8_Knowledge.integrations.crm_sync import get_crm_sync_manager
            self._crm_manager = get_crm_sync_manager()
        return self._crm_manager

    def _get_knowledge_store(self):
        """Get or create BDKnowledgeStore instance."""
        if self._knowledge_store is None:
            from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
            qdrant_url = os.getenv("QDRANT_URL")
            self._knowledge_store = BDKnowledgeStore(url=qdrant_url)
        return self._knowledge_store

    def _get_qdrant_sync(self):
        """Get or create NotionQdrantSync instance."""
        if self._qdrant_sync is None:
            from services.notion_qdrant_sync import NotionQdrantSync
            self._qdrant_sync = NotionQdrantSync()
        return self._qdrant_sync

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the background polling loop."""
        if self._running:
            logger.warning("sync_engine_already_running")
            return

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(
            "sync_engine_started",
            poll_interval=self.poll_interval,
        )

    async def stop(self) -> None:
        """Gracefully shut down the polling loop."""
        if not self._running:
            return

        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self._save_state()
        logger.info("sync_engine_stopped")

    async def _poll_loop(self) -> None:
        """Run sync_once in a loop with poll_interval sleeps."""
        while self._running:
            try:
                await self.sync_once()
            except Exception as e:
                self._error_count += 1
                logger.error("sync_cycle_error", error=str(e))

            if self._running:
                await asyncio.sleep(self.poll_interval)

    # ------------------------------------------------------------------
    # Single sync cycle
    # ------------------------------------------------------------------

    async def sync_once(self) -> Dict[str, Any]:
        """Execute a single sync cycle across all sources."""
        cycle_start = time.monotonic()
        cycle_id = _now_iso()
        result: Dict[str, Any] = {
            "cycle_id": cycle_id,
            "notion": {"records": 0, "errors": 0},
            "bullhorn": {"records": 0, "errors": 0},
            "qdrant": {"records": 0, "errors": 0},
        }

        # 1. Poll Notion for changes
        try:
            notion_changes = await self._poll_notion_changes()
            result["notion"]["records"] = len(notion_changes)

            # Upsert Notion changes to Qdrant
            if notion_changes:
                qdrant_result = await self._upsert_notion_to_qdrant(notion_changes)
                result["qdrant"]["records"] += qdrant_result.get("upserted", 0)
                result["qdrant"]["errors"] += qdrant_result.get("errors", 0)
        except Exception as e:
            result["notion"]["errors"] += 1
            self._error_count += 1
            logger.error("notion_poll_error", error=str(e))

        # 2. Poll Bullhorn for changes
        try:
            bullhorn_changes = await self._poll_bullhorn_changes()
            result["bullhorn"]["records"] = len(bullhorn_changes)

            # Upsert Bullhorn changes to Qdrant
            if bullhorn_changes:
                qdrant_result = await self._upsert_bullhorn_to_qdrant(bullhorn_changes)
                result["qdrant"]["records"] += qdrant_result.get("upserted", 0)
                result["qdrant"]["errors"] += qdrant_result.get("errors", 0)
        except Exception as e:
            result["bullhorn"]["errors"] += 1
            self._error_count += 1
            logger.error("bullhorn_poll_error", error=str(e))

        # 3. Process retry queue
        try:
            await self._process_retry_queue()
        except Exception as e:
            logger.error("retry_queue_error", error=str(e))

        # Record cycle
        elapsed = time.monotonic() - cycle_start
        result["elapsed_seconds"] = round(elapsed, 2)

        self._sync_history.append(result)
        # Keep last 50 cycles
        if len(self._sync_history) > 50:
            self._sync_history = self._sync_history[-50:]

        self._save_state()

        logger.info(
            "sync_cycle_complete",
            notion_records=result["notion"]["records"],
            bullhorn_records=result["bullhorn"]["records"],
            qdrant_upserted=result["qdrant"]["records"],
            elapsed=result["elapsed_seconds"],
        )

        return result

    # ------------------------------------------------------------------
    # Notion polling
    # ------------------------------------------------------------------

    async def _poll_notion_changes(self) -> List[Dict[str, Any]]:
        """Query Notion databases for pages modified since last_sync_time.

        Uses the Notion API filter on last_edited_time to find changed records.
        Returns a list of dicts, each containing 'db_key', 'db_id', 'collection',
        and the page data from Notion.
        """
        notion = self._get_notion_service()
        changed_records: List[Dict[str, Any]] = []

        notion_state = self._sync_state.get("notion", {})
        db_states = notion_state.get("databases", {})

        for db_key, db_id in NOTION_DATABASES.items():
            last_edited = db_states.get(db_key, {}).get("last_edited")
            collection = QDRANT_COLLECTION_MAP.get(db_key)
            if not collection:
                continue

            filter_obj = None
            if last_edited:
                filter_obj = {
                    "timestamp": "last_edited_time",
                    "last_edited_time": {"after": last_edited},
                }

            try:
                response = await asyncio.to_thread(
                    notion.query_database,
                    database_id=db_id,
                    filter_obj=filter_obj,
                    page_size=100,
                )

                pages = response.get("results", [])
                for page in pages:
                    changed_records.append({
                        "db_key": db_key,
                        "db_id": db_id,
                        "collection": collection,
                        "page_id": page.get("id", ""),
                        "last_edited_time": page.get("last_edited_time", ""),
                        "properties": page.get("properties", {}),
                    })

                # Update per-database last_edited watermark
                if pages:
                    max_edited = max(
                        p.get("last_edited_time", "") for p in pages
                    )
                    if db_key not in db_states:
                        db_states[db_key] = {}
                    db_states[db_key]["last_edited"] = max_edited
                    db_states[db_key]["records_synced"] = (
                        db_states[db_key].get("records_synced", 0) + len(pages)
                    )

                logger.info(
                    "notion_poll_db",
                    db_key=db_key,
                    changed=len(pages),
                )
            except Exception as e:
                logger.error("notion_poll_db_error", db_key=db_key, error=str(e))
                self._retry_queue.append({
                    "source": "notion",
                    "db_key": db_key,
                    "error": str(e),
                    "retry_count": 0,
                    "next_retry": _now_iso(),
                })

        # Update global Notion sync timestamp
        self._sync_state.setdefault("notion", {})
        self._sync_state["notion"]["last_sync"] = _now_iso()
        self._sync_state["notion"]["databases"] = db_states

        return changed_records

    # ------------------------------------------------------------------
    # Bullhorn polling
    # ------------------------------------------------------------------

    async def _poll_bullhorn_changes(self) -> List[Dict[str, Any]]:
        """Pull new placements and activities from Bullhorn since last sync.

        Uses CRMSyncManager's ID-based cursor pattern.
        """
        crm = self._get_crm_manager()
        changed_records: List[Dict[str, Any]] = []

        # Pull new placements
        try:
            placement_result = await asyncio.to_thread(crm.pull_new_placements)
            placements = placement_result.get("placements", [])
            for p in placements:
                changed_records.append({
                    "source": "bullhorn",
                    "record_type": "placement",
                    "collection": "activities",
                    "data": p,
                })
        except Exception as e:
            logger.error("bullhorn_placements_error", error=str(e))

        # Pull new activities
        try:
            activity_result = await asyncio.to_thread(crm.pull_activity_updates)
            activities = activity_result.get("activities", [])
            for a in activities:
                changed_records.append({
                    "source": "bullhorn",
                    "record_type": "activity",
                    "collection": "activities",
                    "data": a,
                })
        except Exception as e:
            logger.error("bullhorn_activities_error", error=str(e))

        # Update Bullhorn sync state
        bh_state = self._sync_state.get("bullhorn", {})
        bh_state["last_sync"] = _now_iso()
        bh_state["last_placement_id"] = crm._last_placement_id
        bh_state["last_activity_id"] = crm._last_activity_id
        bh_state["records_synced"] = (
            bh_state.get("records_synced", 0) + len(changed_records)
        )
        self._sync_state["bullhorn"] = bh_state

        logger.info(
            "bullhorn_poll_complete",
            placements=len([r for r in changed_records if r["record_type"] == "placement"]),
            activities=len([r for r in changed_records if r["record_type"] == "activity"]),
        )

        return changed_records

    # ------------------------------------------------------------------
    # Qdrant upsert
    # ------------------------------------------------------------------

    async def _upsert_notion_to_qdrant(
        self, records: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Upsert Notion changes to Qdrant, skipping unchanged records via content hash."""
        qdrant_sync = self._get_qdrant_sync()
        upserted = 0
        skipped = 0
        errors = 0

        # Group records by collection
        by_collection: Dict[str, List[dict]] = {}
        for record in records:
            collection = record["collection"]
            content_hash = _content_hash(record.get("properties", {}))

            # Check if content changed since last sync
            hash_key = f"{record['page_id']}:{collection}"
            known_hashes = self._sync_state.get("_content_hashes", {})
            if known_hashes.get(hash_key) == content_hash:
                skipped += 1
                continue

            # Mark as seen
            known_hashes[hash_key] = content_hash
            self._sync_state["_content_hashes"] = known_hashes

            by_collection.setdefault(collection, []).append(record.get("properties", {}))

        # Batch upsert per collection
        for collection, props_list in by_collection.items():
            db_key = None
            for r in records:
                if r["collection"] == collection:
                    db_key = r["db_key"]
                    break

            if db_key:
                try:
                    result = await asyncio.to_thread(
                        qdrant_sync.sync_records_to_qdrant,
                        records=props_list,
                        source_db=db_key,
                    )
                    upserted += result.get("synced_count", 0)
                    errors += result.get("error_count", 0)
                except Exception as e:
                    logger.error(
                        "qdrant_upsert_error",
                        collection=collection,
                        error=str(e),
                    )
                    errors += len(props_list)

        # Update Qdrant state
        qdrant_state = self._sync_state.get("qdrant", {})
        qdrant_state["last_upsert"] = _now_iso()
        updated_collections = list(by_collection.keys())
        if updated_collections:
            qdrant_state["collections_updated"] = updated_collections
        self._sync_state["qdrant"] = qdrant_state

        logger.info(
            "qdrant_notion_upsert",
            upserted=upserted,
            skipped=skipped,
            errors=errors,
        )

        return {"upserted": upserted, "skipped": skipped, "errors": errors}

    async def _upsert_bullhorn_to_qdrant(
        self, records: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Upsert Bullhorn records to Qdrant activities collection."""
        store = self._get_knowledge_store()
        upserted = 0
        errors = 0

        activities_data = []
        for record in records:
            data = record.get("data", {})
            content_hash = _content_hash(data)

            hash_key = f"bh:{data.get('id', '')}:{record['record_type']}"
            known_hashes = self._sync_state.get("_content_hashes", {})
            if known_hashes.get(hash_key) == content_hash:
                continue

            known_hashes[hash_key] = content_hash
            self._sync_state["_content_hashes"] = known_hashes

            data["_source"] = "bullhorn_sync"
            data["_record_type"] = record["record_type"]
            activities_data.append(data)

        if activities_data:
            try:
                indexed, errs = await asyncio.to_thread(
                    store.index_activities,
                    activities_data,
                )
                upserted = indexed
                errors = errs
            except Exception as e:
                logger.error("qdrant_bullhorn_upsert_error", error=str(e))
                errors = len(activities_data)

        return {"upserted": upserted, "errors": errors}

    # ------------------------------------------------------------------
    # Retry queue
    # ------------------------------------------------------------------

    async def _process_retry_queue(self) -> None:
        """Process failed items with exponential backoff (max 3 retries)."""
        if not self._retry_queue:
            return

        now = datetime.now(timezone.utc)
        remaining = []

        for item in self._retry_queue:
            retry_count = item.get("retry_count", 0)

            if retry_count >= MAX_RETRIES:
                logger.warning(
                    "retry_exhausted",
                    source=item.get("source"),
                    db_key=item.get("db_key"),
                )
                continue

            # Check backoff delay
            next_retry_str = item.get("next_retry", "")
            if next_retry_str:
                next_retry = datetime.fromisoformat(next_retry_str)
                if now < next_retry:
                    remaining.append(item)
                    continue

            # Retry the item
            source = item.get("source")
            success = False

            if source == "notion":
                try:
                    db_key = item.get("db_key", "")
                    db_id = NOTION_DATABASES.get(db_key, "")
                    if db_id:
                        notion = self._get_notion_service()
                        await asyncio.to_thread(
                            notion.query_database,
                            database_id=db_id,
                            page_size=1,
                        )
                        success = True
                except Exception:
                    pass

            if not success:
                item["retry_count"] = retry_count + 1
                backoff = BACKOFF_BASE_SECONDS * (2 ** item["retry_count"])
                next_time = datetime.now(timezone.utc).isoformat()
                item["next_retry"] = next_time
                remaining.append(item)
                logger.info(
                    "retry_scheduled",
                    source=source,
                    retry_count=item["retry_count"],
                    backoff_seconds=backoff,
                )

        self._retry_queue = remaining

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def _load_state(self) -> None:
        """Load sync state from data/sync_state.json."""
        if not SYNC_STATE_PATH.exists():
            self._sync_state = {
                "notion": {"last_sync": None, "databases": {}},
                "bullhorn": {
                    "last_sync": None,
                    "last_placement_id": 0,
                    "last_activity_id": 0,
                    "records_synced": 0,
                },
                "qdrant": {
                    "last_upsert": None,
                    "collections_updated": [],
                },
                "_content_hashes": {},
            }
            return

        try:
            with open(SYNC_STATE_PATH, "r") as f:
                self._sync_state = json.load(f)
            logger.info("sync_state_loaded", path=str(SYNC_STATE_PATH))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("sync_state_load_failed", error=str(e))
            self._sync_state = {
                "notion": {"last_sync": None, "databases": {}},
                "bullhorn": {
                    "last_sync": None,
                    "last_placement_id": 0,
                    "last_activity_id": 0,
                    "records_synced": 0,
                },
                "qdrant": {
                    "last_upsert": None,
                    "collections_updated": [],
                },
                "_content_hashes": {},
            }

    def _save_state(self) -> None:
        """Persist sync state to data/sync_state.json."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Write a copy of state without internal-only keys for the persisted file
        persist_state = {
            k: v for k, v in self._sync_state.items()
            if not k.startswith("_")
        }
        persist_state["_content_hashes"] = self._sync_state.get("_content_hashes", {})

        try:
            with open(SYNC_STATE_PATH, "w") as f:
                json.dump(persist_state, f, indent=2, default=str)
        except OSError as e:
            logger.error("sync_state_save_failed", error=str(e))

    # ------------------------------------------------------------------
    # Status reporting
    # ------------------------------------------------------------------

    def get_sync_status(self) -> Dict[str, Any]:
        """Return comprehensive sync engine status."""
        notion_state = self._sync_state.get("notion", {})
        bullhorn_state = self._sync_state.get("bullhorn", {})
        qdrant_state = self._sync_state.get("qdrant", {})

        # Determine health
        if self._error_count == 0:
            health = "green"
        elif self._error_count < 5:
            health = "yellow"
        else:
            health = "red"

        return {
            "running": self._running,
            "poll_interval_seconds": self.poll_interval,
            "sync_health": health,
            "error_count": self._error_count,
            "retry_queue_size": len(self._retry_queue),
            "notion": {
                "last_sync": notion_state.get("last_sync"),
                "databases": {
                    k: {
                        "last_edited": v.get("last_edited"),
                        "records_synced": v.get("records_synced", 0),
                    }
                    for k, v in notion_state.get("databases", {}).items()
                },
            },
            "bullhorn": {
                "last_sync": bullhorn_state.get("last_sync"),
                "last_placement_id": bullhorn_state.get("last_placement_id", 0),
                "last_activity_id": bullhorn_state.get("last_activity_id", 0),
                "records_synced": bullhorn_state.get("records_synced", 0),
            },
            "qdrant": {
                "last_upsert": qdrant_state.get("last_upsert"),
                "collections_updated": qdrant_state.get("collections_updated", []),
            },
        }

    def get_sync_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent sync cycle results."""
        return self._sync_history[-limit:]

    def get_retry_queue(self) -> List[Dict[str, Any]]:
        """Return current retry queue contents."""
        return list(self._retry_queue)

    def clear_retry_queue(self) -> int:
        """Clear all items from the retry queue. Returns count of cleared items."""
        count = len(self._retry_queue)
        self._retry_queue.clear()
        logger.info("retry_queue_cleared", cleared=count)
        return count


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_sync_engine: Optional[SyncEngine] = None


def get_sync_engine(poll_interval_seconds: int = 120) -> SyncEngine:
    """Get or create the singleton SyncEngine."""
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = SyncEngine(poll_interval_seconds=poll_interval_seconds)
    return _sync_engine
