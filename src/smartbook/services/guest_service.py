"""
Guest Service with TULPS validation.

Implements business logic for guest data collection following
Italian TULPS (Testo Unico delle Leggi di Pubblica Sicurezza) requirements.
"""

from datetime import date
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.enums import GuestRole, DocumentType
from smartbook.domain.models.guest import Guest
from smartbook.domain.schemas.guest import (
    GuestLeaderCreate,
    GuestMemberCreate,
    GuestResponse,
)
from smartbook.repositories.guest import GuestRepository


class TULPSValidationError(Exception):
    """Raised when guest data fails TULPS validation."""

    pass


class GuestService:
    """
    Service for guest data collection and TULPS validation.

    Implements the distinction between:
    - Group Leaders (Capogruppo): Full document details required
    - Group Members: TULPS minimums only (Name, Sex, DOB, Residence)
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.guest_repo = GuestRepository(session)

    async def create_group_leader(
        self,
        booking_id: UUID,
        leader_data: GuestLeaderCreate,
    ) -> GuestResponse:
        """
        Create a group leader with full document validation.

        Args:
            booking_id: ID of the booking
            leader_data: Leader data with full document details

        Returns:
            Created guest response

        Raises:
            TULPSValidationError: If validation fails
        """
        # Validate that booking doesn't already have a leader
        existing_leader = await self.guest_repo.get_leader_for_booking(booking_id)
        if existing_leader:
            raise TULPSValidationError(
                "Booking already has a group leader. "
                "Only one leader per booking is allowed."
            )

        # Validate document completeness
        self._validate_leader_documents(leader_data)

        # Create guest with leader role
        guest_dict = leader_data.model_dump()
        guest_dict["booking_id"] = booking_id
        guest_dict["role"] = GuestRole.LEADER

        # Calculate tax exemption if applicable
        guest_dict["is_tax_exempt"] = False
        guest_dict["tax_exemption_reason"] = None

        guest = await self.guest_repo.create_guest(guest_dict)
        return GuestResponse.model_validate(guest)

    async def create_group_member(
        self,
        booking_id: UUID,
        member_data: GuestMemberCreate,
    ) -> GuestResponse:
        """
        Create a group member with TULPS minimum validation.

        Args:
            booking_id: ID of the booking
            member_data: Member data (documents optional)

        Returns:
            Created guest response

        Raises:
            TULPSValidationError: If validation fails
        """
        # Validate TULPS minimums
        self._validate_member_minimums(member_data)

        # Create guest with member role
        guest_dict = member_data.model_dump()
        guest_dict["booking_id"] = booking_id
        guest_dict["role"] = member_data.role

        # Calculate tax exemption if applicable
        guest_dict["is_tax_exempt"] = False
        guest_dict["tax_exemption_reason"] = None

        guest = await self.guest_repo.create_guest(guest_dict)
        return GuestResponse.model_validate(guest)

    async def bulk_create_members(
        self,
        booking_id: UUID,
        members_data: list[GuestMemberCreate],
    ) -> list[GuestResponse]:
        """
        Bulk create multiple group members (optimized for large groups).

        Args:
            booking_id: ID of the booking
            members_data: List of member data

        Returns:
            List of created guest responses
        """
        # Validate all members first
        for member_data in members_data:
            self._validate_member_minimums(member_data)

        # Prepare guest dictionaries
        guests_dict = []
        for member_data in members_data:
            guest_dict = member_data.model_dump()
            guest_dict["booking_id"] = booking_id
            guest_dict["role"] = member_data.role
            guest_dict["is_tax_exempt"] = False
            guest_dict["tax_exemption_reason"] = None
            guests_dict.append(guest_dict)

        # Bulk create
        guests = await self.guest_repo.bulk_create_guests(guests_dict)
        return [GuestResponse.model_validate(guest) for guest in guests]

    async def apply_same_as_leader_residence(
        self,
        booking_id: UUID,
        member_ids: list[UUID],
    ) -> list[GuestResponse]:
        """
        Apply "Same as Leader" feature - copy residence from leader to members.

        This feature reduces data entry by ~50% for local groups where
        most members reside in the same municipality.

        Args:
            booking_id: ID of the booking
            member_ids: List of member IDs to update

        Returns:
            Updated guest responses

        Raises:
            TULPSValidationError: If no leader exists
        """
        # Get the leader
        leader = await self.guest_repo.get_leader_for_booking(booking_id)
        if not leader:
            raise TULPSValidationError("No group leader found for this booking")

        # Get members to update
        updated_guests = []
        for member_id in member_ids:
            member = await self.guest_repo.get_by_id(member_id)
            if member and member.booking_id == booking_id:
                # Copy residence from leader
                member.residence_municipality_code = leader.residence_municipality_code
                member.residence_country_code = leader.residence_country_code
                member.residence_address = leader.residence_address
                member.residence_zip_code = leader.residence_zip_code

                updated_member = await self.guest_repo.update(member)
                updated_guests.append(GuestResponse.model_validate(updated_member))

        return updated_guests

    async def calculate_tax_exemptions(
        self,
        booking_id: UUID,
        check_in_date: date,
        age_threshold: int = 14,
    ) -> dict:
        """
        Calculate tax exemptions for all guests in a booking.

        Args:
            booking_id: ID of the booking
            check_in_date: Check-in date for age calculation
            age_threshold: Age below which guests are exempt (default: 14)

        Returns:
            Dictionary with exemption statistics
        """
        guests = await self.guest_repo.get_by_booking_id(booking_id)

        exempt_count = 0
        exempt_minors = 0
        exempt_drivers = 0
        exempt_guides = 0

        for guest in guests:
            is_exempt = False
            reason = None

            # Age-based exemption
            age_on_checkin = (check_in_date - guest.date_of_birth).days // 365
            if age_on_checkin < age_threshold:
                is_exempt = True
                reason = f"minor_under_{age_threshold}"
                exempt_minors += 1

            # Role-based exemptions
            elif guest.role == GuestRole.BUS_DRIVER:
                is_exempt = True
                reason = "bus_driver"
                exempt_drivers += 1
            elif guest.role == GuestRole.TOUR_GUIDE:
                is_exempt = True
                reason = "tour_guide"
                exempt_guides += 1

            # Update guest
            if is_exempt:
                guest.is_tax_exempt = True
                guest.tax_exemption_reason = reason
                await self.guest_repo.update(guest)
                exempt_count += 1

        return {
            "total_guests": len(guests),
            "exempt_count": exempt_count,
            "taxable_count": len(guests) - exempt_count,
            "exempt_minors": exempt_minors,
            "exempt_drivers": exempt_drivers,
            "exempt_guides": exempt_guides,
        }

    def _validate_leader_documents(self, leader_data: GuestLeaderCreate) -> None:
        """Validate that leader has all required document fields."""
        if not all([
            leader_data.document_type,
            leader_data.document_number,
            leader_data.document_issuing_authority,
            leader_data.document_issue_date,
            leader_data.document_issue_place,
        ]):
            raise TULPSValidationError(
                "Group leader must have complete document details: "
                "type, number, issuing authority, issue date, and issue place"
            )

    def _validate_member_minimums(self, member_data: GuestMemberCreate) -> None:
        """Validate that member has TULPS minimum fields."""
        if not all([
            member_data.first_name,
            member_data.last_name,
            member_data.sex,
            member_data.date_of_birth,
        ]):
            raise TULPSValidationError(
                "Group member must have TULPS minimum data: "
                "first name, last name, sex, and date of birth"
            )

    async def get_guests_for_booking(self, booking_id: UUID) -> Sequence[GuestResponse]:
        """
        Get all guests for a booking.

        Args:
            booking_id: ID of the booking

        Returns:
            List of all guests for the booking
        """
        guests = await self.guest_repo.get_by_booking_id(booking_id)
        return [GuestResponse.model_validate(guest) for guest in guests]

    async def validate_booking_completeness(self, booking_id: UUID) -> dict:
        """
        Validate that all required guest data is complete for ROS1000 transmission.

        Returns:
            Dictionary with validation results
        """
        return await self.guest_repo.validate_guest_completeness(booking_id)
