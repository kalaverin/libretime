"""Tests for Webstreams LIST endpoint (T245)."""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Webstream


@pytest.mark.django_db(transaction=True)
class TestWebstreamViewSetList:
    """Test Webstreams LIST endpoint - GET /api/v2/webstreams."""

    def setup_method(self):
        """Clean up before each test."""
        Webstream.objects.all().delete()
        User.objects.filter(username__startswith="testws").delete()

    def test_list_empty_returns_200(self, guest_client):
        """LIST empty should return 200 with empty list."""
        response = guest_client.get("/api/v2/webstreams")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_webstream(self, guest_client):
        """LIST should return single webstream with correct fields."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream.mp3",
            description="Test description",
            owner=user,
        )

        response = guest_client.get("/api/v2/webstreams")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Stream"
        assert data[0]["url"] == "http://example.com/stream.mp3"
        assert data[0]["description"] == "Test description"

    def test_list_multiple_webstreams(self, guest_client):
        """LIST should return multiple webstreams."""
        user = baker.make(User, username="testws_user")
        baker.make(
            Webstream,
            name="Stream 1",
            url="http://example.com/1",
            owner=user,
        )
        baker.make(
            Webstream,
            name="Stream 2",
            url="http://example.com/2",
            owner=user,
        )
        baker.make(
            Webstream,
            name="Stream 3",
            url="http://example.com/3",
            owner=user,
        )

        response = guest_client.get("/api/v2/webstreams")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_list_returns_all_fields(self, guest_client):
        """LIST should return all serializer fields."""
        user = baker.make(User, username="testws_user")
        baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream.mp3",
            description="Description",
            mime="audio/mpeg",
            owner=user,
        )

        response = guest_client.get("/api/v2/webstreams")
        assert response.status_code == 200
        data = response.json()[0]
        expected_fields = {
            "id",
            "name",
            "description",
            "url",
            "length",
            "mime",
            "owner",
            "created_at",
            "updated_at",
            "last_played_at",
        }
        assert set(data.keys()) == expected_fields

    def test_list_no_auth_fails(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/webstreams")
        assert response.status_code == 403

    def test_list_with_mime_type(self, guest_client):
        """LIST should include mime type field."""
        user = baker.make(User, username="testws_user")
        baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream.mp3",
            mime="audio/mpeg",
            owner=user,
        )

        response = guest_client.get("/api/v2/webstreams")
        assert response.status_code == 200
        assert response.json()[0]["mime"] == "audio/mpeg"

    def test_list_unicode_names(self, guest_client):
        """LIST should handle unicode in stream names."""
        user = baker.make(User, username="testws_user")
        baker.make(
            Webstream,
            name="Радио поток 🎵",
            url="http://example.com/stream",
            owner=user,
        )

        response = guest_client.get("/api/v2/webstreams")
        assert response.status_code == 200
        assert response.json()[0]["name"] == "Радио поток 🎵"

    def test_list_long_url(self, guest_client):
        """LIST should handle long URLs."""
        user = baker.make(User, username="testws_user")
        long_url = "http://example.com/" + "a" * 400
        baker.make(Webstream, name="Test", url=long_url, owner=user)

        response = guest_client.get("/api/v2/webstreams")
        assert response.status_code == 200
        assert response.json()[0]["url"] == long_url
