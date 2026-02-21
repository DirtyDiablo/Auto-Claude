"""
Generic base repository with CRUD operations.

Extracted from Engine8_Knowledge/db/repository.py.  Engine-specific
repositories should subclass ``BaseRepository[T]`` and set ``model``.
"""

from __future__ import annotations

from typing import Generic, List, Optional, Type, TypeVar

import structlog
from sqlalchemy import func as sa_func, select
from sqlalchemy.orm import Session

from libs.db_layer.base import Base

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic CRUD repository backed by a SQLAlchemy session.

    Subclasses must set ``model`` to the ORM class they manage::

        class ContactRepository(BaseRepository[Contact]):
            model = Contact
    """

    model: Type[T]

    def __init__(self, session: Session) -> None:
        self.session = session

    # -- Create --------------------------------------------------------

    def create(self, entity: T) -> T:
        """Add a new entity and flush to obtain its id."""
        self.session.add(entity)
        self.session.flush()
        return entity

    def create_many(self, entities: List[T]) -> List[T]:
        """Bulk-add entities and flush."""
        self.session.add_all(entities)
        self.session.flush()
        return entities

    # -- Read ----------------------------------------------------------

    def get_by_id(self, entity_id) -> Optional[T]:
        """Fetch a single entity by primary key."""
        return self.session.get(self.model, entity_id)

    def list_all(self, *, offset: int = 0, limit: int = 100) -> List[T]:
        """Return a paginated list of entities."""
        stmt = select(self.model).offset(offset).limit(limit)
        return list(self.session.scalars(stmt).all())

    def count(self) -> int:
        """Return the total number of entities."""
        stmt = select(sa_func.count()).select_from(self.model)
        return self.session.scalar(stmt) or 0

    # -- Update --------------------------------------------------------

    def update(self, entity: T, **kwargs) -> T:
        """Update an entity with keyword arguments."""
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        self.session.flush()
        return entity

    # -- Delete --------------------------------------------------------

    def delete(self, entity: T) -> None:
        """Remove an entity from the session."""
        self.session.delete(entity)
        self.session.flush()

    # -- Soft-delete helpers (for entities with SoftDeleteMixin) --------

    def soft_delete(self, entity: T) -> T:
        """Soft-delete an entity (requires SoftDeleteMixin)."""
        if not hasattr(entity, "soft_delete"):
            raise TypeError(
                f"{type(entity).__name__} does not support soft-delete. "
                "Add SoftDeleteMixin to the model."
            )
        entity.soft_delete()
        self.session.flush()
        return entity

    def restore(self, entity: T) -> T:
        """Restore a soft-deleted entity (requires SoftDeleteMixin)."""
        if not hasattr(entity, "restore"):
            raise TypeError(
                f"{type(entity).__name__} does not support restore. "
                "Add SoftDeleteMixin to the model."
            )
        entity.restore()
        self.session.flush()
        return entity
