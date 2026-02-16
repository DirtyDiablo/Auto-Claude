"""
Phase 23A — LangGraph Checkpoint Store

SQLite-based persistent checkpoint store for LangGraph workflow state.
Uses langgraph-checkpoint-sqlite for async SQLite checkpointing with
thread-based isolation, configurable retention, and export/import support.
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ThreadInfo:
    thread_id: str
    workflow_name: str
    status: str  # running, completed, failed, interrupted, cancelled
    created_at: str
    updated_at: str
    step_count: int
    current_node: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckpointSnapshot:
    thread_id: str
    step: int
    node_name: str
    timestamp: str
    state: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# CheckpointStore
# ---------------------------------------------------------------------------


class CheckpointStore:
    """Production checkpoint store using SQLite for persistent LangGraph state."""

    def __init__(self, db_path: str = "data/checkpoints.db", max_per_thread: int = 50):
        self.db_path = db_path
        self.max_per_thread = max_per_thread
        self._checkpointer = None
        self._db = None

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "checkpoint_store.init", db_path=db_path, max_per_thread=max_per_thread
        )

    # ------------------------------------------------------------------
    # LangGraph checkpointer
    # ------------------------------------------------------------------

    async def get_checkpointer(self):
        """Return an AsyncSqliteSaver for LangGraph graph compilation."""
        if self._checkpointer is None:
            try:
                from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

                self._checkpointer = AsyncSqliteSaver.from_conn_string(self.db_path)
                await self._checkpointer.setup()
                logger.info("checkpoint_store.checkpointer_ready", db=self.db_path)
            except ImportError:
                logger.warning(
                    "checkpoint_store.langgraph_sqlite_not_available, using in-memory fallback"
                )
                self._checkpointer = InMemoryCheckpointer()
        return self._checkpointer

    async def _get_db(self):
        """Get or create the metadata SQLite connection."""
        if self._db is None:
            try:
                import aiosqlite

                self._db = await aiosqlite.connect(
                    self.db_path.replace(".db", "_meta.db")
                )
                await self._init_tables()
            except ImportError:
                logger.warning("aiosqlite not available, using dict fallback")
                self._db = DictMetaStore()
        return self._db

    async def _init_tables(self):
        """Create metadata tables if they don't exist."""
        db = self._db
        await db.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                thread_id TEXT PRIMARY KEY,
                workflow_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'running',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                step_count INTEGER DEFAULT 0,
                current_node TEXT,
                metadata TEXT DEFAULT '{}'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS checkpoint_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                step INTEGER NOT NULL,
                node_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                state TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (thread_id) REFERENCES threads(thread_id)
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_thread ON checkpoint_snapshots(thread_id)
        """)
        await db.commit()

    # ------------------------------------------------------------------
    # Thread management
    # ------------------------------------------------------------------

    async def create_thread(
        self,
        workflow_name: str,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Create a new workflow thread."""
        tid = thread_id or f"thread_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        db = await self._get_db()

        if isinstance(db, DictMetaStore):
            db.threads[tid] = ThreadInfo(
                thread_id=tid,
                workflow_name=workflow_name,
                status="running",
                created_at=now,
                updated_at=now,
                step_count=0,
                metadata=metadata or {},
            )
        else:
            await db.execute(
                "INSERT INTO threads (thread_id, workflow_name, status, created_at, updated_at, metadata) VALUES (?,?,?,?,?,?)",
                (tid, workflow_name, "running", now, now, json.dumps(metadata or {})),
            )
            await db.commit()

        logger.info(
            "checkpoint_store.thread_created", thread_id=tid, workflow=workflow_name
        )
        return tid

    async def update_thread_status(
        self,
        thread_id: str,
        status: str,
        current_node: Optional[str] = None,
        step_count: Optional[int] = None,
    ) -> None:
        """Update thread status and optional fields."""
        now = datetime.utcnow().isoformat()
        db = await self._get_db()

        if isinstance(db, DictMetaStore):
            t = db.threads.get(thread_id)
            if t:
                t.status = status
                t.updated_at = now
                if current_node is not None:
                    t.current_node = current_node
                if step_count is not None:
                    t.step_count = step_count
        else:
            parts = ["status=?", "updated_at=?"]
            vals: list = [status, now]
            if current_node is not None:
                parts.append("current_node=?")
                vals.append(current_node)
            if step_count is not None:
                parts.append("step_count=?")
                vals.append(step_count)
            vals.append(thread_id)
            await db.execute(
                f"UPDATE threads SET {', '.join(parts)} WHERE thread_id=?", vals
            )
            await db.commit()

    async def list_threads(
        self,
        workflow_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ThreadInfo]:
        """List workflow threads with optional filtering."""
        db = await self._get_db()

        if isinstance(db, DictMetaStore):
            results = list(db.threads.values())
            if workflow_name:
                results = [t for t in results if t.workflow_name == workflow_name]
            if status:
                results = [t for t in results if t.status == status]
            return sorted(results, key=lambda t: t.updated_at, reverse=True)[:limit]

        query = "SELECT * FROM threads WHERE 1=1"
        params: list = []
        if workflow_name:
            query += " AND workflow_name=?"
            params.append(workflow_name)
        if status:
            query += " AND status=?"
            params.append(status)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [
            ThreadInfo(
                thread_id=r[0],
                workflow_name=r[1],
                status=r[2],
                created_at=r[3],
                updated_at=r[4],
                step_count=r[5],
                current_node=r[6],
                metadata=json.loads(r[7] or "{}"),
            )
            for r in rows
        ]

    async def get_thread_history(self, thread_id: str) -> List[CheckpointSnapshot]:
        """Get all checkpoint snapshots for a thread."""
        db = await self._get_db()

        if isinstance(db, DictMetaStore):
            return db.snapshots.get(thread_id, [])

        cursor = await db.execute(
            "SELECT thread_id, step, node_name, timestamp, state, metadata FROM checkpoint_snapshots WHERE thread_id=? ORDER BY step",
            (thread_id,),
        )
        rows = await cursor.fetchall()
        return [
            CheckpointSnapshot(
                thread_id=r[0],
                step=r[1],
                node_name=r[2],
                timestamp=r[3],
                state=json.loads(r[4]),
                metadata=json.loads(r[5] or "{}"),
            )
            for r in rows
        ]

    async def save_snapshot(
        self,
        thread_id: str,
        step: int,
        node_name: str,
        state: Dict[str, Any],
        metadata: Optional[Dict] = None,
    ) -> None:
        """Save a checkpoint snapshot and enforce retention limit."""
        now = datetime.utcnow().isoformat()
        db = await self._get_db()

        snap = CheckpointSnapshot(
            thread_id=thread_id,
            step=step,
            node_name=node_name,
            timestamp=now,
            state=state,
            metadata=metadata or {},
        )

        if isinstance(db, DictMetaStore):
            db.snapshots.setdefault(thread_id, []).append(snap)
            # Enforce retention
            if len(db.snapshots[thread_id]) > self.max_per_thread:
                db.snapshots[thread_id] = db.snapshots[thread_id][
                    -self.max_per_thread :
                ]
        else:
            await db.execute(
                "INSERT INTO checkpoint_snapshots (thread_id, step, node_name, timestamp, state, metadata) VALUES (?,?,?,?,?,?)",
                (
                    thread_id,
                    step,
                    node_name,
                    now,
                    json.dumps(state),
                    json.dumps(metadata or {}),
                ),
            )
            # Enforce retention
            cursor = await db.execute(
                "SELECT COUNT(*) FROM checkpoint_snapshots WHERE thread_id=?",
                (thread_id,),
            )
            count = (await cursor.fetchone())[0]
            if count > self.max_per_thread:
                excess = count - self.max_per_thread
                await db.execute(
                    "DELETE FROM checkpoint_snapshots WHERE id IN (SELECT id FROM checkpoint_snapshots WHERE thread_id=? ORDER BY step LIMIT ?)",
                    (thread_id, excess),
                )
            await db.commit()

        # Update thread
        await self.update_thread_status(
            thread_id, "running", current_node=node_name, step_count=step
        )

    async def get_checkpoint_at(
        self, thread_id: str, step: int
    ) -> Optional[CheckpointSnapshot]:
        """Get the state at a specific checkpoint step."""
        db = await self._get_db()

        if isinstance(db, DictMetaStore):
            for s in db.snapshots.get(thread_id, []):
                if s.step == step:
                    return s
            return None

        cursor = await db.execute(
            "SELECT thread_id, step, node_name, timestamp, state, metadata FROM checkpoint_snapshots WHERE thread_id=? AND step=?",
            (thread_id, step),
        )
        row = await cursor.fetchone()
        if row:
            return CheckpointSnapshot(
                thread_id=row[0],
                step=row[1],
                node_name=row[2],
                timestamp=row[3],
                state=json.loads(row[4]),
                metadata=json.loads(row[5] or "{}"),
            )
        return None

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread and all its snapshots."""
        db = await self._get_db()

        if isinstance(db, DictMetaStore):
            removed = db.threads.pop(thread_id, None) is not None
            db.snapshots.pop(thread_id, None)
            return removed

        await db.execute(
            "DELETE FROM checkpoint_snapshots WHERE thread_id=?", (thread_id,)
        )
        await db.execute("DELETE FROM threads WHERE thread_id=?", (thread_id,))
        await db.commit()
        logger.info("checkpoint_store.thread_deleted", thread_id=thread_id)
        return True

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    async def cleanup_old(self, days: int = 30) -> int:
        """Purge threads older than N days."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        db = await self._get_db()

        if isinstance(db, DictMetaStore):
            old = [t for t in db.threads.values() if t.updated_at < cutoff]
            for t in old:
                db.threads.pop(t.thread_id, None)
                db.snapshots.pop(t.thread_id, None)
            return len(old)

        cursor = await db.execute(
            "SELECT thread_id FROM threads WHERE updated_at < ?", (cutoff,)
        )
        old_threads = [r[0] for r in await cursor.fetchall()]
        for tid in old_threads:
            await db.execute(
                "DELETE FROM checkpoint_snapshots WHERE thread_id=?", (tid,)
            )
            await db.execute("DELETE FROM threads WHERE thread_id=?", (tid,))
        await db.commit()
        logger.info(
            "checkpoint_store.cleanup", removed=len(old_threads), cutoff_days=days
        )
        return len(old_threads)

    # ------------------------------------------------------------------
    # Export / Import
    # ------------------------------------------------------------------

    async def export_thread(self, thread_id: str) -> dict:
        """Export a thread and its snapshots for debugging."""
        threads = await self.list_threads()
        thread = next((t for t in threads if t.thread_id == thread_id), None)
        if not thread:
            return {"error": f"Thread {thread_id} not found"}

        snapshots = await self.get_thread_history(thread_id)
        return {
            "thread": asdict(thread),
            "snapshots": [asdict(s) for s in snapshots],
            "exported_at": datetime.utcnow().isoformat(),
        }

    async def import_thread(self, data: dict) -> str:
        """Import a previously exported thread. Returns new thread_id."""
        thread_data = data.get("thread", {})
        new_tid = f"imported_{uuid.uuid4().hex[:8]}"

        await self.create_thread(
            workflow_name=thread_data.get("workflow_name", "unknown"),
            thread_id=new_tid,
            metadata={"imported_from": thread_data.get("thread_id", "unknown")},
        )

        for snap in data.get("snapshots", []):
            await self.save_snapshot(
                thread_id=new_tid,
                step=snap["step"],
                node_name=snap["node_name"],
                state=snap["state"],
                metadata=snap.get("metadata", {}),
            )

        logger.info(
            "checkpoint_store.imported",
            new_thread_id=new_tid,
            original=thread_data.get("thread_id"),
        )
        return new_tid

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    async def get_stats(self) -> dict:
        """Return store statistics."""
        db = await self._get_db()

        if isinstance(db, DictMetaStore):
            total_threads = len(db.threads)
            total_snapshots = sum(len(v) for v in db.snapshots.values())
            by_status = {}
            for t in db.threads.values():
                by_status[t.status] = by_status.get(t.status, 0) + 1
            return {
                "total_threads": total_threads,
                "total_checkpoints": total_snapshots,
                "db_size_mb": 0,
                "by_status": by_status,
                "max_per_thread": self.max_per_thread,
            }

        cursor = await db.execute("SELECT COUNT(*) FROM threads")
        total_threads = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM checkpoint_snapshots")
        total_snapshots = (await cursor.fetchone())[0]
        cursor = await db.execute(
            "SELECT status, COUNT(*) FROM threads GROUP BY status"
        )
        by_status = {r[0]: r[1] for r in await cursor.fetchall()}

        db_size = 0
        meta_path = self.db_path.replace(".db", "_meta.db")
        if os.path.exists(meta_path):
            db_size = os.path.getsize(meta_path) / (1024 * 1024)
        if os.path.exists(self.db_path):
            db_size += os.path.getsize(self.db_path) / (1024 * 1024)

        return {
            "total_threads": total_threads,
            "total_checkpoints": total_snapshots,
            "db_size_mb": round(db_size, 2),
            "by_status": by_status,
            "max_per_thread": self.max_per_thread,
        }

    async def health_check(self) -> dict:
        """Health check for the checkpoint store."""
        try:
            stats = await self.get_stats()
            return {"status": "healthy", "stats": stats}
        except Exception as e:
            logger.error("checkpoint_store.health_check_failed", error=str(e))
            return {"status": "unhealthy", "error": str(e)}

    async def close(self):
        """Close database connections."""
        if self._db and not isinstance(self._db, DictMetaStore):
            await self._db.close()
            self._db = None
        self._checkpointer = None


# ---------------------------------------------------------------------------
# Fallback stores for when dependencies aren't installed
# ---------------------------------------------------------------------------


class DictMetaStore:
    """In-memory fallback when aiosqlite is not available."""

    def __init__(self):
        self.threads: Dict[str, ThreadInfo] = {}
        self.snapshots: Dict[str, List[CheckpointSnapshot]] = {}


class InMemoryCheckpointer:
    """In-memory fallback when langgraph-checkpoint-sqlite is not available."""

    def __init__(self):
        self.storage: Dict[str, Any] = {}

    async def setup(self):
        pass


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_checkpoint_store: Optional[CheckpointStore] = None


def get_checkpoint_store(db_path: str = "data/checkpoints.db") -> CheckpointStore:
    """Get or create the singleton CheckpointStore."""
    global _checkpoint_store
    if _checkpoint_store is None:
        _checkpoint_store = CheckpointStore(db_path=db_path)
    return _checkpoint_store
