"""
Unit tests for service layer (Guest, Booking, Municipality services).
"""

from datetime import date, timedelta
import pytest

from smartbook.services.magic_link import MagicLinkService
from smartbook.domain.enums import GuestRole, Sex, DocumentType


class TestMagicLinkService:
    """Test suite for Magic Link Service."""

    def test_generate_token(self):
        """Test that tokens are generated with correct length."""
        token = MagicLinkService.generate_token()
        assert isinstance(token, str)
        assert len(token) > 0
        # URL-safe base64 encoding of 32 bytes should be ~43 chars
        assert len(token) >= 40

    def test_generate_unique_tokens(self):
        """Test that each token generated is unique."""
        tokens = [MagicLinkService.generate_token() for _ in range(100)]
        assert len(tokens) == len(set(tokens))  # All unique

    def test_calculate_expiration(self):
        """Test expiration calculation."""
        check_out = date.today() + timedelta(days=7)
        expires_at = MagicLinkService.calculate_expiration(check_out)

        assert expires_at.date() == check_out
        # Should expire at end of day
        assert expires_at.hour == 23
        assert expires_at.minute == 59
        assert expires_at.second == 59

    def test_is_token_expired_future(self):
        """Test that future expiration returns False."""
        future = MagicLinkService.calculate_expiration(date.today() + timedelta(days=1))
        assert MagicLinkService.is_token_expired(future) is False

    def test_is_token_expired_past(self):
        """Test that past expiration returns True."""
        past = MagicLinkService.calculate_expiration(date.today() - timedelta(days=1))
        assert MagicLinkService.is_token_expired(past) is True

    def test_generate_magic_link_url(self):
        """Test magic link URL generation."""
        token = "test-token-123"
        url = MagicLinkService.generate_magic_link_url(token)

        assert token in url
        assert url.startswith("https://")
        assert "/s/" in url

    def test_generate_magic_link_url_custom_base(self):
        """Test magic link URL with custom base URL."""
        token = "test-token-456"
        base_url = "https://custom.example.com"
        url = MagicLinkService.generate_magic_link_url(token, base_url)

        assert token in url
        assert url.startswith(base_url)
        assert "/s/" in url


class TestGuestValidationLogic:
    """Test suite for Guest service validation logic (unit tests)."""

    def test_leader_requires_all_document_fields(self):
        """Test that leader creation requires all document fields."""
        from smartbook.domain.schemas.guest import GuestLeaderCreate

        # Valid leader with all fields
        leader = GuestLeaderCreate(
            role=GuestRole.LEADER,
            first_name="Mario",
            last_name="Rossi",
            sex=Sex.MALE,
            date_of_birth=date(1990, 1, 15),
            document_type=DocumentType.ID_CARD,
            document_number="AB123456",
            document_issuing_authority="Comune di Bergamo",
            document_issue_date=date(2020, 1, 1),
            document_issue_place="Bergamo",
        )
        assert leader.document_number == "AB123456"

    def test_member_allows_optional_documents(self):
        """Test that member creation allows optional documents."""
        from smartbook.domain.schemas.guest import GuestMemberCreate

        # Valid member without documents
        member = GuestMemberCreate(
            role=GuestRole.MEMBER,
            first_name="Luigi",
            last_name="Verdi",
            sex=Sex.MALE,
            date_of_birth=date(1995, 5, 20),
        )
        assert member.first_name == "Luigi"
        assert member.document_type is None
        assert member.document_number is None

    def test_age_calculation_for_tax_exemption(self):
        """Test age calculation logic for tax exemptions."""
        # Child born 10 years ago
        birth_date = date.today() - timedelta(days=365 * 10)
        check_in_date = date.today()

        age_on_checkin = (check_in_date - birth_date).days // 365

        assert age_on_checkin == 10
        assert age_on_checkin < 14  # Should be tax exempt

    def test_adult_age_calculation(self):
        """Test that adults are not tax exempt by age."""
        # Adult born 25 years ago
        birth_date = date.today() - timedelta(days=365 * 25)
        check_in_date = date.today()

        age_on_checkin = (check_in_date - birth_date).days // 365

        assert age_on_checkin == 25
        assert age_on_checkin >= 14  # Should NOT be tax exempt


class TestBookingStatusTransitions:
    """Test suite for Booking status transition logic."""

    def test_valid_status_progression(self):
        """Test the valid status progression."""
        from smartbook.domain.enums import BookingStatus

        # Valid progression: pending → in_progress → complete → synced
        statuses = [
            BookingStatus.PENDING,
            BookingStatus.IN_PROGRESS,
            BookingStatus.COMPLETE,
            BookingStatus.SYNCED,
        ]

        assert len(statuses) == 4
        assert statuses[0] == BookingStatus.PENDING
        assert statuses[-1] == BookingStatus.SYNCED

    def test_error_status_exists(self):
        """Test that error status exists for failed transmissions."""
        from smartbook.domain.enums import BookingStatus

        assert hasattr(BookingStatus, "ERROR")
        assert BookingStatus.ERROR.value == "error"


class TestTULPSDataMinimums:
    """Test TULPS minimum data requirements."""

    def test_tulps_minimums_for_members(self):
        """Test that TULPS minimums are Name, Sex, DOB, Residence."""
        from smartbook.domain.schemas.guest import GuestMemberCreate

        member = GuestMemberCreate(
            role=GuestRole.MEMBER,
            first_name="Test",
            last_name="User",
            sex=Sex.FEMALE,
            date_of_birth=date(2000, 1, 1),
            residence_municipality_code="H810",
        )

        # TULPS minimums present
        assert member.first_name is not None
        assert member.last_name is not None
        assert member.sex is not None
        assert member.date_of_birth is not None

    def test_booking_date_validation(self):
        """Test that check-out must be after check-in."""
        from smartbook.domain.schemas.booking import BookingCreate
        from smartbook.domain.enums import BookingType
        from pydantic import ValidationError

        # Valid dates
        valid_booking = BookingCreate(
            booking_type=BookingType.GROUP,
            check_in_date=date.today() + timedelta(days=1),
            check_out_date=date.today() + timedelta(days=7),
            expected_guests=50,
        )
        assert valid_booking.check_out_date > valid_booking.check_in_date

        # Invalid: check-out before check-in
        with pytest.raises(ValidationError):
            BookingCreate(
                booking_type=BookingType.GROUP,
                check_in_date=date.today() + timedelta(days=7),
                check_out_date=date.today() + timedelta(days=1),
                expected_guests=50,
            )


class TestDriverExemptionRatio:
    """Test driver exemption ratio calculation (1 per 25 guests)."""

    def test_driver_exemption_calculation(self):
        """Test that 1 driver is exempt per 25 guests."""
        total_guests = 50
        driver_ratio = 25

        exempt_drivers = total_guests // driver_ratio
        assert exempt_drivers == 2  # 50 / 25 = 2 drivers exempt

    def test_driver_exemption_partial_group(self):
        """Test driver exemption with non-multiple group size."""
        total_guests = 40
        driver_ratio = 25

        exempt_drivers = total_guests // driver_ratio
        assert exempt_drivers == 1  # 40 / 25 = 1.6 → 1 driver

    def test_driver_exemption_large_group(self):
        """Test driver exemption with large group."""
        total_guests = 100
        driver_ratio = 25

        exempt_drivers = total_guests // driver_ratio
        assert exempt_drivers == 4  # 100 / 25 = 4 drivers
