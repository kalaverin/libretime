"""
T295: ReplayGain calculation tests.

Paranoid tests for replay gain functionality.
"""

from decimal import Decimal

import pytest

from model_bakery import baker

from api.core.models import User
from api.storage.models import File, Library


@pytest.mark.django_db
class TestReplayGainStorage:
    """Test replay gain value storage."""

    def test_positive_replay_gain(self, admin_client):
        """Store positive replay gain value."""
        user = baker.make(User, username="replay_test")
        library = baker.make(
            Library,
            code="REPLAY",
            name="Replay",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="loud.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=Decimal("3.50"),
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert Decimal(data["replay_gain"]) == Decimal("3.50")

    def test_negative_replay_gain(self, admin_client):
        """Store negative replay gain value."""
        user = baker.make(User, username="replay_test2")
        library = baker.make(
            Library,
            code="REPLAY2",
            name="Replay",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="quiet.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=Decimal("-8.25"),
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert Decimal(data["replay_gain"]) == Decimal("-8.25")

    def test_zero_replay_gain(self, admin_client):
        """Store zero replay gain value."""
        user = baker.make(User, username="replay_test3")
        library = baker.make(
            Library,
            code="REPLAY3",
            name="Replay",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="normalized.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=Decimal("0.00"),
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert Decimal(data["replay_gain"]) == Decimal("0.00")

    def test_null_replay_gain(self, admin_client):
        """Null replay gain when not calculated."""
        user = baker.make(User, username="replay_test4")
        library = baker.make(
            Library,
            code="REPLAY4",
            name="Replay",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="no_replaygain.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=None,
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["replay_gain"] is None

    def test_high_precision_replay_gain(self, admin_client):
        """Replay gain with 2 decimal precision."""
        user = baker.make(User, username="replay_test5")
        library = baker.make(
            Library,
            code="REPLAY5",
            name="Replay",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="precise.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=Decimal("-4.99"),
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert Decimal(data["replay_gain"]) == Decimal("-4.99")


@pytest.mark.django_db
class TestReplayGainUpdate:
    """Test replay gain value updates."""

    def test_update_replay_gain(self, admin_client):
        """Update replay gain value."""
        import json

        user = baker.make(User, username="replay_update")
        library = baker.make(
            Library,
            code="REPLAY6",
            name="Replay",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="update_me.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=Decimal("-2.00"),
        )

        response = admin_client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"replay_gain": "-5.50"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["replay_gain"]) == Decimal("-5.50")

    def test_clear_replay_gain(self, admin_client):
        """Clear replay gain value."""
        import json

        user = baker.make(User, username="replay_clear")
        library = baker.make(
            Library,
            code="REPLAY7",
            name="Replay",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="clear_me.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=Decimal("-3.00"),
        )

        response = admin_client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"replay_gain": None}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["replay_gain"] is None


@pytest.mark.django_db
class TestReplayGainInList:
    """Test replay gain in list responses."""

    def test_list_includes_replay_gain(self, admin_client):
        """LIST includes replay gain field."""
        user = baker.make(User, username="replay_list")
        library = baker.make(
            Library,
            code="REPLAY8",
            name="Replay",
            description="Test",
        )

        baker.make(
            File,
            name="listed.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=Decimal("-1.50"),
        )

        response = admin_client.get("/api/v2/files")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "replay_gain" in data[0]

    def test_list_shows_null_replay_gain(self, admin_client):
        """LIST shows null replay gain for uncalculated files."""
        user = baker.make(User, username="replay_list2")
        library = baker.make(
            Library,
            code="REPLAY9",
            name="Replay",
            description="Test",
        )

        baker.make(
            File,
            name="no_gain.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=None,
        )

        response = admin_client.get("/api/v2/files")
        assert response.status_code == 200
        data = response.json()
        file_data = next(f for f in data if f.get("replay_gain") is None)
        assert file_data is not None


@pytest.mark.django_db
class TestReplayGainFiltering:
    """Test filtering by replay gain."""

    def test_filter_files_with_replay_gain(self, admin_client):
        """Filter files that have replay gain calculated."""
        user = baker.make(User, username="replay_filter")
        library = baker.make(
            Library,
            code="REPLAY10",
            name="Replay",
            description="Test",
        )

        # Files with replay gain
        for i in range(3):
            baker.make(
                File,
                name=f"with_gain_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
                replay_gain=Decimal(f"-{i+1}.00"),
            )

        # Files without replay gain
        for i in range(2):
            baker.make(
                File,
                name=f"no_gain_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
                replay_gain=None,
            )

        response = admin_client.get("/api/v2/files")
        assert response.status_code == 200
        data = response.json()

        # Count files with and without replay gain
        with_gain = [f for f in data if f.get("replay_gain") is not None]
        without_gain = [f for f in data if f.get("replay_gain") is None]

        assert len(with_gain) >= 3
        assert len(without_gain) >= 2


@pytest.mark.django_db
class TestReplayGainEdgeCases:
    """Test replay gain edge cases."""

    def test_very_large_negative_replay_gain(self, admin_client):
        """Very quiet file with large negative replay gain."""
        user = baker.make(User, username="replay_edge")
        library = baker.make(
            Library,
            code="REPLAY11",
            name="Replay",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="very_quiet.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=Decimal("-20.00"),
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["replay_gain"]) == Decimal("-20.00")

    def test_very_large_positive_replay_gain(self, admin_client):
        """Very loud file with large positive replay gain."""
        user = baker.make(User, username="replay_edge2")
        library = baker.make(
            Library,
            code="REPLAY12",
            name="Replay",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="very_loud.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=Decimal("15.00"),
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["replay_gain"]) == Decimal("15.00")

    def test_replay_gain_with_trailing_zeros(self, admin_client):
        """Replay gain value with trailing zeros."""
        user = baker.make(User, username="replay_edge3")
        library = baker.make(
            Library,
            code="REPLAY13",
            name="Replay",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="trailing.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            replay_gain=Decimal("-5.50"),
        )

        response = admin_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()
        # Value should be preserved or normalized
        assert Decimal(data["replay_gain"]) == Decimal("-5.50")
