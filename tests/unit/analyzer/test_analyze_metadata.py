"""
Unit tests for analyzer.pipeline.analyze_metadata module.

Tests metadata extraction from audio files with mocked mutagen and filesystem.
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from analyzer.pipeline.analyze_metadata import analyze_metadata, flatten, comment_get


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_flatten_empty_list(self):
        """Test flatten with empty list."""
        assert flatten([]) == []

    def test_flatten_single_list(self):
        """Test flatten with single nested list."""
        assert flatten([[1, 2, 3]]) == [1, 2, 3]

    def test_flatten_multiple_lists(self):
        """Test flatten with multiple nested lists."""
        assert flatten([[1, 2], [3, 4], [5, 6]]) == [1, 2, 3, 4, 5, 6]

    def test_flatten_mixed_empty(self):
        """Test flatten with mixed empty lists."""
        assert flatten([[], [1], [], [2, 3], []]) == [1, 2, 3]

    def test_comment_get_with_comment_key(self):
        """Test comment_get with comment key."""
        id3 = {
            "COMM::eng": MagicMock(text=["Test comment"]),
        }
        result = comment_get(id3, None)
        assert result == ["Test comment"]

    def test_comment_get_with_multiple_comments(self):
        """Test comment_get with multiple comment keys."""
        id3 = {
            "COMM::eng": MagicMock(text=["Comment 1"]),
            "COMM:ID3v1Comment:eng": MagicMock(text=["Comment 2"]),
        }
        result = comment_get(id3, None)
        assert "Comment 1" in result
        assert "Comment 2" in result

    def test_comment_get_no_comments(self):
        """Test comment_get with no comment keys."""
        id3 = {
            "TIT2": MagicMock(text=["Title"]),
        }
        result = comment_get(id3, None)
        assert result == []

    def test_comment_get_empty_text(self):
        """Test comment_get with empty text."""
        id3 = {
            "COMM::eng": MagicMock(text=[]),
        }
        result = comment_get(id3, None)
        assert result == []


class TestAnalyzeMetadata:
    """Tests for analyze_metadata function."""

    def test_analyze_metadata_basic_fields(self, tmp_path):
        """Test extraction of basic metadata fields."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake audio data")

        mock_audio = MagicMock()
        mock_audio.mime = ["audio/mp3"]
        mock_audio.info.sample_rate = 44100
        mock_audio.info.bitrate = 128000
        mock_audio.info.length = 180.5
        mock_audio.info.mode = 0  # stereo
        mock_audio.__getitem__ = lambda self, key: {
            "title": ["Test Title"],
            "artist": ["Test Artist"],
        }.get(key, [])

        with patch("analyzer.pipeline.analyze_metadata.File", return_value=mock_audio):
            with patch("analyzer.pipeline.analyze_metadata.compute_md5", return_value="a" * 32):
                result = analyze_metadata(str(test_file), {})

                assert result["ftype"] == "audioclip"
                assert result["hidden"] is False
                assert result["mime"] == "audio/mp3"
                assert result["sample_rate"] == 44100
                assert result["bit_rate"] == 128000
                assert result["length_seconds"] == 180.5
                assert result["length"] == str(timedelta(seconds=180.5))
                assert result["channels"] == 2
                assert result["track_title"] == "Test Title"
                assert result["artist_name"] == "Test Artist"
                assert result["md5"] == "a" * 32

    def test_analyze_metadata_mp3_mono(self, tmp_path):
        """Test MP3 mono channel detection."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake")

        mock_audio = MagicMock()
        mock_audio.mime = ["audio/mp3"]
        mock_audio.info.mode = 3  # mono
        mock_audio.info.sample_rate = 44100
        mock_audio.info.length = 60.0

        with patch("analyzer.pipeline.analyze_metadata.File", return_value=mock_audio):
            with patch("analyzer.pipeline.analyze_metadata.compute_md5", return_value="b" * 32):
                result = analyze_metadata(str(test_file), {})
                assert result["channels"] == 1

    def test_analyze_metadata_non_mp3_channels(self, tmp_path):
        """Test channel detection for non-MP3 files."""
        test_file = tmp_path / "test.flac"
        test_file.write_bytes(b"fake")

        mock_audio = MagicMock()
        mock_audio.mime = ["audio/flac"]
        mock_audio.info.channels = 6  # 5.1 surround
        mock_audio.info.sample_rate = 48000
        mock_audio.info.length = 120.0

        with patch("analyzer.pipeline.analyze_metadata.File", return_value=mock_audio):
            with patch("analyzer.pipeline.analyze_metadata.compute_md5", return_value="c" * 32):
                result = analyze_metadata(str(test_file), {})
                assert result["channels"] == 6

    def test_analyze_metadata_track_number_parsing(self, tmp_path):
        """Test track number parsing with various formats."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake")

        mock_audio = MagicMock()
        mock_audio.mime = ["audio/mp3"]
        mock_audio.info.length = 60.0

        # Test "5/12" format
        mock_audio.__getitem__ = lambda self, key: {"tracknumber": ["5/12"]}.get(key, [])

        with patch("analyzer.pipeline.analyze_metadata.File", return_value=mock_audio):
            with patch("analyzer.pipeline.analyze_metadata.compute_md5", return_value="d" * 32):
                result = analyze_metadata(str(test_file), {})
                assert result["track_number"] == "5"
                assert result["track_total"] == "12"

    def test_analyze_metadata_track_number_hyphen(self, tmp_path):
        """Test track number parsing with hyphen format."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake")

        mock_audio = MagicMock()
        mock_audio.mime = ["audio/mp3"]
        mock_audio.info.length = 60.0
        mock_audio.__getitem__ = lambda self, key: {"tracknumber": ["3-10"]}.get(key, [])

        with patch("analyzer.pipeline.analyze_metadata.File", return_value=mock_audio):
            with patch("analyzer.pipeline.analyze_metadata.compute_md5", return_value="e" * 32):
                result = analyze_metadata(str(test_file), {})
                assert result["track_number"] == "3"
                assert result["track_total"] == "10"

    def test_analyze_metadata_track_number_simple(self, tmp_path):
        """Test track number parsing with simple format."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake")

        mock_audio = MagicMock()
        mock_audio.mime = ["audio/mp3"]
        mock_audio.info.length = 60.0
        mock_audio.__getitem__ = lambda self, key: {"tracknumber": ["7"]}.get(key, [])

        with patch("analyzer.pipeline.analyze_metadata.File", return_value=mock_audio):
            with patch("analyzer.pipeline.analyze_metadata.compute_md5", return_value="f" * 32):
                result = analyze_metadata(str(test_file), {})
                assert result["track_number"] == "7"
                # track_total should not exist
                assert "track_total" not in result

    def test_analyze_metadata_no_tags(self, tmp_path):
        """Test file with no metadata tags."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake")

        mock_audio = MagicMock()
        mock_audio.mime = ["audio/mp3"]
        mock_audio.info.length = 60.0
        mock_audio.__getitem__ = lambda self, key: []  # No tags

        with patch("analyzer.pipeline.analyze_metadata.File", return_value=mock_audio):
            with patch("analyzer.pipeline.analyze_metadata.compute_md5", return_value="0" * 32):
                result = analyze_metadata(str(test_file), {})
                # Should have basic fields but no extracted tags
                assert result["ftype"] == "audioclip"
                assert result["mime"] == "audio/mp3"
                assert "track_title" not in result
                assert "artist_name" not in result

    def test_analyze_metadata_unparsable_file(self, tmp_path):
        """Test file that cannot be parsed by mutagen."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"not audio data")

        with patch("analyzer.pipeline.analyze_metadata.File", return_value=None):
            with patch("analyzer.pipeline.analyze_metadata.compute_md5", return_value="x" * 32):
                result = analyze_metadata(str(test_file), {})
                assert result["ftype"] == "audioclip"
                assert result["hidden"] is False
                assert result["md5"] == "x" * 32
                assert result["filesize"] == len(b"not audio data")
                # Should not have mime or other audio-specific fields
                assert "mime" not in result

    def test_analyze_metadata_preserves_existing_metadata(self, tmp_path):
        """Test that existing metadata in input dict is preserved."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake")

        mock_audio = MagicMock()
        mock_audio.mime = ["audio/mp3"]
        mock_audio.info.length = 60.0
        mock_audio.__getitem__ = lambda self, key: ["New Title"] if key == "title" else []

        with patch("analyzer.pipeline.analyze_metadata.File", return_value=mock_audio):
            with patch("analyzer.pipeline.analyze_metadata.compute_md5", return_value="g" * 32):
                existing = {"custom_field": "custom_value", "track_title": "Old Title"}
                result = analyze_metadata(str(test_file), existing)
                assert result["custom_field"] == "custom_value"
                assert result["track_title"] == "New Title"  # Overwritten

    def test_analyze_metadata_list_values(self, tmp_path):
        """Test handling of list values from mutagen."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake")

        mock_audio = MagicMock()
        mock_audio.mime = ["audio/mp3"]
        mock_audio.info.length = 60.0
        mock_audio.__getitem__ = lambda self, key: ["Artist 1", "Artist 2"] if key == "artist" else []

        with patch("analyzer.pipeline.analyze_metadata.File", return_value=mock_audio):
            with patch("analyzer.pipeline.analyze_metadata.compute_md5", return_value="h" * 32):
                result = analyze_metadata(str(test_file), {})
                assert result["artist_name"] == "Artist 1"  # First item only

    def test_analyze_metadata_empty_list_value(self, tmp_path):
        """Test handling of empty list values from mutagen."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake")

        mock_audio = MagicMock()
        mock_audio.mime = ["audio/mp3"]
        mock_audio.info.length = 60.0
        mock_audio.__getitem__ = lambda self, key: [] if key == "title" else ["Artist"]

        with patch("analyzer.pipeline.analyze_metadata.File", return_value=mock_audio):
            with patch("analyzer.pipeline.analyze_metadata.compute_md5", return_value="i" * 32):
                result = analyze_metadata(str(test_file), {})
                assert result.get("track_title") == ""  # Empty list becomes empty string

    def test_analyze_metadata_tag_mapping(self, tmp_path):
        """Test all tag mappings are correctly applied."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake")

        mock_audio = MagicMock()
        mock_audio.mime = ["audio/mp3"]
        mock_audio.info.length = 60.0

        tag_values = {
            "title": ["Title"],
            "artist": ["Artist"],
            "album": ["Album"],
            "bpm": ["120"],
            "composer": ["Composer"],
            "conductor": ["Conductor"],
            "copyright": ["2024"],
            "comment": ["Comment"],
            "encoded_by": ["Encoder"],
            "genre": ["Genre"],
            "isrc": ["ISRC123"],
            "label": ["Label"],
            "organization": ["Organization"],
            "language": ["English"],
            "last_modified": ["2024-01-01"],
            "mood": ["Happy"],
            "bit_rate": ["128000"],
            "replay_gain": ["-5.0"],
            "website": ["http://example.com"],
            "date": ["2024"],
        }
        mock_audio.__getitem__ = lambda self, key: tag_values.get(key, [])

        with patch("analyzer.pipeline.analyze_metadata.File", return_value=mock_audio):
            with patch("analyzer.pipeline.analyze_metadata.compute_md5", return_value="j" * 32):
                result = analyze_metadata(str(test_file), {})

                assert result["track_title"] == "Title"
                assert result["artist_name"] == "Artist"
                assert result["album_title"] == "Album"
                assert result["bpm"] == "120"
                assert result["composer"] == "Composer"
                assert result["conductor"] == "Conductor"
                assert result["copyright"] == "2024"
                assert result["comment"] == "Comment"
                assert result["comments"] == "Comment"
                assert result["description"] == "Comment"
                assert result["encoder"] == "Encoder"
                assert result["genre"] == "Genre"
                assert result["isrc"] == "ISRC123"
                assert result["label"] == "Label"  # label from "label"
                assert result["language"] == "English"
                assert result["last_modified"] == "2024-01-01"
                assert result["mood"] == "Happy"
                assert result["website"] == "http://example.com"
                assert result["year"] == "2024"

    def test_analyze_metadata_missing_info_attributes(self, tmp_path):
        """Test handling when audio info lacks optional attributes."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake")

        mock_audio = MagicMock()
        mock_audio.mime = ["audio/mp3"]
        # Intentionally not setting sample_rate, bitrate, length
        mock_audio.info = MagicMock()
        mock_audio.info.length = None
        # No sample_rate attribute
        delattr(mock_audio.info, "sample_rate")
        delattr(mock_audio.info, "bitrate")

        with patch("analyzer.pipeline.analyze_metadata.File", return_value=mock_audio):
            with patch("analyzer.pipeline.analyze_metadata.compute_md5", return_value="k" * 32):
                result = analyze_metadata(str(test_file), {})
                # Should not raise, but also should not have these fields
                assert "sample_rate" not in result
                assert "bit_rate" not in result
