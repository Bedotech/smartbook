"""
Country model for ISTAT country codes.
"""

from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column

from smartbook.domain.models.base import Base


class Country(Base):
    """
    Country reference table for ISTAT country codes.

    Stores official ISTAT codes (e.g., 100000100 for Italy)
    required for ROS1000 XML transmission.
    """

    __tablename__ = "countries"

    # ISTAT country code (primary key)
    code: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        comment="ISTAT country code (e.g., 100000100 for Italy)",
    )

    # Country name in Italian
    name_it: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Country name in Italian (e.g., Italia)",
    )

    # Country name in English
    name_en: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Country name in English (e.g., Italy)",
    )

    # ISO 3166-1 alpha-2 code
    iso_code: Mapped[str | None] = mapped_column(
        String(2),
        comment="ISO 3166-1 alpha-2 code (e.g., IT)",
    )

    # Index for autocomplete search
    __table_args__ = (
        Index("ix_country_name_it", "name_it"),
        Index("ix_country_name_en", "name_en"),
    )

    def __repr__(self) -> str:
        return f"<Country {self.name_en} ({self.code})>"
