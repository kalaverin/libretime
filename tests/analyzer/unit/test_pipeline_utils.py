"""
Unit tests for analyzer.pipeline._utils module.

Tests the run_ utility function with mocked subprocess calls.
"""

from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import MagicMock, patch

import pytest

from analyzer.pipeline._utils import run_


class TestRun:
    """Tests for the run_ function."""

    def test_run_success(self):
        """Test successful subprocess execution."""
        mock_result = MagicMock(spec=CompletedProcess)
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch("analyzer.pipeline._utils.run", return_value=mock_result) as mock_run:
            result = run_("echo", "hello")

            mock_run.assert_called_once_with(
                ("echo", "hello"),
                check=True,
                capture_output=True,
                text=True,
            )
            assert result == mock_result

    def test_run_with_kwargs(self):
        """Test subprocess execution with additional kwargs."""
        mock_result = MagicMock(spec=CompletedProcess)
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch("analyzer.pipeline._utils.run", return_value=mock_result) as mock_run:
            result = run_("echo", "hello", cwd="/tmp", env={"KEY": "value"})

            mock_run.assert_called_once_with(
                ("echo", "hello"),
                check=True,
                capture_output=True,
                text=True,
                cwd="/tmp",
                env={"KEY": "value"},
            )
            assert result == mock_result

    def test_run_os_error_executable_not_found(self):
        """Test OSError handling when executable is not found."""
        with patch("analyzer.pipeline._utils.run") as mock_run:
            mock_run.side_effect = OSError(2, "No such file or directory")

            with pytest.raises(OSError):
                run_("nonexistent_binary", "arg")

    def test_run_called_process_error(self):
        """Test CalledProcessError handling when command returns error code."""
        with patch("analyzer.pipeline._utils.run") as mock_run:
            mock_run.side_effect = CalledProcessError(
                returncode=1,
                cmd=["ffmpeg", "-i", "input.mp3"],
                output="",
                stderr="Error: invalid file",
            )

            with pytest.raises(CalledProcessError):
                run_("ffmpeg", "-i", "input.mp3")

    def test_run_os_error_permission_denied(self):
        """Test OSError handling when permission is denied."""
        with patch("analyzer.pipeline._utils.run") as mock_run:
            mock_run.side_effect = OSError(13, "Permission denied")

            with pytest.raises(OSError):
                run_("/root/restricted_binary")

    def test_run_empty_args(self):
        """Test run_ with minimal arguments."""
        mock_result = MagicMock(spec=CompletedProcess)
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("analyzer.pipeline._utils.run", return_value=mock_result):
            result = run_("ls")
            assert result == mock_result

    def test_run_multiple_args(self):
        """Test run_ with multiple arguments."""
        mock_result = MagicMock(spec=CompletedProcess)
        mock_result.stdout = "output"
        mock_result.stderr = "error"

        with patch("analyzer.pipeline._utils.run", return_value=mock_result) as mock_run:
            result = run_(
                "ffmpeg",
                "-i", "input.mp3",
                "-vn",
                "-filter", "replaygain",
                "-f", "null",
                "/dev/null",
            )

            expected_args = (
                "ffmpeg",
                "-i", "input.mp3",
                "-vn",
                "-filter", "replaygain",
                "-f", "null",
                "/dev/null",
            )
            mock_run.assert_called_once_with(
                expected_args,
                check=True,
                capture_output=True,
                text=True,
            )
            assert result == mock_result
