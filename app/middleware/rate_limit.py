"""
Rate Limiting Middleware

Token bucket rate limiter for API endpoint protection.

Features:
- Per-user rate limiting based on IP or user ID
- Configurable limits per endpoint
- Automatic bucket refill
"""

import time
from typing import Dict, Optional, Callable
from dataclasses import dataclass, field
from functools import wraps

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


# ============== Token Bucket Implementation ==============

@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    capacity: int          # Maximum tokens
    refill_rate: float     # Tokens per second
    tokens: float = field(default=0, init=False)
    last_refill: float = field(default=0, init=False)
    
    def __post_init__(self):
        self.tokens = float(self.capacity)
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens.
        
        Args:
            tokens: Number of tokens to consume.
            
        Returns:
            True if tokens were available, False otherwise.
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        self.tokens = min(
            self.capacity,
            self.tokens + (elapsed * self.refill_rate)
        )
        self.last_refill = now


# ============== Rate Limiter ==============

class RateLimiter:
    """
    Per-user rate limiter using token bucket algorithm.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_capacity: int = 10,
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Sustained rate limit.
            burst_capacity: Maximum burst size.
        """
        self._buckets: Dict[str, TokenBucket] = {}
        self._requests_per_minute = requests_per_minute
        self._burst_capacity = burst_capacity
        self._refill_rate = requests_per_minute / 60.0  # Per second
    
    def _get_key(self, request: Request) -> str:
        """
        Get rate limit key for a request.
        
        Uses user ID if authenticated, otherwise IP address.
        """
        # Check for authenticated user
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def _get_bucket(self, key: str) -> TokenBucket:
        """Get or create bucket for key."""
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(
                capacity=self._burst_capacity,
                refill_rate=self._refill_rate,
            )
        return self._buckets[key]
    
    def is_allowed(self, request: Request) -> bool:
        """
        Check if request is allowed.
        
        Args:
            request: FastAPI request object.
            
        Returns:
            True if allowed, False if rate limited.
        """
        key = self._get_key(request)
        bucket = self._get_bucket(key)
        return bucket.consume()
    
    def cleanup(self, max_age: float = 3600) -> int:
        """
        Remove stale buckets.
        
        Args:
            max_age: Maximum age in seconds for inactive buckets.
            
        Returns:
            Number of buckets removed.
        """
        now = time.time()
        stale_keys = [
            key for key, bucket in self._buckets.items()
            if (now - bucket.last_refill) > max_age
        ]
        
        for key in stale_keys:
            del self._buckets[key]
        
        return len(stale_keys)


# ============== Global Rate Limiters ==============

# Default rate limiter (60 requests/minute)
default_limiter = RateLimiter(requests_per_minute=60, burst_capacity=10)

# AI endpoint limiter (more restrictive: 10 requests/minute)
ai_limiter = RateLimiter(requests_per_minute=10, burst_capacity=3)


# ============== Middleware ==============

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that applies rate limiting to all requests.
    """
    
    def __init__(self, app, limiter: RateLimiter = None):
        super().__init__(app)
        self.limiter = limiter or default_limiter
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        if not self.limiter.is_allowed(request):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"},
            )
        
        return await call_next(request)


# ============== Decorator for Specific Endpoints ==============

def rate_limit(limiter: RateLimiter = None):
    """
    Decorator to apply rate limiting to specific endpoints.
    
    Usage:
        @router.post("/analyze")
        @rate_limit(ai_limiter)
        async def analyze_video(...):
            ...
    """
    limiter = limiter or default_limiter
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or args
            request = kwargs.get("request")
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request and not limiter.is_allowed(request):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": "60"},
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
