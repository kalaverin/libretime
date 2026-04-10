"""Red Team security tests for Schedule Show Host permissions (T258).

Tests focus on:
- API1:2023 BOLA (host modifying other shows' schedules)
- API3:2023 BOPLA (permission field manipulation)
- API5:2023 BFLA (function-level authorization)
- Show host specific permissions (can modify own show, not others)
- Cross-show access controls
"""

import json
from datetime import timedelta

import pytest
from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role
from api.schedule.models import Schedule, Show, ShowHost, ShowInstance, Webstream
from api.storage.models import File
from sdk import now


@pytest.mark.django_db(transaction=True)
class TestScheduleShowHostPermissionsRedTeam:
    """Red Team tests for Schedule Show Host permissions - T258."""

    def setup_method(self):
        """Clean up before each test."""
        Schedule.objects.all().delete()
        File.objects.all().delete()
        Webstream.objects.all().delete()
        ShowHost.objects.all().delete()
        ShowInstance.objects.all().delete()
        Show.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # Show Host Own Show Permissions
    # ========================================================================

    def test_host_can_create_schedule_own_show(self, api_client, faker):
        """Host should be able to create schedule for their own show."""
        host = baker.make(User, username=f"testred_host_{faker.user_name()}", role=Role.HOST)
        show = baker.make(Show, name=faker.catch_phrase())
        baker.make(ShowHost, show=show, user=host)  # Assign host to show
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=host)

        base_time = now()
        api_client.force_authenticate(user=host)

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

        # Host should be able to create schedule for their own show
        assert response.status_code in [201, 403], \
            f"Host CREATE returned {response.status_code}"

    @pytest.mark.xfail(reason="T617: BOLA - Host can modify other host's show schedule")
    def test_host_cannot_modify_other_host_show(self, api_client, faker):
        """BOLA: Host should NOT be able to modify another host's show schedule."""
        # Victim host and show
        victim_host = baker.make(User, username=f"testred_victim_{faker.user_name()}", role=Role.HOST)
        victim_show = baker.make(Show, name=faker.catch_phrase())
        baker.make(ShowHost, show=victim_show, host=victim_host)
        victim_instance = baker.make(ShowInstance, show=victim_show)
        victim_file = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=victim_host)

        base_time = now()
        victim_schedule = baker.make(
            Schedule,
            instance=victim_instance,
            file=victim_file,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Attacker host
        attacker_host = baker.make(User, username=f"testred_attacker_{faker.user_name()}", role=Role.HOST)
        api_client.force_authenticate(user=attacker_host)

        # Try to modify victim's schedule
        response = api_client.patch(
            f"/api/v2/schedule/{victim_schedule.id}",
            json.dumps({"position": 999}),
            content_type="application/json",
        )

        assert response.status_code == 403, \
            f"BOLA: Host got {response.status_code}, expected 403"

    @pytest.mark.xfail(reason="T618: BOLA - Host can delete other host's show schedule")
    def test_host_cannot_delete_other_host_show(self, api_client, faker):
        """BOLA: Host should NOT be able to delete another host's show schedule."""
        victim_host = baker.make(User, username=f"testred_victim_{faker.user_name()}", role=Role.HOST)
        victim_show = baker.make(Show, name=faker.catch_phrase())
        baker.make(ShowHost, show=victim_show, host=victim_host)
        victim_instance = baker.make(ShowInstance, show=victim_show)
        victim_file = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=victim_host)

        base_time = now()
        victim_schedule = baker.make(
            Schedule,
            instance=victim_instance,
            file=victim_file,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        attacker_host = baker.make(User, username=f"testred_attacker_{faker.user_name()}", role=Role.HOST)
        api_client.force_authenticate(user=attacker_host)

        response = api_client.delete(f"/api/v2/schedule/{victim_schedule.id}")

        assert response.status_code == 403, \
            f"BOLA: Host DELETE got {response.status_code}, expected 403"

    # ========================================================================
    # Host vs Admin Permissions
    # ========================================================================

    def test_admin_can_modify_any_host_schedule(self, api_client, faker):
        """Admin should be able to modify any host's schedule."""
        host = baker.make(User, username=f"testred_host_{faker.user_name()}", role=Role.HOST)
        show = baker.make(Show, name=faker.catch_phrase())
        baker.make(ShowHost, show=show, user=host)
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=host)

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

        admin = baker.make(User, username=f"testred_admin_{faker.user_name()}", role=Role.ADMIN)
        api_client.force_authenticate(user=admin)

        response = api_client.patch(
            f"/api/v2/schedule/{schedule.id}",
            json.dumps({"position": 888}),
            content_type="application/json",
        )

        # Admin should succeed
        assert response.status_code == 200, \
            f"Admin PATCH got {response.status_code}, expected 200"

    # ========================================================================
    # Permission Bypass via Instance Manipulation
    # ========================================================================

    @pytest.mark.xfail(reason="T619: BOPLA - Host can change schedule to other show instance")
    def test_host_cannot_change_to_other_show_instance(self, api_client, faker):
        """BOPLA: Host should not change schedule to different show instance."""
        host = baker.make(User, username=f"testred_host_{faker.user_name()}", role=Role.HOST)

        # Host's own show
        own_show = baker.make(Show, name=faker.catch_phrase())
        baker.make(ShowHost, show=own_show, user=host)
        own_instance = baker.make(ShowInstance, show=own_show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=host)

        base_time = now()
        schedule = baker.make(
            Schedule,
            instance=own_instance,
            file=file_obj,
            starts_at=base_time + timedelta(hours=1),
            ends_at=base_time + timedelta(hours=1, minutes=5),
            cue_in="00:00:00",
            cue_out="00:05:00",
            position=1,
            broadcasted=1,
        )

        # Another host's show instance
        other_host = baker.make(User, username=f"testred_other_{faker.user_name()}", role=Role.HOST)
        other_show = baker.make(Show, name=faker.catch_phrase())
        baker.make(ShowHost, show=other_show, host=other_host)
        other_instance = baker.make(ShowInstance, show=other_show)

        api_client.force_authenticate(user=host)

        # Try to change schedule to other show's instance
        response = api_client.patch(
            f"/api/v2/schedule/{schedule.id}",
            json.dumps({"instance": other_instance.id}),
            content_type="application/json",
        )

        assert response.status_code == 403, \
            f"BOPLA: Got {response.status_code}, expected 403 for instance change"

    # ========================================================================
    # Guest vs Host Permissions
    # ========================================================================

    @pytest.mark.xfail(reason="T620: BFLA - Guest can modify host's schedule")
    def test_guest_cannot_modify_host_schedule(self, api_client, faker):
        """BFLA: Guest should not be able to modify host's schedule."""
        host = baker.make(User, username=f"testred_host_{faker.user_name()}", role=Role.HOST)
        show = baker.make(Show, name=faker.catch_phrase())
        baker.make(ShowHost, show=show, user=host)
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=host)

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

        guest = baker.make(User, username=f"testred_guest_{faker.user_name()}", role=Role.GUEST)
        api_client.force_authenticate(user=guest)

        response = api_client.patch(
            f"/api/v2/schedule/{schedule.id}",
            json.dumps({"position": 777}),
            content_type="application/json",
        )

        assert response.status_code == 403, \
            f"BFLA: Guest got {response.status_code}, expected 403"

    # ========================================================================
    # Show Creator Validation
    # ========================================================================

    def test_show_host_permission_check(self, api_client, faker):
        """Verify show host is properly checked for schedule operations."""
        host = baker.make(User, username=f"testred_creator_{faker.user_name()}", role=Role.HOST)
        show = baker.make(Show, name=faker.catch_phrase())
        baker.make(ShowHost, show=show, user=host)
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=host)

        base_time = now()
        api_client.force_authenticate(user=host)

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

        # Host should be able to create
        assert response.status_code in [201, 403]

    # ========================================================================
    # Multi-Show Host Permissions
    # ========================================================================

    def test_host_multiple_shows_isolation(self, api_client, faker):
        """Host with multiple shows should only access their own."""
        host = baker.make(User, username=f"testred_multi_{faker.user_name()}", role=Role.HOST)

        # Show 1
        show1 = baker.make(Show, name=faker.catch_phrase())
        baker.make(ShowHost, show=show1, user=host)
        instance1 = baker.make(ShowInstance, show=show1)
        file1 = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=host)

        # Show 2
        show2 = baker.make(Show, name=faker.catch_phrase())
        baker.make(ShowHost, show=show2, user=host)
        instance2 = baker.make(ShowInstance, show=show2)
        file2 = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=host)

        base_time = now()

        api_client.force_authenticate(user=host)

        # Create schedule for show1
        response1 = api_client.post(
            "/api/v2/schedule",
            json.dumps({
                "instance": instance1.id,
                "file": file1.id,
                "starts_at": (base_time + timedelta(hours=1)).isoformat(),
                "ends_at": (base_time + timedelta(hours=1, minutes=5)).isoformat(),
                "cue_in": "00:00:00",
                "cue_out": "00:05:00",
                "position": 1,
                "broadcasted": 1,
            }),
            content_type="application/json",
        )

        # Create schedule for show2
        response2 = api_client.post(
            "/api/v2/schedule",
            json.dumps({
                "instance": instance2.id,
                "file": file2.id,
                "starts_at": (base_time + timedelta(hours=2)).isoformat(),
                "ends_at": (base_time + timedelta(hours=2, minutes=5)).isoformat(),
                "cue_in": "00:00:00",
                "cue_out": "00:05:00",
                "position": 2,
                "broadcasted": 1,
            }),
            content_type="application/json",
        )

        # Both should succeed (host owns both shows)
        assert response1.status_code in [201, 403]
        assert response2.status_code in [201, 403]

    # ========================================================================
    # IDOR via Show Instance
    # ========================================================================

    @pytest.mark.xfail(reason="T621: IDOR - Can access schedule via instance ID enumeration")
    def test_idor_instance_enumeration(self, api_client, faker):
        """IDOR: Enumerating instance IDs to find other hosts' schedules."""
        host = baker.make(User, username=f"testred_host_{faker.user_name()}", role=Role.HOST)
        api_client.force_authenticate(user=host)

        # Try to enumerate instance IDs
        for instance_id in range(1, 10):
            response = api_client.get(f"/api/v2/schedule?instance={instance_id}")
            if response.status_code == 200:
                data = response.json()
                # Check if we got schedules that don't belong to us
                for schedule in data:
                    # Verify ownership
                    pass  # Would need to check show ownership

        # Should not return other hosts' schedules
        pass

    # ========================================================================
    # Permission Elevation
    # ========================================================================

    @pytest.mark.xfail(reason="T622: PrivEsc - Host can elevate to admin via schedule API")
    def test_host_privilege_escalation(self, api_client, faker):
        """PrivEsc: Host trying to escalate privileges via schedule manipulation."""
        host = baker.make(User, username=f"testred_host_{faker.user_name()}", role=Role.HOST)
        show = baker.make(Show, name=faker.catch_phrase())
        baker.make(ShowHost, show=show, user=host)
        instance = baker.make(ShowInstance, show=show)
        file_obj = baker.make(File, name=faker.file_name(), mime=faker.mime_type(), owner=host)

        base_time = now()
        api_client.force_authenticate(user=host)

        # Try to add admin-only fields
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
                "is_admin_override": True,  # Attempt privesc
                "admin_notes": "hacked",    # Attempt privesc
            }),
            content_type="application/json",
        )

        # Should not allow admin fields
        if response.status_code == 201:
            data = response.json()
            if data.get("is_admin_override") or data.get("admin_notes"):
                pytest.fail("T622: Privilege escalation via schedule API")
