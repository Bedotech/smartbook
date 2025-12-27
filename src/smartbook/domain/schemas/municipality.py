"""Pydantic schemas for municipality and country search."""

from pydantic import BaseModel


class MunicipalitySearchResponse(BaseModel):
    """Municipality search result schema."""

    istat_code: str
    name: str
    province_code: str
    province_name: str


class CountrySearchResponse(BaseModel):
    """Country search result schema."""

    istat_code: str
    name: str
    iso_code: str
