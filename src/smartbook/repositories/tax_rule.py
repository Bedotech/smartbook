"""
Tax Rule repository for managing City Tax (Imposta di Soggiorno) configurations.
"""

from datetime import date
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.models.tax_rule import TaxRule
from smartbook.repositories.base import BaseRepository


class TaxRuleRepository(BaseRepository[TaxRule]):
    """Repository for Tax Rule operations with tenant isolation."""

    def __init__(self, session: AsyncSession, property_id: UUID):
        super().__init__(TaxRule, session)
        self.property_id = property_id

    async def create_tax_rule(self, rule_data: dict) -> TaxRule:
        """Create a new tax rule with automatic property_id injection."""
        rule = TaxRule(**rule_data, property_id=self.property_id)
        return await self.create(rule)

    async def get_active_rule(self, check_date: date | None = None) -> TaxRule | None:
        """
        Get the active tax rule for a specific date.

        Args:
            check_date: Date to check (defaults to today)

        Returns:
            Active tax rule or None
        """
        if check_date is None:
            check_date = date.today()

        result = await self.session.execute(
            select(TaxRule)
            .where(
                TaxRule.property_id == self.property_id,
                TaxRule.valid_from <= check_date,
                (TaxRule.valid_until.is_(None)) | (TaxRule.valid_until >= check_date),
            )
            .order_by(TaxRule.valid_from.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_historical_rules(
        self,
        start_date: date,
        end_date: date,
    ) -> Sequence[TaxRule]:
        """Get all tax rules that were active in a date range."""
        result = await self.session.execute(
            select(TaxRule)
            .where(
                TaxRule.property_id == self.property_id,
                TaxRule.valid_from <= end_date,
                (TaxRule.valid_until.is_(None)) | (TaxRule.valid_until >= start_date),
            )
            .order_by(TaxRule.valid_from)
        )
        return result.scalars().all()

    async def get_all_for_tenant(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[TaxRule]:
        """Get all tax rules for the current tenant."""
        result = await self.session.execute(
            select(TaxRule)
            .where(TaxRule.property_id == self.property_id)
            .order_by(TaxRule.valid_from.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
