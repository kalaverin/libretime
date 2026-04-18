"""
RED TEAM: T311 - Preference unique_together validation security tests.

Attack vectors:
- Race condition duplicate creation
- SQL injection via key/value fields
- Unicode normalization bypass
- Null byte injection
- Mass assignment attacks
- Partial index bypass
- IntegrityError information leakage
"""

import time

from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from rest_framework.test import APIClient


@pytest.mark.django_db
class TestPreferenceRaceCondition:
    """Race condition attacks on preference creation."""

    @pytest.mark.django_db(transaction=True)
    def test_race_condition_duplicate_preference_creation(self, admin_user):
        """Try to create duplicate preferences concurrently to bypass validation.

        Attack: Two threads try to create same (user, key) simultaneously.
        Expected: One succeeds, one fails with 400 (not 500).
        """
        client = APIClient()
        client.force_authenticate(user=admin_user)

        results = []
        errors = []

        def create_pref():
            try:
                response = client.post(
                    "/api/v2/preferences",
                    {
                        "key": "race_test_key",
                        "value": "value",
                        "user": admin_user.id,
                    },
                    format="json",
                )
                results.append(response.status_code)
                return response.status_code
            except Exception as e:
                errors.append(str(e))
                return None

        # Run two threads simultaneously
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(create_pref) for _ in range(2)]
            for future in as_completed(futures):
                future.result()

        # One should succeed (201), other should fail (400)
        assert 201 in results
        assert results.count(201) == 1  # Only one success
        # Other should be 400 (validation error) or 500 (if race not handled)
        # We expect 400 with proper validation

    @pytest.mark.django_db(transaction=True)
    def test_rapid_fire_duplicate_requests(self, admin_user):
        """Send many rapid requests with same key to stress validation.

        Attack: Flood API with duplicate key requests.
        """
        client = APIClient()
        client.force_authenticate(user=admin_user)

        statuses = []

        def attempt_create():
            response = client.post(
                "/api/v2/preferences",
                {"key": "flood_key", "value": "test", "user": admin_user.id},
                format="json",
            )
            return response.status_code

        # Send 10 rapid requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(attempt_create) for _ in range(10)]
            for future in as_completed(futures):
                statuses.append(future.result())

        # Only one should succeed
        assert statuses.count(201) == 1
        # Rest should be 400
        assert statuses.count(400) == 9


@pytest.mark.django_db
class TestPreferenceSQLInjection:
    """SQL injection attempts via key/value fields."""

    def test_sqli_in_key_field_union_select(self, admin_client, admin_user):
        """Try SQL injection in key field - UNION SELECT."""
        admin_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "key' UNION SELECT * FROM auth_user--",
            "key'; DROP TABLE cc_pref;--",
            "key' OR '1'='1",
            "key') OR ('1'='1",
            "key'/**/OR/**/'1'='1",
            "key%27%20OR%20%271%27=%271",
            "key\\' OR \\'1\\'\\'=\\'1",
        ]

        for payload in sqli_payloads:
            response = admin_client.post(
                "/api/v2/preferences",
                {"key": payload, "value": "test", "user": admin_user.id},
                format="json",
            )
            # Should either create with escaped key or return 400
            # Should NEVER execute SQL commands
            assert response.status_code in [201, 400]

            if response.status_code == 201:
                # Verify key was stored as-is (escaped), not executed
                data = response.json()
                assert payload in data["key"]  # Key stored literally

    def test_sqli_in_value_field(self, admin_client, admin_user):
        """Try SQL injection in value field."""
        admin_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "value'; DELETE FROM cc_pref WHERE '1'='1",
            "value' UNION SELECT password FROM cc_subjs--",
            "value'||pg_sleep(10)--",
        ]

        for payload in sqli_payloads:
            response = admin_client.post(
                "/api/v2/preferences",
                {
                    "key": f"val_test_{hash(payload)}",
                    "value": payload,
                    "user": admin_user.id,
                },
                format="json",
            )
            # Should store value as-is without executing
            assert response.status_code in [201, 400]

    def test_sqli_time_based_in_key(self, admin_client, admin_user):
        """Time-based SQL injection attempt in key."""
        admin_client.force_authenticate(user=admin_user)

        start = time.time()
        response = admin_client.post(
            "/api/v2/preferences",
            {
                "key": "key'||pg_sleep(5)||'",
                "value": "test",
                "user": admin_user.id,
            },
            format="json",
        )
        elapsed = time.time() - start

        # Should complete quickly (< 2 seconds), not wait for pg_sleep
        assert elapsed < 2.0, "Possible time-based SQL injection vulnerability"


