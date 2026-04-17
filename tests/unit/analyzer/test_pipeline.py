"""
Unit tests for analyzer.pipeline.pipeline module.

Tests the main Pipeline class with all mocked dependencies.
"""

from queue import Queue
from subprocess import CalledProcessError
from unittest.mock import MagicMock, patch

import pytest

from analyzer.pipeline.pipeline import (
    Pipeline,
    PipelineOptions,
    PipelineStatus,
    Step,
)
from analyzer.pipeline.analyze_playability import UnplayableFileError


class TestPipelineStatus:
    """Tests for PipelineStatus enum."""

    def test_pipeline_status_values(self):
        """Test PipelineStatus enum values."""
        assert PipelineStatus.SUCCEED == 0
        assert PipelineStatus.PENDING == 1
        assert PipelineStatus.FAILED == 2

    def test_pipeline_status_is_int_enum(self):
        """Test that PipelineStatus is an int enum."""
        assert isinstance(PipelineStatus.SUCCEED, int)
        assert PipelineStatus.SUCCEED == 0


class TestPipelineOptions:
    """Tests for PipelineOptions model."""

    def test_default_options(self):
        """Test default pipeline options."""
        options = PipelineOptions()
        assert options.analyze_cue_points is False

    def test_custom_options(self):
        """Test custom pipeline options."""
        options = PipelineOptions(analyze_cue_points=True)
        assert options.analyze_cue_points is True

    def test_options_from_dict(self):
        """Test creating options from dict."""
        options = PipelineOptions(**{"analyze_cue_points": True})
        assert options.analyze_cue_points is True


class TestStepProtocol:
    """Tests for Step protocol."""

    def test_step_protocol_callable(self):
        """Test that Step protocol defines a callable."""
        # The protocol should accept any callable with the right signature
        def valid_step(filename: str, metadata: dict) -> dict:
            return metadata

        # This should type-check correctly (though we can't verify at runtime)
        assert callable(valid_step)


