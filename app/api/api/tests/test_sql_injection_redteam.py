"""
Paranoid SQL Injection and Invalid ID tests.

Tests:
- T490: SQLi in SmartBlockCriteria block_id filter
- T356: Invalid ID in SmartBlockContent → 500 error
- T357: Invalid ID in PlaylistContent → 500 error
- T367: Filter crash in SmartBlockCriteria block_id
- T613: SQLi in Schedule overbooked filter
- T814: SQLi in Playlist length field

Usage:
    cd app/api && uv run pytest api/tests/test_sql_injection_redteam.py -v
"""

import pytest

from model_bakery import baker

from api.schedule.models import (
    Playlist,
    SmartBlock,
    SmartBlockCriteria,
)
from api.storage.models import File

# =============================================================================
# SQL Injection in ID Fields (T490, T367)
# =============================================================================


@pytest.mark.django_db
class TestSQLInjectionBlockId:
    """SQL Injection tests for block_id parameter (T490, T367)."""

    def test_smartblock_criteria_block_id_sqli_union(
        self, host_client, host_user, faker,
    ):
        """T490: UNION-based SQLi in block_id filter should be rejected."""
        # Create some criteria first
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )
        baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="0",
            value="Rock",
        )

        # Try SQL injection in block_id query param
        sqli_payloads = [
            "1 UNION SELECT * FROM auth_user",
            "1 OR 1=1",
            "1' OR '1'='1",
            "1; DROP TABLE cc_block--",
            "1) OR (1=1",
        ]

        for payload in sqli_payloads:
            response = host_client.get(
                "/api/v2/smart-block-criteria",
                {"block": payload},
            )
            # Should get 200 with empty results (not 500 or data leak)
            assert (
                response.status_code == 200
            ), f"SQLi payload should not cause error, got {response.status_code}"
            # Should return empty results (no data leak)
            results = (
                response.data
                if isinstance(response.data, list)
                else response.data.get("results", [])
            )
            assert (
                len(results) == 0
            ), f"SQLi payload '{payload}' should return empty results"

    def test_smartblock_criteria_invalid_block_id_format(
        self, host_client, host_user, faker,
    ):
        """T367: Invalid block_id format should not cause 500."""
        invalid_ids = [
            "not-an-id",
            "abc123",
            "1.5",
            "1,2,3",
            "true",
            "false",
            "null",
            "",
            "   ",
        ]

        for invalid_id in invalid_ids:
            response = host_client.get(
                "/api/v2/smart-block-criteria",
                {"block": invalid_id},
            )
            # Should not cause 500 (server error)
            assert (
                response.status_code != 500
            ), f"Invalid block_id '{invalid_id}' should not cause 500"
            # Should return 200 with empty results (safe behavior)
            assert (
                response.status_code == 200
            ), f"Invalid block_id '{invalid_id}' should return 200, got {response.status_code}"

    def test_smartblock_criteria_negative_block_id_rejected(
        self, host_client, host_user, faker,
    ):
        """Negative block_id should not cause 500 and return safe result."""
        response = host_client.get(
            "/api/v2/smart-block-criteria",
            {"block": "-1"},
        )
        # Should not cause 500
        assert (
            response.status_code != 500
        ), "Negative block_id should not cause 500"
        # Should return 200 with empty results
        assert (
            response.status_code == 200
        ), f"Negative block_id should return 200, got {response.status_code}"

    def test_smartblock_criteria_zero_block_id_rejected(
        self, host_client, host_user, faker,
    ):
        """Zero block_id should not cause 500 and return safe result."""
        response = host_client.get(
            "/api/v2/smart-block-criteria",
            {"block": "0"},
        )
        # Should not cause 500
        assert (
            response.status_code != 500
        ), "Zero block_id should not cause 500"
        # Should return 200 with empty results
        assert (
            response.status_code == 200
        ), f"Zero block_id should return 200, got {response.status_code}"

    def test_smartblock_criteria_create_with_invalid_block_id(
        self, host_client, host_user, faker,
    ):
        """Creating SmartBlockCriteria with invalid block_id should fail."""
        data = {
            "block": "invalid-id",
            "criteria": "title",
            "condition": "0",
            "value": "test",
        }

        response = host_client.post(
            "/api/v2/smart-block-criteria", data, format="json",
        )
        assert (
            response.status_code == 400
        ), f"Invalid block_id in POST should return 400, got {response.status_code}"


