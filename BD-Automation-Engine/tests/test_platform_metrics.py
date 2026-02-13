"""Tests for Phase 30A - Platform Metrics (Prometheus instrumentation)."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Engine8_Knowledge.monitoring.metrics import (
    MetricValue,
    PlatformMetrics,
    get_platform_metrics,
)


class TestMetricValueDataclass:
    """Tests for the MetricValue dataclass."""

    def test_metric_value_fields(self):
        """MetricValue should have name, value, labels, and metric_type fields."""
        mv = MetricValue(name="test_counter", value=42.0, labels={"env": "dev"}, metric_type="counter")
        assert mv.name == "test_counter"
        assert mv.value == 42.0
        assert mv.labels == {"env": "dev"}
        assert mv.metric_type == "counter"

    def test_metric_value_types(self):
        """MetricValue should accept counter, gauge, and histogram types."""
        for mtype in ("counter", "gauge", "histogram"):
            mv = MetricValue(name="m", value=1.0, labels={}, metric_type=mtype)
            assert mv.metric_type == mtype


class TestPlatformMetricsInit:
    """Tests for PlatformMetrics initialization."""

    @patch("Engine8_Knowledge.monitoring.metrics.PlatformMetrics._initialize")
    def test_init_creates_empty_stores(self, mock_init):
        """PlatformMetrics should initialize with empty counter, gauge, and histogram dicts."""
        pm = PlatformMetrics()
        assert pm._counters == {}
        assert pm._gauges == {}
        assert pm._histograms == {}

    @patch("Engine8_Knowledge.monitoring.metrics.PlatformMetrics._initialize")
    def test_init_prom_flag_default_false(self, mock_init):
        """PlatformMetrics should default _prom_available to False before _initialize runs."""
        pm = PlatformMetrics()
        assert pm._prom_available is False

    def test_init_calls_initialize(self):
        """PlatformMetrics __init__ should call _initialize."""
        with patch.object(PlatformMetrics, "_initialize") as mock_init:
            PlatformMetrics()
            mock_init.assert_called_once()


class TestIncrementCounter:
    """Tests for inc_counter method."""

    @patch("Engine8_Knowledge.monitoring.metrics.PlatformMetrics._initialize")
    def test_increment_counter_creates_entry(self, mock_init):
        """inc_counter should create a new counter entry if it does not exist."""
        pm = PlatformMetrics()
        pm.inc_counter("requests", {"method": "GET", "endpoint": "/api"})
        assert len(pm._counters) == 1

    @patch("Engine8_Knowledge.monitoring.metrics.PlatformMetrics._initialize")
    def test_increment_counter_adds_value(self, mock_init):
        """inc_counter should add the specified value to the counter."""
        pm = PlatformMetrics()
        pm.inc_counter("test_metric", {"label": "a"}, value=5.0)
        key = "test_metric:{'label': 'a'}"
        assert pm._counters[key]["value"] == 5.0

    @patch("Engine8_Knowledge.monitoring.metrics.PlatformMetrics._initialize")
    def test_increment_counter_accumulates(self, mock_init):
        """inc_counter called multiple times should accumulate the value."""
        pm = PlatformMetrics()
        labels = {"method": "POST"}
        pm.inc_counter("hits", labels, value=1.0)
        pm.inc_counter("hits", labels, value=3.0)
        key = f"hits:{labels}"
        assert pm._counters[key]["value"] == 4.0


class TestSetGauge:
    """Tests for set_gauge method."""

    @patch("Engine8_Knowledge.monitoring.metrics.PlatformMetrics._initialize")
    def test_set_gauge_stores_value(self, mock_init):
        """set_gauge should store the value in the _gauges dict."""
        pm = PlatformMetrics()
        pm.set_gauge("contacts_total", 500.0, {"source": "crm"})
        assert len(pm._gauges) == 1
        key = "contacts_total:{'source': 'crm'}"
        assert pm._gauges[key]["value"] == 500.0

    @patch("Engine8_Knowledge.monitoring.metrics.PlatformMetrics._initialize")
    def test_set_gauge_overwrites(self, mock_init):
        """set_gauge called again with the same key should overwrite the value."""
        pm = PlatformMetrics()
        labels = {"db": "qdrant"}
        pm.set_gauge("vectors", 100.0, labels)
        pm.set_gauge("vectors", 200.0, labels)
        key = f"vectors:{labels}"
        assert pm._gauges[key]["value"] == 200.0


class TestObserveHistogram:
    """Tests for observe_histogram method."""

    @patch("Engine8_Knowledge.monitoring.metrics.PlatformMetrics._initialize")
    def test_observe_histogram_appends(self, mock_init):
        """observe_histogram should append values to the histogram list."""
        pm = PlatformMetrics()
        labels = {"method": "GET", "endpoint": "/search"}
        pm.observe_histogram("request_duration", 0.15, labels)
        pm.observe_histogram("request_duration", 0.25, labels)
        key = f"request_duration:{labels}"
        assert pm._histograms[key] == [0.15, 0.25]

    @patch("Engine8_Knowledge.monitoring.metrics.PlatformMetrics._initialize")
    def test_observe_histogram_creates_list(self, mock_init):
        """observe_histogram should create a new list for a new metric name."""
        pm = PlatformMetrics()
        pm.observe_histogram("db_query", 0.05)
        key = "db_query:None"
        assert len(pm._histograms[key]) == 1
        assert pm._histograms[key][0] == 0.05


class TestGetStats:
    """Tests for get_stats method."""

    @patch("Engine8_Knowledge.monitoring.metrics.PlatformMetrics._initialize")
    def test_get_stats_returns_dict(self, mock_init):
        """get_stats should return a dict with prometheus_available, counters, gauges, histograms."""
        pm = PlatformMetrics()
        stats = pm.get_stats()
        assert "prometheus_available" in stats
        assert "counters" in stats
        assert "gauges" in stats
        assert "histograms" in stats

    @patch("Engine8_Knowledge.monitoring.metrics.PlatformMetrics._initialize")
    def test_get_stats_counts_match(self, mock_init):
        """get_stats counts should reflect actual stored metrics."""
        pm = PlatformMetrics()
        pm.inc_counter("a", {"x": "1"})
        pm.inc_counter("b", {"x": "2"})
        pm.set_gauge("g1", 10.0)
        pm.observe_histogram("h1", 0.5)
        stats = pm.get_stats()
        assert stats["counters"] == 2
        assert stats["gauges"] == 1
        assert stats["histograms"] == 1


class TestFallbackBehavior:
    """Tests for fallback when prometheus_client is not installed."""

    def test_fallback_when_prom_not_available(self):
        """When prometheus_client is not importable, _prom_available should be False."""
        with patch.dict("sys.modules", {"prometheus_client": None}):
            with patch("builtins.__import__", side_effect=_import_side_effect):
                pm = PlatformMetrics()
                assert pm._prom_available is False

    @patch("Engine8_Knowledge.monitoring.metrics.PlatformMetrics._initialize")
    def test_inc_counter_works_without_prom(self, mock_init):
        """inc_counter should still update internal dict even without prometheus_client."""
        pm = PlatformMetrics()
        pm._prom_available = False
        pm.inc_counter("requests", {"method": "GET", "endpoint": "/test", "status_code": "200"})
        assert len(pm._counters) == 1


class TestGetPlatformMetricsSingleton:
    """Tests for get_platform_metrics singleton function."""

    def test_returns_platform_metrics_instance(self):
        """get_platform_metrics should return a PlatformMetrics instance."""
        import Engine8_Knowledge.monitoring.metrics as mod
        # Reset singleton for isolated test
        mod._metrics = None
        m = get_platform_metrics()
        assert isinstance(m, PlatformMetrics)

    def test_returns_same_instance(self):
        """get_platform_metrics should return the same instance on subsequent calls."""
        import Engine8_Knowledge.monitoring.metrics as mod
        mod._metrics = None
        m1 = get_platform_metrics()
        m2 = get_platform_metrics()
        assert m1 is m2


def _import_side_effect(name, *args, **kwargs):
    """Side effect helper that blocks prometheus_client imports."""
    if name == "prometheus_client":
        raise ImportError("mocked: prometheus_client not installed")
    return original_import(name, *args, **kwargs)


import builtins
original_import = builtins.__import__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
