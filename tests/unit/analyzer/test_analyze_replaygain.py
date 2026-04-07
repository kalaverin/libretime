"""
Unit tests for analyzer.pipeline.analyze_replaygain module.

Tests replaygain analysis with mocked ffmpeg calls.
"""

from subprocess import CalledProcessError
from unittest.mock import MagicMock, patch

import pytest

from analyzer.pipeline.analyze_replaygain import analyze_replaygain


class TestAnalyzeReplaygain:
    """Tests for analyze_replaygain function."""

    def test_analyze_replaygain_probe_success(self, tmp_path):
        """Test replaygain extraction when probe finds existing metadata."""
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain", return_value=-5.5):
            result = analyze_replaygain(str(tmp_path / "test.mp3"), {})
            assert result["replay_gain"] == -5.5

    def test_analyze_replaygain_probe_returns_none_compute_success(self, tmp_path):
        """Test fallback to compute when probe returns None."""
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain", return_value=None):
            with patch("analyzer.pipeline.analyze_replaygain.compute_replaygain", return_value=-3.2):
                result = analyze_replaygain(str(tmp_path / "test.mp3"), {})
                assert result["replay_gain"] == -3.2

    def test_analyze_replaygain_probe_fails_compute_success(self, tmp_path):
        """Test fallback to compute when probe fails."""
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain") as mock_probe:
            mock_probe.side_effect = CalledProcessError(1, "ffprobe")
            with patch("analyzer.pipeline.analyze_replaygain.compute_replaygain", return_value=-4.0):
                result = analyze_replaygain(str(tmp_path / "test.mp3"), {})
                assert result["replay_gain"] == -4.0

    def test_analyze_replaygain_probe_fails_compute_fails(self, tmp_path):
        """Test when both probe and compute fail."""
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain") as mock_probe:
            mock_probe.side_effect = CalledProcessError(1, "ffprobe")
            with patch("analyzer.pipeline.analyze_replaygain.compute_replaygain") as mock_compute:
                mock_compute.side_effect = CalledProcessError(1, "ffmpeg")
                result = analyze_replaygain(str(tmp_path / "test.mp3"), {})
                # Should return metadata without replay_gain
                assert "replay_gain" not in result

    def test_analyze_replaygain_probe_not_found_compute_not_found(self, tmp_path):
        """Test when both binaries are not found."""
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain") as mock_probe:
            mock_probe.side_effect = OSError("ffprobe not found")
            with patch("analyzer.pipeline.analyze_replaygain.compute_replaygain") as mock_compute:
                mock_compute.side_effect = OSError("ffmpeg not found")
                result = analyze_replaygain(str(tmp_path / "test.mp3"), {})
                assert "replay_gain" not in result

    def test_analyze_replaygain_compute_returns_none(self, tmp_path):
        """Test when probe returns None and compute also returns None."""
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain", return_value=None):
            with patch("analyzer.pipeline.analyze_replaygain.compute_replaygain", return_value=None):
                result = analyze_replaygain(str(tmp_path / "test.mp3"), {})
                assert "replay_gain" not in result

    def test_analyze_replaygain_positive_value(self, tmp_path):
        """Test replaygain with positive value."""
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain", return_value=7.5):
            result = analyze_replaygain(str(tmp_path / "test.mp3"), {})
            assert result["replay_gain"] == 7.5

    def test_analyze_replaygain_zero_value(self, tmp_path):
        """Test replaygain with zero value."""
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain", return_value=0.0):
            result = analyze_replaygain(str(tmp_path / "test.mp3"), {})
            assert result["replay_gain"] == 0.0

    def test_analyze_replaygain_preserves_existing_metadata(self, tmp_path):
        """Test that existing metadata is preserved."""
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain", return_value=-2.0):
            existing = {"custom_field": "value", "existing_replaygain": 1.0}
            result = analyze_replaygain(str(tmp_path / "test.mp3"), existing)
            assert result["custom_field"] == "value"
            assert result["existing_replaygain"] == 1.0
            assert result["replay_gain"] == -2.0  # New value added

    def test_analyze_replaygain_overwrites_existing_replaygain(self, tmp_path):
        """Test that existing replay_gain is overwritten."""
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain", return_value=-6.0):
            existing = {"replay_gain": -1.0}
            result = analyze_replaygain(str(tmp_path / "test.mp3"), existing)
            assert result["replay_gain"] == -6.0  # New value

    def test_analyze_replaygain_probe_raises_oserror_compute_succeeds(self, tmp_path):
        """Test OSError handling in probe with successful compute fallback."""
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain") as mock_probe:
            mock_probe.side_effect = OSError("Permission denied")
            with patch("analyzer.pipeline.analyze_replaygain.compute_replaygain", return_value=-8.0):
                result = analyze_replaygain(str(tmp_path / "test.mp3"), {})
                assert result["replay_gain"] == -8.0

    def test_analyze_replaygain_calledprocesserror_in_both(self, tmp_path):
        """Test CalledProcessError in both probe and compute."""
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain") as mock_probe:
            mock_probe.side_effect = CalledProcessError(1, "ffprobe", stderr="error")
            with patch("analyzer.pipeline.analyze_replaygain.compute_replaygain") as mock_compute:
                mock_compute.side_effect = CalledProcessError(1, "ffmpeg", stderr="error")
                result = analyze_replaygain(str(tmp_path / "test.mp3"), {})
                assert "replay_gain" not in result

    def test_analyze_replaygain_mixed_errors(self, tmp_path):
        """Test various combinations of errors."""
        # Test: probe raises OSError, compute returns None
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain") as mock_probe:
            mock_probe.side_effect = OSError("not found")
            with patch("analyzer.pipeline.analyze_replaygain.compute_replaygain", return_value=None):
                result = analyze_replaygain(str(tmp_path / "test.mp3"), {})
                assert "replay_gain" not in result

    def test_analyze_replaygain_empty_metadata(self, tmp_path):
        """Test with empty initial metadata dict."""
        with patch("analyzer.pipeline.analyze_replaygain.probe_replaygain", return_value=-4.5):
            result = analyze_replaygain(str(tmp_path / "test.mp3"), {})
            assert result == {"replay_gain": -4.5}
