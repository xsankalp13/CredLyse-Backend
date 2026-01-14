"""
Playlist Model

Course container representing YouTube playlists or single videos.
"""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PlaylistType

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.video import Video
    from app.models.enrollment import Enrollment
    from app.models.certificate import Certificate


class Playlist(Base):
    """
    Playlist model representing a course container.
    
    Can be either a full YouTube playlist or a single video course.
    
    Attributes:
        id: Integer primary key.
        creator_id: Foreign key to the creator user.
        Youtubelist_id: Unique YouTube playlist/video ID.
        title: Course title.
        description: Course description.
        type: PLAYLIST or SINGLE_VIDEO.
        total_videos: Number of videos in the course.
        is_published: Whether the course is publicly visible.
    """
    
    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    Youtubelist_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    type: Mapped[PlaylistType] = mapped_column(
        Enum(PlaylistType, name="playlist_type", create_constraint=True),
        default=PlaylistType.PLAYLIST,
        nullable=False,
    )
    total_videos: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[creator_id],
        lazy="selectin",
    )
    videos: Mapped[list["Video"]] = relationship(
        "Video",
        back_populates="playlist",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="playlist",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    certificates: Mapped[list["Certificate"]] = relationship(
        "Certificate",
        back_populates="playlist",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Playlist(id={self.id}, title={self.title[:30]}...)>"
