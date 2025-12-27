"""
Tax Rule model for configurable City Tax (Imposta di Soggiorno) rules.
"""

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, Date, ForeignKey, Numeric, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from smartbook.domain.models.base import Base

if TYPE_CHECKING:
    from smartbook.domain.models.tenant import Tenant


class TaxRule(Base):
    """
    Tax Rule model for configurable City Tax calculation.

    Stores per-tenant tax configuration including rates, exemptions,
    and caps. Supports historical rules for accurate past calculations.
    """

    __tablename__ = "tax_rules"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Multi-tenant isolation
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Rule validity period
    valid_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Start date for this tax rule",
    )
    valid_until: Mapped[date | None] = mapped_column(
        Date,
        comment="End date (NULL = currently active)",
    )

    # Base tax configuration
    base_rate_per_night: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Tax rate per night in EUR (e.g., 1.00)",
    )

    # Duration cap
    max_taxable_nights: Mapped[int | None] = mapped_column(
        Integer,
        comment="Cap on taxable nights (e.g., 10 = only first 10 nights taxed)",
    )

    # Age-based exemption
    age_exemption_threshold: Mapped[int | None] = mapped_column(
        Integer,
        comment="Age below which guests are exempt (e.g., 14 years)",
    )

    # Role-based exemptions
    exemption_rules: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="JSON config for role exemptions (e.g., {'bus_driver_ratio': 25})",
    )

    # Facility classification rate
    structure_classification: Mapped[str | None] = mapped_column(
        String(50),
        comment="Hotel classification affecting rate (e.g., '3-star', 'hostel')",
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="tax_rules")

    def __repr__(self) -> str:
        return f"<TaxRule {self.base_rate_per_night}€ (valid from {self.valid_from})>"
