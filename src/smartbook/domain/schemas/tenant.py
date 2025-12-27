"""
Pydantic schemas for Tenant model.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class TenantBase(BaseModel):
    """Base tenant schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Property name")
    facility_code: str = Field(
        ..., min_length=1, max_length=50, description="Codice Struttura (CIR)"
    )
    email: EmailStr = Field(..., description="Contact email")
    phone: str | None = Field(None, max_length=50, description="Contact phone")


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""

    ros1000_username: str | None = Field(None, max_length=255)
    ros1000_password: str | None = Field(None, max_length=255)
    ros1000_ws_key: str | None = Field(None, max_length=500)


class TenantUpdate(BaseModel):
    """Schema for updating an existing tenant."""

    name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    ros1000_username: str | None = None
    ros1000_password: str | None = None
    ros1000_ws_key: str | None = None
    is_active: bool | None = None


class TenantResponse(TenantBase):
    """Schema for tenant responses."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Don't expose credentials
    has_ros1000_credentials: bool = Field(
        ..., description="Whether ROS1000 credentials are configured"
    )

    model_config = {"from_attributes": True}
