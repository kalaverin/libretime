"""
Unit tests for analyzer.pipeline.organise_file module.

Tests file organization with mocked filesystem operations.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from analyzer.pipeline.organise_file import organise_file, MAX_DIR_LEN, MAX_FILE_LEN


class TestOrganiseFile:
    """Tests for organise_file function."""

    def test_organise_file_basic(self, tmp_path):
        """Test basic file organization."""
        src_file = tmp_path / "source" / "song.mp3"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        storage = tmp_path / "storage"

        result = organise_file(
            str(src_file),
            str(storage),
            "song.mp3",
            {},
        )

        assert result["full_path"] == str(storage / "song.mp3")
        assert (storage / "song.mp3").exists()
        assert not src_file.exists()  # File should be moved

    def test_organise_file_with_artist(self, tmp_path):
        """Test organization with artist name."""
        src_file = tmp_path / "source" / "song.mp3"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        storage = tmp_path / "storage"

        result = organise_file(
            str(src_file),
            str(storage),
            "song.mp3",
            {"artist_name": "Test Artist"},
        )

        expected_path = storage / "Test Artist" / "song.mp3"
        assert result["full_path"] == str(expected_path)
        assert expected_path.exists()

    def test_organise_file_with_artist_and_album(self, tmp_path):
        """Test organization with both artist and album."""
        src_file = tmp_path / "source" / "song.mp3"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        storage = tmp_path / "storage"

        result = organise_file(
            str(src_file),
            str(storage),
            "song.mp3",
            {"artist_name": "Test Artist", "album_title": "Test Album"},
        )

        expected_path = storage / "Test Artist" / "Test Album" / "song.mp3"
        assert result["full_path"] == str(expected_path)
        assert expected_path.exists()

    def test_organise_file_preserves_original_filename(self, tmp_path):
        """Test that original filename is preserved."""
        src_file = tmp_path / "source" / "tmp_12345"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        storage = tmp_path / "storage"

        result = organise_file(
            str(src_file),
            str(storage),
            "My Song Title.mp3",  # Original filename
            {},
        )

        assert result["full_path"] == str(storage / "My Song Title.mp3")
        assert (storage / "My Song Title.mp3").exists()

    def test_organise_file_samefile(self, tmp_path):
        """Test when source and destination are the same file."""
        storage = tmp_path / "storage"
        storage.mkdir(parents=True)
        dest_file = storage / "song.mp3"
        dest_file.write_text("audio data")

        result = organise_file(
            str(dest_file),
            str(storage),
            "song.mp3",
            {},
        )

        assert result["full_path"] == str(dest_file)
        assert dest_file.exists()

    def test_organise_file_duplicate_adds_uuid(self, tmp_path):
        """Test that duplicate files get UUID appended."""
        storage = tmp_path / "storage"
        storage.mkdir(parents=True)

        # Create existing file
        existing = storage / "song.mp3"
        existing.write_text("existing data")

        # Create source file
        src_file = tmp_path / "source" / "song.mp3"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("new audio data")

        result = organise_file(
            str(src_file),
            str(storage),
            "song.mp3",
            {},
        )

        # Path should have UUID appended
        result_path = result["full_path"]
        assert result_path != str(existing)
        assert result_path.startswith(str(storage / "song_"))
        assert result_path.endswith(".mp3")

        # Verify it's a valid UUID format
        uuid_part = result_path.split("_")[-1].split(".")[0]
        assert len(uuid_part) == 36  # Standard UUID length

    def test_organise_file_duplicate_multiple(self, tmp_path):
        """Test handling multiple duplicate files."""
        storage = tmp_path / "storage"
        storage.mkdir(parents=True)

        # Create multiple source files with same name
        for i in range(3):
            src_file = tmp_path / f"source{i}" / "song.mp3"
            src_file.parent.mkdir(parents=True)
            src_file.write_text(f"audio data {i}")

            result = organise_file(
                str(src_file),
                str(storage),
                "song.mp3",
                {},
            )

            # All results should be unique
            result_path = result["full_path"]
            if i == 0:
                # First one keeps original name (no collision yet)
                assert result_path == str(storage / "song.mp3")
            else:
                # Subsequent ones get UUID
                assert result_path.startswith(str(storage / "song_"))
                assert result_path.endswith(".mp3")

    def test_organise_file_long_artist_truncated(self, tmp_path):
        """Test that long artist names are truncated."""
        src_file = tmp_path / "source" / "song.mp3"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        storage = tmp_path / "storage"
        long_artist = "A" * 100  # Very long artist name

        result = organise_file(
            str(src_file),
            str(storage),
            "song.mp3",
            {"artist_name": long_artist},
        )

        # Artist directory should be truncated
        artist_dir = result["full_path"].split("/")[-2]
        assert len(artist_dir) == MAX_DIR_LEN
        assert artist_dir == "A" * MAX_DIR_LEN

    def test_organise_file_long_album_truncated(self, tmp_path):
        """Test that long album names are truncated."""
        src_file = tmp_path / "source" / "song.mp3"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        storage = tmp_path / "storage"
        long_album = "B" * 100  # Very long album name

        result = organise_file(
            str(src_file),
            str(storage),
            "song.mp3",
            {"artist_name": "Artist", "album_title": long_album},
        )

        # Album directory should be truncated
        album_dir = result["full_path"].split("/")[-2]
        assert len(album_dir) == MAX_DIR_LEN
        assert album_dir == "B" * MAX_DIR_LEN

    def test_organise_file_long_filename_truncated(self, tmp_path):
        """Test that long filenames are truncated."""
        src_file = tmp_path / "source" / "tmp"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        storage = tmp_path / "storage"
        long_filename = "C" * 100 + ".mp3"

        result = organise_file(
            str(src_file),
            str(storage),
            long_filename,
            {},
        )

        # Filename stem should be truncated
        filename = result["full_path"].split("/")[-1]
        stem = filename.replace(".mp3", "")
        assert len(stem) == MAX_FILE_LEN
        assert stem == "C" * MAX_FILE_LEN

    def test_organise_file_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created."""
        src_file = tmp_path / "source" / "song.mp3"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        storage = tmp_path / "deep" / "nested" / "storage"
        # Don't create the directory - it should be created automatically

        result = organise_file(
            str(src_file),
            str(storage),
            "song.mp3",
            {"artist_name": "Artist", "album_title": "Album"},
        )

        assert (storage / "Artist" / "Album" / "song.mp3").exists()

    def test_organise_file_different_suffix(self, tmp_path):
        """Test handling files with different extensions."""
        src_file = tmp_path / "source" / "song.flac"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        storage = tmp_path / "storage"

        result = organise_file(
            str(src_file),
            str(storage),
            "song.flac",
            {},
        )

        assert result["full_path"].endswith(".flac")
        assert (storage / "song.flac").exists()

    def test_organise_file_no_extension(self, tmp_path):
        """Test handling files without extension."""
        src_file = tmp_path / "source" / "song"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        storage = tmp_path / "storage"

        result = organise_file(
            str(src_file),
            str(storage),
            "song",
            {},
        )

        assert result["full_path"].endswith("song")
        assert (storage / "song").exists()

    def test_organise_file_preserves_existing_metadata(self, tmp_path):
        """Test that existing metadata is preserved."""
        src_file = tmp_path / "source" / "song.mp3"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        storage = tmp_path / "storage"
        existing = {"custom_field": "value", "track_title": "My Song"}

        result = organise_file(
            str(src_file),
            str(storage),
            "song.mp3",
            existing,
        )

        assert result["custom_field"] == "value"
        assert result["track_title"] == "My Song"
        assert "full_path" in result

    def test_organise_file_permission_error(self, tmp_path):
        """Test handling of permission errors during move."""
        src_file = tmp_path / "source" / "song.mp3"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        with patch("analyzer.pipeline.organise_file.shutil.move") as mock_move:
            mock_move.side_effect = PermissionError("Permission denied")

            with pytest.raises(PermissionError):
                organise_file(
                    str(src_file),
                    str(tmp_path / "storage"),
                    "song.mp3",
                    {},
                )

    def test_organise_file_os_error_on_mkdir(self, tmp_path):
        """Test handling of OS errors during directory creation."""
        src_file = tmp_path / "source" / "song.mp3"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        with patch.object(Path, "mkdir") as mock_mkdir:
            mock_mkdir.side_effect = OSError("Cannot create directory")

            with pytest.raises(OSError):
                organise_file(
                    str(src_file),
                    str(tmp_path / "storage"),
                    "song.mp3",
                    {},
                )

    def test_organise_file_logs_debug_on_move(self, tmp_path):
        """Test that debug message is logged when moving file."""
        src_file = tmp_path / "source" / "song.mp3"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("audio data")

        storage = tmp_path / "storage"

        with patch("analyzer.pipeline.organise_file.logger") as mock_logger:
            organise_file(
                str(src_file),
                str(storage),
                "song.mp3",
                {},
            )

            mock_logger.debug.assert_called_once()
            log_message = str(mock_logger.debug.call_args)
            assert "moving" in log_message
            assert "song.mp3" in log_message

    def test_organise_file_logs_warning_on_duplicate(self, tmp_path):
        """Test that warning is logged when using UUID for duplicate."""
        storage = tmp_path / "storage"
        storage.mkdir(parents=True)
        existing = storage / "song.mp3"
        existing.write_text("existing")

        src_file = tmp_path / "source" / "song.mp3"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("new data")

        with patch("analyzer.pipeline.organise_file.logger") as mock_logger:
            organise_file(
                str(src_file),
                str(storage),
                "song.mp3",
                {},
            )

            mock_logger.warning.assert_called_once()
            log_message = str(mock_logger.warning.call_args)
            assert "found existing file" in log_message
