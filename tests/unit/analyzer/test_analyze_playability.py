"""
Unit tests for analyzer.pipeline.analyze_playability module.

Tests playability checking with mocked liquidsoap calls.
"""

from subprocess import CalledProcessError
from unittest.mock import MagicMock, patch

import pytest

from analyzer.pipeline.analyze_playability import (
    UnplayableFileError,
    analyze_playability,
)


class TestAnalyzePlayability:
    """Tests for analyze_playability function."""

    def test_analyze_playability_success(self):
        """Test successful playability check."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("analyzer.pipeline.analyze_playability._liquidsoap", return_value=mock_result):
            result = analyze_playability("/path/to/valid.mp3", {})
            # Should return metadata unchanged
            assert result == {}

    def test_analyze_playability_preserves_metadata(self):
        """Test that existing metadata is preserved."""
        mock_result = MagicMock()

        with patch("analyzer.pipeline.analyze_playability._liquidsoap", return_value=mock_result):
            existing = {"track_title": "Test", "artist_name": "Artist"}
            result = analyze_playability("/path/to/valid.mp3", existing)
            assert result["track_title"] == "Test"
            assert result["artist_name"] == "Artist"

    def test_analyze_playability_called_process_error(self):
        """Test when liquidsoap returns error (unplayable file)."""
        with patch("analyzer.pipeline.analyze_playability._liquidsoap") as mock_liquidsoap:
            mock_liquidsoap.side_effect = CalledProcessError(
                returncode=1,
                cmd=["liquidsoap", "-v", "--", "bad_file.mp3"],
                stderr="Error: Could not decode file",
            )

            with pytest.raises(UnplayableFileError):
                analyze_playability("/path/to/bad_file.mp3", {})

    def test_analyze_playability_os_error_binary_not_found(self):
        """Test when liquidsoap binary is not found."""
        with patch("analyzer.pipeline.analyze_playability._liquidsoap") as mock_liquidsoap:
            mock_liquidsoap.side_effect = OSError("liquidsoap not found")

            with patch("analyzer.pipeline.analyze_playability.logger") as mock_logger:
                result = analyze_playability("/path/to/file.mp3", {})
                # Should log warning and return metadata unchanged
                mock_logger.warning.assert_called()
                assert "Failed to run" in str(mock_logger.warning.call_args)
                assert result == {}

    def test_analyze_playability_liquidsoap_correct_args(self):
        """Test that liquidsoap is called with correct arguments."""
        mock_result = MagicMock()

        with patch("analyzer.pipeline.analyze_playability._liquidsoap", return_value=mock_result) as mock_liquidsoap:
            analyze_playability("/path/to/test.mp3", {})

            mock_liquidsoap.assert_called_once_with(
                "-v",
                "-c", "output.dummy(audio_to_stereo(single(argv(1))))",
                "--",
                "/path/to/test.mp3",
            )

    def test_analyze_playability_empty_metadata(self):
        """Test with empty metadata dict."""
        mock_result = MagicMock()

        with patch("analyzer.pipeline.analyze_playability._liquidsoap", return_value=mock_result):
            result = analyze_playability("/path/to/file.mp3", {})
            assert result == {}

    def test_analyze_playability_exception_chaining(self):
        """Test that UnplayableFileError properly chains from CalledProcessError."""
        original_error = CalledProcessError(
            returncode=1,
            cmd=["liquidsoap", "-v", "--", "file.mp3"],
            stderr="Decode error",
        )

        with patch("analyzer.pipeline.analyze_playability._liquidsoap") as mock_liquidsoap:
            mock_liquidsoap.side_effect = original_error

            with pytest.raises(UnplayableFileError) as exc_info:
                analyze_playability("/path/to/file.mp3", {})

            # Check that the original exception is properly chained
            assert exc_info.value.__cause__ is original_error


class TestUnplayableFileError:
    """Tests for UnplayableFileError exception."""

    def test_unplayable_file_error_is_exception(self):
        """Test that UnplayableFileError is an Exception."""
        assert issubclass(UnplayableFileError, Exception)

    def test_unplayable_file_error_can_be_raised(self):
        """Test that UnplayableFileError can be raised and caught."""
        with pytest.raises(UnplayableFileError):
            raise UnplayableFileError("File cannot be played")

    def test_unplayable_file_error_with_message(self):
        """Test UnplayableFileError with custom message."""
        error = UnplayableFileError("Custom error message")
        assert str(error) == "Custom error message"
