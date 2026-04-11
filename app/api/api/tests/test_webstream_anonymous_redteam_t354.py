"""
RED TEAM: T354 - Webstream Anonymous Access Security Tests.

Verifies that anonymous (unauthenticated) access to Webstream endpoints is blocked.
This includes testing that auto-populated fields like created_at cannot be
manipulated by anonymous users.
"""

import pytest

from model_bakery import baker

from api.schedule.models import Webstream


@pytest.mark.django_db
class TestWebstreamAnonymousCreate:
    """T354: Verify anonymous cannot CREATE webstreams with timestamp manipulation."""

    def test_anonymous_create_webstream_blocked(self, anonymous_client):
        """Anonymous user cannot create webstreams."""
        data = {
            "name": "Anonymous Stream",
            "url": "http://example.com/stream",
            "length": "01:00:00",
        }
        response = anonymous_client.post(
            "/api/v2/webstreams", data, format="json",
        )

        assert response.status_code in [
            401,
            403,
        ], f"T354 NOT FIXED: Anonymous CREATE returned {response.status_code}, expected 401/403"

    def test_anonymous_create_with_created_at_blocked(self, anonymous_client):
        """Anonymous cannot manipulate created_at during creation."""
        data = {
            "name": "Hacked Stream",
            "url": "http://example.com/stream",
            "length": "01:00:00",
            "created_at": "2019-01-01T00:00:00Z",  # Try to backdate
        }
        response = anonymous_client.post(
            "/api/v2/webstreams", data, format="json",
        )

        assert response.status_code in [
            401,
            403,
        ], f"T354 NOT FIXED: Anonymous CREATE with created_at returned {response.status_code}"

    def test_anonymous_cannot_set_future_created_at(self, anonymous_client):
        """Anonymous cannot set future created_at timestamp."""
        data = {
            "name": "Future Stream",
            "url": "http://example.com/stream",
            "length": "01:00:00",
            "created_at": "2099-12-31T23:59:59Z",  # Future date
        }
        response = anonymous_client.post(
            "/api/v2/webstreams", data, format="json",
        )

        assert response.status_code in [
            401,
            403,
        ], f"T354 NOT FIXED: Anonymous CREATE with future timestamp returned {response.status_code}"


@pytest.mark.django_db
class TestWebstreamAnonymousRetrieve:
    """Verify anonymous RETRIEVE is blocked."""

    def test_anonymous_list_webstreams_blocked(
        self, anonymous_client, admin_user,
    ):
        """Anonymous cannot list webstreams."""
        baker.make(
            Webstream,
            name="Test Stream",
            url="http://test.com/stream",
            owner=admin_user,
        )

        response = anonymous_client.get("/api/v2/webstreams")
        assert response.status_code in [
            401,
            403,
        ], f"T354: Anonymous LIST returned {response.status_code}, expected 401/403"

    def test_anonymous_retrieve_single_blocked(
        self, anonymous_client, admin_user,
    ):
        """Anonymous cannot retrieve individual webstream."""
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://test.com/stream",
            owner=admin_user,
        )

        response = anonymous_client.get(f"/api/v2/webstreams/{stream.id}")
        assert response.status_code in [
            401,
            403,
        ], f"T354: Anonymous RETRIEVE returned {response.status_code}, expected 401/403"


@pytest.mark.django_db
class TestWebstreamAnonymousUpdate:
    """Verify anonymous UPDATE is blocked."""

    def test_anonymous_patch_blocked(self, anonymous_client, admin_user):
        """Anonymous cannot PATCH webstreams."""
        stream = baker.make(
            Webstream,
            name="Original",
            url="http://test.com/stream",
            owner=admin_user,
        )

        response = anonymous_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            {"name": "Hacked"},
            format="json",
        )
        assert response.status_code in [
            401,
            403,
        ], f"T354: Anonymous PATCH returned {response.status_code}, expected 401/403"

    def test_anonymous_patch_created_at_blocked(
        self, anonymous_client, admin_user,
    ):
        """Anonymous cannot manipulate created_at via PATCH."""
        stream = baker.make(
            Webstream,
            name="Test",
            url="http://test.com/stream",
            owner=admin_user,
        )
        original_created = stream.created_at

        response = anonymous_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            {"created_at": "2015-01-01T00:00:00Z"},
            format="json",
        )
        assert response.status_code in [
            401,
            403,
        ], f"T354: Anonymous PATCH created_at returned {response.status_code}, expected 401/403"

        # Verify timestamp was not modified
        stream.refresh_from_db()
        assert (
            stream.created_at == original_created
        ), "T354: created_at was modified by anonymous"


@pytest.mark.django_db
class TestWebstreamAnonymousDelete:
    """Verify anonymous DELETE is blocked."""

    def test_anonymous_delete_blocked(self, anonymous_client, admin_user):
        """Anonymous cannot DELETE webstreams."""
        stream = baker.make(
            Webstream,
            name="To Delete",
            url="http://test.com/stream",
            owner=admin_user,
        )
        stream_id = stream.id

        response = anonymous_client.delete(f"/api/v2/webstreams/{stream_id}")
        assert response.status_code in [
            401,
            403,
        ], f"T354: Anonymous DELETE returned {response.status_code}, expected 401/403"

        # Verify stream still exists
        assert Webstream.objects.filter(
            id=stream_id,
        ).exists(), "T354: Stream was deleted by anonymous"


@pytest.mark.django_db
class TestWebstreamCreatedAtImmutability:
    """Verify created_at cannot be manipulated even by authenticated users."""

    @pytest.mark.xfail(
        reason="T354: created_at is mutable - needs serializer fix",
    )
    def test_authenticated_cannot_modify_created_at(
        self, api_client, admin_user,
    ):
        """Even admin cannot change created_at - currently FAILS (known issue)."""
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://test.com/stream",
            owner=admin_user,
        )
        original_created = stream.created_at

        api_client.force_authenticate(user=admin_user)

        # Try to PATCH created_at
        response = api_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            {"created_at": "2015-01-01T00:00:00Z"},
            format="json",
        )

        # Should reject or ignore
        if response.status_code == 200:
            stream.refresh_from_db()
            # This will fail - documenting the bug
            assert (
                stream.created_at == original_created
            ), "T354: created_at was modified"
        else:
            assert response.status_code in [200, 400]
