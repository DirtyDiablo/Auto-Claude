"""
Phase 21A — Neo4j Connection Manager

Connection pooling, health checks, retry logic, and transaction support
for the BD Intelligence Knowledge Graph.

Config from environment:
  NEO4J_URI (default: bolt://localhost:7687)
  NEO4J_USER (default: neo4j)
  NEO4J_PASSWORD (required)
"""

import os
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import (
        ServiceUnavailable,
        SessionExpired,
        TransientError,
    )

    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
    )

    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
NEO4J_MAX_POOL = int(os.getenv("NEO4J_MAX_POOL", "50"))


# ---------------------------------------------------------------------------
# Retry decorator
# ---------------------------------------------------------------------------

if TENACITY_AVAILABLE and NEO4J_AVAILABLE:
    _retry_on_transient = retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (ServiceUnavailable, SessionExpired, TransientError)
        ),
        reraise=True,
    )
else:

    def _retry_on_transient(fn):  # type: ignore[misc]
        return fn


# ---------------------------------------------------------------------------
# Neo4jManager
# ---------------------------------------------------------------------------


class Neo4jManager:
    """Manages Neo4j driver lifecycle, connection pooling, and query execution."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        max_pool_size: int = NEO4J_MAX_POOL,
    ) -> None:
        self._uri = uri or NEO4J_URI
        self._user = user or NEO4J_USER
        self._password = password or NEO4J_PASSWORD
        self._database = database or NEO4J_DATABASE
        self._max_pool = max_pool_size
        self._driver: Optional[Any] = None

        if not NEO4J_AVAILABLE:
            logger.warning("neo4j_driver_not_installed", hint="pip install neo4j")

    # -- Lifecycle --

    def connect(self) -> None:
        """Create the Neo4j driver with connection pooling."""
        if not NEO4J_AVAILABLE:
            raise RuntimeError("neo4j package not installed — pip install neo4j")
        if self._driver is not None:
            return

        self._driver = GraphDatabase.driver(
            self._uri,
            auth=(self._user, self._password),
            max_connection_pool_size=self._max_pool,
            connection_timeout=10,
            max_transaction_retry_time=30,
        )
        logger.info("neo4j_connected", uri=self._uri, pool_size=self._max_pool)

    def close(self) -> None:
        """Close the driver and release all connections."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("neo4j_disconnected")

    @property
    def driver(self) -> Any:
        if self._driver is None:
            self.connect()
        return self._driver

    # -- Context manager --

    def __enter__(self) -> "Neo4jManager":
        self.connect()
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # -- Health --

    def health_check(self) -> dict:
        """Check Neo4j connectivity."""
        try:
            with self.driver.session(database=self._database) as session:
                result = session.run("RETURN 1 AS n")
                record = result.single()
                if record and record["n"] == 1:
                    return {
                        "status": "healthy",
                        "uri": self._uri,
                        "database": self._database,
                    }
            return {"status": "unhealthy", "error": "unexpected result"}
        except Exception as e:
            return {"status": "unhealthy", "uri": self._uri, "error": str(e)[:200]}

    def is_connected(self) -> bool:
        return self.health_check().get("status") == "healthy"

    # -- Query execution --

    @_retry_on_transient
    def run_query(
        self,
        cypher: str,
        parameters: Optional[dict] = None,
        database: Optional[str] = None,
    ) -> list[dict]:
        """Execute a Cypher query and return results as list of dicts."""
        db = database or self._database
        with self.driver.session(database=db) as session:
            result = session.run(cypher, parameters or {})
            return [dict(record) for record in result]

    @_retry_on_transient
    def run_single(
        self, cypher: str, parameters: Optional[dict] = None
    ) -> Optional[dict]:
        """Execute a query and return a single result."""
        with self.driver.session(database=self._database) as session:
            result = session.run(cypher, parameters or {})
            record = result.single()
            return dict(record) if record else None

    @_retry_on_transient
    def write_query(self, cypher: str, parameters: Optional[dict] = None) -> dict:
        """Execute a write query and return summary counters."""
        with self.driver.session(database=self._database) as session:
            result = session.run(cypher, parameters or {})
            summary = result.consume()
            counters = summary.counters
            return {
                "nodes_created": counters.nodes_created,
                "nodes_deleted": counters.nodes_deleted,
                "relationships_created": counters.relationships_created,
                "relationships_deleted": counters.relationships_deleted,
                "properties_set": counters.properties_set,
            }

    # -- Transaction support --

    @_retry_on_transient
    def read_transaction(self, work_fn: Any, **kwargs: Any) -> Any:
        """Execute a function within a read transaction."""
        with self.driver.session(database=self._database) as session:
            return session.execute_read(work_fn, **kwargs)

    @_retry_on_transient
    def write_transaction(self, work_fn: Any, **kwargs: Any) -> Any:
        """Execute a function within a write transaction."""
        with self.driver.session(database=self._database) as session:
            return session.execute_write(work_fn, **kwargs)

    # -- Batch operations --

    def run_batch(
        self, cypher: str, batch_data: list[dict], batch_size: int = 500
    ) -> dict:
        """Execute a parameterized query in batches.

        Uses UNWIND for efficient batch processing:
          UNWIND $batch AS row
          MERGE (n:Person {email: row.email})
          SET n.name = row.name, ...
        """
        total_created = 0
        total_props = 0
        total_rels = 0

        for i in range(0, len(batch_data), batch_size):
            chunk = batch_data[i : i + batch_size]
            result = self.write_query(cypher, {"batch": chunk})
            total_created += result.get("nodes_created", 0)
            total_props += result.get("properties_set", 0)
            total_rels += result.get("relationships_created", 0)

        return {
            "batches": (len(batch_data) + batch_size - 1) // batch_size,
            "total_records": len(batch_data),
            "nodes_created": total_created,
            "properties_set": total_props,
            "relationships_created": total_rels,
        }

    # -- Utility --

    def get_node_count(self, label: Optional[str] = None) -> int:
        """Count nodes, optionally filtered by label."""
        if label:
            result = self.run_single(f"MATCH (n:`{label}`) RETURN count(n) AS c")
        else:
            result = self.run_single("MATCH (n) RETURN count(n) AS c")
        return result["c"] if result else 0

    def get_relationship_count(self, rel_type: Optional[str] = None) -> int:
        """Count relationships, optionally filtered by type."""
        if rel_type:
            result = self.run_single(
                f"MATCH ()-[r:`{rel_type}`]->() RETURN count(r) AS c"
            )
        else:
            result = self.run_single("MATCH ()-[r]->() RETURN count(r) AS c")
        return result["c"] if result else 0

    def clear_database(self) -> dict:
        """Delete all nodes and relationships. USE WITH CAUTION."""
        return self.write_query("MATCH (n) DETACH DELETE n")


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: Optional[Neo4jManager] = None


def get_neo4j_manager() -> Neo4jManager:
    global _instance
    if _instance is None:
        _instance = Neo4jManager()
    return _instance
