"""
T297: Stereo/Mono detection tests.

Paranoid tests for audio channel detection (stereo vs mono).
"""

import pytest

from model_bakery import baker

from api.core.models import User
from api.storage.models import File, Library


@pytest.mark.django_db
class TestMonoFileDetection:
    """Test mono (1 channel) audio file detection."""

    def test_mono_file_channels(self, guest_client):
        """Mono file has channels=1."""
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

        response = guest_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["channels"] == 1

    def test_mono_file_retrieve(self, guest_client):
        """Retrieve mono file details."""
        user = baker.make(User, username="mono_test2")
        library = baker.make(
            Library,
            code="MONO2",
            name="Mono",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="voice_recording.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=1,
            sample_rate=22050,
        )

        response = guest_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["channels"] == 1
        assert data["sample_rate"] == 22050

    def test_mono_in_list(self, guest_client):
        """Mono files appear correctly in list."""
        user = baker.make(User, username="mono_list")
        library = baker.make(
            Library,
            code="MONO3",
            name="Mono",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="mono_listed.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=1,
        )

        response = guest_client.get("/api/v2/files")
        assert response.status_code == 200
        data = response.json()

        mono_files = [f for f in data if f.get("channels") == 1]
        assert len(mono_files) >= 1


@pytest.mark.django_db
class TestStereoFileDetection:
    """Test stereo (2 channels) audio file detection."""

    def test_stereo_file_channels(self, guest_client):
        """Stereo file has channels=2."""
        user = baker.make(User, username="stereo_test")
        library = baker.make(
            Library,
            code="STEREO",
            name="Stereo",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="stereo.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
        )

        response = guest_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["channels"] == 2

    def test_stereo_file_retrieve(self, guest_client):
        """Retrieve stereo file details."""
        user = baker.make(User, username="stereo_test2")
        library = baker.make(
            Library,
            code="STEREO2",
            name="Stereo",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="music_track.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
            sample_rate=44100,
        )

        response = guest_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["channels"] == 2
        assert data["sample_rate"] == 44100

    def test_stereo_in_list(self, guest_client):
        """Stereo files appear correctly in list."""
        user = baker.make(User, username="stereo_list")
        library = baker.make(
            Library,
            code="STEREO3",
            name="Stereo",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="stereo_listed.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
        )

        response = guest_client.get("/api/v2/files")
        assert response.status_code == 200
        data = response.json()

        stereo_files = [f for f in data if f.get("channels") == 2]
        assert len(stereo_files) >= 1


@pytest.mark.django_db
class TestSurroundFileDetection:
    """Test surround/multi-channel audio file detection."""

    def test_5_1_surround(self, guest_client):
        """5.1 surround file has channels=6."""
        user = baker.make(User, username="surround_test")
        library = baker.make(
            Library,
            code="SURROUND",
            name="Surround",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="surround_51.flac",
            mime="audio/flac",
            library=library,
            owner=user,
            channels=6,
        )

        response = guest_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["channels"] == 6

    def test_7_1_surround(self, guest_client):
        """7.1 surround file has channels=8."""
        user = baker.make(User, username="surround_test2")
        library = baker.make(
            Library,
            code="SURROUND2",
            name="Surround",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="surround_71.flac",
            mime="audio/flac",
            library=library,
            owner=user,
            channels=8,
        )

        response = guest_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["channels"] == 8

    def test_quadraphonic(self, guest_client):
        """Quadraphonic file has channels=4."""
        user = baker.make(User, username="quad_test")
        library = baker.make(
            Library,
            code="QUAD",
            name="Quad",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="quadraphonic.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=4,
        )

        response = guest_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["channels"] == 4


@pytest.mark.django_db
class TestChannelFiltering:
    """Test filtering by channel count."""

    def test_filter_by_mono(self, guest_client):
        """Filter mono files."""
        user = baker.make(User, username="filter_test")
        library = baker.make(
            Library,
            code="FILTER",
            name="Filter",
            description="Test",
        )

        # Create mono files
        for i in range(3):
            baker.make(
                File,
                name=f"mono_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
                channels=1,
            )

        # Create stereo files
        for i in range(3):
            baker.make(
                File,
                name=f"stereo_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
                channels=2,
            )

        response = guest_client.get("/api/v2/files")
        assert response.status_code == 200
        data = response.json()

        mono_files = [f for f in data if f.get("channels") == 1]
        stereo_files = [f for f in data if f.get("channels") == 2]

        assert len(mono_files) >= 3
        assert len(stereo_files) >= 3

    def test_mixed_channels_in_list(self, guest_client):
        """List contains files with various channel counts."""
        user = baker.make(User, username="mixed_test")
        library = baker.make(
            Library,
            code="MIXED",
            name="Mixed",
            description="Test",
        )

        # Create files with different channel counts
        channel_counts = [1, 2, 4, 6]
        for channels in channel_counts:
            baker.make(
                File,
                name=f"channels_{channels}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
                channels=channels,
            )

        response = guest_client.get("/api/v2/files")
        assert response.status_code == 200
        data = response.json()

        found_channels = set()
        for f in data:
            if f.get("channels") in channel_counts:
                found_channels.add(f["channels"])

        assert 1 in found_channels
        assert 2 in found_channels


@pytest.mark.django_db
class TestChannelUpdate:
    """Test updating channel information."""

    def test_update_mono_to_stereo(self, guest_client):
        """Update file from mono to stereo."""
        import json

        user = baker.make(User, username="update_test")
        library = baker.make(
            Library,
            code="UPDATE",
            name="Update",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="was_mono.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=1,
        )

        response = guest_client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"channels": 2}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["channels"] == 2

    def test_update_stereo_to_mono(self, guest_client):
        """Update file from stereo to mono."""
        import json

        user = baker.make(User, username="update_test2")
        library = baker.make(
            Library,
            code="UPDATE2",
            name="Update",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="was_stereo.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
        )

        response = guest_client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"channels": 1}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["channels"] == 1

    def test_clear_channels(self, guest_client):
        """Clear channels field."""
        import json

        user = baker.make(User, username="clear_test")
        library = baker.make(
            Library,
            code="CLEAR",
            name="Clear",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="unknown_channels.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
        )

        response = guest_client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"channels": None}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["channels"] is None


@pytest.mark.django_db
class TestChannelEdgeCases:
    """Test channel detection edge cases."""

    def test_null_channels(self, guest_client):
        """File with unknown channel count."""
        user = baker.make(User, username="null_test")
        library = baker.make(
            Library,
            code="NULL",
            name="Null",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="unknown.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=None,
        )

        response = guest_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["channels"] is None

    def test_zero_channels_invalid(self, guest_client):
        """Zero channels is unusual but possible."""
        user = baker.make(User, username="zero_test")
        library = baker.make(
            Library,
            code="ZERO",
            name="Zero",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="zero_channels.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=0,
        )

        response = guest_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["channels"] == 0
