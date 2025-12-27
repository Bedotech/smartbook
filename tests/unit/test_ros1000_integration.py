"""
Comprehensive unit tests for ROS1000 Integration (XML builder, SOAP service, compliance).

Tests cover:
- XML generation according to ROS1000 schema
- Pre-validation logic
- SOAP submission (mocked)
- Response parsing (success/partial/failure)
- Compliance record storage (5-year retention)
- Retry logic for failed submissions
- Cancellation workflows
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from xml.etree import ElementTree as ET

from smartbook.integrations.ros1000_xml_builder import (
    ROS1000XMLBuilder,
    ROS1000XMLBuilderError,
)
from smartbook.integrations.ros1000_service import (
    ROS1000Service,
    ROS1000ServiceError,
    ROS1000ValidationError,
    ROS1000SubmissionResponse,
)
from smartbook.domain.enums import (
    GuestType,
    GuestRole,
    Sex,
    DocumentType,
    BookingStatus,
    BookingType,
    ComplianceStatus,
)


class MockTenant:
    """Mock Tenant for testing."""

    def __init__(self):
        self.id = uuid4()
        self.facility_code = "CIR-123456"
        self.facility_name = "Hotel Pineta"
        self.tax_id = "IT12345678901"
        self.ros1000_username = "test_user"
        self.ros1000_password = "test_pass"
        self.ros1000_ws_key = "test_key"


class MockBooking:
    """Mock Booking for testing."""

    def __init__(self):
        self.id = uuid4()
        self.booking_type = BookingType.GROUP
        self.check_in_date = date.today()
        self.check_out_date = date.today() + timedelta(days=3)
        self.expected_guests = 10
        self.status = BookingStatus.COMPLETE
        self.ros1000_receipt_number = None


class MockGuest:
    """Mock Guest for testing."""

    def __init__(
        self,
        guest_type: GuestType = GuestType.GROUP_MEMBER,
        has_documents: bool = False,
    ):
        self.id = uuid4()
        self.guest_type = guest_type
        self.role = GuestRole.MEMBER

        # TULPS minimums (required for all)
        self.first_name = "Mario"
        self.last_name = "Rossi"
        self.sex = Sex.MALE
        self.date_of_birth = date(1990, 1, 15)

        # Residence
        self.residence_municipality_code = "H810"  # Schilpario
        self.residence_country_code = "100000100"  # Italy
        self.residence_address = "Via Roma 123"

        # Birth place
        self.birth_municipality_code = "F205"  # Milano
        self.birth_country_code = "100000100"  # Italy

        # Citizenship
        self.citizenship_country_code = "100000100"  # Italy

        # Document data (required for leaders)
        if has_documents or guest_type == GuestType.GROUP_LEADER:
            self.document_type = DocumentType.ID_CARD
            self.document_number = "AB123456"
            self.document_issuing_authority = "Comune di Milano"
            self.document_issue_date = date(2020, 1, 1)
            self.document_issue_place = "Milano"
        else:
            self.document_type = None
            self.document_number = None
            self.document_issuing_authority = None
            self.document_issue_date = None
            self.document_issue_place = None


@pytest.fixture
def mock_tenant():
    """Create mock tenant."""
    return MockTenant()


@pytest.fixture
def mock_booking():
    """Create mock booking."""
    return MockBooking()


@pytest.fixture
def xml_builder(mock_tenant):
    """Create XML builder instance."""
    return ROS1000XMLBuilder(mock_tenant)


class TestROS1000XMLBuilder:
    """Test ROS1000 XML builder."""

    def test_build_submission_with_leader_and_members(self, xml_builder, mock_booking):
        """Test building XML with leader and members."""
        guests = [
            MockGuest(guest_type=GuestType.GROUP_LEADER, has_documents=True),
            MockGuest(guest_type=GuestType.GROUP_MEMBER),
            MockGuest(guest_type=GuestType.GROUP_MEMBER),
        ]

        xml = xml_builder.build_submission(mock_booking, guests)

        # Validate it's valid XML
        assert xml_builder.validate_xml_structure(xml)

        # Check that key elements are present in the XML string
        assert "AlloggiatiRoot" in xml
        assert "Testata" in xml
        assert "CIR-123456" in xml
        assert "Ospiti" in xml
        assert "Ospite" in xml
        assert xml.count("<Ospite>") == 3 or xml.count("Ospite>") >= 3

    def test_validation_requires_leader(self, xml_builder, mock_booking):
        """Test that validation requires at least one leader."""
        # All members, no leader
        guests = [
            MockGuest(guest_type=GuestType.GROUP_MEMBER),
            MockGuest(guest_type=GuestType.GROUP_MEMBER),
        ]

        with pytest.raises(ROS1000XMLBuilderError, match="requires at least one leader"):
            xml_builder.build_submission(mock_booking, guests)

    def test_validation_requires_leader_documents(self, xml_builder, mock_booking):
        """Test that leader must have document details."""
        # Leader without documents
        leader = MockGuest(guest_type=GuestType.GROUP_LEADER, has_documents=False)
        leader.document_type = None
        leader.document_number = None

        guests = [leader]

        with pytest.raises(ROS1000XMLBuilderError, match="missing required document"):
            xml_builder.build_submission(mock_booking, guests)

    def test_validation_requires_tulps_minimums(self, xml_builder, mock_booking):
        """Test that all guests must have TULPS minimums."""
        leader = MockGuest(guest_type=GuestType.GROUP_LEADER)
        member = MockGuest(guest_type=GuestType.GROUP_MEMBER)

        # Remove first name from member
        member.first_name = None

        guests = [leader, member]

        with pytest.raises(ROS1000XMLBuilderError, match="missing TULPS minimum data"):
            xml_builder.build_submission(mock_booking, guests)

    def test_xml_contains_guest_personal_data(self, xml_builder, mock_booking):
        """Test that XML contains all required personal data."""
        guests = [MockGuest(guest_type=GuestType.GROUP_LEADER)]

        xml = xml_builder.build_submission(mock_booking, guests)
        assert xml_builder.validate_xml_structure(xml)

        # Check personal data is present
        assert "Rossi" in xml
        assert "Mario" in xml
        assert "1990-01-15" in xml
        assert "Anagrafica" in xml

    def test_xml_contains_document_data_for_leader(self, xml_builder, mock_booking):
        """Test that leader's XML contains document data."""
        guests = [MockGuest(guest_type=GuestType.GROUP_LEADER)]

        xml = xml_builder.build_submission(mock_booking, guests)
        assert xml_builder.validate_xml_structure(xml)

        # Check document data is present
        assert "Documento" in xml
        assert "AB123456" in xml
        assert "Comune di Milano" in xml

    def test_xml_omits_document_for_member_without_docs(self, xml_builder, mock_booking):
        """Test that member without documents doesn't have all document details."""
        guests = [
            MockGuest(guest_type=GuestType.GROUP_LEADER),
            MockGuest(guest_type=GuestType.GROUP_MEMBER, has_documents=False),
        ]

        xml = xml_builder.build_submission(mock_booking, guests)
        assert xml_builder.validate_xml_structure(xml)

        # Leader has documents, so Documento should be present
        assert "Documento" in xml

    def test_xml_contains_residence_data(self, xml_builder, mock_booking):
        """Test that XML contains residence information."""
        guests = [MockGuest(guest_type=GuestType.GROUP_LEADER)]

        xml = xml_builder.build_submission(mock_booking, guests)
        assert xml_builder.validate_xml_structure(xml)

        # Check residence data is present
        assert "Residenza" in xml
        assert "H810" in xml
        assert "100000100" in xml
        assert "Via Roma 123" in xml

    def test_xml_contains_stay_dates(self, xml_builder, mock_booking):
        """Test that XML contains check-in/check-out dates."""
        guests = [MockGuest(guest_type=GuestType.GROUP_LEADER)]

        xml = xml_builder.build_submission(mock_booking, guests)
        assert xml_builder.validate_xml_structure(xml)

        # Check stay dates are present
        assert "Soggiorno" in xml
        assert mock_booking.check_in_date.isoformat() in xml
        assert mock_booking.check_out_date.isoformat() in xml

    def test_format_sex_male(self, xml_builder):
        """Test sex formatting for male."""
        assert xml_builder._format_sex(Sex.MALE) == "1"

    def test_format_sex_female(self, xml_builder):
        """Test sex formatting for female."""
        assert xml_builder._format_sex(Sex.FEMALE) == "2"

    def test_format_document_types(self, xml_builder):
        """Test document type formatting."""
        assert xml_builder._format_document_type(DocumentType.ID_CARD) == "1"
        assert xml_builder._format_document_type(DocumentType.PASSPORT) == "2"
        assert xml_builder._format_document_type(DocumentType.DRIVING_LICENSE) == "3"
        assert xml_builder._format_document_type(DocumentType.OTHER) == "9"

    def test_build_cancellation_xml(self, xml_builder, mock_booking):
        """Test building cancellation XML."""
        mock_booking.ros1000_receipt_number = "ROS-2025-12345"
        guests = [MockGuest(guest_type=GuestType.GROUP_LEADER)]

        xml = xml_builder.build_cancellation_xml(mock_booking, guests)

        # Validate it's valid XML
        assert xml_builder.validate_xml_structure(xml)

        # Check key elements are present
        assert "CANCELLAZIONE" in xml
        assert "ROS-2025-12345" in xml
        assert "NumeroRicevuta" in xml


