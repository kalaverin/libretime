"""Tests for ShowHosts CREATE endpoint (T221)."""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Show, ShowHost


@pytest.mark.django_db(transaction=True)
class TestShowHostViewSetCreate:
    """Test ShowHosts CREATE endpoint - POST /api/v2/show-hosts."""

    def setup_method(self):
        """Clean up show hosts before each test."""
        ShowHost.objects.all().delete()
        Show.objects.all().delete()
        User.objects.filter(username__startswith="testhost").delete()

    def test_create_show_host_success(self, admin_client):
        """CREATE show host should succeed."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username="testhost1")

        data = {
            "show": show.id,
            "user": user.id,
        }
        response = admin_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["show"] == show.id
        assert response.json()["user"] == user.id

    def test_create_show_host_multiple_hosts(self, admin_client):
        """CREATE multiple hosts for same show should succeed."""
        show = baker.make(Show, name="Test Show")

        for i in range(3):
            user = baker.make(User, username=f"testhost{i}")
            data = {
                "show": show.id,
                "user": user.id,
            }
            response = admin_client.post(
                "/api/v2/show-hosts",
                json.dumps(data),
                content_type="application/json",
            )
            assert response.status_code == 201

        assert ShowHost.objects.filter(show=show).count() == 3

    def test_create_show_host_same_user_multiple_shows(self, admin_client):
        """CREATE same user as host for multiple shows should succeed."""
        user = baker.make(User, username="testhost1")

        for i in range(3):
            show = baker.make(Show, name=f"Show {i}")
            data = {
                "show": show.id,
                "user": user.id,
            }
            response = admin_client.post(
                "/api/v2/show-hosts",
                json.dumps(data),
                content_type="application/json",
            )
            assert response.status_code == 201

        assert ShowHost.objects.filter(user=user).count() == 3

    @pytest.mark.xfail(
        reason="BUG T320: Duplicate show-host entries allowed - no unique constraint",
    )
    def test_create_show_host_duplicate_fails(self, admin_client):
        """CREATE duplicate show-host should fail."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username="testhost1")

        # First create
        data = {
            "show": show.id,
            "user": user.id,
        }
        admin_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )

        # Second create should fail but doesn't
        response = admin_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            400,
            409,
        ]  # Should fail but returns 201

    def test_create_show_host_missing_show_fails(self, admin_client):
        """CREATE without show should fail."""
        user = baker.make(User, username="testhost1")

        data = {
            "user": user.id,
        }
        response = admin_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_host_missing_user_fails(self, admin_client):
        """CREATE without user should fail."""
        show = baker.make(Show, name="Test Show")

        data = {
            "show": show.id,
        }
        response = admin_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_host_invalid_show_fails(self, admin_client):
        """CREATE with invalid show should fail."""
        user = baker.make(User, username="testhost1")

        data = {
            "show": 999999,
            "user": user.id,
        }
        response = admin_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_host_invalid_user_fails(self, admin_client):
        """CREATE with invalid user should fail."""
        show = baker.make(Show, name="Test Show")

        data = {
            "show": show.id,
            "user": 999999,
        }
        response = admin_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_show_host_returns_json(self, admin_client):
        """CREATE should return JSON response."""
        show = baker.make(Show, name="Test Show")
        user = baker.make(User, username="testhost1")

        data = {
            "show": show.id,
            "user": user.id,
        }
        response = admin_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response["Content-Type"] == "application/json"

    def test_create_show_host_no_auth_fails(self, client):
        """CREATE without auth should return 403."""
        data = {"show": 1, "user": 1}
        response = client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 403
