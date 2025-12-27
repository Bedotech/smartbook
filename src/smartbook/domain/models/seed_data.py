"""
Seed data for ISTAT reference tables.

This file contains sample ISTAT country codes and a few key municipalities
from the PDF specification. Full data would be loaded from official ISTAT sources.
"""

# ISTAT Country Codes (from PDF Table 1)
ISTAT_COUNTRIES = [
    {
        "code": "100000100",
        "name_it": "Italia",
        "name_en": "Italy",
        "iso_code": "IT",
    },
    {
        "code": "100000122",
        "name_it": "Germania",
        "name_en": "Germany",
        "iso_code": "DE",
    },
    {
        "code": "100000118",
        "name_it": "Francia",
        "name_en": "France",
        "iso_code": "FR",
    },
    {
        "code": "100000142",
        "name_it": "Svizzera",
        "name_en": "Switzerland",
        "iso_code": "CH",
    },
    {
        "code": "100000139",
        "name_it": "Regno Unito",
        "name_en": "United Kingdom",
        "iso_code": "GB",
    },
]

# Sample municipalities from Bergamo province (Schilpario area)
SAMPLE_MUNICIPALITIES = [
    {
        "code": "H810",
        "name": "Schilpario",
        "province_code": "BG",
        "province_name": "Bergamo",
        "region": "Lombardia",
    },
    {
        "code": "I711",
        "name": "Vilminore di Scalve",
        "province_code": "BG",
        "province_name": "Bergamo",
        "region": "Lombardia",
    },
    {
        "code": "B036",
        "name": "Bergamo",
        "province_code": "BG",
        "province_name": "Bergamo",
        "region": "Lombardia",
    },
    {
        "code": "F205",
        "name": "Milano",
        "province_code": "MI",
        "province_name": "Milano",
        "region": "Lombardia",
    },
    {
        "code": "H501",
        "name": "Roma",
        "province_code": "RM",
        "province_name": "Roma",
        "region": "Lazio",
    },
]
