"""Phase 54A — Chaos Experiment Engine.

Defines, runs, and evaluates chaos experiments that simulate faults
(latency spikes, errors, timeouts, resource exhaustion, network
partitions, data corruption) against BD-engine services.  Validates
steady-state hypotheses before and after each experiment.
"""

from __future__ import annotations

import logging
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================

class FaultType(str, Enum):
    LATENCY = "latency"
    ERROR = "error"
    TIMEOUT = "timeout"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    NETWORK_PARTITION = "network_partition"
    DATA_CORRUPTION = "data_corruption"


class ExperimentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class ChaosExperiment:
    """A single chaos experiment definition and outcome."""
    experiment_id: str
    name: str
    description: str = ""
    fault_type: FaultType = FaultType.LATENCY
    target_service: str = ""
    duration_sec: float = 30.0
    intensity: float = 0.5  # 0.0-1.0
    status: ExperimentStatus = ExperimentStatus.PENDING
    started_at: str = ""
    ended_at: str = ""
    results: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "description": self.description,
            "fault_type": self.fault_type.value,
            "target_service": self.target_service,
            "duration_sec": self.duration_sec,
            "intensity": self.intensity,
            "status": self.status.value,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "results": self.results,
        }


@dataclass
class SteadyStateHypothesis:
    """A hypothesis about normal system behaviour to verify."""
    metric_name: str
    operator: str = "gt"  # gt | lt | eq
    threshold: float = 0.0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "operator": self.operator,
            "threshold": self.threshold,
            "description": self.description,
        }


# =========================================
# PRE-BUILT EXPERIMENT TEMPLATES
# =========================================

_EXPERIMENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "latency_spike_qdrant": {
        "name": "Qdrant Latency Spike",
        "description": "Inject 200-500ms latency into Qdrant search calls",
        "fault_type": FaultType.LATENCY,
        "target_service": "qdrant_search",
        "duration_sec": 60.0,
        "intensity": 0.7,
    },
    "api_gateway_error_burst": {
        "name": "API Gateway Error Burst",
        "description": "Inject HTTP 500 errors at 40% rate on the API gateway",
        "fault_type": FaultType.ERROR,
        "target_service": "api_gateway",
        "duration_sec": 45.0,
        "intensity": 0.4,
    },
    "n8n_timeout": {
        "name": "n8n Workflow Timeout",
        "description": "Simulate n8n workflow execution timeouts",
        "fault_type": FaultType.TIMEOUT,
        "target_service": "n8n_workflow",
        "duration_sec": 90.0,
        "intensity": 0.6,
    },
    "agent_resource_exhaustion": {
        "name": "Agent Resource Exhaustion",
        "description": "Simulate memory/CPU exhaustion in agent executor pool",
        "fault_type": FaultType.RESOURCE_EXHAUSTION,
        "target_service": "agent_executor",
        "duration_sec": 120.0,
        "intensity": 0.8,
    },
    "bullhorn_network_partition": {
        "name": "Bullhorn Network Partition",
        "description": "Simulate network partition to Bullhorn ETL service",
        "fault_type": FaultType.NETWORK_PARTITION,
        "target_service": "bullhorn_etl",
        "duration_sec": 60.0,
        "intensity": 1.0,
    },
}


# =========================================
# CHAOS EXPERIMENT ENGINE
# =========================================

