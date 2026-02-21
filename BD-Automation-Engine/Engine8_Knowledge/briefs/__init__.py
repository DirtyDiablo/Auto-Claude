"""Feature 23 — Automated Weekly Intelligence Briefs.

Generates, stores, and delivers periodic intelligence briefs
from BD pipeline data.
"""

from Engine8_Knowledge.briefs.template_engine import (
    BriefSection,
    BriefTemplateEngine,
    IntelligenceBrief,
)
from Engine8_Knowledge.briefs.delivery import BriefDeliveryService

__all__ = [
    "BriefSection",
    "IntelligenceBrief",
    "BriefTemplateEngine",
    "BriefDeliveryService",
]
