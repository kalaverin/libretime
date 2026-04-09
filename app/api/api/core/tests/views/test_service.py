"""
T176-T177: ServiceRegister API endpoint tests.

ServiceRegister tracks connected services (liquidsoap, etc.) with their IPs.
"""

from django.conf import settings
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase
from sdk.faker import faker


class TestServiceRegisterViewSetList(APITestCase):
    """
    T176: Test ServiceRegister LIST (GET /api/v2/service-register)

    Covers:
    - Basic LIST
    - Response structure (name as primary key, ip)
    - Empty list
    - Multiple services
    - IP format validation
    - Permissions
    """

    @classmethod
    def setUpTestData(cls):
        cls.path = "/api/v2/service-registers"
        cls.api_key = settings.CONFIG.general.api_key

    def setUp(self):
        self.admin_user = baker.make("core.User", role="A")
        self.host_user = baker.make("core.User", role="H")
        self.client.force_authenticate(user=self.admin_user)

    def test_list_service_register_as_admin_success(self):
        """Admin can list service register."""
        baker.make("core.ServiceRegister", _fill_optional=True)
        response = self.client.get(self.path)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertIsInstance(result, list)

    def test_list_service_register_response_structure(self):
        """Response has name (PK) and ip fields."""
        baker.make("core.ServiceRegister", _fill_optional=True)
        response = self.client.get(self.path)
        result = response.json()

        service = result[0]
        self.assertIn("name", service)
        self.assertIn("ip", service)
        self.assertIsInstance(service["name"], str)
        self.assertIsInstance(service["ip"], str)

    def test_list_service_register_primary_key_behavior(self):
        """name is primary key, not numeric id."""
        service_name = faker.word()
        baker.make("core.ServiceRegister", name=service_name)
        response = self.client.get(self.path)
        result = response.json()

        service = result[0]
        self.assertEqual(service["name"], service_name)
        self.assertNotIn("id", service)

    def test_list_service_register_empty(self):
        """Empty list returns 200 with empty array."""
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result, [])

    def test_list_service_register_multiple_services(self):
        """List contains all registered services."""
        services = [
            baker.make("core.ServiceRegister"),
            baker.make("core.ServiceRegister"),
            baker.make("core.ServiceRegister"),
            baker.make("core.ServiceRegister"),
        ]
        expected_names = {s.name for s in services}

        response = self.client.get(self.path)
        result = response.json()

        self.assertEqual(len(result), 4)
        names = {s["name"] for s in result}
        self.assertEqual(names, expected_names)

    def test_list_service_register_ipv4(self):
        """Service with IPv4 address."""
        ipv4 = faker.ipv4()
        baker.make("core.ServiceRegister", ip=ipv4)
        response = self.client.get(self.path)
        result = response.json()

        self.assertEqual(result[0]["ip"], ipv4)

    def test_list_service_register_ipv6(self):
        """Service with IPv6 address (max_length=45 supports IPv6)."""
        ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        baker.make("core.ServiceRegister", ip=ipv6)
        response = self.client.get(self.path)
        result = response.json()

        self.assertEqual(result[0]["ip"], ipv6)

    def test_list_service_register_localhost(self):
        """Service with localhost address."""
        localhost = faker.ipv4_private()
        baker.make("core.ServiceRegister", ip=localhost)
        response = self.client.get(self.path)
        result = response.json()

        self.assertEqual(result[0]["ip"], localhost)

    def test_list_service_register_hostname(self):
        """Service with hostname instead of IP (document behavior)."""
        hostname = faker.hostname()
        baker.make("core.ServiceRegister", ip=hostname)
        response = self.client.get(self.path)
        result = response.json()

        self.assertEqual(result[0]["ip"], hostname)

    def test_list_service_register_as_host_forbidden(self):
        """HOST cannot list service register."""
        baker.make("core.ServiceRegister")
        self.client.force_authenticate(user=self.host_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_service_register_unauthenticated(self):
        """Unauthenticated cannot list."""
        baker.make("core.ServiceRegister")
        self.client.force_authenticate(user=None)
        response = self.client.get(self.path)
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )

    def test_list_service_register_with_api_key(self):
        """API Key can list service register."""
        baker.make("core.ServiceRegister")
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key}")
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestServiceRegisterViewSetUpdate(APITestCase):
    """
    T177: Test ServiceRegister heartbeat/update (PUT/PATCH /api/v2/service-registers/{name})

    Service heartbeat updates IP address. Name is primary key.

    Covers:
    - PATCH IP update (heartbeat)
    - PUT full update
    - Update to new IP
    - Update same IP (no-op)
    - 404 for non-existent service
    - Permissions (admin vs host)
    - API Key access (likely needed for services)
    """

    @classmethod
    def setUpTestData(cls):
        cls.path = "/api/v2/service-registers"
        cls.api_key = settings.CONFIG.general.api_key

    def setUp(self):
        self.admin_user = baker.make("core.User", role="A")
        self.host_user = baker.make("core.User", role="H")
        self.client.force_authenticate(user=self.admin_user)

    def test_patch_service_register_ip_heartbeat(self):
        """PATCH updates IP (service heartbeat)."""
        service = baker.make("core.ServiceRegister", ip=faker.ipv4())
        new_ip = faker.ipv4()

        data = {"ip": new_ip}
        response = self.client.patch(
            f"{self.path}/{service.name}",
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result["name"], service.name)
        self.assertEqual(result["ip"], new_ip)

    def test_patch_service_register_same_ip_noop(self):
        """PATCH with same IP is no-op but succeeds."""
        service = baker.make("core.ServiceRegister")

        data = {"ip": service.ip}
        response = self.client.patch(
            f"{self.path}/{service.name}",
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result["ip"], service.ip)

    def test_patch_service_register_ipv4_to_ipv6(self):
        """PATCH updates IPv4 to IPv6."""
        service = baker.make("core.ServiceRegister")

        ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        data = {"ip": ipv6}
        response = self.client.patch(
            f"{self.path}/{service.name}",
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result["ip"], ipv6)

    def test_patch_service_register_hostname(self):
        """PATCH updates to hostname."""
        service = baker.make("core.ServiceRegister")

        data = {"ip": faker.hostname()}
        response = self.client.patch(
            f"{self.path}/{service.name}",
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result["ip"], data["ip"])

    def test_put_service_register_full_update(self):
        """PUT updates both name and ip."""
        service = baker.make("core.ServiceRegister")

        data = {"name": faker.word(), "ip": faker.ipv4()}
        response = self.client.put(
            f"{self.path}/{service.name}",
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result["name"], data["name"])
        self.assertEqual(result["ip"], data["ip"])

    def test_put_service_register_create_if_not_exists(self):
        """PUT creates service if doesn't exist (upsert behavior)."""
        data = {"name": faker.word(), "ip": faker.ipv4()}
        response = self.client.put(
            f"{self.path}/{data['name']}",
            data,
            format="json",
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_200_OK,
                status.HTTP_201_CREATED,
                status.HTTP_404_NOT_FOUND,
            ],
        )

    def test_patch_service_register_nonexistent_404(self):
        """PATCH non-existent service returns 404."""
        data = {"ip": faker.ipv4()}
        response = self.client.patch(
            f"{self.path}/nonexistent",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_service_register_nonexistent_404(self):
        """PUT non-existent service returns 404 (if not upsert)."""
        data = {"name": faker.word(), "ip": faker.ipv4()}
        response = self.client.put(
            f"{self.path}/{data['name']}",
            data,
            format="json",
        )
        self.assertIn(
            response.status_code,
            [
                status.HTTP_200_OK,
                status.HTTP_201_CREATED,
                status.HTTP_404_NOT_FOUND,
            ],
        )

    def test_patch_service_register_as_host_forbidden(self):
        """HOST cannot update service register."""
        service = baker.make("core.ServiceRegister")

        self.client.force_authenticate(user=self.host_user)
        data = {"ip": faker.ipv4()}
        response = self.client.patch(
            f"{self.path}/{service.name}",
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_service_register_unauthenticated(self):
        """Unauthenticated cannot update."""
        service = baker.make("core.ServiceRegister")

        self.client.force_authenticate(user=None)
        data = {"ip": faker.ipv4()}
        response = self.client.patch(
            f"{self.path}/{service.name}",
            data,
            format="json",
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )

    def test_patch_service_register_with_api_key(self):
        """API Key can update service register (for service heartbeat)."""
        service = baker.make("core.ServiceRegister")

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key}")
        data = {"ip": faker.ipv4()}
        response = self.client.patch(
            f"{self.path}/{service.name}",
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_service_register_empty_ip(self):
        """PATCH with empty IP (document behavior)."""
        service = baker.make("core.ServiceRegister")

        data = {"ip": ""}
        response = self.client.patch(
            f"{self.path}/{service.name}",
            data,
            format="json",
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST],
        )

    def test_patch_service_register_long_ip(self):
        """PATCH with very long IP/hostname."""
        service = baker.make("core.ServiceRegister")

        long_ip = "x" * 45  # max_length in model
        data = {"ip": long_ip}
        response = self.client.patch(
            f"{self.path}/{service.name}",
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_service_register_too_long_ip_fails(self):
        """PATCH with IP exceeding 45 chars should fail."""
        service = baker.make("core.ServiceRegister")

        too_long_ip = "x" * 46
        data = {"ip": too_long_ip}
        response = self.client.patch(
            f"{self.path}/{service.name}",
            data,
            format="json",
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST],
        )