class ChaosExperimentEngine:
    """Chaos engineering engine for fault injection and resilience testing.

    Creates experiments from templates or custom definitions, simulates
    fault injection, records results, and validates steady-state
    hypotheses before and after each run.
    """

    def __init__(self):
        self._experiments: Dict[str, ChaosExperiment] = {}
        self._templates = dict(_EXPERIMENT_TEMPLATES)
        self._total_runs = 0
        self._total_aborted = 0
        logger.info(
            "ChaosExperimentEngine initialized with %d templates",
            len(self._templates),
        )

    # ----- experiment lifecycle -----

    def create_experiment(
        self,
        name: str,
        fault_type: FaultType,
        target_service: str,
        duration_sec: float = 30.0,
        intensity: float = 0.5,
        description: str = "",
    ) -> ChaosExperiment:
        """Create a new chaos experiment."""
        exp_id = f"chaos_{uuid.uuid4().hex[:12]}"
        experiment = ChaosExperiment(
            experiment_id=exp_id,
            name=name,
            description=description or f"{fault_type.value} fault on {target_service}",
            fault_type=fault_type,
            target_service=target_service,
            duration_sec=duration_sec,
            intensity=max(0.0, min(1.0, intensity)),
        )
        self._experiments[exp_id] = experiment
        logger.info(
            "Created chaos experiment '%s' [%s] targeting '%s'",
            name, exp_id, target_service,
        )
        return experiment

    def create_from_template(self, template_key: str) -> Optional[ChaosExperiment]:
        """Create an experiment from a pre-built template."""
        tpl = self._templates.get(template_key)
        if not tpl:
            logger.warning("Unknown template key: %s", template_key)
            return None
        return self.create_experiment(
            name=tpl["name"],
            fault_type=tpl["fault_type"],
            target_service=tpl["target_service"],
            duration_sec=tpl["duration_sec"],
            intensity=tpl["intensity"],
            description=tpl["description"],
        )

    def run_experiment(self, experiment_id: str) -> Optional[ChaosExperiment]:
        """Simulate running a chaos experiment.

        In a real system this would inject faults via sidecar proxies or
        kernel-level fault injection.  Here we simulate the fault effects
        and record synthetic results.
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            logger.warning("Experiment '%s' not found", experiment_id)
            return None

        if experiment.status not in (ExperimentStatus.PENDING,):
            logger.warning(
                "Experiment '%s' cannot run from status '%s'",
                experiment_id, experiment.status.value,
            )
            return experiment

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.utcnow().isoformat()
        self._total_runs += 1

        logger.info(
            "Running chaos experiment '%s' (%s on %s for %.0fs at %.0f%% intensity)",
            experiment.name,
            experiment.fault_type.value,
            experiment.target_service,
            experiment.duration_sec,
            experiment.intensity * 100,
        )

        # Simulate fault injection results based on fault type
        results = self._simulate_fault(experiment)

        experiment.results = results
        experiment.ended_at = datetime.utcnow().isoformat()
        experiment.status = ExperimentStatus.COMPLETED

        logger.info(
            "Chaos experiment '%s' completed: %s",
            experiment.name, results,
        )
        return experiment

    def abort_experiment(self, experiment_id: str) -> bool:
        """Abort a running or pending experiment. Returns False if not found."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return False

        if experiment.status in (ExperimentStatus.RUNNING, ExperimentStatus.PENDING):
            experiment.status = ExperimentStatus.ABORTED
            if experiment.status == ExperimentStatus.RUNNING:
                experiment.ended_at = datetime.utcnow().isoformat()
            self._total_aborted += 1
            logger.warning("Chaos experiment '%s' ABORTED", experiment.name)

        return True

    # ----- querying -----

    def get_experiment(self, experiment_id: str) -> Optional[ChaosExperiment]:
        return self._experiments.get(experiment_id)

    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
        limit: int = 50,
    ) -> List[ChaosExperiment]:
        """List experiments, optionally filtered by status."""
        experiments = list(self._experiments.values())
        if status is not None:
            experiments = [e for e in experiments if e.status == status]
        return experiments[-limit:]

    def list_templates(self) -> Dict[str, Dict[str, Any]]:
        """Return the available experiment templates."""
        return {
            key: {
                "name": tpl["name"],
                "description": tpl["description"],
                "fault_type": tpl["fault_type"].value,
                "target_service": tpl["target_service"],
                "duration_sec": tpl["duration_sec"],
                "intensity": tpl["intensity"],
            }
            for key, tpl in self._templates.items()
        }

    # ----- steady-state verification -----

    def verify_steady_state(self, hypothesis: SteadyStateHypothesis) -> Dict[str, Any]:
        """Check a steady-state hypothesis against current metrics.

        In production this would query the metrics pipeline.  Here we
        simulate a metric value and evaluate the hypothesis.
        """
        # Simulate a current metric value
        simulated_value = self._simulate_metric(hypothesis.metric_name)

        if hypothesis.operator == "gt":
            passed = simulated_value > hypothesis.threshold
        elif hypothesis.operator == "lt":
            passed = simulated_value < hypothesis.threshold
        elif hypothesis.operator == "eq":
            passed = abs(simulated_value - hypothesis.threshold) < 0.001
        else:
            passed = False

        result = {
            "hypothesis": hypothesis.to_dict(),
            "measured_value": round(simulated_value, 4),
            "passed": passed,
            "evaluated_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Steady-state check '%s' %s %.4f (threshold %s %.4f): %s",
            hypothesis.metric_name,
            hypothesis.operator,
            simulated_value,
            hypothesis.operator,
            hypothesis.threshold,
            "PASSED" if passed else "FAILED",
        )
        return result

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        by_status: Dict[str, int] = {}
        for e in self._experiments.values():
            by_status[e.status.value] = by_status.get(e.status.value, 0) + 1
        return {
            "total_experiments": len(self._experiments),
            "total_runs": self._total_runs,
            "total_aborted": self._total_aborted,
            "by_status": by_status,
            "templates_available": len(self._templates),
        }

    # ----- internal simulation helpers -----

    def _simulate_fault(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Produce simulated fault-injection results."""
        intensity = experiment.intensity
        duration = experiment.duration_sec

        if experiment.fault_type == FaultType.LATENCY:
            base_latency_ms = 200 + intensity * 800  # 200-1000ms
            return {
                "latency_added_ms": round(base_latency_ms, 1),
                "requests_affected": int(duration * 10 * intensity),
                "p99_latency_ms": round(base_latency_ms * 1.5, 1),
                "fault_type": "latency",
            }

        if experiment.fault_type == FaultType.ERROR:
            error_rate = intensity * 100
            return {
                "errors_injected": int(duration * 5 * intensity),
                "error_rate_pct": round(error_rate, 1),
                "http_status_codes": {500: int(duration * 3 * intensity), 503: int(duration * 2 * intensity)},
                "fault_type": "error",
            }

        if experiment.fault_type == FaultType.TIMEOUT:
            return {
                "timeouts_injected": int(duration * 2 * intensity),
                "avg_timeout_sec": round(5.0 + intensity * 25.0, 1),
                "connections_hung": int(duration * intensity),
                "fault_type": "timeout",
            }

        if experiment.fault_type == FaultType.RESOURCE_EXHAUSTION:
            return {
                "memory_pressure_pct": round(60 + intensity * 35, 1),
                "cpu_spike_pct": round(50 + intensity * 45, 1),
                "oom_kills": int(intensity * 3),
                "degraded_responses": int(duration * 4 * intensity),
                "fault_type": "resource_exhaustion",
            }

        if experiment.fault_type == FaultType.NETWORK_PARTITION:
            return {
                "packets_dropped": int(duration * 100 * intensity),
                "connections_refused": int(duration * 10 * intensity),
                "partition_duration_sec": round(duration * intensity, 1),
                "fault_type": "network_partition",
            }

        if experiment.fault_type == FaultType.DATA_CORRUPTION:
            return {
                "records_corrupted": int(duration * 2 * intensity),
                "checksums_failed": int(duration * 3 * intensity),
                "corruption_rate_pct": round(intensity * 5, 2),
                "fault_type": "data_corruption",
            }

        return {"fault_type": experiment.fault_type.value, "note": "unknown fault type"}

    def _simulate_metric(self, metric_name: str) -> float:
        """Return a simulated metric value for steady-state verification."""
        known_metrics = {
            "api_availability_pct": 99.5 + random.uniform(0, 0.49),
            "api_error_rate_pct": random.uniform(0.01, 0.5),
            "search_latency_p99_ms": random.uniform(80, 300),
            "pipeline_throughput_rps": random.uniform(800, 1500),
            "agent_pool_utilization": random.uniform(0.3, 0.8),
        }
        return known_metrics.get(metric_name, random.uniform(0, 100))


# =========================================
# SINGLETON
# =========================================

_instance: Optional[ChaosExperimentEngine] = None


def get_chaos_engine() -> ChaosExperimentEngine:
    global _instance
    if _instance is None:
        _instance = ChaosExperimentEngine()
    return _instance
