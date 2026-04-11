"""
Role-based testing fixtures for LibreTime permission system.

Provides users with specific roles and authenticated clients for each role.
"""

import pytest
from django.contrib.auth.management import create_permissions
from django.contrib.contenttypes.models import ContentType
from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role


def ensure_custom_permissions_exist():
    """Ensure custom 'own_*' permissions exist in the database.
    
    These permissions are not auto-created by Django because they're not
    standard CRUD permissions. We create them manually for HOST role.
    """
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    
    # Map of app_label -> models that need own_* permissions
    app_models = {
        'schedule': ['playlist', 'smartblock', 'webstream'],
        'podcasts': ['podcast', 'podcastepisode'],
        'storage': ['file'],
    }
    
    actions = ['change', 'delete']
    
    for app_label, models in app_models.items():
        for model_name in models:
            try:
                ct = ContentType.objects.get(app_label=app_label, model=model_name)
                for action in actions:
                    codename = f'{action}_own_{model_name}'
                    name = f'Can {action} own {model_name}'
                    Permission.objects.get_or_create(
                        codename=codename,
                        content_type=ct,
                        defaults={'name': name}
                    )
            except ContentType.DoesNotExist:
                pass  # Model doesn't exist, skip


def ensure_permissions_exist():
    """Ensure all permissions are created in the database."""
    from django.apps import apps
    # Create standard permissions for all apps
    for app_config in apps.get_app_configs():
        if hasattr(app_config, 'models_module'):
            create_permissions(app_config, verbosity=0)
    # Create custom own_* permissions
    ensure_custom_permissions_exist()





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
def guest_user(faker, db) -> User:
    """Create a user with GUEST role (read-only)."""
    ensure_permissions_exist()
    return baker.make(
        User,
        username=f"guest_{faker.user_name()}_{faker.uuid4()[:8]}",
        email=f"guest_{faker.uuid4()[:8]}@test.com",
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        role=Role.GUEST,
    )


@pytest.fixture
def host_user(faker, db) -> User:
    """Create a user with HOST role (can create and modify own content)."""
    ensure_permissions_exist()
    return baker.make(
        User,
        username=f"host_{faker.user_name()}_{faker.uuid4()[:8]}",
        email=f"host_{faker.uuid4()[:8]}@test.com",
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        role=Role.HOST,
    )


@pytest.fixture
def manager_user(faker, db) -> User:
    """Create a user with MANAGER role (can CRUD all content)."""
    ensure_permissions_exist()
    return baker.make(
        User,
        username=f"manager_{faker.user_name()}_{faker.uuid4()[:8]}",
        email=f"manager_{faker.uuid4()[:8]}@test.com",
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        role=Role.MANAGER,
    )


@pytest.fixture
def admin_user(faker, db) -> User:
    """Create a user with ADMIN role (superuser)."""
    ensure_permissions_exist()
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
def guest_client(guest_user) -> "APIClient":
    """API client authenticated as GUEST user."""
    client = APIClient()
    client.force_authenticate(user=guest_user)
    return client


@pytest.fixture
def host_client(host_user) -> "APIClient":
    """API client authenticated as HOST user."""
    client = APIClient()
    client.force_authenticate(user=host_user)
    return client


@pytest.fixture
def manager_client(manager_user) -> "APIClient":
    """API client authenticated as MANAGER user."""
    client = APIClient()
    client.force_authenticate(user=manager_user)
    return client


@pytest.fixture
def admin_client(admin_user) -> "APIClient":
    """API client authenticated as ADMIN user."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


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
