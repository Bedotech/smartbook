"""
Guest Portal API endpoints (Magic Link authenticated).

These endpoints are accessed by guests using their magic link token
to enter their information for group check-in.
"""

from typing import Sequence
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.database import get_db
from smartbook.domain.schemas.booking import BookingResponse, BookingProgressResponse
from smartbook.domain.schemas.guest import (
    GuestLeaderCreate,
    GuestMemberCreate,
    GuestResponse,
)
from smartbook.domain.schemas.municipality import (
    MunicipalitySearchResponse,
    CountrySearchResponse,
)
from smartbook.services.booking_service import BookingService, BookingServiceError
from smartbook.services.guest_service import GuestService, TULPSValidationError
from smartbook.services.municipality_service import MunicipalityService

router = APIRouter()


# Dependency to get booking by magic link token
async def get_booking_from_token(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> tuple[BookingResponse, AsyncSession]:
    """
    Validate magic link token and return booking.

    Args:
        token: Magic link token
        db: Database session

    Returns:
        Tuple of (booking, session)

    Raises:
        HTTPException: If token invalid or expired
    """
    # Extract tenant_id from booking (we'll need to look up the booking first)
    # For now, we'll use a placeholder - in production, this would be more sophisticated
    from uuid import UUID

    # This is a simplified version - in production you'd:
    # 1. Look up token in database to get tenant_id
    # 2. Create service with proper tenant_id
    # For now, we'll attempt to find any booking with this token

    booking_service = BookingService(db, UUID('00000000-0000-0000-0000-000000000000'))

    try:
        booking = await booking_service.get_booking_by_magic_link(token)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired magic link"
            )
        return booking, db
    except BookingServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/booking/{token}", response_model=BookingResponse)
async def get_booking_by_token(
    booking_data: tuple = Depends(get_booking_from_token),
):
    """
    Get booking details by magic link token.

    This is the entry point for guests - they receive a magic link
    and use it to access their booking.

    Args:
        booking_data: Booking and session from dependency

    Returns:
        Booking details with current progress
    """
    booking, _ = booking_data
    return booking


@router.get("/booking/{token}/progress", response_model=BookingProgressResponse)
async def get_booking_progress(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get booking progress (e.g., "12/50 guests entered").

    Args:
        token: Magic link token
        db: Database session

    Returns:
        Progress information
    """
    booking, db = await get_booking_from_token(token, db)

    booking_service = BookingService(db, booking.tenant_id)
    progress = await booking_service.get_booking_progress(booking.id)

    return progress


@router.post("/booking/{token}/guests/leader", response_model=GuestResponse)
async def create_group_leader(
    token: str,
    leader_data: GuestLeaderCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create group leader with full document details.

    The group leader is the primary contact and must provide
    complete document information for TULPS compliance.

    Args:
        token: Magic link token
        leader_data: Leader information
        db: Database session

    Returns:
        Created leader details
    """
    booking, db = await get_booking_from_token(token, db)

    guest_service = GuestService(db)

    try:
        leader = await guest_service.create_group_leader(
            booking_id=booking.id,
            leader_data=leader_data,
        )
        return leader
    except TULPSValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/booking/{token}/guests/member", response_model=GuestResponse)
async def create_group_member(
    token: str,
    member_data: GuestMemberCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create group member with TULPS minimums.

    Group members only need basic information (name, DOB, sex, residence).
    Document details are optional for members.

    Args:
        token: Magic link token
        member_data: Member information
        db: Database session

    Returns:
        Created member details
    """
    booking, db = await get_booking_from_token(token, db)

    guest_service = GuestService(db)

    try:
        member = await guest_service.create_group_member(
            booking_id=booking.id,
            member_data=member_data,
        )
        return member
    except TULPSValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/booking/{token}/guests", response_model=Sequence[GuestResponse])
async def get_booking_guests(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all guests for a booking.

    Args:
        token: Magic link token
        db: Database session

    Returns:
        List of guests
    """
    booking, db = await get_booking_from_token(token, db)

    guest_service = GuestService(db)
    guests = await guest_service.get_guests_for_booking(booking.id)

    return guests


@router.post("/booking/{token}/complete", response_model=BookingResponse)
async def mark_booking_complete(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark booking as complete when all guests are entered.

    This validates that:
    - All expected guests have been entered
    - Leader exists with full details
    - All members have TULPS minimums

    Args:
        token: Magic link token
        db: Database session

    Returns:
        Updated booking

    Raises:
        HTTPException: If validation fails
    """
    booking, db = await get_booking_from_token(token, db)

    booking_service = BookingService(db, booking.tenant_id)

    try:
        updated_booking = await booking_service.mark_complete(booking.id)
        return updated_booking
    except BookingServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/municipalities/search", response_model=Sequence[MunicipalitySearchResponse])
async def search_municipalities(
    query: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Search Italian municipalities (ISTAT autocomplete).

    Used for residence and birth place fields.

    Args:
        query: Search query (e.g., "Schil" -> "Schilpario")
        limit: Maximum results
        db: Database session

    Returns:
        List of matching municipalities
    """
    # We don't need tenant_id for municipality search (reference data)
    from uuid import UUID
    municipality_service = MunicipalityService(db, UUID('00000000-0000-0000-0000-000000000000'))

    results = await municipality_service.search_municipalities(query, limit)
    return results


@router.get("/countries/search", response_model=Sequence[CountrySearchResponse])
async def search_countries(
    query: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Search countries (ISTAT codes).

    Used for citizenship and foreign birth places.

    Args:
        query: Search query (e.g., "Ital" -> "Italy")
        limit: Maximum results
        db: Database session

    Returns:
        List of matching countries
    """
    from uuid import UUID
    municipality_service = MunicipalityService(db, UUID('00000000-0000-0000-0000-000000000000'))

    results = await municipality_service.search_countries(query, limit)
    return results
