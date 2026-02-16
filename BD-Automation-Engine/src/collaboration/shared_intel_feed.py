"""Phase 50A — Shared Intelligence Feed.

A real-time intelligence feed where BD reps can post, react to, and
discuss intelligence items. Supports typed entries (win_intel, competitor_move,
market_shift, contact_update, opportunity_alert), priority tagging,
and @-mention notifications.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================


class IntelType(str, Enum):
    WIN_INTEL = "win_intel"
    COMPETITOR_MOVE = "competitor_move"
    MARKET_SHIFT = "market_shift"
    CONTACT_UPDATE = "contact_update"
    OPPORTUNITY_ALERT = "opportunity_alert"
    TEAM_UPDATE = "team_update"


class IntelPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class IntelReaction:
    """A reaction (emoji) on an intel item."""

    user_id: str
    user_name: str
    emoji: str  # e.g., "thumbsup", "fire", "eyes", "warning"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "emoji": self.emoji,
            "created_at": self.created_at,
        }


@dataclass
class IntelComment:
    """A comment on an intel item."""

    comment_id: str
    user_id: str
    user_name: str
    text: str
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "text": self.text,
            "created_at": self.created_at,
        }


@dataclass
class IntelItem:
    """A single intelligence feed entry."""

    item_id: str
    intel_type: IntelType
    priority: IntelPriority
    title: str
    body: str
    author_id: str
    author_name: str
    program: str = ""
    tags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)  # @user_ids
    reactions: List[IntelReaction] = field(default_factory=list)
    comments: List[IntelComment] = field(default_factory=list)
    pinned: bool = False
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.utcnow().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "intel_type": self.intel_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "body": self.body,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "program": self.program,
            "tags": self.tags,
            "mentions": self.mentions,
            "reactions": [r.to_dict() for r in self.reactions],
            "comments": [c.to_dict() for c in self.comments],
            "reaction_count": len(self.reactions),
            "comment_count": len(self.comments),
            "pinned": self.pinned,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# =========================================
# SHARED INTELLIGENCE FEED
# =========================================


class SharedIntelligenceFeed:
    """Real-time shared intelligence feed for BD teams.

    Features:
    - Typed entries (win intel, competitor moves, market shifts, etc.)
    - Priority tagging (critical → low)
    - Reactions and threaded comments
    - @-mention notifications
    - Pin important items
    - Program-scoped filtering
    """

    def __init__(self):
        self._items: Dict[str, IntelItem] = {}
        self._item_counter = 0
        self._comment_counter = 0
        self._seed_intel()
        logger.info(
            "SharedIntelligenceFeed initialized with %d seed items", len(self._items)
        )

    def _seed_intel(self):
        """Pre-populate with realistic intelligence items."""
        seeds = [
            (
                IntelType.WIN_INTEL,
                IntelPriority.HIGH,
                "DCGS-A Task Order 3 win confirmed",
                "We secured TO3 for DCGS-A sustainment at Fort Meade. "
                "$12M ceiling over 3 years. Key differentiator was our cleared workforce pool.",
                "rep_01",
                "Sarah Mitchell",
                "DCGS-A",
                ["win", "army"],
            ),
            (
                IntelType.COMPETITOR_MOVE,
                IntelPriority.CRITICAL,
                "Leidos ramping up JADC2 hiring in NCR",
                "Multiple job postings spotted for Leidos JADC2 positions in Arlington and Ft. Belvoir. "
                "Suggests they may be bidding on the upcoming JADC2 IDIQ.",
                "rep_02",
                "James Chen",
                "JADC2",
                ["competitor", "leidos"],
            ),
            (
                IntelType.MARKET_SHIFT,
                IntelPriority.NORMAL,
                "DoD FY26 budget increases ISR funding",
                "ISR/SIGINT line items show 15% increase in FY26 PB. "
                "DCGS modernization specifically called out. Good news for our pipeline.",
                "rep_03",
                "Patricia Okafor",
                "DCGS-A",
                ["budget", "isr"],
            ),
            (
                IntelType.CONTACT_UPDATE,
                IntelPriority.HIGH,
                "Key decision maker retiring from Navy PEO IWS",
                "CAPT Williams retiring in 90 days. His replacement (CAPT Rodriguez) "
                "comes from PEO C4I — could shift Navy DCGS-N priorities.",
                "rep_04",
                "David Reyes",
                "DCGS-N",
                ["navy", "leadership"],
            ),
            (
                IntelType.OPPORTUNITY_ALERT,
                IntelPriority.CRITICAL,
                "New RFI for AF DCGS Block 5 modernization",
                "Air Force released RFI for DCGS Block 5 mod. "
                "Responses due in 30 days. Our TITAN experience is directly relevant.",
                "rep_05",
                "Laura Kim",
                "AF DCGS",
                ["rfi", "air-force"],
            ),
        ]

        for itype, prio, title, body, aid, aname, prog, tags in seeds:
            self._item_counter += 1
            item_id = f"intel_{self._item_counter:04d}"
            self._items[item_id] = IntelItem(
                item_id=item_id,
                intel_type=itype,
                priority=prio,
                title=title,
                body=body,
                author_id=aid,
                author_name=aname,
                program=prog,
                tags=tags,
            )

    # ----- post / manage -----

    def post_intel(
        self,
        intel_type: IntelType,
        priority: IntelPriority,
        title: str,
        body: str,
        author_id: str,
        author_name: str,
        program: str = "",
        tags: Optional[List[str]] = None,
        mentions: Optional[List[str]] = None,
    ) -> IntelItem:
        """Post a new intelligence item to the feed."""
        self._item_counter += 1
        item_id = f"intel_{self._item_counter:04d}"

        item = IntelItem(
            item_id=item_id,
            intel_type=intel_type,
            priority=priority,
            title=title,
            body=body,
            author_id=author_id,
            author_name=author_name,
            program=program,
            tags=tags or [],
            mentions=mentions or [],
        )
        self._items[item_id] = item
        return item

    def get_item(self, item_id: str) -> Optional[IntelItem]:
        return self._items.get(item_id)

    def delete_item(self, item_id: str) -> bool:
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False

    def pin_item(self, item_id: str) -> bool:
        item = self._items.get(item_id)
        if item:
            item.pinned = True
            return True
        return False

    def unpin_item(self, item_id: str) -> bool:
        item = self._items.get(item_id)
        if item:
            item.pinned = False
            return True
        return False

    # ----- reactions -----

    def add_reaction(
        self,
        item_id: str,
        user_id: str,
        user_name: str,
        emoji: str,
    ) -> bool:
        item = self._items.get(item_id)
        if not item:
            return False
        # Prevent duplicate reactions from same user with same emoji
        existing = [
            r for r in item.reactions if r.user_id == user_id and r.emoji == emoji
        ]
        if existing:
            return False
        item.reactions.append(
            IntelReaction(
                user_id=user_id,
                user_name=user_name,
                emoji=emoji,
            )
        )
        return True

    # ----- comments -----

    def add_comment(
        self,
        item_id: str,
        user_id: str,
        user_name: str,
        text: str,
    ) -> Optional[IntelComment]:
        item = self._items.get(item_id)
        if not item:
            return None
        self._comment_counter += 1
        comment = IntelComment(
            comment_id=f"icomment_{self._comment_counter}",
            user_id=user_id,
            user_name=user_name,
            text=text,
        )
        item.comments.append(comment)
        item.updated_at = datetime.utcnow().isoformat()
        return comment

    # ----- feed queries -----

    def get_feed(
        self,
        intel_type: Optional[IntelType] = None,
        priority: Optional[IntelPriority] = None,
        program: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[IntelItem]:
        """Get the intelligence feed with optional filters."""
        items = list(self._items.values())
        if intel_type:
            items = [i for i in items if i.intel_type == intel_type]
        if priority:
            items = [i for i in items if i.priority == priority]
        if program:
            items = [i for i in items if i.program.lower() == program.lower()]
        if tag:
            items = [i for i in items if tag.lower() in [t.lower() for t in i.tags]]

        # Pinned first, then by created_at descending
        items.sort(key=lambda i: (not i.pinned, i.created_at), reverse=False)
        # Actually: pinned first (pinned=True → not pinned=False → sort ascending so False < True)
        # We want pinned first, then most recent first
        items.sort(key=lambda i: (0 if i.pinned else 1, i.created_at), reverse=False)
        # This gives pinned first (0 < 1), but oldest first within groups
        # Let's just sort manually
        pinned = [i for i in items if i.pinned]
        unpinned = [i for i in items if not i.pinned]
        pinned.sort(key=lambda i: i.created_at, reverse=True)
        unpinned.sort(key=lambda i: i.created_at, reverse=True)
        items = pinned + unpinned

        return items[:limit]

    def get_mentions(self, user_id: str) -> List[IntelItem]:
        """Get items that @-mention a specific user."""
        return [i for i in self._items.values() if user_id in i.mentions]

    def search_feed(self, query: str) -> List[IntelItem]:
        """Simple text search across titles and bodies."""
        lower = query.lower()
        results = []
        for item in self._items.values():
            if lower in item.title.lower() or lower in item.body.lower():
                results.append(item)
        return sorted(results, key=lambda i: i.created_at, reverse=True)

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}
        for item in self._items.values():
            by_type[item.intel_type.value] = by_type.get(item.intel_type.value, 0) + 1
            by_priority[item.priority.value] = (
                by_priority.get(item.priority.value, 0) + 1
            )

        return {
            "total_items": len(self._items),
            "by_type": by_type,
            "by_priority": by_priority,
            "total_reactions": sum(len(i.reactions) for i in self._items.values()),
            "total_comments": sum(len(i.comments) for i in self._items.values()),
            "pinned_count": sum(1 for i in self._items.values() if i.pinned),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[SharedIntelligenceFeed] = None


def get_intel_feed() -> SharedIntelligenceFeed:
    global _instance
    if _instance is None:
        _instance = SharedIntelligenceFeed()
    return _instance
