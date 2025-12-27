"""
Base repository class with common CRUD operations.
"""

from typing import Generic, TypeVar, Type, Sequence
from uuid import UUID

from sqlalchemy import select, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing common database operations.

    All repositories inherit from this class to get standard CRUD operations
    with automatic session management.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, obj: ModelType) -> ModelType:
        """Create a new object."""
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def get_by_id(self, obj_id: UUID) -> ModelType | None:
        """Get object by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[ModelType]:
        """Get all objects with pagination."""
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def update(self, obj: ModelType) -> ModelType:
        """Update an existing object."""
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj_id: UUID) -> bool:
        """Delete an object by ID."""
        result = await self.session.execute(
            sql_delete(self.model).where(self.model.id == obj_id)
        )
        await self.session.flush()
        return result.rowcount > 0
