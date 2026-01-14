"""
Video Model

Individual video within a playlist/course with AI analysis data.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AnalysisStatus

if TYPE_CHECKING:
    from app.models.playlist import Playlist
    from app.models.video_progress import VideoProgress


class Video(Base):
    """
    Video model representing individual videos in a course.
    
    Attributes:
        id: Integer primary key.
        playlist_id: Foreign key to playlists table.
        youtube_video_id: Unique YouTube video ID.
        title: Video title.
        duration_seconds: Video duration in seconds.
        transcript_text: AI-extracted transcript (nullable).
        has_quiz: Whether this video has an AI-generated quiz.
        quiz_data: JSONB containing quiz questions and answers.
        analysis_status: Status of AI analysis (PENDING, COMPLETED, FAILED).
    """
    
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    playlist_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
    )
    youtube_video_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    transcript_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    has_quiz: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    quiz_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    analysis_status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, name="analysis_status", create_constraint=True),
        default=AnalysisStatus.PENDING,
        nullable=False,
    )

    # Relationships
    playlist: Mapped["Playlist"] = relationship(
        "Playlist",
        back_populates="videos",
    )
    progress_records: Mapped[list["VideoProgress"]] = relationship(
        "VideoProgress",
        back_populates="video",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Video(id={self.id}, youtube_id={self.youtube_video_id})>"
