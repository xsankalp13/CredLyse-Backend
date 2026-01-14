"""
Credlyse Backend - Models Module

This module exports all SQLAlchemy models for the application.
Import Base for Alembic migrations.
"""

from app.core.database import Base

# Enums
from app.models.enums import (
    UserRole,
    PlaylistType,
    AnalysisStatus,
    WatchStatus,
)

# Models
from app.models.user import User
from app.models.creator_profile import CreatorProfile
from app.models.playlist import Playlist
from app.models.video import Video
from app.models.enrollment import Enrollment
from app.models.video_progress import VideoProgress
from app.models.certificate import Certificate

__all__ = [
    # Base
    "Base",
    # Enums
    "UserRole",
    "PlaylistType",
    "AnalysisStatus",
    "WatchStatus",
    # Models
    "User",
    "CreatorProfile",
    "Playlist",
    "Video",
    "Enrollment",
    "VideoProgress",
    "Certificate",
]
