"""
Caching Module

Provides in-memory caching with TTL support for:
- Transcripts (rarely change)
- Quiz results (prevents redundant AI calls)

This is CRITICAL for scalability - without caching, the same video
analyzed multiple times would trigger multiple expensive AI calls.
"""

import time
from typing import Optional, Dict, Any, TypeVar, Generic
from dataclasses import dataclass, field
from collections import OrderedDict


T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """A single cache entry with TTL support."""
    value: T
    expires_at: float
    
    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        return time.time() > self.expires_at


class TTLCache(Generic[T]):
    """
    Thread-safe TTL cache with LRU eviction.
    
    Features:
    - Time-based expiration
    - Maximum size limit with LRU eviction
    - Cache statistics for monitoring
    """
    
    def __init__(
        self, 
        max_size: int = 1000, 
        default_ttl: int = 3600  # 1 hour default
    ):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of entries.
            default_ttl: Default time-to-live in seconds.
        """
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value or None if not found/expired.
        """
        entry = self._cache.get(key)
        
        if entry is None:
            self._misses += 1
            return None
        
        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Optional TTL override in seconds.
        """
        ttl = ttl or self._default_ttl
        expires_at = time.time() + ttl
        
        # Remove oldest entries if at capacity
        while len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
        
        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
        self._cache.move_to_end(key)
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            True if deleted, False if not found.
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with hit/miss counts and hit rate.
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
        }


# ============== Global Cache Instances ==============

# Cache for video transcripts (1 hour TTL, transcripts rarely change)
transcript_cache: TTLCache[Optional[str]] = TTLCache(
    max_size=1000,
    default_ttl=3600  # 1 hour
)

# Cache for quiz results (4 hours TTL, prevent redundant AI calls)
quiz_cache: TTLCache[Dict[str, Any]] = TTLCache(
    max_size=500,
    default_ttl=14400  # 4 hours
)


# ============== Cache Helper Functions ==============

def get_cached_transcript(video_id: str) -> Optional[str]:
    """Get cached transcript for a video."""
    return transcript_cache.get(video_id)


def cache_transcript(video_id: str, transcript: Optional[str]) -> None:
    """Cache a transcript for a video."""
    transcript_cache.set(video_id, transcript)


def get_cached_quiz(video_id: str) -> Optional[Dict[str, Any]]:
    """Get cached quiz data for a video."""
    return quiz_cache.get(video_id)


def cache_quiz(video_id: str, quiz_data: Dict[str, Any]) -> None:
    """Cache quiz data for a video."""
    quiz_cache.set(video_id, quiz_data)


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches."""
    return {
        "transcript_cache": transcript_cache.stats(),
        "quiz_cache": quiz_cache.stats(),
    }
