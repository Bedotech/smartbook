"""
Municipality model for ISTAT Codice Catastale lookup.
"""

from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column

from smartbook.domain.models.base import Base


class Municipality(Base):
    """
    Municipality reference table for Italian municipalities (Comuni).

    Stores ISTAT Codice Catastale codes (e.g., H810 for Schilpario)
    used in ROS1000 XML transmission and autocomplete features.
    """

    __tablename__ = "municipalities"

    # ISTAT Codice Catastale (primary key)
    code: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
        comment="ISTAT Codice Catastale (e.g., H810)",
    )

    # Municipality name
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Municipality name (e.g., Schilpario)",
    )

    # Province code
    province_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        comment="Province code (e.g., BG for Bergamo)",
    )

    # Province name
    province_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Province full name (e.g., Bergamo)",
    )

    # Region name
    region: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Region name (e.g., Lombardia)",
    )

    # Index for autocomplete search
    __table_args__ = (
        Index("ix_municipality_name", "name"),
        Index("ix_municipality_province", "province_code"),
    )

    def __repr__(self) -> str:
        return f"<Municipality {self.name} ({self.code}) - {self.province_code}>"
