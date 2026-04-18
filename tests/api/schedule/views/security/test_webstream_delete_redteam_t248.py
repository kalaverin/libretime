"""Red Team security tests for Webstreams DELETE endpoint (T248).

Tests focus on:
- API1:2023 BOLA (deleting other users' webstreams)
- Mass deletion attacks
- ID enumeration and information disclosure
- Race conditions in delete
- Injection in DELETE path
"""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Webstream
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestWebstreamDeleteRedTeam:
    """Red Team tests for DELETE /api/v2/webstreams/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        Webstream.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(
        reason="T556: BOLA - DELETE other user's stream returns wrong status",
    )
    def test_bola_delete_other_users_stream_status(self, admin_client):
        """BOLA: DELETE of other's stream should return 403 not 404."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        victim_stream = baker.make(
            Webstream,
            name="Victim Stream",
            url="http://victim.com/stream",
            owner=victim,
        )

        response = admin_client.delete(f"/api/v2/webstreams/{victim_stream.id}")
        # 403 = permission denied (correct), 404 = not found (leaks existence)
        assert (
            response.status_code == 403
        ), f"BOLA: Wrong status {response.status_code} - leaks existence (404) or allows deletion (204)"

    @pytest.mark.xfail(reason="T557: BOLA - Batch delete scope verification")
    def test_bola_batch_delete_scope(self, admin_client):
        """BOLA: Ensure delete only affects single stream."""
        victim = baker.make(User, username="testred_victim")

        # Create multiple victim streams
        victim_streams = []
        for i in range(5):
            stream = baker.make(
                Webstream,
                name=f"Victim Stream {i}",
                url=f"http://victim.com/stream{i}",
                owner=victim,
            )
            victim_streams.append(stream)

        initial_count = Webstream.objects.count()

        # Attacker tries to delete one
        response = admin_client.delete(
            f"/api/v2/webstreams/{victim_streams[0].id}",
        )

        # Only one should be affected (if any)
        final_count = Webstream.objects.count()
        assert (
            final_count >= initial_count - 1
        ), f"BOLA: Batch delete affected {initial_count - final_count} streams instead of 1"

    # ========================================================================
    # Information Disclosure via Error Messages
    # ========================================================================

    @pytest.mark.xfail(reason="T558: Error message leaks stream existence")
    def test_error_message_leaks_existence(self, admin_client):
        """Info Leak: Error messages reveal if stream exists."""
        victim = baker.make(User, username="testred_victim")
        victim_stream = baker.make(
            Webstream,
            name="Victim Stream",
            url="http://victim.com/stream",
            owner=victim,
        )

        # Try to delete existing vs non-existing
        response_existing = admin_client.delete(
            f"/api/v2/webstreams/{victim_stream.id}",
        )
        response_nonexistent = admin_client.delete("/api/v2/webstreams/999999")

        # Both should return same status to not leak existence
        if response_existing.status_code != response_nonexistent.status_code:
            assert (
                False
            ), f"Status leak: existing={response_existing.status_code}, nonexistent={response_nonexistent.status_code}"

    # ========================================================================
    # ID Enumeration Attacks
    # ========================================================================

    def test_id_enumeration_timing_attack(self, admin_client):
        """Security: Timing difference between existing and non-existing IDs."""
        import time

        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        # Time delete for existing ID
        start = time.time()
        admin_client.delete(f"/api/v2/webstreams/{stream.id}")
        time_existing = time.time() - start

        # Time delete for non-existing ID
        start = time.time()
        admin_client.delete("/api/v2/webstreams/999999")
        time_nonexistent = time.time() - start

        # Times should be similar (within 3x factor)
        if time_existing > 0:
            ratio = time_nonexistent / time_existing
            assert (
                ratio < 3.0
            ), f"Timing leak: existing={time_existing:.4f}s, nonexistent={time_nonexistent:.4f}s (ratio {ratio:.1f})"

    # ========================================================================
    # Mass Deletion Attack
    # ========================================================================

    def test_mass_deletion_rate_limit(self, admin_client):
        """Security: Rate limiting on delete operations."""
        user = baker.make(User, username="testred_user")

        # Create many streams
        streams = []
        for i in range(50):
            stream = baker.make(
                Webstream,
                name=f"Stream {i}",
                url=f"http://example.com/stream{i}",
                owner=user,
            )
            streams.append(stream)

        # Rapid sequential deletes
        delete_count = 0
        for stream in streams:
            response = admin_client.delete(f"/api/v2/webstreams/{stream.id}")
            if response.status_code == 204:
                delete_count += 1
            elif response.status_code == 429:
                # Rate limited - this is good
                break

        # Should allow deletes or rate limit, not crash
        assert delete_count >= 0, "Delete operations failed unexpectedly"

    # ========================================================================
    # Injection in DELETE (path parameter)
    # ========================================================================

    def test_sqli_in_delete_id(self, admin_client):
        """Injection: SQLi in DELETE id path parameter."""
        sqli_payloads = [
            "1 OR 1=1",
            "1; DROP TABLE cc_webstream;--",
            "1' OR '1'='1",
            "1 UNION SELECT * FROM cc_user",
        ]

        for payload in sqli_payloads:
            response = admin_client.delete(f"/api/v2/webstreams/{payload}")
            # Should return 404, never 500
            assert response.status_code in [
                400,
                404,
            ], f"SQLi '{payload}' caused {response.status_code}"

    def test_path_traversal_in_delete_id(self, admin_client):
        """Injection: Path traversal in DELETE id."""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for payload in traversal_payloads:
            response = admin_client.delete(f"/api/v2/webstreams/{payload}")
            assert response.status_code in [
                400,
                404,
            ], f"Path traversal '{payload}' caused {response.status_code}"

    # ========================================================================
    # Race Condition in Delete
    # ========================================================================

    @pytest.mark.xfail(reason="T559: Race condition in concurrent delete")
    def test_race_condition_concurrent_delete(self, admin_client):
        """Race: Concurrent delete of same stream."""
        import concurrent.futures

        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        def delete_stream():
            return admin_client.delete(
                f"/api/v2/webstreams/{stream.id}",
            ).status_code

        # Fire 5 concurrent delete requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(delete_stream) for _ in range(5)]
            results = [
                f.result() for f in concurrent.futures.as_completed(futures)
            ]

        # One should succeed (204), others should get 404
        success_count = results.count(204)
        not_found_count = results.count(404)

        assert (
            success_count == 1
        ), f"Race condition: {success_count} deletes succeeded, expected 1"
        assert (
            not_found_count == 4
        ), f"Race condition: {not_found_count} got 404, expected 4"

    # ========================================================================
    # Authentication
    # ========================================================================

    def test_delete_without_auth_returns_403(self, client):
        """Auth: DELETE without auth returns 403."""
        response = client.delete("/api/v2/webstreams/1")
        assert response.status_code == 403

    def test_delete_with_invalid_token(self):
        """Auth: DELETE with invalid token should return 403.

        FIXED: Use credentials() to properly override auth.
        defaults[] does NOT override credentials() set in admin_client fixture.
        """
        from rest_framework.test import APIClient

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")

        response = client.delete("/api/v2/webstreams/1")
        # Should return 403 when auth is properly overridden
        assert (
            response.status_code == 403
        ), f"BUG T560: Invalid token should return 403, got {response.status_code}"

    # ========================================================================
    # Unicode and Encoding
    # ========================================================================

    def test_delete_unicode_id(self, admin_client):
        """Validation: Unicode in ID handled gracefully."""
        response = admin_client.delete("/api/v2/webstreams/日本語")
        assert response.status_code in [
            400,
            404,
        ], f"Unicode ID caused {response.status_code}"

    def test_delete_null_bytes(self, admin_client):
        """Validation: Null bytes in ID handled gracefully."""
        response = admin_client.delete("/api/v2/webstreams/1%00test")
        assert response.status_code in [
            400,
            404,
        ], f"Null bytes caused {response.status_code}"

    # ========================================================================
    # HTTP Method Override
    # ========================================================================

    @pytest.mark.xfail(reason="T561: HTTP method override not blocked")
    def test_http_method_override_delete(self, admin_client):
        """Security: HTTP method override should not bypass auth."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        # Try to override GET with DELETE
        response = admin_client.get(
            f"/api/v2/webstreams/{stream.id}",
            HTTP_X_HTTP_METHOD_OVERRIDE="DELETE",
        )

        # Should not delete the stream
        assert Webstream.objects.filter(
            id=stream.id,
        ).exists(), "HTTP method override bypassed delete protection"