"""
Municipality autocomplete service.

Provides fast ISTAT municipality lookup with autocomplete functionality
for guest data entry forms.
"""

from typing import Sequence

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from smartbook.domain.models.municipality import Municipality
from smartbook.domain.models.country import Country


class MunicipalityService:
    """
    Service for municipality and country autocomplete.

    Implements fast prefix search for Italian municipalities using
    ISTAT Codice Catastale codes (e.g., H810 = Schilpario).
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_municipalities(
        self,
        query: str,
        limit: int = 10,
    ) -> Sequence[Municipality]:
        """
        Search municipalities by name prefix.

        Args:
            query: Search query (e.g., "Schil" → "Schilpario (BG)")
            limit: Maximum number of results (default: 10)

        Returns:
            List of matching municipalities

        Examples:
            >>> await search_municipalities("Schil")
            [Municipality(name="Schilpario", province_code="BG", code="H810")]
        """
        # Normalize query (trim, lowercase for case-insensitive search)
        normalized_query = query.strip().lower()

        if not normalized_query:
            return []

        # Search by name prefix or province code
        result = await self.session.execute(
            select(Municipality)
            .where(
                or_(
                    func.lower(Municipality.name).startswith(normalized_query),
                    func.lower(Municipality.province_code) == normalized_query,
                )
            )
            .order_by(Municipality.name)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_code(self, code: str) -> Municipality | None:
        """
        Get municipality by ISTAT Codice Catastale.

        Args:
            code: ISTAT code (e.g., "H810")

        Returns:
            Municipality or None
        """
        result = await self.session.execute(
            select(Municipality).where(Municipality.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def get_municipalities_by_province(
        self,
        province_code: str,
        limit: int = 100,
    ) -> Sequence[Municipality]:
        """
        Get all municipalities in a province.

        Args:
            province_code: Province code (e.g., "BG" for Bergamo)
            limit: Maximum number of results

        Returns:
            List of municipalities in the province
        """
        result = await self.session.execute(
            select(Municipality)
            .where(Municipality.province_code == province_code.upper())
            .order_by(Municipality.name)
            .limit(limit)
        )
        return result.scalars().all()

    async def search_countries(
        self,
        query: str,
        limit: int = 10,
    ) -> Sequence[Country]:
        """
        Search countries by name prefix.

        Args:
            query: Search query (e.g., "Ital" → "Italia/Italy")
            limit: Maximum number of results

        Returns:
            List of matching countries
        """
        normalized_query = query.strip().lower()

        if not normalized_query:
            return []

        result = await self.session.execute(
            select(Country)
            .where(
                or_(
                    func.lower(Country.name_it).startswith(normalized_query),
                    func.lower(Country.name_en).startswith(normalized_query),
                    func.lower(Country.iso_code) == normalized_query,
                )
            )
            .order_by(Country.name_en)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_country_by_code(self, code: str) -> Country | None:
        """
        Get country by ISTAT code.

        Args:
            code: ISTAT country code (e.g., "100000100" for Italy)

        Returns:
            Country or None
        """
        result = await self.session.execute(
            select(Country).where(Country.code == code)
        )
        return result.scalar_one_or_none()

    async def get_italy(self) -> Country | None:
        """
        Get Italy country record (most common use case).

        Returns:
            Italy country record or None
        """
        return await self.get_country_by_code("100000100")

    async def format_municipality_display(self, municipality: Municipality) -> str:
        """
        Format municipality for display in autocomplete dropdown.

        Args:
            municipality: Municipality object

        Returns:
            Formatted string (e.g., "Schilpario (BG)")
        """
        return f"{municipality.name} ({municipality.province_code})"

    async def seed_sample_data(self) -> None:
        """
        Seed sample municipality and country data from seed_data.py.

        This is used for development and testing. In production, data
        would be loaded from official ISTAT sources.
        """
        from smartbook.domain.models.seed_data import (
            ISTAT_COUNTRIES,
            SAMPLE_MUNICIPALITIES,
        )

        # Seed countries
        for country_data in ISTAT_COUNTRIES:
            existing = await self.get_country_by_code(country_data["code"])
            if not existing:
                country = Country(**country_data)
                self.session.add(country)

        # Seed municipalities
        for muni_data in SAMPLE_MUNICIPALITIES:
            existing = await self.get_by_code(muni_data["code"])
            if not existing:
                municipality = Municipality(**muni_data)
                self.session.add(municipality)

        await self.session.flush()
