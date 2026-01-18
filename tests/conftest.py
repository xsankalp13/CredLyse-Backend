"""
Pytest Configuration and Fixtures

Provides reusable async fixtures for testing the CredLyse Backend.
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


# ==================== Database Fixtures ====================

@pytest.fixture
def mock_async_session() -> AsyncMock:
    """
    Create a mock async database session.
    
    Returns:
        AsyncMock configured to behave like AsyncSession.
    """
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    return session


# ==================== HTTP Client Fixtures ====================

@pytest.fixture
def mock_httpx_response():
    """
    Factory fixture to create mock httpx responses.
    
    Usage:
        response = mock_httpx_response(status_code=200, json_data={"key": "value"})
    """
    def _create_response(status_code: int = 200, json_data: dict = None, text: str = ""):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.text = text
        return response
    return _create_response


@pytest.fixture
def mock_httpx_client(mock_httpx_response):
    """
    Create a mock httpx.AsyncClient.
    
    Returns:
        AsyncMock configured for HTTP operations.
    """
    client = AsyncMock()
    client.get = AsyncMock(return_value=mock_httpx_response())
    client.post = AsyncMock(return_value=mock_httpx_response())
    return client


# ==================== OpenAI Fixtures ====================

@pytest.fixture
def mock_openai_response():
    """
    Create a mock OpenAI chat completion response.
    
    Returns:
        MagicMock structured like OpenAI ChatCompletion.
    """
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = '{"has_quiz": true, "reason": "Educational content", "questions": []}'
    return response


@pytest.fixture
def mock_openai_client(mock_openai_response):
    """
    Create a mock OpenAI async client.
    
    Returns:
        AsyncMock configured for chat completions.
    """
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
    return client


# ==================== Transcript Fixtures ====================

@pytest.fixture
def sample_transcript() -> str:
    """Sample transcript text for testing."""
    return """
    Welcome to this Python tutorial. Today we will learn about decorators.
    Decorators are a powerful feature in Python that allows you to modify
    the behavior of functions or classes. Let's start with a simple example.
    A decorator is essentially a function that takes another function as input
    and returns a new function with extended functionality.
    """


@pytest.fixture
def sample_quiz_data() -> dict:
    """Sample quiz data structure for testing."""
    return {
        "has_quiz": True,
        "reason": "Educational content about Python decorators",
        "questions": [
            {
                "q": "What is a decorator in Python?",
                "options": [
                    "A function that modifies another function",
                    "A type of variable",
                    "A loop construct",
                    "A class method"
                ],
                "answer": "A function that modifies another function"
            },
            {
                "q": "What does a decorator return?",
                "options": [
                    "A new function with extended functionality",
                    "The original function unchanged",
                    "A string",
                    "None"
                ],
                "answer": "A new function with extended functionality"
            }
        ]
    }


# ==================== Video/Playlist Fixtures ====================

@pytest.fixture
def sample_video_data() -> dict:
    """Sample video metadata for testing."""
    return {
        "id": 1,
        "youtube_video_id": "dQw4w9WgXcQ",
        "title": "Python Decorators Tutorial",
        "duration_seconds": 600,
        "analysis_status": "PENDING",
        "has_quiz": False,
        "quiz_data": None,
        "transcript_text": None,
    }


@pytest.fixture
def sample_playlist_data() -> dict:
    """Sample playlist metadata for testing."""
    return {
        "id": 1,
        "Youtubelist_id": "PLxxxxxxxxxxxxxxx",
        "title": "Complete Python Course",
        "description": "Learn Python from scratch",
        "total_videos": 10,
        "is_published": False,
        "creator_id": 1,
    }
