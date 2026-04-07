"""
Unit tests for analyzer.pipeline._ffmpeg module.

Tests all ffmpeg/ffprobe related functions with mocked subprocess calls.
"""

from math import inf
from subprocess import CalledProcessError
from unittest.mock import MagicMock, patch

import pytest

from analyzer.pipeline._ffmpeg import (
    _SILENCE_DETECT_RE,
    compute_replaygain,
    compute_silences,
    probe_duration,
    probe_replaygain,
)


class TestProbeReplaygain:
    """Tests for probe_replaygain function."""

    def test_probe_replaygain_found(self, tmp_path):
        """Test probing replaygain when metadata exists."""
        mock_result = MagicMock()
        mock_result.stderr = "REPLAYGAIN_TRACK_GAIN: -5.60 dB\n"

        with patch("analyzer.pipeline._ffmpeg._ffprobe", return_value=mock_result):
            result = probe_replaygain(tmp_path / "test.mp3")
            assert result == pytest.approx(-5.60, abs=0.01)

    def test_probe_replaygain_positive_value(self, tmp_path):
        """Test probing positive replaygain value."""
        mock_result = MagicMock()
        mock_result.stderr = "REPLAYGAIN_TRACK_GAIN: +3.50 dB\n"

        with patch("analyzer.pipeline._ffmpeg._ffprobe", return_value=mock_result):
            result = probe_replaygain(tmp_path / "test.mp3")
            assert result == pytest.approx(3.50, abs=0.01)

    def test_probe_replaygain_not_found(self, tmp_path):
        """Test probing replaygain when metadata does not exist."""
        mock_result = MagicMock()
        mock_result.stderr = "Some other output without replaygain"

        with patch("analyzer.pipeline._ffmpeg._ffprobe", return_value=mock_result):
            result = probe_replaygain(tmp_path / "test.mp3")
            assert result is None

    def test_probe_replaygain_empty_stderr(self, tmp_path):
        """Test probing replaygain with empty stderr."""
        mock_result = MagicMock()
        mock_result.stderr = ""

        with patch("analyzer.pipeline._ffmpeg._ffprobe", return_value=mock_result):
            result = probe_replaygain(tmp_path / "test.mp3")
            assert result is None

    def test_probe_replaygain_called_process_error(self, tmp_path):
        """Test probing replaygain when ffprobe fails."""
        with patch("analyzer.pipeline._ffmpeg._ffprobe") as mock_ffprobe:
            mock_ffprobe.side_effect = CalledProcessError(1, "ffprobe")

            with pytest.raises(CalledProcessError):
                probe_replaygain(tmp_path / "test.mp3")

    def test_probe_replaygain_os_error(self, tmp_path):
        """Test probing replaygain when ffprobe is not found."""
        with patch("analyzer.pipeline._ffmpeg._ffprobe") as mock_ffprobe:
            mock_ffprobe.side_effect = OSError("ffprobe not found")

            with pytest.raises(OSError):
                probe_replaygain(tmp_path / "test.mp3")


class TestComputeReplaygain:
    """Tests for compute_replaygain function."""

    def test_compute_replaygain_success(self, tmp_path):
        """Test computing replaygain successfully."""
        mock_result = MagicMock()
        mock_result.stderr = " track_gain = -5.60 dB\n"

        with patch("analyzer.pipeline._ffmpeg._ffmpeg", return_value=mock_result):
            result = compute_replaygain(tmp_path / "test.mp3")
            assert result == pytest.approx(-5.60, abs=0.01)

    def test_compute_replaygain_positive_value(self, tmp_path):
        """Test computing positive replaygain value."""
        mock_result = MagicMock()
        mock_result.stderr = " track_gain = +7.20 dB\n"

        with patch("analyzer.pipeline._ffmpeg._ffmpeg", return_value=mock_result):
            result = compute_replaygain(tmp_path / "test.mp3")
            assert result == pytest.approx(7.20, abs=0.01)

    def test_compute_replaygain_not_found(self, tmp_path):
        """Test computing replaygain when result not found."""
        mock_result = MagicMock()
        mock_result.stderr = "Some other output"

        with patch("analyzer.pipeline._ffmpeg._ffmpeg", return_value=mock_result):
            result = compute_replaygain(tmp_path / "test.mp3")
            assert result is None

    def test_compute_replaygain_called_process_error(self, tmp_path):
        """Test computing replaygain when ffmpeg fails."""
        with patch("analyzer.pipeline._ffmpeg._ffmpeg") as mock_ffmpeg:
            mock_ffmpeg.side_effect = CalledProcessError(1, "ffmpeg")

            with pytest.raises(CalledProcessError):
                compute_replaygain(tmp_path / "test.mp3")


