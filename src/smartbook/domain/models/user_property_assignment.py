"""
UserPropertyAssignment model for many-to-many relationship between users and properties.
"""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from smartbook.domain.models.base import Base

if TYPE_CHECKING:
    from smartbook.domain.models.user import User
    from smartbook.domain.models.tenant import Tenant  # Will be renamed to Property


class UserPropertyAssignment(Base):
    """
    Junction table for many-to-many relationship between users and properties.

    Allows:
    - One user to manage multiple properties
    - One property to be managed by multiple users
    - Tracking who assigned whom to what property
    """

    __tablename__ = "user_property_assignments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to users table",
    )
    property_id: Mapped[UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to properties table",
    )

    # Assignment metadata
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When this assignment was created",
    )
    assigned_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="Which user created this assignment (NULL for migration/system)",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="property_assignments",
        foreign_keys=[user_id],
    )
    property: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="user_assignments",
    )
    assigned_by: Mapped["User | None"] = relationship(
        "User",
        back_populates="assignments_created",
        foreign_keys=[assigned_by_user_id],
    )

    def __repr__(self) -> str:
        return f"<UserPropertyAssignment user_id={self.user_id} property_id={self.property_id}>"
