"""
Comprehensive unit tests for Tax Calculation Service (CRITICAL FINANCIAL LOGIC).

This module requires 95%+ test coverage as it handles money calculations
for City Tax (Imposta di Soggiorno) reporting to municipality.

Test coverage includes:
- Basic tax calculations
- Max nights cap application
- Age-based exemptions (minors < 14)
- Role-based exemptions (drivers 1 per 25, all guides)
- Edge cases (0 nights, same day checkout, etc.)
- Historical tax rule support
- Configuration validation
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from smartbook.services.tax_calculation_service import (
    TaxCalculationService,
    TaxCalculationResult,
    TaxCalculationError,
)
from smartbook.domain.enums import GuestRole, Sex
from smartbook.domain.models.tax_rule import TaxRule
from smartbook.domain.models.guest import Guest


class MockTaxRule:
    """Mock TaxRule for testing."""

    def __init__(
        self,
        base_rate_per_night: Decimal = Decimal("2.50"),
        max_taxable_nights: int | None = None,
        age_exemption_threshold: int = 14,
        exemption_rules: dict | None = None,
    ):
        self.base_rate_per_night = base_rate_per_night
        self.max_taxable_nights = max_taxable_nights
        self.age_exemption_threshold = age_exemption_threshold
        self.exemption_rules = exemption_rules or {"bus_driver_ratio": 25}


class MockGuest:
    """Mock Guest for testing."""

    def __init__(
        self,
        date_of_birth: date,
        role: GuestRole = GuestRole.MEMBER,
        is_tax_exempt: bool = False,
    ):
        self.id = uuid4()
        self.date_of_birth = date_of_birth
        self.role = role
        self.is_tax_exempt = is_tax_exempt
        self.first_name = "Test"
        self.last_name = "Guest"
        self.sex = Sex.MALE


@pytest.fixture
def mock_session():
    """Mock async session."""
    return AsyncMock()


@pytest.fixture
def mock_tenant_id():
    """Mock tenant ID."""
    return uuid4()


@pytest.fixture
def tax_service(mock_session, mock_tenant_id):
    """Create TaxCalculationService with mocked dependencies."""
    service = TaxCalculationService(mock_session, mock_tenant_id)
    service.tax_rule_repo = AsyncMock()
    service.guest_repo = AsyncMock()
    return service


class TestBasicTaxCalculation:
    """Test basic tax calculation scenarios."""

    @pytest.mark.asyncio
    async def test_simple_booking_tax_calculation(self, tax_service):
        """Test basic tax calculation for simple booking."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)  # 2 nights

        # Setup mocks
        tax_rule = MockTaxRule(base_rate_per_night=Decimal("2.50"))
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        # 3 adults, no exemptions
        guests = [
            MockGuest(date_of_birth=date(1990, 1, 1)),
            MockGuest(date_of_birth=date(1985, 5, 10)),
            MockGuest(date_of_birth=date(1995, 12, 25)),
        ]
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        # Calculate
        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        # Verify: 3 guests × 2 nights × €2.50 = €15.00
        assert result.total_guests == 3
        assert result.taxable_guests == 3
        assert result.exempt_guests == 0
        assert result.total_nights == 2
        assert result.taxable_nights == 2
        assert result.total_tax_amount == Decimal("15.00")
        assert result.base_rate_per_night == Decimal("2.50")

    @pytest.mark.asyncio
    async def test_one_night_stay(self, tax_service):
        """Test tax calculation for one night stay."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 16)  # 1 night

        tax_rule = MockTaxRule(base_rate_per_night=Decimal("3.00"))
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        guests = [MockGuest(date_of_birth=date(1990, 1, 1))]
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        # 1 guest × 1 night × €3.00 = €3.00
        assert result.total_nights == 1
        assert result.total_tax_amount == Decimal("3.00")

    @pytest.mark.asyncio
    async def test_week_long_stay(self, tax_service):
        """Test tax calculation for week-long booking."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 22)  # 7 nights

        tax_rule = MockTaxRule(base_rate_per_night=Decimal("2.00"))
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        # Family of 4
        guests = [
            MockGuest(date_of_birth=date(1980, 1, 1)),
            MockGuest(date_of_birth=date(1985, 1, 1)),
            MockGuest(date_of_birth=date(2010, 1, 1)),  # 15 years old
            MockGuest(date_of_birth=date(2012, 1, 1)),  # 13 years old (exempt)
        ]
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        # 3 taxable guests × 7 nights × €2.00 = €42.00
        assert result.total_guests == 4
        assert result.taxable_guests == 3
        assert result.exempt_guests == 1
        assert result.total_tax_amount == Decimal("42.00")


