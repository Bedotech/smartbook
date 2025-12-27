"""
Unit tests for Pydantic schemas validation.
"""

from datetime import date, timedelta
import pytest
from pydantic import ValidationError

from smartbook.domain.schemas.tenant import TenantCreate, TenantUpdate
from smartbook.domain.schemas.guest import GuestLeaderCreate, GuestMemberCreate
from smartbook.domain.schemas.booking import BookingCreate
from smartbook.domain.enums import (
    GuestRole,
    Sex,
    DocumentType,
    BookingType,
)


class TestTenantSchemas:
    """Test suite for Tenant schemas."""

    def test_tenant_create_valid(self):
        """Test creating a valid tenant."""
        tenant = TenantCreate(
            name="Hotel Test",
            facility_code="TEST123",
            email="test@example.com",
            phone="+39 123 456 7890",
        )
        assert tenant.name == "Hotel Test"
        assert tenant.facility_code == "TEST123"
        assert tenant.email == "test@example.com"

    def test_tenant_create_invalid_email(self):
        """Test that invalid email is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TenantCreate(
                name="Hotel Test",
                facility_code="TEST123",
                email="invalid-email",
            )
        assert "value is not a valid email address" in str(exc_info.value).lower()

    def test_tenant_create_missing_required(self):
        """Test that missing required fields are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TenantCreate(
                name="Hotel Test",
                # Missing facility_code
                email="test@example.com",
            )
        assert "facility_code" in str(exc_info.value).lower()


class TestGuestSchemas:
    """Test suite for Guest schemas."""

    def test_guest_leader_create_valid(self):
        """Test creating a valid group leader."""
        leader = GuestLeaderCreate(
            role=GuestRole.LEADER,
            first_name="Mario",
            last_name="Rossi",
            sex=Sex.MALE,
            date_of_birth=date(1990, 1, 15),
            place_of_birth_municipality_code="H810",
            place_of_birth_country_code="100000100",
            residence_municipality_code="H810",
            residence_country_code="100000100",
            residence_address="Via Roma 1",
            residence_zip_code="24020",
            document_type=DocumentType.ID_CARD,
            document_number="AB123456",
            document_issuing_authority="Comune di Bergamo",
            document_issue_date=date(2020, 1, 1),
            document_issue_place="Bergamo",
        )
        assert leader.first_name == "Mario"
        assert leader.last_name == "Rossi"
        assert leader.role == GuestRole.LEADER
        assert leader.document_type == DocumentType.ID_CARD

    def test_guest_leader_missing_document(self):
        """Test that leader without document details is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            GuestLeaderCreate(
                role=GuestRole.LEADER,
                first_name="Mario",
                last_name="Rossi",
                sex=Sex.MALE,
                date_of_birth=date(1990, 1, 15),
                # Missing document fields
            )
        assert "document" in str(exc_info.value).lower()

    def test_guest_member_create_valid(self):
        """Test creating a valid group member without documents."""
        member = GuestMemberCreate(
            role=GuestRole.MEMBER,
            first_name="Luigi",
            last_name="Verdi",
            sex=Sex.MALE,
            date_of_birth=date(1995, 5, 20),
            residence_municipality_code="H810",
            residence_country_code="100000100",
        )
        assert member.first_name == "Luigi"
        assert member.role == GuestRole.MEMBER
        # Document fields should be optional
        assert member.document_type is None
        assert member.document_number is None

    def test_guest_birth_date_future(self):
        """Test that future birth dates are rejected."""
        future_date = date.today() + timedelta(days=365)
        with pytest.raises(ValidationError) as exc_info:
            GuestMemberCreate(
                role=GuestRole.MEMBER,
                first_name="Test",
                last_name="User",
                sex=Sex.FEMALE,
                date_of_birth=future_date,
            )
        assert "cannot be in the future" in str(exc_info.value).lower()

    def test_guest_document_issue_date_future(self):
        """Test that future document issue dates are rejected."""
        future_date = date.today() + timedelta(days=30)
        with pytest.raises(ValidationError) as exc_info:
            GuestLeaderCreate(
                role=GuestRole.LEADER,
                first_name="Test",
                last_name="User",
                sex=Sex.MALE,
                date_of_birth=date(1990, 1, 1),
                document_type=DocumentType.PASSPORT,
                document_number="AB123456",
                document_issuing_authority="Test Authority",
                document_issue_date=future_date,
                document_issue_place="Test Place",
            )
        assert "cannot be in the future" in str(exc_info.value).lower()


class TestBookingSchemas:
    """Test suite for Booking schemas."""

    def test_booking_create_valid(self):
        """Test creating a valid booking."""
        booking = BookingCreate(
            booking_type=BookingType.GROUP,
            check_in_date=date.today() + timedelta(days=7),
            check_out_date=date.today() + timedelta(days=14),
            expected_guests=50,
            notes="Ski school group",
        )
        assert booking.booking_type == BookingType.GROUP
        assert booking.expected_guests == 50

    def test_booking_invalid_dates(self):
        """Test that check-out before check-in is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BookingCreate(
                booking_type=BookingType.GROUP,
                check_in_date=date.today() + timedelta(days=14),
                check_out_date=date.today() + timedelta(days=7),  # Before check-in!
                expected_guests=50,
            )
        assert "must be after check-in" in str(exc_info.value).lower()

    def test_booking_same_dates(self):
        """Test that same check-in and check-out dates are rejected."""
        same_date = date.today() + timedelta(days=7)
        with pytest.raises(ValidationError) as exc_info:
            BookingCreate(
                booking_type=BookingType.GROUP,
                check_in_date=same_date,
                check_out_date=same_date,
                expected_guests=50,
            )
        assert "must be after check-in" in str(exc_info.value).lower()

    def test_booking_zero_guests(self):
        """Test that zero or negative guests are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BookingCreate(
                booking_type=BookingType.GROUP,
                check_in_date=date.today() + timedelta(days=7),
                check_out_date=date.today() + timedelta(days=14),
                expected_guests=0,
            )
        assert "greater than 0" in str(exc_info.value).lower()
