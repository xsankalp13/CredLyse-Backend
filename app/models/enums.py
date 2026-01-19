"""
Database Enums

Python Enums that map to PostgreSQL ENUM types.
"""

import enum


class UserRole(str, enum.Enum):
    """User role enumeration."""
    STUDENT = "STUDENT"
    CREATOR = "CREATOR"
    ADMIN = "ADMIN"


class PlaylistType(str, enum.Enum):
    """Playlist type enumeration."""
    PLAYLIST = "PLAYLIST"
    SINGLE_VIDEO = "SINGLE_VIDEO"


class AnalysisStatus(str, enum.Enum):
    """Video analysis status enumeration."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WatchStatus(str, enum.Enum):
    """Video watch status enumeration."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    WATCHED = "WATCHED"


class OTPPurpose(str, enum.Enum):
    """OTP purpose enumeration."""
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    PASSWORD_RESET = "PASSWORD_RESET"

