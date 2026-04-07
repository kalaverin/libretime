"""
Unit tests for analyzer.pipeline.analyze_cuepoint module.

Tests cue point analysis with mocked ffmpeg calls.
"""

from math import inf
from subprocess import CalledProcessError
from unittest.mock import MagicMock, patch

import pytest

from analyzer.pipeline.analyze_cuepoint import analyze_cuepoint, analyze_duration


class TestAnalyzeDuration:
    """Tests for analyze_duration function."""

    def test_analyze_duration_success(self, tmp_path):
        """Test successful duration extraction."""
        with patch("analyzer.pipeline.analyze_cuepoint.probe_duration", return_value=123.456):
            result = analyze_duration(str(tmp_path / "test.mp3"), {})

            assert result["length_seconds"] == 123.456
            assert result["length"] == "0:02:03.456000"
            assert result["cuein"] == 0.0
            assert result["cueout"] == 123.456

    def test_analyze_duration_with_existing_similar_duration(self, tmp_path):
        """Test duration extraction when existing duration is similar."""
        with patch("analyzer.pipeline.analyze_cuepoint.probe_duration", return_value=123.45):
            with patch("analyzer.pipeline.analyze_cuepoint.logger") as mock_logger:
                result = analyze_duration(
                    str(tmp_path / "test.mp3"),
                    {"length_seconds": 123.44},  # Within tolerance
                )
                # Should not log warning for similar durations
                mock_logger.warning.assert_not_called()
                assert result["length_seconds"] == 123.45

    def test_analyze_duration_with_different_existing_duration(self, tmp_path):
        """Test duration extraction when existing duration differs significantly."""
        with patch("analyzer.pipeline.analyze_cuepoint.probe_duration", return_value=150.0):
            with patch("analyzer.pipeline.analyze_cuepoint.logger") as mock_logger:
                result = analyze_duration(
                    str(tmp_path / "test.mp3"),
                    {"length_seconds": 100.0},  # Outside tolerance
                )
                # Should log warning for different durations
                mock_logger.warning.assert_called_once()
                assert "existing duration 100.0 differs" in str(mock_logger.warning.call_args)
                assert result["length_seconds"] == 150.0

    def test_analyze_duration_called_process_error(self, tmp_path):
        """Test duration extraction when ffprobe fails."""
        with patch("analyzer.pipeline.analyze_cuepoint.probe_duration") as mock_probe:
            mock_probe.side_effect = CalledProcessError(1, "ffprobe")
            result = analyze_duration(str(tmp_path / "test.mp3"), {})
            # Should return metadata unchanged
            assert result == {}

    def test_analyze_duration_os_error(self, tmp_path):
        """Test duration extraction when ffprobe is not found."""
        with patch("analyzer.pipeline.analyze_cuepoint.probe_duration") as mock_probe:
            mock_probe.side_effect = OSError("ffprobe not found")
            result = analyze_duration(str(tmp_path / "test.mp3"), {})
            # Should return metadata unchanged
            assert result == {}

    def test_analyze_duration_preserves_existing_metadata(self, tmp_path):
        """Test that existing metadata is preserved."""
        with patch("analyzer.pipeline.analyze_cuepoint.probe_duration", return_value=60.0):
            existing = {"custom_field": "value"}
            result = analyze_duration(str(tmp_path / "test.mp3"), existing)
            assert result["custom_field"] == "value"
            assert result["length_seconds"] == 60.0


