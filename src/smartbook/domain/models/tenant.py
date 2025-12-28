"""
Property model for multi-tenancy support.

Note: This table was renamed from 'tenants' to 'properties' for semantic clarity.
The class name is Property but the module is still tenant.py for backward compatibility.
"""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from smartbook.domain.models.base import Base

if TYPE_CHECKING:
    from smartbook.domain.models.booking import Booking
    from smartbook.domain.models.tax_rule import TaxRule
    from smartbook.domain.models.user_property_assignment import UserPropertyAssignment


class Tenant(Base):
    """
    Property model representing a hotel or B&B property.

    Note: Class is named 'Tenant' for backward compatibility with existing code,
    but semantically represents a Property. The table name is 'properties'.

    Each property has isolated data and its own ROS1000 credentials
    and tax configuration.
    """

    __tablename__ = "properties"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Property information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    facility_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Codice Struttura (CIR) assigned by Lombardy Region",
    )

    # ROS1000 credentials
    ros1000_username: Mapped[str | None] = mapped_column(String(255))
    ros1000_password: Mapped[str | None] = mapped_column(String(255))
    ros1000_ws_key: Mapped[str | None] = mapped_column(
        String(500),
        comment="Web Service Key for Questura bridge (from Alloggiati Web)",
    )

    # Contact information
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    tax_rules: Mapped[list["TaxRule"]] = relationship(
        "TaxRule",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    user_assignments: Mapped[list["UserPropertyAssignment"]] = relationship(
        "UserPropertyAssignment",
        back_populates="property",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Property {self.name} ({self.facility_code})>"
