"""
Compliance Record model for ROS1000 transmission tracking.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, ForeignKey, Enum as SQLEnum, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from smartbook.domain.enums import ComplianceStatus
from smartbook.domain.models.base import Base

if TYPE_CHECKING:
    from smartbook.domain.models.booking import Booking


class ComplianceRecord(Base):
    """
    Compliance Record model for tracking ROS1000 data transmissions.

    Stores the XML payload sent, response received, and digital receipts
    for the mandatory 5-year retention period (TULPS Art. 109).
    """

    __tablename__ = "compliance_records"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Link to booking
    booking_id: Mapped[UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Transmission tracking
    submission_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ROS1000",
        comment="Type of submission (ROS1000, CANCELLATION, etc.)",
    )
    submitted_at: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="When the submission was made",
    )
    status: Mapped[ComplianceStatus] = mapped_column(
        SQLEnum(ComplianceStatus, native_enum=False),
        nullable=False,
    )

    # ROS1000 receipt tracking
    receipt_number: Mapped[str | None] = mapped_column(
        String(100),
        comment="Receipt number (numeroRicevuta) returned by ROS1000",
    )
    ros1000_protocol_id: Mapped[str | None] = mapped_column(
        String(100),
        comment="Protocol ID returned by ROS1000 on success",
    )
    police_receipt_code: Mapped[str | None] = mapped_column(
        String(100),
        comment="Police receipt code from Questura/Alloggiati Web",
    )

    # Request and response data
    xml_payload: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full XML payload sent to ROS1000",
    )
    request_xml: Mapped[str | None] = mapped_column(
        Text,
        comment="Full XML SOAP request envelope (optional)",
    )
    response_xml: Mapped[str | None] = mapped_column(
        Text,
        comment="Full XML SOAP response from ROS1000",
    )
    response_data: Mapped[dict | None] = mapped_column(
        JSON,
        comment="Parsed response data as JSON",
    )

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(
        Text,
        comment="Error details for partial success or failure cases",
    )
    error_details: Mapped[dict | None] = mapped_column(
        JSON,
        comment="Structured error data (e.g., which guests failed validation)",
    )

    # Retry tracking
    retry_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="Number of retry attempts",
    )
    last_retry_at: Mapped[datetime | None] = mapped_column(
        comment="Timestamp of last retry attempt",
    )

    # Relationships
    booking: Mapped["Booking"] = relationship(
        "Booking",
        back_populates="compliance_records",
    )

    def __repr__(self) -> str:
        return f"<ComplianceRecord {self.status.value} at {self.transmitted_at}>"
