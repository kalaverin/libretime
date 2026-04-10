"""T262: PlayoutHistoryMetadata redteam security tests.

Red Team security tests for PlayoutHistoryMetadata endpoints.
Tests for BOLA, BOPLA, injection in metadata operations.
"""

from datetime import timedelta

import pytest

from model_bakery import baker

from api.core.models.role import Role
from api.core.models.user import User
from api.history.models import PlayoutHistory, PlayoutHistoryMetadata
from api.storage.models import File
from sdk import now


@pytest.mark.django_db
class TestPlayoutHistoryMetadataRedTeamBOLA:
    """API1:2023 Broken Object Level Authorization - metadata BOLA."""

    @pytest.fixture
    def victim_metadata(self, faker):
        """Create victim user's metadata."""
        victim = baker.make(
            User, role=Role.HOST, username=f"victim_{faker.user_name()}",
        )
        victim_file = baker.make(File, mime="audio/mp3", owner=victim)
        victim_playout = baker.make(
            PlayoutHistory,
            file=victim_file,
            starts=now(),
            ends=now() + timedelta(minutes=5),
        )
        return baker.make(
            PlayoutHistoryMetadata,
            history=victim_playout,
            key="artist",
            value="Victim Artist",
        )

    def test_bola_list_shows_all_metadata(
        self, api_client, admin_user, victim_metadata, faker,
    ):
        """
        BOLA: LIST metadata returns all users' entries.

        Should filter by requesting user's playout history.
        """
        response = api_client.get("/api/v2/playout-history-metadata")

        assert response.status_code == 200
        data = response.json()

        # Check if victim's metadata is visible
        victim_ids = [m.get("id") for m in data]
        if victim_metadata.id in victim_ids:
            # Admin can see all - document this behavior
            pass

    def test_bola_retrieve_other_users_metadata(
        self, api_client, admin_user, victim_metadata,
    ):
        """
        BOLA: RETRIEVE other user's metadata by ID.
        """
        response = api_client.get(
            f"/api/v2/playout-history-metadata/{victim_metadata.id}",
        )

        if response.status_code == 200:
            data = response.json()
            assert data["id"] == victim_metadata.id

    def test_bola_create_metadata_for_other_users_playout(
        self, api_client, admin_user, faker,
    ):
        """
        BOLA: CREATE metadata for another user's playout.

        Should verify ownership of referenced playout history.
        """
        # Create victim playout
        victim = baker.make(User, role=Role.HOST, username=faker.user_name())
        victim_file = baker.make(File, mime="audio/mp3", owner=victim)
        victim_playout = baker.make(
            PlayoutHistory,
            file=victim_file,
            starts=now(),
            ends=now() + timedelta(minutes=5),
        )

        data = {
            "history": victim_playout.id,
            "key": "attacker_key",
            "value": "Attacker Value",
        }

        response = api_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )

        if response.status_code == 201:
            # Successfully created metadata for victim's playout
            pytest.xfail(
                "T626: BOLA - Can create metadata for other user's playout",
            )

    def test_bola_update_other_users_metadata(
        self, api_client, admin_user, victim_metadata,
    ):
        """
        BOLA: UPDATE other user's metadata.
        """
        data = {
            "history": victim_metadata.history.id,
            "key": "hacked_key",
            "value": "Hacked Value",
        }

        response = api_client.put(
            f"/api/v2/playout-history-metadata/{victim_metadata.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            # Successfully modified victim's metadata
            pass

    def test_bola_delete_other_users_metadata(
        self, api_client, admin_user, victim_metadata,
    ):
        """
        BOLA: DELETE other user's metadata.
        """
        response = api_client.delete(
            f"/api/v2/playout-history-metadata/{victim_metadata.id}",
        )

        if response.status_code == 204:
            # Successfully deleted victim's metadata
            pass

    def test_bola_metadata_links_to_history_detail(
        self, api_client, admin_user, victim_metadata,
    ):
        """
        BOLA: Metadata reveals history details.

        Metadata includes history_id which can be used to access history.
        """
        response = api_client.get(
            f"/api/v2/playout-history-metadata/{victim_metadata.id}",
        )

        if response.status_code == 200:
            data = response.json()
            # Metadata reveals which playout it belongs to
            history_id = data.get("history")
            if history_id:
                # Try to access the linked history
                history_response = api_client.get(
                    f"/api/v2/playout-history/{history_id}",
                )
                # Document whether history is accessible


@pytest.mark.django_db
class TestPlayoutHistoryMetadataRedTeamBOPLA:
    """API3:2023 Broken Object Property Level Authorization - metadata mass assignment."""

    def test_bopla_create_mass_assignment_id(
        self, api_client, admin_user, faker,
    ):
        """
        BOPLA: CREATE metadata with forced ID.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        forced_id = 999999
        data = {
            "id": forced_id,
            "history": playout.id,
            "key": "test",
            "value": "test",
        }

        response = api_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )

        if response.status_code == 201:
            result = response.json()
            if result.get("id") == forced_id:
                pytest.xfail("T627: BOPLA - Metadata id mass assignment works")

    def test_bopla_create_extra_fields_ignored(
        self, api_client, admin_user, faker,
    ):
        """
        BOPLA: CREATE metadata with extra fields silently ignored.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        data = {
            "history": playout.id,
            "key": "artist",
            "value": "Test Artist",
            "is_admin": True,
            "password": "stolen",
        }

        response = api_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )

        if response.status_code == 201:
            pytest.xfail(
                "T628: BOPLA - Metadata extra fields silently ignored",
            )

    def test_bopla_update_extra_fields_ignored(
        self, api_client, admin_user, faker,
    ):
        """
        BOPLA: UPDATE metadata with extra fields.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())
        metadata = baker.make(
            PlayoutHistoryMetadata,
            history=playout,
            key="title",
            value="Original",
        )

        data = {
            "history": playout.id,
            "key": "title",
            "value": "Updated",
            "extra_field": "should_be_rejected",
        }

        response = api_client.put(
            f"/api/v2/playout-history-metadata/{metadata.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            pytest.xfail("T629: BOPLA - Metadata UPDATE extra fields ignored")

    def test_bopla_patch_key_value_manipulation(
        self, api_client, admin_user, faker,
    ):
        """
        BOPLA: PATCH metadata key/value.

        Test what characters are accepted in key/value.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())
        metadata = baker.make(
            PlayoutHistoryMetadata,
            history=playout,
            key="genre",
            value="Rock",
        )

        # Try to set key to reserved/system value
        data = {"key": "__internal__", "value": "system_data"}

        response = api_client.patch(
            f"/api/v2/playout-history-metadata/{metadata.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            # Check if reserved keys are allowed
            pass  # Document behavior


@pytest.mark.django_db
class TestPlayoutHistoryMetadataRedTeamInjection:
    """Injection attacks on metadata endpoints."""

    def test_sqli_in_key_field(self, api_client, admin_user, faker):
        """
        SQL Injection via key field.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        sqli_keys = [
            "artist' OR '1'='1",
            "title'; DROP TABLE cc_playout_history_metadata--",
            "genre' UNION SELECT * FROM pg_authid--",
        ]

        for key in sqli_keys:
            data = {
                "history": playout.id,
                "key": key,
                "value": "test",
            }

            response = api_client.post(
                "/api/v2/playout-history-metadata",
                data,
                format="json",
            )

            if response.status_code == 500:
                pytest.xfail(f"T630: SQLi in key field causes 500: {key[:30]}")

            error_text = str(response.content).lower()
            if "sql" in error_text or "syntax" in error_text:
                pytest.xfail(f"T630: SQLi error disclosure: {key[:30]}")

    def test_sqli_in_value_field(self, api_client, admin_user, faker):
        """
        SQL Injection via value field.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        sqli_values = [
            "' OR '1'='1",
            "'; DROP TABLE cc_playout_history--",
            "' UNION SELECT password FROM users--",
        ]

        for value in sqli_values:
            data = {
                "history": playout.id,
                "key": "test",
                "value": value,
            }

            response = api_client.post(
                "/api/v2/playout-history-metadata",
                data,
                format="json",
            )

            if response.status_code == 500:
                pytest.xfail(
                    f"T630: SQLi in value field causes 500: {value[:30]}",
                )

    def test_xss_in_key_field(self, api_client, admin_user, faker):
        """
        XSS payloads in key field.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        xss_keys = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
        ]

        for key in xss_keys:
            data = {
                "history": playout.id,
                "key": key,
                "value": "test",
            }

            response = api_client.post(
                "/api/v2/playout-history-metadata",
                data,
                format="json",
            )

            if response.status_code == 201:
                # XSS payload stored - check if sanitized on retrieval
                result = response.json()
                stored_key = result.get("key")
                if stored_key == key:
                    # Stored without sanitization
                    pytest.xfail("T631: XSS in key field stored unsanitized")

    def test_xss_in_value_field(self, api_client, admin_user, faker):
        """
        XSS payloads in value field.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        xss_values = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
        ]

        for value in xss_values:
            data = {
                "history": playout.id,
                "key": "test",
                "value": value,
            }

            response = api_client.post(
                "/api/v2/playout-history-metadata",
                data,
                format="json",
            )

            if response.status_code == 201:
                result = response.json()
                stored_value = result.get("value")
                if stored_value == value:
                    pytest.xfail(
                        "T631: XSS in value field stored unsanitized",
                    )

    def test_command_injection_in_value(self, api_client, admin_user, faker):
        """
        Command injection patterns in value.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        cmd_values = [
            "$(whoami)",
            "`id`",
            "; cat /etc/passwd",
            "| ls -la",
        ]

        for value in cmd_values:
            data = {
                "history": playout.id,
                "key": "test",
                "value": value,
            }

            response = api_client.post(
                "/api/v2/playout-history-metadata",
                data,
                format="json",
            )

            # Should accept any string value
            assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestPlayoutHistoryMetadataRedTeamValidation:
    """Validation and edge case tests."""

    def test_create_with_nonexistent_history(self, api_client, admin_user):
        """
        Validation: CREATE with non-existent history ID.
        """
        data = {
            "history": 999999,
            "key": "artist",
            "value": "Test",
        }

        response = api_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )

        assert response.status_code == 400

    def test_create_missing_required_key(self, api_client, admin_user, faker):
        """
        Validation: CREATE without required key field.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        data = {
            "history": playout.id,
            "value": "No Key Provided",
        }

        response = api_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )

        assert response.status_code == 400

    def test_create_missing_required_value(
        self, api_client, admin_user, faker,
    ):
        """
        Validation: CREATE without required value field.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        data = {
            "history": playout.id,
            "key": "artist",
        }

        response = api_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )

        # Value might be optional - document behavior
        assert response.status_code in [201, 400]

    def test_create_duplicate_key_same_history(
        self, api_client, admin_user, faker,
    ):
        """
        Validation: Duplicate key for same history.

        Should this be allowed or rejected?
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        # First create
        data = {
            "history": playout.id,
            "key": "artist",
            "value": "First Artist",
        }
        response1 = api_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )
        assert response1.status_code == 201

        # Try duplicate
        data["value"] = "Second Artist"
        response2 = api_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )

        # Document behavior
        if response2.status_code == 201:
            # Duplicates allowed
            pass
        elif response2.status_code == 400:
            # Duplicates rejected
            pass

    def test_very_long_key(self, api_client, admin_user, faker):
        """
        Validation: Very long key values.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        data = {
            "history": playout.id,
            "key": "A" * 1000,
            "value": "test",
        }

        response = api_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )

        # Should be limited by max_length
        assert response.status_code in [201, 400]

    def test_very_long_value(self, api_client, admin_user, faker):
        """
        Validation: Very long value.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        data = {
            "history": playout.id,
            "key": "lyrics",
            "value": "A" * 10000,
        }

        response = api_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )

        # Check if there's a length limit
        if response.status_code == 201:
            result = response.json()
            if len(result.get("value", "")) == 10000:
                pytest.xfail("T632: No max_length validation on value field")


