"""
Pydantic schemas for Booking model.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from smartbook.domain.enums import BookingType, BookingStatus


class BookingBase(BaseModel):
    """Base booking schema."""

    booking_type: BookingType
    check_in_date: date
    check_out_date: date
    expected_guests: int = Field(..., gt=0, description="Number of expected guests")
    notes: str | None = Field(None, max_length=1000)

    @field_validator("check_out_date")
    @classmethod
    def validate_dates(cls, v: date, info) -> date:
        """Validate that check-out is after check-in."""
        check_in = info.data.get("check_in_date")
        if check_in and v <= check_in:
            raise ValueError("Check-out date must be after check-in date")
        return v


class BookingCreate(BookingBase):
    """Schema for creating a new booking."""

    pass


class BookingUpdate(BaseModel):
    """Schema for updating a booking."""

    booking_type: BookingType | None = None
    check_in_date: date | None = None
    check_out_date: date | None = None
    expected_guests: int | None = Field(None, gt=0)
    notes: str | None = None
    status: BookingStatus | None = None


class BookingResponse(BookingBase):
    """Schema for booking responses."""

    id: UUID
    tenant_id: UUID
    status: BookingStatus
    magic_link_token: str
    token_expires_at: datetime
    created_at: datetime
    updated_at: datetime

    # Computed fields
    current_guest_count: int = Field(
        0, description="Number of guests currently entered"
    )

    model_config = {"from_attributes": True}


class BookingProgressResponse(BaseModel):
    """Schema for booking progress tracking."""

    booking_id: UUID
    expected_guests: int
    current_guest_count: int
    has_leader: bool
    completion_percentage: float = Field(..., ge=0, le=100)
    status: BookingStatus

    model_config = {"from_attributes": True}
