"""
User repository for authentication and user management.
"""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.models.user import User
from smartbook.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User operations (no tenant isolation - users are global)."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """
        Get user by email address.

        Args:
            email: User email address

        Returns:
            User object or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_oauth_provider_id(
        self,
        provider: str,
        provider_id: str
    ) -> User | None:
        """
        Get user by OAuth provider and provider user ID.

        Args:
            provider: OAuth provider name (e.g., 'google')
            provider_id: OAuth provider user ID (e.g., Google sub claim)

        Returns:
            User object or None if not found
        """
        result = await self.session.execute(
            select(User).where(
                User.oauth_provider == provider,
                User.oauth_provider_id == provider_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_users(self) -> Sequence[User]:
        """Get all active users."""
        result = await self.session.execute(
            select(User).where(User.is_active == True).order_by(User.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_role(self, role: str) -> Sequence[User]:
        """
        Get all users with a specific role.

        Args:
            role: User role ('admin' or 'staff')

        Returns:
            List of users with the specified role
        """
        result = await self.session.execute(
            select(User).where(User.role == role).order_by(User.created_at.desc())
        )
        return result.scalars().all()

    async def deactivate_user(self, user_id: UUID) -> User | None:
        """
        Deactivate a user account (soft delete).

        Args:
            user_id: ID of the user to deactivate

        Returns:
            Updated user object or None if not found
        """
        user = await self.get_by_id(user_id)
        if user:
            user.is_active = False
            await self.update(user)
        return user

    async def activate_user(self, user_id: UUID) -> User | None:
        """
        Activate a user account.

        Args:
            user_id: ID of the user to activate

        Returns:
            Updated user object or None if not found
        """
        user = await self.get_by_id(user_id)
        if user:
            user.is_active = True
            await self.update(user)
        return user
