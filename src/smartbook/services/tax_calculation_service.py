"""
City Tax (Imposta di Soggiorno) Calculation Service.

Implements the sophisticated tax calculation engine with:
- Base rate per night
- Max nights cap (e.g., only first 10 nights taxed)
- Age-based exemptions (dynamic calculation)
- Role-based exemptions (bus drivers: 1 per 25, tour guides)
- Historical rule support for past calculations
"""

from datetime import date
from decimal import Decimal
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.enums import GuestRole
from smartbook.domain.models.guest import Guest
from smartbook.domain.models.tax_rule import TaxRule
from smartbook.repositories.guest import GuestRepository
from smartbook.repositories.tax_rule import TaxRuleRepository


class TaxCalculationError(Exception):
    """Raised when tax calculation fails."""
    pass


class TaxCalculationResult:
    """Result of tax calculation for a booking."""

    def __init__(
        self,
        booking_id: UUID,
        total_guests: int,
        taxable_guests: int,
        exempt_guests: int,
        base_rate_per_night: Decimal,
        total_nights: int,
        taxable_nights: int,
        total_tax_amount: Decimal,
        exemption_breakdown: dict,
    ):
        self.booking_id = booking_id
        self.total_guests = total_guests
        self.taxable_guests = taxable_guests
        self.exempt_guests = exempt_guests
        self.base_rate_per_night = base_rate_per_night
        self.total_nights = total_nights
        self.taxable_nights = taxable_nights
        self.total_tax_amount = total_tax_amount
        self.exemption_breakdown = exemption_breakdown

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "booking_id": str(self.booking_id),
            "total_guests": self.total_guests,
            "taxable_guests": self.taxable_guests,
            "exempt_guests": self.exempt_guests,
            "base_rate_per_night": float(self.base_rate_per_night),
            "total_nights": self.total_nights,
            "taxable_nights": self.taxable_nights,
            "total_tax_amount": float(self.total_tax_amount),
            "exemption_breakdown": self.exemption_breakdown,
        }