# =============================================================================
# Invalid ID → 500 Error Tests (T356)
# =============================================================================


@pytest.mark.django_db
class TestInvalidIDHandling:
    """Invalid ID handling tests (T356, T357)."""

    def test_smartblock_content_invalid_block_id_500(
        self, host_client, host_user, faker,
    ):
        """T356: Invalid block_id in SmartBlockContent should not cause 500."""
        invalid_ids = [
            "not-an-id",
            "abc",
            "1.5",
            "true",
            "",
        ]

        for invalid_id in invalid_ids:
            response = host_client.get(
                "/api/v2/smart-block-contents",
                {"block": invalid_id},
            )
            # Should not cause 500
            assert (
                response.status_code != 500
            ), f"Server error (500) for invalid block_id '{invalid_id}'"
            # Should return 200 with empty results
            assert (
                response.status_code == 200
            ), f"Invalid block_id '{invalid_id}' should return 200, got {response.status_code}"

    def test_smartblock_content_create_invalid_block_id(
        self, host_client, host_user, faker,
    ):
        """T356: Creating with invalid block_id should return 400."""
        file_obj = baker.make(
            File,
            name=f"test_{faker.uuid4()[:8]}.mp3",
            owner=host_user,
            mime="audio/mpeg",
            filepath=f"test/{faker.uuid4()[:8]}.mp3",
        )

        data = {
            "block": "not-an-id",
            "file": file_obj.id,
            "offset": 0,
        }

        response = host_client.post(
            "/api/v2/smart-block-contents", data, format="json",
        )
        assert (
            response.status_code == 400
        ), f"Invalid block_id in POST should return 400, got {response.status_code}"

    def test_playlist_content_invalid_playlist_id_500(
        self, host_client, host_user, faker,
    ):
        """T357: Invalid playlist_id in PlaylistContent should not cause 500."""
        invalid_ids = [
            "not-an-id",
            "abc",
            "1.5",
            "true",
            "",
        ]

        for invalid_id in invalid_ids:
            response = host_client.get(
                "/api/v2/playlist-contents",
                {"playlist": invalid_id},
            )
            # Should not cause 500
            assert (
                response.status_code != 500
            ), f"Server error (500) for invalid playlist_id '{invalid_id}'"
            # Should return 200 with empty results
            assert (
                response.status_code == 200
            ), f"Invalid playlist_id '{invalid_id}' should return 200, got {response.status_code}"

    def test_playlist_content_create_invalid_playlist_id(
        self, host_client, host_user, faker,
    ):
        """T357: Creating with invalid playlist_id should return 400."""
        file_obj = baker.make(
            File,
            name=f"test_{faker.uuid4()[:8]}.mp3",
            owner=host_user,
            mime="audio/mpeg",
            filepath=f"test/{faker.uuid4()[:8]}.mp3",
        )

        data = {
            "playlist": "not-an-id",
            "file": file_obj.id,
            "kind": 0,  # FILE
        }

        response = host_client.post(
            "/api/v2/playlist-contents", data, format="json",
        )
        assert (
            response.status_code == 400
        ), f"Invalid playlist_id in POST should return 400, got {response.status_code}"


# =============================================================================
# SQL Injection in Length Field (T814) - Django ORM Protection
# =============================================================================


