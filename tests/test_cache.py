"""
Cache Unit Tests

Tests for TTL cache functionality.
"""

import time
from unittest.mock import patch

import pytest


class TestTTLCache:
    """Tests for the TTL cache implementation."""

    def test_set_and_get(self):
        """Verify basic set and get functionality."""
        from app.core.cache import TTLCache
        
        cache: TTLCache[str] = TTLCache(max_size=10, default_ttl=60)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_returns_none_for_missing_key(self):
        """Verify None is returned for missing keys."""
        from app.core.cache import TTLCache
        
        cache: TTLCache[str] = TTLCache(max_size=10, default_ttl=60)
        
        assert cache.get("missing_key") is None

    def test_expires_after_ttl(self):
        """Verify entries expire after TTL."""
        from app.core.cache import TTLCache
        
        cache: TTLCache[str] = TTLCache(max_size=10, default_ttl=1)
        
        cache.set("key1", "value1", ttl=1)
        
        # Should be available immediately
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        assert cache.get("key1") is None

    def test_lru_eviction(self):
        """Verify LRU eviction when at capacity."""
        from app.core.cache import TTLCache
        
        cache: TTLCache[str] = TTLCache(max_size=3, default_ttl=60)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add key4, should evict key2 (least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"  # Still here
        assert cache.get("key2") is None       # Evicted
        assert cache.get("key3") == "value3"  # Still here
        assert cache.get("key4") == "value4"  # New

    def test_stats_tracking(self):
        """Verify cache statistics are tracked correctly."""
        from app.core.cache import TTLCache
        
        cache: TTLCache[str] = TTLCache(max_size=10, default_ttl=60)
        
        cache.set("key1", "value1")
        
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("missing")  # Miss
        
        stats = cache.stats()
        
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate_percent"] == 66.67

    def test_delete(self):
        """Verify delete removes entries."""
        from app.core.cache import TTLCache
        
        cache: TTLCache[str] = TTLCache(max_size=10, default_ttl=60)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        
        assert cache.delete("missing") is False


class TestCacheHelpers:
    """Tests for cache helper functions."""

    def test_transcript_cache_helpers(self):
        """Verify transcript cache helpers work correctly."""
        from app.core.cache import (
            get_cached_transcript,
            cache_transcript,
            transcript_cache,
        )
        
        # Clear cache for test isolation
        transcript_cache.clear()
        
        # Initially empty
        assert get_cached_transcript("test_video") is None
        
        # Cache a transcript
        cache_transcript("test_video", "This is a test transcript.")
        
        # Should be retrievable
        assert get_cached_transcript("test_video") == "This is a test transcript."

    def test_quiz_cache_helpers(self):
        """Verify quiz cache helpers work correctly."""
        from app.core.cache import (
            get_cached_quiz,
            cache_quiz,
            quiz_cache,
        )
        
        # Clear cache for test isolation
        quiz_cache.clear()
        
        quiz_data = {
            "has_quiz": True,
            "questions": [{"q": "Test?", "options": ["A", "B"]}]
        }
        
        # Initially empty
        assert get_cached_quiz("test_video") is None
        
        # Cache quiz data
        cache_quiz("test_video", quiz_data)
        
        # Should be retrievable
        assert get_cached_quiz("test_video") == quiz_data
