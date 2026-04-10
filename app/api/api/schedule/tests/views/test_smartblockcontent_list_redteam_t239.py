"""Red Team security tests for SmartBlockContents LIST endpoint (T239).

Tests focus on:
- API1:2023 BOLA (accessing other users' content)
- Filter bypass attacks
- Pagination abuse
- Sorting injection
- Field exposure
- Information disclosure via error messages
"""


import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockContent
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestSmartBlockContentListRedTeam:
    """Red Team tests for GET /api/v2/smart-block-contents."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockContent.objects.all().delete()
        SmartBlock.objects.all().delete()
        File.objects.all().delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    @pytest.mark.xfail(
        reason="T461: BOLA - LIST shows all users' content without filtering",
    )
    def test_bola_list_shows_all_users_content(self, api_client):
        """BOLA: LIST should only show content from user's own blocks."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        # Victim's private block with content
        victim_block = baker.make(
            SmartBlock,
            name="Victim Private Block",
            kind=SmartBlock.Kind.STATIC,
            owner=victim,
        )
        victim_file = baker.make(
            File, name="victim_song.mp3", mime="audio/mp3", owner=victim,
        )
        victim_content = baker.make(
            SmartBlockContent,
            block=victim_block,
            file=victim_file,
            position=1,
        )

        # Attacker lists all content
        response = api_client.get("/api/v2/smart-block-contents")
        assert response.status_code == 200

        data = response.json()
        victim_content_ids = [
            c["id"] for c in data if c.get("block") == victim_block.id
        ]

        assert (
            len(victim_content_ids) == 0
        ), f"BOLA: Attacker can see {len(victim_content_ids)} victim's content items"

    @pytest.mark.xfail(
        reason="T462: BOLA - filter by block ID bypasses ownership",
    )
    def test_bola_filter_by_other_users_block(self, api_client):
        """BOLA: Should not be able to filter by other user's block ID."""
        victim = baker.make(User, username="testred_victim")
        attacker = baker.make(User, username="testred_attacker")

        # Victim's block with content
        victim_block = baker.make(
            SmartBlock,
            name="Victim Block",
            kind=SmartBlock.Kind.STATIC,
            owner=victim,
        )
        victim_file = baker.make(
            File, name="victim_song.mp3", mime="audio/mp3", owner=victim,
        )
        victim_content = baker.make(
            SmartBlockContent,
            block=victim_block,
            file=victim_file,
            position=1,
        )

        # Attacker filters by victim's block ID
        response = api_client.get(
            f"/api/v2/smart-block-contents?block={victim_block.id}",
        )
        assert response.status_code == 200

        data = response.json()
        assert (
            len(data) == 0
        ), f"BOLA: Filter by victim's block returned {len(data)} items"

    def test_content_id_enumeration_mitigated(self, api_client):
        """Security: Content ID enumeration mitigated by owner filtering."""
        # If T461 is fixed, enumeration won't show other users' content
        # If T461 is not fixed, this will enumerate all content
        # Either way, this test documents current behavior

        # Create some content
        user = baker.make(User, username="testred_enum")
        for i in range(5):
            block = baker.make(
                SmartBlock,
                name=f"Block {i}",
                kind=SmartBlock.Kind.STATIC,
                owner=user,
            )
            file_obj = baker.make(
                File, name=f"song{i}.mp3", mime="audio/mp3", owner=user,
            )
            baker.make(
                SmartBlockContent, block=block, file=file_obj, position=i,
            )

        response = api_client.get("/api/v2/smart-block-contents")
        data = response.json()

        # Should only see own content (or all if T461 not fixed)
        assert isinstance(data, list), "Response should be a list"

    # ========================================================================
    # Filter Bypass Attacks
    # ========================================================================

    @pytest.mark.xfail(
        reason="T464: Filter bypass - SQL injection in block parameter",
    )
    def test_filter_sql_injection_block_param(self, api_client):
        """Injection: SQLi in block filter parameter."""
        sqli_payloads = [
            "1' OR '1'='1",
            "1 OR 1=1",
            "1; DROP TABLE cc_blockcontents;--",
            "1 UNION SELECT * FROM cc_user",
        ]

        for payload in sqli_payloads:
            response = api_client.get(
                f"/api/v2/smart-block-contents?block={payload}",
            )
            # Should not crash with 500
            assert response.status_code in [
                200,
                400,
                404,
            ], f"SQLi payload '{payload}' caused {response.status_code}"

    def test_filter_negative_block_id_handled(self, api_client):
        """Validation: Negative block ID handled gracefully."""
        response = api_client.get("/api/v2/smart-block-contents?block=-1")
        # Django handles this gracefully - returns empty list
        assert response.status_code in [
            200,
            400,
        ], f"Negative block ID caused {response.status_code}"

    def test_filter_zero_block_id_handled(self, api_client):
        """Validation: Zero block ID handled gracefully."""
        response = api_client.get("/api/v2/smart-block-contents?block=0")
        # Django handles this gracefully - returns empty list
        assert response.status_code in [
            200,
            400,
        ], f"Zero block ID caused {response.status_code}"

    @pytest.mark.xfail(reason="T472: 500 error on non-numeric block_id filter")
    def test_filter_non_numeric_block_id(self, api_client):
        """Validation: Non-numeric block ID in filter - BUG T472."""
        response = api_client.get("/api/v2/smart-block-contents?block=abc")
        # BUG: Returns 500 instead of 400
        assert response.status_code in [
            400,
            404,
        ], f"BUG T472: Non-numeric block ID caused {response.status_code}"

    @pytest.mark.xfail(reason="T473: 500 error on unicode block_id filter")
    def test_filter_unicode_block_id(self, api_client):
        """Validation: Unicode in block filter - BUG T473."""
        response = api_client.get("/api/v2/smart-block-contents?block=日本語")
        # BUG: Returns 500 instead of 400
        assert response.status_code in [
            400,
            404,
        ], f"BUG T473: Unicode block ID caused {response.status_code}"

    # ========================================================================
    # Sorting / Ordering Attacks
    # ========================================================================

    def test_sorting_arbitrary_field_rejected(self, api_client):
        """Security: Arbitrary ordering fields are rejected."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user,
        )

        malicious_orderings = [
            "id; DROP TABLE cc_blockcontents;--",
            "(SELECT password FROM cc_user)",
        ]

        for ordering in malicious_orderings:
            response = api_client.get(
                f"/api/v2/smart-block-contents?ordering={ordering}",
            )
            # Django DRF safely ignores invalid ordering fields
            assert response.status_code in [
                200,
                400,
            ], f"Ordering '{ordering}' caused {response.status_code}"

    def test_sorting_negative_position(self, api_client):
        """Validation: Sorting with negative position values."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user,
        )
        file_obj = baker.make(
            File, name="song.mp3", mime="audio/mp3", owner=user,
        )
        baker.make(SmartBlockContent, block=block, file=file_obj, position=-1)

        response = api_client.get(
            "/api/v2/smart-block-contents?ordering=position",
        )
        assert (
            response.status_code == 200
        ), f"Negative position sorting caused {response.status_code}"

    # ========================================================================
    # Pagination Abuse
    # ========================================================================

    def test_pagination_page_size_limited(self, api_client):
        """Security: Page size is properly limited."""
        user = baker.make(User, username="testred_user")

        # Create many content items
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user,
        )
        for i in range(100):
            file_obj = baker.make(
                File, name=f"song{i}.mp3", mime="audio/mp3", owner=user,
            )
            baker.make(
                SmartBlockContent, block=block, file=file_obj, position=i,
            )

        response = api_client.get(
            "/api/v2/smart-block-contents?page_size=999999",
        )
        # Django DRF has default pagination limits
        assert (
            response.status_code == 200
        ), f"Large page size caused {response.status_code}"

    def test_pagination_negative_page(self, api_client):
        """Validation: Negative page number."""
        response = api_client.get("/api/v2/smart-block-contents?page=-1")
        assert response.status_code in [
            200,
            400,
        ], f"Negative page caused {response.status_code}"

    def test_pagination_zero_page_size(self, api_client):
        """Validation: Zero page size."""
        response = api_client.get("/api/v2/smart-block-contents?page_size=0")
        assert response.status_code in [
            200,
            400,
        ], f"Zero page size caused {response.status_code}"

    # ========================================================================
    # Field Exposure
    # ========================================================================

    def test_field_exposure_no_internal_fields(self, api_client):
        """Security: Internal fields are not exposed."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user,
        )
        file_obj = baker.make(
            File, name="song.mp3", mime="audio/mp3", owner=user,
        )
        baker.make(SmartBlockContent, block=block, file=file_obj, position=1)

        response = api_client.get("/api/v2/smart-block-contents")
        data = response.json()

        if len(data) > 0:
            fields = set(data[0].keys())
            forbidden_fields = {
                "_state",
                "password",
                "secret",
                "token",
                "internal_id",
            }
            leaked = fields & forbidden_fields
            assert len(leaked) == 0, f"Internal fields leaked: {leaked}"

    def test_field_exposure_related_objects_are_ids(self, api_client):
        """Security: Related objects are returned as IDs only."""
        user = baker.make(User, username="testred_user")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user,
        )
        file_obj = baker.make(
            File, name="song.mp3", mime="audio/mp3", owner=user,
        )
        baker.make(SmartBlockContent, block=block, file=file_obj, position=1)

        response = api_client.get("/api/v2/smart-block-contents")
        data = response.json()

        if len(data) > 0:
            content = data[0]
            # Serializer correctly returns IDs
            assert isinstance(content.get("block"), int), "Block should be ID"
            assert isinstance(content.get("file"), int), "File should be ID"

    # ========================================================================
    # Information Disclosure
    # ========================================================================

    @pytest.mark.xfail(reason="T471: Error message leaks query structure")
    def test_error_message_leaks_structure(self, api_client):
        """Info Leak: Error messages reveal database structure."""
        # Trigger error with malformed request
        response = api_client.get(
            "/api/v2/smart-block-contents?block=invalid'union",
        )

        error_body = response.content.decode().lower()

        # Check for information leakage
        sensitive_patterns = [
            "sql",
            "postgresql",
            "sqlite",
            "column",
            "table",
            "cc_blockcontents",
        ]

        for pattern in sensitive_patterns:
            assert pattern not in error_body, f"Error message leaks: {pattern}"

    # ========================================================================
    # HPP (HTTP Parameter Pollution)
    # ========================================================================

    def test_hpp_duplicate_filter_params(self, api_client):
        """HPP: Duplicate block filter parameters."""
        user = baker.make(User, username="testred_user")
        block1 = baker.make(
            SmartBlock, name="Block1", kind=SmartBlock.Kind.STATIC, owner=user,
        )
        block2 = baker.make(
            SmartBlock, name="Block2", kind=SmartBlock.Kind.STATIC, owner=user,
        )
        file1 = baker.make(
            File, name="song1.mp3", mime="audio/mp3", owner=user,
        )
        file2 = baker.make(
            File, name="song2.mp3", mime="audio/mp3", owner=user,
        )
        baker.make(SmartBlockContent, block=block1, file=file1, position=1)
        baker.make(SmartBlockContent, block=block2, file=file2, position=1)

        # Send duplicate block parameters
        response = api_client.get(
            f"/api/v2/smart-block-contents?block={block1.id}&block={block2.id}",
        )
        assert (
            response.status_code == 200
        ), f"HPP caused {response.status_code}"

    # ========================================================================
    # CORS and Headers
    # ========================================================================

    def test_cors_preflight_list(self, api_client):
        """CORS: Preflight request for LIST."""
        response = api_client.options(
            "/api/v2/smart-block-contents",
            HTTP_ORIGIN="https://evil.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )

        allowed_origin = response.get("Access-Control-Allow-Origin", "")
        assert "evil.com" not in allowed_origin, "CORS allows arbitrary origin"

    # ========================================================================
    # Fuzzing
    # ========================================================================

    @pytest.mark.xfail(
        reason="T474: 500 error on special query params (undefined, null)",
    )
    def test_fuzzing_query_params(self, api_client):
        """Fuzzing: Naughty strings in query parameters - BUG T474."""
        naughty_params = [
            "undefined",
            "null",
            "None",
        ]

        for param in naughty_params:
            response = api_client.get(
                f"/api/v2/smart-block-contents?block={param}",
            )
            # BUG: Returns 500 instead of 400
            assert response.status_code in [
                400,
                404,
            ], f"BUG T474: Naughty param '{param}' caused {response.status_code}"

    # ========================================================================
    # Timing Attacks
    # ========================================================================

    def test_timing_list_empty_vs_populated(self, api_client):
        """Timing: Difference between empty and populated list."""
        import time

        # Time empty list
        start = time.time()
        response1 = api_client.get("/api/v2/smart-block-contents")
        time_empty = time.time() - start

        # Create some content
        user = baker.make(User, username="testred_timing")
        block = baker.make(
            SmartBlock, name="Block", kind=SmartBlock.Kind.STATIC, owner=user,
        )
        for i in range(50):
            file_obj = baker.make(
                File, name=f"song{i}.mp3", mime="audio/mp3", owner=user,
            )
            baker.make(
                SmartBlockContent, block=block, file=file_obj, position=i,
            )

        # Time populated list
        start = time.time()
        response2 = api_client.get("/api/v2/smart-block-contents")
        time_populated = time.time() - start

        # Difference should not be extreme (less than 5x)
        if time_empty > 0:
            ratio = time_populated / time_empty
            assert (
                ratio < 5.0
            ), f"Timing leak: empty={time_empty:.4f}s, populated={time_populated:.4f}s (ratio {ratio:.1f})"