class TestComputeSilences:
    """Tests for compute_silences function."""

    def test_compute_silences_single_silence(self, tmp_path):
        """Test detecting a single silence."""
        mock_result = MagicMock()
        mock_result.stderr = """[silencedetect @ 0x563121aee500] silence_start: 0.5
[silencedetect @ 0x563121aee500] silence_end: 1.5 | silence_duration: 1.0
"""

        with patch("analyzer.pipeline._ffmpeg._ffmpeg", return_value=mock_result):
            result = compute_silences(tmp_path / "test.mp3")
            assert result == [(0.5, 1.5)]

    def test_compute_silences_multiple_silences(self, tmp_path):
        """Test detecting multiple silences."""
        mock_result = MagicMock()
        mock_result.stderr = """[silencedetect @ 0x563121aee500] silence_start: 0.5
[silencedetect @ 0x563121aee500] silence_end: 1.5 | silence_duration: 1.0
[silencedetect @ 0x563121aee500] silence_start: 8.0
[silencedetect @ 0x563121aee500] silence_end: 9.5 | silence_duration: 1.5
"""

        with patch("analyzer.pipeline._ffmpeg._ffmpeg", return_value=mock_result):
            result = compute_silences(tmp_path / "test.mp3")
            assert result == [(0.5, 1.5), (8.0, 9.5)]

    def test_compute_silences_unclosed_silence(self, tmp_path):
        """Test detecting silence without end (file ends in silence)."""
        mock_result = MagicMock()
        mock_result.stderr = """[silencedetect @ 0x563121aee500] silence_start: 8.0
"""

        with patch("analyzer.pipeline._ffmpeg._ffmpeg", return_value=mock_result):
            result = compute_silences(tmp_path / "test.mp3")
            assert result == [(8.0, inf)]

    def test_compute_silences_negative_start_clamped(self, tmp_path):
        """Test that negative silence start values are clamped to 0."""
        mock_result = MagicMock()
        mock_result.stderr = """[silencedetect @ 0x563121aee500] silence_start: -0.00154195
[silencedetect @ 0x563121aee500] silence_end: 0.998458 | silence_duration: 1
"""

        with patch("analyzer.pipeline._ffmpeg._ffmpeg", return_value=mock_result):
            result = compute_silences(tmp_path / "test.mp3")
            assert result == [(0.0, 0.998458)]

    def test_compute_silences_no_silences(self, tmp_path):
        """Test when no silences are detected."""
        mock_result = MagicMock()
        mock_result.stderr = "No silence detected in this file"

        with patch("analyzer.pipeline._ffmpeg._ffmpeg", return_value=mock_result):
            result = compute_silences(tmp_path / "test.mp3")
            assert result == []

    def test_compute_silences_called_process_error(self, tmp_path):
        """Test when ffmpeg fails during silence detection."""
        with patch("analyzer.pipeline._ffmpeg._ffmpeg") as mock_ffmpeg:
            mock_ffmpeg.side_effect = CalledProcessError(1, "ffmpeg")

            with pytest.raises(CalledProcessError):
                compute_silences(tmp_path / "test.mp3")

    def test_compute_silences_mismatched_start_end(self, tmp_path):
        """Test handling of mismatched start/end silence markers."""
        # This is an edge case - starts but no ends, and more than one start
        mock_result = MagicMock()
        mock_result.stderr = """[silencedetect @ 0x563121aee500] silence_start: 1.0
[silencedetect @ 0x563121aee500] silence_start: 5.0
[silencedetect @ 0x563121aee500] silence_end: 6.0 | silence_duration: 1.0
"""

        with patch("analyzer.pipeline._ffmpeg._ffmpeg", return_value=mock_result):
            result = compute_silences(tmp_path / "test.mp3")
            # First start (1.0) paired with end (6.0)
            assert result == [(1.0, 6.0)]


