"""Phase 58A — PWA Manager.

Service worker lifecycle, manifest generation, offline storage
management, and install prompt handling for the BD Intelligence PWA.
"""

from __future__ import annotations

import hashlib
import logging
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

class CacheStrategy(Enum):
    CACHE_FIRST = "cache_first"
    NETWORK_FIRST = "network_first"
    STALE_WHILE_REVALIDATE = "stale_while_revalidate"
    NETWORK_ONLY = "network_only"
    CACHE_ONLY = "cache_only"


class SyncStatus(Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    CONFLICT = "conflict"
    FAILED = "failed"


@dataclass
class OfflineResource:
    """A resource cached for offline use."""
    resource_id: str
    url: str
    cache_strategy: CacheStrategy = CacheStrategy.CACHE_FIRST
    size_bytes: int = 0
    last_cached: float = field(default_factory=time.time)
    version: str = "1.0"
    etag: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "url": self.url,
            "cache_strategy": self.cache_strategy.value,
            "size_bytes": self.size_bytes,
            "last_cached": self.last_cached,
            "version": self.version,
            "etag": self.etag,
        }


@dataclass
class SyncQueueItem:
    """An offline action queued for sync when back online."""
    item_id: str
    action: str  # e.g., "create_contact", "update_program"
    payload: Dict[str, Any] = field(default_factory=dict)
    status: SyncStatus = SyncStatus.PENDING
    created_at: float = field(default_factory=time.time)
    synced_at: float = 0.0
    retries: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "action": self.action,
            "payload": self.payload,
            "status": self.status.value,
            "created_at": self.created_at,
            "synced_at": self.synced_at,
            "retries": self.retries,
        }


@dataclass
class AppManifest:
    """PWA Web App Manifest."""
    name: str = "BD Intelligence Hub"
    short_name: str = "BD Hub"
    description: str = "PTS BD Intelligence System for federal defense programs"
    start_url: str = "/"
    display: str = "standalone"
    background_color: str = "#1a1a2e"
    theme_color: str = "#16213e"
    orientation: str = "any"
    icons: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if not self.icons:
            self.icons = [
                {"src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
            ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "short_name": self.short_name,
            "description": self.description,
            "start_url": self.start_url,
            "display": self.display,
            "background_color": self.background_color,
            "theme_color": self.theme_color,
            "orientation": self.orientation,
            "icons": self.icons,
        }


# =========================================
# PWA MANAGER
# =========================================

class PWAManager:
    """Manages PWA lifecycle including service worker registration,
    offline caching, sync queue, and manifest generation.
    """

    def __init__(self):
        self._resources: Dict[str, OfflineResource] = {}
        self._sync_queue: List[SyncQueueItem] = []
        self._manifest = AppManifest()
        self._sw_version = "1.0.0"
        self._is_online = True
        self._register_default_resources()
        logger.info("PWAManager initialized with %d cached resources", len(self._resources))

    def _register_default_resources(self) -> None:
        defaults = [
            OfflineResource(resource_id="app_shell", url="/", cache_strategy=CacheStrategy.CACHE_FIRST, size_bytes=15000),
            OfflineResource(resource_id="api_contacts", url="/api/v2/contacts", cache_strategy=CacheStrategy.NETWORK_FIRST, size_bytes=50000),
            OfflineResource(resource_id="api_programs", url="/api/v2/programs", cache_strategy=CacheStrategy.STALE_WHILE_REVALIDATE, size_bytes=30000),
            OfflineResource(resource_id="static_css", url="/assets/app.css", cache_strategy=CacheStrategy.CACHE_FIRST, size_bytes=8000),
            OfflineResource(resource_id="static_js", url="/assets/app.js", cache_strategy=CacheStrategy.CACHE_FIRST, size_bytes=120000),
            OfflineResource(resource_id="search_index", url="/api/search/index", cache_strategy=CacheStrategy.STALE_WHILE_REVALIDATE, size_bytes=200000),
        ]
        for r in defaults:
            self._resources[r.resource_id] = r

    # ----- resource management -----

    def get_resource(self, resource_id: str) -> Optional[OfflineResource]:
        return self._resources.get(resource_id)

    def list_resources(self) -> List[OfflineResource]:
        return list(self._resources.values())

    def add_resource(self, url: str, strategy: CacheStrategy = CacheStrategy.CACHE_FIRST, size_bytes: int = 0) -> OfflineResource:
        rid = f"res_{hashlib.md5(url.encode()).hexdigest()[:12]}"
        resource = OfflineResource(resource_id=rid, url=url, cache_strategy=strategy, size_bytes=size_bytes)
        self._resources[rid] = resource
        return resource

    def remove_resource(self, resource_id: str) -> bool:
        if resource_id in self._resources:
            del self._resources[resource_id]
            return True
        return False

    # ----- sync queue -----

    def queue_sync(self, action: str, payload: Dict[str, Any] = None) -> SyncQueueItem:
        """Add an action to the offline sync queue."""
        item = SyncQueueItem(
            item_id=f"sync_{uuid.uuid4().hex[:12]}",
            action=action,
            payload=payload or {},
        )
        self._sync_queue.append(item)
        logger.info("Queued sync action: %s (%s)", action, item.item_id)
        return item

    def process_sync_queue(self) -> Dict[str, int]:
        """Process all pending sync items (simulated)."""
        synced = 0
        failed = 0
        for item in self._sync_queue:
            if item.status == SyncStatus.PENDING:
                item.status = SyncStatus.SYNCED
                item.synced_at = time.time()
                synced += 1
        return {"synced": synced, "failed": failed, "remaining": self.pending_sync_count()}

    def pending_sync_count(self) -> int:
        return sum(1 for item in self._sync_queue if item.status == SyncStatus.PENDING)

    def get_sync_queue(self) -> List[SyncQueueItem]:
        return list(self._sync_queue)

    # ----- manifest -----

    def get_manifest(self) -> AppManifest:
        return self._manifest

    def update_manifest(self, **kwargs: Any) -> AppManifest:
        for key, value in kwargs.items():
            if hasattr(self._manifest, key):
                setattr(self._manifest, key, value)
        return self._manifest

    # ----- service worker -----

    def get_sw_version(self) -> str:
        return self._sw_version

    def set_online(self, online: bool) -> None:
        self._is_online = online

    def is_online(self) -> bool:
        return self._is_online

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        total_cache_bytes = sum(r.size_bytes for r in self._resources.values())
        return {
            "total_resources": len(self._resources),
            "total_cache_bytes": total_cache_bytes,
            "sync_queue_size": len(self._sync_queue),
            "pending_syncs": self.pending_sync_count(),
            "sw_version": self._sw_version,
            "is_online": self._is_online,
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[PWAManager] = None


def get_pwa_manager() -> PWAManager:
    global _instance
    if _instance is None:
        _instance = PWAManager()
    return _instance
