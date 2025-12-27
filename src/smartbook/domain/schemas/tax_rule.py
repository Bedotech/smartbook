"""Pydantic schemas for tax rules."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaxRuleBase(BaseModel):
    """Base tax rule schema."""

    base_rate_per_night: Decimal = Field(..., description="Base tax rate per person per night (EUR)")
    max_taxable_nights: int | None = Field(None, description="Max nights to charge tax (None = unlimited)")
    valid_from: date = Field(..., description="Start date for this tax rule")
    valid_until: date | None = Field(None, description="End date for this tax rule (None = indefinite)")
    exemption_rules: dict = Field(
        default_factory=dict,
        description="Exemption configuration (age_under, bus_driver_ratio, etc.)"
    )


class TaxRuleCreate(TaxRuleBase):
    """Schema for creating a tax rule."""
    pass


class TaxRuleUpdate(BaseModel):
    """Schema for updating a tax rule."""

    base_rate_per_night: Decimal | None = None
    max_taxable_nights: int | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    exemption_rules: dict | None = None


class TaxRuleResponse(TaxRuleBase):
    """Tax rule response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
