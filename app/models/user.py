"""
User Model

Core user entity with authentication and role management.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.creator_profile import CreatorProfile
    from app.models.enrollment import Enrollment
    from app.models.certificate import Certificate


class User(Base):
    """
    User model representing students, creators, and admins.
    
    Attributes:
        id: UUID primary key for public-facing identification.
        email: Unique email address, indexed for fast lookups.
        password_hash: Hashed password (never store plain text).
        full_name: User's display name.
        role: User role (STUDENT, CREATOR, ADMIN).
        created_at: Account creation timestamp.
    """
    
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True),
        default=UserRole.STUDENT,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Email Verification
    is_email_verified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # OAuth Fields
    google_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )
    auth_provider: Mapped[str] = mapped_column(
        String(50),
        default="email",
        nullable=False,
    )
    profile_picture_url: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )

    # Relationships
    creator_profile: Mapped[Optional["CreatorProfile"]] = relationship(
        "CreatorProfile",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="user",
        lazy="selectin",
    )
    certificates: Mapped[list["Certificate"]] = relationship(
        "Certificate",
        back_populates="user",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
