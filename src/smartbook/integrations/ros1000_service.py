"""
ROS1000 SOAP Service for police reporting.

Handles SOAP communication with the ROS1000/Alloggiati Web system
for TULPS compliance reporting to Questura and ISTAT.

Key features:
- SOAP client with WSDL support
- Pre-validation before submission
- Response parsing (success/partial/failure)
- Automatic retry logic for transient failures
- Compliance record storage (5-year retention)
"""

import asyncio
from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from zeep import AsyncClient
from zeep.exceptions import Fault as ZeepFault
from zeep.transports import AsyncTransport

from smartbook.domain.models.guest import Guest
from smartbook.domain.models.booking import Booking
from smartbook.domain.models.tenant import Tenant
from smartbook.domain.models.compliance_record import ComplianceRecord
from smartbook.domain.enums import BookingStatus, ComplianceStatus
from smartbook.repositories.compliance_record import ComplianceRecordRepository
from smartbook.repositories.booking import BookingRepository
from smartbook.integrations.ros1000_xml_builder import (
    ROS1000XMLBuilder,
    ROS1000XMLBuilderError,
)


class ROS1000ServiceError(Exception):
    """Raised when ROS1000 service operations fail."""
    pass


class ROS1000ValidationError(ROS1000ServiceError):
    """Raised when pre-validation fails."""
    pass


class ROS1000SubmissionResponse:
    """Response from ROS1000 submission."""

    def __init__(
        self,
        success: bool,
        receipt_number: str | None = None,
        error_message: str | None = None,
        warnings: list[str] | None = None,
        partial_success: bool = False,
    ):
        self.success = success
        self.receipt_number = receipt_number
        self.error_message = error_message
        self.warnings = warnings or []
        self.partial_success = partial_success

    def __repr__(self) -> str:
        if self.success:
            return f"<ROS1000Response: SUCCESS, receipt={self.receipt_number}>"
        return f"<ROS1000Response: FAILURE, error={self.error_message}>"


