"""
FastAPI dependencies for authentication, authorization, and tenant context.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.database import get_db


class TenantContext:
    """
    Tenant context for row-level multi-tenancy.

    Ensures that all database queries are automatically filtered
    by tenant_id to prevent data leakage between tenants.
    """

    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id

    def __repr__(self) -> str:
        return f"<TenantContext tenant_id={self.tenant_id}>"


async def get_current_tenant_id(
    x_tenant_id: Annotated[str | None, Header()] = None,
) -> UUID:
    """
    Extract tenant ID from request header.

    In production, this would typically come from:
    1. JWT token claims
    2. Session data
    3. Subdomain mapping
    4. API key lookup

    For now, we use a header for simplicity.
    """
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required",
        )

    try:
        return UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant ID format",
        )


async def get_tenant_context(
    tenant_id: Annotated[UUID, Depends(get_current_tenant_id)],
) -> TenantContext:
    """
    Get tenant context from tenant ID.

    This dependency injects the tenant context into route handlers,
    ensuring all operations are scoped to the correct tenant.
    """
    return TenantContext(tenant_id=tenant_id)


# Type alias for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentTenant = Annotated[TenantContext, Depends(get_tenant_context)]
