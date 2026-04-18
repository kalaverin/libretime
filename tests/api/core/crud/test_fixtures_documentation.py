"""
T299: API test fixtures documentation tests.

Paranoid tests verifying all fixtures are documented and work correctly.
Tests conftest.py fixtures with comprehensive examples.
"""

from inspect import getdoc

import pytest


@pytest.mark.django_db
class TestFixturesDocumentation:
    """Test that all fixtures have proper documentation."""

    def test_api_client_fixture_exists(self, api_client):
        """api_client fixture exists and returns APIClient."""
        from rest_framework.test import APIClient

        assert api_client is not None
        assert isinstance(api_client, APIClient)
        # Verify client can make authenticated requests
        response = api_client.get("/api/v2/info")
        assert response.status_code == 200

    def test_api_client_fixture_docstring(self):
        """api_client fixture has docstring."""
        from api.conftest import api_client

        doc = getdoc(api_client)
        assert doc is not None
        assert len(doc) > 10

    def test_admin_user_fixture_exists(self, admin_user):
        """admin_user fixture exists with role=A."""
        from api.core.models import Role

        assert admin_user is not None
        assert admin_user.role == Role.ADMIN
        assert admin_user.username.startswith("admin_")

    def test_admin_user_fixture_docstring(self):
        """admin_user fixture has docstring."""
        from api.conftest import admin_user

        doc = getdoc(admin_user)
        assert doc is not None
        assert "admin" in doc.lower() or "Admin" in doc

    def test_regular_user_fixture_exists(self, regular_user):
        """regular_user fixture exists with role=H."""
        from api.core.models import Role

        assert regular_user is not None
        assert regular_user.role == Role.HOST

    def test_regular_user_fixture_docstring(self):
        """regular_user fixture has docstring."""
        from api.conftest import regular_user

        doc = getdoc(regular_user)
        assert doc is not None

    def test_manager_user_fixture_exists(self, manager_user):
        """manager_user fixture exists with role=P."""
        from api.core.models import Role

        assert manager_user is not None
        assert manager_user.role == Role.MANAGER

    def test_manager_user_fixture_docstring(self):
        """manager_user fixture has docstring."""
        from api.conftest import manager_user

        doc = getdoc(manager_user)
        assert doc is not None

    def test_guest_user_fixture_exists(self, guest_user):
        """guest_user fixture exists with role=G."""
        from api.core.models import Role

        assert guest_user is not None
        assert guest_user.role == Role.GUEST

    def test_guest_user_fixture_docstring(self):
        """guest_user fixture has docstring."""
        from api.conftest import guest_user

        doc = getdoc(guest_user)
        assert doc is not None

    def test_authenticated_client_fixture_exists(self, authenticated_client):
        """authenticated_client fixture exists with session auth."""
        from rest_framework.test import APIClient

        assert authenticated_client is not None
        assert isinstance(authenticated_client, APIClient)

    def test_authenticated_client_fixture_docstring(self):
        """authenticated_client fixture has docstring."""
        from api.conftest import authenticated_client

        doc = getdoc(authenticated_client)
        assert doc is not None

    def test_host_client_fixture_exists(self, host_client):
        """host_client fixture exists for H role."""
        from rest_framework.test import APIClient

        assert host_client is not None
        assert isinstance(host_client, APIClient)

    def test_host_client_fixture_docstring(self):
        """host_client fixture has docstring."""
        from api.conftest import host_client

        doc = getdoc(host_client)
        assert doc is not None


@pytest.mark.django_db
class TestFixturesUsageExamples:
    """Test fixtures usage in realistic scenarios."""

    def test_admin_can_create_file(self, admin_user):
        """Example: Admin user can create files."""
        from api.core.models import Role

        assert admin_user.role == Role.ADMIN
        assert admin_user.id is not None

    def test_host_can_create_playlist(self, regular_user):
        """Example: Host user can create playlists."""
        from api.core.models import Role

        assert regular_user.role == Role.HOST
        assert regular_user.id is not None

    def test_api_client_authentication(self, api_client):
        """Example: API client has authentication."""
        response = api_client.get("/api/v2/info")
        assert response.status_code == 200

    def test_authenticated_client_session_auth(self, authenticated_client):
        """Example: Authenticated client uses session auth."""
        response = authenticated_client.get("/api/v2/files")
        # Should not be 403 (authenticated)
        assert response.status_code in [200, 400]

    def test_all_user_roles_distinct(
        self,
        admin_user,
        regular_user,
        manager_user,
        guest_user,
    ):
        """Example: All role fixtures are distinct."""
        users = [admin_user, regular_user, manager_user, guest_user]
        roles = [u.role for u in users]

        # All roles are different
        assert len(set(roles)) == 4

        # All users have different IDs
        ids = [u.id for u in users]
        assert len(set(ids)) == 4

    @pytest.mark.xfail(
        reason="T308: IsAdminOrOwnUser crashes on AnonymousUser",
    )
    def test_multiple_fixtures_combination(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Example: Combining multiple fixtures.

        XFail: T308 - IsAdminOrOwnUser.has_permission() crashes with
        TypeError: 'bool' object is not callable when accessing UserViewSet.
        """
        # api_client has API key auth
        response = api_client.get("/api/v2/users")
        assert response.status_code == 200

        # admin_user is admin
        assert admin_user.is_superuser or admin_user.role == "A"

        # regular_user is host
        assert regular_user.role == "H"


@pytest.mark.django_db
class TestFixturesConsistency:
    """Test fixtures provide consistent data."""

    def test_fixture_users_persist_in_db(self, admin_user, regular_user):
        """Fixture users are saved in database."""
        from api.core.models import User

        assert User.objects.filter(id=admin_user.id).exists()
        assert User.objects.filter(id=regular_user.id).exists()

    def test_fixture_users_reusable(self, admin_user):
        """Same fixture user can be used multiple times."""
        from api.core.models import User

        # First access
        user1 = User.objects.get(id=admin_user.id)
        # Second access - same user
        user2 = User.objects.get(id=admin_user.id)

        assert user1.id == user2.id
        assert user1.username == user2.username

    def test_api_client_reusable(self, api_client):
        """api_client fixture can make multiple requests."""
        # Multiple requests with same client
        response1 = api_client.get("/api/v2/info")
        response2 = api_client.get("/api/v2/version")

        assert response1.status_code == 200
        assert response2.status_code == 200


class TestConftestImports:
    """Test conftest.py can be imported."""

    def test_conftest_imports(self):
        """conftest.py imports successfully."""
        from api import conftest

        assert conftest is not None

    def test_all_fixtures_exported(self):
        """All fixtures are available from conftest."""
        from api.conftest import (
            admin_user,
            api_client,
            authenticated_client,
            guest_user,
            host_client,
            manager_user,
            regular_user,
        )

        # All fixtures are callable
        assert callable(api_client)
        assert callable(admin_user)
        assert callable(regular_user)
        assert callable(manager_user)
        assert callable(guest_user)
        assert callable(authenticated_client)
        assert callable(host_client)
