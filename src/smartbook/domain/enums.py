"""
Enumerations for domain models.
"""

from enum import Enum


class GuestType(str, Enum):
    """Guest type codes for ROS1000."""
    SINGLE_GUEST = "16"  # Ospite Singolo
    FAMILY_HEAD = "17"   # Capofamiglia
    FAMILY_MEMBER = "18"  # Familiare
    GROUP_LEADER = "19"   # Capogruppo
    GROUP_MEMBER = "20"   # Membro Gruppo


class GuestRole(str, Enum):
    """Guest roles within a booking."""
    LEADER = "leader"        # Group/Family head (Capogruppo/Capofamiglia)
    MEMBER = "member"        # Group/Family member
    BUS_DRIVER = "bus_driver"  # Exempt bus driver (1 per 25 guests)
    TOUR_GUIDE = "tour_guide"  # Exempt tour guide


class Sex(str, Enum):
    """Biological sex."""
    MALE = "M"
    FEMALE = "F"


class DocumentType(str, Enum):
    """Identity document types."""
    PASSPORT = "passport"
    ID_CARD = "id_card"
    DRIVING_LICENSE = "driving_license"
    OTHER = "other"


class BookingType(str, Enum):
    """Type of booking."""
    INDIVIDUAL = "individual"
    FAMILY = "family"
    GROUP = "group"


class BookingStatus(str, Enum):
    """Booking workflow status."""
    PENDING = "pending"          # Created, magic link not used yet
    IN_PROGRESS = "in_progress"  # Guest is entering data
    COMPLETE = "complete"        # All guest data entered
    SYNCED = "synced"            # Transmitted to ROS1000 successfully
    ERROR = "error"              # ROS1000 transmission error


class ComplianceStatus(str, Enum):
    """ROS1000 compliance record status."""
    SUBMITTED = "submitted"        # Successfully submitted and accepted
    FAILED = "failed"              # Submission failed
    CANCELLED = "cancelled"        # Submission cancelled/corrected
    SUCCESS = "success"            # Both Region and Police accepted (legacy)
    PARTIAL_SUCCESS = "partial_success"  # Region OK, Police error (legacy)
    FAILURE = "failure"            # Complete rejection (legacy)
