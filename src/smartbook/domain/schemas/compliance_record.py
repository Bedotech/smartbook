"""Pydantic schemas for compliance records."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from smartbook.domain.enums import ComplianceStatus


class ComplianceRecordResponse(BaseModel):
    """Compliance record response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    booking_id: UUID
    submission_type: str
    status: ComplianceStatus
    receipt_number: str | None
    xml_payload: str
    response_data: dict | None
    error_message: str | None
    retry_count: int
    submitted_at: datetime
    last_retry_at: datetime | None
    created_at: datetime
    updated_at: datetime