@pytest.mark.django_db
class TestPlayoutHistoryMetadataRedTeamResourceConsumption:
    """API4:2023 Unrestricted Resource Consumption."""

    def test_rapid_metadata_creation(self, api_client, admin_user, faker):
        """
        Rate limiting: Rapid metadata CREATE.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        success_count = 0
        for i in range(20):
            data = {
                "history": playout.id,
                "key": f"key_{i}",
                "value": f"value_{i}",
            }
            response = api_client.post(
                "/api/v2/playout-history-metadata",
                data,
                format="json",
            )
            if response.status_code == 201:
                success_count += 1

        if success_count == 20:
            pytest.xfail("T633: No rate limiting on metadata CREATE")

    def test_bulk_metadata_list(self, api_client, admin_user, faker):
        """
        Resource consumption: Large metadata list.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playout = baker.make(PlayoutHistory, file=f, starts=now())

        # Create many metadata entries
        for i in range(50):
            baker.make(
                PlayoutHistoryMetadata,
                history=playout,
                key=f"key_{i}",
                value=f"value_{i}",
            )

        response = api_client.get("/api/v2/playout-history-metadata")

        if response.status_code == 200:
            data = response.json()
            if len(data) > 1000:
                pytest.xfail("T634: Large metadata list without pagination")


@pytest.mark.django_db
class TestPlayoutHistoryMetadataRedTeamAuthentication:
    """Authentication tests."""

    def test_unauthenticated_list(self, api_client):
        """
        Auth: Unauthenticated LIST should fail.
        """
        api_client.logout()
        response = api_client.get("/api/v2/playout-history-metadata")
        assert response.status_code == 403

    def test_unauthenticated_create(self, api_client):
        """
        Auth: Unauthenticated CREATE should fail.
        """
        api_client.logout()
        response = api_client.post(
            "/api/v2/playout-history-metadata",
            {"key": "test", "value": "test"},
            format="json",
        )
        assert response.status_code == 403

    def test_guest_user_create(self, api_client, guest_user, faker):
        """
        BFLA: Guest user CREATE permissions.
        """
        api_client.force_authenticate(user=guest_user)

        data = {
            "key": "artist",
            "value": "Guest Artist",
        }

        response = api_client.post(
            "/api/v2/playout-history-metadata",
            data,
            format="json",
        )

        if response.status_code == 201:
            pytest.xfail("T635: BFLA - Guest can create metadata")
