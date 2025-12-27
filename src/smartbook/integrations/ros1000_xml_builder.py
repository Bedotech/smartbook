"""
ROS1000 XML Builder for TULPS compliance reporting.

Builds XML according to the ROS1000/Alloggiati Web schema for submission
to the Questura (Police) and ISTAT (National Statistics Institute).

Key compliance requirements:
- Group leaders require full document details
- Group members require TULPS minimums (name, DOB, sex, residence)
- ISTAT codes for municipalities and countries
- Accommodation facility identification
- Proper date/time formatting (ISO 8601)
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Sequence
from xml.etree import ElementTree as ET
from xml.dom import minidom

from smartbook.domain.models.guest import Guest
from smartbook.domain.models.booking import Booking
from smartbook.domain.models.tenant import Tenant
from smartbook.domain.enums import GuestType, GuestRole, Sex, DocumentType


class ROS1000XMLBuilderError(Exception):
    """Raised when XML building fails."""
    pass


class ROS1000XMLBuilder:
    """
    XML builder for ROS1000/Alloggiati Web submissions.

    Generates properly formatted XML for police reporting according to
    Italian TULPS regulations (Art. 109).
    """

    def __init__(self, tenant: Tenant):
        """
        Initialize XML builder with tenant/facility information.

        Args:
            tenant: Tenant (accommodation facility) information
        """
        self.tenant = tenant

    def build_submission(
        self,
        booking: Booking,
        guests: Sequence[Guest],
    ) -> str:
        """
        Build complete ROS1000 XML submission for a booking.

        Args:
            booking: Booking information
            guests: List of guests (must include leader)

        Returns:
            Formatted XML string ready for SOAP submission

        Raises:
            ROS1000XMLBuilderError: If validation fails or required data missing
        """
        # Validate inputs
        self._validate_submission_data(booking, guests)

        # Build XML structure
        root = self._build_root_element()
        header = self._build_header(booking)
        root.append(header)

        # Add guests
        guests_element = ET.SubElement(root, "Ospiti")

        for guest in guests:
            guest_element = self._build_guest_element(guest, booking)
            guests_element.append(guest_element)

        # Format and return XML
        return self._format_xml(root)

    def _validate_submission_data(
        self,
        booking: Booking,
        guests: Sequence[Guest],
    ) -> None:
        """
        Validate that submission data meets ROS1000 requirements.

        Args:
            booking: Booking to validate
            guests: Guests to validate

        Raises:
            ROS1000XMLBuilderError: If validation fails
        """
        if not guests:
            raise ROS1000XMLBuilderError("No guests provided for submission")

        # Check for group leader
        has_leader = any(
            guest.guest_type == GuestType.GROUP_LEADER for guest in guests
        )
        if not has_leader:
            raise ROS1000XMLBuilderError(
                "Group submission requires at least one leader"
            )

        # Validate leader has full document details
        for guest in guests:
            if guest.guest_type == GuestType.GROUP_LEADER:
                if not guest.document_number or not guest.document_type:
                    raise ROS1000XMLBuilderError(
                        f"Group leader {guest.id} missing required document details"
                    )

        # Validate TULPS minimums for all guests
        for guest in guests:
            if not all([
                guest.first_name,
                guest.last_name,
                guest.date_of_birth,
                guest.sex,
            ]):
                raise ROS1000XMLBuilderError(
                    f"Guest {guest.id} missing TULPS minimum data "
                    "(name, DOB, sex required)"
                )

    def _build_root_element(self) -> ET.Element:
        """Build root XML element with namespace declarations."""
        root = ET.Element("AlloggiatiRoot")
        root.set("xmlns", "http://alloggiatiweb.poliziadistato.it/schema")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        return root

    def _build_header(self, booking: Booking) -> ET.Element:
        """
        Build header section with facility and booking information.

        Args:
            booking: Booking information

        Returns:
            Header XML element
        """
        header = ET.Element("Testata")

        # Facility identification
        facility = ET.SubElement(header, "Struttura")
        ET.SubElement(facility, "CodiceFiscale").text = self.tenant.tax_id or ""
        ET.SubElement(facility, "CodiceStruttura").text = self.tenant.facility_code

        # Arrival date
        ET.SubElement(header, "DataArrivo").text = booking.check_in_date.isoformat()

        # Number of guests
        ET.SubElement(header, "NumeroOspiti").text = str(booking.expected_guests)

        # Submission timestamp
        ET.SubElement(header, "DataInvio").text = datetime.now().isoformat()

        return header

    def _build_guest_element(
        self,
        guest: Guest,
        booking: Booking,
    ) -> ET.Element:
        """
        Build guest element with personal and document data.

        Args:
            guest: Guest information
            booking: Booking information (for dates)

        Returns:
            Guest XML element
        """
        ospite = ET.Element("Ospite")

        # Guest type (19 = leader, 20 = member)
        ET.SubElement(ospite, "TipoAlloggiato").text = guest.guest_type.value

        # Personal data (required for all)
        anagrafica = ET.SubElement(ospite, "Anagrafica")
        ET.SubElement(anagrafica, "Cognome").text = guest.last_name
        ET.SubElement(anagrafica, "Nome").text = guest.first_name
        ET.SubElement(anagrafica, "Sesso").text = self._format_sex(guest.sex)
        ET.SubElement(anagrafica, "DataNascita").text = guest.date_of_birth.isoformat()

        # Birth place (if available)
        if guest.birth_municipality_code:
            ET.SubElement(anagrafica, "ComuneNascitaCod").text = guest.birth_municipality_code
        if guest.birth_country_code:
            ET.SubElement(anagrafica, "StatoNascitaCod").text = guest.birth_country_code

        # Citizenship
        if guest.citizenship_country_code:
            ET.SubElement(anagrafica, "Cittadinanza").text = guest.citizenship_country_code

        # Residence (required for all)
        residenza = ET.SubElement(ospite, "Residenza")
        if guest.residence_municipality_code:
            ET.SubElement(residenza, "ComuneCod").text = guest.residence_municipality_code
        if guest.residence_country_code:
            ET.SubElement(residenza, "StatoCod").text = guest.residence_country_code
        if guest.residence_address:
            ET.SubElement(residenza, "Indirizzo").text = guest.residence_address

        # Document data (required for leaders, optional for members)
        if guest.document_type and guest.document_number:
            documento = ET.SubElement(ospite, "Documento")
            ET.SubElement(documento, "TipoDocumento").text = self._format_document_type(
                guest.document_type
            )
            ET.SubElement(documento, "NumeroDocumento").text = guest.document_number

            if guest.document_issuing_authority:
                ET.SubElement(documento, "LuogoRilascio").text = (
                    guest.document_issuing_authority
                )
            if guest.document_issue_date:
                ET.SubElement(documento, "DataRilascio").text = (
                    guest.document_issue_date.isoformat()
                )
            if guest.document_issue_place:
                ET.SubElement(documento, "ComuneRilascio").text = (
                    guest.document_issue_place
                )

        # Stay dates
        soggiorno = ET.SubElement(ospite, "Soggiorno")
        ET.SubElement(soggiorno, "DataArrivo").text = booking.check_in_date.isoformat()
        ET.SubElement(soggiorno, "DataPartenza").text = booking.check_out_date.isoformat()

        return ospite

    def _format_sex(self, sex: Sex) -> str:
        """
        Format sex enum for ROS1000.

        Args:
            sex: Sex enum value

        Returns:
            ROS1000 format (1 = M, 2 = F)
        """
        return "1" if sex == Sex.MALE else "2"

    def _format_document_type(self, doc_type: DocumentType) -> str:
        """
        Format document type for ROS1000.

        Args:
            doc_type: Document type enum

        Returns:
            ROS1000 document type code
        """
        mapping = {
            DocumentType.ID_CARD: "1",  # Carta d'identità
            DocumentType.PASSPORT: "2",  # Passaporto
            DocumentType.DRIVING_LICENSE: "3",  # Patente
            DocumentType.OTHER: "9",  # Altro
        }
        return mapping.get(doc_type, "9")

    def _format_xml(self, root: ET.Element) -> str:
        """
        Format XML with proper indentation for human readability.

        Args:
            root: Root XML element

        Returns:
            Formatted XML string
        """
        # Convert to string
        xml_str = ET.tostring(root, encoding="unicode")

        # Parse and prettify
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ", encoding="UTF-8")

        # Remove empty lines and decode
        lines = [
            line for line in pretty_xml.decode("utf-8").split("\n")
            if line.strip()
        ]

        return "\n".join(lines)

    def validate_xml_structure(self, xml_string: str) -> bool:
        """
        Validate XML structure (basic well-formedness check).

        Args:
            xml_string: XML string to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            ET.fromstring(xml_string)
            return True
        except ET.ParseError:
            return False

    def build_cancellation_xml(
        self,
        booking: Booking,
        guests: Sequence[Guest],
    ) -> str:
        """
        Build XML for canceling/correcting a previous submission.

        Args:
            booking: Original booking
            guests: Guests to cancel

        Returns:
            Cancellation XML string
        """
        root = self._build_root_element()
        root.set("TipoOperazione", "CANCELLAZIONE")

        header = self._build_header(booking)
        root.append(header)

        # Add reference to original submission
        if booking.ros1000_receipt_number:
            ET.SubElement(header, "NumeroRicevuta").text = (
                booking.ros1000_receipt_number
            )

        return self._format_xml(root)
