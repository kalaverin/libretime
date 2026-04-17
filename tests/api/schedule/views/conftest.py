"""
Pytest configuration for schedule view tests.

Imports role-based fixtures to make them available.
"""

# Import role-based fixtures to make them available to all tests in this directory
from tests.api.fixtures.role_fixtures import (  # noqa: F401
    admin_client,
    admin_user,
    guest_client,
    guest_user,
    host_client,
    host_user,
    manager_client,
    manager_user,
    session_client,
    two_host_users,
)