@pytest.mark.django_db
class TestSQLInjectionLengthFieldORMProtection:
    """Verify Django ORM protects against SQLi in length field (T814).

    Django uses parameterized queries - SQLi in text fields is automatically
    escaped. The format validator rejects invalid formats, but SQLi patterns
    in valid format strings are handled by ORM.
    """

    def test_playlist_length_sqli_stored_as_text(
        self, host_client, host_user, faker,
    ):
        """T814: SQLi patterns in length are stored safely via ORM escaping."""
        # Valid time format with SQLi appended - should fail format validation
        data = {
            "name": f"Test Playlist {faker.uuid4()[:8]}",
            "length": "00:05:00'; DROP TABLE cc_playlist--",
        }

        response = host_client.post("/api/v2/playlists", data, format="json")
        # Should fail format validation (not SQLi, just invalid format)
        assert (
            response.status_code == 400
        ), f"Invalid length format should be rejected, got {response.status_code}"

    def test_playlist_content_length_valid_with_sqli_appended(
        self, host_client, host_user, faker,
    ):
        """SQLi appended to valid length is rejected by format validator."""
        playlist = baker.make(
            Playlist,
            name=f"Test Playlist {faker.uuid4()[:8]}",
            owner=host_user,
        )
        file_obj = baker.make(
            File,
            name=f"test_{faker.uuid4()[:8]}.mp3",
            owner=host_user,
            mime="audio/mpeg",
            filepath=f"test/{faker.uuid4()[:8]}.mp3",
        )

        data = {
            "playlist": playlist.id,
            "file": file_obj.id,
            "kind": 0,
            "length": "00:05:00'; DROP TABLE--",
        }

        response = host_client.post(
            "/api/v2/playlist-contents", data, format="json",
        )
        # Should fail format validation
        assert (
            response.status_code == 400
        ), f"Invalid length format should be rejected, got {response.status_code}"


# =============================================================================
# SQL Injection in Value Field (T490) - Django ORM Protection
# =============================================================================


@pytest.mark.django_db
class TestSQLInjectionValueFieldORMProtection:
    """Verify Django ORM protects against SQLi in value field (T490).

    Django uses parameterized queries - SQLi in text fields is automatically
    escaped. These tests verify that malicious values are stored as-is text,
    not executed as SQL.
    """

    def test_smartblock_criteria_value_sqli_stored_as_text(
        self, host_client, host_user, faker,
    ):
        """T490: SQLi patterns in value are stored as text, not executed."""
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )

        # These should be stored as text, not cause SQL errors
        sqli_payloads = [
            "'; DROP TABLE cc_block--",
            "' UNION SELECT * FROM auth_user--",
            "' OR '1'='1",
        ]

        for payload in sqli_payloads:
            data = {
                "block": block.id,
                "criteria": "genre",
                "condition": "0",
                "value": payload,
            }

            response = host_client.post(
                "/api/v2/smart-block-criteria", data, format="json",
            )
            # Should succeed - Django ORM escapes the value
            assert (
                response.status_code == 201
            ), f"SQLi value '{payload}' should be stored as text, got {response.status_code}"
            # Verify the value is stored exactly as provided
            assert response.data["value"] == payload


# =============================================================================
# Valid ID Tests
# =============================================================================


@pytest.mark.django_db
class TestValidIDHandling:
    """Valid ID handling tests."""

    def test_smartblock_criteria_valid_block_id(
        self, host_client, host_user, faker,
    ):
        """Valid block_id should work."""
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )

        # Create a criteria first
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="0",
            value="Rock",
        )

        response = host_client.get(
            "/api/v2/smart-block-criteria",
            {"block": block.id},
        )
        assert (
            response.status_code == 200
        ), f"Valid block_id should return 200, got {response.status_code}"

    def test_playlist_content_valid_playlist_id(
        self, host_client, host_user, faker,
    ):
        """Valid playlist_id should work."""
        playlist = baker.make(
            Playlist,
            name=f"Test Playlist {faker.uuid4()[:8]}",
            owner=host_user,
        )

        response = host_client.get(
            "/api/v2/playlist-contents",
            {"playlist": playlist.id},
        )
        assert (
            response.status_code == 200
        ), f"Valid playlist_id should return 200, got {response.status_code}"
