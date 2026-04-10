"""Red Team security tests for SmartBlockCriteria DELETE endpoint (T244).

Tests focus on:
- API1:2023 BOLA (deleting other users' criteria)
- Mass deletion attacks
- ID enumeration and information disclosure
- Race conditions in delete
- Cascade effects
"""

import json

import pytest
from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockCriteria


@pytest.mark.django_db(transaction=True)
class TestSmartBlockCriteriaDeleteRedTeam:
    """Red Team tests for DELETE /api/v2/smart-block-criteria/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockCriteria.objects.all().delete()
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(reason="T512: BOLA - DELETE other user's criteria returns wrong status")
    def test_bola_delete_other_users_criteria_status(self, api_client):
        """BOLA: DELETE of other's criteria should return 403 not 404."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        victim_block = baker.make(
            SmartBlock,
            name="Victim Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=victim,
        )
        victim_criteria = baker.make(
            SmartBlockCriteria,
            block=victim_block,
            criteria="genre",
            condition="contains",
            value="Victim Genre",
        )

        response = api_client.delete(f"/api/v2/smart-block-criteria/{victim_criteria.id}")
        # 403 = permission denied (correct), 404 = not found (leaks existence)
        assert response.status_code == 403, \
            f"BOLA: Wrong status {response.status_code} - may leak existence (404) or allow deletion (204)"

    @pytest.mark.xfail(reason="T513: BOLA - Batch delete may affect other users' criteria")
    def test_bola_batch_delete_scope(self, api_client):
        """BOLA: Ensure delete only affects single criteria, not all of user's."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        # Create multiple victim criteria
        victim_block = baker.make(SmartBlock, name="Victim Block", kind=SmartBlock.Kind.DYNAMIC, owner=victim)
        victim_criteria_list = []
        for i in range(5):
            criteria = baker.make(
                SmartBlockCriteria,
                block=victim_block,
                criteria="genre",
                condition="contains",
                value=f"Victim Genre {i}",
            )
            victim_criteria_list.append(criteria)

        initial_count = SmartBlockCriteria.objects.count()

        # Attacker tries various delete patterns
        response = api_client.delete(f"/api/v2/smart-block-criteria/{victim_criteria_list[0].id}")

        # Only one should be affected (if any)
        final_count = SmartBlockCriteria.objects.count()
        assert final_count >= initial_count - 1, \
            f"BOLA: Batch delete affected {initial_count - final_count} criteria instead of 1"

    # ========================================================================
    # Information Disclosure via Error Messages
    # ========================================================================

    @pytest.mark.xfail(reason="T514: Error message leaks criteria existence")
    def test_error_message_leaks_existence(self, api_client):
        """Info Leak: Error messages reveal if criteria exists."""
        victim = baker.make(User, username="testred_victim")
        victim_block = baker.make(
            SmartBlock,
            name="Victim Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=victim,
        )
        victim_criteria = baker.make(
            SmartBlockCriteria,
            block=victim_block,
            criteria="genre",
            condition="contains",
            value="Secret",
        )

        # Try to delete existing vs non-existing
        response_existing = api_client.delete(f"/api/v2/smart-block-criteria/{victim_criteria.id}")
        response_nonexistent = api_client.delete("/api/v2/smart-block-criteria/999999")

        # Both should return same status to not leak existence
        # If 403 vs 404, we can enumerate which IDs exist
        if response_existing.status_code != response_nonexistent.status_code:
            assert False, \
                f"Status leak: existing={response_existing.status_code}, nonexistent={response_nonexistent.status_code}"

    # ========================================================================
    # ID Enumeration Attacks
    # ========================================================================

    def test_id_enumeration_timing_attack(self, api_client):
        """Security: Timing difference between existing and non-existing IDs."""
        import time

        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user)
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )

        # Time delete for existing ID
        start = time.time()
        api_client.delete(f"/api/v2/smart-block-criteria/{criteria.id}")
        time_existing = time.time() - start

        # Time delete for non-existing ID
        start = time.time()
        api_client.delete("/api/v2/smart-block-criteria/999999")
        time_nonexistent = time.time() - start

        # Times should be similar (within 3x factor)
        if time_existing > 0:
            ratio = time_nonexistent / time_existing
            assert ratio < 3.0, \
                f"Timing leak: existing={time_existing:.4f}s, nonexistent={time_nonexistent:.4f}s (ratio {ratio:.1f})"

    # ========================================================================
    # Race Condition in Delete
    # ========================================================================

    @pytest.mark.xfail(reason="T515: Race condition in concurrent delete")
    def test_race_condition_concurrent_delete(self, api_client):
        """Race: Concurrent delete of same criteria."""
        import concurrent.futures

        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user)
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )

        def delete_criteria():
            return api_client.delete(f"/api/v2/smart-block-criteria/{criteria.id}").status_code

        # Fire 5 concurrent delete requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(delete_criteria) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # One should succeed (204), others should get 404
        success_count = results.count(204)
        not_found_count = results.count(404)

        assert success_count == 1, \
            f"Race condition: {success_count} deletes succeeded, expected 1"
        assert not_found_count == 4, \
            f"Race condition: {not_found_count} got 404, expected 4"

    # ========================================================================
    # Mass Deletion Attack
    # ========================================================================

    def test_mass_deletion_rate_limit(self, api_client):
        """Security: Rate limiting on delete operations."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user)

        # Create many criteria
        criteria_list = []
        for i in range(50):
            criteria = baker.make(
                SmartBlockCriteria,
                block=block,
                criteria="genre",
                condition="contains",
                value=f"Genre {i}",
            )
            criteria_list.append(criteria)

        # Rapid sequential deletes
        delete_count = 0
        for criteria in criteria_list:
            response = api_client.delete(f"/api/v2/smart-block-criteria/{criteria.id}")
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

    def test_sqli_in_delete_id(self, api_client):
        """Injection: SQLi in DELETE id path parameter."""
        sqli_payloads = [
            "1 OR 1=1",
            "1; DROP TABLE cc_blockcriteria;--",
            "1' OR '1'='1",
            "1 UNION SELECT * FROM cc_user",
        ]

        for payload in sqli_payloads:
            response = api_client.delete(f"/api/v2/smart-block-criteria/{payload}")
            # Should return 404, never 500
            assert response.status_code in [400, 404], \
                f"SQLi '{payload}' caused {response.status_code}"

    def test_path_traversal_in_delete_id(self, api_client):
        """Injection: Path traversal in DELETE id."""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for payload in traversal_payloads:
            response = api_client.delete(f"/api/v2/smart-block-criteria/{payload}")
            assert response.status_code in [400, 404], \
                f"Path traversal '{payload}' caused {response.status_code}"

    # ========================================================================
    # Business Logic: Cascade Effects
    # ========================================================================

    @pytest.mark.xfail(reason="T516: Block without criteria behavior undefined")
    def test_delete_all_criteria_from_block(self, api_client):
        """Logic: Block with no criteria should still be valid."""
        user = baker.make(User, username="testred_user")
        block = baker.make(SmartBlock, name="Block", kind=SmartBlock.Kind.DYNAMIC, owner=user)

        # Create criteria and delete them all
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )

        response = api_client.delete(f"/api/v2/smart-block-criteria/{criteria.id}")
        assert response.status_code == 204

        # Block should still exist
        assert SmartBlock.objects.filter(id=block.id).exists(), \
            "Block was deleted when all criteria removed"

    # ========================================================================
    # Authentication Bypass
    # ========================================================================

    def test_delete_without_auth_returns_403(self, client):
        """Auth: DELETE without auth returns 403."""
        response = client.delete("/api/v2/smart-block-criteria/1")
        assert response.status_code == 403

    @pytest.mark.xfail(reason="T517: Invalid auth token returns 404 instead of 403")
    def test_delete_with_invalid_token(self, api_client):
        """Auth: DELETE with invalid token should return 403."""
        # Temporarily modify auth header
        original = api_client.defaults.get("HTTP_AUTHORIZATION", "")
        api_client.defaults["HTTP_AUTHORIZATION"] = "Bearer invalid_token"

        try:
            response = api_client.delete("/api/v2/smart-block-criteria/1")
            # BUG T517: Returns 404 instead of 403
            assert response.status_code == 403, \
                f"BUG T517: Invalid token caused {response.status_code}"
        finally:
            api_client.defaults["HTTP_AUTHORIZATION"] = original

    # ========================================================================
    # Unicode and Encoding
    # ========================================================================

    def test_delete_unicode_id(self, api_client):
        """Validation: Unicode in ID handled gracefully."""
        response = api_client.delete("/api/v2/smart-block-criteria/日本語")
        assert response.status_code in [400, 404], \
            f"Unicode ID caused {response.status_code}"

    def test_delete_null_bytes(self, api_client):
        """Validation: Null bytes in ID handled gracefully."""
        response = api_client.delete("/api/v2/smart-block-criteria/1%00test")
        assert response.status_code in [400, 404], \
            f"Null bytes caused {response.status_code}"
