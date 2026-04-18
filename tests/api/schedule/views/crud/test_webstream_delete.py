"""Tests for Webstreams DELETE endpoint (T248)."""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Webstream


@pytest.mark.django_db(transaction=True)
class TestWebstreamViewSetDelete:
    """Test Webstreams DELETE endpoint - DELETE /api/v2/webstreams/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        Webstream.objects.all().delete()
        User.objects.filter(username__startswith="testws").delete()

    def test_delete_webstream_success_returns_204(self, admin_client):
        """DELETE should return 204 on success."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        response = admin_client.delete(f"/api/v2/webstreams/{stream.id}")
        assert response.status_code == 204

    def test_delete_webstream_removes_from_db(self, admin_client):
        """DELETE should remove webstream from database."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        admin_client.delete(f"/api/v2/webstreams/{stream.id}")
        assert Webstream.objects.filter(id=stream.id).count() == 0

    def test_delete_not_found_returns_404(self, admin_client):
        """DELETE non-existent webstream should return 404."""
        response = admin_client.delete("/api/v2/webstreams/999999")
        assert response.status_code == 404

    def test_delete_no_auth_fails(self, client):
        """DELETE without auth should return 403."""
        response = client.delete("/api/v2/webstreams/1")
        assert response.status_code == 403

    def test_delete_double_delete_returns_404(self, admin_client):
        """DELETE already deleted webstream should return 404."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        admin_client.delete(f"/api/v2/webstreams/{stream.id}")
        response = admin_client.delete(f"/api/v2/webstreams/{stream.id}")
        assert response.status_code == 404

    def test_delete_returns_empty_body(self, admin_client):
        """DELETE should return empty response body."""
        user = baker.make(User, username="testws_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        response = admin_client.delete(f"/api/v2/webstreams/{stream.id}")
        assert response.content == b""

    def test_delete_one_webstream_others_remain(self, admin_client):
        """DELETE one webstream should leave others."""
        user = baker.make(User, username="testws_user")
        stream1 = baker.make(
            Webstream,
            name="Stream 1",
            url="http://example.com/1",
            owner=user,
        )
        stream2 = baker.make(
            Webstream,
            name="Stream 2",
            url="http://example.com/2",
            owner=user,
        )
        stream3 = baker.make(
            Webstream,
            name="Stream 3",
            url="http://example.com/3",
            owner=user,
        )

        admin_client.delete(f"/api/v2/webstreams/{stream2.id}")

        assert Webstream.objects.filter(id=stream1.id).exists()
        assert not Webstream.objects.filter(id=stream2.id).exists()
        assert Webstream.objects.filter(id=stream3.id).exists()

    def test_delete_id_zero_returns_404(self, admin_client):
        """DELETE with id=0 should return 404."""
        response = admin_client.delete("/api/v2/webstreams/0")
        assert response.status_code == 404

    def test_delete_negative_id_returns_404(self, admin_client):
        """DELETE with negative id should return 404."""
        response = admin_client.delete("/api/v2/webstreams/-1")
        assert response.status_code == 404

    def test_delete_sql_injection_attempt(self, admin_client):
        """DELETE with SQL injection in id should be handled safely."""
        response = admin_client.delete("/api/v2/webstreams/1 OR 1=1")
        assert response.status_code == 404
