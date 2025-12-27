"""
Unit tests for Tax Reporting Service.

Tests report generation for monthly/quarterly/detailed reports
with Italian locale formatting and proper aggregation.
"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from smartbook.services.tax_reporting_service import TaxReportGenerator
from smartbook.services.tax_calculation_service import TaxCalculationResult


@pytest.fixture
def report_generator():
    """Create TaxReportGenerator instance."""
    return TaxReportGenerator(
        tenant_name="Hotel Pineta",
        facility_code="CIR-123456",
    )


@pytest.fixture
def sample_results():
    """Create sample tax calculation results."""
    return [
        TaxCalculationResult(
            booking_id=uuid4(),
            total_guests=10,
            taxable_guests=8,
            exempt_guests=2,
            base_rate_per_night=Decimal("2.50"),
            total_nights=3,
            taxable_nights=3,
            total_tax_amount=Decimal("60.00"),
            exemption_breakdown={
                "exempt_minors": 2,
                "exempt_drivers_allowed": 0,
                "exempt_guides": 0,
            },
        ),
        TaxCalculationResult(
            booking_id=uuid4(),
            total_guests=25,
            taxable_guests=23,
            exempt_guests=2,
            base_rate_per_night=Decimal("2.50"),
            total_nights=2,
            taxable_nights=2,
            total_tax_amount=Decimal("115.00"),
            exemption_breakdown={
                "exempt_minors": 1,
                "exempt_drivers_allowed": 1,
                "exempt_guides": 0,
            },
        ),
        TaxCalculationResult(
            booking_id=uuid4(),
            total_guests=30,
            taxable_guests=27,
            exempt_guests=3,
            base_rate_per_night=Decimal("2.50"),
            total_nights=4,
            taxable_nights=4,
            total_tax_amount=Decimal("270.00"),
            exemption_breakdown={
                "exempt_minors": 0,
                "exempt_drivers_allowed": 1,
                "exempt_guides": 2,
            },
        ),
    ]


class TestMonthlyReport:
    """Test monthly report generation."""

    def test_generate_monthly_report_basic(self, report_generator, sample_results):
        """Test basic monthly report generation."""
        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=sample_results,
        )

        assert report["report_type"] == "monthly"
        assert report["period"]["year"] == 2025
        assert report["period"]["month"] == 1
        assert report["period"]["month_name"] == "Gennaio"
        assert report["property"]["name"] == "Hotel Pineta"
        assert report["property"]["facility_code"] == "CIR-123456"

    def test_monthly_report_totals(self, report_generator, sample_results):
        """Test monthly report calculates correct totals."""
        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=sample_results,
        )

        summary = report["summary"]

        # 3 bookings total
        assert summary["total_bookings"] == 3

        # Total guests: 10 + 25 + 30 = 65
        assert summary["total_guests"] == 65

        # Taxable guests: 8 + 23 + 27 = 58
        assert summary["total_taxable_guests"] == 58

        # Exempt guests: 2 + 2 + 3 = 7
        assert summary["total_exempt_guests"] == 7

        # Total tax: 60 + 115 + 270 = 445
        assert summary["total_tax_collected"] == 445.00

    def test_monthly_report_exemption_breakdown(self, report_generator, sample_results):
        """Test monthly report aggregates exemptions correctly."""
        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=sample_results,
        )

        exemptions = report["exemptions"]

        # Minors: 2 + 1 + 0 = 3
        assert exemptions["minors"] == 3

        # Drivers: 0 + 1 + 1 = 2
        assert exemptions["bus_drivers"] == 2

        # Guides: 0 + 0 + 2 = 2
        assert exemptions["tour_guides"] == 2

        # Total: 3 + 2 + 2 = 7
        assert exemptions["total"] == 7

    def test_monthly_report_averages(self, report_generator, sample_results):
        """Test monthly report calculates averages correctly."""
        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=sample_results,
        )

        averages = report["average_per_booking"]

        # Average guests: 65 / 3 = 21.67
        assert abs(averages["guests"] - 21.67) < 0.01

        # Average tax: 445 / 3 = 148.33
        assert abs(averages["tax"] - 148.33) < 0.01

    def test_monthly_report_empty_results(self, report_generator):
        """Test monthly report with no results."""
        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=[],
        )

        summary = report["summary"]
        assert summary["total_bookings"] == 0
        assert summary["total_guests"] == 0
        assert summary["total_tax_collected"] == 0.0

    def test_monthly_report_all_months(self, report_generator, sample_results):
        """Test monthly report generates correct Italian month names."""
        months = {
            1: "Gennaio",
            2: "Febbraio",
            3: "Marzo",
            4: "Aprile",
            5: "Maggio",
            6: "Giugno",
            7: "Luglio",
            8: "Agosto",
            9: "Settembre",
            10: "Ottobre",
            11: "Novembre",
            12: "Dicembre",
        }

        for month_num, month_name in months.items():
            report = report_generator.generate_monthly_report(
                year=2025,
                month=month_num,
                results=sample_results,
            )
            assert report["period"]["month_name"] == month_name

    def test_monthly_report_nights_calculation(self, report_generator, sample_results):
        """Test monthly report calculates nights correctly."""
        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=sample_results,
        )

        summary = report["summary"]

        # Total nights: (3*10) + (2*25) + (4*30) = 30 + 50 + 120 = 200
        assert summary["total_nights"] == 200

        # Taxable nights: (3*8) + (2*23) + (4*27) = 24 + 46 + 108 = 178
        assert summary["total_taxable_nights"] == 178


class TestQuarterlyReport:
    """Test quarterly report generation."""

    def test_generate_quarterly_report_q1(self, report_generator, sample_results):
        """Test Q1 quarterly report."""
        report = report_generator.generate_quarterly_report(
            year=2025,
            quarter=1,
            results=sample_results,
        )

        assert report["report_type"] == "quarterly"
        assert report["period"]["year"] == 2025
        assert report["period"]["quarter"] == 1
        assert report["period"]["months"] == ["Gennaio", "Febbraio", "Marzo"]

    def test_generate_quarterly_report_q2(self, report_generator, sample_results):
        """Test Q2 quarterly report."""
        report = report_generator.generate_quarterly_report(
            year=2025,
            quarter=2,
            results=sample_results,
        )

        assert report["period"]["quarter"] == 2
        assert report["period"]["months"] == ["Aprile", "Maggio", "Giugno"]

    def test_generate_quarterly_report_q3(self, report_generator, sample_results):
        """Test Q3 quarterly report."""
        report = report_generator.generate_quarterly_report(
            year=2025,
            quarter=3,
            results=sample_results,
        )

        assert report["period"]["quarter"] == 3
        assert report["period"]["months"] == ["Luglio", "Agosto", "Settembre"]

    def test_generate_quarterly_report_q4(self, report_generator, sample_results):
        """Test Q4 quarterly report."""
        report = report_generator.generate_quarterly_report(
            year=2025,
            quarter=4,
            results=sample_results,
        )

        assert report["period"]["quarter"] == 4
        assert report["period"]["months"] == ["Ottobre", "Novembre", "Dicembre"]

    def test_quarterly_report_summary(self, report_generator, sample_results):
        """Test quarterly report summary totals."""
        report = report_generator.generate_quarterly_report(
            year=2025,
            quarter=1,
            results=sample_results,
        )

        summary = report["summary"]
        assert summary["total_bookings"] == 3
        assert summary["total_tax_collected"] == 445.00


class TestBookingDetailReport:
    """Test booking detail report generation."""

    def test_generate_booking_detail_report(self, report_generator, sample_results):
        """Test detailed booking report."""
        report = report_generator.generate_booking_detail_report(
            results=sample_results,
        )

        assert report["report_type"] == "detailed"
        assert report["property"]["name"] == "Hotel Pineta"
        assert len(report["bookings"]) == 3

    def test_booking_detail_contains_all_fields(self, report_generator, sample_results):
        """Test that booking details contain all required fields."""
        report = report_generator.generate_booking_detail_report(
            results=sample_results,
        )

        booking = report["bookings"][0]

        assert "booking_id" in booking
        assert "guests" in booking
        assert "taxable_guests" in booking
        assert "exempt_guests" in booking
        assert "nights" in booking
        assert "taxable_nights" in booking
        assert "rate_per_night" in booking
        assert "tax_amount" in booking
        assert "exemptions" in booking

    def test_booking_detail_values(self, report_generator, sample_results):
        """Test booking detail values are correct."""
        report = report_generator.generate_booking_detail_report(
            results=sample_results,
        )

        # First booking
        booking = report["bookings"][0]
        assert booking["guests"] == 10
        assert booking["taxable_guests"] == 8
        assert booking["exempt_guests"] == 2
        assert booking["nights"] == 3
        assert booking["rate_per_night"] == 2.50
        assert booking["tax_amount"] == 60.00


class TestCurrencyFormatting:
    """Test Italian currency formatting."""

    def test_format_currency_decimal(self, report_generator):
        """Test formatting Decimal to Italian currency."""
        formatted = report_generator.format_currency(Decimal("1234.56"))
        assert formatted == "€ 1.234,56"

    def test_format_currency_float(self, report_generator):
        """Test formatting float to Italian currency."""
        formatted = report_generator.format_currency(1234.56)
        assert formatted == "€ 1.234,56"

    def test_format_currency_small_amount(self, report_generator):
        """Test formatting small amount."""
        formatted = report_generator.format_currency(Decimal("2.50"))
        assert formatted == "€ 2,50"

    def test_format_currency_large_amount(self, report_generator):
        """Test formatting large amount."""
        formatted = report_generator.format_currency(Decimal("123456.78"))
        assert formatted == "€ 123.456,78"

    def test_format_currency_zero(self, report_generator):
        """Test formatting zero."""
        formatted = report_generator.format_currency(Decimal("0.00"))
        assert formatted == "€ 0,00"

    def test_format_currency_whole_number(self, report_generator):
        """Test formatting whole number."""
        formatted = report_generator.format_currency(Decimal("1000.00"))
        assert formatted == "€ 1.000,00"


class TestTextSummary:
    """Test plain text summary generation."""

    def test_generate_text_summary_monthly(self, report_generator, sample_results):
        """Test text summary for monthly report."""
        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=sample_results,
        )

        summary = report_generator.generate_text_summary(report)

        assert "IMPOSTA DI SOGGIORNO" in summary
        assert "Hotel Pineta" in summary
        assert "CIR-123456" in summary
        assert "Gennaio 2025" in summary
        assert "€ 445,00" in summary

    def test_generate_text_summary_quarterly(self, report_generator, sample_results):
        """Test text summary for quarterly report."""
        report = report_generator.generate_quarterly_report(
            year=2025,
            quarter=1,
            results=sample_results,
        )

        summary = report_generator.generate_text_summary(report)

        assert "Q1 2025" in summary
        assert "Hotel Pineta" in summary

    def test_text_summary_contains_totals(self, report_generator, sample_results):
        """Test that text summary contains all totals."""
        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=sample_results,
        )

        summary = report_generator.generate_text_summary(report)

        assert "Prenotazioni totali: 3" in summary
        assert "Ospiti totali: 65" in summary
        assert "Ospiti soggetti a imposta: 58" in summary
        assert "Ospiti esenti: 7" in summary

    def test_text_summary_contains_exemptions(self, report_generator, sample_results):
        """Test that text summary contains exemption breakdown."""
        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=sample_results,
        )

        summary = report_generator.generate_text_summary(report)

        assert "DETTAGLIO ESENZIONI" in summary
        assert "Minori: 3" in summary
        assert "Autisti pullman: 2" in summary
        assert "Guide turistiche: 2" in summary

    def test_text_summary_formatting(self, report_generator, sample_results):
        """Test that text summary has proper formatting."""
        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=sample_results,
        )

        summary = report_generator.generate_text_summary(report)

        # Check for formatting elements
        assert "=" * 60 in summary
        assert "-" * 60 in summary
        assert "RIEPILOGO" in summary

    def test_text_summary_includes_generation_date(self, report_generator, sample_results):
        """Test that text summary includes generation date."""
        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=sample_results,
        )

        summary = report_generator.generate_text_summary(report)

        assert "Generato il:" in summary


class TestReportEdgeCases:
    """Test edge cases in report generation."""

    def test_single_booking_report(self, report_generator):
        """Test report with single booking."""
        results = [
            TaxCalculationResult(
                booking_id=uuid4(),
                total_guests=5,
                taxable_guests=5,
                exempt_guests=0,
                base_rate_per_night=Decimal("2.00"),
                total_nights=2,
                taxable_nights=2,
                total_tax_amount=Decimal("20.00"),
                exemption_breakdown={
                    "exempt_minors": 0,
                    "exempt_drivers_allowed": 0,
                    "exempt_guides": 0,
                },
            )
        ]

        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=results,
        )

        assert report["summary"]["total_bookings"] == 1
        assert report["summary"]["total_tax_collected"] == 20.00

    def test_large_group_booking(self, report_generator):
        """Test report with large group booking."""
        results = [
            TaxCalculationResult(
                booking_id=uuid4(),
                total_guests=100,
                taxable_guests=92,
                exempt_guests=8,
                base_rate_per_night=Decimal("2.50"),
                total_nights=5,
                taxable_nights=5,
                total_tax_amount=Decimal("1150.00"),
                exemption_breakdown={
                    "exempt_minors": 5,
                    "exempt_drivers_allowed": 3,
                    "exempt_guides": 0,
                },
            )
        ]

        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=results,
        )

        assert report["summary"]["total_guests"] == 100
        assert report["summary"]["total_tax_collected"] == 1150.00
        assert report["exemptions"]["minors"] == 5
        assert report["exemptions"]["bus_drivers"] == 3

    def test_all_exempt_booking(self, report_generator):
        """Test report with all guests exempt."""
        results = [
            TaxCalculationResult(
                booking_id=uuid4(),
                total_guests=10,
                taxable_guests=0,
                exempt_guests=10,
                base_rate_per_night=Decimal("2.50"),
                total_nights=3,
                taxable_nights=3,
                total_tax_amount=Decimal("0.00"),
                exemption_breakdown={
                    "exempt_minors": 10,
                    "exempt_drivers_allowed": 0,
                    "exempt_guides": 0,
                },
            )
        ]

        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=results,
        )

        assert report["summary"]["total_tax_collected"] == 0.00
        assert report["summary"]["total_exempt_guests"] == 10
        assert report["summary"]["total_taxable_guests"] == 0


class TestReportMetadata:
    """Test report metadata fields."""

    def test_report_includes_generation_date(self, report_generator, sample_results):
        """Test that report includes generation date."""
        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=sample_results,
        )

        assert "generated_at" in report
        assert isinstance(report["generated_at"], str)
        # Should be in ISO format
        date.fromisoformat(report["generated_at"])

    def test_report_includes_property_info(self, report_generator, sample_results):
        """Test that report includes property information."""
        report = report_generator.generate_monthly_report(
            year=2025,
            month=1,
            results=sample_results,
        )

        assert report["property"]["name"] == "Hotel Pineta"
        assert report["property"]["facility_code"] == "CIR-123456"

    def test_report_type_field(self, report_generator, sample_results):
        """Test that report_type field is correctly set."""
        monthly = report_generator.generate_monthly_report(2025, 1, sample_results)
        assert monthly["report_type"] == "monthly"

        quarterly = report_generator.generate_quarterly_report(2025, 1, sample_results)
        assert quarterly["report_type"] == "quarterly"

        detailed = report_generator.generate_booking_detail_report(sample_results)
        assert detailed["report_type"] == "detailed"
