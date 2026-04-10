"""
RED TEAM: T319 - Show live_auth fields security tests.

Attack vectors:
- Live auth credential exposure (password leak)
- Unauthorized live auth modification
- Mass assignment via __all__
- BOLA: modify other users' show auth settings
"""

import pytest

from model_bakery import baker


@pytest.mark.django_db
class TestShowLiveAuthExposure:
    """Live auth credential exposure attacks."""

    def test_password_visible_in_list(self, api_client, admin_user):
        """Check if live_auth_custom_password is visible in list."""
        show = baker.make(
            "schedule.Show",
            name="Test Show",
            live_auth_registered=True,
            live_auth_custom=True,
            live_auth_custom_user="admin",
            live_auth_custom_password="secret123",
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/shows")

        assert response.status_code == 200
        data = response.json()

        for show_data in data:
            if show_data.get("live_auth_custom_password"):
                if show_data["live_auth_custom_password"] == "secret123":
                    pytest.fail(
                        "CRITICAL BUG: Password exposed in LIST response",
                    )

    def test_password_visible_in_detail(self, api_client, admin_user):
        """Check if live_auth_custom_password is visible in detail."""
        show = baker.make(
            "schedule.Show",
            name="Test Show",
            live_auth_registered=True,
            live_auth_custom=True,
            live_auth_custom_user="admin",
            live_auth_custom_password="secret123",
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f"/api/v2/shows{show.id}/")

        assert response.status_code == 200
        data = response.json()

        password = data.get("live_auth_custom_password")
        if password and password == "secret123":
            pytest.fail(
                "CRITICAL BUG: Plaintext password exposed in detail view",
            )

    def test_other_user_password_not_visible(
        self, api_client, admin_user, regular_user,
    ):
        """Verify other users can't see password."""
        show = baker.make(
            "schedule.Show",
            name="Admin Show",
            owner=admin_user,
            live_auth_registered=True,
            live_auth_custom=True,
            live_auth_custom_user="admin",
            live_auth_custom_password="admin_secret",
        )

        # Regular user tries to access show
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/shows{show.id}/")

        if response.status_code == 200:
            data = response.json()
            password = data.get("live_auth_custom_password")
            if password and "admin_secret" in str(password):
                pytest.fail(
                    "CRITICAL BUG: Other user can see plaintext password",
                )


@pytest.mark.django_db
class TestShowLiveAuthModification:
    """Unauthorized live auth modification attacks."""

    def test_other_user_can_modify_live_auth(
        self, api_client, admin_user, regular_user,
    ):
        """Try to modify live auth settings on another user's show."""
        show = baker.make(
            "schedule.Show",
            name="Admin Show",
            live_auth_registered=True,
            live_auth_custom=False,
        )

        # Regular user tries to enable live auth
        api_client.force_authenticate(user=regular_user)
        response = api_client.patch(
            f"/api/v2/shows{show.id}/",
            {
                "live_auth_custom": True,
                "live_auth_custom_user": "hacker",
                "live_auth_custom_password": "hacked123",
            },
            format="json",
        )

        if response.status_code == 200:
            pytest.fail(
                "CRITICAL BUG: Can modify other user's live auth settings",
            )

    def test_disable_live_auth_on_other_show(
        self, api_client, admin_user, regular_user,
    ):
        """Try to disable live auth on another user's show."""
        show = baker.make(
            "schedule.Show",
            name="Admin Show",
            live_auth_registered=True,
            live_auth_custom=True,
            live_auth_custom_user="admin",
            live_auth_custom_password="secret",
        )

        # Regular user tries to disable
        api_client.force_authenticate(user=regular_user)
        response = api_client.patch(
            f"/api/v2/shows{show.id}/",
            {"live_auth_registered": False, "live_auth_custom": False},
            format="json",
        )

        if response.status_code == 200:
            pytest.fail("BUG: Can disable other user's live auth")


@pytest.mark.django_db
class TestShowLiveAuthBOLA:
    """Broken Object Level Authorization for shows."""

    def test_list_shows_only_own(self, api_client, admin_user, regular_user):
        """Verify list returns only user's own shows."""
        admin_show = baker.make(
            "schedule.Show",
            name="Admin Show",
            live_auth_registered=True,
        )
        user_show = baker.make(
            "schedule.Show",
            name="User Show",
            live_auth_registered=True,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/shows")

        assert response.status_code == 200
        data = response.json()

        show_names = [s["name"] for s in data]
        assert "User Show" in show_names

        if "Admin Show" in show_names:
            pytest.fail("CRITICAL BUG: List shows other users' shows (BOLA)")

    def test_access_other_user_show(
        self, api_client, admin_user, regular_user,
    ):
        """Try to access another user's show."""
        show = baker.make(
            "schedule.Show",
            name="Admin Show",
            live_auth_registered=True,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/shows{show.id}/")

        if response.status_code == 200:
            pytest.fail("CRITICAL BUG: Can access other user's show (BOLA)")

    def test_delete_other_user_show(
        self, api_client, admin_user, regular_user,
    ):
        """Try to delete another user's show."""
        show = baker.make(
            "schedule.Show",
            name="Admin Show",
            live_auth_registered=True,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(f"/api/v2/shows{show.id}/")

        if response.status_code == 204:
            pytest.fail("CRITICAL BUG: Can delete other user's show (BOLA)")


@pytest.mark.django_db
class TestShowLiveAuthValidation:
    """Live auth validation bypass attacks."""

    def test_create_with_live_auth_but_no_password(
        self, api_client, admin_user,
    ):
        """Try to create show with live_auth_custom=True but no password."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "live_auth_custom": True,
                "live_auth_custom_user": "admin",
                # No password!
            },
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [201, 400]

    def test_create_with_empty_password(self, api_client, admin_user):
        """Try to create with empty password."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "live_auth_custom": True,
                "live_auth_custom_user": "admin",
                "live_auth_custom_password": "",
            },
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [201, 400]

    def test_create_with_long_password(self, api_client, admin_user):
        """Try to create with very long password."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "live_auth_custom": True,
                "live_auth_custom_user": "admin",
                "live_auth_custom_password": "A" * 1000,
            },
            format="json",
        )

        # Should handle gracefully
        assert response.status_code in [201, 400]

    def test_create_both_auth_types(self, api_client, admin_user):
        """Try to create with both registered and custom auth."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "live_auth_registered": True,
                "live_auth_custom": True,
                "live_auth_custom_user": "admin",
                "live_auth_custom_password": "secret",
            },
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestShowLiveAuthBusinessLogic:
    """Business logic bypasses."""

    def test_create_without_auth(self, api_client):
        """Try to create show without authentication."""
        response = api_client.post(
            "/api/v2/shows",
            {"name": "Anonymous Show"},
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("CRITICAL BUG: Anonymous can create show")

    def test_create_duplicate_name(self, api_client, admin_user):
        """Try to create show with duplicate name."""
        baker.make("schedule.Show", name="Unique Show")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {"name": "Unique Show"},
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [201, 400]