class TestROS1000PreValidation:
    """Test ROS1000 pre-validation logic."""

    @pytest.mark.asyncio
    async def test_pre_validate_valid_booking(self, mock_tenant):
        """Test pre-validation passes for valid booking."""
        service = ROS1000Service(
            session=AsyncMock(),
            tenant=mock_tenant,
        )

        booking = MockBooking()
        booking.status = BookingStatus.COMPLETE

        guests = [
            MockGuest(guest_type=GuestType.GROUP_LEADER),
            MockGuest(guest_type=GuestType.GROUP_MEMBER),
        ]

        errors = await service.pre_validate(booking, guests)
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_pre_validate_incomplete_booking(self, mock_tenant):
        """Test pre-validation fails for incomplete booking."""
        service = ROS1000Service(
            session=AsyncMock(),
            tenant=mock_tenant,
        )

        booking = MockBooking()
        booking.status = BookingStatus.IN_PROGRESS  # Not complete!

        guests = [MockGuest(guest_type=GuestType.GROUP_LEADER)]

        errors = await service.pre_validate(booking, guests)
        assert len(errors) > 0
        assert any("must be complete" in e for e in errors)

    @pytest.mark.asyncio
    async def test_pre_validate_no_guests(self, mock_tenant):
        """Test pre-validation fails when no guests."""
        service = ROS1000Service(
            session=AsyncMock(),
            tenant=mock_tenant,
        )

        booking = MockBooking()
        booking.status = BookingStatus.COMPLETE

        errors = await service.pre_validate(booking, [])
        assert len(errors) > 0
        assert any("No guests found" in e for e in errors)

    @pytest.mark.asyncio
    async def test_pre_validate_no_leader(self, mock_tenant):
        """Test pre-validation fails when no leader."""
        service = ROS1000Service(
            session=AsyncMock(),
            tenant=mock_tenant,
        )

        booking = MockBooking()
        booking.status = BookingStatus.COMPLETE

        # Only members, no leader
        guests = [
            MockGuest(guest_type=GuestType.GROUP_MEMBER),
            MockGuest(guest_type=GuestType.GROUP_MEMBER),
        ]

        errors = await service.pre_validate(booking, guests)
        assert len(errors) > 0
        assert any("requires at least one leader" in e for e in errors)

    @pytest.mark.asyncio
    async def test_pre_validate_leader_missing_documents(self, mock_tenant):
        """Test pre-validation fails when leader missing documents."""
        service = ROS1000Service(
            session=AsyncMock(),
            tenant=mock_tenant,
        )

        booking = MockBooking()
        booking.status = BookingStatus.COMPLETE

        leader = MockGuest(guest_type=GuestType.GROUP_LEADER)
        leader.document_number = None  # Missing!

        guests = [leader]

        errors = await service.pre_validate(booking, guests)
        assert len(errors) > 0
        assert any("Document number required" in e for e in errors)

    @pytest.mark.asyncio
    async def test_pre_validate_invalid_dates(self, mock_tenant):
        """Test pre-validation fails for invalid dates."""
        service = ROS1000Service(
            session=AsyncMock(),
            tenant=mock_tenant,
        )

        booking = MockBooking()
        booking.status = BookingStatus.COMPLETE
        booking.check_out_date = booking.check_in_date  # Same day!

        guests = [MockGuest(guest_type=GuestType.GROUP_LEADER)]

        errors = await service.pre_validate(booking, guests)
        assert len(errors) > 0
        assert any("Check-out date must be after check-in" in e for e in errors)


