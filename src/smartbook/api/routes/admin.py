"""
Admin Dashboard API endpoints.

These endpoints require authentication and are used by property managers
to manage bookings, guests, tax reporting, and ROS1000 compliance.
"""

from datetime import date
from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from smartbook.api.dependencies import CurrentUser, AdminUser, UserPropertyIds, DbSession
from smartbook.domain.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingUpdate,
    BookingProgressResponse,
)
from smartbook.domain.schemas.guest import GuestResponse, GuestUpdate
from smartbook.domain.schemas.tax_rule import (
    TaxRuleCreate,
    TaxRuleResponse,
    TaxRuleUpdate,
)
from smartbook.domain.schemas.compliance_record import ComplianceRecordResponse
from smartbook.domain.enums import BookingStatus, ComplianceStatus
from smartbook.services.booking_service import BookingService, BookingServiceError
from smartbook.services.guest_service import GuestService, TULPSValidationError
from smartbook.services.tax_calculation_service import TaxCalculationService
from smartbook.services.tax_reporting_service import TaxReportGenerator
from smartbook.integrations.ros1000_service import (
    ROS1000Service,
    ROS1000ServiceError,
    ROS1000ValidationError,
)
from smartbook.repositories.tax_rule import TaxRuleRepository
from smartbook.repositories.compliance_record import ComplianceRecordRepository

router = APIRouter()


# Helper function for property access validation
async def validate_property_access_helper(
    property_id: UUID,
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
) -> UUID:
    """Validate user has access to property."""
    from smartbook.repositories.user_property_assignment import UserPropertyAssignmentRepository

    assignment_repo = UserPropertyAssignmentRepository(db)
    property_ids = await assignment_repo.get_property_ids_for_user(user.id)

    if property_id not in property_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this property"
        )

    return property_id


# ============================================================================
# BOOKING MANAGEMENT
# ============================================================================