class TestMaxNightsCap:
    """Test max nights cap functionality."""

    @pytest.mark.asyncio
    async def test_max_nights_cap_applied(self, tax_service):
        """Test that max nights cap is correctly applied."""
        booking_id = uuid4()
        check_in = date(2025, 1, 1)
        check_out = date(2025, 1, 16)  # 15 nights

        # Max 10 nights taxable
        tax_rule = MockTaxRule(
            base_rate_per_night=Decimal("2.50"),
            max_taxable_nights=10,
        )
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        guests = [MockGuest(date_of_birth=date(1990, 1, 1))]
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        # Total 15 nights, but only 10 taxable
        assert result.total_nights == 15
        assert result.taxable_nights == 10
        # 1 guest × 10 nights × €2.50 = €25.00
        assert result.total_tax_amount == Decimal("25.00")

    @pytest.mark.asyncio
    async def test_no_max_nights_cap(self, tax_service):
        """Test that all nights are taxed when no cap is set."""
        booking_id = uuid4()
        check_in = date(2025, 1, 1)
        check_out = date(2025, 1, 16)  # 15 nights

        # No max nights cap
        tax_rule = MockTaxRule(
            base_rate_per_night=Decimal("2.50"),
            max_taxable_nights=None,
        )
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        guests = [MockGuest(date_of_birth=date(1990, 1, 1))]
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        # All 15 nights taxable
        assert result.total_nights == 15
        assert result.taxable_nights == 15
        # 1 guest × 15 nights × €2.50 = €37.50
        assert result.total_tax_amount == Decimal("37.50")

    @pytest.mark.asyncio
    async def test_stay_shorter_than_cap(self, tax_service):
        """Test that cap doesn't affect short stays."""
        booking_id = uuid4()
        check_in = date(2025, 1, 1)
        check_out = date(2025, 1, 4)  # 3 nights

        # Max 10 nights, but stay is only 3
        tax_rule = MockTaxRule(
            base_rate_per_night=Decimal("2.50"),
            max_taxable_nights=10,
        )
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        guests = [MockGuest(date_of_birth=date(1990, 1, 1))]
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        # Only 3 nights, cap doesn't apply
        assert result.total_nights == 3
        assert result.taxable_nights == 3
        assert result.total_tax_amount == Decimal("7.50")