class TestAnalyzeCuepoint:
    """Tests for analyze_cuepoint function."""

    def test_analyze_cuepoint_no_silences(self, tmp_path):
        """Test cuepoint analysis when no silences detected."""
        with patch("analyzer.pipeline.analyze_cuepoint.compute_silences", return_value=[]):
            result = analyze_cuepoint(
                str(tmp_path / "test.mp3"),
                {"length_seconds": 60.0, "cuein": 0.0, "cueout": 60.0},
            )
            # cuein and cueout should remain as-is (formatted)
            assert result["cuein"] == "0.000000"
            assert result["cueout"] == "60.000000"

    def test_analyze_cuepoint_leading_silence(self, tmp_path):
        """Test cuepoint analysis with leading silence."""
        silences = [(0.0, 1.5)]  # Silence at the beginning
        with patch("analyzer.pipeline.analyze_cuepoint.compute_silences", return_value=silences):
            result = analyze_cuepoint(
                str(tmp_path / "test.mp3"),
                {"length_seconds": 60.0, "cuein": 0.0, "cueout": 60.0},
            )
            assert float(result["cuein"]) == pytest.approx(1.5, abs=0.1)
            assert float(result["cueout"]) == pytest.approx(60.0, abs=0.1)

    def test_analyze_cuepoint_trailing_silence(self, tmp_path):
        """Test cuepoint analysis with trailing silence."""
        silences = [(58.0, 60.0)]  # Silence at the end
        with patch("analyzer.pipeline.analyze_cuepoint.compute_silences", return_value=silences):
            result = analyze_cuepoint(
                str(tmp_path / "test.mp3"),
                {"length_seconds": 60.0, "cuein": 0.0, "cueout": 60.0},
            )
            assert float(result["cuein"]) == pytest.approx(0.0, abs=0.1)
            assert float(result["cueout"]) == pytest.approx(58.0, abs=0.1)

    def test_analyze_cuepoint_both_silences(self, tmp_path):
        """Test cuepoint analysis with both leading and trailing silences."""
        silences = [(0.0, 1.5), (58.0, 60.0)]
        with patch("analyzer.pipeline.analyze_cuepoint.compute_silences", return_value=silences):
            result = analyze_cuepoint(
                str(tmp_path / "test.mp3"),
                {"length_seconds": 60.0, "cuein": 0.0, "cueout": 60.0},
            )
            assert float(result["cuein"]) == pytest.approx(1.5, abs=0.1)
            assert float(result["cueout"]) == pytest.approx(58.0, abs=0.1)

    def test_analyze_cuepoint_unclosed_trailing_silence(self, tmp_path):
        """Test cuepoint analysis with unclosed trailing silence (inf)."""
        silences = [(58.0, inf)]
        with patch("analyzer.pipeline.analyze_cuepoint.compute_silences", return_value=silences):
            result = analyze_cuepoint(
                str(tmp_path / "test.mp3"),
                {"length_seconds": 60.0, "cuein": 0.0, "cueout": 60.0},
            )
            assert float(result["cuein"]) == pytest.approx(0.0, abs=0.1)
            assert float(result["cueout"]) == pytest.approx(58.0, abs=0.1)

    def test_analyze_cuepoint_multiple_silences_keep_first_last(self, tmp_path):
        """Test that only first and last silences are kept when more than 2."""
        silences = [(0.0, 1.0), (10.0, 11.0), (20.0, 21.0), (58.0, 60.0)]
        with patch("analyzer.pipeline.analyze_cuepoint.compute_silences", return_value=silences):
            result = analyze_cuepoint(
                str(tmp_path / "test.mp3"),
                {"length_seconds": 60.0, "cuein": 0.0, "cueout": 60.0},
            )
            # Should only use first (0.0, 1.0) and last (58.0, 60.0)
            assert float(result["cuein"]) == pytest.approx(1.0, abs=0.1)
            assert float(result["cueout"]) == pytest.approx(58.0, abs=0.1)

    def test_analyze_cuepoint_sanity_check_failure(self, tmp_path):
        """Test that invalid silences (start > end) raise ValueError."""
        silences = [(5.0, 3.0)]  # Invalid: start after end
        with patch("analyzer.pipeline.analyze_cuepoint.compute_silences", return_value=silences):
            with pytest.raises(ValueError, match="silence starts.*after ending"):
                analyze_cuepoint(
                    str(tmp_path / "test.mp3"),
                    {"length_seconds": 60.0, "cuein": 0.0, "cueout": 60.0},
                )

    def test_analyze_cuepoint_called_process_error(self, tmp_path):
        """Test cuepoint analysis when ffmpeg fails."""
        with patch("analyzer.pipeline.analyze_cuepoint.compute_silences") as mock_compute:
            mock_compute.side_effect = CalledProcessError(1, "ffmpeg")
            result = analyze_cuepoint(
                str(tmp_path / "test.mp3"),
                {"length_seconds": 60.0, "cuein": 0.0, "cueout": 60.0},
            )
            # Should return metadata unchanged
            assert result["cuein"] == 0.0  # Original value
            assert result["cueout"] == 60.0  # Original value

    def test_analyze_cuepoint_os_error(self, tmp_path):
        """Test cuepoint analysis when ffmpeg is not found."""
        with patch("analyzer.pipeline.analyze_cuepoint.compute_silences") as mock_compute:
            mock_compute.side_effect = OSError("ffmpeg not found")
            result = analyze_cuepoint(
                str(tmp_path / "test.mp3"),
                {"length_seconds": 60.0, "cuein": 0.0, "cueout": 60.0},
            )
            # Should return metadata unchanged
            assert result["cuein"] == 0.0
            assert result["cueout"] == 60.0

    def test_analyze_cuepoint_clamps_negative_silence_start(self, tmp_path):
        """Test that negative silence start values are clamped to 0."""
        silences = [(-0.1, 1.0)]  # Negative start should be treated as 0
        with patch("analyzer.pipeline.analyze_cuepoint.compute_silences", return_value=silences):
            result = analyze_cuepoint(
                str(tmp_path / "test.mp3"),
                {"length_seconds": 60.0, "cuein": 0.0, "cueout": 60.0},
            )
            # The negative start is clamped to 0, so it's considered leading silence
            assert float(result["cuein"]) == pytest.approx(1.0, abs=0.1)

    def test_analyze_cuepoint_preserves_existing_metadata(self, tmp_path):
        """Test that existing metadata is preserved."""
        silences = []
        with patch("analyzer.pipeline.analyze_cuepoint.compute_silences", return_value=silences):
            existing = {
                "length_seconds": 60.0,
                "cuein": 0.0,
                "cueout": 60.0,
                "custom_field": "value",
            }
            result = analyze_cuepoint(str(tmp_path / "test.mp3"), existing)
            assert result["custom_field"] == "value"
