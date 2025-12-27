"""
Guest repository with booking-scoped operations.
"""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.models.guest import Guest
from smartbook.domain.enums import GuestRole
from smartbook.repositories.base import BaseRepository


class GuestRepository(BaseRepository[Guest]):
    """Repository for Guest operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Guest, session)

    async def create_guest(self, guest_data: dict) -> Guest:
        """Create a new guest for a booking."""
        guest = Guest(**guest_data)
        return await self.create(guest)

    async def get_by_booking_id(self, booking_id: UUID) -> Sequence[Guest]:
        """Get all guests for a specific booking."""
        result = await self.session.execute(
            select(Guest).where(Guest.booking_id == booking_id)
        )
        return result.scalars().all()

    async def get_leader_for_booking(self, booking_id: UUID) -> Guest | None:
        """Get the group/family leader for a booking."""
        result = await self.session.execute(
            select(Guest).where(
                Guest.booking_id == booking_id,
                Guest.role == GuestRole.LEADER,
            )
        )
        return result.scalar_one_or_none()

    async def count_guests_for_booking(self, booking_id: UUID) -> int:
        """Count total guests entered for a booking."""
        result = await self.session.execute(
            select(func.count(Guest.id)).where(Guest.booking_id == booking_id)
        )
        return result.scalar_one()

    async def count_exempt_guests(self, booking_id: UUID) -> int:
        """Count tax-exempt guests for a booking."""
        result = await self.session.execute(
            select(func.count(Guest.id)).where(
                Guest.booking_id == booking_id,
                Guest.is_tax_exempt == True,  # noqa: E712
            )
        )
        return result.scalar_one()

    async def bulk_create_guests(self, guests_data: list[dict]) -> Sequence[Guest]:
        """Bulk create multiple guests (useful for large groups)."""
        guests = [Guest(**guest_data) for guest_data in guests_data]
        for guest in guests:
            self.session.add(guest)
        await self.session.flush()
        for guest in guests:
            await self.session.refresh(guest)
        return guests

    async def validate_guest_completeness(self, booking_id: UUID) -> dict:
        """
        Validate that all required guest data is complete.

        Returns:
            Dict with validation results (has_leader, total_guests, etc.)
        """
        guests = await self.get_by_booking_id(booking_id)
        leader = await self.get_leader_for_booking(booking_id)

        return {
            "has_leader": leader is not None,
            "total_guests": len(guests),
            "missing_fields": self._check_missing_fields(guests, leader),
            "is_complete": leader is not None and len(guests) > 0,
        }

    def _check_missing_fields(
        self,
        guests: Sequence[Guest],
        leader: Guest | None,
    ) -> list[str]:
        """Check for missing required fields across all guests."""
        missing = []

        if not leader:
            missing.append("No group leader defined")
        elif not all([
            leader.document_type,
            leader.document_number,
            leader.document_issuing_authority,
        ]):
            missing.append("Leader missing document details")

        for guest in guests:
            if not all([guest.first_name, guest.last_name, guest.date_of_birth]):
                missing.append(f"Guest {guest.id}: Missing TULPS minimum data")

        return missing
