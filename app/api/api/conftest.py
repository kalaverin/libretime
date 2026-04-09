"""
API v2 test fixtures and utilities.
"""

import pytest
from django.conf import settings
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    """API client with Api-Key auth."""
    obj = APIClient()
    obj.credentials(
        HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
    )
    return obj


@pytest.fixture
def admin_user():
    """Admin user (role=A)."""
    from api.core.models.role import Role
    from api.core.models.user import User
    return User.objects.create_user(
        role=Role.ADMIN, username="admin_test", password="test",
        email="admin@test.com", first_name="Admin", last_name="Test",
    )


@pytest.fixture
def regular_user():
    """Host user (role=H)."""
    from api.core.models.role import Role
    from api.core.models.user import User
    return User.objects.create_user(
        role=Role.HOST, username="host_test", password="test",
        email="host@test.com", first_name="Host", last_name="Test",
    )


@pytest.fixture
def manager_user():
    """Manager user (role=P)."""
    from api.core.models.role import Role
    from api.core.models.user import User
    return User.objects.create_user(
        role=Role.MANAGER, username="manager_test", password="test",
        email="manager@test.com", first_name="Manager", last_name="Test",
    )


@pytest.fixture
def guest_user():
    """Guest user (role=G)."""
    from api.core.models.role import Role
    from api.core.models.user import User
    return User.objects.create_user(
        role=Role.GUEST, username="guest_test", password="test",
        email="guest@test.com", first_name="Guest", last_name="Test",
    )


@pytest.fixture
def authenticated_client(admin_user) -> APIClient:
    """Session auth as admin."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def host_client(regular_user) -> APIClient:
    """Session auth as host."""
    client = APIClient()
    client.force_authenticate(user=regular_user)
    return client
