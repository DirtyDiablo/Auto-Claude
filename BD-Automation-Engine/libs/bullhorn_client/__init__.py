"""
BD Automation Engine - Bullhorn CRM Client Library.

Extracted from services/bullhorn_integration.py.  Provides a typed
client for the Bullhorn REST API with OAuth authentication, search,
and CRUD operations.
"""

__version__ = "0.1.0"

from libs.bullhorn_client.client import (
    BullhornClient,
    BullhornConfig,
    MockBullhornClient,
    get_bullhorn_client,
)
from libs.bullhorn_client.models import (
    BullhornCandidate,
    BullhornContact,
    BullhornJobOrder,
)

__all__ = [
    "BullhornClient",
    "BullhornConfig",
    "MockBullhornClient",
    "get_bullhorn_client",
    "BullhornCandidate",
    "BullhornContact",
    "BullhornJobOrder",
]
