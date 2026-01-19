"""
YouTube Configuration API

Provides dynamic CSS selectors for the Chrome extension.
This enables "hotfixing" - updating selectors without waiting for
Chrome Web Store approval (48h).

IMPORTANT: Edit youtube_config.json to update selectors instantly.
"""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Response
from pydantic import BaseModel


router = APIRouter(prefix="/config", tags=["Configuration"])


# ============== Pydantic Models ==============

class YouTubeSelectors(BaseModel):
    """
    CSS selectors for YouTube elements to hide in Study Mode.
    
    These are fetched by the Chrome extension and cached locally.
    Update youtube_config.json to change selectors without redeploying.
    
    IMPORTANT: Do NOT hide #secondary itself - the Progress Panel is injected there!
    Extension uses opacity:0 for hiding to preserve layout.
    """
    sidebar: str = "#secondary ytd-watch-next-secondary-results-renderer, #secondary #related, #secondary ytd-compact-video-renderer, #secondary ytd-compact-playlist-renderer, #secondary ytd-compact-radio-renderer"
    comments: str = "#comments, ytd-comments, ytd-comment-thread-renderer"
    end_screen: str = ".ytp-ce-element, .ytp-endscreen-content, .ytp-ce-covering-overlay"
    version: str = "1.2.0"


# ============== Config Loading ==============

# Path to config file (relative to backend root)
CONFIG_FILE = Path(__file__).parent.parent.parent / "youtube_config.json"

# Fallback selectors if file read fails
FALLBACK_SELECTORS = YouTubeSelectors()


def load_config() -> YouTubeSelectors:
    """
    Load selectors from config file.
    
    Reads fresh from file on each request to enable instant updates.
    Falls back to hardcoded values if file is missing or invalid.
    
    Returns:
        YouTubeSelectors with current configuration.
    """
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            
            # Filter out underscore-prefixed keys (comments)
            filtered = {k: v for k, v in data.items() if not k.startswith("_")}
            return YouTubeSelectors(**filtered)
    except Exception as e:
        print(f"[Config] Failed to load youtube_config.json: {e}")
    
    return FALLBACK_SELECTORS


# ============== API Endpoints ==============

@router.get("/youtube", response_model=YouTubeSelectors)
async def get_youtube_selectors(response: Response) -> YouTubeSelectors:
    """
    Get current CSS selectors for YouTube Study Mode.
    
    The extension fetches this on startup and caches for 24 hours.
    To update selectors instantly:
    1. Edit youtube_config.json
    2. Extension will get new selectors on next cache refresh
    
    Returns:
        YouTubeSelectors with sidebar, comments, end_screen, version.
    """
    # Add cache headers (CDN can cache, browser should revalidate)
    response.headers["Cache-Control"] = "public, max-age=300"  # 5 min cache
    
    return load_config()


@router.get("/youtube/version")
async def get_youtube_config_version() -> dict:
    """Get just the version for cache busting checks."""
    config = load_config()
    return {"version": config.version}
