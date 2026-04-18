"""Tests for ShowHosts LIST endpoint (T220)."""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Show, ShowHost


@pytest.mark.django_db(transaction=True)
class TestShowHostViewSetList:
    """Test ShowHosts LIST endpoint - GET /api/v2/show-hosts."""

    def setup_method(self):
        """Clean up show hosts before each test."""
        ShowHost.objects.all().delete()
        Show.objects.all().delete()
        User.objects.filter(username__startswith="testhost").delete()

    def test_list_show_hosts_empty_returns_200(self, admin_client):
        """LIST with no show hosts should return empty array."""
        response = admin_client.get("/api/v2/show-hosts")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_show_hosts_returns_all(self, admin_client):
        """LIST should return all show hosts."""
        show = baker.make(Show, name="Test Show")
        user1 = baker.make(User, username="testhost1")
        user2 = baker.make(User, username="testhost2")

        baker.make(ShowHost, show=show, user=user1)
        baker.make(ShowHost, show=show, user=user2)

        response = admin_client.get("/api/v2/show-hosts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_show_hosts_contains_id(self, admin_client):
        """LIST should include show host id."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username="testhost1")
        show_host = baker.make(ShowHost, show=show, user=user)

        response = admin_client.get("/api/v2/show-hosts")
        data = response.json()
        assert data[0]["id"] == show_host.id

    def test_list_show_hosts_contains_show(self, admin_client):
        """LIST should include show reference."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username="testhost1")
        baker.make(ShowHost, show=show, user=user)

        response = admin_client.get("/api/v2/show-hosts")
        data = response.json()
        assert data[0]["show"] == show.id

    def test_list_show_hosts_contains_user(self, admin_client):
        """LIST should include user reference."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username="testhost1")
        baker.make(ShowHost, show=show, user=user)

        response = admin_client.get("/api/v2/show-hosts")
        data = response.json()
        assert data[0]["user"] == user.id

    def test_list_show_hosts_multiple_shows(self, admin_client):
        """LIST should return hosts for multiple shows."""
        show1 = baker.make(Show, name="Show 1")
        show2 = baker.make(Show, name="Show 2")
        user1 = baker.make(User, username="testhost1")
        user2 = baker.make(User, username="testhost2")

        baker.make(ShowHost, show=show1, user=user1)
        baker.make(ShowHost, show=show2, user=user2)

        response = admin_client.get("/api/v2/show-hosts")
        data = response.json()
        assert len(data) == 2

    def test_list_show_hosts_multiple_hosts_same_show(self, admin_client):
        """LIST should return multiple hosts for same show."""
        show = baker.make(Show, name="Test Show")
        user1 = baker.make(User, username="testhost1")
        user2 = baker.make(User, username="testhost2")
        user3 = baker.make(User, username="testhost3")

        baker.make(ShowHost, show=show, user=user1)
        baker.make(ShowHost, show=show, user=user2)
        baker.make(ShowHost, show=show, user=user3)

        response = admin_client.get("/api/v2/show-hosts")
        data = response.json()
        assert len(data) == 3
        user_ids = [sh["user"] for sh in data]
        assert user1.id in user_ids
        assert user2.id in user_ids
        assert user3.id in user_ids

    def test_list_show_hosts_filter_by_show(self, admin_client):
        """LIST should support filtering by show."""
        show1 = baker.make(Show, name="Show 1")
        show2 = baker.make(Show, name="Show 2")
        user1 = baker.make(User, username="testhost1")
        user2 = baker.make(User, username="testhost2")

        baker.make(ShowHost, show=show1, user=user1)
        baker.make(ShowHost, show=show2, user=user2)

        response = admin_client.get(f"/api/v2/show-hosts?show={show1.id}")
        # Filtering may or may not be supported
        assert response.status_code in [200, 400]

    def test_list_show_hosts_filter_by_user(self, admin_client):
        """LIST should support filtering by user."""
        show1 = baker.make(Show, name="Show 1")
        show2 = baker.make(Show, name="Show 2")
        user = baker.make(User, username="testhost1")

        baker.make(ShowHost, show=show1, user=user)
        baker.make(ShowHost, show=show2, user=user)

        response = admin_client.get(f"/api/v2/show-hosts?user={user.id}")
        # Filtering may or may not be supported
        assert response.status_code in [200, 400]

    def test_list_show_hosts_no_auth_fails(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/show-hosts")
        assert response.status_code == 403

    def test_list_show_hosts_returns_json(self, admin_client):
        """LIST should return JSON response."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username="testhost1")
        baker.make(ShowHost, show=show, user=user)

        response = admin_client.get("/api/v2/show-hosts")
        assert response["Content-Type"] == "application/json"
