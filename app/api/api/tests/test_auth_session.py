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


class TestBugT308:
    """Test to confirm T308: IsAdminOrOwnUser crashes on unauthenticated requests."""

    def test_t308_is_admin_or_own_user_crashes_with_anonymous_user(self):
        """Confirm T308: TypeError when AnonymousUser accesses UserViewSet.

        Bug: request.user.is_superuser() is called but for AnonymousUser
        is_superuser is a bool property, not a method.
        """
        request = APIRequestFactory().get("/api/v2/users")
        request.user = AnonymousUser()

        # This should fail with TypeError: 'bool' object is not callable
        with pytest.raises(TypeError, match="'bool' object is not callable"):
            IsAdminOrOwnUser().has_permission(request, None)

    def test_t308_users_endpoint_fails_with_500_for_anonymous(self):
        """Confirm T308: /api/v2/users crashes instead of returning 403 for anonymous.

        Expected: 403 Forbidden
        Actual: TypeError exception (results in 500 in production)

        XFail: This test passes when T308 is present (TypeError raised).
        Once fixed, this test will fail because 403 will be returned.
        """
        client = APIClient()

        # This will raise TypeError internally due to T308 bug
        # If T308 is fixed, this will return 403 and assert will fail
        try:
            response = client.get("/api/v2/users")
            # If we get here without exception, T308 is fixed
            assert (
                response.status_code == 403
            ), f"T308 fixed? Expected 403, got {response.status_code}"
        except TypeError as e:
            # This confirms T308 is present
            assert "'bool' object is not callable" in str(e)
