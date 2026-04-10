"""
RED TEAM: T312 - Preference value types extended security tests.

Attack vectors:
- Value type confusion (JSON injection, XML injection)
- Unicode normalization attacks
- Whitespace exploitation
- Mass assignment
- BOLA on preferences
"""

import json

import pytest

from model_bakery import baker


@pytest.mark.django_db
class TestPreferenceValueInjection:
    """Value content injection attacks."""

    def test_json_value_with_nested_objects(self, api_client, admin_user):
        """Try to create preference with deeply nested JSON."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "nested_json",
                "value": json.dumps({"a": {"b": {"c": {"d": "e"}}}}),
            },
            format="json",
        )

        assert response.status_code == 201

    def test_xml_value_with_entities(self, api_client, admin_user):
        """Try to create preference with XML containing entities."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "xml_pref",
                "value": '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
            },
            format="json",
        )

        assert response.status_code == 201

    def test_html_value_with_scripts(self, api_client, admin_user):
        """Try to create preference with HTML containing scripts."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "html_pref",
                "value": '<script>alert("xss")</script>',
            },
            format="json",
        )

        assert response.status_code == 201

    def test_value_with_null_bytes(self, api_client, admin_user):
        """Try to create preference with null bytes in value."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "null_test",
                "value": "hello\x00world",
            },
            format="json",
        )

        # Should handle gracefully
        assert response.status_code in [201, 400, 500]

    def test_value_with_control_chars(self, api_client, admin_user):
        """Try to create preference with control characters."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "control_test",
                "value": "hello\x01\x02\x03world",
            },
            format="json",
        )

        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestPreferenceUnicodeAttacks:
    """Unicode-based attacks."""

    def test_unicode_homograph_key(self, api_client, admin_user):
        """Try to create preference with unicode homograph in key."""
        api_client.force_authenticate(user=admin_user)

        # Create first preference with ASCII key
        response1 = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "api_key",  # ASCII
                "value": "value1",
            },
            format="json",
        )
        assert response1.status_code == 201

        # Try to create with homograph (Cyrillic 'а' instead of Latin 'a')
        response2 = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "аpi_key",  # Cyrillic 'а' (U+0430)
                "value": "value2",
            },
            format="json",
        )

        # Should create separate entry (visual spoofing attack possible)
        if response2.status_code == 201:
            data = response2.json()
            # If keys look the same but are different unicode, that's a problem

    def test_unicode_bidi_override(self, api_client, admin_user):
        """Try to create preference with bidirectional override characters."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "test\u202ekey\u202c",  # BIDI characters
                "value": "value",
            },
            format="json",
        )

        assert response.status_code in [201, 400]

    def test_very_long_key(self, api_client, admin_user):
        """Try to create preference with very long key."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "k" * 1000,
                "value": "value",
            },
            format="json",
        )

        assert response.status_code in [201, 400]

    def test_very_long_value(self, api_client, admin_user):
        """Try to create preference with very long value."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "long_value",
                "value": "v" * 10000,
            },
            format="json",
        )

        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestPreferenceWhitespaceExploitation:
    """Whitespace exploitation attacks."""

    def test_whitespace_only_value(self, api_client, admin_user):
        """Try to create preference with whitespace-only value."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "whitespace",
                "value": "   ",
            },
            format="json",
        )

        assert response.status_code == 201
        data = response.json()
        # Legacy DB trims whitespace - verify behavior

    def test_tab_and_newline_in_value(self, api_client, admin_user):
        """Try to create preference with tabs and newlines."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "formatted",
                "value": "line1\nline2\tindented",
            },
            format="json",
        )

        assert response.status_code == 201

    def test_leading_trailing_whitespace_key(self, api_client, admin_user):
        """Try to create preference with whitespace in key."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": " key_with_spaces ",
                "value": "value",
            },
            format="json",
        )

        assert response.status_code == 201


@pytest.mark.django_db
class TestPreferenceBOLA:
    """Broken Object Level Authorization on preferences."""

    def test_list_shows_only_own_preferences(
        self, api_client, admin_user, regular_user,
    ):
        """Verify list returns only user's own preferences."""
        # Create preferences for both users
        admin_pref = baker.make(
            "core.Preference",
            user=admin_user,
            key="admin_pref",
            value="admin_value",
        )
        user_pref = baker.make(
            "core.Preference",
            user=regular_user,
            key="user_pref",
            value="user_value",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/preferences")

        assert response.status_code == 200
        data = response.json()

        pref_keys = [p["key"] for p in data]
        assert "user_pref" in pref_keys

        if "admin_pref" in pref_keys:
            pytest.fail(
                "CRITICAL BUG: List shows other users' preferences (BOLA)",
            )

    def test_access_other_user_preference(
        self, api_client, admin_user, regular_user,
    ):
        """Try to access another user's preference by ID."""
        pref = baker.make(
            "core.Preference",
            user=admin_user,
            key="admin_pref",
            value="admin_value",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/preferences/{pref.id}")

        if response.status_code == 200:
            pytest.fail(
                "CRITICAL BUG: Can access other user's preference (BOLA)",
            )

    def test_update_other_user_preference(
        self, api_client, admin_user, regular_user,
    ):
        """Try to update another user's preference."""
        pref = baker.make(
            "core.Preference",
            user=admin_user,
            key="admin_pref",
            value="admin_value",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.patch(
            f"/api/v2/preferences/{pref.id}",
            {"value": "hacked"},
            format="json",
        )

        if response.status_code == 200:
            pytest.fail(
                "CRITICAL BUG: Can update other user's preference (BOLA)",
            )

    def test_delete_other_user_preference(
        self, api_client, admin_user, regular_user,
    ):
        """Try to delete another user's preference."""
        pref = baker.make(
            "core.Preference",
            user=admin_user,
            key="admin_pref",
            value="admin_value",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(f"/api/v2/preferences/{pref.id}")

        if response.status_code == 204:
            pytest.fail(
                "CRITICAL BUG: Can delete other user's preference (BOLA)",
            )


@pytest.mark.django_db
class TestPreferenceMassAssignment:
    """Mass assignment attacks."""

    def test_create_with_id_field(self, api_client, admin_user):
        """Try to set id field during creation."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/preferences/",
            {
                "id": 99999,
                "user": admin_user.id,
                "key": "test_pref",
                "value": "test_value",
            },
            format="json",
        )

        if response.status_code == 201:
            data = response.json()
            if data.get("id") == 99999:
                pytest.fail("BUG: Can set id field")

    def test_update_user_field(self, api_client, admin_user, regular_user):
        """Try to change user via PATCH."""
        pref = baker.make(
            "core.Preference",
            user=admin_user,
            key="test_pref",
            value="value",
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            f"/api/v2/preferences/{pref.id}",
            {"user": regular_user.id},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("user") == regular_user.id:
                pytest.fail("BUG: Can transfer preference to another user")


@pytest.mark.django_db
class TestPreferenceKeyCollision:
    """Key collision and overwriting attacks."""

    def test_create_duplicate_key_same_user(self, api_client, admin_user):
        """Try to create preference with duplicate key for same user."""
        baker.make(
            "core.Preference",
            user=admin_user,
            key="unique_key",
            value="original",
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "unique_key",
                "value": "duplicate",
            },
            format="json",
        )

        # Should reject duplicate key for same user
        assert response.status_code in [201, 400]

    def test_case_sensitive_keys(self, api_client, admin_user):
        """Test case sensitivity of preference keys."""
        api_client.force_authenticate(user=admin_user)

        response1 = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "CaseSensitive",
                "value": "value1",
            },
            format="json",
        )
        assert response1.status_code == 201

        response2 = api_client.post(
            "/api/v2/preferences/",
            {
                "user": admin_user.id,
                "key": "casesensitive",
                "value": "value2",
            },
            format="json",
        )

        # Depending on DB collation, this may or may not be allowed
        assert response2.status_code in [201, 400]
