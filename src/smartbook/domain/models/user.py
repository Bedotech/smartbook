"""
User model for multi-user authentication.
"""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from smartbook.domain.models.base import Base

if TYPE_CHECKING:
    from smartbook.domain.models.user_property_assignment import UserPropertyAssignment


class User(Base):
    """
    User model for authentication and authorization.

    Users authenticate via OAuth (Google) and can be assigned to
    multiple properties through the UserPropertyAssignment junction table.

    Roles:
    - admin: Full access (create/edit bookings, manage properties, users)
    - staff: View-only access (view bookings and reports)
    """

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # User information
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="User email address (unique)",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="User full name",
    )

    # OAuth provider information
    oauth_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="OAuth provider (e.g., 'google', 'microsoft')",
    )
    oauth_provider_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="OAuth provider user ID (e.g., Google sub claim)",
    )
    oauth_picture_url: Mapped[str | None] = mapped_column(
        String(500),
        comment="Profile picture URL from OAuth provider",
    )

    # Authorization
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="admin",
        comment="User role: 'admin' (full access) or 'staff' (view-only)",
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether user account is active",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="Last successful login timestamp",
    )

    # Relationships
    property_assignments: Mapped[list["UserPropertyAssignment"]] = relationship(
        "UserPropertyAssignment",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="[UserPropertyAssignment.user_id]",
    )

    # Self-referential relationship for assignments created by this user
    assignments_created: Mapped[list["UserPropertyAssignment"]] = relationship(
        "UserPropertyAssignment",
        back_populates="assigned_by",
        foreign_keys="[UserPropertyAssignment.assigned_by_user_id]",
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
