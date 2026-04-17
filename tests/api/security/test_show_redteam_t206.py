"""
RED TEAM: T206 - Show DELETE endpoint security tests.

Attack vectors:
- ID enumeration via deletion
- SQL injection in DELETE
- Path traversal
- Delete other users' shows
- Cascade deletion abuse
- Double deletion race condition
"""

import pytest

from model_bakery import baker


@pytest.mark.django_db
class TestShowDeleteIDEnumeration:
    """ID enumeration via DELETE attacks."""

    def test_sequential_delete_enumeration(self, api_client, admin_user):
        """Try to enumerate shows by attempting deletes."""
        api_client.force_authenticate(user=admin_user)

        for i in range(1, 10):
            response = api_client.delete(f"/api/v2/shows/{i}")
            # Should return 404 for non-existent, not reveal existence
            assert response.status_code in [204, 404]

    def test_delete_negative_id(self, api_client, admin_user):
        """Try to delete with negative ID."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.delete("/api/v2/shows/-1")

        assert response.status_code in [404, 400]

    def test_delete_zero_id(self, api_client, admin_user):
        """Try to delete with zero ID."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.delete("/api/v2/shows/0")

        assert response.status_code in [404, 400]

    def test_delete_very_large_id(self, api_client, admin_user):
        """Try to delete with very large ID."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.delete("/api/v2/shows/999999999999999999")

        assert response.status_code in [404, 400]


@pytest.mark.django_db
class TestShowDeleteSQLInjection:
    """SQL injection in DELETE attacks."""

    def test_sql_injection_in_delete_id(self, api_client, admin_user):
        """Try SQL injection in DELETE ID."""
        api_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_show;--",
            "1' OR '1'='1' OR '1'='1",
        ]

        for payload in sqli_payloads:
            response = api_client.delete(f"/api/v2/shows/{payload}")
            if response.status_code == 500:
                pytest.fail(
                    f"BUG: SQL injection in DELETE causes crash: {payload}",
                )
            assert response.status_code in [404, 400]


@pytest.mark.django_db
class TestShowDeletePathTraversal:
    """Path traversal in DELETE attacks."""

    def test_path_traversal_in_delete(self, api_client, admin_user):
        """Try path traversal in DELETE."""
        api_client.force_authenticate(user=admin_user)

        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for path in traversal_paths:
            response = api_client.delete(f"/api/v2/shows/{path}")
            assert response.status_code in [404, 400]


@pytest.mark.django_db
class TestShowDeleteBOLA:
    """Broken Object Level Authorization on DELETE."""

    def test_delete_other_user_show(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to DELETE another user's show."""
        show = baker.make("schedule.Show", name="Admin Show")

        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(f"/api/v2/shows/{show.id}")

        if response.status_code == 204:
            pytest.fail("CRITICAL BUG: Can DELETE other user's show")

    def test_delete_with_related_models(self, api_client, admin_user):
        """Try to delete show with related data."""
        show = baker.make("schedule.Show", name="Test Show")
        # Related models may exist depending on the setup

        api_client.force_authenticate(user=admin_user)
        response = api_client.delete(f"/api/v2/shows/{show.id}")

        assert response.status_code == 204


@pytest.mark.django_db
class TestShowDeleteRaceCondition:
    """Race condition attacks."""

    def test_double_delete(self, api_client, admin_user):
        """Try to delete same show twice."""
        show = baker.make("schedule.Show", name="Test Show")

        api_client.force_authenticate(user=admin_user)

        # First delete
        response1 = api_client.delete(f"/api/v2/shows/{show.id}")
        assert response1.status_code == 204

        # Second delete (should return 404)
        response2 = api_client.delete(f"/api/v2/shows/{show.id}")
        assert response2.status_code == 404

    def test_delete_while_updating(self, api_client, admin_user):
        """Try race condition between DELETE and PATCH."""
        show = baker.make("schedule.Show", name="Test Show")

        api_client.force_authenticate(user=admin_user)

        # Start with both operations (may not actually race in test)
        response_patch = api_client.patch(
            f"/api/v2/shows/{show.id}",
            {"name": "Updated"},
            format="json",
        )
        response_delete = api_client.delete(f"/api/v2/shows/{show.id}")

        # One should succeed, one should fail
        statuses = {response_patch.status_code, response_delete.status_code}
        assert 204 in statuses or 200 in statuses or 404 in statuses


@pytest.mark.django_db
class TestShowDeleteBusinessLogic:
    """Business logic bypass attacks."""

    def test_delete_without_auth(self, anonymous_client):
        """Try to DELETE without authentication - should be blocked."""
        show = baker.make("schedule.Show", name="Test Show")

        response = anonymous_client.delete(f"/api/v2/shows/{show.id}")

        # Fixed: Should return 403 Forbidden for anonymous
        assert (
            response.status_code == 403
        ), f"Expected 403, got {response.status_code}"

    def test_delete_nonexistent_show(self, api_client, admin_user):
        """Try to DELETE non-existent show."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.delete("/api/v2/shows/99999")

        assert response.status_code == 404

    def test_get_after_delete(self, api_client, admin_user):
        """Verify GET returns 404 after DELETE."""
        show = baker.make("schedule.Show", name="Test Show")
        show_id = show.id

        api_client.force_authenticate(user=admin_user)

        # Delete
        delete_response = api_client.delete(f"/api/v2/shows/{show_id}")
        assert delete_response.status_code == 204

        # Verify GET returns 404
        get_response = api_client.get(f"/api/v2/shows/{show_id}")
        assert get_response.status_code == 404

    def test_post_to_delete_endpoint(self, api_client, admin_user):
        """Try POST instead of DELETE."""
        show = baker.make("schedule.Show", name="Test Show")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            f"/api/v2/shows/{show.id}",
            {},
            format="json",
        )

        # Should return 405 Method Not Allowed
        assert response.status_code in [405, 404]

    def test_put_to_delete_endpoint(self, api_client, admin_user):
        """Try PUT instead of DELETE."""
        from api.schedule.models import ShowHost

        show = baker.make("schedule.Show", name="Test Show")
        # Assign admin as host
        baker.make(ShowHost, show=show, user=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.put(
            f"/api/v2/shows/{show.id}",
            {
                "name": "Test",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        # PUT should update, not delete
        assert response.status_code == 200


@pytest.mark.django_db
class TestShowDeleteBulk:
    """Bulk deletion attacks."""

    def test_rapid_deletions(self, api_client, admin_user):
        """Try rapid sequential deletions."""
        shows = [
            baker.make("schedule.Show", name=f"Show {i}") for i in range(5)
        ]

        api_client.force_authenticate(user=admin_user)

        for show in shows:
            response = api_client.delete(f"/api/v2/shows/{show.id}")
            assert response.status_code == 204

    def test_delete_all_shows(self, api_client, admin_user):
        """Try to enumerate and delete all shows."""
        # Create some shows
        shows = [
            baker.make("schedule.Show", name=f"Show {i}") for i in range(3)
        ]

        api_client.force_authenticate(user=admin_user)

        # List shows
        list_response = api_client.get("/api/v2/shows")
        if list_response.status_code == 200:
            data = list_response.json()
            show_ids = [s["id"] for s in data]

            # Delete all
            for show_id in show_ids:
                response = api_client.delete(f"/api/v2/shows/{show_id}")
                assert response.status_code == 204
