import logging

from enum import Enum
from queue import Queue
from typing import Any, Protocol

from pydantic import BaseModel

from analyzer.pipeline.analyze_cuepoint import (
    analyze_cuepoint,
    analyze_duration,
)
from analyzer.pipeline.analyze_metadata import analyze_metadata
from analyzer.pipeline.analyze_playability import (
    UnplayableFileError,
    analyze_playability,
)
from analyzer.pipeline.analyze_replaygain import analyze_replaygain
from analyzer.pipeline.organise_file import organise_file

logger = logging.getLogger(__name__)


class Step(Protocol):
    @staticmethod
    def __call__(filename: str, metadata: dict[str, Any]): ...


class PipelineStatus(int, Enum):
    SUCCEED = 0
    PENDING = 1
    FAILED = 2


class PipelineOptions(BaseModel):
    analyze_cue_points: bool = False


class Pipeline:
    """Analyzes and imports an audio file into the Airtime library.

    This currently performs metadata extraction (eg. gets the ID3 tags from an MP3),
    then moves the file to the Airtime music library (stor/imported), and returns
    the results back to the parent process.
    """

    @staticmethod
    def run_analysis(
        queue: Queue[Any],
        audio_file_path: str,
        import_directory: str,
        original_filename: str,
        options: PipelineOptions,
    ) -> None:
        """Analyze and import an audio file, and put all extracted metadata into queue.

        Keyword arguments:
            queue: A multiprocessing.queues.Queue which will be used to pass the
                   extracted metadata back to the parent process.
            audio_file_path: Path on disk to the audio file to analyze.
            import_directory: Path to the final Airtime "import" directory where
                              we will move the file.
            original_filename: The original filename of the file, which we'll try to
                               preserve. The file at audio_file_path typically has a
                               temporary randomly generated name, which is why we want
                               to know what the original name was.
        """
        metadata: dict[str, Any] = {}

        try:
            # Analyze the audio file we were told to analyze:
            # First, we extract the ID3 tags and other metadata:

            metadata = analyze_metadata(audio_file_path, metadata)

            # Then we analyze the duration of the file.
            metadata = analyze_duration(audio_file_path, metadata)

            # Then we analyze the cue points in the file.
            if options.analyze_cue_points:
                metadata = analyze_cuepoint(audio_file_path, metadata)

            # Then we analyze the replaygain of the file.
            metadata = analyze_replaygain(audio_file_path, metadata)

            # Finally, we check if the file is playable.
            metadata = analyze_playability(audio_file_path, metadata)

            # If all the analysis steps above succeeded, we store file.
            metadata = organise_file(
                audio_file_path,
                import_directory,
                original_filename,
                metadata,
            )

            # If we got here, then the file was successfully analyzed.
            metadata["import_status"] = PipelineStatus.SUCCEED

            # Pass all the file metadata back to the main analyzer process
            queue.put(metadata)

        except UnplayableFileError as exception:
            logger.exception(exception)
            metadata["import_status"] = PipelineStatus.FAILED
            metadata["reason"] = "The file could not be played."
            raise

        except Exception as exception:
            logger.exception(exception)
            raise