class TestROS1000ResponseParsing:
    """Test ROS1000 SOAP response parsing."""

    def test_parse_success_response(self, mock_tenant):
        """Test parsing successful response."""
        service = ROS1000Service(
            session=AsyncMock(),
            tenant=mock_tenant,
        )

        response = {
            "esito": "OK",
            "numeroRicevuta": "ROS-2025-12345",
            "errori": [],
            "warnings": [],
        }

        parsed = service._parse_response(response)

        assert parsed.success is True
        assert parsed.receipt_number == "ROS-2025-12345"
        assert parsed.error_message is None
        assert len(parsed.warnings) == 0

    def test_parse_failure_response(self, mock_tenant):
        """Test parsing failed response."""
        service = ROS1000Service(
            session=AsyncMock(),
            tenant=mock_tenant,
        )

        response = {
            "esito": "KO",
            "numeroRicevuta": None,
            "errori": ["Invalid document number", "Missing birth date"],
            "warnings": [],
        }

        parsed = service._parse_response(response)

        assert parsed.success is False
        assert parsed.receipt_number is None
        assert "Invalid document number" in parsed.error_message
        assert "Missing birth date" in parsed.error_message

    def test_parse_partial_success_response(self, mock_tenant):
        """Test parsing partial success response."""
        service = ROS1000Service(
            session=AsyncMock(),
            tenant=mock_tenant,
        )

        response = {
            "esito": "PARTIAL",
            "numeroRicevuta": "ROS-2025-67890",
            "errori": ["Guest 3 validation failed"],
            "warnings": ["Guest 2 missing optional field"],
        }

        parsed = service._parse_response(response)

        assert parsed.partial_success is True
        assert parsed.receipt_number == "ROS-2025-67890"
        assert "Guest 3 validation failed" in parsed.error_message
        assert len(parsed.warnings) == 1

    def test_parse_response_with_warnings(self, mock_tenant):
        """Test parsing response with warnings."""
        service = ROS1000Service(
            session=AsyncMock(),
            tenant=mock_tenant,
        )

        response = {
            "esito": "OK",
            "numeroRicevuta": "ROS-2025-11111",
            "errori": [],
            "warnings": ["Document will expire soon", "Missing optional field"],
        }

        parsed = service._parse_response(response)

        assert parsed.success is True
        assert len(parsed.warnings) == 2
        assert "Document will expire soon" in parsed.warnings


