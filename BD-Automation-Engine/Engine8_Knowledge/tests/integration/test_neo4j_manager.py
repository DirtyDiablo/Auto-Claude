"""
Phase 21A — Neo4j Manager Tests

Tests connection management, health checks, query execution, retry logic.
Uses mocking — does not require running Neo4j instance.
"""

from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class TestNeo4jManagerInit:
    """Test Neo4jManager initialization and configuration."""

    def test_default_config(self):
        with patch.dict("os.environ", {}, clear=False):
            from Engine8_Knowledge.graph.neo4j_manager import Neo4jManager
            mgr = Neo4jManager()
            assert mgr._uri == "bolt://localhost:7687"
            assert mgr._user == "neo4j"
            assert mgr._password == "pts_bd_2026"
            assert mgr._database == "neo4j"
            assert mgr._max_pool == 50

    def test_custom_config(self):
        from Engine8_Knowledge.graph.neo4j_manager import Neo4jManager
        mgr = Neo4jManager(
            uri="bolt://custom:7688",
            user="admin",
            password="secret",
            database="bd",
            max_pool_size=10,
        )
        assert mgr._uri == "bolt://custom:7688"
        assert mgr._user == "admin"
        assert mgr._database == "bd"
        assert mgr._max_pool == 10

    def test_env_config(self):
        with patch.dict("os.environ", {
            "NEO4J_URI": "bolt://envhost:7687",
            "NEO4J_USER": "envuser",
            "NEO4J_PASSWORD": "envpass",
        }):
            # Need to reimport to pick up env
            import importlib
            import Engine8_Knowledge.graph.neo4j_manager as mod
            importlib.reload(mod)
            mgr = mod.Neo4jManager()
            assert mgr._uri == "bolt://envhost:7687"

    def test_driver_initially_none(self):
        from Engine8_Knowledge.graph.neo4j_manager import Neo4jManager
        mgr = Neo4jManager()
        assert mgr._driver is None

    def test_context_manager(self):
        from Engine8_Knowledge.graph.neo4j_manager import Neo4jManager
        mgr = Neo4jManager()
        with patch.object(mgr, "connect") as mock_connect, \
             patch.object(mgr, "close") as mock_close:
            with mgr:
                mock_connect.assert_called_once()
            mock_close.assert_called_once()

    def test_close_sets_driver_none(self):
        from Engine8_Knowledge.graph.neo4j_manager import Neo4jManager
        mgr = Neo4jManager()
        mock_driver = MagicMock()
        mgr._driver = mock_driver
        mgr.close()
        assert mgr._driver is None
        mock_driver.close.assert_called_once()


class TestNeo4jManagerHealth:
    """Test health check functionality."""

    def test_health_check_healthy(self):
        from Engine8_Knowledge.graph.neo4j_manager import Neo4jManager
        mgr = Neo4jManager()
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_record = {"n": 1}
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_driver.session.return_value = mock_session
        mgr._driver = mock_driver

        result = mgr.health_check()
        assert result["status"] == "healthy"

    def test_health_check_unhealthy(self):
        from Engine8_Knowledge.graph.neo4j_manager import Neo4jManager
        mgr = Neo4jManager()
        mock_driver = MagicMock()
        mock_driver.session.side_effect = Exception("Connection refused")
        mgr._driver = mock_driver

        result = mgr.health_check()
        assert result["status"] == "unhealthy"
        assert "Connection refused" in result["error"]


class TestNeo4jManagerQueries:
    """Test query execution methods."""

    def _setup_mgr_with_mock(self):
        from Engine8_Knowledge.graph.neo4j_manager import Neo4jManager
        mgr = Neo4jManager()
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_driver.session.return_value = mock_session
        mgr._driver = mock_driver
        return mgr, mock_session

    def test_run_query_returns_list(self):
        mgr, session = self._setup_mgr_with_mock()
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([{"name": "Alice"}, {"name": "Bob"}]))
        session.run.return_value = mock_result

        results = mgr.run_query("MATCH (n) RETURN n.name AS name")
        assert len(results) == 2
        assert results[0]["name"] == "Alice"

    def test_run_single_returns_dict(self):
        mgr, session = self._setup_mgr_with_mock()
        mock_result = MagicMock()
        mock_record = {"count": 42}
        mock_result.single.return_value = mock_record
        session.run.return_value = mock_result

        result = mgr.run_single("MATCH (n) RETURN count(n) AS count")
        assert result["count"] == 42

    def test_run_single_returns_none(self):
        mgr, session = self._setup_mgr_with_mock()
        mock_result = MagicMock()
        mock_result.single.return_value = None
        session.run.return_value = mock_result

        result = mgr.run_single("MATCH (n) RETURN n LIMIT 1")
        assert result is None

    def test_write_query_returns_counters(self):
        mgr, session = self._setup_mgr_with_mock()
        mock_result = MagicMock()
        mock_summary = MagicMock()
        mock_counters = MagicMock()
        mock_counters.nodes_created = 5
        mock_counters.nodes_deleted = 0
        mock_counters.relationships_created = 3
        mock_counters.relationships_deleted = 0
        mock_counters.properties_set = 15
        mock_summary.counters = mock_counters
        mock_result.consume.return_value = mock_summary
        session.run.return_value = mock_result

        result = mgr.write_query("CREATE (n:Person {name: 'Alice'})")
        assert result["nodes_created"] == 5
        assert result["relationships_created"] == 3

    def test_get_node_count(self):
        mgr, session = self._setup_mgr_with_mock()
        mock_result = MagicMock()
        mock_result.single.return_value = {"c": 100}
        session.run.return_value = mock_result

        count = mgr.get_node_count("Person")
        assert count == 100

    def test_get_relationship_count(self):
        mgr, session = self._setup_mgr_with_mock()
        mock_result = MagicMock()
        mock_result.single.return_value = {"c": 50}
        session.run.return_value = mock_result

        count = mgr.get_relationship_count("WORKS_AT")
        assert count == 50


class TestNeo4jManagerBatch:
    """Test batch operations."""

    def test_run_batch_small(self):
        from Engine8_Knowledge.graph.neo4j_manager import Neo4jManager
        mgr = Neo4jManager()

        with patch.object(mgr, "write_query") as mock_write:
            mock_write.return_value = {"nodes_created": 3, "properties_set": 9, "relationships_created": 0, "nodes_deleted": 0, "relationships_deleted": 0}
            result = mgr.run_batch("UNWIND $batch AS row CREATE (n:Test)", [{"a": 1}, {"a": 2}, {"a": 3}])
            assert result["total_records"] == 3
            assert result["batches"] == 1

    def test_run_batch_large(self):
        from Engine8_Knowledge.graph.neo4j_manager import Neo4jManager
        mgr = Neo4jManager()

        with patch.object(mgr, "write_query") as mock_write:
            mock_write.return_value = {"nodes_created": 500, "properties_set": 0, "relationships_created": 0, "nodes_deleted": 0, "relationships_deleted": 0}
            data = [{"i": i} for i in range(1200)]
            result = mgr.run_batch("UNWIND $batch AS row CREATE (n:Test)", data, batch_size=500)
            assert result["total_records"] == 1200
            assert result["batches"] == 3
            assert mock_write.call_count == 3


class TestNeo4jSingleton:
    """Test singleton pattern."""

    def test_get_neo4j_manager_returns_instance(self):
        import Engine8_Knowledge.graph.neo4j_manager as mod
        mod._instance = None  # reset
        mgr = mod.get_neo4j_manager()
        assert mgr is not None
        mgr2 = mod.get_neo4j_manager()
        assert mgr is mgr2
        mod._instance = None  # cleanup
