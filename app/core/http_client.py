"""
HTTP Client Module

Provides a globally shared, high-performance httpx.AsyncClient with:
- Connection pooling for efficient reuse
- Automatic retries with exponential backoff
- Configurable timeouts

This is CRITICAL for scalability - creating a new client per request is
extremely inefficient and leads to connection exhaustion under load.
"""

import asyncio
from typing import Optional, Any

import httpx


# ============== Configuration ==============

# Connection pool limits
MAX_CONNECTIONS = 100
MAX_KEEPALIVE_CONNECTIONS = 20
KEEPALIVE_EXPIRY = 30  # seconds

# Timeout configuration
DEFAULT_TIMEOUT = 30.0  # seconds then

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 0.5  # seconds


# ============== Global Client Instance ==============

_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    """
    Get or create the global async HTTP client.
    
    Uses connection pooling for efficient request handling at scale.
    The client should be reused across all requests.
    
    Returns:
        httpx.AsyncClient: Shared client instance.
    """
    global _http_client
    if _http_client is None:
        limits = httpx.Limits(
            max_connections=MAX_CONNECTIONS,
            max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,
            keepalive_expiry=KEEPALIVE_EXPIRY,
        )
        timeout = httpx.Timeout(DEFAULT_TIMEOUT)
        
        _http_client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            http2=True,  # Enable HTTP/2 for better performance
        )
    return _http_client


async def close_http_client() -> None:
    """
    Close the global HTTP client.
    
    Should be called during application shutdown.
    """
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


# ============== Request Helpers with Retry ==============

async def request_with_retry(
    method: str,
    url: str,
    max_retries: int = MAX_RETRIES,
    **kwargs: Any,
) -> httpx.Response:
    """
    Make an HTTP request with automatic retry on failure.
    
    Uses exponential backoff between retries.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        max_retries: Maximum number of retry attempts
        **kwargs: Additional arguments passed to httpx request
        
    Returns:
        httpx.Response: The response object
        
    Raises:
        httpx.HTTPError: If all retries fail
    """
    client = get_http_client()
    last_exception: Optional[Exception] = None
    
    for attempt in range(max_retries + 1):
        try:
            response = await client.request(method, url, **kwargs)
            
            # Retry on 5xx server errors
            if response.status_code >= 500:
                if attempt < max_retries:
                    wait_time = RETRY_BACKOFF_BASE * (2 ** attempt)
                    print(f"[HTTP] Server error {response.status_code}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
            
            return response
            
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = RETRY_BACKOFF_BASE * (2 ** attempt)
                print(f"[HTTP] Connection error, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
            else:
                raise
    
    if last_exception:
        raise last_exception
    raise httpx.HTTPError(f"Request to {url} failed after {max_retries} retries")


async def get_with_retry(url: str, **kwargs: Any) -> httpx.Response:
    """Convenience wrapper for GET requests with retry."""
    return await request_with_retry("GET", url, **kwargs)


async def post_with_retry(url: str, **kwargs: Any) -> httpx.Response:
    """Convenience wrapper for POST requests with retry."""
    return await request_with_retry("POST", url, **kwargs)