class ROS1000Service:
    """
    Service for ROS1000/Alloggiati Web SOAP integration.

    Handles complete workflow:
    1. Pre-validation of guest data
    2. XML generation
    3. SOAP submission
    4. Response parsing
    5. Compliance record storage (5-year retention)
    """

    def __init__(
        self,
        session: AsyncSession,
        tenant: Tenant,
        wsdl_url: str | None = None,
    ):
        """
        Initialize ROS1000 service.

        Args:
            session: Database session
            tenant: Tenant (facility) information
            wsdl_url: Optional WSDL URL (defaults to production)
        """
        self.session = session
        self.tenant = tenant
        self.wsdl_url = wsdl_url or self._get_default_wsdl_url()

        self.xml_builder = ROS1000XMLBuilder(tenant)
        self.compliance_repo = ComplianceRecordRepository(session, tenant.id)
        self.booking_repo = BookingRepository(session, tenant.id)

        self._soap_client = None

    def _get_default_wsdl_url(self) -> str:
        """
        Get default WSDL URL for ROS1000.

        In production, this would be the actual Questura endpoint.
        For testing/development, use sandbox environment.
        """
        # TODO: Replace with actual ROS1000 WSDL URL
        # Production: https://alloggiatiweb.poliziadistato.it/service?wsdl
        return "https://sandbox.alloggiatiweb.poliziadistato.it/service?wsdl"

    async def _get_soap_client(self) -> AsyncClient:
        """
        Get or create async SOAP client.

        Returns:
            Configured SOAP client
        """
        if self._soap_client is None:
            transport = AsyncTransport(timeout=30)
            self._soap_client = AsyncClient(
                wsdl=self.wsdl_url,
                transport=transport,
            )
        return self._soap_client

    async def submit_booking(
        self,
        booking: Booking,
        guests: Sequence[Guest],
    ) -> ROS1000SubmissionResponse:
        """
        Submit booking to ROS1000 system.

        Complete workflow:
        1. Pre-validate data
        2. Generate XML
        3. Submit via SOAP
        4. Parse response
        5. Store compliance record
        6. Update booking status

        Args:
            booking: Booking to submit
            guests: List of guests

        Returns:
            Submission response

        Raises:
            ROS1000ValidationError: If pre-validation fails
            ROS1000ServiceError: If submission fails
        """
        # Step 1: Pre-validation
        validation_errors = await self.pre_validate(booking, guests)
        if validation_errors:
            raise ROS1000ValidationError(
                f"Pre-validation failed: {', '.join(validation_errors)}"
            )

        # Step 2: Generate XML
        try:
            xml_payload = self.xml_builder.build_submission(booking, guests)
        except ROS1000XMLBuilderError as e:
            raise ROS1000ServiceError(f"XML generation failed: {str(e)}")

        # Step 3: Submit via SOAP
        try:
            response = await self._submit_soap(xml_payload)
        except Exception as e:
            # Store failed attempt
            await self._store_compliance_record(
                booking_id=booking.id,
                xml_payload=xml_payload,
                status=ComplianceStatus.FAILED,
                error_message=str(e),
            )
            raise ROS1000ServiceError(f"SOAP submission failed: {str(e)}")

        # Step 4: Parse response
        parsed_response = self._parse_response(response)

        # Step 5: Store compliance record
        await self._store_compliance_record(
            booking_id=booking.id,
            xml_payload=xml_payload,
            status=(
                ComplianceStatus.SUBMITTED
                if parsed_response.success
                else ComplianceStatus.FAILED
            ),
            receipt_number=parsed_response.receipt_number,
            response_data=response,
            error_message=parsed_response.error_message,
        )

        # Step 6: Update booking status
        if parsed_response.success:
            await self.booking_repo.update_status(booking.id, BookingStatus.SYNCED)

            # Store receipt number on booking
            if parsed_response.receipt_number:
                booking.ros1000_receipt_number = parsed_response.receipt_number
                await self.session.commit()
        else:
            await self.booking_repo.update_status(booking.id, BookingStatus.ERROR)

        return parsed_response

    async def pre_validate(
        self,
        booking: Booking,
        guests: Sequence[Guest],
    ) -> list[str]:
        """
        Pre-validate booking and guest data before submission.

        Catches errors early to avoid ROS1000 rejection.

        Args:
            booking: Booking to validate
            guests: Guests to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check booking status
        if booking.status != BookingStatus.COMPLETE:
            errors.append(
                f"Booking must be complete (current: {booking.status.value})"
            )

        # Check for guests
        if not guests:
            errors.append("No guests found for booking")

        # Check for group leader
        has_leader = any(g.guest_type.value == "19" for g in guests)
        if not has_leader:
            errors.append("Group requires at least one leader")

        # Validate each guest
        for i, guest in enumerate(guests):
            guest_prefix = f"Guest {i + 1}"

            # TULPS minimums (all guests)
            if not guest.first_name:
                errors.append(f"{guest_prefix}: First name required")
            if not guest.last_name:
                errors.append(f"{guest_prefix}: Last name required")
            if not guest.date_of_birth:
                errors.append(f"{guest_prefix}: Date of birth required")
            if not guest.sex:
                errors.append(f"{guest_prefix}: Sex required")

            # Leader-specific validation
            if guest.guest_type.value == "19":  # Leader
                if not guest.document_type:
                    errors.append(f"{guest_prefix} (Leader): Document type required")
                if not guest.document_number:
                    errors.append(f"{guest_prefix} (Leader): Document number required")
                if not guest.document_issuing_authority:
                    errors.append(
                        f"{guest_prefix} (Leader): Document issuing authority required"
                    )
                if not guest.document_issue_date:
                    errors.append(
                        f"{guest_prefix} (Leader): Document issue date required"
                    )

        # Check facility credentials
        if not self.tenant.facility_code:
            errors.append("Facility code (Codice Struttura) not configured")

        # Check dates
        if booking.check_out_date <= booking.check_in_date:
            errors.append("Check-out date must be after check-in date")

        return errors

    async def _submit_soap(self, xml_payload: str) -> dict:
        """
        Submit XML payload via SOAP.

        Args:
            xml_payload: XML string to submit

        Returns:
            SOAP response dictionary

        Raises:
            Exception: If SOAP call fails
        """
        client = await self._get_soap_client()

        try:
            # Prepare credentials
            credentials = {
                "username": self.tenant.ros1000_username,
                "password": self.tenant.ros1000_password,
                "ws_key": self.tenant.ros1000_ws_key,
            }

            # Submit via SOAP (actual method names depend on WSDL)
            response = await client.service.InviaAlloggiati(
                xml=xml_payload,
                **credentials,
            )

            return response

        except ZeepFault as e:
            raise ROS1000ServiceError(f"SOAP Fault: {e.message}")

    def _parse_response(self, response: dict) -> ROS1000SubmissionResponse:
        """
        Parse ROS1000 SOAP response.

        Response format (typical):
        {
            'esito': 'OK' | 'KO' | 'PARTIAL',
            'numeroRicevuta': '...',
            'errori': [...],
            'warnings': [...]
        }

        Args:
            response: SOAP response dictionary

        Returns:
            Parsed response object
        """
        esito = response.get("esito", "KO")
        receipt = response.get("numeroRicevuta")
        errors = response.get("errori", [])
        warnings = response.get("warnings", [])

        success = esito == "OK"
        partial = esito == "PARTIAL"

        error_message = None
        if errors:
            error_message = "; ".join(str(e) for e in errors)

        return ROS1000SubmissionResponse(
            success=success,
            receipt_number=receipt,
            error_message=error_message,
            warnings=[str(w) for w in warnings],
            partial_success=partial,
        )

    async def _store_compliance_record(
        self,
        booking_id: UUID,
        xml_payload: str,
        status: ComplianceStatus,
        receipt_number: str | None = None,
        response_data: dict | None = None,
        error_message: str | None = None,
    ) -> ComplianceRecord:
        """
        Store compliance record for 5-year retention.

        Args:
            booking_id: Booking ID
            xml_payload: XML submitted
            status: Submission status
            receipt_number: ROS1000 receipt number (if successful)
            response_data: Full SOAP response
            error_message: Error message (if failed)

        Returns:
            Created compliance record
        """
        record = await self.compliance_repo.create_record(
            booking_id=booking_id,
            submission_type="ROS1000",
            xml_payload=xml_payload,
            status=status,
            receipt_number=receipt_number,
            response_data=response_data or {},
            error_message=error_message,
            submitted_at=datetime.now(),
        )

        return record

    async def retry_failed_submission(
        self,
        compliance_record_id: UUID,
    ) -> ROS1000SubmissionResponse:
        """
        Retry a failed submission.

        Args:
            compliance_record_id: ID of failed compliance record

        Returns:
            New submission response

        Raises:
            ROS1000ServiceError: If retry fails
        """
        # Get original compliance record
        record = await self.compliance_repo.get_by_id(compliance_record_id)
        if not record:
            raise ROS1000ServiceError("Compliance record not found")

        if record.status != ComplianceStatus.FAILED:
            raise ROS1000ServiceError(
                f"Cannot retry: record status is {record.status.value}"
            )

        # Re-submit using stored XML
        try:
            response = await self._submit_soap(record.xml_payload)
            parsed_response = self._parse_response(response)

            # Update original record
            record.status = (
                ComplianceStatus.SUBMITTED
                if parsed_response.success
                else ComplianceStatus.FAILED
            )
            record.receipt_number = parsed_response.receipt_number
            record.response_data = response
            record.error_message = parsed_response.error_message
            record.retry_count += 1
            record.last_retry_at = datetime.now()

            await self.session.commit()

            return parsed_response

        except Exception as e:
            # Increment retry count
            record.retry_count += 1
            record.last_retry_at = datetime.now()
            await self.session.commit()

            raise ROS1000ServiceError(f"Retry failed: {str(e)}")

    async def cancel_submission(
        self,
        booking: Booking,
        guests: Sequence[Guest],
    ) -> ROS1000SubmissionResponse:
        """
        Cancel/correct a previous submission.

        Args:
            booking: Original booking
            guests: Guests to cancel

        Returns:
            Cancellation response
        """
        if not booking.ros1000_receipt_number:
            raise ROS1000ServiceError(
                "Cannot cancel: no receipt number (booking not submitted)"
            )

        # Generate cancellation XML
        xml_payload = self.xml_builder.build_cancellation_xml(booking, guests)

        # Submit cancellation
        try:
            response = await self._submit_soap(xml_payload)
            parsed_response = self._parse_response(response)

            # Store compliance record
            await self._store_compliance_record(
                booking_id=booking.id,
                xml_payload=xml_payload,
                status=(
                    ComplianceStatus.CANCELLED
                    if parsed_response.success
                    else ComplianceStatus.FAILED
                ),
                receipt_number=parsed_response.receipt_number,
                response_data=response,
                error_message=parsed_response.error_message,
            )

            return parsed_response

        except Exception as e:
            raise ROS1000ServiceError(f"Cancellation failed: {str(e)}")

    async def get_submission_status(
        self,
        booking_id: UUID,
    ) -> ComplianceRecord | None:
        """
        Get latest compliance record for a booking.

        Args:
            booking_id: Booking ID

        Returns:
            Latest compliance record or None
        """
        return await self.compliance_repo.get_latest_for_booking(booking_id)