class TestSilenceDetectRegex:
    """Tests for the silence detection regex."""

    def test_silence_start_regex(self):
        """Test matching silence_start lines."""
        line = "[silencedetect @ 0x563121aee500] silence_start: 1.234567"
        match = _SILENCE_DETECT_RE.search(line)
        assert match is not None
        assert match.group(1) == "start"
        assert float(match.group(2)) == pytest.approx(1.234567)

    def test_silence_end_regex(self):
        """Test matching silence_end lines."""
        line = "[silencedetect @ 0x563121aee500] silence_end: 5.678901 | silence_duration: 3.444334"
        match = _SILENCE_DETECT_RE.search(line)
        assert match is not None
        assert match.group(1) == "end"
        assert float(match.group(2)) == pytest.approx(5.678901)

    def test_silence_start_negative_value(self):
        """Test matching negative silence_start values."""
        line = "[silencedetect @ 0x563121aee500] silence_start: -0.00154195"
        match = _SILENCE_DETECT_RE.search(line)
        assert match is not None
        assert match.group(1) == "start"
        assert float(match.group(2)) == pytest.approx(-0.00154195)

    def test_silence_integer_values(self):
        """Test matching integer silence values."""
        line = "[silencedetect @ 0x563121aee500] silence_start: 12"
        match = _SILENCE_DETECT_RE.search(line)
        assert match is not None
        assert float(match.group(2)) == 12.0


class TestProbeDuration:
    """Tests for probe_duration function."""

    def test_probe_duration_success(self, tmp_path):
        """Test probing duration successfully."""
        mock_result = MagicMock()
        mock_result.stdout = "123.456789\n"

        with patch("analyzer.pipeline._ffmpeg._ffprobe", return_value=mock_result):
            result = probe_duration(tmp_path / "test.mp3")
            assert result == pytest.approx(123.456789)

    def test_probe_duration_integer(self, tmp_path):
        """Test probing integer duration."""
        mock_result = MagicMock()
        mock_result.stdout = "300\n"

        with patch("analyzer.pipeline._ffmpeg._ffprobe", return_value=mock_result):
            result = probe_duration(tmp_path / "test.mp3")
            assert result == 300.0

    def test_probe_duration_called_process_error(self, tmp_path):
        """Test when ffprobe fails during duration probing."""
        with patch("analyzer.pipeline._ffmpeg._ffprobe") as mock_ffprobe:
            mock_ffprobe.side_effect = CalledProcessError(1, "ffprobe")

            with pytest.raises(CalledProcessError):
                probe_duration(tmp_path / "test.mp3")

    def test_probe_duration_value_error_invalid_output(self, tmp_path):
        """Test when ffprobe returns invalid output."""
        mock_result = MagicMock()
        mock_result.stdout = "not_a_number\n"

        with patch("analyzer.pipeline._ffmpeg._ffprobe", return_value=mock_result):
            with pytest.raises(ValueError):
                probe_duration(tmp_path / "test.mp3")


class TestFfmpegHelpers:
    """Tests for ffmpeg helper functions."""

    def test_ffmpeg_calls_run_with_correct_args(self):
        """Test that _ffmpeg calls run_ with correct arguments."""
        with patch("analyzer.pipeline._ffmpeg.run_") as mock_run:
            mock_run.return_value = MagicMock()
            from analyzer.pipeline._ffmpeg import _ffmpeg

            _ffmpeg("-i", "test.mp3", "-vn")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0]
            assert call_args[0] == "ffmpeg"
            assert "-i" in call_args
            assert "test.mp3" in call_args
            assert "-f" in call_args
            assert "null" in call_args
            assert "/dev/null" in call_args
            assert "-hide_banner" in call_args
            assert "-nostats" in call_args

    def test_ffprobe_calls_run_with_correct_args(self):
        """Test that _ffprobe calls run_ with correct arguments."""
        with patch("analyzer.pipeline._ffmpeg.run_") as mock_run:
            mock_run.return_value = MagicMock()
            from analyzer.pipeline._ffmpeg import _ffprobe

            _ffprobe("-i", "test.mp3", "-show_format")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0]
            assert call_args[0] == "ffprobe"
            assert "-i" in call_args
            assert "test.mp3" in call_args
            assert "-show_format" in call_args
