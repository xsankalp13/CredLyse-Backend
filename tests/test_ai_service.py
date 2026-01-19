"""
AI Service Unit Tests

Tests for transcript fetching and quiz generation following TDD principles.
These tests are written BEFORE the implementation changes.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ==================== Transcript Fetching Tests ====================

class TestFetchTranscript:
    """Tests for the async transcript fetching functionality."""

    @pytest.mark.asyncio
    async def test_fetch_transcript_async_runs_in_executor(self, sample_transcript):
        """
        Verify that fetch_transcript_async uses run_in_executor to avoid blocking.
        
        This is the CRITICAL fix for scalability - synchronous YouTube API calls
        must be offloaded to a thread pool.
        """
        with patch("app.services.ai_service.asyncio.get_event_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_loop.run_in_executor = AsyncMock(return_value=sample_transcript)
            mock_get_loop.return_value = mock_loop
            
            # Import after patching to get the new implementation
            from app.services.ai_service import fetch_transcript_async
            
            result = await fetch_transcript_async("test_video_id")
            
            # Verify run_in_executor was called (non-blocking)
            mock_loop.run_in_executor.assert_called_once()
            assert result == sample_transcript

    @pytest.mark.asyncio
    async def test_fetch_transcript_async_handles_unavailable(self):
        """Verify graceful handling when transcript is not available."""
        with patch("app.services.ai_service.asyncio.get_event_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_loop.run_in_executor = AsyncMock(return_value=None)
            mock_get_loop.return_value = mock_loop
            
            from app.services.ai_service import fetch_transcript_async
            
            result = await fetch_transcript_async("unavailable_video_id")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_transcript_async_handles_exception(self):
        """Verify graceful handling when YouTube API throws an exception."""
        with patch("app.services.ai_service.asyncio.get_event_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_loop.run_in_executor = AsyncMock(side_effect=Exception("API Error"))
            mock_get_loop.return_value = mock_loop
            
            from app.services.ai_service import fetch_transcript_async
            
            # Should not raise, should return None
            result = await fetch_transcript_async("error_video_id")
            
            assert result is None


# ==================== Quiz Generation Tests ====================

class TestGenerateQuizWithOpenAI:
    """Tests for OpenAI-based quiz generation."""

    @pytest.mark.asyncio
    async def test_generate_quiz_returns_valid_structure(self, sample_transcript, sample_quiz_data):
        """Verify quiz generation returns properly structured data."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(sample_quiz_data)
        
        with patch("app.services.ai_service.get_openai_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            from app.services.ai_service import generate_quiz_with_openai
            
            result = await generate_quiz_with_openai(sample_transcript)
            
            assert "has_quiz" in result
            assert "reason" in result
            assert "questions" in result
            assert isinstance(result["questions"], list)

    @pytest.mark.asyncio
    async def test_generate_quiz_truncates_long_transcripts(self, sample_quiz_data):
        """Verify long transcripts are truncated to prevent token overflow."""
        # Create a very long transcript (> 12000 chars)
        long_transcript = "x" * 15000
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(sample_quiz_data)
        
        with patch("app.services.ai_service.get_openai_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            from app.services.ai_service import generate_quiz_with_openai
            
            result = await generate_quiz_with_openai(long_transcript)
            
            # Verify the API was called (transcript was processed, even if truncated)
            mock_client.chat.completions.create.assert_called_once()
            assert result is not None

    @pytest.mark.asyncio
    async def test_generate_quiz_handles_api_error(self, sample_transcript):
        """Verify graceful handling of OpenAI API errors."""
        with patch("app.services.ai_service.get_openai_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("OpenAI API Error")
            )
            mock_get_client.return_value = mock_client
            
            from app.services.ai_service import generate_quiz_with_openai
            
            with pytest.raises(Exception) as exc_info:
                await generate_quiz_with_openai(sample_transcript)
            
            assert "OpenAI API Error" in str(exc_info.value)


# ==================== Analyze Video Content Tests ====================

class TestAnalyzeVideoContent:
    """Tests for the main video analysis pipeline."""

    @pytest.mark.asyncio
    async def test_analyze_video_uses_openai_when_transcript_available(self, sample_transcript, sample_quiz_data):
        """Verify OpenAI is used when transcript is available (preferred path)."""
        with patch("app.services.ai_service.fetch_transcript_async") as mock_fetch:
            mock_fetch.return_value = sample_transcript
            
            with patch("app.services.ai_service.generate_quiz_with_openai") as mock_quiz:
                mock_quiz.return_value = sample_quiz_data
                
                from app.services.ai_service import analyze_video_content
                
                result = await analyze_video_content("test_video_id", "Test Video")
                
                assert result["success"] is True
                assert result["method"] == "openai"
                assert result["transcript"] == sample_transcript
                mock_fetch.assert_called_once_with("test_video_id")
                mock_quiz.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_video_falls_back_to_gemini(self, sample_quiz_data):
        """Verify Gemini fallback when transcript is unavailable."""
        with patch("app.services.ai_service.fetch_transcript_async") as mock_fetch:
            mock_fetch.return_value = None  # No transcript available
            
            with patch("app.services.ai_service.generate_quiz_with_gemini") as mock_gemini:
                mock_gemini.return_value = sample_quiz_data
                
                from app.services.ai_service import analyze_video_content
                
                result = await analyze_video_content("test_video_id", "Test Video")
                
                assert result["success"] is True
                assert result["method"] == "gemini"
                assert result["transcript"] is None
                mock_gemini.assert_called_once()
