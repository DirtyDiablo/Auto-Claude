"""Phase 58A — Responsive API Layer.

Adaptive API responses based on client capabilities, network conditions,
and device type. Supports content negotiation, pagination adaptation,
and bandwidth-aware payload optimization.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================

class DeviceType(Enum):
    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"
    WATCH = "watch"
    API_CLIENT = "api_client"


class NetworkQuality(Enum):
    EXCELLENT = "excellent"  # 4G+ / WiFi
    GOOD = "good"           # 4G
    FAIR = "fair"            # 3G
    POOR = "poor"            # 2G / slow
    OFFLINE = "offline"


class ResponseFormat(Enum):
    FULL = "full"
    COMPACT = "compact"
    MINIMAL = "minimal"
    SUMMARY = "summary"


@dataclass
class ClientProfile:
    """Detected client capabilities and preferences."""
    profile_id: str
    device_type: DeviceType = DeviceType.DESKTOP
    network_quality: NetworkQuality = NetworkQuality.EXCELLENT
    screen_width: int = 1920
    preferred_format: ResponseFormat = ResponseFormat.FULL
    supports_webp: bool = True
    supports_push: bool = True
    max_payload_kb: int = 500
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "device_type": self.device_type.value,
            "network_quality": self.network_quality.value,
            "screen_width": self.screen_width,
            "preferred_format": self.preferred_format.value,
            "supports_webp": self.supports_webp,
            "supports_push": self.supports_push,
            "max_payload_kb": self.max_payload_kb,
        }


@dataclass
class AdaptiveResponse:
    """Metadata about an adapted API response."""
    original_size_bytes: int = 0
    adapted_size_bytes: int = 0
    format_used: ResponseFormat = ResponseFormat.FULL
    fields_included: int = 0
    fields_omitted: int = 0
    page_size_used: int = 50
    compression_ratio: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_size_bytes": self.original_size_bytes,
            "adapted_size_bytes": self.adapted_size_bytes,
            "format_used": self.format_used.value,
            "fields_included": self.fields_included,
            "fields_omitted": self.fields_omitted,
            "page_size_used": self.page_size_used,
            "compression_ratio": round(self.compression_ratio, 3),
        }


# =========================================
# ADAPTATION RULES
# =========================================

_DEFAULT_PAGE_SIZES = {
    DeviceType.DESKTOP: 50,
    DeviceType.TABLET: 30,
    DeviceType.MOBILE: 15,
    DeviceType.WATCH: 5,
    DeviceType.API_CLIENT: 100,
}

_FORMAT_BY_NETWORK = {
    NetworkQuality.EXCELLENT: ResponseFormat.FULL,
    NetworkQuality.GOOD: ResponseFormat.FULL,
    NetworkQuality.FAIR: ResponseFormat.COMPACT,
    NetworkQuality.POOR: ResponseFormat.MINIMAL,
    NetworkQuality.OFFLINE: ResponseFormat.MINIMAL,
}

_FULL_FIELDS = [
    "id", "name", "title", "description", "status", "score",
    "company", "email", "phone", "program", "tier",
    "created_at", "updated_at", "metadata", "tags", "notes",
]

_COMPACT_FIELDS = [
    "id", "name", "title", "status", "score",
    "company", "program", "tier", "created_at",
]

_MINIMAL_FIELDS = [
    "id", "name", "status", "score",
]


# =========================================
# RESPONSIVE API LAYER
# =========================================

class ResponsiveAPILayer:
    """Adapts API responses based on client device type,
    network conditions, and bandwidth constraints.
    """

    def __init__(self):
        self._profiles: Dict[str, ClientProfile] = {}
        self._request_count = 0
        self._total_bytes_saved = 0
        logger.info("ResponsiveAPILayer initialized")

    # ----- client profiles -----

    def detect_client(self, user_agent: str = "", screen_width: int = 0,
                      network_hint: str = "") -> ClientProfile:
        """Detect client capabilities from hints."""
        import hashlib
        pid = f"client_{hashlib.md5(f'{user_agent}:{screen_width}:{time.time()}'.encode()).hexdigest()[:12]}"

        device = self._detect_device(user_agent, screen_width)
        network = self._detect_network(network_hint)
        fmt = _FORMAT_BY_NETWORK.get(network, ResponseFormat.FULL)

        # Override format for small devices
        if device == DeviceType.WATCH:
            fmt = ResponseFormat.MINIMAL
        elif device == DeviceType.MOBILE and network in (NetworkQuality.FAIR, NetworkQuality.POOR):
            fmt = ResponseFormat.MINIMAL

        max_payload = {
            DeviceType.DESKTOP: 500,
            DeviceType.TABLET: 300,
            DeviceType.MOBILE: 150,
            DeviceType.WATCH: 50,
            DeviceType.API_CLIENT: 1000,
        }.get(device, 500)

        profile = ClientProfile(
            profile_id=pid,
            device_type=device,
            network_quality=network,
            screen_width=screen_width or 1920,
            preferred_format=fmt,
            max_payload_kb=max_payload,
        )
        self._profiles[pid] = profile
        return profile

    def get_profile(self, profile_id: str) -> Optional[ClientProfile]:
        return self._profiles.get(profile_id)

    # ----- response adaptation -----

    def adapt_response(self, data: List[Dict[str, Any]], profile: Optional[ClientProfile] = None) -> Dict[str, Any]:
        """Adapt a list of records based on client profile."""
        self._request_count += 1

        if profile is None:
            profile = ClientProfile(profile_id="default")

        fmt = profile.preferred_format
        page_size = _DEFAULT_PAGE_SIZES.get(profile.device_type, 50)

        # Select fields based on format
        if fmt == ResponseFormat.FULL:
            fields = _FULL_FIELDS
        elif fmt == ResponseFormat.COMPACT:
            fields = _COMPACT_FIELDS
        elif fmt == ResponseFormat.MINIMAL:
            fields = _MINIMAL_FIELDS
        else:
            fields = _FULL_FIELDS

        # Paginate
        paginated = data[:page_size]

        # Filter fields
        adapted = []
        for record in paginated:
            adapted_record = {k: v for k, v in record.items() if k in fields}
            adapted.append(adapted_record)

        # Compute sizes (estimated)
        original_size = len(str(data)) * 2
        adapted_size = len(str(adapted)) * 2
        ratio = adapted_size / max(original_size, 1)
        bytes_saved = max(0, original_size - adapted_size)
        self._total_bytes_saved += bytes_saved

        meta = AdaptiveResponse(
            original_size_bytes=original_size,
            adapted_size_bytes=adapted_size,
            format_used=fmt,
            fields_included=len(fields),
            fields_omitted=len(_FULL_FIELDS) - len(fields),
            page_size_used=page_size,
            compression_ratio=ratio,
        )

        return {
            "data": adapted,
            "total": len(data),
            "page_size": page_size,
            "adaptation": meta.to_dict(),
        }

    def get_recommended_page_size(self, device_type: DeviceType) -> int:
        return _DEFAULT_PAGE_SIZES.get(device_type, 50)

    def get_fields_for_format(self, fmt: ResponseFormat) -> List[str]:
        if fmt == ResponseFormat.FULL:
            return list(_FULL_FIELDS)
        elif fmt == ResponseFormat.COMPACT:
            return list(_COMPACT_FIELDS)
        elif fmt == ResponseFormat.MINIMAL:
            return list(_MINIMAL_FIELDS)
        return list(_FULL_FIELDS)

    # ----- detection helpers -----

    @staticmethod
    def _detect_device(user_agent: str, screen_width: int) -> DeviceType:
        ua = user_agent.lower()
        # Check API clients first (before screen_width checks)
        if "bot" in ua or "api" in ua or "curl" in ua:
            return DeviceType.API_CLIENT
        if "watch" in ua or (0 < screen_width < 300):
            return DeviceType.WATCH
        if "mobile" in ua or "android" in ua or (0 < screen_width < 768):
            return DeviceType.MOBILE
        if "tablet" in ua or "ipad" in ua or (768 <= screen_width < 1024):
            return DeviceType.TABLET
        return DeviceType.DESKTOP

    @staticmethod
    def _detect_network(hint: str) -> NetworkQuality:
        hint = hint.lower()
        mapping = {
            "4g": NetworkQuality.EXCELLENT,
            "wifi": NetworkQuality.EXCELLENT,
            "3g": NetworkQuality.FAIR,
            "2g": NetworkQuality.POOR,
            "slow": NetworkQuality.POOR,
            "offline": NetworkQuality.OFFLINE,
        }
        return mapping.get(hint, NetworkQuality.GOOD)

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_profiles": len(self._profiles),
            "total_requests": self._request_count,
            "total_bytes_saved": self._total_bytes_saved,
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[ResponsiveAPILayer] = None


def get_responsive_api() -> ResponsiveAPILayer:
    global _instance
    if _instance is None:
        _instance = ResponsiveAPILayer()
    return _instance
