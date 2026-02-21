"""
BD Automation Engine - Database Layer Library.

Generic SQLAlchemy base model, session factory, repository pattern,
and reusable mixins extracted from Engine8_Knowledge/db/.
"""

__version__ = "0.1.0"

from libs.db_layer.base import Base, SessionManager, TimestampMixin, SoftDeleteMixin
from libs.db_layer.repository import BaseRepository

__all__ = [
    "Base",
    "SessionManager",
    "TimestampMixin",
    "SoftDeleteMixin",
    "BaseRepository",
]
