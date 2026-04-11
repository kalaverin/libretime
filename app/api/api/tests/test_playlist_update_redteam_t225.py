"""
RED TEAM: T225 - Playlists UPDATE endpoint security tests.

Attack vectors:
- Anonymous UPDATE (authentication bypass)
- BOLA: update other users' playlists
- Mass assignment: id, created_at modification
- XSS in name/description via PATCH
- SQL injection
- Transfer ownership
"""

import json

import pytest

from model_bakery import baker

from api.schedule.models import Playlist


@pytest.mark.django_db(transaction=True)
class TestPlaylistUpdateAuthentication:
    """UPDATE authentication tests."""

    @pytest.mark.xfail(reason="T417: Anonymous UPDATE playlist allowed")
    def test_update_without_auth(self, api_client):
        """Anonymous PATCH should fail."""
        user = baker.make("core.User")
        playlist = baker.make(Playlist, name="Original", owner=user)

        data = {"name": "Hacked"}
        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can update playlists"

    @pytest.mark.xfail(reason="T417: Anonymous PUT playlist allowed")
    def test_put_without_auth(self, api_client):
        """Anonymous PUT should fail."""
        user = baker.make("core.User")
        playlist = baker.make(Playlist, name="Original", owner=user)

        data = {"name": "Hacked", "owner": user.id}
        response = api_client.put(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can PUT playlists"


@pytest.mark.django_db(transaction=True)
class TestPlaylistUpdateBOLA:
    """UPDATE BOLA tests."""

    @pytest.mark.xfail(reason="T412: No owner filtering")
    def test_update_other_user_playlist(
        self,
        api_client,
        regular_user,
        admin_user,
    ):
        """Update another user's playlist."""
        playlist = baker.make(
            Playlist,
            name="Admin Playlist",
            owner=admin_user,
        )

        api_client.force_authenticate(user=regular_user)
        data = {"name": "Hacked by attacker"}
        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            403,
            404,
        ], "Can update other user's playlist (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestPlaylistUpdateMassAssignment:
    """UPDATE mass assignment tests."""

    def test_update_id_field(self, api_client):
        """Try to change id via PATCH."""
        user = baker.make("core.User")
        playlist = baker.make(Playlist, name="Test", owner=user)
        api_client.force_authenticate(user=user)

        original_id = playlist.id
        data = {"id": 99999}
        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(data),
            content_type="application/json",
        )

        playlist.refresh_from_db()
        assert playlist.id == original_id, "ID was changed via mass assignment"

    @pytest.mark.xfail(reason="T419: created_at mutable via PATCH")
    def test_update_created_at(self, api_client):
        """Try to change created_at via PATCH."""
        user = baker.make("core.User")
        playlist = baker.make(Playlist, name="Test", owner=user)
        api_client.force_authenticate(user=user)

        data = {"created_at": "2020-01-01T00:00:00Z"}
        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            result = response.json()
            assert not result.get("created_at", "").startswith(
                "2020",
            ), "created_at was changed via mass assignment"


@pytest.mark.django_db(transaction=True)
class TestPlaylistUpdateOwnershipTransfer:
    """Ownership transfer tests."""

    @pytest.mark.xfail(reason="T418: Ownership transfer allowed")
    def test_transfer_ownership_via_patch(
        self,
        api_client,
        regular_user,
        admin_user,
    ):
        """Try to transfer ownership via PATCH."""
        playlist = baker.make(Playlist, name="Test", owner=regular_user)

        api_client.force_authenticate(user=regular_user)
        data = {"owner": admin_user.id}
        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            result = response.json()
            assert (
                result.get("owner") != admin_user.id
            ), "Can transfer ownership via PATCH (BOLA)"

    @pytest.mark.xfail(reason="T418: Ownership transfer allowed")
    def test_transfer_ownership_via_put(
        self,
        api_client,
        regular_user,
        admin_user,
    ):
        """Try to transfer ownership via PUT."""
        playlist = baker.make(Playlist, name="Test", owner=regular_user)

        api_client.force_authenticate(user=regular_user)
        data = {"name": "Test", "description": "Test", "owner": admin_user.id}
        response = api_client.put(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            result = response.json()
            assert (
                result.get("owner") != admin_user.id
            ), "Can transfer ownership via PUT (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestPlaylistUpdateXSS:
    """UPDATE XSS injection tests."""

    @pytest.mark.xfail(reason="T416: XSS stored unescaped")
    def test_xss_in_name_via_patch(self, api_client):
        """Try XSS in name via PATCH."""
        user = baker.make("core.User")
        playlist = baker.make(Playlist, name="Original", owner=user)
        api_client.force_authenticate(user=user)

        xss_payload = "<script>alert('XSS')</script>"
        data = {"name": xss_payload}
        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("name") == xss_payload:
                pytest.fail(
                    "BUG: XSS payload stored unescaped in name via PATCH",
                )


@pytest.mark.django_db(transaction=True)
class TestPlaylistUpdateSQLInjection:
    """UPDATE SQL injection tests."""

    def test_sqli_in_name_via_patch(self, api_client):
        """Try SQL injection in name via PATCH."""
        user = baker.make("core.User")
        playlist = baker.make(Playlist, name="Original", owner=user)
        api_client.force_authenticate(user=user)

        sqli_payloads = [
            "'; DROP TABLE cc_playlist;--",
            "' OR '1'='1",
        ]

        for payload in sqli_payloads:
            data = {"name": payload}
            response = api_client.patch(
                f"/api/v2/playlists/{playlist.id}",
                json.dumps(data),
                content_type="application/json",
            )

            if response.status_code == 500:
                pytest.fail(f"BUG: SQLi in PATCH name: {payload}")


@pytest.mark.django_db(transaction=True)
class TestPlaylistUpdateValidation:
    """UPDATE validation tests."""

    def test_update_to_empty_name(self, api_client):
        """Try to update to empty name."""
        user = baker.make("core.User")
        playlist = baker.make(Playlist, name="Original", owner=user)
        api_client.force_authenticate(user=user)

        data = {"name": ""}
        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            pytest.fail("BUG: Empty name accepted via PATCH")

    def test_update_to_whitespace_name(self, api_client):
        """Try to update to whitespace-only name."""
        user = baker.make("core.User")
        playlist = baker.make(Playlist, name="Original", owner=user)
        api_client.force_authenticate(user=user)

        data = {"name": "   "}
        response = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            pytest.fail("BUG: Whitespace-only name accepted via PATCH")
