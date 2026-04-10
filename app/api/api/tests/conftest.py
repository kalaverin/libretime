"""
Pytest configuration for API tests.

Imports role-based fixtures from fixtures/role_fixtures.py
"""

# Import role-based fixtures to make them available to all tests
# Note: api_client is defined in api/conftest.py (parent directory)
from api.tests.fixtures.role_fixtures import (  # noqa: F401
    admin_client,
    admin_user,
    guest_client,
    guest_user,
    host_and_guest_users,
    host_and_manager_users,
    host_client,
    host_user,
    manager_client,
    manager_user,
    session_client,
    two_host_users,
)
