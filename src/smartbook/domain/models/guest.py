"""
Guest model for individual guest data.
"""

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, Date, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from smartbook.domain.enums import GuestRole, Sex, DocumentType
from smartbook.domain.models.base import Base

if TYPE_CHECKING:
    from smartbook.domain.models.booking import Booking


class Guest(Base):
    """
    Guest model representing an individual staying at the property.

    For Group Leaders: Full document details required (TULPS Art. 109).
    For Group Members: Only TULPS minimums (name, sex, DOB, residence).
    """

    __tablename__ = "guests"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Link to booking
    booking_id: Mapped[UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Guest role
    role: Mapped[GuestRole] = mapped_column(
        SQLEnum(GuestRole, native_enum=False),
        nullable=False,
    )

    # TULPS minimum data (required for all guests)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sex: Mapped[Sex] = mapped_column(
        SQLEnum(Sex, native_enum=False),
        nullable=False,
    )
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)

    # Place of birth
    place_of_birth_municipality_code: Mapped[str | None] = mapped_column(
        String(10),
        comment="ISTAT Codice Catastale (e.g., H810 for Schilpario)",
    )
    place_of_birth_country_code: Mapped[str | None] = mapped_column(
        String(20),
        comment="ISTAT country code (e.g., 100000100 for Italy)",
    )

    # Residence
    residence_municipality_code: Mapped[str | None] = mapped_column(
        String(10),
        comment="ISTAT Codice Catastale",
    )
    residence_country_code: Mapped[str | None] = mapped_column(
        String(20),
        comment="ISTAT country code",
    )
    residence_address: Mapped[str | None] = mapped_column(String(255))
    residence_zip_code: Mapped[str | None] = mapped_column(String(20))

    # Document details (required only for Group/Family Leaders)
    document_type: Mapped[DocumentType | None] = mapped_column(
        SQLEnum(DocumentType, native_enum=False),
    )
    document_number: Mapped[str | None] = mapped_column(String(50))
    document_issuing_authority: Mapped[str | None] = mapped_column(String(255))
    document_issue_date: Mapped[date | None] = mapped_column(Date)
    document_issue_place: Mapped[str | None] = mapped_column(String(255))

    # Tax calculation flags
    is_tax_exempt: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Exempt from City Tax (minor, driver, guide)",
    )
    tax_exemption_reason: Mapped[str | None] = mapped_column(
        String(100),
        comment="Reason for exemption (age, bus_driver, tour_guide)",
    )

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="guests")

    def __repr__(self) -> str:
        return f"<Guest {self.first_name} {self.last_name} ({self.role.value})>"
