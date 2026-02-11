"""Phase 53A — OpenTelemetry-Compatible Distributed Tracer.

W3C Trace-Context propagation, span trees, automatic instrumentation
for API requests, database calls, and agent invocations.  Supports
sampling strategies and trace export.
"""

from __future__ import annotations

import hashlib
import logging
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================

class SpanKind(str, Enum):
    SERVER = "server"
    CLIENT = "client"
    INTERNAL = "internal"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


@dataclass
class SpanEvent:
    """An event within a span (e.g., exception, log)."""
    name: str
    timestamp: str
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "attributes": self.attributes,
        }


@dataclass
class Span:
    """A single unit of work in a distributed trace."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    operation_name: str = ""
    service_name: str = "bd-engine"
    kind: SpanKind = SpanKind.INTERNAL
    status: SpanStatus = SpanStatus.UNSET
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    links: List[str] = field(default_factory=list)  # linked trace_ids

    def __post_init__(self):
        if not self.start_time:
            self.start_time = time.time()

    def end(self) -> None:
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000

    def set_status(self, status: SpanStatus, message: str = "") -> None:
        self.status = status
        if message:
            self.attributes["status.message"] = message

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        self.events.append(SpanEvent(
            name=name,
            timestamp=datetime.utcnow().isoformat(),
            attributes=attributes or {},
        ))

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "service_name": self.service_name,
            "kind": self.kind.value,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": round(self.duration_ms, 3),
            "attributes": self.attributes,
            "events": [e.to_dict() for e in self.events],
        }


@dataclass
class Trace:
    """A distributed trace — a tree of spans."""
    trace_id: str
    root_span_id: str = ""
    service_name: str = "bd-engine"
    span_count: int = 0
    duration_ms: float = 0.0
    status: SpanStatus = SpanStatus.UNSET
    started_at: str = ""
    ended_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "root_span_id": self.root_span_id,
            "service_name": self.service_name,
            "span_count": self.span_count,
            "duration_ms": round(self.duration_ms, 3),
            "status": self.status.value,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }


@dataclass
class SamplingConfig:
    """Trace sampling configuration."""
    strategy: str = "probabilistic"  # always | never | probabilistic | rate_limiting
    sample_rate: float = 1.0  # 0.0-1.0 for probabilistic
    rate_limit_per_sec: float = 100.0  # for rate_limiting strategy

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "sample_rate": self.sample_rate,
            "rate_limit_per_sec": self.rate_limit_per_sec,
        }


# =========================================
# DISTRIBUTED TRACER
# =========================================

class DistributedTracer:
    """OpenTelemetry-compatible distributed tracing engine.

    Creates trace contexts, manages span trees, and supports W3C
    Trace-Context header propagation for cross-service tracing.
    """

    def __init__(self, service_name: str = "bd-engine"):
        self._service_name = service_name
        self._spans: Dict[str, Span] = {}  # span_id → Span
        self._traces: Dict[str, List[str]] = {}  # trace_id → [span_ids]
        self._active_spans: Dict[str, str] = {}  # context_id → span_id
        self._sampling = SamplingConfig()
        self._exported_traces: List[str] = []
        self._total_spans_created = 0
        self._total_spans_dropped = 0
        logger.info("DistributedTracer initialized for service '%s'", service_name)

    # ----- span lifecycle -----

    def start_span(
        self,
        operation_name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Start a new span, optionally within an existing trace."""
        # Sampling decision
        if not self._should_sample():
            self._total_spans_dropped += 1
            # Return a no-op span
            return Span(
                trace_id=trace_id or self._generate_trace_id(),
                span_id=self._generate_span_id(),
                operation_name=operation_name,
                service_name=self._service_name,
                kind=kind,
                status=SpanStatus.UNSET,
            )

        tid = trace_id or self._generate_trace_id()
        sid = self._generate_span_id()

        span = Span(
            trace_id=tid,
            span_id=sid,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            service_name=self._service_name,
            kind=kind,
            attributes=attributes or {},
        )

        self._spans[sid] = span
        self._traces.setdefault(tid, []).append(sid)
        self._total_spans_created += 1

        return span

    def end_span(self, span: Span) -> None:
        """End a span and record its duration."""
        span.end()
        if span.status == SpanStatus.UNSET:
            span.set_status(SpanStatus.OK)

    def start_trace(
        self,
        operation_name: str,
        kind: SpanKind = SpanKind.SERVER,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Start a new trace with a root span."""
        return self.start_span(
            operation_name=operation_name,
            kind=kind,
            attributes=attributes,
        )

    # ----- context propagation -----

    def inject_context(self, span: Span) -> Dict[str, str]:
        """Generate W3C traceparent header for outgoing requests."""
        version = "00"
        trace_id = span.trace_id
        span_id = span.span_id
        flags = "01"  # sampled
        traceparent = f"{version}-{trace_id}-{span_id}-{flags}"
        return {"traceparent": traceparent}

    def extract_context(self, headers: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Extract trace context from incoming W3C traceparent header."""
        traceparent = headers.get("traceparent", "")
        if not traceparent:
            return None
        parts = traceparent.split("-")
        if len(parts) != 4:
            return None
        return {
            "version": parts[0],
            "trace_id": parts[1],
            "parent_span_id": parts[2],
            "flags": parts[3],
        }

    # ----- querying -----

    def get_span(self, span_id: str) -> Optional[Span]:
        return self._spans.get(span_id)

    def get_trace_spans(self, trace_id: str) -> List[Span]:
        """Get all spans in a trace."""
        span_ids = self._traces.get(trace_id, [])
        return [self._spans[sid] for sid in span_ids if sid in self._spans]

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Build a Trace summary from span data."""
        spans = self.get_trace_spans(trace_id)
        if not spans:
            return None

        root = None
        for s in spans:
            if s.parent_span_id is None:
                root = s
                break
        if not root:
            root = spans[0]

        # Find earliest start and latest end
        min_start = min(s.start_time for s in spans)
        max_end = max(s.end_time for s in spans if s.end_time > 0)
        if max_end == 0:
            max_end = time.time()

        has_error = any(s.status == SpanStatus.ERROR for s in spans)

        return Trace(
            trace_id=trace_id,
            root_span_id=root.span_id,
            service_name=self._service_name,
            span_count=len(spans),
            duration_ms=(max_end - min_start) * 1000,
            status=SpanStatus.ERROR if has_error else SpanStatus.OK,
            started_at=datetime.fromtimestamp(min_start).isoformat(),
            ended_at=datetime.fromtimestamp(max_end).isoformat(),
        )

    def list_traces(self, limit: int = 50) -> List[Trace]:
        """List recent traces."""
        traces = []
        for tid in list(self._traces.keys())[-limit:]:
            t = self.get_trace(tid)
            if t:
                traces.append(t)
        return list(reversed(traces))

    def search_spans(
        self,
        operation_name: Optional[str] = None,
        service_name: Optional[str] = None,
        min_duration_ms: Optional[float] = None,
        status: Optional[SpanStatus] = None,
        limit: int = 50,
    ) -> List[Span]:
        """Search spans by attributes."""
        spans = list(self._spans.values())
        if operation_name:
            spans = [s for s in spans if operation_name in s.operation_name]
        if service_name:
            spans = [s for s in spans if s.service_name == service_name]
        if min_duration_ms is not None:
            spans = [s for s in spans if s.duration_ms >= min_duration_ms]
        if status:
            spans = [s for s in spans if s.status == status]
        return spans[-limit:]

    # ----- sampling -----

    def set_sampling(self, config: SamplingConfig) -> None:
        self._sampling = config

    def get_sampling(self) -> SamplingConfig:
        return self._sampling

    def _should_sample(self) -> bool:
        if self._sampling.strategy == "always":
            return True
        if self._sampling.strategy == "never":
            return False
        if self._sampling.strategy == "probabilistic":
            return random.random() < self._sampling.sample_rate
        return True  # default: sample

    # ----- export -----

    def export_traces(self, trace_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Export traces in OTLP-compatible format."""
        ids = trace_ids or list(self._traces.keys())
        result = []
        for tid in ids:
            trace = self.get_trace(tid)
            if trace:
                spans = self.get_trace_spans(tid)
                result.append({
                    "trace": trace.to_dict(),
                    "spans": [s.to_dict() for s in spans],
                })
                if tid not in self._exported_traces:
                    self._exported_traces.append(tid)
        return result

    # ----- helpers -----

    def _generate_trace_id(self) -> str:
        return uuid.uuid4().hex

    def _generate_span_id(self) -> str:
        return uuid.uuid4().hex[:16]

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_traces": len(self._traces),
            "total_spans": len(self._spans),
            "total_spans_created": self._total_spans_created,
            "total_spans_dropped": self._total_spans_dropped,
            "exported_traces": len(self._exported_traces),
            "sampling": self._sampling.to_dict(),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[DistributedTracer] = None


def get_tracer() -> DistributedTracer:
    global _instance
    if _instance is None:
        _instance = DistributedTracer()
    return _instance
