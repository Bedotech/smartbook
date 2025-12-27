"""
Compliance Record Repository for ROS1000 transmission tracking.
"""

from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.models.compliance_record import ComplianceRecord
from smartbook.domain.enums import ComplianceStatus
from smartbook.repositories.base import BaseRepository


class ComplianceRecordRepository(BaseRepository[ComplianceRecord]):
    """
    Repository for ComplianceRecord operations.

    Handles storage and retrieval of compliance records
    with 5-year retention for TULPS compliance.
    """

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, ComplianceRecord)
        self.tenant_id = tenant_id

    async def create_record(
        self,
        booking_id: UUID,
        submission_type: str,
        xml_payload: str,
        status: ComplianceStatus,
        receipt_number: str | None = None,
        response_data: dict | None = None,
        error_message: str | None = None,
        submitted_at: datetime | None = None,
    ) -> ComplianceRecord:
        """
        Create a new compliance record.

        Args:
            booking_id: ID of the booking
            submission_type: Type of submission (ROS1000, CANCELLATION, etc.)
            xml_payload: XML payload sent
            status: Submission status
            receipt_number: Receipt number from ROS1000 (if successful)
            response_data: Full response data
            error_message: Error message (if failed)
            submitted_at: Submission timestamp (defaults to now)

        Returns:
            Created compliance record
        """
        record = ComplianceRecord(
            booking_id=booking_id,
            submission_type=submission_type,
            xml_payload=xml_payload,
            status=status,
            receipt_number=receipt_number,
            response_data=response_data or {},
            error_message=error_message,
            submitted_at=submitted_at or datetime.utcnow(),
            retry_count=0,
        )

        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        return record

    async def get_latest_for_booking(
        self,
        booking_id: UUID,
    ) -> ComplianceRecord | None:
        """
        Get the latest compliance record for a booking.

        Args:
            booking_id: Booking ID

        Returns:
            Latest compliance record or None
        """
        result = await self.session.execute(
            select(ComplianceRecord)
            .where(ComplianceRecord.booking_id == booking_id)
            .order_by(desc(ComplianceRecord.submitted_at))
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def get_all_for_booking(
        self,
        booking_id: UUID,
    ) -> Sequence[ComplianceRecord]:
        """
        Get all compliance records for a booking (chronological).

        Args:
            booking_id: Booking ID

        Returns:
            List of compliance records
        """
        result = await self.session.execute(
            select(ComplianceRecord)
            .where(ComplianceRecord.booking_id == booking_id)
            .order_by(ComplianceRecord.submitted_at)
        )

        return result.scalars().all()

    async def get_failed_submissions(
        self,
        limit: int = 100,
    ) -> Sequence[ComplianceRecord]:
        """
        Get failed submissions that may need retry.

        Args:
            limit: Maximum number of records

        Returns:
            List of failed compliance records
        """
        result = await self.session.execute(
            select(ComplianceRecord)
            .where(ComplianceRecord.status == ComplianceStatus.FAILED)
            .order_by(desc(ComplianceRecord.submitted_at))
            .limit(limit)
        )

        return result.scalars().all()

    async def get_by_receipt_number(
        self,
        receipt_number: str,
    ) -> ComplianceRecord | None:
        """
        Get compliance record by ROS1000 receipt number.

        Args:
            receipt_number: ROS1000 receipt number

        Returns:
            Compliance record or None
        """
        result = await self.session.execute(
            select(ComplianceRecord).where(
                ComplianceRecord.receipt_number == receipt_number
            )
        )

        return result.scalar_one_or_none()

    async def count_by_status(
        self,
        status: ComplianceStatus,
    ) -> int:
        """
        Count compliance records by status.

        Args:
            status: Status to count

        Returns:
            Count of records
        """
        result = await self.session.execute(
            select(ComplianceRecord).where(ComplianceRecord.status == status)
        )

        return len(result.scalars().all())

    async def get_records_for_retention_cleanup(
        self,
        cutoff_date: datetime,
    ) -> Sequence[ComplianceRecord]:
        """
        Get records older than retention period for cleanup.

        TULPS requires 5-year retention, but allows cleanup after that.

        Args:
            cutoff_date: Records before this date can be archived/deleted

        Returns:
            List of old compliance records
        """
        result = await self.session.execute(
            select(ComplianceRecord).where(
                ComplianceRecord.submitted_at < cutoff_date
            )
        )

        return result.scalars().all()