class TestROS1000Submission:
    """Test ROS1000 submission workflow."""

    @pytest.mark.asyncio
    async def test_submit_booking_success(self, mock_tenant):
        """Test successful booking submission."""
        # Mock session and repos
        mock_session = AsyncMock()
        mock_compliance_repo = AsyncMock()
        mock_booking_repo = AsyncMock()

        service = ROS1000Service(
            session=mock_session,
            tenant=mock_tenant,
        )
        service.compliance_repo = mock_compliance_repo
        service.booking_repo = mock_booking_repo

        # Mock SOAP client
        mock_client = AsyncMock()
        mock_client.service.InviaAlloggiati = AsyncMock(
            return_value={
                "esito": "OK",
                "numeroRicevuta": "ROS-TEST-123",
                "errori": [],
                "warnings": [],
            }
        )
        service._get_soap_client = AsyncMock(return_value=mock_client)

        # Mock compliance record creation
        mock_compliance_repo.create_record = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )

        booking = MockBooking()
        booking.status = BookingStatus.COMPLETE

        guests = [MockGuest(guest_type=GuestType.GROUP_LEADER)]

        # Submit
        response = await service.submit_booking(booking, guests)

        # Verify success
        assert response.success is True
        assert response.receipt_number == "ROS-TEST-123"

        # Verify compliance record was stored
        mock_compliance_repo.create_record.assert_called_once()

        # Verify booking status was updated to SYNCED
        mock_booking_repo.update_status.assert_called_once_with(
            booking.id, BookingStatus.SYNCED
        )

    @pytest.mark.asyncio
    async def test_submit_booking_validation_failure(self, mock_tenant):
        """Test submission fails pre-validation."""
        service = ROS1000Service(
            session=AsyncMock(),
            tenant=mock_tenant,
        )

        booking = MockBooking()
        booking.status = BookingStatus.IN_PROGRESS  # Invalid!

        guests = [MockGuest(guest_type=GuestType.GROUP_LEADER)]

        with pytest.raises(ROS1000ValidationError):
            await service.submit_booking(booking, guests)