class TestPipelineRunAnalysis:
    """Tests for Pipeline.run_analysis method."""

    def test_run_analysis_success(self, tmp_path):
        """Test successful full analysis pipeline."""
        queue = Queue()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("audio data")
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        mock_metadata = {
            "track_title": "Test",
            "artist_name": "Artist",
            "length_seconds": 60.0,
        }

        with patch("analyzer.pipeline.pipeline.analyze_metadata", return_value=mock_metadata.copy()):
            with patch("analyzer.pipeline.pipeline.analyze_duration", return_value={**mock_metadata, "length_seconds": 60.0}):
                with patch("analyzer.pipeline.pipeline.analyze_replaygain", return_value={**mock_metadata, "replay_gain": -5.0}):
                    with patch("analyzer.pipeline.pipeline.analyze_playability", return_value=mock_metadata):
                        with patch("analyzer.pipeline.pipeline.organise_file", return_value={**mock_metadata, "full_path": str(dest_dir / "test.mp3")}):
                            Pipeline.run_analysis(
                                queue,
                                str(audio_file),
                                str(dest_dir),
                                "test.mp3",
                                PipelineOptions(),
                            )

        result = queue.get()
        assert result["import_status"] == PipelineStatus.SUCCEED
        assert result["track_title"] == "Test"
        assert result["full_path"] == str(dest_dir / "test.mp3")

    def test_run_analysis_with_cue_points(self, tmp_path):
        """Test analysis with cue points enabled."""
        queue = Queue()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("audio data")
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        with patch("analyzer.pipeline.pipeline.analyze_metadata") as mock_metadata:
            mock_metadata.return_value = {"length_seconds": 60.0}
            with patch("analyzer.pipeline.pipeline.analyze_duration") as mock_duration:
                mock_duration.return_value = {"length_seconds": 60.0, "cuein": 0.0, "cueout": 60.0}
                with patch("analyzer.pipeline.pipeline.analyze_cuepoint") as mock_cuepoint:
                    mock_cuepoint.return_value = {"length_seconds": 60.0, "cuein": "1.5", "cueout": "58.0"}
                    with patch("analyzer.pipeline.pipeline.analyze_replaygain") as mock_replaygain:
                        mock_replaygain.return_value = {"replay_gain": -5.0}
                        with patch("analyzer.pipeline.pipeline.analyze_playability") as mock_playability:
                            mock_playability.return_value = {}
                            with patch("analyzer.pipeline.pipeline.organise_file") as mock_organise:
                                mock_organise.return_value = {"full_path": str(dest_dir / "test.mp3")}

                                Pipeline.run_analysis(
                                    queue,
                                    str(audio_file),
                                    str(dest_dir),
                                    "test.mp3",
                                    PipelineOptions(analyze_cue_points=True),
                                )

                                # Verify analyze_cuepoint was called
                                mock_cuepoint.assert_called_once()

        result = queue.get()
        assert result["import_status"] == PipelineStatus.SUCCEED

    def test_run_analysis_without_cue_points(self, tmp_path):
        """Test analysis with cue points disabled (default)."""
        queue = Queue()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("audio data")
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        with patch("analyzer.pipeline.pipeline.analyze_metadata") as mock_metadata:
            mock_metadata.return_value = {}
            with patch("analyzer.pipeline.pipeline.analyze_duration") as mock_duration:
                mock_duration.return_value = {}
                with patch("analyzer.pipeline.pipeline.analyze_cuepoint") as mock_cuepoint:
                    mock_cuepoint.return_value = {}
                    with patch("analyzer.pipeline.pipeline.analyze_replaygain") as mock_replaygain:
                        mock_replaygain.return_value = {}
                        with patch("analyzer.pipeline.pipeline.analyze_playability") as mock_playability:
                            mock_playability.return_value = {}
                            with patch("analyzer.pipeline.pipeline.organise_file") as mock_organise:
                                mock_organise.return_value = {"full_path": str(dest_dir / "test.mp3")}

                                Pipeline.run_analysis(
                                    queue,
                                    str(audio_file),
                                    str(dest_dir),
                                    "test.mp3",
                                    PipelineOptions(analyze_cue_points=False),
                                )

                                # Verify analyze_cuepoint was NOT called
                                mock_cuepoint.assert_not_called()

        result = queue.get()
        assert result["import_status"] == PipelineStatus.SUCCEED

    def test_run_analysis_unplayable_file(self, tmp_path):
        """Test handling of unplayable file error."""
        queue = Queue()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("audio data")
        dest_dir = tmp_path / "dest"

        with patch("analyzer.pipeline.pipeline.analyze_metadata", return_value={}):
            with patch("analyzer.pipeline.pipeline.analyze_duration", return_value={}):
                with patch("analyzer.pipeline.pipeline.analyze_replaygain", return_value={}):
                    with patch("analyzer.pipeline.pipeline.analyze_playability") as mock_playability:
                        original_error = CalledProcessError(1, "liquidsoap")
                        mock_playability.side_effect = UnplayableFileError(original_error)

                        with pytest.raises(UnplayableFileError):
                            Pipeline.run_analysis(
                                queue,
                                str(audio_file),
                                str(dest_dir),
                                "test.mp3",
                                PipelineOptions(),
                            )

        # Production code raises without queue.put on UnplayableFileError
        assert queue.empty()

    def test_run_analysis_metadata_step_failure(self, tmp_path):
        """Test handling of failure in metadata analysis step."""
        queue = Queue()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("audio data")
        dest_dir = tmp_path / "dest"

        with patch("analyzer.pipeline.pipeline.analyze_metadata") as mock_metadata:
            mock_metadata.side_effect = Exception("Metadata parsing failed")

            with pytest.raises(Exception, match="Metadata parsing failed"):
                Pipeline.run_analysis(
                    queue,
                    str(audio_file),
                    str(dest_dir),
                    "test.mp3",
                    PipelineOptions(),
                )

        # Queue should be empty since exception was raised before putting
        assert queue.empty()

    def test_run_analysis_duration_step_failure(self, tmp_path):
        """Test handling of failure in duration analysis step."""
        queue = Queue()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("audio data")
        dest_dir = tmp_path / "dest"

        with patch("analyzer.pipeline.pipeline.analyze_metadata", return_value={}):
            with patch("analyzer.pipeline.pipeline.analyze_duration") as mock_duration:
                mock_duration.side_effect = Exception("Duration analysis failed")

                with pytest.raises(Exception, match="Duration analysis failed"):
                    Pipeline.run_analysis(
                        queue,
                        str(audio_file),
                        str(dest_dir),
                        "test.mp3",
                        PipelineOptions(),
                    )

    def test_run_analysis_replaygain_step_failure(self, tmp_path):
        """Test handling of failure in replaygain analysis step."""
        queue = Queue()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("audio data")
        dest_dir = tmp_path / "dest"

        with patch("analyzer.pipeline.pipeline.analyze_metadata", return_value={}):
            with patch("analyzer.pipeline.pipeline.analyze_duration", return_value={}):
                with patch("analyzer.pipeline.pipeline.analyze_replaygain") as mock_replaygain:
                    mock_replaygain.side_effect = Exception("Replaygain analysis failed")

                    with pytest.raises(Exception, match="Replaygain analysis failed"):
                        Pipeline.run_analysis(
                            queue,
                            str(audio_file),
                            str(dest_dir),
                            "test.mp3",
                            PipelineOptions(),
                        )

    def test_run_analysis_organise_failure(self, tmp_path):
        """Test handling of failure in file organization step."""
        queue = Queue()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("audio data")
        dest_dir = tmp_path / "dest"

        with patch("analyzer.pipeline.pipeline.analyze_metadata", return_value={}):
            with patch("analyzer.pipeline.pipeline.analyze_duration", return_value={}):
                with patch("analyzer.pipeline.pipeline.analyze_replaygain", return_value={}):
                    with patch("analyzer.pipeline.pipeline.analyze_playability", return_value={}):
                        with patch("analyzer.pipeline.pipeline.organise_file") as mock_organise:
                            mock_organise.side_effect = PermissionError("Cannot write to destination")

                            with pytest.raises(PermissionError, match="Cannot write to destination"):
                                Pipeline.run_analysis(
                                    queue,
                                    str(audio_file),
                                    str(dest_dir),
                                    "test.mp3",
                                    PipelineOptions(),
                                )

    def test_run_analysis_cuepoint_step_failure(self, tmp_path):
        """Test handling of failure in cuepoint analysis step."""
        queue = Queue()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("audio data")
        dest_dir = tmp_path / "dest"

        with patch("analyzer.pipeline.pipeline.analyze_metadata", return_value={}):
            with patch("analyzer.pipeline.pipeline.analyze_duration", return_value={}):
                with patch("analyzer.pipeline.pipeline.analyze_cuepoint") as mock_cuepoint:
                    mock_cuepoint.side_effect = Exception("Cuepoint analysis failed")

                    with pytest.raises(Exception, match="Cuepoint analysis failed"):
                        Pipeline.run_analysis(
                            queue,
                            str(audio_file),
                            str(dest_dir),
                            "test.mp3",
                            PipelineOptions(analyze_cue_points=True),
                        )

    def test_run_analysis_logs_exception(self, tmp_path):
        """Test that exceptions are properly logged."""
        queue = Queue()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("audio data")
        dest_dir = tmp_path / "dest"

        with patch("analyzer.pipeline.pipeline.analyze_metadata") as mock_metadata:
            mock_metadata.side_effect = ValueError("Test error")

            with patch("analyzer.pipeline.pipeline.logger") as mock_logger:
                with pytest.raises(ValueError):
                    Pipeline.run_analysis(
                        queue,
                        str(audio_file),
                        str(dest_dir),
                        "test.mp3",
                        PipelineOptions(),
                    )

                mock_logger.exception.assert_called_once()

    def test_run_analysis_metadata_propagation(self, tmp_path):
        """Test that metadata is correctly passed between pipeline steps."""
        queue = Queue()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("audio data")
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        # Track how metadata evolves through the pipeline
        metadata_evolution = [
            {"step": "initial"},
            {"step": "metadata", "track_title": "Test"},
            {"step": "duration", "length_seconds": 60.0},
            {"step": "replaygain", "replay_gain": -5.0},
            {"step": "playability"},
            {"step": "organise", "full_path": str(dest_dir / "test.mp3")},
        ]

        with patch("analyzer.pipeline.pipeline.analyze_metadata", return_value=metadata_evolution[1]):
            with patch("analyzer.pipeline.pipeline.analyze_duration", return_value=metadata_evolution[2]):
                with patch("analyzer.pipeline.pipeline.analyze_replaygain", return_value=metadata_evolution[3]):
                    with patch("analyzer.pipeline.pipeline.analyze_playability", return_value=metadata_evolution[4]):
                        with patch("analyzer.pipeline.pipeline.organise_file", return_value=metadata_evolution[5]):
                            Pipeline.run_analysis(
                                queue,
                                str(audio_file),
                                str(dest_dir),
                                "test.mp3",
                                PipelineOptions(),
                            )

        result = queue.get()
        assert result["import_status"] == PipelineStatus.SUCCEED
        # Final metadata should have all accumulated fields
        assert "full_path" in result

    def test_run_analysis_logs_unplayable_exception(self, tmp_path):
        """Test that UnplayableFileError is properly logged."""
        queue = Queue()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("audio data")
        dest_dir = tmp_path / "dest"

        with patch("analyzer.pipeline.pipeline.analyze_metadata", return_value={}):
            with patch("analyzer.pipeline.pipeline.analyze_duration", return_value={}):
                with patch("analyzer.pipeline.pipeline.analyze_replaygain", return_value={}):
                    with patch("analyzer.pipeline.pipeline.analyze_playability") as mock_playability:
                        error = UnplayableFileError("Cannot play")
                        mock_playability.side_effect = error

                        with patch("analyzer.pipeline.pipeline.logger") as mock_logger:
                            with pytest.raises(UnplayableFileError):
                                Pipeline.run_analysis(
                                    queue,
                                    str(audio_file),
                                    str(dest_dir),
                                    "test.mp3",
                                    PipelineOptions(),
                                )

                            mock_logger.exception.assert_called_once_with(error)


