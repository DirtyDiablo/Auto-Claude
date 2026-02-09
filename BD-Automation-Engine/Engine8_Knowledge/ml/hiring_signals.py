"""
Hiring Signal Detection — Anomaly detection for BD intelligence.

Detects hiring surges, new capability acquisitions, and clearance escalations
by analyzing job posting patterns over time.
"""

import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


# ─── Signal Types ────────────────────────────────────────────────────────────

@dataclass
class HiringSignal:
    """A detected hiring anomaly signal."""
    signal_type: str           # hiring_surge | new_capability | clearance_escalation
    program: str               # affected program name
    location: str              # affected location
    confidence: float          # 0.0 to 1.0
    detected_at: str           # ISO timestamp
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── Signal Detector ─────────────────────────────────────────────────────────

class HiringSignalDetector:
    """
    Analyzes job posting patterns to detect BD-relevant signals.

    Signal types:
    - hiring_surge: Posting frequency > 2x the rolling average
    - new_capability: New role types never posted before for a program
    - clearance_escalation: Higher clearance requirements appearing
    """

    # Clearance level ordering (higher = more restrictive)
    CLEARANCE_LEVELS = {
        "none": 0,
        "public trust": 1,
        "secret": 2,
        "top secret": 3,
        "ts/sci": 4,
        "ts/sci w/ poly": 5,
        "ts/sci with poly": 5,
        "ts/sci w/ ci poly": 5,
        "ts/sci w/ full scope poly": 6,
        "ts/sci with full scope poly": 6,
    }

    def __init__(self):
        self._active_signals: List[HiringSignal] = []
        self._last_detection: Optional[str] = None
        # Historical state for tracking known roles/clearances per program
        self._known_roles: Dict[str, set] = defaultdict(set)
        self._known_clearances: Dict[str, int] = defaultdict(int)

    def detect_signals(self, jobs_data: List[Dict[str, Any]]) -> List[HiringSignal]:
        """
        Run all signal detectors on the provided job data.

        Args:
            jobs_data: List of job dicts with keys: title, program, location,
                       clearance, company, scraped_at/created_at, functional_area

        Returns:
            List of detected HiringSignal objects
        """
        signals: List[HiringSignal] = []

        if not jobs_data:
            return signals

        signals.extend(self._detect_hiring_surges(jobs_data))
        signals.extend(self._detect_new_capabilities(jobs_data))
        signals.extend(self._detect_clearance_escalations(jobs_data))

        # Sort by confidence descending
        signals.sort(key=lambda s: s.confidence, reverse=True)

        self._active_signals = signals
        self._last_detection = datetime.now().isoformat()

        logger.info(f"Detected {len(signals)} hiring signals")
        return signals

    def get_active_signals(self) -> List[HiringSignal]:
        """Return most recently detected signals."""
        return self._active_signals

    def get_status(self) -> Dict[str, Any]:
        """Get detector status."""
        signal_counts = defaultdict(int)
        for s in self._active_signals:
            signal_counts[s.signal_type] += 1

        return {
            "active_signals": len(self._active_signals),
            "last_detection": self._last_detection,
            "signal_counts": dict(signal_counts),
        }

    # ─── Hiring Surge Detection ──────────────────────────────────────────

    def _detect_hiring_surges(self, jobs_data: List[Dict[str, Any]]) -> List[HiringSignal]:
        """Detect programs/locations with posting frequency > 2x rolling average."""
        signals = []

        # Group jobs by program and bucket by week
        program_weeks: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        program_locations: Dict[str, set] = defaultdict(set)

        for job in jobs_data:
            program = job.get("program", "").strip()
            if not program:
                continue

            date_str = job.get("scraped_at") or job.get("created_at") or ""
            location = job.get("location", "Unknown")
            program_locations[program].add(location)

            try:
                if date_str:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    dt = datetime.now()
                week_key = dt.strftime("%Y-W%W")
            except (ValueError, TypeError):
                week_key = datetime.now().strftime("%Y-W%W")

            program_weeks[program][week_key] += 1

        # Analyze each program
        for program, weeks in program_weeks.items():
            if len(weeks) < 2:
                continue

            weekly_counts = sorted(weeks.items())
            counts = [c for _, c in weekly_counts]

            # Rolling average (all weeks except last)
            if len(counts) >= 2:
                rolling_avg = sum(counts[:-1]) / len(counts[:-1])
                latest = counts[-1]

                if rolling_avg > 0 and latest > 2 * rolling_avg and latest >= 3:
                    ratio = latest / rolling_avg
                    confidence = min(0.95, 0.5 + (ratio - 2.0) * 0.15)
                    locations = list(program_locations.get(program, {"Unknown"}))

                    signals.append(HiringSignal(
                        signal_type="hiring_surge",
                        program=program,
                        location=locations[0] if locations else "Unknown",
                        confidence=round(confidence, 2),
                        detected_at=datetime.now().isoformat(),
                        details={
                            "latest_week_count": latest,
                            "rolling_average": round(rolling_avg, 1),
                            "surge_ratio": round(ratio, 1),
                            "total_weeks_analyzed": len(counts),
                            "all_locations": locations[:5],
                        },
                    ))

        return signals

    # ─── New Capability Detection ────────────────────────────────────────

    def _detect_new_capabilities(self, jobs_data: List[Dict[str, Any]]) -> List[HiringSignal]:
        """Detect new role types never posted before for a program."""
        signals = []

        # Group jobs by program
        program_roles: Dict[str, List[Dict]] = defaultdict(list)
        for job in jobs_data:
            program = job.get("program", "").strip()
            if not program:
                continue
            program_roles[program].append(job)

        for program, jobs in program_roles.items():
            # Sort by date to determine "new" roles
            dated_jobs = []
            for job in jobs:
                date_str = job.get("scraped_at") or job.get("created_at") or ""
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else datetime.now()
                except (ValueError, TypeError):
                    dt = datetime.now()
                dated_jobs.append((dt, job))

            dated_jobs.sort(key=lambda x: x[0])

            # Split into historical (first 70%) and recent (last 30%)
            split_idx = max(1, int(len(dated_jobs) * 0.7))
            historical = dated_jobs[:split_idx]
            recent = dated_jobs[split_idx:]

            if not recent:
                continue

            # Extract functional areas / role categories
            historical_areas = set()
            for _, job in historical:
                area = (job.get("functional_area") or job.get("title", "")).lower().strip()
                if area:
                    historical_areas.add(area)
                self._known_roles[program].add(area)

            for _, job in recent:
                area = (job.get("functional_area") or job.get("title", "")).lower().strip()
                if area and area not in historical_areas and area not in self._known_roles[program]:
                    confidence = 0.7 if len(historical_areas) >= 5 else 0.5
                    location = job.get("location", "Unknown")

                    signals.append(HiringSignal(
                        signal_type="new_capability",
                        program=program,
                        location=location,
                        confidence=round(confidence, 2),
                        detected_at=datetime.now().isoformat(),
                        details={
                            "new_role": job.get("title", area),
                            "functional_area": job.get("functional_area", ""),
                            "company": job.get("company", ""),
                            "historical_role_count": len(historical_areas),
                        },
                    ))
                    self._known_roles[program].add(area)

        return signals

    # ─── Clearance Escalation Detection ──────────────────────────────────

    def _detect_clearance_escalations(self, jobs_data: List[Dict[str, Any]]) -> List[HiringSignal]:
        """Detect higher clearance requirements appearing for a program."""
        signals = []

        # Group by program
        program_jobs: Dict[str, List[Dict]] = defaultdict(list)
        for job in jobs_data:
            program = job.get("program", "").strip()
            if not program:
                continue
            program_jobs[program].append(job)

        for program, jobs in program_jobs.items():
            # Sort by date
            dated_jobs = []
            for job in jobs:
                date_str = job.get("scraped_at") or job.get("created_at") or ""
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else datetime.now()
                except (ValueError, TypeError):
                    dt = datetime.now()
                dated_jobs.append((dt, job))

            dated_jobs.sort(key=lambda x: x[0])

            split_idx = max(1, int(len(dated_jobs) * 0.7))
            historical = dated_jobs[:split_idx]
            recent = dated_jobs[split_idx:]

            if not recent:
                continue

            # Find max historical clearance level
            max_historical = 0
            for _, job in historical:
                clearance = (job.get("clearance") or "").lower().strip()
                level = self.CLEARANCE_LEVELS.get(clearance, 0)
                max_historical = max(max_historical, level)

            # Track per program
            prev_max = self._known_clearances.get(program, max_historical)
            self._known_clearances[program] = max_historical

            # Check recent for escalation
            for _, job in recent:
                clearance = (job.get("clearance") or "").lower().strip()
                level = self.CLEARANCE_LEVELS.get(clearance, 0)

                if level > max(max_historical, prev_max) and level >= 2:
                    escalation = level - max(max_historical, prev_max)
                    confidence = min(0.95, 0.6 + escalation * 0.1)
                    location = job.get("location", "Unknown")

                    signals.append(HiringSignal(
                        signal_type="clearance_escalation",
                        program=program,
                        location=location,
                        confidence=round(confidence, 2),
                        detected_at=datetime.now().isoformat(),
                        details={
                            "new_clearance": clearance,
                            "new_level": level,
                            "previous_max_level": max(max_historical, prev_max),
                            "escalation_steps": escalation,
                            "job_title": job.get("title", ""),
                            "company": job.get("company", ""),
                        },
                    ))

                    # Update tracked max
                    self._known_clearances[program] = max(self._known_clearances[program], level)

        return signals


# ─── Singleton ──────────────────────────────────────────────────────────────

_detector: Optional[HiringSignalDetector] = None


def get_signal_detector() -> HiringSignalDetector:
    """Get or create the singleton HiringSignalDetector."""
    global _detector
    if _detector is None:
        _detector = HiringSignalDetector()
    return _detector
