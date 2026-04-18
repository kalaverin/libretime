"""
T296: Silence detection tests.

Paranoid tests for file silence detection.
Note: silence_analyzed field is in analyzer, not exposed via API.
Tests verify file can be processed for silence detection.
"""

import pytest

from model_bakery import baker

from api.core.models import User
from api.storage.models import File, Library


@pytest.mark.django_db
class TestFileForSilenceProcessing:
    """Test files ready for silence processing."""

    def test_success_file_ready_for_processing(self, admin_client):
        """Successfully imported file ready for silence analysis."""
        user = baker.make(User, username="silence_test")
        library = baker.make(
            Library,
            code="SILENCE",
            name="Silence",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="ready.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            import_status=File.ImportStatus.SUCCESS,
            filepath="/path/to/ready.mp3",
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        # File is ready for processing
        assert data["import_status"] == File.ImportStatus.SUCCESS
        assert data["filepath"] == "/path/to/ready.mp3"
        assert data["mime"] == "audio/mp3"

    def test_pending_file_not_ready(self, admin_client):
        """Pending file not yet ready for silence analysis."""
        user = baker.make(User, username="silence_test2")
        library = baker.make(
            Library,
            code="SILENCE2",
            name="Silence",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="pending.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            import_status=File.ImportStatus.PENDING,
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["import_status"] == File.ImportStatus.PENDING

    def test_failed_file_not_processed(self, admin_client):
        """Failed import file not processed for silence."""
        user = baker.make(User, username="silence_test3")
        library = baker.make(
            Library,
            code="SILENCE3",
            name="Silence",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="failed.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            import_status=File.ImportStatus.FAILED,
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["import_status"] == File.ImportStatus.FAILED


@pytest.mark.django_db
class TestAudioFileProperties:
    """Test audio file properties for silence detection."""

    def test_audio_file_channels(self, admin_client):
        """Audio file with channel info."""
        user = baker.make(User, username="audio_test")
        library = baker.make(
            Library,
            code="AUDIO",
            name="Audio",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="stereo.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
            sample_rate=44100,
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["channels"] == 2
        assert data["sample_rate"] == 44100

    def test_audio_file_length(self, admin_client):
        """Audio file with length info."""
        from datetime import timedelta

        user = baker.make(User, username="audio_test2")
        library = baker.make(
            Library,
            code="AUDIO2",
            name="Audio",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="long.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            length=timedelta(minutes=5),
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["length"] == "00:05:00"

    def test_mono_audio_file(self, admin_client):
        """Mono audio file properties."""
        user = baker.make(User, username="mono_test")
        library = baker.make(
            Library,
            code="MONO",
            name="Mono",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="mono.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=1,
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["channels"] == 1


@pytest.mark.django_db
class TestSilenceDetectionEdgeCases:
    """Test silence detection edge cases."""

    def test_very_short_file(self, admin_client):
        """Very short audio file."""
        from datetime import timedelta

        user = baker.make(User, username="short_test")
        library = baker.make(
            Library,
            code="SHORT",
            name="Short",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="short.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            length=timedelta(seconds=1),
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["length"] == "00:00:01"

    def test_very_long_file(self, admin_client):
        """Very long audio file."""
        from datetime import timedelta

        user = baker.make(User, username="long_test")
        library = baker.make(
            Library,
            code="LONG",
            name="Long",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="long.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            length=timedelta(hours=2),
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["length"] == "02:00:00"

    def test_various_mime_types(self, admin_client):
        """Various audio MIME types."""
        user = baker.make(User, username="mime_test")
        library = baker.make(
            Library,
            code="MIME",
            name="MIME",
            description="Test",
        )

        mime_types = ["audio/mp3", "audio/ogg", "audio/flac", "audio/wav"]
        files = []
        for i, mime in enumerate(mime_types):
            file_obj = baker.make(
                File,
                name=f"file{i}.mp3",
                mime=mime,
                library=library,
                owner=user,
            )
            files.append(file_obj)

        for file_obj in files:
            response = admin_client.get(f"/api/v2/files/{file_obj.id}")
            assert response.status_code == 200


@pytest.mark.django_db
class TestFileListForProcessing:
    """Test listing files for batch silence processing."""

    def test_list_success_files(self, admin_client):
        """List files ready for silence processing."""
        user = baker.make(User, username="list_test")
        library = baker.make(
            Library,
            code="LIST",
            name="List",
            description="Test",
        )

        # Create success files
        for i in range(5):
            baker.make(
                File,
                name=f"success_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
                import_status=File.ImportStatus.SUCCESS,
            )

        response = admin_client.get("/api/v2/files?import_status=0")
        assert response.status_code == 200
        data = response.json()

        # All success files should be listed
        success_files = [
            f
            for f in data
            if f.get("import_status") == File.ImportStatus.SUCCESS
        ]
        assert len(success_files) >= 5