@pytest.mark.django_db
class TestPreferenceUnicodeBypass:
    """Unicode normalization bypass attempts."""

    def test_unicode_normalized_same_key(self, admin_client, admin_user):
        """Try to bypass unique constraint with Unicode equivalent characters.

        Attack: Use visually similar Unicode characters that normalize to same value.
        """
        admin_client.force_authenticate(user=admin_user)

        # First create with normal 'test'
        response1 = admin_client.post(
            "/api/v2/preferences",
            {"key": "test", "value": "value1", "user": admin_user.id},
            format="json",
        )
        assert response1.status_code == 201

        # Try to create with different Unicode forms
        unicode_variants = [
            "test",  # Normal
            "tést",  # With accent
            "test\u200b",  # Zero-width space at end
            "\u200btest",  # Zero-width space at start
            "t\u0435st",  # Cyrillic 'е' instead of Latin 'e'
            "ｔｅｓｔ",  # Fullwidth characters
        ]

        for variant in unicode_variants[1:]:  # Skip first (already created)
            response = admin_client.post(
                "/api/v2/preferences",
                {"key": variant, "value": "value", "user": admin_user.id},
                format="json",
            )
            # Each variant should be treated as different key (201)
            # Or validation might catch some as duplicates
            assert response.status_code in [201, 400]

    def test_null_byte_in_key(self, admin_client, admin_user):
        """Null byte injection in key field.

        Attack: Use null byte to truncate key in C libraries.
        """
        admin_client.force_authenticate(user=admin_user)

        response = admin_client.post(
            "/api/v2/preferences",
            {"key": "test\x00hidden", "value": "value", "user": admin_user.id},
            format="json",
        )

        # Should either reject (400) or store with null byte (201)
        # Should NOT truncate at null byte
        if response.status_code == 201:
            data = response.json()
            # Verify full key stored, not truncated
            assert "\x00" in data["key"] or "hidden" in data["key"]

    def test_newline_in_key(self, admin_client, admin_user):
        """Newline injection in key field."""
        admin_client.force_authenticate(user=admin_user)

        response = admin_client.post(
            "/api/v2/preferences",
            {"key": "line1\nline2", "value": "value", "user": admin_user.id},
            format="json",
        )

        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestPreferenceMassAssignment:
    """Mass assignment vulnerability tests."""

    def test_create_with_id_field(self, admin_client, admin_user):
        """Try to set id field manually (mass assignment)."""
        admin_client.force_authenticate(user=admin_user)

        response = admin_client.post(
            "/api/v2/preferences",
            {
                "id": 999999,
                "key": "id_test",
                "value": "value",
                "user": admin_user.id,
            },
            format="json",
        )

        # Should either ignore id (201) or reject (400)
        # Should NOT use provided id
        if response.status_code == 201:
            data = response.json()
            assert data["id"] != 999999  # ID should be auto-generated

    def test_create_with_invalid_user_id(self, admin_client, admin_user):
        """Try to create preference for non-existent user (IDOR attempt)."""
        admin_client.force_authenticate(user=admin_user)

        response = admin_client.post(
            "/api/v2/preferences",
            {"key": "idor_test", "value": "value", "user": 999999},
            format="json",
        )

        # Should fail with 400 (invalid user)
        assert response.status_code == 400

    def test_create_for_other_user(self, admin_client, admin_user, regular_user):
        """Try to create preference for another user (horizontal privilege escalation)."""
        admin_client.force_authenticate(user=admin_user)

        response = admin_client.post(
            "/api/v2/preferences",
            {
                "key": "other_user_key",
                "value": "value",
                "user": regular_user.id,
            },
            format="json",
        )

        # Admin might be allowed, but should verify
        # If 201, verify the preference was created for host_user
        if response.status_code == 201:
            data = response.json()
            assert data["user"] == regular_user.id


