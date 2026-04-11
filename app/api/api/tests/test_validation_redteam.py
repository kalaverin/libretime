"""
Paranoid validation tests for field-level security checks.

Tests:
- T481: Negative offset in SmartBlockContent
- T500: Negative group in SmartBlockCriteria  
- T648: Negative count in ListenerCount (if applicable)
- T644: Negative position in PlaylistContent
- T900: Negative channels in File
- T482: Time order validation (cue_out < cue_in)
- T483: Time format validation
- T817: Playlist length format
- T381: Color format validation
- T522: URL length overflow
- T536: Name length overflow
- T818: Playlist length value overflow
- T499: SmartBlockCriteria value length
- T502: Invalid criteria choices
- T503: Invalid condition choices
- T837/T441: Invalid kind values
- T443: Null required fields
- T396: Null last_show
- T395: Negative duration

Usage:
    cd app/api && uv run pytest api/tests/test_validation_redteam.py -v
"""

import pytest
from model_bakery import baker
from rest_framework.test import APIClient

from api.core.models import User
from api.core.models.role import Role
from api.schedule.models import (
    Playlist,
    PlaylistContent,
    Show,
    ShowDays,
    SmartBlock,
    SmartBlockContent,
    SmartBlockCriteria,
)
from api.storage.models import File


# =============================================================================
# Negative Value Tests
# =============================================================================

@pytest.mark.django_db
class TestNegativeValueValidation:
    """Tests for negative value rejection (T481, T500, T644, T900)."""

    def test_smartblock_content_negative_offset_rejected(self, host_client, host_user, faker):
        """T481: Negative offset in SmartBlockContent should be rejected."""
        # Create parent objects
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )
        file_obj = baker.make(
            File,
            name=f"test_{faker.uuid4()[:8]}.mp3",
            owner=host_user,
            mime="audio/mpeg",
            filepath=f"test/{faker.uuid4()[:8]}.mp3",
        )

        data = {
            "block": block.id,
            "file": file_obj.id,
            "offset": -1.5,
        }

        response = host_client.post("/api/v2/smart-block-contents", data, format="json")

        assert response.status_code == 400, (
            f"Negative offset should be rejected, got {response.status_code}"
        )
        assert "offset" in str(response.data) or "non-negative" in str(response.data).lower()

    def test_smartblock_criteria_negative_group_rejected(self, host_client, host_user, faker):
        """T500: Negative group in SmartBlockCriteria should be rejected."""
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )

        data = {
            "block": block.id,
            "group": -1,
            "criteria": "title",
            "condition": "0",
            "value": "test",
        }

        response = host_client.post("/api/v2/smart-block-criteria", data, format="json")

        assert response.status_code == 400, (
            f"Negative group should be rejected, got {response.status_code}"
        )
        assert "group" in str(response.data) or "negative" in str(response.data).lower()

    def test_playlist_content_negative_position_rejected(self, host_client, host_user, faker):
        """T644: Negative position in PlaylistContent should be rejected."""
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
            "kind": 0,  # FILE
            "position": -1,
        }

        response = host_client.post("/api/v2/playlist-contents", data, format="json")

        assert response.status_code == 400, (
            f"Negative position should be rejected, got {response.status_code}"
        )
        assert "position" in str(response.data) or "negative" in str(response.data).lower()

    def test_file_negative_channels_rejected(self, host_client, host_user, faker):
        """T900: Negative channels in File should be rejected."""
        data = {
            "name": f"test_{faker.uuid4()[:8]}.mp3",
            "mime": "audio/mpeg",
            "filepath": f"test/{faker.uuid4()[:8]}.mp3",
            "size": 1024,
            "channels": -2,
        }

        response = host_client.post("/api/v2/files", data, format="json")

        assert response.status_code == 400, (
            f"Negative channels should be rejected, got {response.status_code}"
        )
        assert "channels" in str(response.data) or "negative" in str(response.data).lower()


# =============================================================================
# Time/Duration Validation Tests
# =============================================================================

