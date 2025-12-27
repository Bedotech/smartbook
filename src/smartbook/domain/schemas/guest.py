"""
Pydantic schemas for Guest model with TULPS validation.
"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from smartbook.domain.enums import GuestRole, Sex, DocumentType


class GuestBase(BaseModel):
    """Base guest schema with TULPS minimum fields."""

    role: GuestRole = Field(..., description="Guest role in booking")

    # TULPS minimums (required for all)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    sex: Sex
    date_of_birth: date = Field(..., description="Date of birth")

    # Place of birth
    place_of_birth_municipality_code: str | None = Field(
        None, max_length=10, description="ISTAT Codice Catastale"
    )
    place_of_birth_country_code: str | None = Field(
        None, max_length=20, description="ISTAT country code"
    )

    # Residence
    residence_municipality_code: str | None = Field(
        None, max_length=10, description="ISTAT Codice Catastale"
    )
    residence_country_code: str | None = Field(
        None, max_length=20, description="ISTAT country code"
    )
    residence_address: str | None = Field(None, max_length=255)
    residence_zip_code: str | None = Field(None, max_length=20)

    @field_validator("date_of_birth")
    @classmethod
    def validate_birth_date(cls, v: date) -> date:
        """Validate that birth date is not in the future."""
        if v > date.today():
            raise ValueError("Birth date cannot be in the future")
        return v


class GuestLeaderCreate(GuestBase):
    """Schema for creating a Group/Family Leader with full document details."""

    # Document details (REQUIRED for leaders)
    document_type: DocumentType = Field(..., description="Type of identity document")
    document_number: str = Field(..., min_length=1, max_length=50)
    document_issuing_authority: str = Field(..., min_length=1, max_length=255)
    document_issue_date: date = Field(..., description="Document issue date")
    document_issue_place: str = Field(..., min_length=1, max_length=255)

    @field_validator("document_issue_date")
    @classmethod
    def validate_issue_date(cls, v: date) -> date:
        """Validate that issue date is not in the future."""
        if v > date.today():
            raise ValueError("Document issue date cannot be in the future")
        return v


class GuestMemberCreate(GuestBase):
    """Schema for creating a Group/Family Member with TULPS minimums only."""

    # Document details are OPTIONAL for members
    document_type: DocumentType | None = None
    document_number: str | None = Field(None, max_length=50)


class GuestUpdate(BaseModel):
    """Schema for updating guest information."""

    role: GuestRole | None = None
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    sex: Sex | None = None
    date_of_birth: date | None = None
    place_of_birth_municipality_code: str | None = None
    place_of_birth_country_code: str | None = None
    residence_municipality_code: str | None = None
    residence_country_code: str | None = None
    residence_address: str | None = None
    residence_zip_code: str | None = None
    document_type: DocumentType | None = None
    document_number: str | None = None
    document_issuing_authority: str | None = None
    document_issue_date: date | None = None
    document_issue_place: str | None = None


class GuestResponse(GuestBase):
    """Schema for guest responses."""

    id: UUID
    booking_id: UUID
    is_tax_exempt: bool
    tax_exemption_reason: str | None = None

    # Include document details if present
    document_type: DocumentType | None = None
    document_number: str | None = None
    document_issuing_authority: str | None = None
    document_issue_date: date | None = None
    document_issue_place: str | None = None

    model_config = {"from_attributes": True}
