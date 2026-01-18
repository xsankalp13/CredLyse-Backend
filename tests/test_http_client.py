"""
HTTP Client Unit Tests

Tests for the connection pooling and retry logic.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx


class TestHttpClient:
    """Tests for the HTTP client module."""

    def test_get_http_client_returns_singleton(self):
        """Verify that get_http_client returns the same instance."""
        with patch("app.core.http_client._http_client", None):
            from app.core.http_client import get_http_client
            
            client1 = get_http_client()
            client2 = get_http_client()
            
            assert client1 is client2

    def test_http_client_has_connection_limits(self):
        """Verify connection pool limits are configured."""
        with patch("app.core.http_client._http_client", None):
            from app.core.http_client import get_http_client
            
            client = get_http_client()
            
            assert client._limits.max_connections == 100
            assert client._limits.max_keepalive_connections == 20


class TestRequestWithRetry:
    """Tests for retry logic."""

    @pytest.mark.asyncio
    async def test_retry_on_server_error(self):
        """Verify retry on 5xx status codes."""
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(
            side_effect=[mock_response_fail, mock_response_success]
        )
        
        with patch("app.core.http_client.get_http_client", return_value=mock_client):
            with patch("app.core.http_client.RETRY_BACKOFF_BASE", 0.01):  # Fast retry
                from app.core.http_client import request_with_retry
                
                response = await request_with_retry("GET", "http://test.com")
                
                assert response.status_code == 200
                assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_success(self):
        """Verify no retry when request succeeds."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        
        with patch("app.core.http_client.get_http_client", return_value=mock_client):
            from app.core.http_client import request_with_retry
            
            response = await request_with_retry("GET", "http://test.com")
            
            assert response.status_code == 200
            assert mock_client.request.call_count == 1

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        """Verify exception after all retries exhausted."""
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        
        with patch("app.core.http_client.get_http_client", return_value=mock_client):
            with patch("app.core.http_client.RETRY_BACKOFF_BASE", 0.01):
                from app.core.http_client import request_with_retry
                
                with pytest.raises(httpx.ConnectError):
                    await request_with_retry("GET", "http://test.com", max_retries=2)
                
                assert mock_client.request.call_count == 3  # Initial + 2 retries
