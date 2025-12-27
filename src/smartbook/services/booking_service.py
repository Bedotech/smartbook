"""
Booking Service with status management and workflow orchestration.

Manages the complete booking lifecycle from creation to ROS1000 sync.
"""

from datetime import datetime, date
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.enums import BookingStatus, BookingType
from smartbook.domain.models.booking import Booking
from smartbook.domain.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingProgressResponse,
)
from smartbook.repositories.booking import BookingRepository
from smartbook.repositories.guest import GuestRepository
from smartbook.services.magic_link import MagicLinkService


class BookingServiceError(Exception):
    """Raised when booking service operations fail."""

    pass


class BookingService:
    """
    Service for booking management and workflow orchestration.

    Handles the complete booking lifecycle:
    1. Creation with magic link generation
    2. Progress tracking (e.g., "12/50 Guests Entered")
    3. Status transitions (pending → in_progress → complete → synced)
    4. Validation before ROS1000 transmission
    """

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.booking_repo = BookingRepository(session, tenant_id)
        self.guest_repo = GuestRepository(session)
        self.magic_link_service = MagicLinkService()

    async def create_booking(
        self,
        booking_data: BookingCreate,
    ) -> BookingResponse:
        """
        Create a new booking with automatic magic link generation.

        Args:
            booking_data: Booking creation data

        Returns:
            Created booking with magic link token

        Raises:
            BookingServiceError: If creation fails
        """
        # Generate secure magic link token
        token = self.magic_link_service.generate_token()

        # Calculate token expiration (end of check-out day)
        expires_at = self.magic_link_service.calculate_expiration(
            booking_data.check_out_date
        )

        # Prepare booking dictionary
        booking_dict = booking_data.model_dump()

        # Create booking
        booking = await self.booking_repo.create_booking(
            booking_data=booking_dict,
            magic_link_token=token,
            token_expires_at=expires_at,
        )

        # Convert to response
        response = BookingResponse.model_validate(booking)
        response.current_guest_count = 0  # No guests yet

        return response

    async def get_booking_by_id(self, booking_id: UUID) -> BookingResponse | None:
        """Get booking by ID with guest count."""
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            return None

        # Get current guest count
        guest_count = await self.guest_repo.count_guests_for_booking(booking_id)

        response = BookingResponse.model_validate(booking)
        response.current_guest_count = guest_count
        return response

    async def get_booking_by_magic_link(self, token: str) -> BookingResponse | None:
        """
        Get booking by magic link token (for guest portal).

        Args:
            token: Magic link token

        Returns:
            Booking or None if not found/expired

        Raises:
            BookingServiceError: If token is expired
        """
        booking = await self.booking_repo.get_by_magic_link(token)
        if not booking:
            return None

        # Check if token is expired
        if self.magic_link_service.is_token_expired(booking.token_expires_at):
            raise BookingServiceError(
                "Magic link has expired. Please contact the property."
            )

        # Get current guest count
        guest_count = await self.guest_repo.count_guests_for_booking(booking.id)

        response = BookingResponse.model_validate(booking)
        response.current_guest_count = guest_count
        return response

    async def get_all_bookings(
        self,
        limit: int = 100,
        offset: int = 0,
        status: BookingStatus | None = None,
    ) -> Sequence[BookingResponse]:
        """Get all bookings for the current tenant."""
        bookings = await self.booking_repo.get_all_for_tenant(limit, offset, status)

        responses = []
        for booking in bookings:
            guest_count = await self.guest_repo.count_guests_for_booking(booking.id)
            response = BookingResponse.model_validate(booking)
            response.current_guest_count = guest_count
            responses.append(response)

        return responses

    async def get_booking_progress(
        self,
        booking_id: UUID,
    ) -> BookingProgressResponse:
        """
        Get booking progress for progress tracking UI.

        Returns:
            Progress response with completion percentage
        """
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingServiceError(f"Booking {booking_id} not found")

        # Get guest counts
        current_count = await self.guest_repo.count_guests_for_booking(booking_id)
        leader = await self.guest_repo.get_leader_for_booking(booking_id)

        # Calculate completion percentage
        if booking.expected_guests > 0:
            completion = (current_count / booking.expected_guests) * 100
        else:
            completion = 0.0

        return BookingProgressResponse(
            booking_id=booking.id,
            expected_guests=booking.expected_guests,
            current_guest_count=current_count,
            has_leader=leader is not None,
            completion_percentage=min(completion, 100.0),
            status=booking.status,
        )

    async def mark_in_progress(self, booking_id: UUID) -> BookingResponse:
        """
        Mark booking as in_progress when guest starts data entry.

        Args:
            booking_id: ID of the booking

        Returns:
            Updated booking

        Raises:
            BookingServiceError: If transition is invalid
        """
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingServiceError(f"Booking {booking_id} not found")

        if booking.status != BookingStatus.PENDING:
            raise BookingServiceError(
                f"Cannot mark as in_progress: booking is {booking.status.value}"
            )

        updated = await self.booking_repo.update_status(
            booking_id, BookingStatus.IN_PROGRESS
        )

        guest_count = await self.guest_repo.count_guests_for_booking(booking_id)
        response = BookingResponse.model_validate(updated)
        response.current_guest_count = guest_count
        return response

    async def mark_complete(self, booking_id: UUID) -> BookingResponse:
        """
        Mark booking as complete when all guest data is entered.

        Args:
            booking_id: ID of the booking

        Returns:
            Updated booking

        Raises:
            BookingServiceError: If validation fails
        """
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingServiceError(f"Booking {booking_id} not found")

        # Validate completeness
        validation = await self.guest_repo.validate_guest_completeness(booking_id)
        if not validation["is_complete"]:
            raise BookingServiceError(
                f"Booking is incomplete: {', '.join(validation['missing_fields'])}"
            )

        # Validate guest count matches expected
        current_count = validation["total_guests"]
        if current_count < booking.expected_guests:
            raise BookingServiceError(
                f"Only {current_count}/{booking.expected_guests} guests entered"
            )

        updated = await self.booking_repo.update_status(
            booking_id, BookingStatus.COMPLETE
        )

        response = BookingResponse.model_validate(updated)
        response.current_guest_count = current_count
        return response

    async def mark_synced(self, booking_id: UUID) -> BookingResponse:
        """
        Mark booking as synced after successful ROS1000 transmission.

        Args:
            booking_id: ID of the booking

        Returns:
            Updated booking
        """
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingServiceError(f"Booking {booking_id} not found")

        if booking.status != BookingStatus.COMPLETE:
            raise BookingServiceError(
                f"Cannot sync: booking must be complete (current: {booking.status.value})"
            )

        updated = await self.booking_repo.update_status(
            booking_id, BookingStatus.SYNCED
        )

        guest_count = await self.guest_repo.count_guests_for_booking(booking_id)
        response = BookingResponse.model_validate(updated)
        response.current_guest_count = guest_count
        return response

    async def mark_error(self, booking_id: UUID) -> BookingResponse:
        """
        Mark booking as error after failed ROS1000 transmission.

        Args:
            booking_id: ID of the booking

        Returns:
            Updated booking
        """
        updated = await self.booking_repo.update_status(
            booking_id, BookingStatus.ERROR
        )

        guest_count = await self.guest_repo.count_guests_for_booking(booking_id)
        response = BookingResponse.model_validate(updated)
        response.current_guest_count = guest_count
        return response

    async def get_bookings_requiring_sync(self) -> Sequence[BookingResponse]:
        """
        Get all complete bookings that need ROS1000 sync.

        Returns:
            List of bookings in COMPLETE status
        """
        return await self.get_all_bookings(status=BookingStatus.COMPLETE, limit=1000)

    async def get_sla_warnings(self, warning_hour: int = 10) -> Sequence[BookingResponse]:
        """
        Get bookings at risk of missing TULPS 24-hour deadline.

        Args:
            warning_hour: Hour of day to send warning (default: 10:00 AM)

        Returns:
            List of bookings needing attention
        """
        today = date.today()
        bookings = await self.booking_repo.get_bookings_by_date_range(today, today)

        warnings = []
        for booking in bookings:
            # Check if booking is incomplete on arrival day
            if booking.status in [BookingStatus.PENDING, BookingStatus.IN_PROGRESS]:
                guest_count = await self.guest_repo.count_guests_for_booking(booking.id)
                response = BookingResponse.model_validate(booking)
                response.current_guest_count = guest_count
                warnings.append(response)

        return warnings
