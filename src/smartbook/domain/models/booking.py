"""
Booking model for group reservations.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, Date, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from smartbook.domain.enums import BookingType, BookingStatus
from smartbook.domain.models.base import Base

if TYPE_CHECKING:
    from smartbook.domain.models.tenant import Tenant
    from smartbook.domain.models.guest import Guest
    from smartbook.domain.models.compliance_record import ComplianceRecord


class Booking(Base):
    """
    Booking model representing a group reservation.

    Contains check-in/out dates, booking type, and the magic link token
    for guest data entry.
    """

    __tablename__ = "bookings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Multi-tenant isolation (property-based)
    property_id: Mapped[UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Booking details
    booking_type: Mapped[BookingType] = mapped_column(
        SQLEnum(BookingType, native_enum=False),
        nullable=False,
    )
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_guests: Mapped[int] = mapped_column(nullable=False)

    # Status tracking
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus, native_enum=False),
        default=BookingStatus.PENDING,
        nullable=False,
    )

    # Magic link authentication
    magic_link_token: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Cryptographically secure token for guest portal access",
    )
    token_expires_at: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="Token expires on check-out date for security",
    )

    # Optional notes
    notes: Mapped[str | None] = mapped_column(Text)

    # ROS1000 tracking
    ros1000_receipt_number: Mapped[str | None] = mapped_column(
        String(100),
        comment="ROS1000 receipt number from successful submission",
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="bookings", foreign_keys=[property_id])
    guests: Mapped[list["Guest"]] = relationship(
        "Guest",
        back_populates="booking",
        cascade="all, delete-orphan",
    )
    compliance_records: Mapped[list["ComplianceRecord"]] = relationship(
        "ComplianceRecord",
        back_populates="booking",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Booking {self.id} - {self.booking_type.value} ({self.status.value})>"
