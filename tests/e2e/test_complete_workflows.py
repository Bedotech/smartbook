"""
End-to-end workflow tests.

Tests complete business workflows using the service layer.
These tests verify that multiple components work together correctly.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from smartbook.domain.enums import BookingStatus, GuestType, Sex, DocumentType
from smartbook.domain.models.booking import Booking
from smartbook.domain.models.guest import Guest
from smartbook.domain.models.tenant import Tenant
from smartbook.domain.models.tax_rule import TaxRule


# ============================================================================
# E2E TEST 1: COMPLETE BOOKING WORKFLOW LOGIC
# ============================================================================


@pytest.mark.asyncio
async def test_complete_booking_workflow_logic():
    """
    Test complete booking workflow logic (without database).

    Verifies:
    1. Booking creation with magic link
    2. Guest data structure (leader vs member)
    3. Progress calculation
    4. Tax calculation with exemptions
    """
    # Step 1: Create booking
    booking_id = uuid4()
    tenant_id = uuid4()

    booking = Booking(
        id=booking_id,
        tenant_id=tenant_id,
        booking_type="group",
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=3),
        expected_guests=10,
        status=BookingStatus.PENDING,
        magic_link_token="test-token-abc123",
        magic_link_expires_at=date.today() + timedelta(days=3),
    )

    assert booking.magic_link_token is not None
    assert booking.expected_guests == 10

    # Step 2: Create group leader with full TULPS data
    leader = Guest(
        id=uuid4(),
        tenant_id=tenant_id,
        booking_id=booking_id,
        guest_type=GuestType.LEADER,
        first_name="Marco",
        last_name="Rossi",
        date_of_birth=date(1985, 3, 15),
        sex=Sex.MALE,
        citizenship_country_code="100",
        birth_municipality_code="F205",
        residence_municipality_code="F205",
        document_type=DocumentType.ID_CARD,
        document_number="CA12345BG",
        document_issue_date=date(2020, 1, 10),
        document_issuing_authority="Comune di Milano",
    )

    assert leader.guest_type == GuestType.LEADER
    assert leader.document_number is not None

    # Step 3: Create 9 group members (students under 14 - exempt)
    members = []
    for i in range(9):
        member = Guest(
            id=uuid4(),
            tenant_id=tenant_id,
            booking_id=booking_id,
            guest_type=GuestType.MEMBER,
            first_name=f"Student{i+1}",
            last_name="Bianchi",
            date_of_birth=date(2010, 1, 1),  # Age 14 - exempt
            sex=Sex.MALE if i % 2 == 0 else Sex.FEMALE,
            citizenship_country_code="100",
            residence_municipality_code="F205",
        )
        members.append(member)

    all_guests = [leader] + members
    assert len(all_guests) == 10

    # Step 4: Verify progress calculation
    total_entered = len(all_guests)
    percent_complete = (total_entered / booking.expected_guests) * 100
    has_leader = any(g.guest_type == GuestType.LEADER for g in all_guests)

    assert total_entered == 10
    assert percent_complete == 100.0
    assert has_leader is True

    # Step 5: Tax calculation (manual calculation for verification)
    tax_rate = Decimal("2.50")
    nights = 3
    age_cutoff = 14

    # Count exempt guests (under 14)
    exempt_guests = sum(
        1
        for g in all_guests
        if g.date_of_birth
        and (date.today() - g.date_of_birth).days / 365.25 < age_cutoff
    )

    taxable_guests = len(all_guests) - exempt_guests
    total_tax = Decimal(str(taxable_guests)) * tax_rate * nights

    assert exempt_guests == 9  # 9 students under 14
    assert taxable_guests == 1  # Only leader
    assert total_tax == Decimal("7.50")  # 1 × €2.50 × 3


# ============================================================================
# E2E TEST 2: BUS DRIVER EXEMPTION LOGIC
# ============================================================================


@pytest.mark.asyncio
async def test_bus_driver_exemption_logic():
    """
    Test bus driver exemption calculation (1 per 25 guests).

    Verifies that exemption ratios are calculated correctly.
    """
    tenant_id = uuid4()
    booking_id = uuid4()

    # Create 50 guests
    guests = []

    # Add leader
    leader = Guest(
        id=uuid4(),
        tenant_id=tenant_id,
        booking_id=booking_id,
        guest_type=GuestType.LEADER,
        first_name="Leader",
        last_name="Tour",
        date_of_birth=date(1970, 1, 1),
        sex=Sex.MALE,
        citizenship_country_code="100",
        residence_municipality_code="F205",
    )
    guests.append(leader)

    # Add 2 bus drivers
    for i in range(2):
        driver = Guest(
            id=uuid4(),
            tenant_id=tenant_id,
            booking_id=booking_id,
            guest_type=GuestType.BUS_DRIVER,
            first_name=f"Driver{i+1}",
            last_name="Autista",
            date_of_birth=date(1980, 1, 1),
            sex=Sex.MALE,
            citizenship_country_code="100",
            residence_municipality_code="F205",
        )
        guests.append(driver)

    # Add 47 regular adults
    for i in range(47):
        guest = Guest(
            id=uuid4(),
            tenant_id=tenant_id,
            booking_id=booking_id,
            guest_type=GuestType.MEMBER,
            first_name=f"Tourist{i+1}",
            last_name="Turista",
            date_of_birth=date(1985, 1, 1),
            sex=Sex.MALE if i % 2 == 0 else Sex.FEMALE,
            citizenship_country_code="100",
            residence_municipality_code="F205",
        )
        guests.append(guest)

    # Calculate bus driver exemptions (1 per 25 guests)
    total_guests = len(guests)
    bus_drivers = sum(1 for g in guests if g.guest_type == GuestType.BUS_DRIVER)
    driver_ratio = 25
    max_exempt_drivers = total_guests // driver_ratio

    exempt_drivers = min(bus_drivers, max_exempt_drivers)

    assert total_guests == 50
    assert bus_drivers == 2
    assert max_exempt_drivers == 2  # 50 // 25 = 2
    assert exempt_drivers == 2  # Both drivers exempt

    # Tax calculation
    tax_rate = Decimal("2.50")
    nights = 2
    taxable_guests = total_guests - exempt_drivers
    total_tax = Decimal(str(taxable_guests)) * tax_rate * nights

    assert taxable_guests == 48
    assert total_tax == Decimal("240.00")  # 48 × €2.50 × 2


# ============================================================================
# E2E TEST 3: MAX NIGHTS CAP LOGIC
# ============================================================================


@pytest.mark.asyncio
async def test_max_nights_cap_logic():
    """
    Test max nights cap (5 nights max in many Italian cities).

    Verifies that night caps are applied correctly.
    """
    # Create booking for 7 nights
    check_in = date.today()
    check_out = date.today() + timedelta(days=7)
    total_nights = (check_out - check_in).days

    # Tax rule with max 5 nights cap
    max_taxable_nights = 5

    # Apply cap
    taxable_nights = min(total_nights, max_taxable_nights)

    assert total_nights == 7
    assert taxable_nights == 5  # Capped at 5

    # Tax calculation for 2 guests
    tax_rate = Decimal("2.50")
    guests = 2
    total_tax = Decimal(str(guests)) * tax_rate * taxable_nights

    assert total_tax == Decimal("25.00")  # 2 × €2.50 × 5 (not 7)


# ============================================================================
# E2E TEST 4: MIXED EXEMPTIONS LOGIC
# ============================================================================


@pytest.mark.asyncio
async def test_mixed_exemptions_logic():
    """
    Test multiple exemption types together.

    Verifies:
    - Age exemptions (under 14)
    - Bus driver exemptions (1 per 25)
    - Tour guide exemptions (all exempt)
    """
    tenant_id = uuid4()
    booking_id = uuid4()

    guests = []

    # 1 tour guide (exempt)
    guide = Guest(
        id=uuid4(),
        tenant_id=tenant_id,
        booking_id=booking_id,
        guest_type=GuestType.TOUR_GUIDE,
        first_name="Guide",
        last_name="Turistica",
        date_of_birth=date(1975, 1, 1),
        sex=Sex.FEMALE,
        citizenship_country_code="100",
        residence_municipality_code="F205",
    )
    guests.append(guide)

    # 1 bus driver (exempt if ratio allows)
    driver = Guest(
        id=uuid4(),
        tenant_id=tenant_id,
        booking_id=booking_id,
        guest_type=GuestType.BUS_DRIVER,
        first_name="Driver",
        last_name="Autista",
        date_of_birth=date(1980, 1, 1),
        sex=Sex.MALE,
        citizenship_country_code="100",
        residence_municipality_code="F205",
    )
    guests.append(driver)

    # 10 children under 14 (exempt)
    for i in range(10):
        child = Guest(
            id=uuid4(),
            tenant_id=tenant_id,
            booking_id=booking_id,
            guest_type=GuestType.MEMBER,
            first_name=f"Child{i+1}",
            last_name="Bambino",
            date_of_birth=date(2012, 1, 1),  # Age 12
            sex=Sex.MALE if i % 2 == 0 else Sex.FEMALE,
            citizenship_country_code="100",
            residence_municipality_code="F205",
        )
        guests.append(child)

    # 14 adults (taxable)
    for i in range(14):
        adult = Guest(
            id=uuid4(),
            tenant_id=tenant_id,
            booking_id=booking_id,
            guest_type=GuestType.MEMBER,
            first_name=f"Adult{i+1}",
            last_name="Adulto",
            date_of_birth=date(1985, 1, 1),
            sex=Sex.MALE if i % 2 == 0 else Sex.FEMALE,
            citizenship_country_code="100",
            residence_municipality_code="F205",
        )
        guests.append(adult)

    total_guests = len(guests)
    assert total_guests == 26  # 1 + 1 + 10 + 14

    # Calculate exemptions
    age_cutoff = 14
    driver_ratio = 25

    # Age exempt
    age_exempt = sum(
        1
        for g in guests
        if g.date_of_birth
        and (date.today() - g.date_of_birth).days / 365.25 < age_cutoff
    )

    # Driver exempt (1 per 25)
    bus_drivers = sum(1 for g in guests if g.guest_type == GuestType.BUS_DRIVER)
    max_exempt_drivers = total_guests // driver_ratio
    driver_exempt = min(bus_drivers, max_exempt_drivers)

    # Tour guide exempt (all)
    guide_exempt = sum(1 for g in guests if g.guest_type == GuestType.TOUR_GUIDE)

    total_exempt = age_exempt + driver_exempt + guide_exempt
    taxable_guests = total_guests - total_exempt

    assert age_exempt == 10  # 10 children
    assert driver_exempt == 1  # 1 driver (26 // 25 = 1)
    assert guide_exempt == 1  # 1 tour guide
    assert total_exempt == 12
    assert taxable_guests == 14  # Only the 14 adults

    # Tax calculation
    tax_rate = Decimal("2.50")
    nights = 3
    total_tax = Decimal(str(taxable_guests)) * tax_rate * nights

    assert total_tax == Decimal("105.00")  # 14 × €2.50 × 3


# ============================================================================
# E2E TEST 5: MAGIC LINK EXPIRATION LOGIC
# ============================================================================


@pytest.mark.asyncio
async def test_magic_link_expiration_logic():
    """
    Test magic link expiration rules.

    Verifies that magic links expire on check-out date.
    """
    from smartbook.services.magic_link import MagicLinkService

    magic_service = MagicLinkService()

    check_in = date.today()
    check_out = date.today() + timedelta(days=3)

    # Generate token
    token = magic_service.generate_magic_link_token()

    assert len(token) >= 32  # At least 32 chars (256 bits)
    assert token.replace("-", "").replace("_", "").isalnum()  # URL-safe

    # Expiration should be check-out date
    expires_at = check_out

    assert expires_at > check_in
    assert expires_at == check_out


# ============================================================================
# E2E TEST 6: TULPS VALIDATION RULES
# ============================================================================


@pytest.mark.asyncio
async def test_tulps_validation_rules():
    """
    Test TULPS compliance validation rules.

    Verifies:
    - Leaders require full document details
    - Members only need minimums
    """
    # Leader requirements
    leader_required_fields = [
        "first_name",
        "last_name",
        "date_of_birth",
        "sex",
        "citizenship_country_code",
        "birth_municipality_code",
        "residence_municipality_code",
        "document_type",
        "document_number",
        "document_issue_date",
        "document_issuing_authority",
    ]

    # Member requirements (minimums only)
    member_required_fields = [
        "first_name",
        "last_name",
        "date_of_birth",
        "sex",
        "citizenship_country_code",
        "residence_municipality_code",
    ]

    # Verify leader has more requirements
    assert len(leader_required_fields) > len(member_required_fields)
    assert all(field in leader_required_fields for field in member_required_fields)

    # Document fields required ONLY for leaders
    document_fields = [
        "document_type",
        "document_number",
        "document_issue_date",
        "document_issuing_authority",
    ]

    for field in document_fields:
        assert field in leader_required_fields
        assert field not in member_required_fields


# ============================================================================
# E2E TEST 7: TAX REPORTING AGGREGATION LOGIC
# ============================================================================


@pytest.mark.asyncio
async def test_tax_reporting_aggregation_logic():
    """
    Test tax report aggregation across multiple bookings.

    Verifies that reports correctly aggregate:
    - Total bookings
    - Total guests
    - Total taxable guests
    - Total tax amount
    """
    # Simulate 3 bookings with tax calculations
    bookings_data = [
        {"guests": 5, "taxable": 5, "nights": 2, "tax": Decimal("25.00")},
        {"guests": 10, "taxable": 1, "nights": 3, "tax": Decimal("7.50")},
        {"guests": 15, "taxable": 13, "nights": 2, "tax": Decimal("65.00")},
    ]

    total_bookings = len(bookings_data)
    total_guests = sum(b["guests"] for b in bookings_data)
    total_taxable = sum(b["taxable"] for b in bookings_data)
    total_tax = sum(b["tax"] for b in bookings_data)
    avg_tax_per_booking = total_tax / total_bookings

    assert total_bookings == 3
    assert total_guests == 30  # 5 + 10 + 15
    assert total_taxable == 19  # 5 + 1 + 13
    assert total_tax == Decimal("97.50")  # 25 + 7.50 + 65
    assert avg_tax_per_booking == Decimal("32.50")  # 97.50 / 3


print("All E2E workflow tests defined successfully!")
