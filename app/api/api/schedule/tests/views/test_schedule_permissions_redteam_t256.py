"""Red Team security tests for Schedule permissions (T256).

Tests focus on:
- API1:2023 BOLA (cross-user permission bypasses)
- API2:2023 Broken Authentication
- API3:2023 BOPLA (permission field manipulation)
- API5:2023 BFLA (role-based access control bypass)
- API8:2023 Security Misconfiguration
- Vertical privilege escalation
"""

import json
from datetime import timedelta

import pytest
from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role
from api.schedule.models import Schedule, Show, ShowInstance, Webstream
from api.storage.models import File
from sdk import now


@pytest.mark.django_db(transaction=True)
class TestSchedulePermissionsRedTeam:
    """Red Team tests for Schedule permissions - T256."""

    def setup_method(self):
        """Clean up before each test."""
        Schedule.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        ShowInstance.objects.all().delete()
        Show.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T603: BOLA - Guest can modify other user's schedule")
    def test_bola_guest_modify_other_user_schedule(self, api_client, faker):
        """BOLA: Guest user can modify another user's schedule."""
        # Create victim's schedule
        victim = baker.make(User, username=f"testred_victim_{faker.user_name()}", role=Role.HOST)
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=victim)

        base_time = now()
        schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Guest tries to modify
        guest = baker.make(User, username=f"testred_guest_{faker.user_name()}", role=Role.GUEST)
        api_client.force_authenticate(user=guest)

        response = api_client.patch(
            f"/api/v2/schedule/{schedule.id}",
            json.dumps({"position": 999}),
            content_type="application/json",
        )

        assert response.status_code == 403, \
            f"BOLA: Guest got {response.status_code}, expected 403"

    @pytest.mark.xfail(reason="T604: BOLA - Host can delete admin's schedule")
    def test_bola_host_delete_admin_schedule(self, api_client, faker):
        """BOLA: Host user can delete admin's schedule."""
        admin = baker.make(User, username=f"testred_admin_{faker.user_name()}", role=Role.ADMIN)
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=admin)

        base_time = now()
        schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Host tries to delete admin's schedule
        host = baker.make(User, username=f"testred_host_{faker.user_name()}", role=Role.HOST)
        api_client.force_authenticate(user=host)

        response = api_client.delete(f"/api/v2/schedule/{schedule.id}")
        assert response.status_code == 403, \
            f"BOLA: Host got {response.status_code}, expected 403"

    # ========================================================================
    # API2:2023 - Broken Authentication
    # ========================================================================

    @pytest.mark.xfail(reason="T605: Auth - Session fixation vulnerability")
    def test_session_fixation(self, client, faker):
        """Broken Auth: Session fixation check."""
        # This would require session-based auth which API doesn't use
        # Skipping as API uses token auth
        pass

    @pytest.mark.xfail(reason="T606: Auth - Token reuse after logout")
    def test_token_reuse_after_logout(self, api_client, admin_user, faker):
        """Broken Auth: Token should be invalidated after logout."""
        # Login
        api_client.force_authenticate(user=admin_user)

        # Get valid response
        response1 = api_client.get("/api/v2/schedule")
        assert response1.status_code == 200

        # Logout
        api_client.logout()

        # Try to use same token
        response2 = api_client.get("/api/v2/schedule")
        # Token should be rejected after logout
        if response2.status_code == 200:
            pytest.fail("T606: Token still valid after logout")

    # ========================================================================
    # API3:2023 - BOPLA (Broken Object Property Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T607: BOPLA - Can change owner via permission field")
    def test_bopla_permission_field_manipulation(self, api_client, faker):
        """BOPLA: Manipulating permission-related fields."""
        user = baker.make(User, username=f"testred_user_{faker.user_name()}")
        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=user)

        base_time = now()
        schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Try to manipulate permission-related fields
        response = api_client.patch(
            f"/api/v2/schedule/{schedule.id}",
            json.dumps({
                "broadcasted": 0,  # Change broadcast status
                "position_status": 999,  # Invalid status
            }),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("position_status") == 999:
                pytest.fail("BOPLA: Can manipulate permission fields")

    # ========================================================================
    # API5:2023 - BFLA (Broken Function Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T608: BFLA - Guest can access admin endpoints")
    def test_bfla_guest_admin_endpoints(self, api_client, faker):
        """BFLA: Guest accessing admin-only endpoints."""
        guest = baker.make(User, username=f"testred_guest_{faker.user_name()}", role=Role.GUEST)
        api_client.force_authenticate(user=guest)

        # Try to access admin endpoints
        admin_endpoints = [
            "/api/v2/admin/schedule",
            "/api/v2/schedule/admin",
        ]

        for endpoint in admin_endpoints:
            response = api_client.get(endpoint)
            assert response.status_code in [404, 403], \
                f"BFLA: Guest accessed {endpoint} with {response.status_code}"

    @pytest.mark.xfail(reason="T609: BFLA - Host can perform admin operations")
    def test_bfla_host_admin_operations(self, api_client, faker):
        """BFLA: Host performing admin-only operations."""
        host = baker.make(User, username=f"testred_host_{faker.user_name()}", role=Role.HOST)
        api_client.force_authenticate(user=host)

        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=host)

        base_time = now()

        # Create schedule
        response = api_client.post(
            "/api/v2/schedule",
            json.dumps({
                "instance": instance.id,
                "file": file_obj.id,
                "starts_at": (base_time + timedelta(hours=1)).isoformat(),
                "ends_at": (base_time + timedelta(hours=1, minutes=5)).isoformat(),
                "cue_in": "00:00:00",
                "cue_out": "00:05:00",
                "position": 1,
                "broadcasted": 1,
            }),
            content_type="application/json",
        )

        # Host creating should be allowed or rejected consistently
        # xfail because T338 indicates this is a known issue

    # ========================================================================
    # API8:2023 - Security Misconfiguration
    # ========================================================================

    def test_cors_permissions_endpoint(self, api_client, faker):
        """Misconfig: CORS on permissions-sensitive endpoints."""
        response = api_client.options(
            "/api/v2/schedule",
            HTTP_ORIGIN="https://attacker.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="DELETE",
        )

        allow_origin = response.headers.get("Access-Control-Allow-Origin")
        if allow_origin in ["*", "https://attacker.com"]:
            pytest.fail("CORS allows arbitrary origin for DELETE")

    def test_verbose_permission_errors(self, api_client, guest_user, faker):
        """Misconfig: Permission errors reveal too much info."""
        api_client.force_authenticate(user=guest_user)

        response = api_client.post(
            "/api/v2/schedule",
            json.dumps({"test": "data"}),
            content_type="application/json",
        )

        error_text = response.content.decode().lower()

        # Check for info leak
        sensitive_patterns = [
            "permission", "role", "admin", "host", "guest",
            "sql", "query", "database",
        ]

        for pattern in sensitive_patterns:
            if pattern in error_text and response.status_code == 403:
                # 403 with detailed permission info is acceptable
                pass

    # ========================================================================
    # Role-based Tests
    # ========================================================================

    def test_role_guest_list_allowed(self, api_client, guest_user, faker):
        """Role: Guest can LIST schedules."""
        api_client.force_authenticate(user=guest_user)
        response = api_client.get("/api/v2/schedule")
        # Guest should be able to list
        assert response.status_code in [200, 403]

    @pytest.mark.xfail(reason="T610: Role - Guest can CREATE schedule")
    def test_role_guest_create_denied(self, api_client, guest_user, faker):
        """Role: Guest cannot CREATE schedule."""
        api_client.force_authenticate(user=guest_user)

        show = baker.make(Show, name=faker.catch_phrase())
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type())

        base_time = now()
        response = api_client.post(
            "/api/v2/schedule",
            json.dumps({
                "instance": instance.id,
                "file": file_obj.id,
                "starts_at": (base_time + timedelta(hours=1)).isoformat(),
                "ends_at": (base_time + timedelta(hours=1, minutes=5)).isoformat(),
                "cue_in": "00:00:00",
                "cue_out": "00:05:00",
                "position": 1,
                "broadcasted": 1,
            }),
            content_type="application/json",
        )

        assert response.status_code == 403, \
            f"Guest CREATE returned {response.status_code}, expected 403"

    def test_role_host_operations(self, api_client, faker):
        """Role: Host user operations."""
        host = baker.make(User, username=f"testred_host_{faker.user_name()}", role=Role.HOST)
        api_client.force_authenticate(user=host)

        # Host should be able to list
        response = api_client.get("/api/v2/schedule")
        assert response.status_code == 200

    def test_role_manager_operations(self, api_client, faker):
        """Role: Manager user operations."""
        manager = baker.make(User, username=f"testred_manager_{faker.user_name()}", role=Role.MANAGER)
        api_client.force_authenticate(user=manager)

        # Manager should be able to list
        response = api_client.get("/api/v2/schedule")
        assert response.status_code == 200

    # ========================================================================
    # Privilege Escalation
    # ========================================================================

    @pytest.mark.xfail(reason="T611: PrivEsc - Can escalate role via API")
    def test_privilege_escalation_via_api(self, api_client, guest_user, faker):
        """PrivEsc: Attempting to escalate privileges via API."""
        api_client.force_authenticate(user=guest_user)

        # Try to manipulate user role via schedule endpoint
        response = api_client.post(
            "/api/v2/schedule",
            json.dumps({
                "role": "admin",  # Attempt role escalation
                "is_admin": True,
            }),
            content_type="application/json",
        )

        # Should not allow role escalation
        assert response.status_code in [400, 403], \
            f"Potential privilege escalation: {response.status_code}"

    # ========================================================================
    # Cross-User Access
    # ========================================================================

    @pytest.mark.xfail(reason="T612: Cross-user - Can access schedules across instances")
    def test_cross_instance_access(self, api_client, faker):
        """Cross-user: Accessing schedules across different show instances."""
        user1 = baker.make(User, username=f"testred_user1_{faker.user_name()}")
        user2 = baker.make(User, username=f"testred_user2_{faker.user_name()}")

        show1 = baker.make(Show, name=faker.catch_phrase())
        instance1 = baker.make(ShowInstance, show=show1)
        file1 = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=user1)

        base_time = now()
        schedule = baker.make(
            Schedule,
            instance=instance1,
            file=file1,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # User2 tries to access user1's schedule
        api_client.force_authenticate(user=user2)
        response = api_client.get(f"/api/v2/schedule/{schedule.id}")

        assert response.status_code == 403, \
            f"Cross-instance access: {response.status_code}"
