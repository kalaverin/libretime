"""
RED TEAM: T205 - Show UPDATE endpoint security tests.

Attack vectors:
- Mass assignment during PATCH/PUT
- ID manipulation
- Update other users' shows
- Partial update bypasses
- Null injection
- Immutable field modification
"""

import pytest

from model_bakery import baker


@pytest.mark.django_db
class TestShowUpdateMassAssignment:
    """Mass assignment attacks on UPDATE."""

    def test_patch_id_field(self, admin_client, admin_user):
        """Try to change id via PATCH."""
        show = baker.make("schedule.Show", name="Test Show")
        original_id = show.id

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            {"id": 99999},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("id") != original_id:
                pytest.fail("BUG: Can change id via PATCH")

    def test_patch_created_at(self, admin_client, admin_user):
        """Try to change created_at via PATCH."""
        show = baker.make("schedule.Show", name="Test Show")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            {"created_at": "2019-01-01T00:00:00Z"},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if "2019" in str(data.get("created_at", "")):
                pytest.fail("BUG: Can modify created_at via PATCH")

    def test_put_with_extra_fields(self, admin_client, admin_user):
        """Try PUT with extra fields."""
        show = baker.make("schedule.Show", name="Test Show")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.put(
            f"/api/v2/shows/{show.id}",
            {
                "name": "Updated Show",
                "description": "Updated",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
                "id": 99999,  # Extra field
                "created_at": "2019-01-01T00:00:00Z",  # Extra field
            },
            format="json",
        )

        # Should either reject or ignore extra fields
        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestShowUpdateBOLA:
    """Broken Object Level Authorization on UPDATE."""

    def test_patch_other_user_show(self, host_client, admin_user, regular_user):
        """Try to PATCH another user's show."""
        show = baker.make("schedule.Show", name="Admin Show")

        response = host_client.patch(
            f"/api/v2/shows/{show.id}",
            {"name": "Hacked Show"},
            format="json",
        )

        # Should be denied (not host of this show)
        assert response.status_code in [403, 404]

    def test_put_other_user_show(self, host_client, admin_user, regular_user):
        """Try to PUT another user's show."""
        show = baker.make("schedule.Show", name="Admin Show")

        response = host_client.put(
            f"/api/v2/shows/{show.id}",
            {
                "name": "Hacked Show",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        # Should be denied (not host of this show)
        assert response.status_code in [403, 404]

    def test_delete_other_user_show(
        self,
        host_client,
        admin_user,
        regular_user,
    ):
        """Try to DELETE another user's show."""
        show = baker.make("schedule.Show", name="Admin Show")

        response = host_client.delete(f"/api/v2/shows/{show.id}")

        # Should be denied (not host of this show)
        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestShowUpdateValidationBypass:
    """Validation bypass attacks."""

    def test_patch_to_empty_name(self, admin_client, admin_user):
        """Try to PATCH name to empty string."""
        show = baker.make("schedule.Show", name="Test Show")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            {"name": ""},
            format="json",
        )

        # Should reject empty name
        if response.status_code == 200:
            data = response.json()
            if data.get("name") == "":
                pytest.fail("BUG: Can set empty name via PATCH")

    def test_patch_to_whitespace_name(self, admin_client, admin_user):
        """Try to PATCH name to whitespace only."""
        show = baker.make("schedule.Show", name="Test Show")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            {"name": "   "},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("name") == "   ":
                pytest.fail("BUG: Can set whitespace-only name via PATCH")

    def test_patch_to_null_name(self, admin_client, admin_user):
        """Try to PATCH name to null."""
        show = baker.make("schedule.Show", name="Test Show")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            {"name": None},
            format="json",
        )

        # Should reject null name
        if response.status_code == 200:
            pytest.fail("BUG: Can set null name via PATCH")

    def test_patch_to_very_long_name(self, admin_client, admin_user):
        """Try to PATCH name to very long string."""
        show = baker.make("schedule.Show", name="Test Show")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            {"name": "A" * 1000},
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestShowUpdateURLAttacks:
    """URL field attacks via PATCH."""

    def test_patch_url_to_javascript(self, admin_client, admin_user):
        """Try to PATCH URL to javascript protocol."""
        show = baker.make(
            "schedule.Show",
            name="Test Show",
            url="https://example.com",
        )

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            {"url": "javascript:alert('xss')"},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if "javascript:" in str(data.get("url", "")):
                pytest.fail("BUG: Can set javascript: URL via PATCH")

    def test_patch_url_to_data_protocol(self, admin_client, admin_user):
        """Try to PATCH URL to data protocol."""
        show = baker.make(
            "schedule.Show",
            name="Test Show",
            url="https://example.com",
        )

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            {"url": "data:text/html,<script>alert('xss')</script>"},
            format="json",
        )

        if response.status_code == 200:
            pytest.fail("BUG: Can set data: URL via PATCH")


@pytest.mark.django_db
class TestShowUpdateDescriptionXSS:
    """Description XSS via PATCH."""

    def test_patch_description_with_script(self, admin_client, admin_user):
        """Try to PATCH description with script tag."""
        show = baker.make("schedule.Show", name="Test Show")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            {"description": "<script>alert('xss')</script>"},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if "<script>" in str(data.get("description", "")):
                pytest.fail("BUG: Can inject script via description PATCH")

    def test_patch_description_with_event_handler(
        self,
        admin_client,
        admin_user,
    ):
        """Try to PATCH description with event handler."""
        show = baker.make("schedule.Show", name="Test Show")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            {"description": "<img src=x onerror=alert('xss')>"},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if "onerror=" in str(data.get("description", "")):
                pytest.fail("BUG: Can inject event handler via PATCH")


@pytest.mark.django_db
class TestShowUpdateBusinessLogic:
    """Business logic bypass attacks."""

    def test_patch_without_auth(self, anonymous_client):
        """Try to PATCH without authentication - should be blocked."""
        show = baker.make("schedule.Show", name="Test Show")

        response = anonymous_client.patch(
            f"/api/v2/shows/{show.id}",
            {"name": "Hacked"},
            format="json",
        )

        # Fixed: Should return 403 Forbidden for anonymous
        assert (
            response.status_code == 403
        ), f"Expected 403, got {response.status_code}"

    def test_put_without_auth(self, anonymous_client):
        """Try to PUT without authentication - should be blocked."""
        show = baker.make("schedule.Show", name="Test Show")

        response = anonymous_client.put(
            f"/api/v2/shows/{show.id}",
            {
                "name": "Hacked Show",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        # Fixed: Should return 403 Forbidden for anonymous
        assert (
            response.status_code == 403
        ), f"Expected 403, got {response.status_code}"

    def test_patch_nonexistent_show(self, admin_client, admin_user):
        """Try to PATCH non-existent show."""
        admin_client.force_authenticate(user=admin_user)
        response = admin_client.patch(
            "/api/v2/shows/99999",
            {"name": "Hacked"},
            format="json",
        )

        assert response.status_code == 404

    def test_empty_body_patch(self, admin_client, admin_user):
        """Try PATCH with empty body."""
        show = baker.make("schedule.Show", name="Test Show")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.patch(
            f"/api/v2/shows/{show.id}",
            {},
            format="json",
        )

        # Should return 200 with unchanged data
        assert response.status_code == 200

    def test_patch_duplicate_name(self, admin_client, admin_user):
        """Try to PATCH name to duplicate of existing show."""
        show1 = baker.make("schedule.Show", name="Existing Show")
        show2 = baker.make("schedule.Show", name="Another Show")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.patch(
            f"/api/v2/shows/{show2.id}",
            {"name": "Existing Show"},
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [200, 400]
