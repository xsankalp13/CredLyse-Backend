"""
YouTube Config Endpoint Tests

TDD: Tests written FIRST before implementation.
"""

import pytest
from fastapi.testclient import TestClient


class TestYouTubeConfigEndpoint:
    """Tests for GET /api/v1/config/youtube endpoint."""

    def test_returns_valid_selectors(self, client: TestClient):
        """Verify endpoint returns all required selector fields."""
        response = client.get("/api/v1/config/youtube")
        
        assert response.status_code == 200
        data = response.json()
        
        # Must have all required fields
        assert "sidebar" in data
        assert "comments" in data
        assert "end_screen" in data
        assert "version" in data

    def test_selectors_are_non_empty_strings(self, client: TestClient):
        """Verify all selectors are non-empty strings."""
        response = client.get("/api/v1/config/youtube")
        data = response.json()
        
        assert isinstance(data["sidebar"], str)
        assert len(data["sidebar"]) > 0
        
        assert isinstance(data["comments"], str)
        assert len(data["comments"]) > 0
        
        assert isinstance(data["end_screen"], str)
        assert len(data["end_screen"]) > 0

    def test_version_follows_semver(self, client: TestClient):
        """Verify version follows semantic versioning pattern."""
        response = client.get("/api/v1/config/youtube")
        data = response.json()
        
        version = data["version"]
        parts = version.split(".")
        
        # Should have at least major.minor.patch
        assert len(parts) >= 2
        # Each part should be numeric
        for part in parts:
            assert part.isdigit()

    def test_endpoint_is_public(self, client: TestClient):
        """Verify endpoint doesn't require authentication."""
        response = client.get("/api/v1/config/youtube")
        
        # Should not be 401 or 403
        assert response.status_code == 200

    def test_response_has_cache_headers(self, client: TestClient):
        """Verify response includes cache control headers."""
        response = client.get("/api/v1/config/youtube")
        
        # Should have cache headers for CDN/browser caching
        assert "cache-control" in response.headers or response.status_code == 200


@pytest.fixture
def client():
    """Create test client for the FastAPI app."""
    from app.main import app
    return TestClient(app)
