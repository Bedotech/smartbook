"""
Tax Reporting Service for generating reports to municipality.

Generates PDF summaries of City Tax collected for submission
to the Municipality of Schilpario / Comunità Montana di Scalve.
"""

from datetime import date
from decimal import Decimal
from typing import Sequence

from smartbook.services.tax_calculation_service import TaxCalculationResult


class TaxReportGenerator:
    """
    Generator for City Tax reports.

    Creates formatted reports for monthly/quarterly submission
    to the municipality with full audit trail.
    """

    def __init__(self, tenant_name: str, facility_code: str):
        self.tenant_name = tenant_name
        self.facility_code = facility_code

    def generate_monthly_report(
        self,
        year: int,
        month: int,
        results: Sequence[TaxCalculationResult],
    ) -> dict:
        """
        Generate monthly tax report.

        Args:
            year: Year
            month: Month (1-12)
            results: Tax calculation results for the month

        Returns:
            Report dictionary ready for PDF generation
        """
        # Calculate totals
        total_bookings = len(results)
        total_guests = sum(r.total_guests for r in results)
        total_taxable_guests = sum(r.taxable_guests for r in results)
        total_exempt_guests = sum(r.exempt_guests for r in results)
        total_tax = sum(r.total_tax_amount for r in results)

        # Aggregate exemptions
        total_exempt_minors = sum(
            r.exemption_breakdown.get("exempt_minors", 0) for r in results
        )
        total_exempt_drivers = sum(
            r.exemption_breakdown.get("exempt_drivers_allowed", 0) for r in results
        )
        total_exempt_guides = sum(
            r.exemption_breakdown.get("exempt_guides", 0) for r in results
        )

        # Calculate nights
        total_nights = sum(r.total_nights * r.total_guests for r in results)
        total_taxable_nights = sum(r.taxable_nights * r.taxable_guests for r in results)

        return {
            "report_type": "monthly",
            "period": {
                "year": year,
                "month": month,
                "month_name": self._get_month_name(month),
            },
            "property": {
                "name": self.tenant_name,
                "facility_code": self.facility_code,
            },
            "summary": {
                "total_bookings": total_bookings,
                "total_guests": total_guests,
                "total_taxable_guests": total_taxable_guests,
                "total_exempt_guests": total_exempt_guests,
                "total_nights": total_nights,
                "total_taxable_nights": total_taxable_nights,
                "total_tax_collected": float(total_tax),
            },
            "exemptions": {
                "minors": total_exempt_minors,
                "bus_drivers": total_exempt_drivers,
                "tour_guides": total_exempt_guides,
                "total": total_exempt_guests,
            },
            "average_per_booking": {
                "guests": float(total_guests / total_bookings) if total_bookings > 0 else 0,
                "tax": float(total_tax / total_bookings) if total_bookings > 0 else 0,
            },
            "generated_at": date.today().isoformat(),
        }

    def generate_quarterly_report(
        self,
        year: int,
        quarter: int,
        results: Sequence[TaxCalculationResult],
    ) -> dict:
        """
        Generate quarterly tax report.

        Args:
            year: Year
            quarter: Quarter (1-4)
            results: Tax calculation results for the quarter

        Returns:
            Report dictionary ready for PDF generation
        """
        # Similar to monthly but aggregated by quarter
        total_tax = sum(r.total_tax_amount for r in results)

        return {
            "report_type": "quarterly",
            "period": {
                "year": year,
                "quarter": quarter,
                "months": self._get_quarter_months(quarter),
            },
            "property": {
                "name": self.tenant_name,
                "facility_code": self.facility_code,
            },
            "summary": {
                "total_bookings": len(results),
                "total_tax_collected": float(total_tax),
            },
            "generated_at": date.today().isoformat(),
        }

    def generate_booking_detail_report(
        self,
        results: Sequence[TaxCalculationResult],
    ) -> dict:
        """
        Generate detailed report with per-booking breakdown.

        Args:
            results: Tax calculation results

        Returns:
            Detailed report dictionary
        """
        bookings_detail = []
        for result in results:
            bookings_detail.append({
                "booking_id": str(result.booking_id),
                "guests": result.total_guests,
                "taxable_guests": result.taxable_guests,
                "exempt_guests": result.exempt_guests,
                "nights": result.total_nights,
                "taxable_nights": result.taxable_nights,
                "rate_per_night": float(result.base_rate_per_night),
                "tax_amount": float(result.total_tax_amount),
                "exemptions": result.exemption_breakdown,
            })

        return {
            "report_type": "detailed",
            "property": {
                "name": self.tenant_name,
                "facility_code": self.facility_code,
            },
            "bookings": bookings_detail,
            "generated_at": date.today().isoformat(),
        }

    def format_currency(self, amount: Decimal | float) -> str:
        """Format currency for Italian locale (EUR)."""
        if isinstance(amount, Decimal):
            amount = float(amount)
        return f"€ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _get_month_name(self, month: int) -> str:
        """Get Italian month name."""
        months = {
            1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
            5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
            9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre",
        }
        return months.get(month, "")

    def _get_quarter_months(self, quarter: int) -> list[str]:
        """Get month names for a quarter."""
        quarters = {
            1: ["Gennaio", "Febbraio", "Marzo"],
            2: ["Aprile", "Maggio", "Giugno"],
            3: ["Luglio", "Agosto", "Settembre"],
            4: ["Ottobre", "Novembre", "Dicembre"],
        }
        return quarters.get(quarter, [])

    def generate_text_summary(self, report: dict) -> str:
        """
        Generate a plain text summary of the report.

        Args:
            report: Report dictionary

        Returns:
            Formatted text summary
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"IMPOSTA DI SOGGIORNO - REPORT {report['report_type'].upper()}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Struttura: {report['property']['name']}")
        lines.append(f"Codice: {report['property']['facility_code']}")
        lines.append("")

        if report["report_type"] == "monthly":
            period = report["period"]
            lines.append(f"Periodo: {period['month_name']} {period['year']}")
        elif report["report_type"] == "quarterly":
            period = report["period"]
            lines.append(f"Periodo: Q{period['quarter']} {period['year']}")

        lines.append("")
        lines.append("RIEPILOGO")
        lines.append("-" * 60)

        summary = report["summary"]
        lines.append(f"Prenotazioni totali: {summary['total_bookings']}")
        lines.append(f"Ospiti totali: {summary.get('total_guests', 0)}")
        lines.append(f"Ospiti soggetti a imposta: {summary.get('total_taxable_guests', 0)}")
        lines.append(f"Ospiti esenti: {summary.get('total_exempt_guests', 0)}")
        lines.append("")
        lines.append(f"TOTALE IMPOSTA: {self.format_currency(summary['total_tax_collected'])}")
        lines.append("")

        if "exemptions" in report:
            lines.append("DETTAGLIO ESENZIONI")
            lines.append("-" * 60)
            exemptions = report["exemptions"]
            lines.append(f"Minori: {exemptions['minors']}")
            lines.append(f"Autisti pullman: {exemptions['bus_drivers']}")
            lines.append(f"Guide turistiche: {exemptions['tour_guides']}")
            lines.append("")

        lines.append("=" * 60)
        lines.append(f"Generato il: {report['generated_at']}")
        lines.append("=" * 60)

        return "\n".join(lines)
