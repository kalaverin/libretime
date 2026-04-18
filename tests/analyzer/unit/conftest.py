"""
Pytest fixtures for analyzer unit tests.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_subprocess_result():
    """Factory fixture for creating mock subprocess results."""
    def _make(stdout: str = "", stderr: str = "", returncode: int = 0):
        result = MagicMock()
        result.stdout = stdout
        result.stderr = stderr
        result.returncode = returncode
        return result
    return _make


@pytest.fixture
def audio_file_factory(tmp_path: Path):
    """Factory fixture for creating temporary audio files."""
    def _make(filename: str = "test.mp3", content: bytes = b"fake audio data") -> Path:
        file_path = tmp_path / filename
        file_path.write_bytes(content)
        return file_path
    return _make


@pytest.fixture
def storage_path(tmp_path: Path) -> Path:
    """Create a temporary storage directory."""
    storage = tmp_path / "storage"
    storage.mkdir()
    return storage
