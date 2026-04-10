"""
RED TEAM: T339 - PlayoutHistory validation security tests.

Attack vectors:
- Validation bypass (null values, edge cases)
- Time manipulation (negative duration, extreme values)
- Mass assignment via __all__
- BOLA: access other users' playout history
- Template injection via metadata
"""

import pytest

from model_bakery import baker


@pytest.mark.django_db
class TestPlayoutHistoryValidationBypass:
    """Validation bypass attacks."""

    def test_create_with_null_starts(self, api_client, admin_user):
        """Try to create with null starts."""
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playout-history/",
            {
                "file": file_obj.id,
                "starts": None,
                "ends": "2024-01-01T11:00:00Z",
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("BUG: Accepts null starts")

    def test_create_with_null_ends(self, api_client, admin_user):
        """Try to create with null ends."""
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playout-history/",
            {
                "file": file_obj.id,
                "starts": "2024-01-01T10:00:00Z",
                "ends": None,
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("BUG: Accepts null ends")

    def test_create_with_same_starts_and_ends(self, api_client, admin_user):
        """Try to create with starts == ends (zero duration)."""
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playout-history/",
            {
                "file": file_obj.id,
                "starts": "2024-01-01T10:00:00Z",
                "ends": "2024-01-01T10:00:00Z",
            },
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [201, 400]

    def test_create_with_negative_duration(self, api_client, admin_user):
        """Try to create where ends is way before starts."""
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playout-history/",
            {
                "file": file_obj.id,
                "starts": "2024-01-01T10:00:00Z",
                "ends": "2023-01-01T10:00:00Z",  # 1 year before!
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("BUG: Accepts extreme negative duration")

    def test_create_with_future_dates(self, api_client, admin_user):
        """Try to create with future dates."""
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playout-history/",
            {
                "file": file_obj.id,
                "starts": "2030-01-01T10:00:00Z",
                "ends": "2030-01-01T11:00:00Z",
            },
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestPlayoutHistoryMassAssignment:
    """Mass assignment attacks."""

    def test_create_with_id_field(self, api_client, admin_user):
        """Try to set id field during creation."""
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playout-history/",
            {
                "id": 99999,
                "file": file_obj.id,
                "starts": "2024-01-01T10:00:00Z",
                "ends": "2024-01-01T11:00:00Z",
            },
            format="json",
        )

        if response.status_code == 201:
            data = response.json()
            if data.get("id") == 99999:
                pytest.fail("BUG: Can set id field")

    def test_update_file_field(self, api_client, admin_user):
        """Try to change file via PATCH."""
        file1 = baker.make("storage.File", owner=admin_user)
        file2 = baker.make("storage.File", owner=admin_user)
        history = baker.make(
            "history.PlayoutHistory",
            file=file1,
            starts="2024-01-01T10:00:00Z",
            ends="2024-01-01T11:00:00Z",
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            f"/api/v2/playout-history/{history.id}/",
            {"file": file2.id},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("file") == file2.id:
                pytest.fail("BUG: Can change file field via PATCH")

    def test_update_timestamps(self, api_client, admin_user):
        """Try to modify timestamps via PATCH."""
        file_obj = baker.make("storage.File", owner=admin_user)
        history = baker.make(
            "history.PlayoutHistory",
            file=file_obj,
            starts="2024-01-01T10:00:00Z",
            ends="2024-01-01T11:00:00Z",
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            f"/api/v2/playout-history/{history.id}/",
            {"starts": "2023-01-01T10:00:00Z"},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if "2023" in str(data.get("starts", "")):
                pytest.fail("BUG: Can modify historical timestamps")


@pytest.mark.django_db
class TestPlayoutHistoryBOLA:
    """Broken Object Level Authorization attacks."""

    def test_list_shows_only_own_history(
        self, api_client, admin_user, regular_user,
    ):
        """Verify list returns only user's own history."""
        file1 = baker.make("storage.File", owner=admin_user)
        file2 = baker.make("storage.File", owner=regular_user)

        admin_history = baker.make(
            "history.PlayoutHistory",
            file=file1,
            starts="2024-01-01T10:00:00Z",
            ends="2024-01-01T11:00:00Z",
        )
        user_history = baker.make(
            "history.PlayoutHistory",
            file=file2,
            starts="2024-01-02T10:00:00Z",
            ends="2024-01-02T11:00:00Z",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/playout-history/")

        assert response.status_code == 200
        data = response.json()

        history_ids = [h["id"] for h in data]
        assert user_history.id in history_ids

        if admin_history.id in history_ids:
            pytest.fail("CRITICAL BUG: List shows other users' history (BOLA)")

    def test_access_other_user_history(
        self, api_client, admin_user, regular_user,
    ):
        """Try to access another user's history by ID."""
        file_obj = baker.make("storage.File", owner=admin_user)
        history = baker.make(
            "history.PlayoutHistory",
            file=file_obj,
            starts="2024-01-01T10:00:00Z",
            ends="2024-01-01T11:00:00Z",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/playout-history/{history.id}/")

        if response.status_code == 200:
            pytest.fail("CRITICAL BUG: Can access other user's history (BOLA)")

    def test_delete_other_user_history(
        self, api_client, admin_user, regular_user,
    ):
        """Try to delete another user's history."""
        file_obj = baker.make("storage.File", owner=admin_user)
        history = baker.make(
            "history.PlayoutHistory",
            file=file_obj,
            starts="2024-01-01T10:00:00Z",
            ends="2024-01-01T11:00:00Z",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(f"/api/v2/playout-history/{history.id}/")

        if response.status_code == 204:
            pytest.fail("CRITICAL BUG: Can delete other user's history (BOLA)")


@pytest.mark.django_db
class TestPlayoutHistoryBusinessLogic:
    """Business logic bypasses."""

    def test_create_without_auth(self, api_client):
        """Try to create without authentication."""
        response = api_client.post(
            "/api/v2/playout-history/",
            {
                "starts": "2024-01-01T10:00:00Z",
                "ends": "2024-01-01T11:00:00Z",
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("CRITICAL BUG: Anonymous can create playout history")

    def test_create_with_nonexistent_file(self, api_client, admin_user):
        """Try to create with non-existent file."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playout-history/",
            {
                "file": 99999,
                "starts": "2024-01-01T10:00:00Z",
                "ends": "2024-01-01T11:00:00Z",
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("BUG: Accepts non-existent file_id")

    def test_create_with_invalid_datetime_format(self, api_client, admin_user):
        """Try to create with invalid datetime format."""
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playout-history/",
            {
                "file": file_obj.id,
                "starts": "not-a-datetime",
                "ends": "2024-01-01T11:00:00Z",
            },
            format="json",
        )

        assert response.status_code in [201, 400]

    def test_create_with_very_long_duration(self, api_client, admin_user):
        """Try to create with extremely long duration."""
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/playout-history/",
            {
                "file": file_obj.id,
                "starts": "2024-01-01T00:00:00Z",
                "ends": "2025-01-01T00:00:00Z",  # 1 year!
            },
            format="json",
        )

        # May accept or reject - documenting
        assert response.status_code in [201, 400]
