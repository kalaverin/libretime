"""Tests for ShowHosts DELETE endpoint (T222)."""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Show, ShowHost


@pytest.mark.django_db(transaction=True)
class TestShowHostViewSetDelete:
    """Test ShowHosts DELETE endpoint - DELETE /api/v2/show-hosts/{id}."""

    def setup_method(self):
        """Clean up show hosts before each test."""
        ShowHost.objects.all().delete()
        Show.objects.all().delete()
        User.objects.filter(username__startswith="testhost").delete()

    def test_delete_show_host_success_returns_204(self, guest_client):
        """DELETE should return 204 on successful removal."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username="testhost1")
        show_host = baker.make(ShowHost, show=show, user=user)

        response = guest_client.delete(f"/api/v2/show-hosts/{show_host.id}")
        assert response.status_code == 204

    def test_delete_show_host_removes_from_db(self, guest_client):
        """DELETE should remove show host from database."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username="testhost1")
        show_host = baker.make(ShowHost, show=show, user=user)

        guest_client.delete(f"/api/v2/show-hosts/{show_host.id}")
        assert ShowHost.objects.filter(id=show_host.id).count() == 0

    def test_delete_show_host_not_found_returns_404(self, guest_client):
        """DELETE non-existent show host should return 404."""
        response = guest_client.delete("/api/v2/show-hosts/999999")
        assert response.status_code == 404

    def test_delete_show_host_no_auth_fails(self, client):
        """DELETE without auth should return 403."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username="testhost1")
        show_host = baker.make(ShowHost, show=show, user=user)

        response = client.delete(f"/api/v2/show-hosts/{show_host.id}")
        assert response.status_code == 403

    def test_delete_show_host_double_delete_returns_404(self, guest_client):
        """DELETE already deleted show host should return 404."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username="testhost1")
        show_host = baker.make(ShowHost, show=show, user=user)

        guest_client.delete(f"/api/v2/show-hosts/{show_host.id}")
        response = guest_client.delete(f"/api/v2/show-hosts/{show_host.id}")
        assert response.status_code == 404

    def test_delete_show_host_returns_empty_body(self, guest_client):
        """DELETE should return empty response body."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username="testhost1")
        show_host = baker.make(ShowHost, show=show, user=user)

        response = guest_client.delete(f"/api/v2/show-hosts/{show_host.id}")
        assert response.content == b""

    def test_delete_one_host_others_remain(self, guest_client):
        """DELETE one host should leave other hosts."""
        show = baker.make(Show, name="Test Show")
        user1 = baker.make(User, username="testhost1")
        user2 = baker.make(User, username="testhost2")
        user3 = baker.make(User, username="testhost3")

        show_host1 = baker.make(ShowHost, show=show, user=user1)
        show_host2 = baker.make(ShowHost, show=show, user=user2)
        show_host3 = baker.make(ShowHost, show=show, user=user3)

        guest_client.delete(f"/api/v2/show-hosts/{show_host2.id}")

        assert ShowHost.objects.filter(id=show_host1.id).exists()
        assert not ShowHost.objects.filter(id=show_host2.id).exists()
        assert ShowHost.objects.filter(id=show_host3.id).exists()

    def test_delete_host_from_one_show_keeps_other_shows(self, guest_client):
        """DELETE host from one show should keep host on other shows."""
        user = baker.make(User, username="testhost1")
        show1 = baker.make(Show, name="Show 1")
        show2 = baker.make(Show, name="Show 2")
        show3 = baker.make(Show, name="Show 3")

        show_host1 = baker.make(ShowHost, show=show1, user=user)
        show_host2 = baker.make(ShowHost, show=show2, user=user)
        show_host3 = baker.make(ShowHost, show=show3, user=user)

        guest_client.delete(f"/api/v2/show-hosts/{show_host2.id}")

        assert ShowHost.objects.filter(id=show_host1.id).exists()
        assert not ShowHost.objects.filter(id=show_host2.id).exists()
        assert ShowHost.objects.filter(id=show_host3.id).exists()

    def test_delete_show_host_id_zero_returns_404(self, guest_client):
        """DELETE with id=0 should return 404."""
        response = guest_client.delete("/api/v2/show-hosts/0")
        assert response.status_code == 404

    def test_delete_show_host_negative_id_returns_404(self, guest_client):
        """DELETE with negative id should return 404."""
        response = guest_client.delete("/api/v2/show-hosts/-1")
        assert response.status_code == 404

    def test_delete_show_host_sql_injection_attempt(self, guest_client):
        """DELETE with SQL injection in id should be handled safely."""
        response = guest_client.delete("/api/v2/show-hosts/1 OR 1=1")
        assert response.status_code == 404
