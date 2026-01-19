"""
Processing Service Unit Tests

Tests for concurrent video processing following TDD principles.
These tests verify the scalability improvements.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ==================== Concurrent Processing Tests ====================

class TestProcessCourseContent:
    """Tests for course content processing with concurrency."""

    @pytest.mark.asyncio
    async def test_process_videos_concurrently_with_semaphore(self, mock_async_session):
        """
        Verify that videos are processed concurrently with a semaphore limit.
        
        This is CRITICAL for scalability - processing 50 videos should not take
        50x the time of processing 1 video.
        """
        # Create mock videos
        mock_videos = [
            MagicMock(
                id=i,
                youtube_video_id=f"video_{i}",
                title=f"Video {i}",
                analysis_status="PENDING"
            )
            for i in range(10)
        ]
        
        # Track how many videos are being processed simultaneously
        concurrent_count = 0
        max_concurrent = 0
        
        async def mock_analyze(video_id, title):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.1)  # Simulate API call
            concurrent_count -= 1
            return {
                "success": True,
                "transcript": "test",
                "quiz_data": {"has_quiz": True, "questions": []},
                "method": "openai"
            }
        
        with patch("app.services.processing_service.ai_service") as mock_ai:
            mock_ai.analyze_video_content = mock_analyze
            
            # Mock playlist query
            mock_playlist = MagicMock(id=1, title="Test Playlist")
            mock_async_session.execute.return_value.scalar_one_or_none.return_value = mock_playlist
            mock_async_session.execute.return_value.scalars.return_value.all.return_value = mock_videos
            
            from app.services.processing_service import process_course_content
            
            result = await process_course_content(1, mock_async_session)
            
            # Verify concurrent processing happened (max should be > 1)
            assert max_concurrent > 1, f"Expected concurrent processing, but max was {max_concurrent}"
            assert max_concurrent <= 5, f"Semaphore limit exceeded: {max_concurrent}"

    @pytest.mark.asyncio
    async def test_process_handles_partial_failures(self, mock_async_session):
        """
        Verify that processing continues even when some videos fail.
        
        Important for reliability - one bad video shouldn't stop the entire batch.
        """
        mock_videos = [
            MagicMock(
                id=i,
                youtube_video_id=f"video_{i}",
                title=f"Video {i}",
                analysis_status="PENDING"
            )
            for i in range(5)
        ]
        
        call_count = 0
        
        async def mock_analyze(video_id, title):
            nonlocal call_count
            call_count += 1
            if call_count == 3:  # Fail on 3rd video
                raise Exception("API Error")
            return {
                "success": True,
                "transcript": "test",
                "quiz_data": {"has_quiz": True, "questions": []},
                "method": "openai"
            }
        
        with patch("app.services.processing_service.ai_service") as mock_ai:
            mock_ai.analyze_video_content = mock_analyze
            
            mock_playlist = MagicMock(id=1, title="Test Playlist")
            mock_async_session.execute.return_value.scalar_one_or_none.return_value = mock_playlist
            mock_async_session.execute.return_value.scalars.return_value.all.return_value = mock_videos
            
            from app.services.processing_service import process_course_content
            
            result = await process_course_content(1, mock_async_session)
            
            # Should have processed all 5, with 1 failure
            assert result["processed"] + result["failed"] == 5

    @pytest.mark.asyncio
    async def test_process_empty_playlist_returns_early(self, mock_async_session):
        """Verify early return when no pending videos exist."""
        mock_playlist = MagicMock(id=1, title="Test Playlist")
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = mock_playlist
        mock_async_session.execute.return_value.scalars.return_value.all.return_value = []
        
        from app.services.processing_service import process_course_content
        
        result = await process_course_content(1, mock_async_session)
        
        assert result["success"] is True
        assert result["processed"] == 0
        assert "No pending videos" in result.get("message", "")


# ==================== Analysis Status Tests ====================

class TestGetAnalysisStatus:
    """Tests for analysis status retrieval."""

    @pytest.mark.asyncio
    async def test_get_status_counts_correctly(self, mock_async_session):
        """Verify accurate counting of video statuses."""
        from app.models.enums import AnalysisStatus
        
        mock_videos = [
            MagicMock(analysis_status=AnalysisStatus.PENDING, has_quiz=False),
            MagicMock(analysis_status=AnalysisStatus.PENDING, has_quiz=False),
            MagicMock(analysis_status=AnalysisStatus.COMPLETED, has_quiz=True),
            MagicMock(analysis_status=AnalysisStatus.COMPLETED, has_quiz=False),
            MagicMock(analysis_status=AnalysisStatus.FAILED, has_quiz=False),
        ]
        
        mock_async_session.execute.return_value.scalars.return_value.all.return_value = mock_videos
        
        from app.services.processing_service import get_analysis_status
        
        result = await get_analysis_status(1, mock_async_session)
        
        assert result["total"] == 5
        assert result["pending"] == 2
        assert result["completed"] == 2
        assert result["failed"] == 1
        assert result["with_quiz"] == 1
