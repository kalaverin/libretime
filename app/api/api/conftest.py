"""
API v2 test fixtures and utilities.

Provides authentication clients and user fixtures for API contract testing.
Tests must pass on both Django REST Framework and future FastAPI implementation.
"""

import pytest
from django.conf import settings
from model_bakery import baker
from rest_framework.test import APIClient

from api.core.models.role import Role
from api.core.models.user import User


@pytest.fixture
def api_client() -> APIClient:
    """
    API client authenticated with service Api-Key.
    Use for testing service-to-service communication (liquidsoap, etc.).
    """
    obj = APIClient()
    obj.credentials(
        HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
    )
    return obj


@pytest.fixture
def admin_user() -> User:
    """Admin user (role=A) with full permissions."""
    return baker.make(
        User,
        role=Role.ADMIN,
        username="admin_test",
        email="admin@test.com",
        first_name="Admin",
        last_name="Test",
    )


@pytest.fixture
def regular_user() -> User:
    """Regular host user (role=H) with standard permissions."""
    return baker.make(
        User,
        role=Role.HOST,
        username="host_test",
        email="host@test.com",
        first_name="Host",
        last_name="Test",
    )


@pytest.fixture
def manager_user() -> User:
    """Manager user (role=P) with elevated permissions."""
    return baker.make(
        User,
        role=Role.MANAGER,
        username="manager_test",
        email="manager@test.com",
        first_name="Manager",
        last_name="Test",
    )


@pytest.fixture
def guest_user() -> User:
    """Guest user (role=G) with minimal permissions."""
    return baker.make(
        User,
        role=Role.GUEST,
        username="guest_test",
        email="guest@test.com",
        first_name="Guest",
        last_name="Test",
    )


@pytest.fixture
def authenticated_client(admin_user: User) -> APIClient:
    """
    API client authenticated as admin user via session.
    Use for testing user-facing endpoints.
    """
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def host_client(regular_user: User) -> APIClient:
    """
    API client authenticated as regular host user.
    Use for testing host-specific permissions.
    """
    client = APIClient()
    client.force_authenticate(user=regular_user)
    return client


@pytest.fixture
def manager_client(manager_user: User) -> APIClient:
    """
    API client authenticated as manager user.
    Use for testing manager-specific permissions.
    """
    client = APIClient()
    client.force_authenticate(user=manager_user)
    return client


@pytest.fixture
def guest_client(guest_user: User) -> APIClient:
    """
    API client authenticated as guest user.
    Use for testing guest-specific permissions.
    """
    client = APIClient()
    client.force_authenticate(user=guest_user)
    return client