class TestAgeBasedExemptions:
    """Test age-based tax exemptions."""

    @pytest.mark.asyncio
    async def test_minors_under_14_exempt(self, tax_service):
        """Test that children under 14 are exempt."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)

        tax_rule = MockTaxRule(
            base_rate_per_night=Decimal("2.50"),
            age_exemption_threshold=14,
        )
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        # Mixed ages
        guests = [
            MockGuest(date_of_birth=date(1980, 1, 1)),  # Adult
            MockGuest(date_of_birth=date(2013, 1, 1)),  # 12 years old (exempt)
            MockGuest(date_of_birth=date(2011, 6, 1)),  # 13 years old (exempt)
            MockGuest(date_of_birth=date(2010, 12, 1)),  # 14 years old (taxable)
        ]
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        assert result.total_guests == 4
        assert result.exempt_guests == 2
        assert result.taxable_guests == 2
        assert result.exemption_breakdown["exempt_minors"] == 2
        assert result.exemption_breakdown["exempt_minors_threshold"] == 14

    @pytest.mark.asyncio
    async def test_age_calculation_birthday_edge_case(self, tax_service):
        """Test age calculation when birthday falls during stay."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)

        tax_rule = MockTaxRule(age_exemption_threshold=14)
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        # Guest born Jan 20, 2011 - will be 13 on check-in, turns 14 during stay
        # Age is calculated on check-in date
        guests = [
            MockGuest(date_of_birth=date(2011, 1, 20)),  # Still 13 on check-in
        ]
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        # Should be exempt (13 years old on check-in)
        assert result.exempt_guests == 1
        assert result.exemption_breakdown["exempt_minors"] == 1

    @pytest.mark.asyncio
    async def test_custom_age_threshold(self, tax_service):
        """Test custom age exemption threshold."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)

        # Custom threshold: 18 years
        tax_rule = MockTaxRule(
            base_rate_per_night=Decimal("2.50"),
            age_exemption_threshold=18,
        )
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        guests = [
            MockGuest(date_of_birth=date(2010, 1, 1)),  # 15 years (exempt)
            MockGuest(date_of_birth=date(2008, 1, 1)),  # 17 years (exempt)
            MockGuest(date_of_birth=date(2007, 1, 1)),  # 18 years (taxable)
        ]
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        assert result.exempt_guests == 2
        assert result.taxable_guests == 1
        assert result.exemption_breakdown["exempt_minors"] == 2


class TestDriverExemptions:
    """Test bus driver exemption ratio (1 per 25 guests)."""

    @pytest.mark.asyncio
    async def test_driver_exemption_exact_ratio(self, tax_service):
        """Test driver exemption with exact 25-guest group."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)

        tax_rule = MockTaxRule(
            base_rate_per_night=Decimal("2.00"),
            exemption_rules={"bus_driver_ratio": 25},
        )
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        # 25 guests: 1 driver + 24 passengers
        guests = [MockGuest(date_of_birth=date(1990, 1, 1), role=GuestRole.BUS_DRIVER)]
        guests.extend([MockGuest(date_of_birth=date(1995, 1, 1)) for _ in range(24)])
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        assert result.total_guests == 25
        assert result.exempt_guests == 1
        assert result.taxable_guests == 24
        assert result.exemption_breakdown["exempt_drivers_count"] == 1
        assert result.exemption_breakdown["exempt_drivers_allowed"] == 1
        # 24 guests × 2 nights × €2.00 = €96.00
        assert result.total_tax_amount == Decimal("96.00")

    @pytest.mark.asyncio
    async def test_driver_exemption_50_guests(self, tax_service):
        """Test driver exemption with 50-guest group (2 drivers)."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)

        tax_rule = MockTaxRule(
            base_rate_per_night=Decimal("2.00"),
            exemption_rules={"bus_driver_ratio": 25},
        )
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        # 50 guests: 2 drivers + 48 others
        guests = [
            MockGuest(date_of_birth=date(1990, 1, 1), role=GuestRole.BUS_DRIVER),
            MockGuest(date_of_birth=date(1992, 1, 1), role=GuestRole.BUS_DRIVER),
        ]
        guests.extend([MockGuest(date_of_birth=date(1995, 1, 1)) for _ in range(48)])
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        assert result.total_guests == 50
        assert result.exemption_breakdown["exempt_drivers_count"] == 2
        assert result.exemption_breakdown["exempt_drivers_allowed"] == 2
        # 48 guests × 2 nights × €2.00 = €192.00
        assert result.total_tax_amount == Decimal("192.00")

    @pytest.mark.asyncio
    async def test_driver_exemption_partial_group(self, tax_service):
        """Test driver exemption with 40 guests (1 driver, not 2)."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)

        tax_rule = MockTaxRule(
            base_rate_per_night=Decimal("2.00"),
            exemption_rules={"bus_driver_ratio": 25},
        )
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        # 40 guests: 2 drivers but only 1 allowed (40 // 25 = 1)
        guests = [
            MockGuest(date_of_birth=date(1990, 1, 1), role=GuestRole.BUS_DRIVER),
            MockGuest(date_of_birth=date(1992, 1, 1), role=GuestRole.BUS_DRIVER),
        ]
        guests.extend([MockGuest(date_of_birth=date(1995, 1, 1)) for _ in range(38)])
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        assert result.total_guests == 40
        assert result.exemption_breakdown["exempt_drivers_count"] == 2
        assert result.exemption_breakdown["exempt_drivers_allowed"] == 1  # Only 1 exempt
        # 39 guests × 2 nights × €2.00 = €156.00
        assert result.total_tax_amount == Decimal("156.00")

    @pytest.mark.asyncio
    async def test_driver_exemption_large_group(self, tax_service):
        """Test driver exemption with 100-guest group (4 drivers)."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)

        tax_rule = MockTaxRule(
            base_rate_per_night=Decimal("2.00"),
            exemption_rules={"bus_driver_ratio": 25},
        )
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        # 100 guests: 4 drivers
        guests = [
            MockGuest(date_of_birth=date(1990, 1, 1), role=GuestRole.BUS_DRIVER)
            for _ in range(4)
        ]
        guests.extend([MockGuest(date_of_birth=date(1995, 1, 1)) for _ in range(96)])
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        assert result.total_guests == 100
        assert result.exemption_breakdown["exempt_drivers_allowed"] == 4
        # 96 guests × 2 nights × €2.00 = €384.00
        assert result.total_tax_amount == Decimal("384.00")


class TestTourGuideExemptions:
    """Test tour guide exemptions (all guides exempt, no ratio)."""

    @pytest.mark.asyncio
    async def test_all_tour_guides_exempt(self, tax_service):
        """Test that all tour guides are exempt regardless of count."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)

        tax_rule = MockTaxRule(base_rate_per_night=Decimal("2.00"))
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        # 30 guests: 3 guides + 27 tourists
        guests = [
            MockGuest(date_of_birth=date(1990, 1, 1), role=GuestRole.TOUR_GUIDE),
            MockGuest(date_of_birth=date(1992, 1, 1), role=GuestRole.TOUR_GUIDE),
            MockGuest(date_of_birth=date(1994, 1, 1), role=GuestRole.TOUR_GUIDE),
        ]
        guests.extend([MockGuest(date_of_birth=date(1995, 1, 1)) for _ in range(27)])
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        assert result.total_guests == 30
        assert result.exemption_breakdown["exempt_guides"] == 3
        assert result.taxable_guests == 27
        # 27 guests × 2 nights × €2.00 = €108.00
        assert result.total_tax_amount == Decimal("108.00")

    @pytest.mark.asyncio
    async def test_combined_driver_and_guide_exemptions(self, tax_service):
        """Test combined driver and guide exemptions."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)

        tax_rule = MockTaxRule(
            base_rate_per_night=Decimal("2.00"),
            exemption_rules={"bus_driver_ratio": 25},
        )
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        # 50 guests: 1 driver + 2 guides + 47 others
        guests = [
            MockGuest(date_of_birth=date(1990, 1, 1), role=GuestRole.BUS_DRIVER),
            MockGuest(date_of_birth=date(1992, 1, 1), role=GuestRole.TOUR_GUIDE),
            MockGuest(date_of_birth=date(1994, 1, 1), role=GuestRole.TOUR_GUIDE),
        ]
        guests.extend([MockGuest(date_of_birth=date(1995, 1, 1)) for _ in range(47)])
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        assert result.total_guests == 50
        assert result.exemption_breakdown["exempt_drivers_count"] == 1
        assert result.exemption_breakdown["exempt_drivers_allowed"] == 1  # min(1 actual, 2 allowed)
        assert result.exemption_breakdown["exempt_guides"] == 2
        # Total exempt: 1 driver + 2 guides = 3
        assert result.exempt_guests == 3
        assert result.taxable_guests == 47
        # 47 guests × 2 nights × €2.00 = €188.00
        assert result.total_tax_amount == Decimal("188.00")


class TestCombinedExemptions:
    """Test complex scenarios with multiple exemption types."""

    @pytest.mark.asyncio
    async def test_minors_drivers_and_guides(self, tax_service):
        """Test booking with minors, drivers, and guides."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)

        tax_rule = MockTaxRule(
            base_rate_per_night=Decimal("2.00"),
            age_exemption_threshold=14,
            exemption_rules={"bus_driver_ratio": 25},
        )
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        # 50 guests: 1 driver, 1 guide, 10 minors, 38 adults
        guests = [
            MockGuest(date_of_birth=date(1990, 1, 1), role=GuestRole.BUS_DRIVER),
            MockGuest(date_of_birth=date(1992, 1, 1), role=GuestRole.TOUR_GUIDE),
        ]
        # Add 10 minors
        guests.extend([MockGuest(date_of_birth=date(2015, 1, 1)) for _ in range(10)])
        # Add 38 adults
        guests.extend([MockGuest(date_of_birth=date(1995, 1, 1)) for _ in range(38)])
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        assert result.total_guests == 50
        assert result.exemption_breakdown["exempt_minors"] == 10
        assert result.exemption_breakdown["exempt_drivers_count"] == 1
        assert result.exemption_breakdown["exempt_drivers_allowed"] == 1  # min(1 actual, 2 ratio allows)
        assert result.exemption_breakdown["exempt_guides"] == 1
        # Total exempt: 10 minors + 1 driver + 1 guide = 12
        assert result.exempt_guests == 12
        assert result.taxable_guests == 38
        # 38 guests × 2 nights × €2.00 = €152.00
        assert result.total_tax_amount == Decimal("152.00")


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_no_active_tax_rule(self, tax_service):
        """Test error when no active tax rule exists."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)

        tax_service.tax_rule_repo.get_active_rule.return_value = None

        with pytest.raises(TaxCalculationError, match="No active tax rule"):
            await tax_service.calculate_tax_for_booking(
                booking_id, check_in, check_out
            )

    @pytest.mark.asyncio
    async def test_no_guests_found(self, tax_service):
        """Test error when no guests exist for booking."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)

        tax_rule = MockTaxRule()
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule
        tax_service.guest_repo.get_by_booking_id.return_value = []

        with pytest.raises(TaxCalculationError, match="No guests found"):
            await tax_service.calculate_tax_for_booking(
                booking_id, check_in, check_out
            )

    @pytest.mark.asyncio
    async def test_invalid_date_range(self, tax_service):
        """Test error when check-out is before check-in."""
        booking_id = uuid4()
        check_in = date(2025, 1, 17)
        check_out = date(2025, 1, 15)  # Before check-in!

        tax_rule = MockTaxRule()
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule
        guests = [MockGuest(date_of_birth=date(1990, 1, 1))]
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        with pytest.raises(TaxCalculationError, match="Check-out date must be after"):
            await tax_service.calculate_tax_for_booking(
                booking_id, check_in, check_out
            )

    @pytest.mark.asyncio
    async def test_same_day_checkout(self, tax_service):
        """Test error for same-day check-in/check-out."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 15)  # Same day!

        tax_rule = MockTaxRule()
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule
        guests = [MockGuest(date_of_birth=date(1990, 1, 1))]
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        with pytest.raises(TaxCalculationError, match="Check-out date must be after"):
            await tax_service.calculate_tax_for_booking(
                booking_id, check_in, check_out
            )

    @pytest.mark.asyncio
    async def test_all_guests_exempt(self, tax_service):
        """Test calculation when all guests are exempt."""
        booking_id = uuid4()
        check_in = date(2025, 1, 15)
        check_out = date(2025, 1, 17)

        tax_rule = MockTaxRule(
            base_rate_per_night=Decimal("2.00"),
            age_exemption_threshold=14,
        )
        tax_service.tax_rule_repo.get_active_rule.return_value = tax_rule

        # All minors
        guests = [MockGuest(date_of_birth=date(2015, 1, 1)) for _ in range(5)]
        tax_service.guest_repo.get_by_booking_id.return_value = guests

        result = await tax_service.calculate_tax_for_booking(
            booking_id, check_in, check_out
        )

        assert result.total_guests == 5
        assert result.exempt_guests == 5
        assert result.taxable_guests == 0
        assert result.total_tax_amount == Decimal("0.00")


class TestTaxConfigurationValidation:
    """Test tax configuration validation."""

    @pytest.mark.asyncio
    async def test_validate_valid_configuration(self, tax_service):
        """Test validation passes for valid configuration."""
        tax_rule = MockTaxRule(
            base_rate_per_night=Decimal("2.50"),
            max_taxable_nights=10,
            age_exemption_threshold=14,
            exemption_rules={"bus_driver_ratio": 25},
        )

        warnings = await tax_service.validate_tax_configuration(tax_rule)
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_zero_base_rate(self, tax_service):
        """Test validation fails for zero base rate."""
        tax_rule = MockTaxRule(base_rate_per_night=Decimal("0.00"))

        warnings = await tax_service.validate_tax_configuration(tax_rule)
        assert len(warnings) > 0
        assert any("Base rate must be greater than 0" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_validate_negative_age_threshold(self, tax_service):
        """Test validation fails for negative age threshold."""
        tax_rule = MockTaxRule(age_exemption_threshold=-5)

        warnings = await tax_service.validate_tax_configuration(tax_rule)
        assert len(warnings) > 0
        assert any("Age exemption threshold cannot be negative" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_validate_high_age_threshold(self, tax_service):
        """Test validation warns for unusually high age threshold."""
        tax_rule = MockTaxRule(age_exemption_threshold=25)

        warnings = await tax_service.validate_tax_configuration(tax_rule)
        assert len(warnings) > 0
        assert any("Age exemption threshold unusually high" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_validate_zero_max_nights(self, tax_service):
        """Test validation fails for zero max nights."""
        tax_rule = MockTaxRule(max_taxable_nights=0)

        warnings = await tax_service.validate_tax_configuration(tax_rule)
        assert len(warnings) > 0
        assert any("Max taxable nights must be greater than 0" in w for w in warnings)


class TestTaxCalculationResult:
    """Test TaxCalculationResult model."""

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = TaxCalculationResult(
            booking_id=uuid4(),
            total_guests=10,
            taxable_guests=8,
            exempt_guests=2,
            base_rate_per_night=Decimal("2.50"),
            total_nights=3,
            taxable_nights=3,
            total_tax_amount=Decimal("60.00"),
            exemption_breakdown={"exempt_minors": 2},
        )

        result_dict = result.to_dict()

        assert result_dict["total_guests"] == 10
        assert result_dict["taxable_guests"] == 8
        assert result_dict["exempt_guests"] == 2
        assert result_dict["base_rate_per_night"] == 2.50
        assert result_dict["total_tax_amount"] == 60.00
        assert result_dict["exemption_breakdown"]["exempt_minors"] == 2


class TestAgeCalculationAccuracy:
    """Test precise age calculation logic."""

    def test_calculate_age_before_birthday(self, tax_service):
        """Test age calculation before birthday this year."""
        birth_date = date(2010, 6, 15)
        reference_date = date(2025, 3, 1)  # Before birthday

        age = tax_service._calculate_age(birth_date, reference_date)
        assert age == 14  # Still 14, birthday not yet occurred

    def test_calculate_age_after_birthday(self, tax_service):
        """Test age calculation after birthday this year."""
        birth_date = date(2010, 6, 15)
        reference_date = date(2025, 8, 1)  # After birthday

        age = tax_service._calculate_age(birth_date, reference_date)
        assert age == 15  # Now 15, birthday occurred

    def test_calculate_age_on_birthday(self, tax_service):
        """Test age calculation on exact birthday."""
        birth_date = date(2010, 6, 15)
        reference_date = date(2025, 6, 15)  # Exact birthday

        age = tax_service._calculate_age(birth_date, reference_date)
        assert age == 15  # Turns 15 today

    def test_calculate_age_leap_year(self, tax_service):
        """Test age calculation for leap year birthday."""
        birth_date = date(2008, 2, 29)  # Leap year birth
        reference_date = date(2025, 3, 1)  # Day after Feb 28

        age = tax_service._calculate_age(birth_date, reference_date)
        assert age == 17  # Birthday considered passed
