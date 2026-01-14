"""
Video Progress Model

Granular tracking of user progress within individual videos.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import WatchStatus

if TYPE_CHECKING:
    from app.models.enrollment import Enrollment
    from app.models.video import Video


class VideoProgress(Base):
    """
    Video progress model for granular watch tracking.
    
    Links progress to a specific enrollment (user taking a course).
    
    Attributes:
        id: Integer primary key.
        enrollment_id: Foreign key to enrollments table.
        video_id: Foreign key to videos table.
        watch_status: Current watch status (NOT_STARTED, IN_PROGRESS, WATCHED).
        seconds_watched: Number of seconds watched (for progress bar).
        quiz_score: User's score on the video quiz (nullable).
        is_quiz_passed: Whether the user passed the quiz.
    """
    
    __tablename__ = "video_progress"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    enrollment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("enrollments.id", ondelete="CASCADE"),
        nullable=False,
    )
    video_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
    )
    watch_status: Mapped[WatchStatus] = mapped_column(
        Enum(WatchStatus, name="watch_status", create_constraint=True),
        default=WatchStatus.NOT_STARTED,
        nullable=False,
    )
    seconds_watched: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    quiz_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    is_quiz_passed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    enrollment: Mapped["Enrollment"] = relationship(
        "Enrollment",
        back_populates="video_progress",
    )
    video: Mapped["Video"] = relationship(
        "Video",
        back_populates="progress_records",
    )

    def __repr__(self) -> str:
        return f"<VideoProgress(id={self.id}, status={self.watch_status})>"
