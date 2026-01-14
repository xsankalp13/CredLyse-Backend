"""
Certificate Model

Course completion certificates with UUID for verification.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.playlist import Playlist


class Certificate(Base):
    """
    Certificate model for course completion.
    
    UUID primary key is used for public verification links.
    
    Attributes:
        id: UUID primary key for verification URLs.
        user_id: Foreign key to users table.
        playlist_id: Foreign key to playlists table.
        issued_at: Timestamp when certificate was issued.
        pdf_url: URL to the generated PDF certificate.
    """
    
    __tablename__ = "certificates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    playlist_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    pdf_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="certificates",
    )
    playlist: Mapped["Playlist"] = relationship(
        "Playlist",
        back_populates="certificates",
    )

    def __repr__(self) -> str:
        return f"<Certificate(id={self.id}, user_id={self.user_id})>"