class TestPipelineStaticMethod:
    """Tests for Pipeline static method behavior."""

    def test_run_analysis_is_static(self):
        """Test that run_analysis is a static method."""
        # Should be callable without instantiating Pipeline
        assert callable(Pipeline.run_analysis)

        # Should not require 'self' argument
        import inspect
        sig = inspect.signature(Pipeline.run_analysis)
        params = list(sig.parameters.keys())
        assert "self" not in params


class TestPipelineIntegrationScenarios:
    """Integration-style tests with multiple mocked components."""

    def test_full_pipeline_happy_path(self, tmp_path):
        """Test complete happy path through all pipeline stages."""
        queue = Queue()
        audio_file = tmp_path / "input.mp3"
        audio_file.write_text("audio")
        dest_dir = tmp_path / "imported"
        dest_dir.mkdir()

        # Simulate each step enriching the metadata
        def make_step(additional_data):
            def step(*args, **kwargs):
                metadata = args[-1] if args else kwargs.get("metadata", {})
                return {**metadata, **additional_data}
            return step

        with patch("analyzer.pipeline.pipeline.analyze_metadata", side_effect=make_step({
            "track_title": "My Song",
            "artist_name": "My Artist",
            "album_title": "My Album",
            "mime": "audio/mp3",
        })):
            with patch("analyzer.pipeline.pipeline.analyze_duration", side_effect=make_step({
                "length_seconds": 180.5,
                "length": "0:03:00.500000",
                "cuein": 0.0,
                "cueout": 180.5,
            })):
                with patch("analyzer.pipeline.pipeline.analyze_replaygain", side_effect=make_step({
                    "replay_gain": -6.5,
                })):
                    with patch("analyzer.pipeline.pipeline.analyze_playability", side_effect=make_step({})):
                        with patch("analyzer.pipeline.pipeline.organise_file", side_effect=make_step({
                            "full_path": str(dest_dir / "My Artist" / "My Album" / "My Song.mp3"),
                        })):
                            Pipeline.run_analysis(
                                queue,
                                str(audio_file),
                                str(dest_dir),
                                "My Song.mp3",
                                PipelineOptions(),
                            )

        result = queue.get()
        assert result["import_status"] == PipelineStatus.SUCCEED
        assert result["track_title"] == "My Song"
        assert result["artist_name"] == "My Artist"
        assert result["album_title"] == "My Album"
        assert result["mime"] == "audio/mp3"
        assert result["length_seconds"] == 180.5
        assert result["replay_gain"] == -6.5
        assert "full_path" in result
