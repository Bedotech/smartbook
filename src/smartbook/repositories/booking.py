"""
Booking repository with tenant-scoped operations.
"""

from datetime import date, datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.models.booking import Booking
from smartbook.domain.enums import BookingStatus
from smartbook.repositories.base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    """Repository for Booking operations with property isolation."""

    def __init__(self, session: AsyncSession, property_id: UUID):
        super().__init__(Booking, session)
        self.property_id = property_id

    async def create_booking(
        self,
        booking_data: dict,
        magic_link_token: str,
        token_expires_at: datetime,
    ) -> Booking:
        """
        Create a new booking with automatic property_id injection.

        Args:
            booking_data: Dictionary of booking fields
            magic_link_token: Unique token for guest portal access
            token_expires_at: Token expiration datetime

        Returns:
            Created booking object
        """
        booking = Booking(
            **booking_data,
            property_id=self.property_id,
            magic_link_token=magic_link_token,
            token_expires_at=token_expires_at,
            status=BookingStatus.PENDING,
        )
        return await self.create(booking)

    async def get_by_id(self, booking_id: UUID) -> Booking | None:
        """Get booking by ID with tenant isolation."""
        result = await self.session.execute(
            select(Booking).where(
                Booking.id == booking_id,
                Booking.property_id == self.property_id,  # Tenant isolation
            )
        )
        return result.scalar_one_or_none()

    async def get_by_magic_link(self, token: str) -> Booking | None:
        """
        Get booking by magic link token.

        Note: This does NOT require property_id since the token itself
        is the authentication mechanism for guests.
        """
        result = await self.session.execute(
            select(Booking).where(Booking.magic_link_token == token)
        )
        return result.scalar_one_or_none()

    async def get_all_for_tenant(
        self,
        limit: int = 100,
        offset: int = 0,
        status: BookingStatus | None = None,
    ) -> Sequence[Booking]:
        """Get all bookings for the current tenant with optional status filter."""
        query = select(Booking).where(Booking.property_id == self.property_id)

        if status:
            query = query.where(Booking.status == status)

        query = query.limit(limit).offset(offset).order_by(Booking.check_in_date.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_bookings_by_date_range(
        self,
        start_date: date,
        end_date: date,
    ) -> Sequence[Booking]:
        """Get bookings within a date range for the current tenant."""
        result = await self.session.execute(
            select(Booking).where(
                Booking.property_id == self.property_id,
                Booking.check_in_date >= start_date,
                Booking.check_in_date <= end_date,
            ).order_by(Booking.check_in_date)
        )
        return result.scalars().all()

    async def update_status(
        self,
        booking_id: UUID,
        new_status: BookingStatus,
    ) -> Booking | None:
        """Update booking status with tenant isolation."""
        booking = await self.get_by_id(booking_id)
        if booking:
            booking.status = new_status
            return await self.update(booking)
        return None

    async def count_bookings_by_status(self, status: BookingStatus) -> int:
        """Count bookings by status for the current tenant."""
        result = await self.session.execute(
            select(func.count(Booking.id)).where(
                Booking.property_id == self.property_id,
                Booking.status == status,
            )
        )
        return result.scalar_one()