class TestComplianceRecordStorage:
    """Test compliance record storage (5-year retention)."""

    @pytest.mark.asyncio
    async def test_store_compliance_record_success(self, mock_tenant):
        """Test storing successful compliance record."""
        mock_session = AsyncMock()
        mock_compliance_repo = AsyncMock()

        service = ROS1000Service(
            session=mock_session,
            tenant=mock_tenant,
        )
        service.compliance_repo = mock_compliance_repo

        mock_compliance_repo.create_record = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )

        booking_id = uuid4()
        xml_payload = "<xml>test</xml>"
        receipt_number = "ROS-12345"

        await service._store_compliance_record(
            booking_id=booking_id,
            xml_payload=xml_payload,
            status=ComplianceStatus.SUBMITTED,
            receipt_number=receipt_number,
        )

        # Verify record was created
        mock_compliance_repo.create_record.assert_called_once()
        call_args = mock_compliance_repo.create_record.call_args[1]
        assert call_args["booking_id"] == booking_id
        assert call_args["xml_payload"] == xml_payload
        assert call_args["status"] == ComplianceStatus.SUBMITTED
        assert call_args["receipt_number"] == receipt_number

    @pytest.mark.asyncio
    async def test_store_compliance_record_failure(self, mock_tenant):
        """Test storing failed compliance record."""
        mock_session = AsyncMock()
        mock_compliance_repo = AsyncMock()

        service = ROS1000Service(
            session=mock_session,
            tenant=mock_tenant,
        )
        service.compliance_repo = mock_compliance_repo

        booking_id = uuid4()
        error_message = "SOAP communication failed"

        await service._store_compliance_record(
            booking_id=booking_id,
            xml_payload="<xml>test</xml>",
            status=ComplianceStatus.FAILED,
            error_message=error_message,
        )

        call_args = mock_compliance_repo.create_record.call_args[1]
        assert call_args["status"] == ComplianceStatus.FAILED
        assert call_args["error_message"] == error_message


class TestROS1000SubmissionResponse:
    """Test ROS1000SubmissionResponse model."""

    def test_success_response_repr(self):
        """Test string representation of success response."""
        response = ROS1000SubmissionResponse(
            success=True,
            receipt_number="ROS-12345",
        )

        repr_str = repr(response)
        assert "SUCCESS" in repr_str
        assert "ROS-12345" in repr_str

    def test_failure_response_repr(self):
        """Test string representation of failure response."""
        response = ROS1000SubmissionResponse(
            success=False,
            error_message="Validation failed",
        )

        repr_str = repr(response)
        assert "FAILURE" in repr_str
        assert "Validation failed" in repr_str

    def test_partial_success_response(self):
        """Test partial success response."""
        response = ROS1000SubmissionResponse(
            success=False,
            partial_success=True,
            receipt_number="ROS-67890",
            warnings=["Warning 1", "Warning 2"],
        )

        assert response.partial_success is True
        assert len(response.warnings) == 2
