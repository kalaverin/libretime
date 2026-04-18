"""Red Team security tests for SmartBlocks permissions (T238).

Tests focus on:
- API5:2023 BFLA (Broken Function Level Authorization)
- API1:2023 BOLA (cross-user access violations)
- Permission escalation attempts
- Role-based access control bypasses
- API key vs session auth differences
- Permission enumeration
"""

import json

import pytest

from model_bakery import baker

from api.core.models import Role, User
from api.schedule.models import SmartBlock
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestSmartBlockPermissionsRedTeam:
    """Red Team tests for SmartBlocks permissions."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlock.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(
        reason="T448: BOLA - LIST shows all blocks without owner filtering",
    )
    def test_bola_list_shows_all_users_blocks(self, guest_client):
        """BOLA: LIST endpoint should only show user's own blocks."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        # Create victim's private blocks
        for i in range(5):
            baker.make(
                SmartBlock,
                name=f"Victim Private Block {i}",
                kind=SmartBlock.Kind.STATIC,
                owner=victim,
            )

        # Attacker lists blocks
        response = guest_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200

        data = response.json()
        victim_blocks = [b for b in data if "Victim" in b.get("name", "")]

        assert (
            len(victim_blocks) == 0
        ), f"BOLA: Attacker can see {len(victim_blocks)} victim blocks"

    @pytest.mark.xfail(
        reason="T449: BOLA - RETRIEVE allows access to any block by ID",
    )
    def test_bola_retrieve_other_users_private_block(self, guest_client):
        """BOLA: Should NOT be able to retrieve other user's private block."""
        victim = baker.make(User, username="testred_victim")
        private_block = baker.make(
            SmartBlock,
            name="Victim Super Private Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=victim,
        )

        response = guest_client.get(f"/api/v2/smart-blocks/{private_block.id}")

        assert (
            response.status_code == 403
        ), f"BOLA: Can retrieve victim's private block (got {response.status_code})"

    @pytest.mark.xfail(reason="T450: BOLA - can enumerate block IDs")
    def test_bola_block_id_enumeration(self, guest_client):
        """BOLA: Sequential ID enumeration exposes all blocks."""
        # Create blocks with sequential IDs
        for i in range(100, 110):
            try:
                SmartBlock.objects.create(
                    id=i,
                    name=f"Block {i}",
                    kind=SmartBlock.Kind.STATIC,
                    owner=baker.make(User, username=f"testred_user_{i}"),
                )
            except Exception:
                pass

        # Try to enumerate
        found_blocks = []
        for i in range(1, 200):
            response = guest_client.get(f"/api/v2/smart-blocks/{i}")
            if response.status_code == 200:
                found_blocks.append(i)

        # Should not find blocks we don't own
        assert (
            len(found_blocks) == 0
        ), f"BOLA: Enumerated {len(found_blocks)} blocks without ownership"

    # ========================================================================
    # API5:2023 - BFLA (Broken Function Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(
        reason="T451: BFLA - admin endpoints accessible to regular users",
    )
    def test_bfla_admin_bulk_delete_accessible(self, guest_client):
        """BFLA: Bulk delete should require admin permissions."""
        # Try to access potential admin endpoint
        response = guest_client.post(
            "/api/v2/smart-blocks/bulk-delete",
            json.dumps({"ids": [1, 2, 3]}),
            content_type="application/json",
        )

        # Should be 404 (endpoint doesn't exist) or 403 (admin only)
        assert response.status_code in [
            404,
            403,
        ], f"BFLA: Bulk delete accessible with status {response.status_code}"

    def test_bfla_admin_export_not_accessible(self, guest_client):
        """BFLA: Admin export endpoint should not exist or be restricted."""
        response = guest_client.get("/api/v2/smart-blocks/export")

        # 404 is acceptable (endpoint doesn't exist)
        # 403 would mean endpoint exists but is protected
        assert response.status_code in [
            404,
            403,
        ], f"Admin export accessible with unexpected status {response.status_code}"

    @pytest.mark.xfail(
        reason="T453: BFLA - admin import accessible to regular users",
    )
    def test_bfla_admin_import_accessible(self, guest_client):
        """BFLA: Import endpoint should require admin permissions."""
        response = guest_client.post(
            "/api/v2/smart-blocks/import",
            json.dumps({"blocks": [{"name": "Imported"}]}),
            content_type="application/json",
        )

        assert response.status_code in [
            404,
            403,
        ], f"BFLA: Import accessible with status {response.status_code}"

    # ========================================================================
    # Permission Escalation
    # ========================================================================

    @pytest.mark.xfail(
        reason="T454: Privilege escalation - HOST role can do admin actions",
    )
    def test_privesc_host_to_admin_actions(self, guest_client):
        """Privilege Escalation: HOST user attempting admin actions."""
        host_user = baker.make(
            User,
            username="testred_host",
            role=Role.HOST,
        )

        # Try to create blocks for other users (admin action)
        other_user = baker.make(User, username="testred_other")
        response = guest_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Block for Other",
                    "kind": SmartBlock.Kind.STATIC,
                    "owner": other_user.id,
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            assert (
                data.get("owner") != other_user.id
            ), "Privilege Escalation: HOST created block for other user"

    @pytest.mark.xfail(
        reason="T455: Privilege escalation - DJ role can bypass restrictions",
    )
    def test_privesc_dj_role_bypass(self, guest_client):
        """Privilege Escalation: DJ user trying to modify protected blocks."""
        dj_user = baker.make(
            User,
            username="testred_dj",
            role=Role.DJ,
        )

        # DJ tries to modify blocks (might be read-only)
        response = guest_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "DJ Block",
                    "kind": SmartBlock.Kind.STATIC,
                },
            ),
            content_type="application/json",
        )

        # DJ should not be able to create blocks (if role is restricted)
        # This depends on business logic - documenting current behavior
        assert response.status_code in [
            201,
            403,
        ], f"DJ role create returned unexpected {response.status_code}"

    @pytest.mark.xfail(
        reason="T456: Privilege escalation - Guest role has unexpected access",
    )
    def test_privesc_guest_role_access(self, guest_client):
        """Privilege Escalation: Guest user checking access levels."""
        guest_user = baker.make(
            User,
            username="testred_guest",
            role=Role.GUEST,
        )

        # Guest tries various operations
        endpoints = [
            ("GET", "/api/v2/smart-blocks"),
            ("POST", "/api/v2/smart-blocks"),
            ("GET", "/api/v2/smart-blocks/1"),
            ("PATCH", "/api/v2/smart-blocks/1"),
            ("DELETE", "/api/v2/smart-blocks/1"),
        ]

        for method, url in endpoints:
            if method == "GET":
                response = guest_client.get(url)
            elif method == "POST":
                response = guest_client.post(
                    url,
                    json.dumps({"name": "Test"}),
                    content_type="application/json",
                )
            elif method == "PATCH":
                response = guest_client.patch(
                    url,
                    json.dumps({"name": "Test"}),
                    content_type="application/json",
                )
            else:
                response = guest_client.delete(url)

            # Guest should have very limited access
            assert response.status_code in [
                200,
                403,
                404,
            ], f"Guest {method} {url} returned {response.status_code}"

    # ========================================================================
    # Authentication Bypass
    # ========================================================================

    def test_auth_bypass_session_vs_api_key(self, guest_client, client):
        """Auth: Compare session auth vs API key behavior."""
        # API key auth (via guest_client fixture)
        response_api = guest_client.get("/api/v2/smart-blocks")

        # No auth (via client fixture)
        response_no_auth = client.get("/api/v2/smart-blocks")

        # Both should be treated similarly (or API key should have more access)
        assert (
            response_no_auth.status_code == 403
        ), "No auth request should be rejected"

    @pytest.mark.xfail(
        reason="T459: Auth bypass - case-insensitive authorization header accepted",
    )
    def test_auth_bypass_case_insensitive_headers(self, guest_client):
        """Auth: Case-insensitive authorization header - BUG T459.

        Lowercase 'authorization' header should be rejected same as 'Authorization'.
        """
        response = guest_client.get(
            "/api/v2/smart-blocks",
            HTTP_authorization="invalid",
        )

        # BUG: Currently returns 200
        assert response.status_code in [
            403,
            401,
        ], f"BUG T459: Case-insensitive auth bypass: {response.status_code}"

    @pytest.mark.xfail(
        reason="T460: Auth bypass - empty/malformed tokens accepted",
    )
    def test_auth_bypass_empty_token(self, guest_client):
        """Auth: Empty or malformed token - BUG T460."""
        malformed_tokens = [
            "",
            "Bearer ",
            "Bearer",
            "Token ",
            "Api-Key ",
            "null",
            "undefined",
        ]

        for token in malformed_tokens:
            response = guest_client.get(
                "/api/v2/smart-blocks",
                HTTP_AUTHORIZATION=token,
            )
            # BUG: Currently returns 200 for empty token
            assert response.status_code in [
                403,
                401,
            ], f"BUG T460: Malformed token '{token}' accepted"

    # ========================================================================
    # Permission Enumeration
    # ========================================================================

    def test_perm_enum_error_messages_consistent(self, guest_client):
        """Permission Enumeration: Error messages should be consistent.

        Same error code for non-existent resources regardless of method.
        """
        operations = [
            ("GET", "/api/v2/smart-blocks/999999"),
            ("PATCH", "/api/v2/smart-blocks/999999"),
            ("DELETE", "/api/v2/smart-blocks/999999"),
        ]

        statuses = []
        for method, url in operations:
            if method == "GET":
                response = guest_client.get(url)
            elif method == "PATCH":
                response = guest_client.patch(
                    url,
                    json.dumps({}),
                    content_type="application/json",
                )
            else:
                response = guest_client.delete(url)
            statuses.append(response.status_code)

        # All should return 404 for non-existent resource
        # (403 would indicate permission check before existence check - info leak)
        assert all(
            s == 404 for s in statuses
        ), f"Permission enumeration: different statuses {statuses}"

    def test_perm_enum_via_timing(self, guest_client):
        """Permission Enumeration: Timing differences leak permissions."""
        import time

        # Time request to existing resource (no permission)
        start = time.time()
        response1 = guest_client.get("/api/v2/smart-blocks/1")
        time_no_perm = time.time() - start

        # Time request to non-existing resource
        start = time.time()
        response2 = guest_client.get("/api/v2/smart-blocks/999999")
        time_not_exist = time.time() - start

        # Should be similar timing to not leak info
        ratio = time_no_perm / time_not_exist if time_not_exist > 0 else 1
        assert (
            0.5 < ratio < 2.0
        ), f"Timing leak: no_perm={time_no_perm:.4f}s, not_exist={time_not_exist:.4f}s"

    # ========================================================================
    # HTTP Parameter Pollution
    # ========================================================================

    def test_hpp_duplicate_permission_params(self, guest_client):
        """HPP: Duplicate permission-related parameters."""
        response = guest_client.get(
            "/api/v2/smart-blocks",
            {"owner": "user1", "owner": "user2"},
        )

        # Should handle gracefully
        assert response.status_code in [
            200,
            400,
        ], f"HPP caused {response.status_code}"

    def test_hpp_permission_override_via_query(self, guest_client):
        """HPP: Query params trying to override permissions."""
        response = guest_client.get(
            "/api/v2/smart-blocks?bypass_auth=true&admin=true",
        )

        # Should ignore query params for auth
        assert (
            response.status_code == 200
        ), "Query params affected auth (unexpected)"

    # ========================================================================
    # Mass Assignment via Permissions
    # ========================================================================

    @pytest.mark.xfail(reason="T458: Can escalate privileges via user update")
    def test_perm_mass_assignment_role_escalation(self, guest_client):
        """Permission: Try to escalate role via update."""
        user = baker.make(User, username="testred_user", role=Role.DJ)

        # Try to update own role
        response = guest_client.patch(
            "/api/v2/users/me",
            json.dumps({"role": Role.ADMIN}),
            content_type="application/json",
        )

        # Should be rejected or endpoint doesn't exist
        assert response.status_code in [
            404,
            403,
            400,
        ], f"Role escalation attempt returned {response.status_code}"

    # ========================================================================
    # API Version Bypass
    # ========================================================================

    def test_api_version_unauthorized_access(self, guest_client):
        """API Version: Try deprecated/unauthorized versions."""
        versions = ["v1", "v3", "internal", "admin", "beta"]

        for version in versions:
            response = guest_client.get(f"/api/{version}/smart-blocks")
            # Should be 404 for non-existent versions
            assert response.status_code in [
                404,
                403,
            ], f"Version {version} accessible with {response.status_code}"

    # ========================================================================
    # Cross-Origin / CORS
    # ========================================================================

    def test_cors_preflight_permissions(self, guest_client):
        """CORS: Preflight request permissions."""
        response = guest_client.options(
            "/api/v2/smart-blocks",
            HTTP_ORIGIN="https://evil.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="DELETE",
        )

        # Should not allow dangerous methods from arbitrary origins
        allowed_methods = response.get("Access-Control-Allow-Methods", "")
        if "DELETE" in allowed_methods:
            origin = response.get("Access-Control-Allow-Origin", "")
            assert (
                origin != "*" and "evil.com" not in origin
            ), "CORS allows DELETE from arbitrary origin"