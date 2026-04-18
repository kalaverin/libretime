"""Tests for ShowInstances RETRIEVE endpoint (T216)."""

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowInstance


@pytest.mark.django_db(transaction=True)
class TestShowInstanceViewSetRetrieve:
    """Test ShowInstances RETRIEVE endpoint - GET /api/v2/show-instances/{id}."""

    def setup_method(self):
        """Clean up instances before each test."""
        ShowInstance.objects.all().delete()
        Show.objects.all().delete()

    def test_retrieve_instance_success(self, admin_client):
        """RETRIEVE should return instance details."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        assert response.status_code == 200
        assert response.json()["id"] == instance.id

    def test_retrieve_instance_contains_show(self, admin_client):
        """RETRIEVE should include show reference."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        assert response.json()["show"] == show.id

    def test_retrieve_instance_contains_starts_at(self, admin_client):
        """RETRIEVE should include starts_at datetime."""
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

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        data = response.json()
        assert "starts_at" in data

    def test_retrieve_instance_contains_ends_at(self, admin_client):
        """RETRIEVE should include ends_at datetime."""
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

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        data = response.json()
        assert "ends_at" in data

    def test_retrieve_instance_contains_filled_time(self, admin_client):
        """RETRIEVE should include filled_time."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            filled_time=timedelta(minutes=45),
        )

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        data = response.json()
        assert "filled_time" in data

    def test_retrieve_instance_null_filled_time(self, admin_client):
        """RETRIEVE should handle null filled_time."""
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

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        assert response.json()["filled_time"] is None

    def test_retrieve_instance_contains_description(self, admin_client):
        """RETRIEVE should include description."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            description="Special episode",
        )

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        assert response.json()["description"] == "Special episode"

    def test_retrieve_instance_contains_modified(self, admin_client):
        """RETRIEVE should include modified flag."""
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

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        assert response.json()["modified"] is True

    def test_retrieve_instance_modified_false(self, admin_client):
        """RETRIEVE should show modified=false."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            modified=False,
        )

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        assert response.json()["modified"] is False

    def test_retrieve_instance_contains_rebroadcast(self, admin_client):
        """RETRIEVE should include rebroadcast flag."""
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

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        assert response.json()["rebroadcast"] == 1

    def test_retrieve_instance_contains_auto_playlist_built(self, admin_client):
        """RETRIEVE should include auto_playlist_built flag."""
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

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        assert response.json()["auto_playlist_built"] is True

    def test_retrieve_instance_contains_last_scheduled_at(self, admin_client):
        """RETRIEVE should include last_scheduled_at."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        last_scheduled = now().replace(microsecond=0)
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            last_scheduled_at=last_scheduled,
        )

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        data = response.json()
        assert "last_scheduled_at" in data

    def test_retrieve_instance_null_last_scheduled_at(self, admin_client):
        """RETRIEVE should handle null last_scheduled_at."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            last_scheduled_at=None,
        )

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        assert response.json()["last_scheduled_at"] is None

    def test_retrieve_instance_contains_record_enabled(self, admin_client):
        """RETRIEVE should include record_enabled."""
        from datetime import timedelta

        from api.schedule.models.show import Record
        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            record_enabled=Record.YES,
        )

        response = admin_client.get(f"/api/v2/show-instances/{instance.id}")
        data = response.json()
        assert "record_enabled" in data

    def test_retrieve_instance_not_found_returns_404(self, admin_client):
        """RETRIEVE non-existent instance should return 404."""
        response = admin_client.get("/api/v2/show-instances/999999")
        assert response.status_code == 404

    def test_retrieve_instance_no_auth_fails(self, client):
        """RETRIEVE without auth should return 403."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )

        response = client.get(f"/api/v2/show-instances/{instance.id}")
        assert response.status_code == 403

    def test_retrieve_instance_invalid_id_returns_404(self, admin_client):
        """RETRIEVE with invalid id should return 404."""
        response = admin_client.get("/api/v2/show-instances/abc")
        assert response.status_code == 404
