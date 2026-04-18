"""Tests for ShowInstances DELETE endpoint (T218)."""

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowInstance


@pytest.mark.django_db(transaction=True)
class TestShowInstanceViewSetDelete:
    """Test ShowInstances DELETE endpoint - DELETE /api/v2/show-instances/{id}."""

    def setup_method(self):
        """Clean up instances before each test."""
        ShowInstance.objects.all().delete()
        Show.objects.all().delete()

    def test_delete_instance_success_returns_204(self, admin_client):
        """DELETE should return 204 on successful deletion."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )

        response = admin_client.delete(f"/api/v2/show-instances/{instance.id}")
        assert response.status_code == 204

    def test_delete_instance_removes_from_db(self, admin_client):
        """DELETE should remove instance from database."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )

        admin_client.delete(f"/api/v2/show-instances/{instance.id}")
        assert ShowInstance.objects.filter(id=instance.id).count() == 0

    def test_delete_instance_not_found_returns_404(self, admin_client):
        """DELETE non-existent instance should return 404."""
        response = admin_client.delete("/api/v2/show-instances/999999")
        assert response.status_code == 404

    def test_delete_instance_no_auth_fails(self, client):
        """DELETE without auth should return 403."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )

        response = client.delete(f"/api/v2/show-instances/{instance.id}")
        assert response.status_code == 403

    def test_delete_instance_double_delete_returns_404(self, admin_client):
        """DELETE already deleted instance should return 404."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )

        admin_client.delete(f"/api/v2/show-instances/{instance.id}")
        response = admin_client.delete(f"/api/v2/show-instances/{instance.id}")
        assert response.status_code == 404

    def test_delete_instance_returns_empty_body(self, admin_client):
        """DELETE should return empty response body."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
        )

        response = admin_client.delete(f"/api/v2/show-instances/{instance.id}")
        assert response.content == b""

    def test_delete_single_instance_others_remain(self, admin_client):
        """DELETE single instance should leave other instances."""
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
        instance3 = baker.make(
            ShowInstance,
            show=show,
            starts_at=now() + timedelta(days=2),
            ends_at=now() + timedelta(days=2, hours=1),
        )

        admin_client.delete(f"/api/v2/show-instances/{instance2.id}")

        assert ShowInstance.objects.filter(id=instance1.id).exists()
        assert not ShowInstance.objects.filter(id=instance2.id).exists()
        assert ShowInstance.objects.filter(id=instance3.id).exists()

    def test_delete_instance_modified_flag(self, admin_client):
        """DELETE should work regardless of modified flag."""
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

        response = admin_client.delete(f"/api/v2/show-instances/{instance.id}")
        assert response.status_code == 204

    def test_delete_instance_with_description(self, admin_client):
        """DELETE should work with instances that have descriptions."""
        from datetime import timedelta

        from sdk import now

        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=now(),
            ends_at=now() + timedelta(hours=1),
            description="Special episode description",
        )

        response = admin_client.delete(f"/api/v2/show-instances/{instance.id}")
        assert response.status_code == 204

    def test_delete_instance_with_filled_time(self, admin_client):
        """DELETE should work with instances that have filled_time."""
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

        response = admin_client.delete(f"/api/v2/show-instances/{instance.id}")
        assert response.status_code == 204

    def test_delete_instance_with_record_enabled(self, admin_client):
        """DELETE should work with instances that have record_enabled."""
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

        response = admin_client.delete(f"/api/v2/show-instances/{instance.id}")
        assert response.status_code == 204

    def test_delete_instance_id_zero_returns_404(self, admin_client):
        """DELETE with id=0 should return 404."""
        response = admin_client.delete("/api/v2/show-instances/0")
        assert response.status_code == 404

    def test_delete_instance_negative_id_returns_404(self, admin_client):
        """DELETE with negative id should return 404."""
        response = admin_client.delete("/api/v2/show-instances/-1")
        assert response.status_code == 404

    def test_delete_instance_sql_injection_attempt(self, admin_client):
        """DELETE with SQL injection in id should be handled safely."""
        response = admin_client.delete("/api/v2/show-instances/1 OR 1=1")
        assert response.status_code == 404
