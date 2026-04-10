"""
RED TEAM: T335/T336 - Schedule filter/validation security tests.

Attack vectors:
- Filter injection (SQLi through instance param)
- Validation bypass (null file/stream, both provided)
- Mass assignment via __all__
- BOLA: access other users' schedules
- Instance ID type confusion
"""

import pytest

from model_bakery import baker


@pytest.mark.django_db
class TestScheduleFilterInjection:
    """Filter parameter injection attacks."""

    def test_filter_by_invalid_instance_id(self, api_client, admin_user):
        """Try to filter by invalid instance_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/schedule?instance=invalid")

        if response.status_code == 500:
            pytest.fail(
                "BUG: Filter crashes on invalid instance_id (500 error)",
            )
        assert response.status_code in [200, 400]

    def test_filter_by_sql_injection(self, api_client, admin_user):
        """Try SQL injection in instance filter."""
        api_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_schedule;--",
            "1 UNION SELECT * FROM cc_subjs",
        ]

        for payload in sqli_payloads:
            response = api_client.get(f"/api/v2/schedule?instance={payload}")

            if response.status_code == 500:
                pytest.fail(f"BUG: SQL injection causes 500: {payload}")

    def test_filter_by_negative_instance_id(self, api_client, admin_user):
        """Try to filter by negative instance_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/schedule?instance=-1")
        assert response.status_code in [200, 400]

    def test_filter_by_float_instance_id(self, api_client, admin_user):
        """Try to filter by float instance_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/schedule?instance=1.5")
        assert response.status_code in [200, 400]

    def test_filter_without_auth(self, api_client):
        """Try to filter without authentication."""
        response = api_client.get("/api/v2/schedule?instance=1")

        if response.status_code == 200:
            pytest.fail("BUG: Anonymous can filter schedules")


@pytest.mark.django_db
class TestScheduleValidationBypass:
    """Validation bypass attacks."""

    def test_create_with_null_file_and_stream(self, api_client, admin_user):
        """Try to create with explicit null file and stream."""
        instance = baker.make("schedule.ShowInstance")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/schedule/",
            {
                "instance": instance.id,
                "file": None,
                "stream": None,
                "starts_at": "2024-01-01T10:00:00Z",
                "ends_at": "2024-01-01T11:00:00Z",
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("BUG: Accepts null file and null stream")

    def test_create_with_both_file_and_stream(self, api_client, admin_user):
        """Try to create with BOTH file and stream (should be exclusive)."""
        instance = baker.make("schedule.ShowInstance")
        file_obj = baker.make("storage.File", owner=admin_user)
        stream = baker.make("schedule.Webstream", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/schedule/",
            {
                "instance": instance.id,
                "file": file_obj.id,
                "stream": stream.id,
                "starts_at": "2024-01-01T10:00:00Z",
                "ends_at": "2024-01-01T11:00:00Z",
            },
            format="json",
        )

        # Should reject - can't have both file AND stream
        if response.status_code == 201:
            pytest.fail(
                "BUG: Accepts both file AND stream (should be exclusive)",
            )

    def test_create_with_empty_string_file(self, api_client, admin_user):
        """Try to create with empty string file."""
        instance = baker.make("schedule.ShowInstance")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/schedule/",
            {
                "instance": instance.id,
                "file": "",
                "starts_at": "2024-01-01T10:00:00Z",
                "ends_at": "2024-01-01T11:00:00Z",
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("BUG: Accepts empty string as file")

    def test_create_with_zero_file_id(self, api_client, admin_user):
        """Try to create with file=0."""
        instance = baker.make("schedule.ShowInstance")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/schedule/",
            {
                "instance": instance.id,
                "file": 0,
                "starts_at": "2024-01-01T10:00:00Z",
                "ends_at": "2024-01-01T11:00:00Z",
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("BUG: Accepts file=0 as valid")

    def test_create_with_nonexistent_file(self, api_client, admin_user):
        """Try to create with non-existent file ID."""
        instance = baker.make("schedule.ShowInstance")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/schedule/",
            {
                "instance": instance.id,
                "file": 99999,
                "starts_at": "2024-01-01T10:00:00Z",
                "ends_at": "2024-01-01T11:00:00Z",
            },
            format="json",
        )

        # Should reject non-existent file
        if response.status_code == 201:
            pytest.fail("BUG: Accepts non-existent file_id")

    def test_create_with_nonexistent_stream(self, api_client, admin_user):
        """Try to create with non-existent stream ID."""
        instance = baker.make("schedule.ShowInstance")

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/schedule/",
            {
                "instance": instance.id,
                "stream": 99999,
                "starts_at": "2024-01-01T10:00:00Z",
                "ends_at": "2024-01-01T11:00:00Z",
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("BUG: Accepts non-existent stream_id")


@pytest.mark.django_db
class TestScheduleMassAssignment:
    """Mass assignment attacks."""

    def test_create_with_id_field(self, api_client, admin_user):
        """Try to set id field during creation."""
        instance = baker.make("schedule.ShowInstance")
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/schedule/",
            {
                "id": 99999,
                "instance": instance.id,
                "file": file_obj.id,
                "starts_at": "2024-01-01T10:00:00Z",
                "ends_at": "2024-01-01T11:00:00Z",
            },
            format="json",
        )

        if response.status_code == 201:
            data = response.json()
            if data.get("id") == 99999:
                pytest.fail("BUG: Can set id field during creation")

    def test_update_instance_field(self, api_client, admin_user):
        """Try to change instance via PATCH."""
        instance1 = baker.make("schedule.ShowInstance")
        instance2 = baker.make("schedule.ShowInstance")
        file_obj = baker.make("storage.File", owner=admin_user)
        schedule = baker.make(
            "schedule.Schedule",
            instance=instance1,
            file=file_obj,
            starts_at="2024-01-01T10:00:00Z",
            ends_at="2024-01-01T11:00:00Z",
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            f"/api/v2/schedule/{schedule.id}/",
            {"instance": instance2.id},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("instance") == instance2.id:
                pytest.fail("BUG: Can transfer schedule to different instance")


@pytest.mark.django_db
class TestScheduleBOLA:
    """Broken Object Level Authorization attacks."""

    def test_list_shows_only_own_schedules(
        self, api_client, admin_user, regular_user,
    ):
        """Verify list returns only user's own schedules."""
        # Create schedules for both users
        instance1 = baker.make("schedule.ShowInstance")
        instance2 = baker.make("schedule.ShowInstance")
        file1 = baker.make("storage.File", owner=admin_user)
        file2 = baker.make("storage.File", owner=regular_user)

        admin_schedule = baker.make(
            "schedule.Schedule",
            instance=instance1,
            file=file1,
            starts_at="2024-01-01T10:00:00Z",
            ends_at="2024-01-01T11:00:00Z",
        )
        user_schedule = baker.make(
            "schedule.Schedule",
            instance=instance2,
            file=file2,
            starts_at="2024-01-02T10:00:00Z",
            ends_at="2024-01-02T11:00:00Z",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/schedule/")

        assert response.status_code == 200
        data = response.json()

        schedule_ids = [s["id"] for s in data]
        assert user_schedule.id in schedule_ids

        if admin_schedule.id in schedule_ids:
            pytest.fail(
                "CRITICAL BUG: List shows other users' schedules (BOLA)",
            )

    def test_access_other_user_schedule(
        self, api_client, admin_user, regular_user,
    ):
        """Try to access another user's schedule by ID."""
        instance = baker.make("schedule.ShowInstance")
        file_obj = baker.make("storage.File", owner=admin_user)
        schedule = baker.make(
            "schedule.Schedule",
            instance=instance,
            file=file_obj,
            starts_at="2024-01-01T10:00:00Z",
            ends_at="2024-01-01T11:00:00Z",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/schedule/{schedule.id}/")

        if response.status_code == 200:
            pytest.fail(
                "CRITICAL BUG: Can access other user's schedule (BOLA)",
            )

    def test_update_other_user_schedule(
        self, api_client, admin_user, regular_user,
    ):
        """Try to update another user's schedule."""
        instance = baker.make("schedule.ShowInstance")
        file_obj = baker.make("storage.File", owner=admin_user)
        schedule = baker.make(
            "schedule.Schedule",
            instance=instance,
            file=file_obj,
            starts_at="2024-01-01T10:00:00Z",
            ends_at="2024-01-01T11:00:00Z",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.patch(
            f"/api/v2/schedule/{schedule.id}/",
            {"ends_at": "2024-01-01T12:00:00Z"},
            format="json",
        )

        if response.status_code == 200:
            pytest.fail(
                "CRITICAL BUG: Can update other user's schedule (BOLA)",
            )

    def test_delete_other_user_schedule(
        self, api_client, admin_user, regular_user,
    ):
        """Try to delete another user's schedule."""
        instance = baker.make("schedule.ShowInstance")
        file_obj = baker.make("storage.File", owner=admin_user)
        schedule = baker.make(
            "schedule.Schedule",
            instance=instance,
            file=file_obj,
            starts_at="2024-01-01T10:00:00Z",
            ends_at="2024-01-01T11:00:00Z",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(f"/api/v2/schedule/{schedule.id}/")

        if response.status_code == 204:
            pytest.fail(
                "CRITICAL BUG: Can delete other user's schedule (BOLA)",
            )


@pytest.mark.django_db
class TestScheduleBusinessLogic:
    """Business logic bypasses."""

    def test_create_without_auth(self, api_client):
        """Try to create without authentication."""
        instance = baker.make("schedule.ShowInstance")

        response = api_client.post(
            "/api/v2/schedule/",
            {
                "instance": instance.id,
                "starts_at": "2024-01-01T10:00:00Z",
                "ends_at": "2024-01-01T11:00:00Z",
            },
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("CRITICAL BUG: Anonymous can create schedule")

    def test_create_with_ends_before_starts(self, api_client, admin_user):
        """Try to create schedule where ends_at < starts_at."""
        instance = baker.make("schedule.ShowInstance")
        file_obj = baker.make("storage.File", owner=admin_user)

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/schedule/",
            {
                "instance": instance.id,
                "file": file_obj.id,
                "starts_at": "2024-01-01T12:00:00Z",
                "ends_at": "2024-01-01T10:00:00Z",  # Before starts!
            },
            format="json",
        )

        # Should reject illogical times
        if response.status_code == 201:
            pytest.fail("BUG: Accepts ends_at before starts_at")

    def test_create_with_overlapping_schedule(self, api_client, admin_user):
        """Try to create overlapping schedule for same instance."""
        instance = baker.make("schedule.ShowInstance")
        file1 = baker.make("storage.File", owner=admin_user)
        file2 = baker.make("storage.File", owner=admin_user)

        # Create first schedule
        baker.make(
            "schedule.Schedule",
            instance=instance,
            file=file1,
            starts_at="2024-01-01T10:00:00Z",
            ends_at="2024-01-01T11:00:00Z",
        )

        # Try to create overlapping schedule
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/schedule/",
            {
                "instance": instance.id,
                "file": file2.id,
                "starts_at": "2024-01-01T10:30:00Z",  # Overlaps!
                "ends_at": "2024-01-01T11:30:00Z",
            },
            format="json",
        )

        # May accept or reject - documenting behavior
        assert response.status_code in [201, 400]
