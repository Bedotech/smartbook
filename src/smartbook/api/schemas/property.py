"""
Property schemas for API request/response validation.
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class PropertyBase(BaseModel):
    """Base schema for property data."""

    name: str = Field(..., min_length=1, max_length=255, description="Property name")
    facility_code: str = Field(..., min_length=1, max_length=50, description="Facility code (CIR)")
    email: EmailStr = Field(..., description="Property contact email")
    phone: Optional[str] = Field(None, max_length=50, description="Property phone number")
    ros1000_username: Optional[str] = Field(None, max_length=255, description="ROS1000 username")
    ros1000_password: Optional[str] = Field(None, max_length=255, description="ROS1000 password")
    ros1000_ws_key: Optional[str] = Field(None, max_length=500, description="ROS1000 web service key")


class PropertyCreate(PropertyBase):
    """Schema for creating a new property."""
    pass


class PropertyUpdate(BaseModel):
    """Schema for updating an existing property."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    facility_code: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    ros1000_username: Optional[str] = Field(None, max_length=255)
    ros1000_password: Optional[str] = Field(None, max_length=255)
    ros1000_ws_key: Optional[str] = Field(None, max_length=500)


class PropertyResponse(PropertyBase):
    """Schema for property response."""

    id: UUID
    is_active: bool

    class Config:
        from_attributes = True


class PropertyListResponse(BaseModel):
    """Schema for property list response."""

    properties: list[PropertyResponse]
    total: int
    page: int
    page_size: int


class PropertyUserAssignment(BaseModel):
    """Schema for user-property assignment."""

    user_id: UUID
    property_id: UUID


class PropertyUserAssignmentResponse(PropertyUserAssignment):
    """Schema for user-property assignment response."""

    id: UUID
    assigned_at: str

    class Config:
        from_attributes = True