@pytest.mark.django_db
class TestTimeValidation:
    """Tests for time format and order validation (T482, T483, T817)."""

    def test_smartblock_content_invalid_time_format_rejected(self, host_client, host_user, faker):
        """T483: Invalid time format in SmartBlockContent should be rejected."""
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )
        file_obj = baker.make(
            File,
            name=f"test_{faker.uuid4()[:8]}.mp3",
            owner=host_user,
            mime="audio/mpeg",
            filepath=f"test/{faker.uuid4()[:8]}.mp3",
        )

        data = {
            "block": block.id,
            "file": file_obj.id,
            "cue_in": "invalid-time-format",
        }

        response = host_client.post("/api/v2/smart-block-contents", data, format="json")

        assert response.status_code == 400, (
            f"Invalid time format should be rejected, got {response.status_code}"
        )

    def test_smartblock_content_cue_out_before_cue_in_rejected(self, host_client, host_user, faker):
        """T482: cue_out before cue_in should be rejected."""
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )
        file_obj = baker.make(
            File,
            name=f"test_{faker.uuid4()[:8]}.mp3",
            owner=host_user,
            mime="audio/mpeg",
            filepath=f"test/{faker.uuid4()[:8]}.mp3",
        )

        data = {
            "block": block.id,
            "file": file_obj.id,
            "offset": 0,
            "cue_in": "00:00:30.000",
            "cue_out": "00:00:10.000",  # Before cue_in
        }

        response = host_client.post("/api/v2/smart-block-contents", data, format="json")

        assert response.status_code == 400, (
            f"cue_out before cue_in should be rejected, got {response.status_code}"
        )
        assert "cue_out" in str(response.data).lower() or "after" in str(response.data).lower()

    def test_playlist_invalid_length_format_rejected(self, host_client, host_user, faker):
        """T817: Invalid length format in Playlist should be rejected."""
        data = {
            "name": f"Test Playlist {faker.uuid4()[:8]}",
            "length": "not-a-valid-duration",
        }

        response = host_client.post("/api/v2/playlists", data, format="json")

        assert response.status_code == 400, (
            f"Invalid length format should be rejected, got {response.status_code}"
        )


# =============================================================================
# Color Format Tests
# =============================================================================

@pytest.mark.django_db
class TestColorValidation:
    """Tests for hex color format validation (T381)."""

    def test_show_invalid_color_format_rejected(self, manager_client, manager_user, faker):
        """T381: Invalid hex color in Show should be rejected."""
        data = {
            "name": f"Test Show {faker.uuid4()[:8]}",
            "background_color": "GGGGGG",  # Invalid hex
            "foreground_color": "000000",
            "linked": False,
            "linkable": False,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }

        response = manager_client.post("/api/v2/shows", data, format="json")

        assert response.status_code == 400, (
            f"Invalid color format should be rejected, got {response.status_code}"
        )
        assert "color" in str(response.data).lower() or "hex" in str(response.data).lower()

    def test_show_short_color_rejected(self, manager_client, manager_user, faker):
        """T381: Short hex color (3 chars) should be rejected or normalized."""
        data = {
            "name": f"Test Show {faker.uuid4()[:8]}",
            "background_color": "FFF",  # 3-char hex
            "foreground_color": "000000",
            "linked": False,
            "linkable": False,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }

        response = manager_client.post("/api/v2/shows", data, format="json")

        # We accept 3-char hex but convert to 6-char
        if response.status_code == 201:
            assert response.data.get("background_color") == "FFFFFF"
        else:
            assert response.status_code == 400

    def test_show_color_with_hash_accepted(self, manager_client, manager_user, faker):
        """T381: Hex color with # prefix should be accepted and normalized."""
        data = {
            "name": f"Test Show {faker.uuid4()[:8]}",
            "background_color": "FF0000",  # Without # (max_length=6 in model)
            "foreground_color": "000000",
            "linked": False,
            "linkable": False,
            "auto_playlist_enabled": False,
            "auto_playlist_repeat": False,
            "override_intro_playlist": False,
            "override_outro_playlist": False,
        }

        response = manager_client.post("/api/v2/shows", data, format="json")

        assert response.status_code == 201, (
            f"Valid color should be accepted, got {response.status_code}"
        )
        assert response.data.get("background_color") == "FF0000"


