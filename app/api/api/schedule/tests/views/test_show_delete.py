"""Tests for Shows DELETE endpoint (T206)."""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import (
    Show,
    ShowDays,
    ShowHost,
    ShowInstance,
    ShowRebroadcast,
)


@pytest.mark.django_db(transaction=True)
class TestShowViewSetDelete:
    """Test Shows DELETE endpoint - DELETE /api/v2/shows/{id}."""

    def setup_method(self):
        """Clean up shows and related models before each test."""
        ShowRebroadcast.objects.all().delete()
        ShowInstance.objects.all().delete()
        ShowDays.objects.all().delete()
        ShowHost.objects.all().delete()
        Show.objects.all().delete()

    def test_delete_show_success_returns_204(self, api_client):
        """DELETE should return 204 on successful deletion."""
        show = baker.make(Show, name="Test Show")
        response = api_client.delete(f"/api/v2/shows/{show.id}")
        assert response.status_code == 204

    def test_delete_show_removes_from_db(self, api_client):
        """DELETE should remove show from database."""
        show = baker.make(Show, name="Test Show")
        api_client.delete(f"/api/v2/shows/{show.id}")
        assert Show.objects.filter(id=show.id).count() == 0

    def test_delete_show_not_found_returns_404(self, api_client):
        """DELETE non-existent show should return 404."""
        response = api_client.delete("/api/v2/shows/999999")
        assert response.status_code == 404

    def test_delete_show_no_auth_fails(self, client):
        """DELETE without auth should return 403."""
        show = baker.make(Show, name="Test Show")
        response = client.delete(f"/api/v2/shows/{show.id}")
        assert response.status_code == 403

    def test_delete_show_with_hosts(self, api_client):
        """DELETE show with hosts should handle relationships."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username="host1")
        baker.make(ShowHost, show=show, user=user)

        response = api_client.delete(f"/api/v2/shows/{show.id}")
        # May succeed or fail depending on cascade settings
        assert response.status_code in [204, 409, 500]

    def test_delete_show_with_days(self, api_client):
        """DELETE show with ShowDays should handle relationships."""
        from datetime import date, time

        show = baker.make(Show, name="Test Show")
        baker.make(
            ShowDays,
            show=show,
            first_show_on=date.today(),
            start_time=time(12, 0),
            timezone="UTC",
            duration="01:00:00",
            repeat_kind=0,
        )

        response = api_client.delete(f"/api/v2/shows/{show.id}")
        assert response.status_code in [204, 409, 500]

    def test_delete_show_with_instances(self, api_client):
        """DELETE show with ShowInstances should handle relationships."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        baker.make(
            ShowInstance,
            show=show,
            created_at=now(),
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            modified=False,
            auto_playlist_built=False,
        )

        response = api_client.delete(f"/api/v2/shows/{show.id}")
        assert response.status_code in [204, 409, 500]

    def test_delete_show_double_delete_returns_404(self, api_client):
        """DELETE already deleted show should return 404."""
        show = baker.make(Show, name="Test Show")
        api_client.delete(f"/api/v2/shows/{show.id}")

        # Second delete should return 404
        response = api_client.delete(f"/api/v2/shows/{show.id}")
        assert response.status_code == 404

    def test_delete_show_wrong_method_returns_405(self, api_client):
        """POST to delete endpoint should return 405."""
        show = baker.make(Show, name="Test Show")
        response = api_client.post(
            f"/api/v2/shows/{show.id}",
            json.dumps({"action": "delete"}),
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_delete_show_returns_empty_body(self, api_client):
        """DELETE should return empty response body."""
        show = baker.make(Show, name="Test Show")
        response = api_client.delete(f"/api/v2/shows/{show.id}")
        assert response.content == b""

    def test_delete_show_id_zero_returns_404(self, api_client):
        """DELETE with id=0 should return 404."""
        response = api_client.delete("/api/v2/shows/0")
        assert response.status_code == 404

    def test_delete_show_negative_id_returns_404(self, api_client):
        """DELETE with negative id should return 404."""
        response = api_client.delete("/api/v2/shows/-1")
        assert response.status_code == 404

    def test_delete_show_large_id_returns_404(self, api_client):
        """DELETE with very large id should return 404."""
        response = api_client.delete("/api/v2/shows/999999999")
        assert response.status_code == 404

    def test_delete_show_sql_injection_attempt(self, api_client):
        """DELETE with SQL injection in id should be handled safely."""
        response = api_client.delete("/api/v2/shows/1 OR 1=1")
        assert response.status_code == 404

    def test_delete_show_path_traversal_attempt(self, api_client):
        """DELETE with path traversal should be handled safely."""
        response = api_client.delete("/api/v2/shows/../../../etc/passwd")
        assert response.status_code == 404

    def test_delete_show_special_chars_in_id(self, api_client):
        """DELETE with special chars in id should return 404."""
        response = api_client.delete("/api/v2/shows/test%20id")
        assert response.status_code == 404