@router.get("/bookings", response_model=Sequence[BookingResponse])
async def list_bookings(
    property_id: UUID = Query(..., description="Property ID to list bookings for"),
    status: BookingStatus | None = None,
    check_in_from: date | None = None,
    check_in_to: date | None = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    List all bookings for a specific property.

    User must have access to the requested property.

    Args:
        property_id: Property ID to list bookings for
        status: Filter by booking status
        check_in_from: Filter bookings checking in after this date
        check_in_to: Filter bookings checking in before this date
        limit: Maximum number of results
        offset: Pagination offset
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        List of bookings
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    booking_service = BookingService(db, property_id)

    # TODO: Implement repository methods for filtering
    # For now, get all and filter in Python (inefficient for production)
    all_bookings = await booking_service.get_all_bookings()

    # Apply filters
    filtered = all_bookings
    if status:
        filtered = [b for b in filtered if b.status == status]
    if check_in_from:
        filtered = [b for b in filtered if b.check_in_date >= check_in_from]
    if check_in_to:
        filtered = [b for b in filtered if b.check_in_date <= check_in_to]

    # Apply pagination
    paginated = filtered[offset:offset + limit]

    return paginated


@router.post("/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    property_id: UUID = Query(..., description="Property ID for the booking"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Create a new booking for a specific property.

    Generates magic link token for guest access.
    User must have access to the property.

    Args:
        booking_data: Booking information
        property_id: Property ID for the booking
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Created booking with magic link
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    booking_service = BookingService(db, property_id)

    try:
        booking = await booking_service.create_booking(booking_data)
        return booking
    except BookingServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Get booking by ID.

    Args:
        booking_id: Booking ID
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Booking details
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    booking_service = BookingService(db, property_id)

    booking = await booking_service.get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    return booking


@router.put("/bookings/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: UUID,
    booking_data: BookingUpdate,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Update booking details.

    Args:
        booking_id: Booking ID
        booking_data: Updated booking data
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Updated booking
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    booking_service = BookingService(db, property_id)

    try:
        booking = await booking_service.update_booking(booking_id, booking_data)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        return booking
    except BookingServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: UUID,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Delete a booking.

    Only allowed if booking has not been submitted to ROS1000.

    Args:
        booking_id: Booking ID
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    booking_service = BookingService(db, property_id)

    try:
        success = await booking_service.delete_booking(booking_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
    except BookingServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/bookings/{booking_id}/progress", response_model=BookingProgressResponse)
async def get_booking_progress(
    booking_id: UUID,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Get booking progress (guests entered).

    Args:
        booking_id: Booking ID
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Progress information
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    booking_service = BookingService(db, property_id)
    progress = await booking_service.get_booking_progress(booking_id)

    return progress


# ============================================================================
# GUEST MANAGEMENT
# ============================================================================

@router.get("/bookings/{booking_id}/guests", response_model=Sequence[GuestResponse])
async def get_booking_guests(
    booking_id: UUID,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Get all guests for a booking.

    Args:
        booking_id: Booking ID
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        List of guests
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    guest_service = GuestService(db)
    guests = await guest_service.get_guests_for_booking(booking_id)

    return guests


@router.put("/guests/{guest_id}", response_model=GuestResponse)
async def update_guest(
    guest_id: UUID,
    guest_data: GuestUpdate,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Update guest details.

    Args:
        guest_id: Guest ID
        guest_data: Updated guest data
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Updated guest
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    guest_service = GuestService(db)

    try:
        guest = await guest_service.update_guest(guest_id, guest_data)
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guest not found"
            )
        return guest
    except TULPSValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/guests/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guest(
    guest_id: UUID,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Delete a guest.

    Args:
        guest_id: Guest ID
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    guest_service = GuestService(db)

    try:
        success = await guest_service.delete_guest(guest_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guest not found"
            )
    except TULPSValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# ROS1000 COMPLIANCE
# ============================================================================

@router.post("/bookings/{booking_id}/submit-ros1000")
async def submit_booking_to_ros1000(
    booking_id: UUID,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Submit booking to ROS1000/Alloggiati Web system.

    Validates data, generates XML, submits via SOAP, and stores
    compliance record for 5-year retention.

    Args:
        booking_id: Booking ID
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Submission response with receipt number
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    # Get property and booking
    from smartbook.repositories.tenant import TenantRepository
    from smartbook.repositories.booking import BookingRepository

    property_repo = TenantRepository(db)
    booking_repo = BookingRepository(db, property_id)

    property = await property_repo.get_by_id(property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    booking = await booking_repo.get_by_id(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Get guests
    guest_service = GuestService(db)
    guests = await guest_service.get_guests_for_booking(booking_id)

    # Submit to ROS1000
    ros1000_service = ROS1000Service(db, property)

    try:
        response = await ros1000_service.submit_booking(booking, guests)

        return {
            "success": response.success,
            "receipt_number": response.receipt_number,
            "error_message": response.error_message,
            "warnings": response.warnings,
            "partial_success": response.partial_success,
        }

    except ROS1000ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed: {str(e)}"
        )
    except ROS1000ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Submission failed: {str(e)}"
        )


@router.post("/bookings/{booking_id}/cancel-ros1000")
async def cancel_ros1000_submission(
    booking_id: UUID,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Cancel/correct a previous ROS1000 submission.

    Args:
        booking_id: Booking ID
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Cancellation response
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    from smartbook.repositories.tenant import TenantRepository
    from smartbook.repositories.booking import BookingRepository

    property_repo = TenantRepository(db)
    booking_repo = BookingRepository(db, property_id)

    property = await property_repo.get_by_id(property_id)
    booking = await booking_repo.get_by_id(booking_id)

    if not property or not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property or booking not found"
        )

    guest_service = GuestService(db)
    guests = await guest_service.get_guests_for_booking(booking_id)

    ros1000_service = ROS1000Service(db, property)

    try:
        response = await ros1000_service.cancel_submission(booking, guests)

        return {
            "success": response.success,
            "receipt_number": response.receipt_number,
            "error_message": response.error_message,
        }

    except ROS1000ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/compliance/records", response_model=Sequence[ComplianceRecordResponse])
async def list_compliance_records(
    property_id: UUID = Query(..., description="Property ID"),
    booking_id: UUID | None = None,
    status: ComplianceStatus | None = None,
    limit: int = Query(default=50, le=100),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    List compliance records (5-year retention).

    Args:
        property_id: Property ID
        booking_id: Filter by booking ID
        status: Filter by compliance status
        limit: Maximum number of results
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        List of compliance records
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    compliance_repo = ComplianceRecordRepository(db, property_id)

    if booking_id:
        # Get records for specific booking
        record = await compliance_repo.get_latest_for_booking(booking_id)
        return [record] if record else []
    else:
        # TODO: Implement list_all method in repository
        # For now, return empty list
        return []


@router.post("/compliance/records/{record_id}/retry")
async def retry_failed_submission(
    record_id: UUID,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Retry a failed ROS1000 submission.

    Args:
        record_id: Compliance record ID
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Retry response
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    from smartbook.repositories.tenant import TenantRepository

    property_repo = TenantRepository(db)
    property = await property_repo.get_by_id(property_id)

    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    ros1000_service = ROS1000Service(db, property)

    try:
        response = await ros1000_service.retry_failed_submission(record_id)

        return {
            "success": response.success,
            "receipt_number": response.receipt_number,
            "error_message": response.error_message,
        }

    except ROS1000ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# TAX CALCULATION & REPORTING
# ============================================================================

@router.post("/bookings/{booking_id}/calculate-tax")
async def calculate_booking_tax(
    booking_id: UUID,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Calculate city tax for a booking.

    Args:
        booking_id: Booking ID
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Tax calculation result
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    from smartbook.repositories.booking import BookingRepository

    booking_repo = BookingRepository(db, property_id)
    booking = await booking_repo.get_by_id(booking_id)

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    tax_service = TaxCalculationService(db, property_id)

    result = await tax_service.calculate_tax_for_booking(
        booking_id=booking_id,
        check_in_date=booking.check_in_date,
        check_out_date=booking.check_out_date,
    )

    return {
        "booking_id": str(result.booking_id),
        "total_tax": str(result.total_tax),
        "total_nights": result.total_nights,
        "taxable_nights": result.taxable_nights,
        "total_guests": result.total_guests,
        "taxable_guests": result.taxable_guests,
        "base_rate_per_night": str(result.base_rate_per_night),
        "exemptions": result.exemptions,
        "breakdown_by_guest": [
            {
                "guest_id": str(g["guest_id"]),
                "guest_name": g["guest_name"],
                "is_exempt": g["is_exempt"],
                "exemption_reason": g["exemption_reason"],
                "nights_taxed": g["nights_taxed"],
                "tax_amount": str(g["tax_amount"]),
            }
            for g in result.breakdown_by_guest
        ],
    }


@router.get("/tax/reports/monthly")
async def generate_monthly_tax_report(
    property_id: UUID = Query(..., description="Property ID"),
    year: int = Query(...),
    month: int = Query(...),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Generate monthly tax report.

    Args:
        property_id: Property ID
        year: Year (e.g., 2024)
        month: Month (1-12)
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Monthly tax report with Italian formatting
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    tax_service = TaxCalculationService(db, property_id)
    report_generator = TaxReportGenerator(tax_service)

    report = await report_generator.generate_monthly_report(year, month)

    # Convert Decimal to string for JSON serialization
    return {
        "period": report.period,
        "total_bookings": report.total_bookings,
        "total_guests": report.total_guests,
        "total_taxable_guests": report.total_taxable_guests,
        "total_nights": report.total_nights,
        "total_tax": str(report.total_tax),
        "average_tax_per_booking": str(report.average_tax_per_booking),
        "exemption_summary": report.exemption_summary,
        "booking_details": [
            {
                "booking_id": str(b["booking_id"]),
                "booking_name": b["booking_name"],
                "check_in": b["check_in"],
                "check_out": b["check_out"],
                "guests": b["guests"],
                "nights": b["nights"],
                "tax_amount": str(b["tax_amount"]),
            }
            for b in report.booking_details
        ],
    }


@router.get("/tax/reports/quarterly")
async def generate_quarterly_tax_report(
    property_id: UUID = Query(..., description="Property ID"),
    year: int = Query(...),
    quarter: int = Query(..., ge=1, le=4),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Generate quarterly tax report.

    Args:
        property_id: Property ID
        year: Year (e.g., 2024)
        quarter: Quarter (1-4)
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Quarterly tax report
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    tax_service = TaxCalculationService(db, property_id)
    report_generator = TaxReportGenerator(tax_service)

    report = await report_generator.generate_quarterly_report(year, quarter)

    return {
        "period": report.period,
        "total_bookings": report.total_bookings,
        "total_guests": report.total_guests,
        "total_taxable_guests": report.total_taxable_guests,
        "total_nights": report.total_nights,
        "total_tax": str(report.total_tax),
        "average_tax_per_booking": str(report.average_tax_per_booking),
        "exemption_summary": report.exemption_summary,
        "booking_details": [
            {
                "booking_id": str(b["booking_id"]),
                "booking_name": b["booking_name"],
                "check_in": b["check_in"],
                "check_out": b["check_out"],
                "guests": b["guests"],
                "nights": b["nights"],
                "tax_amount": str(b["tax_amount"]),
            }
            for b in report.booking_details
        ],
    }


# ============================================================================
# TAX RULE CONFIGURATION
# ============================================================================

@router.get("/tax/rules", response_model=Sequence[TaxRuleResponse])
async def list_tax_rules(
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    List all tax rules for the property.

    Args:
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        List of tax rules
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    tax_rule_repo = TaxRuleRepository(db, property_id)
    rules = await tax_rule_repo.get_all()

    return rules


@router.post("/tax/rules", response_model=TaxRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_tax_rule(
    rule_data: TaxRuleCreate,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Create a new tax rule.

    Args:
        rule_data: Tax rule data
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Created tax rule
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    tax_rule_repo = TaxRuleRepository(db, property_id)
    rule = await tax_rule_repo.create(rule_data)

    return rule


@router.put("/tax/rules/{rule_id}", response_model=TaxRuleResponse)
async def update_tax_rule(
    rule_id: UUID,
    rule_data: TaxRuleUpdate,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Update a tax rule.

    Args:
        rule_id: Tax rule ID
        rule_data: Updated tax rule data
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Updated tax rule
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    tax_rule_repo = TaxRuleRepository(db, property_id)
    rule = await tax_rule_repo.update(rule_id, rule_data)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tax rule not found"
        )

    return rule


@router.delete("/tax/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tax_rule(
    rule_id: UUID,
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Delete a tax rule.

    Args:
        rule_id: Tax rule ID
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    tax_rule_repo = TaxRuleRepository(db, property_id)
    success = await tax_rule_repo.delete(rule_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tax rule not found"
        )


# ============================================================================
# DASHBOARD ANALYTICS
# ============================================================================

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    property_id: UUID = Query(..., description="Property ID"),
    user: CurrentUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Get dashboard statistics for a specific property.

    Args:
        property_id: Property ID
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Dashboard statistics
    """
    # Validate property access
    await validate_property_access_helper(property_id, user, db)

    booking_service = BookingService(db, property_id)

    # Get all bookings
    all_bookings = await booking_service.get_all_bookings()

    # Calculate statistics
    total_bookings = len(all_bookings)
    pending_bookings = len([b for b in all_bookings if b.status == BookingStatus.PENDING])
    complete_bookings = len([b for b in all_bookings if b.status == BookingStatus.COMPLETE])
    synced_bookings = len([b for b in all_bookings if b.status == BookingStatus.SYNCED])
    error_bookings = len([b for b in all_bookings if b.status == BookingStatus.ERROR])

    return {
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,
        "complete_bookings": complete_bookings,
        "synced_bookings": synced_bookings,
        "error_bookings": error_bookings,
        "completion_rate": (
            round((complete_bookings + synced_bookings) / total_bookings * 100, 1)
            if total_bookings > 0 else 0.0
        ),
    }


# ============================================================================
# PROPERTY MANAGEMENT (Admin Only)
# ============================================================================

@router.get("/properties", response_model=list)
async def list_properties(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=100),
    search: str | None = Query(None, description="Search by name or facility code"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    List all properties (admin only).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search term for name or facility code
        is_active: Filter by active status
        admin: Admin user (from JWT)
        db: Database session

    Returns:
        List of properties
    """
    from smartbook.repositories.tenant import TenantRepository

    tenant_repo = TenantRepository(db)
    properties = await tenant_repo.get_all(limit=limit, offset=skip)

    # Apply filters
    if search:
        search_lower = search.lower()
        properties = [
            p for p in properties
            if search_lower in p.name.lower() or search_lower in p.facility_code.lower()
        ]

    if is_active is not None:
        properties = [p for p in properties if p.is_active == is_active]

    # Convert to dict for serialization
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "facility_code": p.facility_code,
            "email": p.email,
            "phone": p.phone,
            "ros1000_username": p.ros1000_username,
            "ros1000_ws_key": p.ros1000_ws_key,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in properties
    ]


@router.get("/properties/{property_id}")
async def get_property(
    property_id: UUID,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Get a single property by ID (admin only).

    Args:
        property_id: Property ID
        admin: Admin user (from JWT)
        db: Database session

    Returns:
        Property details
    """
    from smartbook.repositories.tenant import TenantRepository

    tenant_repo = TenantRepository(db)
    property_obj = await tenant_repo.get_by_id(property_id)

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    return {
        "id": str(property_obj.id),
        "name": property_obj.name,
        "facility_code": property_obj.facility_code,
        "email": property_obj.email,
        "phone": property_obj.phone,
        "ros1000_username": property_obj.ros1000_username,
        "ros1000_ws_key": property_obj.ros1000_ws_key,
        "is_active": property_obj.is_active,
        "created_at": property_obj.created_at.isoformat() if property_obj.created_at else None,
        "updated_at": property_obj.updated_at.isoformat() if property_obj.updated_at else None,
    }


@router.post("/properties", status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: dict,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Create a new property (admin only).

    Args:
        property_data: Property creation data
        admin: Admin user (from JWT)
        db: Database session

    Returns:
        Created property
    """
    from smartbook.repositories.tenant import TenantRepository
    from smartbook.domain.models.tenant import Tenant

    tenant_repo = TenantRepository(db)

    # Check if facility code already exists
    existing = await tenant_repo.get_by_facility_code(property_data.get("facility_code"))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property with this facility code already exists"
        )

    # Create property
    new_property = Tenant(
        name=property_data["name"],
        facility_code=property_data["facility_code"],
        email=property_data["email"],
        phone=property_data.get("phone"),
        ros1000_username=property_data.get("ros1000_username"),
        ros1000_password=property_data.get("ros1000_password"),
        ros1000_ws_key=property_data.get("ros1000_ws_key"),
        is_active=True
    )

    db.add(new_property)
    await db.commit()
    await db.refresh(new_property)

    return {
        "id": str(new_property.id),
        "name": new_property.name,
        "facility_code": new_property.facility_code,
        "email": new_property.email,
        "phone": new_property.phone,
        "ros1000_username": new_property.ros1000_username,
        "ros1000_ws_key": new_property.ros1000_ws_key,
        "is_active": new_property.is_active,
        "created_at": new_property.created_at.isoformat() if new_property.created_at else None,
        "updated_at": new_property.updated_at.isoformat() if new_property.updated_at else None,
    }


@router.put("/properties/{property_id}")
async def update_property(
    property_id: UUID,
    property_data: dict,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Update a property (admin only).

    Args:
        property_id: Property ID
        property_data: Updated property data
        admin: Admin user (from JWT)
        db: Database session

    Returns:
        Updated property
    """
    from smartbook.repositories.tenant import TenantRepository

    tenant_repo = TenantRepository(db)
    property_obj = await tenant_repo.get_by_id(property_id)

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Check if facility code is being changed and if it's already in use
    if "facility_code" in property_data and property_data["facility_code"] != property_obj.facility_code:
        existing = await tenant_repo.get_by_facility_code(property_data["facility_code"])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property with this facility code already exists"
            )

    # Update fields
    for key, value in property_data.items():
        if hasattr(property_obj, key):
            setattr(property_obj, key, value)

    await db.commit()
    await db.refresh(property_obj)

    return {
        "id": str(property_obj.id),
        "name": property_obj.name,
        "facility_code": property_obj.facility_code,
        "email": property_obj.email,
        "phone": property_obj.phone,
        "ros1000_username": property_obj.ros1000_username,
        "ros1000_ws_key": property_obj.ros1000_ws_key,
        "is_active": property_obj.is_active,
        "created_at": property_obj.created_at.isoformat() if property_obj.created_at else None,
        "updated_at": property_obj.updated_at.isoformat() if property_obj.updated_at else None,
    }


@router.patch("/properties/{property_id}/activate", status_code=status.HTTP_200_OK)
async def activate_property(
    property_id: UUID,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Activate a property (admin only).

    Args:
        property_id: Property ID
        admin: Admin user (from JWT)
        db: Database session

    Returns:
        Success message
    """
    from smartbook.repositories.tenant import TenantRepository

    tenant_repo = TenantRepository(db)
    property_obj = await tenant_repo.get_by_id(property_id)

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    property_obj.is_active = True
    await db.commit()

    return {"message": "Property activated successfully"}


@router.patch("/properties/{property_id}/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_property(
    property_id: UUID,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Deactivate a property (admin only).

    Args:
        property_id: Property ID
        admin: Admin user (from JWT)
        db: Database session

    Returns:
        Success message
    """
    from smartbook.repositories.tenant import TenantRepository

    tenant_repo = TenantRepository(db)
    property_obj = await tenant_repo.get_by_id(property_id)

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    property_obj.is_active = False
    await db.commit()

    return {"message": "Property deactivated successfully"}


@router.get("/properties/{property_id}/users")
async def list_property_users(
    property_id: UUID,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    List users assigned to a property (admin only).

    Args:
        property_id: Property ID
        admin: Admin user (from JWT)
        db: Database session

    Returns:
        List of assigned users
    """
    from smartbook.repositories.user_property_assignment import UserPropertyAssignmentRepository
    from smartbook.repositories.user import UserRepository

    assignment_repo = UserPropertyAssignmentRepository(db)
    user_repo = UserRepository(db)

    # Get all assignments for this property
    assignments = await assignment_repo.get_assignments_for_property(property_id)

    # Get user details for each assignment
    users = []
    for assignment in assignments:
        user = await user_repo.get_by_id(assignment.user_id)
        if user:
            users.append({
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "assigned_at": assignment.assigned_at.isoformat(),
            })

    return users


@router.post("/properties/{property_id}/users/{user_id}", status_code=status.HTTP_201_CREATED)
async def assign_user_to_property(
    property_id: UUID,
    user_id: UUID,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Assign a user to a property (admin only).

    Args:
        property_id: Property ID
        user_id: User ID to assign
        admin: Admin user (from JWT)
        db: Database session

    Returns:
        Success message
    """
    from smartbook.repositories.user_property_assignment import UserPropertyAssignmentRepository
    from smartbook.repositories.user import UserRepository
    from smartbook.repositories.tenant import TenantRepository
    from smartbook.domain.models.user_property_assignment import UserPropertyAssignment

    # Verify property exists
    tenant_repo = TenantRepository(db)
    property_obj = await tenant_repo.get_by_id(property_id)
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Verify user exists
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if assignment already exists
    assignment_repo = UserPropertyAssignmentRepository(db)
    existing = await assignment_repo.get_assignment(user_id, property_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already assigned to this property"
        )

    # Create assignment
    assignment = UserPropertyAssignment(
        user_id=user_id,
        property_id=property_id,
        assigned_by_user_id=admin.id
    )

    db.add(assignment)
    await db.commit()

    return {"message": "User assigned to property successfully"}


@router.delete("/properties/{property_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_property(
    property_id: UUID,
    user_id: UUID,
    admin: AdminUser = None,  # type: ignore
    db: DbSession = None,  # type: ignore
):
    """
    Remove a user from a property (admin only).

    Args:
        property_id: Property ID
        user_id: User ID to remove
        admin: Admin user (from JWT)
        db: Database session
    """
    from smartbook.repositories.user_property_assignment import UserPropertyAssignmentRepository

    assignment_repo = UserPropertyAssignmentRepository(db)
    assignment = await assignment_repo.get_assignment(user_id, property_id)

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User assignment not found"
        )

    await db.delete(assignment)
    await db.commit()