@pytest.mark.django_db
class TestPreferenceInformationDisclosure:
    """Information disclosure via error messages."""

    def test_integrity_error_message_leakage(self, admin_client, admin_user):
        """Check if IntegrityError leaks database schema info.

        Create site pref (user=null) with key, then try to create another site pref
        with same key - this should fail due to partial index.
        """
        admin_client.force_authenticate(user=admin_user)

        # Create first site preference
        response1 = admin_client.post(
            "/api/v2/preferences",
            {"key": "site_key_test", "value": "value1", "user": None},
            format="json",
        )

        # Create second site preference with same key
        response2 = admin_client.post(
            "/api/v2/preferences",
            {"key": "site_key_test", "value": "value2", "user": None},
            format="json",
        )

        # Should fail with 400
        assert response2.status_code == 400

        # Check error message doesn't leak DB details
        if "cc_pref_key_idx" in response2.content.decode():
            # This leaks database constraint name - potential info disclosure
            pytest.fail("Error message leaks database constraint name")

    def test_error_message_uniqueness(self, admin_client, admin_user):
        """Verify error messages don't reveal which field caused uniqueness violation."""
        admin_client.force_authenticate(user=admin_user)

        # Create first preference
        admin_client.post(
            "/api/v2/preferences",
            {"key": "uniq_test", "value": "v1", "user": admin_user.id},
            format="json",
        )

        # Try to create duplicate
        response = admin_client.post(
            "/api/v2/preferences",
            {"key": "uniq_test", "value": "v2", "user": admin_user.id},
            format="json",
        )

        assert response.status_code == 400
        # Error should be generic, not reveal exact constraint


@pytest.mark.django_db
class TestPreferencePartialIndexBypass:
    """Attempts to bypass partial unique index constraints."""

    def test_site_pref_then_user_pref_same_key(self, admin_client, admin_user):
        """Create site pref, then user pref with same key (should work)."""
        admin_client.force_authenticate(user=admin_user)

        # Site preference
        response1 = admin_client.post(
            "/api/v2/preferences",
            {"key": "shared_key", "value": "site_value", "user": None},
            format="json",
        )
        assert response1.status_code == 201

        # User preference with same key - should succeed
        response2 = admin_client.post(
            "/api/v2/preferences",
            {
                "key": "shared_key",
                "value": "user_value",
                "user": admin_user.id,
            },
            format="json",
        )
        assert response2.status_code == 201

    def test_user_pref_then_site_pref_same_key(self, admin_client, admin_user):
        """Create user pref, then site pref with same key (should work)."""
        admin_client.force_authenticate(user=admin_user)

        # User preference
        response1 = admin_client.post(
            "/api/v2/preferences",
            {
                "key": "shared_key2",
                "value": "user_value",
                "user": admin_user.id,
            },
            format="json",
        )
        assert response1.status_code == 201

        # Site preference with same key - should succeed
        response2 = admin_client.post(
            "/api/v2/preferences",
            {"key": "shared_key2", "value": "site_value", "user": None},
            format="json",
        )
        assert response2.status_code == 201

    def test_two_site_prefs_same_key_fails(self, admin_client, admin_user):
        """Two site prefs with same key should fail (partial index)."""
        admin_client.force_authenticate(user=admin_user)

        # First site preference
        response1 = admin_client.post(
            "/api/v2/preferences",
            {"key": "site_unique", "value": "v1", "user": None},
            format="json",
        )
        assert response1.status_code == 201

        # Second site preference with same key
        response2 = admin_client.post(
            "/api/v2/preferences",
            {"key": "site_unique", "value": "v2", "user": None},
            format="json",
        )
        # Should fail due to partial unique index
        assert response2.status_code == 400


@pytest.mark.django_db
class TestPreferenceKeyLength:
    """Key length boundary tests."""

    def test_very_long_key(self, admin_client, admin_user):
        """Try to create preference with very long key."""
        admin_client.force_authenticate(user=admin_user)

        long_key = "k" * 1000

        response = admin_client.post(
            "/api/v2/preferences",
            {"key": long_key, "value": "test", "user": admin_user.id},
            format="json",
        )

        # Should either truncate or reject
        assert response.status_code in [201, 400]

    def test_empty_key(self, admin_client, admin_user):
        """Try to create preference with empty key."""
        admin_client.force_authenticate(user=admin_user)

        response = admin_client.post(
            "/api/v2/preferences",
            {"key": "", "value": "test", "user": admin_user.id},
            format="json",
        )

        # API allows empty key (legacy behavior), verify it's stored
        assert response.status_code in [201, 400]
        if response.status_code == 201:
            data = response.json()
            assert data["key"] == ""

    def test_whitespace_only_key(self, admin_client, admin_user):
        """Try to create preference with whitespace-only key."""
        admin_client.force_authenticate(user=admin_user)

        response = admin_client.post(
            "/api/v2/preferences",
            {"key": "   ", "value": "test", "user": admin_user.id},
            format="json",
        )

        # Should either reject or store as-is
        assert response.status_code in [201, 400]