class TaxCalculationService:
    """
    Service for City Tax (Imposta di Soggiorno) calculation.

    This is CRITICAL FINANCIAL LOGIC requiring 95%+ test coverage.
    All calculations must be auditable and historically accurate.
    """

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.guest_repo = GuestRepository(session)
        self.tax_rule_repo = TaxRuleRepository(session, tenant_id)

    async def calculate_tax_for_booking(
        self,
        booking_id: UUID,
        check_in_date: date,
        check_out_date: date,
    ) -> TaxCalculationResult:
        """
        Calculate total City Tax for a booking.

        Args:
            booking_id: ID of the booking
            check_in_date: Check-in date
            check_out_date: Check-out date

        Returns:
            TaxCalculationResult with complete breakdown

        Raises:
            TaxCalculationError: If calculation fails
        """
        # Get active tax rule for check-in date
        tax_rule = await self.tax_rule_repo.get_active_rule(check_in_date)
        if not tax_rule:
            raise TaxCalculationError(
                f"No active tax rule found for date {check_in_date}"
            )

        # Get all guests for the booking
        guests = await self.guest_repo.get_by_booking_id(booking_id)
        if not guests:
            raise TaxCalculationError(f"No guests found for booking {booking_id}")

        # Calculate total nights
        total_nights = (check_out_date - check_in_date).days
        if total_nights <= 0:
            raise TaxCalculationError("Check-out date must be after check-in date")

        # Apply max nights cap if configured
        taxable_nights = total_nights
        if tax_rule.max_taxable_nights:
            taxable_nights = min(total_nights, tax_rule.max_taxable_nights)

        # Calculate exemptions
        exemptions = await self._calculate_exemptions(
            guests=guests,
            check_in_date=check_in_date,
            tax_rule=tax_rule,
        )

        # Calculate tax amount
        taxable_guests = len(guests) - exemptions["total_exempt"]
        total_tax = Decimal(str(tax_rule.base_rate_per_night)) * taxable_guests * taxable_nights

        return TaxCalculationResult(
            booking_id=booking_id,
            total_guests=len(guests),
            taxable_guests=taxable_guests,
            exempt_guests=exemptions["total_exempt"],
            base_rate_per_night=Decimal(str(tax_rule.base_rate_per_night)),
            total_nights=total_nights,
            taxable_nights=taxable_nights,
            total_tax_amount=total_tax,
            exemption_breakdown=exemptions,
        )

    async def _calculate_exemptions(
        self,
        guests: Sequence[Guest],
        check_in_date: date,
        tax_rule: TaxRule,
    ) -> dict:
        """
        Calculate all tax exemptions for guests.

        Returns:
            Dictionary with exemption breakdown
        """
        exempt_minors = 0
        exempt_drivers = 0
        exempt_guides = 0
        exempt_other = 0

        # Age threshold from tax rule
        age_threshold = tax_rule.age_exemption_threshold or 14

        # Count exemptions by type
        for guest in guests:
            # Age-based exemption (highest priority)
            age_on_checkin = self._calculate_age(guest.date_of_birth, check_in_date)
            if age_on_checkin < age_threshold:
                exempt_minors += 1
                continue

            # Role-based exemptions
            if guest.role == GuestRole.BUS_DRIVER:
                exempt_drivers += 1
            elif guest.role == GuestRole.TOUR_GUIDE:
                exempt_guides += 1
            elif guest.is_tax_exempt:
                # Other exemptions (e.g., disabled, students)
                exempt_other += 1

        # Apply driver exemption ratio (e.g., 1 per 25 guests)
        driver_ratio = tax_rule.exemption_rules.get("bus_driver_ratio", 25)
        max_exempt_drivers = len(guests) // driver_ratio
        actual_exempt_drivers = min(exempt_drivers, max_exempt_drivers)

        # All tour guides are exempt (no ratio limit)
        actual_exempt_guides = exempt_guides

        total_exempt = (
            exempt_minors + actual_exempt_drivers + actual_exempt_guides + exempt_other
        )

        return {
            "total_exempt": total_exempt,
            "exempt_minors": exempt_minors,
            "exempt_minors_threshold": age_threshold,
            "exempt_drivers_count": exempt_drivers,
            "exempt_drivers_allowed": actual_exempt_drivers,
            "exempt_drivers_ratio": driver_ratio,
            "exempt_guides": actual_exempt_guides,
            "exempt_other": exempt_other,
        }

    def _calculate_age(self, birth_date: date, reference_date: date) -> int:
        """
        Calculate age on a specific date.

        Args:
            birth_date: Date of birth
            reference_date: Date to calculate age on (e.g., check-in date)

        Returns:
            Age in years
        """
        age = reference_date.year - birth_date.year

        # Adjust if birthday hasn't occurred yet this year
        if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
            age -= 1

        return age

    async def calculate_tax_for_date_range(
        self,
        start_date: date,
        end_date: date,
    ) -> list[TaxCalculationResult]:
        """
        Calculate tax for all bookings in a date range.

        Useful for monthly tax reporting to municipality.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of tax calculation results
        """
        # This would get all bookings in the date range
        # For now, returning empty list as we'd need BookingRepository
        return []

    async def get_tax_summary(
        self,
        results: list[TaxCalculationResult],
    ) -> dict:
        """
        Generate summary statistics for multiple tax calculations.

        Args:
            results: List of tax calculation results

        Returns:
            Summary dictionary
        """
        if not results:
            return {
                "total_bookings": 0,
                "total_guests": 0,
                "total_tax_collected": 0.0,
                "total_exempt_guests": 0,
            }

        total_tax = sum(result.total_tax_amount for result in results)
        total_guests = sum(result.total_guests for result in results)
        total_exempt = sum(result.exempt_guests for result in results)

        return {
            "total_bookings": len(results),
            "total_guests": total_guests,
            "total_taxable_guests": total_guests - total_exempt,
            "total_exempt_guests": total_exempt,
            "total_tax_collected": float(total_tax),
            "average_tax_per_booking": float(total_tax / len(results)) if results else 0.0,
        }

    async def validate_tax_configuration(self, tax_rule: TaxRule) -> list[str]:
        """
        Validate tax configuration for common issues.

        Args:
            tax_rule: Tax rule to validate

        Returns:
            List of validation warnings (empty if all good)
        """
        warnings = []

        if tax_rule.base_rate_per_night <= 0:
            warnings.append("Base rate must be greater than 0")

        if tax_rule.age_exemption_threshold and tax_rule.age_exemption_threshold < 0:
            warnings.append("Age exemption threshold cannot be negative")

        if tax_rule.age_exemption_threshold and tax_rule.age_exemption_threshold > 18:
            warnings.append("Age exemption threshold unusually high (> 18 years)")

        if tax_rule.max_taxable_nights is not None and tax_rule.max_taxable_nights <= 0:
            warnings.append("Max taxable nights must be greater than 0 if set")

        # Validate exemption rules
        driver_ratio = tax_rule.exemption_rules.get("bus_driver_ratio")
        if driver_ratio and driver_ratio <= 0:
            warnings.append("Bus driver ratio must be greater than 0")

        return warnings
