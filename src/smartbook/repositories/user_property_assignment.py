"""
UserPropertyAssignment repository for managing user-property relationships.
"""

from datetime import datetime
from typing import Sequence
from uuid import UUID, uuid4

from sqlalchemy import select, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.models.user_property_assignment import UserPropertyAssignment
from smartbook.repositories.base import BaseRepository


class UserPropertyAssignmentRepository(BaseRepository[UserPropertyAssignment]):
    """
    Repository for UserPropertyAssignment operations.

    Manages the many-to-many relationship between users and properties.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(UserPropertyAssignment, session)

    async def get_property_ids_for_user(self, user_id: UUID) -> list[UUID]:
        """
        Get all property IDs assigned to a user.

        Args:
            user_id: ID of the user

        Returns:
            List of property UUIDs
        """
        result = await self.session.execute(
            select(UserPropertyAssignment.property_id).where(
                UserPropertyAssignment.user_id == user_id
            )
        )
        return [row[0] for row in result.all()]

    async def get_user_ids_for_property(self, property_id: UUID) -> list[UUID]:
        """
        Get all user IDs assigned to a property.

        Args:
            property_id: ID of the property

        Returns:
            List of user UUIDs
        """
        result = await self.session.execute(
            select(UserPropertyAssignment.user_id).where(
                UserPropertyAssignment.property_id == property_id
            )
        )
        return [row[0] for row in result.all()]

    async def get_assignments_for_user(
        self,
        user_id: UUID
    ) -> Sequence[UserPropertyAssignment]:
        """
        Get all property assignments for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of UserPropertyAssignment objects
        """
        result = await self.session.execute(
            select(UserPropertyAssignment)
            .where(UserPropertyAssignment.user_id == user_id)
            .order_by(UserPropertyAssignment.assigned_at.desc())
        )
        return result.scalars().all()

    async def get_assignments_for_property(
        self,
        property_id: UUID
    ) -> Sequence[UserPropertyAssignment]:
        """
        Get all user assignments for a property.

        Args:
            property_id: ID of the property

        Returns:
            List of UserPropertyAssignment objects
        """
        result = await self.session.execute(
            select(UserPropertyAssignment)
            .where(UserPropertyAssignment.property_id == property_id)
            .order_by(UserPropertyAssignment.assigned_at.desc())
        )
        return result.scalars().all()

    async def assign_property_to_user(
        self,
        user_id: UUID,
        property_id: UUID,
        assigned_by_user_id: UUID | None = None,
    ) -> UserPropertyAssignment:
        """
        Assign a property to a user.

        Args:
            user_id: ID of the user
            property_id: ID of the property
            assigned_by_user_id: ID of the user who created this assignment (optional)

        Returns:
            Created UserPropertyAssignment object

        Raises:
            IntegrityError: If assignment already exists (unique constraint violation)
        """
        assignment = UserPropertyAssignment(
            id=uuid4(),
            user_id=user_id,
            property_id=property_id,
            assigned_at=datetime.utcnow(),
            assigned_by_user_id=assigned_by_user_id,
        )
        return await self.create(assignment)

    async def remove_assignment(
        self,
        user_id: UUID,
        property_id: UUID
    ) -> bool:
        """
        Remove a specific user-property assignment.

        Args:
            user_id: ID of the user
            property_id: ID of the property

        Returns:
            True if assignment was removed, False if not found
        """
        result = await self.session.execute(
            sql_delete(UserPropertyAssignment).where(
                UserPropertyAssignment.user_id == user_id,
                UserPropertyAssignment.property_id == property_id,
            )
        )
        await self.session.flush()
        return result.rowcount > 0

    async def remove_all_for_user(self, user_id: UUID) -> int:
        """
        Remove all property assignments for a user.

        Args:
            user_id: ID of the user

        Returns:
            Number of assignments removed
        """
        result = await self.session.execute(
            sql_delete(UserPropertyAssignment).where(
                UserPropertyAssignment.user_id == user_id
            )
        )
        await self.session.flush()
        return result.rowcount

    async def remove_all_for_property(self, property_id: UUID) -> int:
        """
        Remove all user assignments for a property.

        Args:
            property_id: ID of the property

        Returns:
            Number of assignments removed
        """
        result = await self.session.execute(
            sql_delete(UserPropertyAssignment).where(
                UserPropertyAssignment.property_id == property_id
            )
        )
        await self.session.flush()
        return result.rowcount

    async def is_user_assigned_to_property(
        self,
        user_id: UUID,
        property_id: UUID
    ) -> bool:
        """
        Check if a user is assigned to a property.

        Args:
            user_id: ID of the user
            property_id: ID of the property

        Returns:
            True if assignment exists, False otherwise
        """
        result = await self.session.execute(
            select(UserPropertyAssignment).where(
                UserPropertyAssignment.user_id == user_id,
                UserPropertyAssignment.property_id == property_id,
            )
        )
        return result.scalar_one_or_none() is not None
