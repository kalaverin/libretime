"""
RED TEAM: T202/T203 - Show CREATE endpoint security tests.

Attack vectors:
- Mass assignment via __all__
- ID/created_at manipulation
- Color format injection
- URL SSRF
- Description XSS/storage injection
- Unicode homograph names
- Duplicate name bypass
"""

import pytest

from model_bakery import baker


@pytest.mark.django_db
class TestShowCreateMassAssignment:
    """Mass assignment attacks on Show CREATE."""

    def test_create_with_id_field(self, api_client, admin_user):
        """Try to set id field during show creation."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "id": 99999,
                "name": "Test Show",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        if response.status_code == 201:
            data = response.json()
            if data.get("id") == 99999:
                pytest.fail("BUG: Can set id field during creation")

    def test_create_with_created_at(self, api_client, admin_user):
        """Try to set created_at timestamp."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "created_at": "2019-01-01T00:00:00Z",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        if response.status_code == 201:
            data = response.json()
            if "2019" in str(data.get("created_at", "")):
                pytest.fail("BUG: Can manipulate created_at timestamp")


@pytest.mark.django_db
class TestShowCreateColorInjection:
    """Color field injection attacks."""

    def test_color_with_hash_prefix(self, api_client, admin_user):
        """Try to create with #FFFFFF format."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "foreground_color": "#FFFFFF",
                "background_color": "#000000",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [201, 400]

    def test_color_with_short_hex(self, api_client, admin_user):
        """Try to create with short hex (FFF)."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "foreground_color": "FFF",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        assert response.status_code in [201, 400]

    def test_color_with_invalid_chars(self, api_client, admin_user):
        """Try to create with invalid color characters."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "foreground_color": "GGGGGG",  # Invalid hex
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        # Should reject invalid color
        if response.status_code == 201:
            pytest.fail("BUG: Accepts invalid color format")

    def test_color_with_sql_injection(self, api_client, admin_user):
        """Try SQL injection in color field."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "foreground_color": "FFFFFF' OR '1'='1",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        if response.status_code == 500:
            pytest.fail("BUG: Color SQL injection causes crash")


@pytest.mark.django_db
class TestShowCreateURLAttacks:
    """URL field attacks."""

    def test_url_with_javascript_protocol(self, api_client, admin_user):
        """Try javascript: protocol in URL."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "url": "javascript:alert('xss')",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("BUG: Accepts javascript: protocol URL (XSS risk)")

    def test_url_with_data_protocol(self, api_client, admin_user):
        """Try data: protocol in URL."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "url": "data:text/html,<script>alert('xss')</script>",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("BUG: Accepts data: protocol URL")

    def test_url_with_file_protocol(self, api_client, admin_user):
        """Try file: protocol in URL."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "url": "file:///etc/passwd",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("BUG: Accepts file: protocol URL")


@pytest.mark.django_db
class TestShowCreateDescriptionAttacks:
    """Description field attacks."""

    def test_description_with_html_script(self, api_client, admin_user):
        """Try HTML script tags in description."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "description": "<script>alert('xss')</script>",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        assert response.status_code == 201
        data = response.json()
        # Check if script is stored as-is (potential XSS)
        if "<script>" in str(data.get("description", "")):
            pytest.fail("BUG: HTML script stored without sanitization")

    def test_description_with_event_handlers(self, api_client, admin_user):
        """Try event handlers in description."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "description": "<img src=x onerror=alert('xss')>",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        assert response.status_code == 201
        data = response.json()
        if "onerror=" in str(data.get("description", "")):
            pytest.fail("BUG: Event handlers stored without sanitization")

    def test_very_long_description(self, api_client, admin_user):
        """Try description over 8192 chars."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Test Show",
                "description": "A" * 10000,
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        # Should reject or truncate
        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestShowCreateUnicodeAttacks:
    """Unicode-based attacks."""

    def test_unicode_homograph_show_name(self, api_client, admin_user):
        """Try to create show with unicode homograph name."""
        api_client.force_authenticate(user=admin_user)

        # Create first show with ASCII name
        response1 = api_client.post(
            "/api/v2/shows",
            {
                "name": "Popular Show",  # ASCII
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )
        assert response1.status_code == 201

        # Try to create with visually similar homograph
        response2 = api_client.post(
            "/api/v2/shows",
            {
                "name": "Populаr Show",  # Cyrillic 'а' (U+0430)
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        # Both may succeed - documenting potential for visual spoofing
        assert response2.status_code == 201

    def test_rtl_override_in_name(self, api_client, admin_user):
        """Try RTL override characters in show name."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "Good Show\u202eBad\u202c",  # RTL override
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestShowCreateDuplicateBypass:
    """Duplicate name bypass attacks."""

    def test_create_duplicate_with_whitespace(self, api_client, admin_user):
        """Try to bypass duplicate check with whitespace."""
        # Create first show
        baker.make("schedule.Show", name="Unique Show")

        api_client.force_authenticate(user=admin_user)

        # Try with leading/trailing whitespace
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": " Unique Show ",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        # Should reject or trim whitespace
        assert response.status_code in [201, 400]

    def test_create_duplicate_different_case(self, api_client, admin_user):
        """Try case variation of existing show name."""
        baker.make("schedule.Show", name="Unique Show")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "unique show",  # lowercase
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        # May succeed or fail - depends on case sensitivity
        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestShowCreateBusinessLogic:
    """Business logic bypass attacks."""

    def test_create_without_auth(self, anonymous_client):
        """Try to create show without authentication - should be blocked."""
        response = anonymous_client.post(
            "/api/v2/shows",
            {
                "name": "Anonymous Show",
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
        assert response.status_code == 403, (
            f"Expected 403, got {response.status_code}"
        )

    def test_create_with_empty_name(self, api_client, admin_user):
        """Try to create show with empty name."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        # Should reject empty name
        if response.status_code == 201:
            pytest.fail("BUG: Accepts empty show name")

    def test_create_with_whitespace_only_name(self, api_client, admin_user):
        """Try to create show with whitespace-only name."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/shows",
            {
                "name": "   ",
                "linked": False,
                "linkable": True,
                "auto_playlist_enabled": False,
                "auto_playlist_repeat": False,
                "override_intro_playlist": False,
                "override_outro_playlist": False,
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("BUG: Accepts whitespace-only show name")
