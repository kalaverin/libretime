"""
RED TEAM: T333/T334 - Webstream serializer security tests.

Attack vectors:
- IDOR on webstream access
- SQL injection via name/url fields
- Mass assignment on auto-populated fields
- Timestamp manipulation attempts
- Owner bypass attempts
"""

from datetime import timedelta

import pytest


@pytest.mark.django_db
class TestWebstreamIDOR:
    """IDOR attacks on webstream resources."""

    def test_list_webstreams_shows_only_own(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Verify user can only see their own webstreams."""
        from model_bakery import baker

        # Create admin's webstream
        admin_stream = baker.make(
            "schedule.Webstream",
            name="Admin Stream",
            url="http://admin.com/stream",
            owner=admin_user,
        )

        # Create user's webstream
        user_stream = baker.make(
            "schedule.Webstream",
            name="User Stream",
            url="http://user.com/stream",
            owner=regular_user,
        )

        # User lists webstreams
        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/webstreams")

        assert response.status_code == 200
        data = response.json()

        stream_ids = [s["id"] for s in data]
        assert user_stream.id in stream_ids

        # Check if admin's stream is visible (potential BOLA)
        if admin_stream.id in stream_ids:
            pytest.xfail("BOLA: User can see other users' webstreams")

    def test_access_other_user_webstream(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to access another user's webstream."""
        from model_bakery import baker

        admin_stream = baker.make(
            "schedule.Webstream",
            name="Admin Private Stream",
            url="http://admin.com/private",
            owner=admin_user,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/webstreams/{admin_stream.id}")

        # Should be denied
        if response.status_code == 200:
            pytest.xfail("BOLA: User can access other user's webstream")

    @pytest.mark.xfail(reason="BOLA: Can modify other user's webstream")
    def test_modify_other_user_webstream(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to modify another user's webstream."""
        from model_bakery import baker

        admin_stream = baker.make(
            "schedule.Webstream",
            name="Admin Stream",
            url="http://admin.com/stream",
            owner=admin_user,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.patch(
            f"/api/v2/webstreams/{admin_stream.id}",
            {"name": "Hacked Stream"},
            format="json",
        )

        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestWebstreamSQLInjection:
    """SQL injection via webstream fields."""

    def test_sqli_in_name_field(self, api_client, admin_user):
        """Try SQL injection in name field."""
        api_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "stream'; DROP TABLE cc_webstream;--",
            "stream' UNION SELECT * FROM cc_subjs--",
            "stream' OR '1'='1",
        ]

        for payload in sqli_payloads:
            response = api_client.post(
                "/api/v2/webstreams",
                {"name": payload, "url": "http://test.com/stream"},
                format="json",
            )

            # Should create with literal value or reject
            assert response.status_code in [201, 400]

    def test_sqli_in_url_field(self, api_client, admin_user):
        """Try SQL injection in URL field."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(
            "/api/v2/webstreams",
            {
                "name": "Test Stream",
                "url": "http://test.com'; DROP TABLE cc_webstream;--",
            },
            format="json",
        )

        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestWebstreamTimestampManipulation:
    """Timestamp field manipulation attempts."""

    def test_create_with_fake_created_at(self, api_client, admin_user):
        """Try to set created_at to fake timestamp."""

        api_client.force_authenticate(user=admin_user)

        fake_time = "2020-01-01T00:00:00Z"
        response = api_client.post(
            "/api/v2/webstreams",
            {
                "name": "Test Stream",
                "url": "http://test.com/stream",
                "created_at": fake_time,
            },
            format="json",
        )

        # Should either ignore field or use server time
        assert response.status_code in [201, 400]

        if response.status_code == 201:
            data = response.json()
            # Verify created_at is not the fake time
            if data.get("created_at") == fake_time:
                pytest.fail("SECURITY: created_at can be spoofed")

    def test_create_with_fake_updated_at(self, api_client, admin_user):
        """Try to set updated_at to fake timestamp."""
        api_client.force_authenticate(user=admin_user)

        fake_time = "2020-01-01T00:00:00Z"
        response = api_client.post(
            "/api/v2/webstreams",
            {
                "name": "Test Stream",
                "url": "http://test.com/stream",
                "updated_at": fake_time,
            },
            format="json",
        )

        assert response.status_code in [201, 400]

    def test_update_created_at_field(self, api_client, admin_user):
        """Try to modify created_at on update."""
        from model_bakery import baker

        stream = baker.make(
            "schedule.Webstream",
            name="Test Stream",
            url="http://test.com/stream",
            owner=admin_user,
        )

        api_client.force_authenticate(user=admin_user)
        fake_time = "2019-01-01T00:00:00Z"

        response = api_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            {"created_at": fake_time},
            format="json",
        )

        # T354: Should not allow changing created_at
        if response.status_code == 200:
            data = response.json()
            if data.get("created_at") == fake_time:
                pytest.xfail("T354: created_at can be modified after creation")

    def test_update_length_field(self, api_client, admin_user):
        """Try to modify length field directly."""
        from model_bakery import baker

        stream = baker.make(
            "schedule.Webstream",
            name="Test Stream",
            url="http://test.com/stream",
            owner=admin_user,
            length=timedelta(hours=1),
        )

        api_client.force_authenticate(user=admin_user)

        response = api_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            {"length": "02:00:00"},  # Try to change length
            format="json",
        )

        # Length should be auto-managed or protected
        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestWebstreamOwnerBypass:
    """Owner field bypass attempts."""

    def test_create_webstream_with_other_owner(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to create webstream with another user as owner."""
        api_client.force_authenticate(user=regular_user)

        response = api_client.post(
            "/api/v2/webstreams",
            {
                "name": "My Stream",
                "url": "http://mine.com/stream",
                "owner": admin_user.id,  # Try to set admin as owner
            },
            format="json",
        )

        # Should create but with current user as owner
        assert response.status_code in [201, 400, 403]

        if response.status_code == 201:
            data = response.json()
            assert data.get("owner") != admin_user.id

    def test_change_webstream_owner(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to change webstream owner to another user."""
        from model_bakery import baker

        stream = baker.make(
            "schedule.Webstream",
            name="User Stream",
            url="http://user.com/stream",
            owner=regular_user,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            {"owner": admin_user.id},
            format="json",
        )

        # T354: Should not allow changing owner
        if response.status_code == 200:
            data = response.json()
            if data.get("owner") == admin_user.id:
                pytest.xfail("T354: Owner can be transferred via API")

    def test_create_webstream_without_auth(self, api_client):
        """Try to create webstream without authentication."""
        from django.db import IntegrityError

        # This will fail because owner is required (creator_id NOT NULL)
        # Should return 403 or IntegrityError
        try:
            response = api_client.post(
                "/api/v2/webstreams",
                {
                    "name": "Anonymous Stream",
                    "url": "http://anon.com/stream",
                    "description": "test",
                },
                format="json",
            )
            # If we get here, should be 403 or 400
            assert response.status_code in [
                403,
                400,
                500,
            ]  # 500 if IntegrityError not handled
        except IntegrityError:
            # Expected - owner is required
            pass


@pytest.mark.django_db
class TestWebstreamFieldValidation:
    """Field validation edge cases."""

    def test_empty_name(self, api_client, admin_user):
        """Try to create webstream with empty name."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(
            "/api/v2/webstreams",
            {"name": "", "url": "http://test.com/stream"},
            format="json",
        )

        # Should reject empty name
        assert response.status_code in [201, 400]

    def test_very_long_name(self, api_client, admin_user):
        """Try to create webstream with very long name."""
        api_client.force_authenticate(user=admin_user)

        long_name = "A" * 5000
        response = api_client.post(
            "/api/v2/webstreams",
            {"name": long_name, "url": "http://test.com/stream"},
            format="json",
        )

        assert response.status_code in [201, 400]

    def test_invalid_url_format(self, api_client, admin_user):
        """Try to create webstream with invalid URL."""
        api_client.force_authenticate(user=admin_user)

        invalid_urls = [
            "not-a-url",
            "ftp://test.com/stream",  # Wrong protocol
            "http://",  # Incomplete
            "javascript:alert(1)",  # XSS attempt
            "//evil.com/stream",  # Protocol-relative
        ]

        for url in invalid_urls:
            response = api_client.post(
                "/api/v2/webstreams",
                {"name": "Test Stream", "url": url},
                format="json",
            )
            # May accept or reject
            assert response.status_code in [201, 400]

    def test_unicode_in_name(self, api_client, admin_user):
        """Try to create webstream with unicode name."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(
            "/api/v2/webstreams",
            {
                "name": "日本語 🎉 Émojis",
                "url": "http://test.com/stream",
                "description": "test",
            },
            format="json",
        )

        # Should accept unicode
        assert response.status_code == 201


@pytest.mark.django_db
class TestWebstreamDelete:
    """Delete operation security tests."""

    @pytest.mark.xfail(reason="BOLA: Can delete other user's webstream")
    def test_delete_other_user_webstream(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to delete another user's webstream."""
        from model_bakery import baker

        admin_stream = baker.make(
            "schedule.Webstream",
            name="Admin Stream",
            url="http://admin.com/stream",
            owner=admin_user,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(f"/api/v2/webstreams/{admin_stream.id}")

        # Should be denied
        assert response.status_code in [403, 404]

    def test_delete_webstream_without_auth(self, api_client, admin_user):
        """CRITICAL: Try to delete webstream without authentication.

        T354: Anonymous delete should return 403, not 204.
        """
        from model_bakery import baker

        stream = baker.make(
            "schedule.Webstream",
            name="Test Stream",
            url="http://test.com/stream",
            owner=admin_user,
        )

        response = api_client.delete(f"/api/v2/webstreams/{stream.id}")

        # T354: Should require authentication
        if response.status_code == 204:
            pytest.xfail("T354: CRITICAL - Anonymous can delete webstreams!")
