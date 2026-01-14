"""
Creator Profile Model

Extended profile for content creators with social links and stats.
"""

import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class CreatorProfile(Base):
    """
    Creator profile model for users with CREATOR role.
    
    One-to-one relationship with User model.
    
    Attributes:
        id: Integer primary key.
        user_id: Foreign key to users table.
        public_handle: Unique public identifier (e.g., "@sarthak").
        bio: Creator biography/description.
        social_links: JSON object containing social media links.
        total_students: Count of enrolled students across all courses.
    """
    
    __tablename__ = "creator_profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    public_handle: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    social_links: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    total_students: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="creator_profile",
    )

    def __repr__(self) -> str:
        return f"<CreatorProfile(id={self.id}, handle={self.public_handle})>"