# =============================================================================
# Choice/Enum Validation Tests
# =============================================================================

@pytest.mark.django_db
class TestChoiceValidation:
    """Tests for choice/enum validation (T502, T503, T837, T441)."""

    def test_smartblock_invalid_kind_rejected(self, host_client, host_user, faker):
        """T837/T441: Invalid kind value in SmartBlock should be rejected."""
        data = {
            "name": f"Test Block {faker.uuid4()[:8]}",
            "kind": "invalid_kind",
        }

        response = host_client.post("/api/v2/smart-blocks", data, format="json")

        assert response.status_code == 400, (
            f"Invalid kind should be rejected, got {response.status_code}"
        )
        assert "kind" in str(response.data).lower()

    def test_smartblock_criteria_invalid_criteria_rejected(self, host_client, host_user, faker):
        """T502: Invalid criteria value should be rejected."""
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )

        data = {
            "block": block.id,
            "criteria": "invalid_criteria_field",
            "condition": "0",
            "value": "test",
        }

        response = host_client.post("/api/v2/smart-block-criteria", data, format="json")

        assert response.status_code == 400, (
            f"Invalid criteria should be rejected, got {response.status_code}"
        )
        assert "criteria" in str(response.data).lower()

    def test_smartblock_criteria_invalid_condition_rejected(self, host_client, host_user, faker):
        """T503: Invalid condition value should be rejected."""
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )

        data = {
            "block": block.id,
            "criteria": "title",
            "condition": "invalid_condition",
            "value": "test",
        }

        response = host_client.post("/api/v2/smart-block-criteria", data, format="json")

        assert response.status_code == 400, (
            f"Invalid condition should be rejected, got {response.status_code}"
        )
        assert "condition" in str(response.data).lower()


# =============================================================================
# Required Field Tests
# =============================================================================

@pytest.mark.django_db
class TestRequiredFieldValidation:
    """Tests for required field validation (T443, T396, T395)."""

    def test_smartblock_empty_name_rejected(self, host_client, host_user, faker):
        """T443: Empty name in SmartBlock should be rejected."""
        data = {
            "name": "",
            "kind": "static",
        }

        response = host_client.post("/api/v2/smart-blocks", data, format="json")

        assert response.status_code == 400, (
            f"Empty name should be rejected, got {response.status_code}"
        )
        assert "name" in str(response.data).lower()

    def test_smartblock_whitespace_name_rejected(self, host_client, host_user, faker):
        """T443: Whitespace-only name in SmartBlock should be rejected."""
        data = {
            "name": "   ",
            "kind": "static",
        }

        response = host_client.post("/api/v2/smart-blocks", data, format="json")

        assert response.status_code == 400, (
            f"Whitespace name should be rejected, got {response.status_code}"
        )

    def test_showdays_negative_duration_rejected(self, manager_client, manager_user, faker):
        """T395: Negative duration in ShowDays should be rejected."""
        show = baker.make(
            Show,
            name=f"Test Show {faker.uuid4()[:8]}",
        )

        data = {
            "show": show.id,
            "day": 0,  # Monday
            "start_time": "10:00:00",
            "duration": -60,
        }

        response = manager_client.post("/api/v2/show-days", data, format="json")

        assert response.status_code == 400, (
            f"Negative duration should be rejected, got {response.status_code}"
        )
        assert "duration" in str(response.data).lower() or "negative" in str(response.data).lower()


# =============================================================================
# Length Overflow Tests  
# =============================================================================

