"""
Rate Limiting Unit Tests

Tests for token bucket and rate limiter functionality.
"""

import time
from unittest.mock import MagicMock

import pytest


class TestTokenBucket:
    """Tests for TokenBucket implementation."""

    def test_initial_tokens_at_capacity(self):
        """Verify bucket starts at full capacity."""
        from app.middleware.rate_limit import TokenBucket
        
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        
        assert bucket.tokens == 10.0

    def test_consume_reduces_tokens(self):
        """Verify consuming tokens reduces count."""
        from app.middleware.rate_limit import TokenBucket
        
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        
        assert bucket.consume(3) is True
        assert bucket.tokens == 7.0

    def test_consume_fails_when_empty(self):
        """Verify consume fails when insufficient tokens."""
        from app.middleware.rate_limit import TokenBucket
        
        bucket = TokenBucket(capacity=2, refill_rate=0.1)
        
        assert bucket.consume(2) is True
        assert bucket.consume(1) is False

    def test_refill_over_time(self):
        """Verify tokens refill over time."""
        from app.middleware.rate_limit import TokenBucket
        
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10 tokens/sec
        
        # Consume all tokens
        bucket.consume(10)
        assert bucket.tokens == 0.0
        
        # Wait for refill
        time.sleep(0.5)
        
        # Should have refilled some tokens
        bucket._refill()
        assert bucket.tokens >= 4.0  # At least 5 tokens after 0.5s at 10/sec


class TestRateLimiter:
    """Tests for RateLimiter implementation."""

    def test_allows_requests_within_limit(self):
        """Verify requests within limit are allowed."""
        from app.middleware.rate_limit import RateLimiter
        
        limiter = RateLimiter(requests_per_minute=60, burst_capacity=5)
        
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = None
        mock_request.state = MagicMock()
        mock_request.state.user = None
        
        # First 5 requests should be allowed (burst capacity)
        for _ in range(5):
            assert limiter.is_allowed(mock_request) is True

    def test_blocks_requests_over_burst(self):
        """Verify requests over burst limit are blocked."""
        from app.middleware.rate_limit import RateLimiter
        
        limiter = RateLimiter(requests_per_minute=60, burst_capacity=3)
        
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers.get.return_value = None
        mock_request.state = MagicMock()
        mock_request.state.user = None
        
        # First 3 requests allowed
        for _ in range(3):
            assert limiter.is_allowed(mock_request) is True
        
        # 4th request should be blocked
        assert limiter.is_allowed(mock_request) is False

    def test_uses_user_id_when_authenticated(self):
        """Verify user ID is used for authenticated users."""
        from app.middleware.rate_limit import RateLimiter
        
        limiter = RateLimiter(requests_per_minute=60, burst_capacity=5)
        
        mock_user = MagicMock()
        mock_user.id = 123
        
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = None
        mock_request.state.user = mock_user
        
        key = limiter._get_key(mock_request)
        
        assert key == "user:123"

    def test_cleanup_removes_stale_buckets(self):
        """Verify cleanup removes old buckets."""
        from app.middleware.rate_limit import RateLimiter
        
        limiter = RateLimiter(requests_per_minute=60, burst_capacity=5)
        
        # Create a bucket manually
        mock_request = MagicMock()
        mock_request.client.host = "10.0.0.1"
        mock_request.headers.get.return_value = None
        mock_request.state = MagicMock()
        mock_request.state.user = None
        
        limiter.is_allowed(mock_request)
        
        assert len(limiter._buckets) == 1
        
        # Cleanup with 0 max_age should remove it
        removed = limiter.cleanup(max_age=0)
        
        assert removed == 1
        assert len(limiter._buckets) == 0
