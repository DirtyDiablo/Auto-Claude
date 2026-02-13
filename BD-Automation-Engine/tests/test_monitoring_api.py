"""Tests for Phase 30A - Monitoring API Router (health, readiness, liveness, etc.)."""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from Engine8_Knowledge.api_routers.monitoring_api import router


@pytest.fixture
def client():
    """Create a FastAPI TestClient with the monitoring router mounted."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestRouterSetup:
    """Tests for router configuration."""

    def test_router_has_monitoring_tag(self):
        """Router should be tagged with 'monitoring'."""
        assert "monitoring" in router.tags

    def test_router_has_expected_routes(self):
        """Router should register all 7 monitoring endpoints."""
        paths = [route.path for route in router.routes]
        expected = [
            "/monitoring/health",
            "/monitoring/ready",
            "/monitoring/live",
            "/monitoring/resource-usage",
            "/monitoring/dashboard-urls",
            "/monitoring/alerts",
            "/monitoring/status",
        ]
        for ep in expected:
            assert ep in paths, f"Missing route: {ep}"


class TestHealthEndpoint:
    """Tests for /monitoring/health endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/monitoring/health")
        assert response.status_code == 200

    def test_health_returns_status(self, client):
        """Health response should contain status field."""
        response = client.get("/monitoring/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded")

    def test_health_returns_subsystems(self, client):
        """Health response should contain subsystems dict."""
        response = client.get("/monitoring/health")
        data = response.json()
        assert "subsystems" in data
        assert isinstance(data["subsystems"], dict)

    def test_health_returns_uptime(self, client):
        """Health response should contain uptime_seconds."""
        response = client.get("/monitoring/health")
        data = response.json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)


class TestReadinessEndpoint:
    """Tests for /monitoring/ready endpoint."""

    def test_ready_returns_200(self, client):
        """Readiness probe should return 200 OK."""
        response = client.get("/monitoring/ready")
        assert response.status_code == 200

    def test_ready_returns_true(self, client):
        """Readiness response should have ready=True."""
        data = client.get("/monitoring/ready").json()
        assert data["ready"] is True

    def test_ready_returns_timestamp(self, client):
        """Readiness response should have a timestamp."""
        data = client.get("/monitoring/ready").json()
        assert "timestamp" in data
        assert isinstance(data["timestamp"], float)


class TestLivenessEndpoint:
    """Tests for /monitoring/live endpoint."""

    def test_live_returns_200(self, client):
        """Liveness probe should return 200 OK."""
        response = client.get("/monitoring/live")
        assert response.status_code == 200

    def test_live_returns_alive(self, client):
        """Liveness response should have alive=True."""
        data = client.get("/monitoring/live").json()
        assert data["alive"] is True

    def test_live_returns_uptime(self, client):
        """Liveness response should have uptime_seconds."""
        data = client.get("/monitoring/live").json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0


class TestResourceUsageEndpoint:
    """Tests for /monitoring/resource-usage endpoint."""

    def test_resource_usage_returns_200(self, client):
        """Resource usage endpoint should return 200 OK."""
        response = client.get("/monitoring/resource-usage")
        assert response.status_code == 200

    def test_resource_usage_has_platform(self, client):
        """Resource usage response should include the platform name."""
        data = client.get("/monitoring/resource-usage").json()
        assert "platform" in data
        assert isinstance(data["platform"], str)

    def test_resource_usage_has_cpu_memory(self, client):
        """Resource usage should report cpu_percent and memory_rss_mb (or fallback)."""
        data = client.get("/monitoring/resource-usage").json()
        assert "cpu_percent" in data
        assert "memory_rss_mb" in data


class TestDashboardUrlsEndpoint:
    """Tests for /monitoring/dashboard-urls endpoint."""

    def test_dashboard_urls_returns_200(self, client):
        """Dashboard URLs endpoint should return 200 OK."""
        response = client.get("/monitoring/dashboard-urls")
        assert response.status_code == 200

    def test_dashboard_urls_has_dashboards(self, client):
        """Response should contain a dashboards dict with known keys."""
        data = client.get("/monitoring/dashboard-urls").json()
        assert "dashboards" in data
        dashboards = data["dashboards"]
        expected_keys = ["api_health", "search_performance", "agent_activity", "campaign_metrics", "infrastructure"]
        for key in expected_keys:
            assert key in dashboards, f"Missing dashboard: {key}"

    def test_dashboard_urls_are_strings(self, client):
        """Each dashboard URL should be a string starting with http."""
        data = client.get("/monitoring/dashboard-urls").json()
        for name, url in data["dashboards"].items():
            assert isinstance(url, str)
            assert url.startswith("http"), f"Dashboard URL for {name} does not start with http"


class TestAlertsEndpoint:
    """Tests for /monitoring/alerts endpoint."""

    def test_alerts_returns_200(self, client):
        """Alerts endpoint should return 200 OK."""
        response = client.get("/monitoring/alerts")
        assert response.status_code == 200

    def test_alerts_has_expected_fields(self, client):
        """Alerts response should have alerts list, total count, and status."""
        data = client.get("/monitoring/alerts").json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)
        assert "total" in data
        assert data["total"] == 0
        assert "status" in data
        assert data["status"] == "all_clear"


class TestStatusEndpoint:
    """Tests for /monitoring/status endpoint."""

    def test_status_returns_200(self, client):
        """Status endpoint should return 200 OK."""
        response = client.get("/monitoring/status")
        assert response.status_code == 200

    def test_status_has_platform_name(self, client):
        """Status response should identify the platform."""
        data = client.get("/monitoring/status").json()
        assert data["platform"] == "PTS BD Intelligence"

    def test_status_has_operational_status(self, client):
        """Status response should have status=operational."""
        data = client.get("/monitoring/status").json()
        assert data["status"] == "operational"

    def test_status_has_subsystems_list(self, client):
        """Status response should list subsystems."""
        data = client.get("/monitoring/status").json()
        assert "subsystems" in data
        assert isinstance(data["subsystems"], list)
        assert "hub_api" in data["subsystems"]
        assert "qdrant" in data["subsystems"]

    def test_status_has_uptime(self, client):
        """Status response should have uptime_seconds."""
        data = client.get("/monitoring/status").json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)

    def test_status_has_metrics_available(self, client):
        """Status response should have metrics_available field."""
        data = client.get("/monitoring/status").json()
        assert "metrics_available" in data
        assert isinstance(data["metrics_available"], bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
