"""
Tenant repository for managing properties.
"""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.models.tenant import Tenant
from smartbook.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository for Tenant operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Tenant, session)

    async def create_tenant(self, tenant_data: dict) -> Tenant:
        """Create a new tenant (property)."""
        tenant = Tenant(**tenant_data)
        return await self.create(tenant)

    async def get_by_facility_code(self, facility_code: str) -> Tenant | None:
        """Get tenant by facility code (CIR)."""
        result = await self.session.execute(
            select(Tenant).where(Tenant.facility_code == facility_code)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Tenant | None:
        """Get tenant by email."""
        result = await self.session.execute(
            select(Tenant).where(Tenant.email == email)
        )
        return result.scalar_one_or_none()

    async def get_active_tenants(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Tenant]:
        """Get all active tenants."""
        result = await self.session.execute(
            select(Tenant)
            .where(Tenant.is_active == True)  # noqa: E712
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