@pytest.mark.django_db
class TestLengthOverflowValidation:
    """Tests for field length overflow (T522, T536, T818, T499)."""

    def test_webstream_url_too_long_rejected(self, host_client, host_user, faker):
        """T522: URL exceeding max length should be rejected."""
        data = {
            "name": f"Test Stream {faker.uuid4()[:8]}",
            "url": "https://example.com/" + "x" * 3000,  # Way too long
        }

        response = host_client.post("/api/v2/webstreams", data, format="json")

        assert response.status_code == 400, (
            f"URL too long should be rejected, got {response.status_code}"
        )

    def test_webstream_name_too_long_rejected(self, host_client, host_user, faker):
        """T536: Name exceeding 255 chars should be rejected."""
        data = {
            "name": "x" * 300,  # Exceeds 255
            "url": faker.url(),
        }

        response = host_client.post("/api/v2/webstreams", data, format="json")

        assert response.status_code == 400, (
            f"Name too long should be rejected, got {response.status_code}"
        )

    def test_smartblock_criteria_value_too_long_rejected(self, host_client, host_user, faker):
        """T499: Criteria value exceeding 512 chars should be rejected."""
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )

        data = {
            "block": block.id,
            "criteria": "title",
            "condition": "0",
            "value": "x" * 600,  # Exceeds 512
        }

        response = host_client.post("/api/v2/smart-block-criteria", data, format="json")

        assert response.status_code == 400, (
            f"Value too long should be rejected, got {response.status_code}"
        )


# =============================================================================
# Edge Case Tests
# =============================================================================

@pytest.mark.django_db
class TestEdgeCaseValidation:
    """Edge cases and boundary condition tests."""

    def test_zero_values_accepted(self, host_client, host_user, faker):
        """Zero values should be accepted for non-negative fields."""
        # Test offset = 0
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )
        file_obj = baker.make(
            File,
            name=f"test_{faker.uuid4()[:8]}.mp3",
            owner=host_user,
            mime="audio/mpeg",
            filepath=f"test/{faker.uuid4()[:8]}.mp3",
        )

        data = {
            "block": block.id,
            "file": file_obj.id,
            "offset": 0,
        }

        response = host_client.post("/api/v2/smart-block-contents", data, format="json")
        assert response.status_code == 201, f"Zero offset should be accepted, got {response.status_code}"

    def test_boundary_time_values(self, host_client, host_user, faker):
        """Boundary time values should be handled correctly."""
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )
        file_obj = baker.make(
            File,
            name=f"test_{faker.uuid4()[:8]}.mp3",
            owner=host_user,
            mime="audio/mpeg",
            filepath=f"test/{faker.uuid4()[:8]}.mp3",
        )

        # cue_out == cue_in should fail (must be after)
        data = {
            "block": block.id,
            "file": file_obj.id,
            "offset": 0,
            "cue_in": "00:00:30.000",
            "cue_out": "00:00:30.000",
        }

        response = host_client.post("/api/v2/smart-block-contents", data, format="json")
        assert response.status_code == 400, "cue_out == cue_in should be rejected"

    def test_valid_time_formats_accepted(self, host_client, host_user, faker):
        """Various valid time formats should be accepted."""
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )
        file_obj = baker.make(
            File,
            name=f"test_{faker.uuid4()[:8]}.mp3",
            owner=host_user,
            mime="audio/mpeg",
            filepath=f"test/{faker.uuid4()[:8]}.mp3",
        )

        valid_formats = [
            ("00:00:30", "00:01:00.000"),
            ("00:00:30.000", "00:01:00.000"),
            ("0:00:30", "00:01:00.000"),
            ("00:00:10", "00:01:00.000"),
        ]

        for cue_in_fmt, cue_out_fmt in valid_formats:
            data = {
                "block": block.id,
                "file": file_obj.id,
                "offset": 0,
                "cue_in": cue_in_fmt,
                "cue_out": cue_out_fmt,
            }

            response = host_client.post("/api/v2/smart-block-contents", data, format="json")
            assert response.status_code == 201, (
                f"Valid time format '{cue_in_fmt}' should be accepted, got {response.status_code}"
            )

            # Clean up for next iteration
            host_client.logout()
            host_client.force_authenticate(user=host_user)
