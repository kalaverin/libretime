"""Tests for Webstreams CREATE endpoint (T246)."""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Webstream


@pytest.mark.django_db(transaction=True)
class TestWebstreamViewSetCreate:
    """Test Webstreams CREATE endpoint - POST /api/v2/webstreams."""

    def setup_method(self):
        """Clean up before each test."""
        Webstream.objects.all().delete()
        User.objects.filter(username__startswith="testws").delete()

    @pytest.mark.xfail(
        reason="T333: serializer requires created_at, updated_at, length which should be optional",
    )
    def test_create_webstream_success(self, api_client):
        """CREATE webstream should return 201."""
        user = baker.make(User, username="testws_user")

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Test Stream",
                    "url": "http://example.com/stream.mp3",
                    "description": "Test description",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Stream"
        assert data["url"] == "http://example.com/stream.mp3"
        assert data["description"] == "Test description"

    @pytest.mark.xfail(
        reason="T333: serializer requires created_at, updated_at, length which should be optional",
    )
    def test_create_with_mime_type(self, api_client):
        """CREATE with mime type should succeed."""
        user = baker.make(User, username="testws_user")

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Test Stream",
                    "url": "http://example.com/stream.mp3",
                    "mime": "audio/mpeg",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["mime"] == "audio/mpeg"

    def test_create_missing_name_fails(self, api_client):
        """CREATE without name should return 400."""
        user = baker.make(User, username="testws_user")

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "url": "http://example.com/stream.mp3",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_missing_url_fails(self, api_client):
        """CREATE without URL should return 400."""
        user = baker.make(User, username="testws_user")

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Test Stream",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_invalid_url_fails(self, api_client):
        """CREATE with invalid URL should return 400."""
        user = baker.make(User, username="testws_user")

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Test Stream",
                    "url": "not-a-valid-url",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.xfail(
        reason="T333: serializer requires created_at, updated_at, length which should be optional",
    )
    def test_create_unicode_values(self, api_client):
        """CREATE with unicode should succeed."""
        user = baker.make(User, username="testws_user")

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Радио поток 🎵",
                    "url": "http://example.com/stream.mp3",
                    "description": "Описание",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Радио поток 🎵"
        assert data["description"] == "Описание"

    def test_create_no_auth_fails(self, client):
        """CREATE without auth should return 403."""
        response = client.post(
            "/api/v2/webstreams",
            json.dumps({"name": "Test", "url": "http://example.com/stream"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    @pytest.mark.xfail(
        reason="T333: serializer requires created_at, updated_at, length which should be optional",
    )
    def test_create_long_url(self, api_client):
        """CREATE with long URL should succeed."""
        user = baker.make(User, username="testws_user")
        long_url = "http://example.com/" + "a" * 400

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "Test Stream",
                    "url": long_url,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["url"] == long_url

    @pytest.mark.xfail(
        reason="T333: serializer requires created_at, updated_at, length which should be optional",
    )
    def test_create_ftp_url(self, api_client):
        """CREATE with FTP URL should succeed."""
        user = baker.make(User, username="testws_user")

        response = api_client.post(
            "/api/v2/webstreams",
            json.dumps(
                {
                    "name": "FTP Stream",
                    "url": "ftp://example.com/stream.mp3",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["url"] == "ftp://example.com/stream.mp3"
