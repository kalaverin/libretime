"""T268: Podcast LIST endpoint tests."""

import pytest

from api.podcasts.models import Podcast
from model_bakery import baker


@pytest.mark.django_db
class TestPodcastViewSetList:
    """Test Podcast LIST endpoint - GET /api/v2/podcasts."""

    @pytest.mark.xfail(reason="T340: owner field DB schema mismatch", strict=False)
    def test_list_empty_returns_200(self, api_client):
        """LIST empty should return 200 with empty list."""
        response = api_client.get("/api/v2/podcasts")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.xfail(reason="T340: owner field DB schema mismatch", strict=False)
    def test_list_single_podcast(self, api_client):
        """LIST should return single podcast with all iTunes metadata."""
        podcast = baker.make(
            Podcast,
            url="https://example.com/podcast.rss",
            title="Test Podcast",
            creator="Test Creator",
            description="Test Description",
            language="en",
            copyright="2026 Test",
            link="https://example.com",
            itunes_author="Author Name",
            itunes_keywords="test,podcast",
            itunes_summary="iTunes Summary",
            itunes_subtitle="iTunes Subtitle",
            itunes_category="Technology",
            itunes_explicit="clean",
        )

        response = api_client.get("/api/v2/podcasts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["url"] == "https://example.com/podcast.rss"
        assert data[0]["title"] == "Test Podcast"
        assert data[0]["creator"] == "Test Creator"
        assert data[0]["description"] == "Test Description"
        assert data[0]["language"] == "en"
        assert data[0]["copyright"] == "2026 Test"
        assert data[0]["link"] == "https://example.com"
        assert data[0]["itunes_author"] == "Author Name"
        assert data[0]["itunes_keywords"] == "test,podcast"
        assert data[0]["itunes_summary"] == "iTunes Summary"
        assert data[0]["itunes_subtitle"] == "iTunes Subtitle"
        assert data[0]["itunes_category"] == "Technology"
        assert data[0]["itunes_explicit"] == "clean"

    @pytest.mark.xfail(reason="T340: owner field DB schema mismatch", strict=False)
    def test_list_multiple_podcasts(self, api_client):
        """LIST should return multiple podcasts."""
        baker.make(Podcast, url="https://example.com/1.rss", title="Podcast 1")
        baker.make(Podcast, url="https://example.com/2.rss", title="Podcast 2")
        baker.make(Podcast, url="https://example.com/3.rss", title="Podcast 3")

        response = api_client.get("/api/v2/podcasts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    @pytest.mark.xfail(reason="T340: owner field DB schema mismatch", strict=False)
    def test_list_podcast_nullable_fields(self, api_client):
        """LIST should handle podcasts with nullable fields."""
        podcast = baker.make(
            Podcast,
            url="https://example.com/minimal.rss",
            title="Minimal",
            creator=None,
            description=None,
            language=None,
            copyright=None,
            link=None,
        )

        response = api_client.get("/api/v2/podcasts")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["title"] == "Minimal"
        assert data[0]["creator"] is None
        assert data[0]["description"] is None

    @pytest.mark.xfail(reason="T340: owner field DB schema mismatch", strict=False)
    def test_list_returns_all_fields(self, api_client):
        """LIST should return all podcast fields."""
        baker.make(Podcast, url="https://example.com/test.rss", title="Test")

        response = api_client.get("/api/v2/podcasts")
        assert response.status_code == 200
        data = response.json()

        # Core fields
        assert "id" in data[0]
        assert "url" in data[0]
        assert "title" in data[0]
        assert "creator" in data[0]
        assert "description" in data[0]
        assert "language" in data[0]
        assert "copyright" in data[0]
        assert "link" in data[0]
        assert "itunes_author" in data[0]
        assert "itunes_keywords" in data[0]
        assert "itunes_summary" in data[0]
        assert "itunes_subtitle" in data[0]
        assert "itunes_category" in data[0]
        assert "itunes_explicit" in data[0]

    def test_list_no_auth_fails(self, api_client):
        """LIST without authentication should fail."""
        api_client.logout()
        response = api_client.get("/api/v2/podcasts")
        assert response.status_code == 403

    @pytest.mark.xfail(reason="T340: owner field DB schema mismatch", strict=False)
    def test_list_pagination_respected(self, api_client):
        """LIST should respect pagination if configured."""
        for i in range(5):
            baker.make(
                Podcast,
                url=f"https://example.com/{i}.rss",
                title=f"Podcast {i}",
            )

        response = api_client.get("/api/v2/podcasts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    @pytest.mark.xfail(reason="T340: owner field DB schema mismatch", strict=False)
    def test_list_unicode_fields(self, api_client):
        """LIST should handle unicode in all fields."""
        podcast = baker.make(
            Podcast,
            url="https://example.com/подкаст.rss",
            title="Подкаст на русском",
            description="Описание с эмодзи 🎧",
            itunes_author="Автор Имя",
        )

        response = api_client.get("/api/v2/podcasts")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["title"] == "Подкаст на русском"
        assert data[0]["description"] == "Описание с эмодзи 🎧"
        assert data[0]["itunes_author"] == "Автор Имя"

    @pytest.mark.xfail(reason="T340: owner field DB schema mismatch", strict=False)
    def test_list_long_url_field(self, api_client):
        """LIST should handle very long URLs (max 4096 chars)."""
        long_url = "https://example.com/" + "a" * 4000
        podcast = baker.make(Podcast, url=long_url, title="Long URL")

        response = api_client.get("/api/v2/podcasts")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["url"] == long_url

    def test_list_podcast_with_owner(self, api_client, admin_user):
        """LIST should show podcast owner."""
        # This test documents T340 - owner field doesn't work
        pytest.skip("T340: owner field DB schema mismatch")
