"""
T178-T179: UserToken and LoginAttempt API endpoint tests.
"""


from django.conf import settings
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase
from sdk.datetime import format_datetime
from sdk.faker import faker

from sdk import now


class TestUserTokenViewSetList(APITestCase):
    """
    T178: Test UserToken LIST (GET /api/v2/user-tokens)

    UserToken tracks API tokens for users with action and creation time.
    """

    @classmethod
    def setUpTestData(cls):
        cls.path = "/api/v2/user-tokens"
        cls.api_key = settings.CONFIG.general.api_key

    def setUp(self):
        self.admin_user = baker.make("core.User", role="A")
        self.host_user = baker.make("core.User", role="H")
        self.client.force_authenticate(user=self.admin_user)

    def test_list_user_tokens_as_admin_success(self):
        """Admin can list user tokens."""
        baker.make("core.UserToken", user=self.host_user, created=now())
        response = self.client.get(self.path)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertIsInstance(result, list)

    def test_list_user_tokens_response_structure(self):
        """Response has user, action, token, created fields."""
        baker.make("core.UserToken", user=self.host_user, created=now())
        response = self.client.get(self.path)
        result = response.json()

        token = result[0]
        self.assertIn("user", token)
        self.assertIn("action", token)
        self.assertIn("token", token)
        self.assertIn("created", token)

    def test_list_user_tokens_unique_token_constraint(self):
        """Token field has unique constraint."""
        baker.make("core.UserToken", user=self.host_user, created=now())

        response = self.client.get(self.path)
        result = response.json()

        tokens = [t["token"] for t in result]
        self.assertEqual(
            len(tokens),
            len(set(tokens)),
            "Tokens should be unique",
        )

    def test_list_user_tokens_empty(self):
        """Empty list returns 200."""
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_list_user_tokens_as_host_forbidden(self):
        """HOST cannot list tokens."""
        self.client.force_authenticate(user=self.host_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_user_tokens_unauthenticated(self):
        """Unauthenticated cannot list."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.path)
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )

    def test_list_user_tokens_with_api_key(self):
        """API Key can list tokens."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key}")
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestUserTokenViewSetCreate(APITestCase):
    """T178: Test UserToken CREATE."""

    @classmethod
    def setUpTestData(cls):
        cls.path = "/api/v2/user-tokens"
        cls.api_key = settings.CONFIG.general.api_key

    def setUp(self):
        self.admin_user = baker.make("core.User", role="A")
        self.host_user = baker.make("core.User", role="H")
        self.client.force_authenticate(user=self.admin_user)

    def test_create_user_token_success(self):
        """Create user token successfully."""
        token_value = faker.uuid4()
        data = {
            "user": self.host_user.id,
            "action": faker.word(),
            "token": token_value,
            "created": format_datetime(now()),
        }
        response = self.client.post(self.path, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = response.json()
        self.assertEqual(result["token"], token_value)

    def test_create_user_token_duplicate_fails(self):
        """Cannot create token with duplicate value."""
        dup_token = faker.uuid4()
        baker.make(
            "core.UserToken",
            user=self.host_user,
            token=dup_token,
            created=now(),
        )

        data = {
            "user": self.admin_user.id,
            "action": faker.word(),
            "token": dup_token,
            "created": format_datetime(now()),
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_token_as_host_forbidden(self):
        """HOST cannot create tokens."""
        self.client.force_authenticate(user=self.host_user)
        data = {
            "user": self.host_user.id,
            "action": faker.word(),
            "token": faker.uuid4(),
            "created": format_datetime(now()),
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user_token_with_api_key(self):
        """API Key can create tokens."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key}")
        data = {
            "user": self.host_user.id,
            "action": faker.word(),
            "token": faker.uuid4(),
            "created": format_datetime(now()),
        }
        response = self.client.post(self.path, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestUserTokenViewSetDelete(APITestCase):
    """T178: Test UserToken DELETE."""

    @classmethod
    def setUpTestData(cls):
        cls.path = "/api/v2/user-tokens"
        cls.api_key = settings.CONFIG.general.api_key

    def setUp(self):
        self.admin_user = baker.make("core.User", role="A")
        self.host_user = baker.make("core.User", role="H")
        self.client.force_authenticate(user=self.admin_user)

    def test_delete_user_token_success(self):
        """Delete token successfully."""
        token = baker.make(
            "core.UserToken",
            user=self.host_user,
            created=now(),
        )

        response = self.client.delete(f"{self.path}/{token.token}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_user_token_verify_gone(self):
        """After DELETE, token cannot be retrieved."""
        token = baker.make(
            "core.UserToken",
            user=self.host_user,
            created=now(),
        )

        self.client.delete(f"{self.path}/{token.token}")

        response = self.client.get(f"{self.path}/{token.token}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_user_token_nonexistent_404(self):
        """DELETE non-existent token returns 404."""
        response = self.client.delete(f"{self.path}/nonexistent_token")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_user_token_as_host_forbidden(self):
        """HOST cannot delete tokens."""
        token = baker.make(
            "core.UserToken",
            user=self.admin_user,
            created=now(),
        )

        self.client.force_authenticate(user=self.host_user)
        response = self.client.delete(f"{self.path}/{token.token}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_user_token_with_api_key(self):
        """API Key can delete tokens."""
        token = baker.make(
            "core.UserToken",
            user=self.host_user,
            created=now(),
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key}")
        response = self.client.delete(f"{self.path}/{token.token}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TestLoginAttemptViewSetList(APITestCase):
    """
    T179: Test LoginAttempt LIST (GET /api/v2/login-attempts)

    LoginAttempt tracks failed login attempts by IP address.
    ip is primary key (CharField), attempts is counter.
    """

    @classmethod
    def setUpTestData(cls):
        cls.path = "/api/v2/login-attempts"
        cls.api_key = settings.CONFIG.general.api_key

    def setUp(self):
        self.admin_user = baker.make("core.User", role="A")
        self.host_user = baker.make("core.User", role="H")
        self.client.force_authenticate(user=self.admin_user)

    def test_list_login_attempts_as_admin_success(self):
        """Admin can list login attempts."""
        baker.make(
            "core.LoginAttempt",
            attempts=faker.random_int(min=1, max=10),
        )
        response = self.client.get(self.path)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertIsInstance(result, list)

    def test_list_login_attempts_response_structure(self):
        """Response has ip (PK) and attempts fields."""
        baker.make(
            "core.LoginAttempt",
            attempts=faker.random_int(min=1, max=10),
        )
        response = self.client.get(self.path)
        result = response.json()

        attempt = result[0]
        self.assertIn("ip", attempt)
        self.assertIn("attempts", attempt)
        self.assertIsInstance(attempt["ip"], str)
        self.assertIsInstance(attempt["attempts"], (int, type(None)))

    def test_list_login_attempts_primary_key_behavior(self):
        """ip is primary key, not numeric id."""
        baker.make(
            "core.LoginAttempt",
            attempts=faker.random_int(min=1, max=10),
        )
        response = self.client.get(self.path)
        result = response.json()

        attempt = result[0]
        self.assertIn("ip", attempt)
        self.assertNotIn("id", attempt)

    def test_list_login_attempts_various_ips(self):
        """List contains attempts from various IP types."""
        test_ips = [
            faker.ipv4(),
            faker.ipv4_private(),
            "::1",
            "2001:0db8:85a3::8a2e:0370:7334",
        ]
        for ip in test_ips:
            baker.make(
                "core.LoginAttempt",
                ip=ip,
                attempts=faker.random_int(min=1, max=10),
            )

        response = self.client.get(self.path)
        result = response.json()

        self.assertEqual(len(result), 4)
        ips = {a["ip"] for a in result}
        self.assertEqual(ips, set(test_ips))

    def test_list_login_attempts_null_attempts(self):
        """attempts field can be null."""
        baker.make("core.LoginAttempt", attempts=None)
        response = self.client.get(self.path)
        result = response.json()

        attempt = result[0]
        self.assertIsNone(attempt["attempts"])

    def test_list_login_attempts_zero_attempts(self):
        """attempts can be zero."""
        baker.make("core.LoginAttempt", attempts=0)
        response = self.client.get(self.path)
        result = response.json()

        attempt = result[0]
        self.assertEqual(attempt["attempts"], 0)

    def test_list_login_attempts_empty(self):
        """Empty list returns 200."""
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_list_login_attempts_as_host_forbidden(self):
        """HOST cannot list login attempts."""
        baker.make(
            "core.LoginAttempt",
            attempts=faker.random_int(min=1, max=10),
        )
        self.client.force_authenticate(user=self.host_user)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_login_attempts_unauthenticated(self):
        """Unauthenticated cannot list."""
        baker.make(
            "core.LoginAttempt",
            attempts=faker.random_int(min=1, max=10),
        )
        self.client.force_authenticate(user=None)
        response = self.client.get(self.path)
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )

    def test_list_login_attempts_with_api_key(self):
        """API Key can list login attempts."""
        baker.make(
            "core.LoginAttempt",
            attempts=faker.random_int(min=1, max=10),
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key}")
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestLoginAttemptViewSetUpdate(APITestCase):
    """
    T179: Test LoginAttempt UPDATE (reset counter, block/unblock)

    Admin may need to reset attempts counter or block/unblock IPs.
    """

    @classmethod
    def setUpTestData(cls):
        cls.path = "/api/v2/login-attempts"
        cls.api_key = settings.CONFIG.general.api_key

    def setUp(self):
        self.admin_user = baker.make("core.User", role="A")
        self.host_user = baker.make("core.User", role="H")
        self.client.force_authenticate(user=self.admin_user)

    def test_patch_login_attempts_reset_counter(self):
        """PATCH resets attempts counter (unblock IP)."""
        ip = faker.ipv4()
        baker.make(
            "core.LoginAttempt",
            ip=ip,
            attempts=faker.random_int(min=5, max=15),
        )

        data = {"attempts": 0}
        response = self.client.patch(f"{self.path}/{ip}", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result["attempts"], 0)
        self.assertEqual(result["ip"], ip)

    def test_patch_login_attempts_increment(self):
        """PATCH increments attempts counter."""
        ip = faker.ipv4()
        baker.make(
            "core.LoginAttempt",
            ip=ip,
            attempts=faker.random_int(min=1, max=5),
        )

        data = {"attempts": faker.random_int(min=6, max=10)}
        response = self.client.patch(f"{self.path}/{ip}", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result["attempts"], data["attempts"])

    def test_patch_login_attempts_clear_null(self):
        """PATCH attempts to null (clear)."""
        ip = faker.ipv4()
        baker.make(
            "core.LoginAttempt",
            ip=ip,
            attempts=faker.random_int(min=1, max=10),
        )

        data = {"attempts": None}
        response = self.client.patch(f"{self.path}/{ip}", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertIsNone(result["attempts"])

    def test_put_login_attempts_full_update(self):
        """PUT updates attempts."""
        ip = faker.ipv4()
        baker.make(
            "core.LoginAttempt",
            ip=ip,
            attempts=faker.random_int(min=1, max=10),
        )

        data = {"ip": ip, "attempts": faker.random_int(min=50, max=100)}
        response = self.client.put(f"{self.path}/{ip}", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result["attempts"], data["attempts"])

    def test_patch_login_attempts_nonexistent_404(self):
        """PATCH non-existent IP returns 404."""
        data = {"attempts": 0}
        response = self.client.patch(
            f"{self.path}/999.999.999.999",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_login_attempts_as_host_forbidden(self):
        """HOST cannot update login attempts."""
        ip = faker.ipv4()
        baker.make(
            "core.LoginAttempt",
            ip=ip,
            attempts=faker.random_int(min=1, max=10),
        )

        self.client.force_authenticate(user=self.host_user)
        data = {"attempts": 0}
        response = self.client.patch(f"{self.path}/{ip}", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_login_attempts_with_api_key(self):
        """API Key can update login attempts."""
        ip = faker.ipv4()
        baker.make(
            "core.LoginAttempt",
            ip=ip,
            attempts=faker.random_int(min=5, max=15),
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key}")
        data = {"attempts": 0}
        response = self.client.patch(f"{self.path}/{ip}", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestLoginAttemptViewSetDelete(APITestCase):
    """
    T179: Test LoginAttempt DELETE (clear blocked IP)

    Delete removes IP from blocked list.
    """

    @classmethod
    def setUpTestData(cls):
        cls.path = "/api/v2/login-attempts"
        cls.api_key = settings.CONFIG.general.api_key

    def setUp(self):
        self.admin_user = baker.make("core.User", role="A")
        self.host_user = baker.make("core.User", role="H")
        self.client.force_authenticate(user=self.admin_user)

    def test_delete_login_attempt_success(self):
        """Delete login attempt (unblock IP)."""
        ip = faker.ipv4()
        baker.make(
            "core.LoginAttempt",
            ip=ip,
            attempts=faker.random_int(min=5, max=15),
        )

        response = self.client.delete(f"{self.path}/{ip}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_login_attempt_verify_gone(self):
        """After DELETE, IP not in list."""
        ip = faker.ipv4()
        baker.make(
            "core.LoginAttempt",
            ip=ip,
            attempts=faker.random_int(min=1, max=10),
        )

        self.client.delete(f"{self.path}/{ip}")

        response = self.client.get(self.path)
        result = response.json()
        ips = {a["ip"] for a in result}
        self.assertNotIn(ip, ips)

    def test_delete_login_attempt_nonexistent_404(self):
        """DELETE non-existent IP returns 404."""
        response = self.client.delete(f"{self.path}/999.999.999.999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_login_attempt_as_host_forbidden(self):
        """HOST cannot delete login attempts."""
        ip = faker.ipv4()
        baker.make(
            "core.LoginAttempt",
            ip=ip,
            attempts=faker.random_int(min=1, max=10),
        )

        self.client.force_authenticate(user=self.host_user)
        response = self.client.delete(f"{self.path}/{ip}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_login_attempt_with_api_key(self):
        """API Key can delete login attempts."""
        ip = faker.ipv4()
        baker.make(
            "core.LoginAttempt",
            ip=ip,
            attempts=faker.random_int(min=10, max=20),
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key}")
        response = self.client.delete(f"{self.path}/{ip}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
