"""
CHECKPOINTER CONFIGURATION
==========================
SQLite-based persistence for LangGraph workflow state.

Provides durable checkpointing so workflows can:
- Survive Python restarts
- Resume from human-in-the-loop interrupts
- Track execution history
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import sqlite3

try:
    # LangGraph >= 0.2 (newer API)
    from langgraph_checkpoint_sqlite import SqliteSaver
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    try:
        # LangGraph < 0.2 (older API)
        from langgraph.checkpoint.sqlite import SqliteSaver
        from langgraph.checkpoint.memory import MemorySaver
    except ImportError:
        # Fallback - provide stubs
        SqliteSaver = None
        MemorySaver = None

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "langgraph_checkpoints.db"


def get_checkpointer(db_path: Optional[str] = None):
    """
    Get a SQLite-based checkpointer for production use.

    Args:
        db_path: Path to SQLite database. Defaults to data/langgraph_checkpoints.db

    Returns:
        SqliteSaver instance configured for the database
    """
    if SqliteSaver is None:
        raise ImportError(
            "SqliteSaver not available. Install with: pip install langgraph-checkpoint-sqlite"
        )

    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)

    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Create connection and checkpointer
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn)


def get_memory_checkpointer():
    """
    Get an in-memory checkpointer for testing.

    Returns:
        MemorySaver instance (state lost on restart)
    """
    if MemorySaver is None:
        raise ImportError(
            "MemorySaver not available. Install with: pip install langgraph"
        )
    return MemorySaver()


class CheckpointManager:
    """
    Manager for listing and managing workflow checkpoints.

    Provides utilities to:
    - List all threads/workflows
    - Get thread history
    - Delete old checkpoints
    - Export checkpoint data
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize checkpoint manager.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or str(DEFAULT_DB_PATH)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure metadata tables exist."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            # Create workflow metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_metadata (
                    thread_id TEXT PRIMARY KEY,
                    workflow_type TEXT,
                    workflow_id TEXT,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    completed_at TEXT,
                    error_message TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def register_workflow(
        self,
        thread_id: str,
        workflow_type: str,
        workflow_id: str,
        status: str = "pending"
    ) -> None:
        """
        Register a new workflow in metadata.

        Args:
            thread_id: LangGraph thread ID
            workflow_type: Type of workflow (bd_proposal, contact_outreach, etc.)
            workflow_id: User-friendly workflow identifier
            status: Initial status
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT OR REPLACE INTO workflow_metadata
                (thread_id, workflow_type, workflow_id, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (thread_id, workflow_type, workflow_id, status, now, now))
            conn.commit()
        finally:
            conn.close()

    def update_workflow_status(
        self,
        thread_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update workflow status in metadata.

        Args:
            thread_id: LangGraph thread ID
            status: New status
            error_message: Error message if failed
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            completed_at = now if status in ("completed", "failed", "aborted") else None

            cursor.execute("""
                UPDATE workflow_metadata
                SET status = ?, updated_at = ?, completed_at = ?, error_message = ?
                WHERE thread_id = ?
            """, (status, now, completed_at, error_message, thread_id))
            conn.commit()
        finally:
            conn.close()

    def list_workflows(
        self,
        workflow_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List workflows from metadata.

        Args:
            workflow_type: Filter by workflow type
            status: Filter by status
            limit: Maximum number of results

        Returns:
            List of workflow metadata dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM workflow_metadata WHERE 1=1"
            params = []

            if workflow_type:
                query += " AND workflow_type = ?"
                params.append(workflow_type)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]
        finally:
            conn.close()

    def get_workflow(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow metadata by thread ID.

        Args:
            thread_id: LangGraph thread ID

        Returns:
            Workflow metadata dictionary or None
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM workflow_metadata WHERE thread_id = ?",
                (thread_id,)
            )
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
        finally:
            conn.close()

    def get_pending_reviews(self) -> List[Dict[str, Any]]:
        """
        Get all workflows awaiting human review.

        Returns:
            List of workflows with status 'awaiting_human_review'
        """
        return self.list_workflows(status="awaiting_human_review")

    def delete_workflow(self, thread_id: str) -> bool:
        """
        Delete a workflow from metadata.

        Note: This does not delete the actual checkpoints from LangGraph tables.

        Args:
            thread_id: LangGraph thread ID

        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM workflow_metadata WHERE thread_id = ?",
                (thread_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def cleanup_old_workflows(self, days_old: int = 30) -> int:
        """
        Delete workflows older than specified days.

        Args:
            days_old: Delete workflows older than this many days

        Returns:
            Number of workflows deleted
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cutoff = datetime.now().isoformat()
            cursor.execute("""
                DELETE FROM workflow_metadata
                WHERE datetime(updated_at) < datetime(?, '-' || ? || ' days')
                AND status IN ('completed', 'failed', 'aborted')
            """, (cutoff, days_old))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about workflows.

        Returns:
            Dictionary with workflow statistics
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Count by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM workflow_metadata
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())

            # Count by type
            cursor.execute("""
                SELECT workflow_type, COUNT(*) as count
                FROM workflow_metadata
                GROUP BY workflow_type
            """)
            type_counts = dict(cursor.fetchall())

            # Total count
            cursor.execute("SELECT COUNT(*) FROM workflow_metadata")
            total = cursor.fetchone()[0]

            return {
                'total': total,
                'by_status': status_counts,
                'by_type': type_counts,
            }
        finally:
            conn.close()


# Export
__all__ = [
    'get_checkpointer',
    'get_memory_checkpointer',
    'CheckpointManager',
    'DEFAULT_DB_PATH',
]
