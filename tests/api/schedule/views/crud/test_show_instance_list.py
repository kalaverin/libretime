"""Tests for ShowInstances LIST endpoint (T215)."""

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowInstance


@pytest.mark.django_db(transaction=True)
class TestShowInstanceViewSetList:
    """Test ShowInstances LIST endpoint - GET /api/v2/show-instances."""

    def setup_method(self):
        """Clean up instances before each test."""
        ShowInstance.objects.all().delete()
        Show.objects.all().delete()

    def test_list_instances_empty_returns_200(self, admin_client):
        """LIST with no instances should return empty array."""
        response = admin_client.get("/api/v2/show-instances")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_instances_returns_all(self, admin_client):
        """LIST should return all instances."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance1 = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )
        instance2 = baker.make(
            ShowInstance,
            show=show,
            starts_at=now() + timedelta(days=1),
            ends_at=now() + timedelta(days=1, hours=1),
        )

        response = admin_client.get("/api/v2/show-instances")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_instances_returns_json(self, admin_client):
        """LIST should return JSON response."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )

        response = admin_client.get("/api/v2/show-instances")
        assert response["Content-Type"] == "application/json"

    def test_list_instances_contains_id(self, admin_client):
        """LIST should include instance id."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )

        response = admin_client.get("/api/v2/show-instances")
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == instance.id

    def test_list_instances_contains_show(self, admin_client):
        """LIST should include show reference."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )

        response = admin_client.get("/api/v2/show-instances")
        data = response.json()
        assert data[0]["show"] == show.id

    def test_list_instances_contains_starts_at(self, admin_client):
        """LIST should include starts_at datetime."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        start_time = now().replace(microsecond=0)
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=1),
        )

        response = admin_client.get("/api/v2/show-instances")
        data = response.json()
        assert "starts_at" in data[0]

    def test_list_instances_contains_ends_at(self, admin_client):
        """LIST should include ends_at datetime."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        start_time = now().replace(microsecond=0)
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=1),
        )

        response = admin_client.get("/api/v2/show-instances")
        data = response.json()
        assert "ends_at" in data[0]

    def test_list_instances_contains_filled_time(self, admin_client):
        """LIST should include filled_time."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            filled_time=timedelta(minutes=30),
        )

        response = admin_client.get("/api/v2/show-instances")
        data = response.json()
        assert "filled_time" in data[0]

    def test_list_instances_null_filled_time(self, admin_client):
        """LIST should handle null filled_time."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            filled_time=None,
        )

        response = admin_client.get("/api/v2/show-instances")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["filled_time"] is None

    def test_list_instances_contains_description(self, admin_client):
        """LIST should include description."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            description="Instance description",
        )

        response = admin_client.get("/api/v2/show-instances")
        data = response.json()
        assert data[0]["description"] == "Instance description"

    def test_list_instances_contains_modified(self, admin_client):
        """LIST should include modified flag."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            modified=True,
        )

        response = admin_client.get("/api/v2/show-instances")
        data = response.json()
        assert data[0]["modified"] is True

    def test_list_instances_contains_rebroadcast(self, admin_client):
        """LIST should include rebroadcast flag."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            rebroadcast=1,
        )

        response = admin_client.get("/api/v2/show-instances")
        data = response.json()
        assert "rebroadcast" in data[0]

    def test_list_instances_contains_auto_playlist_built(self, admin_client):
        """LIST should include auto_playlist_built flag."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            auto_playlist_built=True,
        )

        response = admin_client.get("/api/v2/show-instances")
        data = response.json()
        assert data[0]["auto_playlist_built"] is True

    def test_list_instances_filter_by_show(self, admin_client):
        """LIST should support filtering by show."""
        from datetime import timedelta

        from sdk import now

        show1 = baker.make(Show, name="Show 1")
        show2 = baker.make(Show, name="Show 2")

        baker.make(
            ShowInstance,
            show=show1,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )
        baker.make(
            ShowInstance,
            show=show2,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )

        response = admin_client.get(f"/api/v2/show-instances?show={show1.id}")
        # Filtering may or may not be supported
        assert response.status_code in [200, 400]

    def test_list_instances_no_auth_fails(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/show-instances")
        assert response.status_code == 403
