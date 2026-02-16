"""Tests for Phase 53A — Distributed Tracer."""

import pytest

from src.observability.distributed_tracer import (
    DistributedTracer,
    Span,
    SpanKind,
    SpanStatus,
    Trace,
    SamplingConfig,
    get_tracer,
)


@pytest.fixture
def tracer():
    return DistributedTracer(service_name="test-service")


# =========================================
# SPAN LIFECYCLE
# =========================================


def test_start_span(tracer):
    span = tracer.start_span("test.operation")
    assert isinstance(span, Span)
    assert span.operation_name == "test.operation"
    assert span.service_name == "test-service"


def test_span_has_ids(tracer):
    span = tracer.start_span("test.op")
    assert len(span.trace_id) == 32
    assert len(span.span_id) == 16


def test_end_span(tracer):
    span = tracer.start_span("test.op")
    tracer.end_span(span)
    assert span.end_time > 0
    assert span.duration_ms >= 0
    assert span.status == SpanStatus.OK


def test_span_with_error(tracer):
    span = tracer.start_span("test.op")
    span.set_status(SpanStatus.ERROR, "something failed")
    tracer.end_span(span)
    assert span.status == SpanStatus.ERROR
    assert span.attributes["status.message"] == "something failed"


def test_span_attributes(tracer):
    span = tracer.start_span("test.op", attributes={"key": "value"})
    span.set_attribute("method", "GET")
    assert span.attributes["key"] == "value"
    assert span.attributes["method"] == "GET"


def test_span_events(tracer):
    span = tracer.start_span("test.op")
    span.add_event("exception", {"type": "ValueError"})
    assert len(span.events) == 1
    assert span.events[0].name == "exception"


def test_span_kind(tracer):
    span = tracer.start_span("test.op", kind=SpanKind.CLIENT)
    assert span.kind == SpanKind.CLIENT


# =========================================
# TRACES
# =========================================


def test_start_trace(tracer):
    root = tracer.start_trace("api.request")
    assert root.parent_span_id is None
    assert root.kind == SpanKind.SERVER


def test_child_span(tracer):
    root = tracer.start_trace("api.request")
    child = tracer.start_span(
        "db.query",
        trace_id=root.trace_id,
        parent_span_id=root.span_id,
    )
    assert child.trace_id == root.trace_id
    assert child.parent_span_id == root.span_id


def test_get_trace(tracer):
    root = tracer.start_trace("api.request")
    tracer.end_span(root)
    trace = tracer.get_trace(root.trace_id)
    assert isinstance(trace, Trace)
    assert trace.span_count == 1


def test_get_trace_spans(tracer):
    root = tracer.start_trace("api.request")
    child = tracer.start_span(
        "db.query", trace_id=root.trace_id, parent_span_id=root.span_id
    )
    tracer.end_span(child)
    tracer.end_span(root)
    spans = tracer.get_trace_spans(root.trace_id)
    assert len(spans) == 2


def test_trace_has_error_status(tracer):
    root = tracer.start_trace("api.request")
    child = tracer.start_span(
        "db.query", trace_id=root.trace_id, parent_span_id=root.span_id
    )
    child.set_status(SpanStatus.ERROR)
    tracer.end_span(child)
    tracer.end_span(root)
    trace = tracer.get_trace(root.trace_id)
    assert trace.status == SpanStatus.ERROR


def test_list_traces(tracer):
    for i in range(5):
        span = tracer.start_trace(f"op_{i}")
        tracer.end_span(span)
    traces = tracer.list_traces()
    assert len(traces) == 5


def test_get_trace_not_found(tracer):
    assert tracer.get_trace("nonexistent") is None


# =========================================
# CONTEXT PROPAGATION
# =========================================


def test_inject_context(tracer):
    span = tracer.start_trace("api.request")
    headers = tracer.inject_context(span)
    assert "traceparent" in headers
    parts = headers["traceparent"].split("-")
    assert len(parts) == 4
    assert parts[0] == "00"


def test_extract_context(tracer):
    span = tracer.start_trace("api.request")
    headers = tracer.inject_context(span)
    ctx = tracer.extract_context(headers)
    assert ctx is not None
    assert ctx["trace_id"] == span.trace_id
    assert ctx["parent_span_id"] == span.span_id


def test_extract_context_invalid(tracer):
    assert tracer.extract_context({}) is None
    assert tracer.extract_context({"traceparent": "bad"}) is None


# =========================================
# SEARCH
# =========================================


def test_search_by_operation(tracer):
    s1 = tracer.start_span("api.users")
    tracer.end_span(s1)
    s2 = tracer.start_span("db.query")
    tracer.end_span(s2)
    results = tracer.search_spans(operation_name="api")
    assert len(results) == 1
    assert results[0].operation_name == "api.users"


def test_search_by_min_duration(tracer):
    s1 = tracer.start_span("fast")
    s1.duration_ms = 10
    s2 = tracer.start_span("slow")
    s2.duration_ms = 500
    results = tracer.search_spans(min_duration_ms=100)
    assert len(results) == 1


# =========================================
# SAMPLING
# =========================================


def test_sampling_always(tracer):
    tracer.set_sampling(SamplingConfig(strategy="always"))
    span = tracer.start_span("test")
    assert span.span_id in tracer._spans


def test_sampling_never(tracer):
    tracer.set_sampling(SamplingConfig(strategy="never"))
    before = len(tracer._spans)
    tracer.start_span("test")
    assert len(tracer._spans) == before  # not recorded


def test_get_sampling(tracer):
    cfg = tracer.get_sampling()
    assert cfg.strategy == "probabilistic"
    assert cfg.sample_rate == 1.0


# =========================================
# EXPORT
# =========================================


def test_export_traces(tracer):
    root = tracer.start_trace("api.request")
    tracer.end_span(root)
    exported = tracer.export_traces()
    assert len(exported) == 1
    assert "trace" in exported[0]
    assert "spans" in exported[0]


# =========================================
# TO_DICT & STATS
# =========================================


def test_span_to_dict(tracer):
    span = tracer.start_span("test")
    tracer.end_span(span)
    d = span.to_dict()
    assert "trace_id" in d
    assert "span_id" in d
    assert "duration_ms" in d


def test_trace_to_dict(tracer):
    root = tracer.start_trace("test")
    tracer.end_span(root)
    trace = tracer.get_trace(root.trace_id)
    d = trace.to_dict()
    assert "trace_id" in d
    assert "span_count" in d


def test_stats(tracer):
    tracer.start_trace("test")
    stats = tracer.get_stats()
    assert stats["total_traces"] == 1
    assert stats["total_spans"] == 1


# =========================================
# SINGLETON
# =========================================


def test_singleton():
    import src.observability.distributed_tracer as mod

    mod._instance = None
    t1 = get_tracer()
    t2 = get_tracer()
    assert t1 is t2
    mod._instance = None
