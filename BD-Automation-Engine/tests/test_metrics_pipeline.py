"""Tests for Phase 53A — Metrics Pipeline."""

import pytest

from src.observability.metrics_pipeline import (
    MetricsPipeline,
    MetricType,
    AlertRule,
    get_metrics,
)


@pytest.fixture
def pipeline():
    return MetricsPipeline()


# =========================================
# BUILT-IN METRICS
# =========================================


def test_builtin_metrics(pipeline):
    metrics = pipeline.list_metrics()
    assert len(metrics) == 14


def test_builtin_api_latency(pipeline):
    m = pipeline.get_metric("api_request_duration_ms")
    assert m is not None
    assert m.metric_type == MetricType.HISTOGRAM


def test_builtin_contacts_indexed(pipeline):
    m = pipeline.get_metric("contacts_indexed")
    assert m is not None
    assert m.metric_type == MetricType.GAUGE


# =========================================
# RECORDING
# =========================================


def test_record_counter(pipeline):
    pipeline.increment("api_requests_total")
    pipeline.increment("api_requests_total")
    m = pipeline.get_metric("api_requests_total")
    assert m._count == 2
    assert m._sum == 2.0


def test_record_gauge(pipeline):
    pipeline.set_gauge("contacts_indexed", 8447)
    m = pipeline.get_metric("contacts_indexed")
    assert m.get_current() == 8447


def test_record_histogram(pipeline):
    for val in [10, 50, 100, 200, 500]:
        pipeline.observe("api_request_duration_ms", val)
    m = pipeline.get_metric("api_request_duration_ms")
    assert m._count == 5
    assert m.get_average() == 172.0


def test_record_with_labels(pipeline):
    pipeline.record("api_requests_total", 1, {"method": "GET", "path": "/search"})
    m = pipeline.get_metric("api_requests_total")
    assert m.points[-1].labels["method"] == "GET"


def test_auto_create_metric(pipeline):
    pipeline.record("custom_metric", 42.0)
    m = pipeline.get_metric("custom_metric")
    assert m is not None
    assert m.metric_type == MetricType.GAUGE


# =========================================
# STATISTICS
# =========================================


def test_percentile(pipeline):
    for i in range(100):
        pipeline.observe("api_request_duration_ms", float(i))
    m = pipeline.get_metric("api_request_duration_ms")
    p50 = m.get_percentile(50)
    assert 45 <= p50 <= 55
    p99 = m.get_percentile(99)
    assert p99 >= 95


def test_min_max(pipeline):
    for val in [10, 50, 100]:
        pipeline.observe("search_latency_ms", val)
    m = pipeline.get_metric("search_latency_ms")
    assert m._min == 10
    assert m._max == 100


def test_histogram_buckets(pipeline):
    for val in [5, 15, 30, 60, 200]:
        pipeline.observe("api_request_duration_ms", val)
    m = pipeline.get_metric("api_request_duration_ms")
    # 5ms bucket should have 1 value (5)
    assert m.bucket_counts.get("5", 0) == 1
    # 25ms bucket should have 2 values (5, 15)
    assert m.bucket_counts.get("25", 0) == 2


# =========================================
# CUSTOM METRICS
# =========================================


def test_register_metric(pipeline):
    m = pipeline.register_metric(
        "my_custom_counter",
        MetricType.COUNTER,
        "A custom counter",
        "ops",
    )
    assert m.name == "my_custom_counter"
    pipeline.increment("my_custom_counter")
    assert pipeline.get_metric("my_custom_counter")._sum == 1.0


def test_list_by_type(pipeline):
    gauges = pipeline.list_metrics(metric_type=MetricType.GAUGE)
    assert all(m.metric_type == MetricType.GAUGE for m in gauges)


def test_get_metric_value(pipeline):
    pipeline.set_gauge("contacts_indexed", 100)
    assert pipeline.get_metric_value("contacts_indexed") == 100


def test_get_metric_value_not_found(pipeline):
    assert pipeline.get_metric_value("nonexistent") is None


# =========================================
# ALERTS
# =========================================


def test_add_alert_rule(pipeline):
    rule = pipeline.add_alert_rule(
        "api_request_duration_ms",
        "gt",
        1000.0,
        "critical",
    )
    assert isinstance(rule, AlertRule)
    assert rule.rule_id.startswith("rule_")


def test_alert_triggers(pipeline):
    pipeline.add_alert_rule(
        "api_request_duration_ms",
        "gt",
        100.0,
        "warning",
    )
    pipeline.observe("api_request_duration_ms", 200.0)
    alerts = pipeline.get_alerts()
    assert len(alerts) >= 1
    assert alerts[0].severity == "warning"


def test_alert_not_triggered_below_threshold(pipeline):
    pipeline.add_alert_rule(
        "api_request_duration_ms",
        "gt",
        1000.0,
        "critical",
    )
    pipeline.observe("api_request_duration_ms", 50.0)
    alerts = pipeline.get_alerts()
    assert len(alerts) == 0


def test_list_alert_rules(pipeline):
    pipeline.add_alert_rule("m1", "gt", 100)
    pipeline.add_alert_rule("m2", "lt", 50)
    rules = pipeline.list_alert_rules()
    assert len(rules) == 2


def test_alert_to_dict(pipeline):
    pipeline.add_alert_rule("api_request_duration_ms", "gt", 10.0)
    pipeline.observe("api_request_duration_ms", 200.0)
    alerts = pipeline.get_alerts()
    d = alerts[0].to_dict()
    assert "alert_id" in d
    assert "severity" in d


# =========================================
# EXPORT
# =========================================


def test_export_prometheus(pipeline):
    pipeline.increment("api_requests_total")
    text = pipeline.export_prometheus()
    assert "api_requests_total" in text
    assert "HELP" in text
    assert "TYPE" in text


def test_export_json(pipeline):
    pipeline.increment("api_requests_total")
    data = pipeline.export_json()
    assert len(data) >= 1
    assert data[0]["name"] == "api_requests_total"


# =========================================
# TO_DICT & STATS
# =========================================


def test_metric_to_dict(pipeline):
    pipeline.observe("api_request_duration_ms", 100)
    m = pipeline.get_metric("api_request_duration_ms")
    d = m.to_dict()
    assert "name" in d
    assert "p50" in d
    assert "p95" in d


def test_stats(pipeline):
    pipeline.increment("api_requests_total")
    stats = pipeline.get_stats()
    assert stats["total_metrics"] == 14
    assert stats["active_metrics"] >= 1


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    import src.observability.metrics_pipeline as mod

    mod._instance = None
    m1 = get_metrics()
    m2 = get_metrics()
    assert m1 is m2
    mod._instance = None
