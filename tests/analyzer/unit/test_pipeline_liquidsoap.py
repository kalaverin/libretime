"""
Unit tests for analyzer.pipeline._liquidsoap module.

Tests the liquidsoap subprocess wrapper with mocked calls.
"""

from subprocess import CalledProcessError
from unittest.mock import MagicMock, patch

import pytest

from analyzer.pipeline._liquidsoap import _liquidsoap


class TestLiquidsoap:
    """Tests for the _liquidsoap function."""

    def test_liquidsoap_success(self):
        """Test successful liquidsoap execution."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("analyzer.pipeline._liquidsoap.LIQUIDSOAP", "liquidsoap"):
            with patch("analyzer.pipeline._liquidsoap.run_", return_value=mock_result) as mock_run:
                result = _liquidsoap(
                    "-v",
                    "-c", "output.dummy(audio_to_stereo(single(argv(1))))",
                    "--",
                    "/path/to/file.mp3",
                )

                mock_run.assert_called_once_with(
                    "liquidsoap",
                    "-v",
                    "-c", "output.dummy(audio_to_stereo(single(argv(1))))",
                    "--",
                    "/path/to/file.mp3",
                )
                assert result == mock_result

    def test_liquidsoap_with_kwargs(self):
        """Test liquidsoap execution with additional kwargs."""
        mock_result = MagicMock()

        with patch("analyzer.pipeline._liquidsoap.LIQUIDSOAP", "liquidsoap"):
            with patch("analyzer.pipeline._liquidsoap.run_", return_value=mock_result) as mock_run:
                _liquidsoap("-v", "--", "file.mp3", cwd="/tmp")

                mock_run.assert_called_once_with(
                    "liquidsoap",
                    "-v",
                    "--",
                    "file.mp3",
                    cwd="/tmp",
                )

    def test_liquidsoap_called_process_error(self):
        """Test liquidsoap when command returns error."""
        with patch("analyzer.pipeline._liquidsoap.run_") as mock_run:
            mock_run.side_effect = CalledProcessError(
                returncode=1,
                cmd=["liquidsoap", "-v", "--", "bad_file.mp3"],
                stderr="Error: Could not decode file",
            )

            with pytest.raises(CalledProcessError):
                _liquidsoap("-v", "--", "bad_file.mp3")

    def test_liquidsoap_os_error_not_found(self):
        """Test liquidsoap when binary is not found."""
        with patch("analyzer.pipeline._liquidsoap.run_") as mock_run:
            mock_run.side_effect = OSError("liquidsoap not found")

            with pytest.raises(OSError):
                _liquidsoap("-v", "--", "file.mp3")

    def test_liquidsoap_empty_args(self):
        """Test liquidsoap with minimal arguments."""
        mock_result = MagicMock()

        with patch("analyzer.pipeline._liquidsoap.LIQUIDSOAP", "liquidsoap"):
            with patch("analyzer.pipeline._liquidsoap.run_", return_value=mock_result) as mock_run:
                _liquidsoap()

                mock_run.assert_called_once_with("liquidsoap")

    def test_liquidsoap_custom_path_from_env(self):
        """Test liquidsoap with custom path from environment variable."""
        mock_result = MagicMock()

        with patch("analyzer.pipeline._liquidsoap.LIQUIDSOAP", "/custom/path/liquidsoap"):
            with patch("analyzer.pipeline._liquidsoap.run_", return_value=mock_result) as mock_run:
                _liquidsoap("--", "file.mp3")

                mock_run.assert_called_once_with(
                    "/custom/path/liquidsoap",
                    "--",
                    "file.mp3",
                )
