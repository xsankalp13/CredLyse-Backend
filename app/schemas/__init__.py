"""
Credlyse Backend - Schemas Module

Pydantic models for request/response validation.
"""

from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserLogin
from app.schemas.token import Token, TokenPayload
from app.schemas.course import (
    VideoBase,
    VideoResponse,
    PlaylistCreate,
    PlaylistBase,
    PlaylistResponse,
    PlaylistListResponse,
)

__all__ = [
    # User
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "UserLogin",
    # Token
    "Token",
    "TokenPayload",
    # Course
    "VideoBase",
    "VideoResponse",
    "PlaylistCreate",
    "PlaylistBase",
    "PlaylistResponse",
    "PlaylistListResponse",
]
