"""
Role-based testing fixtures for LibreTime permission system.

Provides users with specific roles and authenticated clients for each role.
"""

import pytest
from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role


# =============================================================================
# Session-only authenticated clients (no API-Key)
# =============================================================================

from rest_framework.test import APIClient


@pytest.fixture
def session_client() -> "APIClient":
    """API client without API-Key (for session-based auth testing)."""
    return APIClient()


# =============================================================================
# Role-based User Fixtures
# =============================================================================


@pytest.fixture
def guest_user(faker) -> User:
    """Create a user with GUEST role (read-only)."""
    return baker.make(
        User,
        username=f"guest_{faker.user_name()}_{faker.uuid4()[:8]}",
        email=f"guest_{faker.uuid4()[:8]}@test.com",
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        role=Role.GUEST,
    )


@pytest.fixture
def host_user(faker) -> User:
    """Create a user with HOST role (can create and modify own content)."""
    return baker.make(
        User,
        username=f"host_{faker.user_name()}_{faker.uuid4()[:8]}",
        email=f"host_{faker.uuid4()[:8]}@test.com",
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        role=Role.HOST,
    )


@pytest.fixture
def manager_user(faker) -> User:
    """Create a user with MANAGER role (can CRUD all content)."""
    return baker.make(
        User,
        username=f"manager_{faker.user_name()}_{faker.uuid4()[:8]}",
        email=f"manager_{faker.uuid4()[:8]}@test.com",
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        role=Role.MANAGER,
    )


@pytest.fixture
def admin_user(faker) -> User:
    """Create a user with ADMIN role (superuser)."""
    user = baker.make(
        User,
        username=f"admin_{faker.user_name()}_{faker.uuid4()[:8]}",
        email=f"admin_{faker.uuid4()[:8]}@test.com",
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        role=Role.ADMIN,
    )
    # Promote to superuser for admin privileges
    user.is_superuser = True
    user.save()
    return user


# =============================================================================
# Role-based Authenticated Client Fixtures
# =============================================================================


@pytest.fixture
def guest_client(session_client, guest_user) -> "APIClient":
    """API client authenticated as GUEST user."""
    session_client.force_authenticate(user=guest_user)
    return session_client


@pytest.fixture
def host_client(session_client, host_user) -> "APIClient":
    """API client authenticated as HOST user."""
    session_client.force_authenticate(user=host_user)
    return session_client


@pytest.fixture
def manager_client(session_client, manager_user) -> "APIClient":
    """API client authenticated as MANAGER user."""
    session_client.force_authenticate(user=manager_user)
    return session_client


@pytest.fixture
def admin_client(session_client, admin_user) -> "APIClient":
    """API client authenticated as ADMIN user."""
    session_client.force_authenticate(user=admin_user)
    return session_client


# =============================================================================
# Multi-User Fixtures for Cross-User Testing
# =============================================================================


@pytest.fixture
def two_host_users(faker) -> tuple[User, User]:
    """Create two HOST users for testing own_* permissions."""
    host1 = baker.make(
        User,
        username=f"host1_{faker.user_name()}_{faker.uuid4()[:8]}",
        email=f"host1_{faker.uuid4()[:8]}@test.com",
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        role=Role.HOST,
    )
    host2 = baker.make(
        User,
        username=f"host2_{faker.user_name()}_{faker.uuid4()[:8]}",
        email=f"host2_{faker.uuid4()[:8]}@test.com",
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        role=Role.HOST,
    )
    return host1, host2


@pytest.fixture
def host_and_guest_users(faker) -> tuple[User, User]:
    """Create HOST and GUEST users for permission comparison."""
    host = baker.make(
        User,
        username=f"host_{faker.user_name()}_{faker.uuid4()[:8]}",
        email=f"host_{faker.uuid4()[:8]}@test.com",
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        role=Role.HOST,
    )
    guest = baker.make(
        User,
        username=f"guest_{faker.user_name()}_{faker.uuid4()[:8]}",
        email=f"guest_{faker.uuid4()[:8]}@test.com",
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        role=Role.GUEST,
    )
    return host, guest


@pytest.fixture
def host_and_manager_users(faker) -> tuple[User, User]:
    """Create HOST and MANAGER users for cross-role testing."""
    host = baker.make(
        User,
        username=f"host_{faker.user_name()}_{faker.uuid4()[:8]}",
        email=f"host_{faker.uuid4()[:8]}@test.com",
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        role=Role.HOST,
    )
    manager = baker.make(
        User,
        username=f"manager_{faker.user_name()}_{faker.uuid4()[:8]}",
        email=f"manager_{faker.uuid4()[:8]}@test.com",
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        role=Role.MANAGER,
    )
    return host, manager
