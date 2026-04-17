"""
T279: Session authentication tests.

Tests for Django REST Framework session-based authentication.
"""

import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIClient, APIRequestFactory

from api.core.models import Role
from api.permissions import IsAdminOrOwnUser


@pytest.mark.django_db
class TestSessionAuth:
    """Test session-based authentication for protected endpoints."""

    PROTECTED_ENDPOINTS = [
        "/api/v2/users",
        "/api/v2/files",
        "/api/v2/libraries",
        "/api/v2/shows",
        "/api/v2/playlists",
    ]

    @pytest.mark.xfail(
        reason="T308: IsAdminOrOwnUser crashes on AnonymousUser",
    )
    def test_unauthenticated_user_cannot_access_protected_endpoints(self):
        """Unauthenticated user should receive 403.

        XFail: T308 - IsAdminOrOwnUser.has_permission() crashes with
        TypeError: 'bool' object is not callable when unauthenticated
        user accesses UserViewSet. Expected 403, got 500.
        """
        client = APIClient()

        for endpoint in self.PROTECTED_ENDPOINTS:
            response = client.get(endpoint)
            assert (
                response.status_code == 403
            ), f"Expected 403 for {endpoint}, got {response.status_code}"

    def test_authenticated_user_can_access_protected_endpoints(
        self,
        admin_user,
    ):
        """Authenticated user should receive 200."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        for endpoint in self.PROTECTED_ENDPOINTS:
            response = client.get(endpoint)
            assert (
                response.status_code == 200
            ), f"Expected 200 for {endpoint}, got {response.status_code}"

    def test_session_login_logout_flow(self):
        """Test complete login/logout flow with session auth."""
        User = get_user_model()
        user = User.objects.create_user(
            role=Role.HOST,
            username="session_test_user",
            password="testpassword123",
            email="session@test.com",
            first_name="Session",
            last_name="Test",
        )

        client = APIClient()

        # Before login - should be 403
        response = client.get("/api/v2/files")
        assert response.status_code == 403

        # Login using Django test client login
        logged_in = client.login(
            username="session_test_user",
            password="testpassword123",
        )
        assert logged_in is True

        # After login - should be 200
        response = client.get("/api/v2/files")
        assert response.status_code == 200

        # Logout
        client.logout()

        # After logout - should be 403 again
        response = client.get("/api/v2/files")
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "role",
        [Role.ADMIN, Role.HOST, Role.MANAGER, Role.GUEST],
    )
    def test_all_roles_can_access_with_session_auth(self, role):
        """All user roles should work with session auth."""
        User = get_user_model()
        user = User.objects.create_user(
            role=role,
            username=f"session_user_{role}",
            password="testpass123",
            email=f"{role}@test.com",
            first_name="Test",
            last_name="User",
        )

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v2/files")
        assert (
            response.status_code == 200
        ), f"Role {role} should access files endpoint"

    @pytest.mark.xfail(
        reason="T308: IsAdminOrOwnUser crashes on AnonymousUser",
    )
    def test_session_auth_with_invalid_credentials(self):
        """Invalid login credentials should fail.

        XFail: T308 - Also affected by T308 crash on unauthenticated access.
        """
        User = get_user_model()
        User.objects.create_user(
            role=Role.GUEST,
            username="valid_user",
            password="correct_password",
            email="valid@test.com",
        )

        client = APIClient()

        # Try login with wrong password
        logged_in = client.login(
            username="valid_user",
            password="wrong_password",
        )
        assert logged_in is False

        # Should still be 403
        response = client.get("/api/v2/files")
        assert response.status_code == 403

    def test_session_auth_nonexistent_user(self):
        """Login with non-existent user should fail."""
        client = APIClient()

        logged_in = client.login(
            username="nonexistent_user",
            password="any_password",
        )
        assert logged_in is False

        response = client.get("/api/v2/files")
        assert response.status_code == 403


class TestIsAdminOrOwnUserPermission:
    """Tests for IsAdminOrOwnUser permission class."""

    def test_anonymous_user_denied(self):
        """AnonymousUser is denied permission (returns False, not TypeError)."""
        request = APIRequestFactory().get("/api/v2/users")
        request.user = AnonymousUser()

        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is False

    def test_unauthenticated_request_returns_403(self):
        """Unauthenticated request to /api/v2/users returns 403."""
        client = APIClient()
        response = client.get("/api/v2/users")
        assert response.status_code == 403

    def test_has_object_permission_anonymous_denied(self):
        """AnonymousUser is denied object permission."""
        request = APIRequestFactory().get("/api/v2/users/1")
        request.user = AnonymousUser()

        # Mock object with username
        obj = type("MockUser", (), {"username": "testuser"})()

        result = IsAdminOrOwnUser().has_object_permission(request, None, obj)
        assert result is False

    @pytest.mark.django_db
    def test_admin_user_granted_permission(self, faker):
        """Admin user is granted permission."""
        from model_bakery import baker

        admin_user = baker.make(
            "core.User",
            role=Role.ADMIN,
            username=faker.user_name(),
            email=faker.fake_email(),
        )
        request = APIRequestFactory().get("/api/v2/users")
        request.user = admin_user

        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is True

    @pytest.mark.django_db
    def test_non_admin_user_denied_permission(self, faker):
        """Non-admin user is denied permission."""
        from model_bakery import baker

        host_user = baker.make(
            "core.User",
            role=Role.HOST,
            username=faker.user_name(),
            email=faker.fake_email(),
        )
        request = APIRequestFactory().get("/api/v2/users")
        request.user = host_user

        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is False

    @pytest.mark.django_db
    def test_has_object_permission_admin_granted(self, faker):
        """Admin is granted object permission regardless of ownership."""
        from model_bakery import baker

        admin_user = baker.make(
            "core.User",
            role=Role.ADMIN,
            username=faker.user_name(),
            email=faker.fake_email(),
        )
        request = APIRequestFactory().get("/api/v2/users/1")
        request.user = admin_user

        # Mock object with different username
        obj = type("MockUser", (), {"username": faker.user_name()})()

        result = IsAdminOrOwnUser().has_object_permission(request, None, obj)
        assert result is True

    @pytest.mark.django_db
    def test_has_object_permission_owner_granted(self, faker):
        """User is granted object permission for their own object."""
        from model_bakery import baker

        user = baker.make(
            "core.User",
            role=Role.HOST,
            username=faker.user_name(),
            email=faker.fake_email(),
        )
        request = APIRequestFactory().get("/api/v2/users/1")
        request.user = user

        # Mock object with same username - note: permissions.py compares obj.username == request.user
        obj = type("MockUser", (), {"username": user})()

        result = IsAdminOrOwnUser().has_object_permission(request, None, obj)
        assert result is True

    @pytest.mark.django_db
    def test_has_object_permission_non_owner_denied(self, faker):
        """User is denied object permission for other user's object."""
        from model_bakery import baker

        user = baker.make(
            "core.User",
            role=Role.HOST,
            username=faker.user_name(),
            email=faker.fake_email(),
        )
        request = APIRequestFactory().get("/api/v2/users/1")
        request.user = user

        # Mock object with different username
        obj = type("MockUser", (), {"username": faker.user_name()})()

        result = IsAdminOrOwnUser().has_object_permission(request, None, obj)
        assert result is False
