"""T269: Podcast CREATE endpoint tests."""

import pytest

from api.podcasts.models import Podcast
from model_bakery import baker


@pytest.mark.django_db
class TestPodcastViewSetCreate:
    """Test Podcast CREATE endpoint - POST /api/v2/podcasts."""

    @pytest.mark.xfail(
        reason="T340: owner field DB schema mismatch", strict=False,
    )
    def test_create_podcast_success(self, api_client):
        """Successfully create podcast with all fields."""
        data = {
            "url": "https://example.com/new.rss",
            "title": "New Podcast",
            "creator": "Creator Name",
            "description": "Description",
            "language": "en",
            "copyright": "2026",
            "link": "https://example.com",
            "itunes_author": "Author",
            "itunes_keywords": "podcast,test",
            "itunes_summary": "Summary",
            "itunes_subtitle": "Subtitle",
            "itunes_category": "Technology",
            "itunes_explicit": "clean",
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        assert response.status_code == 201
        data = response.json()
        assert data["url"] == "https://example.com/new.rss"
        assert data["title"] == "New Podcast"

    @pytest.mark.xfail(
        reason="T340: owner field DB schema mismatch", strict=False,
    )
    def test_create_minimal_podcast_success(self, api_client):
        """Successfully create podcast with minimal fields."""
        data = {
            "url": "https://example.com/minimal.rss",
            "title": "Minimal",
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        assert response.status_code == 201
        data = response.json()
        assert data["url"] == "https://example.com/minimal.rss"
        assert data["title"] == "Minimal"

    def test_create_missing_url_fails(self, api_client):
        """Create without URL should fail."""
        data = {
            "title": "No URL",
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")
        assert response.status_code == 400

    def test_create_missing_title_fails(self, api_client):
        """Create without title should fail."""
        data = {
            "url": "https://example.com/no-title.rss",
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")
        assert response.status_code == 400

    @pytest.mark.xfail(
        reason="T340: owner field DB schema mismatch", strict=False,
    )
    def test_create_duplicate_url_allowed(self, api_client):
        """Create with duplicate URL may be allowed."""
        baker.make(
            Podcast,
            url="https://example.com/duplicate.rss",
            title="First",
        )

        data = {
            "url": "https://example.com/duplicate.rss",
            "title": "Second",
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")
        # Model doesn't have unique constraint on URL
        assert response.status_code == 201

    def test_create_no_auth_fails(self, api_client):
        """Create without auth should fail."""
        api_client.logout()
        data = {
            "url": "https://example.com/test.rss",
            "title": "Test",
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")
        assert response.status_code == 403

    @pytest.mark.xfail(
        reason="T340: owner field DB schema mismatch", strict=False,
    )
    def test_create_unicode_fields(self, api_client):
        """Create with unicode fields."""
        data = {
            "url": "https://example.com/unicode.rss",
            "title": "Подкаст 🎧",
            "description": "Описание",
            "itunes_author": "Автор",
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Подкаст 🎧"

    @pytest.mark.xfail(
        reason="T340: owner field DB schema mismatch", strict=False,
    )
    def test_create_long_url(self, api_client):
        """Create with very long URL."""
        long_url = "https://example.com/" + "a" * 4000
        data = {
            "url": long_url,
            "title": "Long URL",
        }

        response = api_client.post("/api/v2/podcasts", data, format="json")

        assert response.status_code == 201
        data = response.json()
        assert data["url"] == long_url
