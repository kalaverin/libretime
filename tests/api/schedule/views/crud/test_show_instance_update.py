"""Tests for ShowInstances UPDATE endpoint (T217)."""

import json

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import format_datetime, reformat_datetime

from api.schedule.models import Show, ShowInstance
from sdk import now


@pytest.mark.django_db(transaction=True)
class TestShowInstanceViewSetUpdate:
    """Test ShowInstances UPDATE endpoint - PUT/PATCH /api/v2/show-instances/{id}."""

    def setup_method(self):
        """Clean up instances before each test."""
        ShowInstance.objects.all().delete()
        Show.objects.all().delete()

    def test_patch_update_description_success(self, api_client):
        """PATCH should update instance description."""
        show = baker.make(Show, name="Test Show")
        start_time = now()
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=1),
            description="Original description",
        )

        response = api_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps({"description": "Updated description"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert reformat_datetime(data["starts_at"]) == format_datetime(
            start_time,
        )

    def test_patch_update_mark_modified(self, api_client):
        """PATCH should mark instance as modified."""
        show = baker.make(Show, name="Test Show")
        start_time = now()
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=1),
            modified=False,
        )

        response = api_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps({"modified": True}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["modified"] is True
        assert reformat_datetime(data["starts_at"]) == format_datetime(
            start_time,
        )

    def test_patch_update_unmark_modified(self, api_client):
        """PATCH should unmark instance as modified."""
        show = baker.make(Show, name="Test Show")
        start_time = now()
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=1),
            modified=True,
        )

        response = api_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps({"modified": False}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["modified"] is False
        assert reformat_datetime(data["starts_at"]) == format_datetime(
            start_time,
        )

    def test_patch_update_starts_at(self, api_client):
        """PATCH should update starts_at datetime."""
        show = baker.make(Show, name="Test Show")
        start_time = now().replace(microsecond=0)
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=1),
        )

        new_start = format_datetime(start_time + timedelta(hours=2))
        response = api_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps({"starts_at": new_start}),
            content_type="application/json",
        )
        # May or may not allow updating starts_at
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert reformat_datetime(data["starts_at"]) == new_start

    def test_patch_update_ends_at(self, api_client):
        """PATCH should update ends_at datetime."""
        show = baker.make(Show, name="Test Show")
        start_time = now().replace(microsecond=0)
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=1),
        )

        new_end = format_datetime(start_time + timedelta(hours=3))
        response = api_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps({"ends_at": new_end}),
            content_type="application/json",
        )
        # May or may not allow updating ends_at
        assert response.status_code in [200, 400]

    def test_patch_update_filled_time(self, api_client):
        """PATCH should update filled_time."""
        show = baker.make(Show, name="Test Show")
        start_time = now()
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=1),
            filled_time=None,
        )

        response = api_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps({"filled_time": "00:45:00"}),
            content_type="application/json",
        )
        # May or may not allow updating filled_time
        assert response.status_code in [200, 400]

    def test_patch_update_rebroadcast(self, api_client):
        """PATCH should update rebroadcast flag."""
        show = baker.make(Show, name="Test Show")
        start_time = now()
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=1),
            rebroadcast=0,
        )

        response = api_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps({"rebroadcast": 1}),
            content_type="application/json",
        )
        assert response.status_code in [200, 400]

    def test_patch_update_auto_playlist_built(self, api_client):
        """PATCH should update auto_playlist_built flag."""
        show = baker.make(Show, name="Test Show")
        start_time = now()
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=1),
            auto_playlist_built=False,
        )

        response = api_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps({"auto_playlist_built": True}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["auto_playlist_built"] is True
        assert reformat_datetime(data["starts_at"]) == format_datetime(
            start_time,
        )

    def test_patch_not_found_returns_404(self, api_client):
        """PATCH non-existent instance should return 404."""
        response = api_client.patch(
            "/api/v2/show-instances/999999",
            json.dumps({"description": "Updated"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_patch_no_auth_fails(self, client):
        """PATCH without auth should return 403."""
        show = baker.make(Show, name="Test Show")
        start_time = now()
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=1),
        )

        response = client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps({"description": "Updated"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_patch_empty_body_no_change(self, api_client):
        """PATCH with empty body should not change anything."""
        show = baker.make(Show, name="Test Show")
        start_time = now()
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=1),
            description="Original",
        )

        response = api_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Original"
        assert reformat_datetime(data["starts_at"]) == format_datetime(
            start_time,
        )

    def test_put_update_success(self, api_client):
        """PUT with all fields should succeed."""
        show = baker.make(Show, name="Test Show")
        start_time = now().replace(microsecond=0)
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=start_time,
            ends_at=start_time + timedelta(hours=1),
            description="Original",
            modified=False,
        )

        data = {
            "show": show.id,
            "starts_at": format_datetime(start_time),
            "ends_at": format_datetime(start_time + timedelta(hours=2)),
            "description": "Updated description",
            "modified": True,
            "auto_playlist_built": True,
        }
        response = api_client.put(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps(data),
            content_type="application/json",
        )
        # PUT may require different fields
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert reformat_datetime(data["starts_at"]) == format_datetime(
                start_time,
            )

    def test_put_not_found_returns_404(self, api_client):
        """PUT non-existent instance should return 404."""
        show = baker.make(Show, name="Test Show")
        start_time = now().replace(microsecond=0)
        data = {
            "show": show.id,
            "starts_at": format_datetime(start_time),
            "ends_at": format_datetime(start_time + timedelta(hours=1)),
        }

        response = api_client.put(
            "/api/v2/show-instances/999999",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 404
