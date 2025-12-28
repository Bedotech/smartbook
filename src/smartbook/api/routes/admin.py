"""
Admin Dashboard API endpoints.

These endpoints require authentication and are used by property managers
to manage bookings, guests, tax reporting, and ROS1000 compliance.
"""

from datetime import date
from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.database import get_db
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


# TODO: Add JWT authentication dependency
# For now, we'll use a placeholder that extracts tenant_id from headers
async def get_current_tenant_id() -> UUID:
    """
    Get current authenticated tenant ID.

    In production, this would:
    1. Validate JWT token
    2. Extract tenant_id from token claims
    3. Verify tenant is active

    For now, this is a placeholder.
    """
    # Placeholder - in production this would decode JWT
    from uuid import UUID
    return UUID('00000000-0000-0000-0000-000000000000')


# ============================================================================
# BOOKING MANAGEMENT
# ============================================================================

@router.get("/bookings", response_model=Sequence[BookingResponse])
async def list_bookings(
    status: BookingStatus | None = None,
    check_in_from: date | None = None,
    check_in_to: date | None = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    List all bookings for the current tenant.

    Supports filtering by status and check-in date range.

    Args:
        status: Filter by booking status
        check_in_from: Filter bookings checking in after this date
        check_in_to: Filter bookings checking in before this date
        limit: Maximum number of results
        offset: Pagination offset
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        List of bookings
    """
    booking_service = BookingService(db, tenant_id)

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
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new booking.

    Generates magic link token for guest access.

    Args:
        booking_data: Booking information
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Created booking with magic link
    """
    booking_service = BookingService(db, tenant_id)

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
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get booking by ID.

    Args:
        booking_id: Booking ID
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Booking details
    """
    booking_service = BookingService(db, tenant_id)

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
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Update booking details.

    Args:
        booking_id: Booking ID
        booking_data: Updated booking data
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Updated booking
    """
    booking_service = BookingService(db, tenant_id)

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
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a booking.

    Only allowed if booking has not been submitted to ROS1000.

    Args:
        booking_id: Booking ID
        tenant_id: Current tenant ID (from JWT)
        db: Database session
    """
    booking_service = BookingService(db, tenant_id)

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
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get booking progress (guests entered).

    Args:
        booking_id: Booking ID
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Progress information
    """
    booking_service = BookingService(db, tenant_id)
    progress = await booking_service.get_booking_progress(booking_id)

    return progress


# ============================================================================
# GUEST MANAGEMENT
# ============================================================================

@router.get("/bookings/{booking_id}/guests", response_model=Sequence[GuestResponse])
async def get_booking_guests(
    booking_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all guests for a booking.

    Args:
        booking_id: Booking ID
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        List of guests
    """
    guest_service = GuestService(db)
    guests = await guest_service.get_guests_for_booking(booking_id)

    return guests


@router.put("/guests/{guest_id}", response_model=GuestResponse)
async def update_guest(
    guest_id: UUID,
    guest_data: GuestUpdate,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Update guest details.

    Args:
        guest_id: Guest ID
        guest_data: Updated guest data
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Updated guest
    """
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
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a guest.

    Args:
        guest_id: Guest ID
        tenant_id: Current tenant ID (from JWT)
        db: Database session
    """
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
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit booking to ROS1000/Alloggiati Web system.

    Validates data, generates XML, submits via SOAP, and stores
    compliance record for 5-year retention.

    Args:
        booking_id: Booking ID
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Submission response with receipt number
    """
    # Get tenant and booking
    from smartbook.repositories.tenant import TenantRepository
    from smartbook.repositories.booking import BookingRepository

    tenant_repo = TenantRepository(db, tenant_id)
    booking_repo = BookingRepository(db, tenant_id)

    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
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
    ros1000_service = ROS1000Service(db, tenant)

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
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel/correct a previous ROS1000 submission.

    Args:
        booking_id: Booking ID
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Cancellation response
    """
    from smartbook.repositories.tenant import TenantRepository
    from smartbook.repositories.booking import BookingRepository

    tenant_repo = TenantRepository(db, tenant_id)
    booking_repo = BookingRepository(db, tenant_id)

    tenant = await tenant_repo.get_by_id(tenant_id)
    booking = await booking_repo.get_by_id(booking_id)

    if not tenant or not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant or booking not found"
        )

    guest_service = GuestService(db)
    guests = await guest_service.get_guests_for_booking(booking_id)

    ros1000_service = ROS1000Service(db, tenant)

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
    booking_id: UUID | None = None,
    status: ComplianceStatus | None = None,
    limit: int = Query(default=50, le=100),
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    List compliance records (5-year retention).

    Args:
        booking_id: Filter by booking ID
        status: Filter by compliance status
        limit: Maximum number of results
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        List of compliance records
    """
    compliance_repo = ComplianceRecordRepository(db, tenant_id)

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
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Retry a failed ROS1000 submission.

    Args:
        record_id: Compliance record ID
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Retry response
    """
    from smartbook.repositories.tenant import TenantRepository

    tenant_repo = TenantRepository(db, tenant_id)
    tenant = await tenant_repo.get_by_id(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    ros1000_service = ROS1000Service(db, tenant)

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
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate city tax for a booking.

    Args:
        booking_id: Booking ID
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Tax calculation result
    """
    from smartbook.repositories.booking import BookingRepository

    booking_repo = BookingRepository(db, tenant_id)
    booking = await booking_repo.get_by_id(booking_id)

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    tax_service = TaxCalculationService(db, tenant_id)

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
    year: int,
    month: int,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate monthly tax report.

    Args:
        year: Year (e.g., 2024)
        month: Month (1-12)
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Monthly tax report with Italian formatting
    """
    tax_service = TaxCalculationService(db, tenant_id)
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
    year: int,
    quarter: int = Query(..., ge=1, le=4),
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate quarterly tax report.

    Args:
        year: Year (e.g., 2024)
        quarter: Quarter (1-4)
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Quarterly tax report
    """
    tax_service = TaxCalculationService(db, tenant_id)
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
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    List all tax rules for the tenant.

    Args:
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        List of tax rules
    """
    tax_rule_repo = TaxRuleRepository(db, tenant_id)
    rules = await tax_rule_repo.get_all()

    return rules


@router.post("/tax/rules", response_model=TaxRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_tax_rule(
    rule_data: TaxRuleCreate,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new tax rule.

    Args:
        rule_data: Tax rule data
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Created tax rule
    """
    tax_rule_repo = TaxRuleRepository(db, tenant_id)
    rule = await tax_rule_repo.create(rule_data)

    return rule


@router.put("/tax/rules/{rule_id}", response_model=TaxRuleResponse)
async def update_tax_rule(
    rule_id: UUID,
    rule_data: TaxRuleUpdate,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a tax rule.

    Args:
        rule_id: Tax rule ID
        rule_data: Updated tax rule data
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Updated tax rule
    """
    tax_rule_repo = TaxRuleRepository(db, tenant_id)
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
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a tax rule.

    Args:
        rule_id: Tax rule ID
        tenant_id: Current tenant ID (from JWT)
        db: Database session
    """
    tax_rule_repo = TaxRuleRepository(db, tenant_id)
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
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get dashboard statistics.

    Args:
        tenant_id: Current tenant ID (from JWT)
        db: Database session

    Returns:
        Dashboard statistics
    """
    booking_service = BookingService(db, tenant_id)

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
