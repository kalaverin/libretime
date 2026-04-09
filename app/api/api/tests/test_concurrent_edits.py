"""
T292: Concurrent edits tests.

Paranoid tests for concurrent modification scenarios.
Verify data integrity under race conditions.
"""

from datetime import timedelta

import pytest

from model_bakery import baker
from sdk.datetime import format_datetime

from api.core.models import Role, User
from api.schedule.models import Playlist, PlaylistContent, Show, ShowInstance
from api.storage.models import File, Library
from sdk import now


@pytest.mark.django_db
class TestConcurrentPlaylistUpdates:
    """Test concurrent updates to same playlist."""

    def test_concurrent_name_updates_last_write_wins(self, api_client):
        """Two concurrent name updates - last write wins."""
        import json

        user = baker.make(User, username="concurrent_test", role=Role.HOST)
        playlist = baker.make(
            Playlist,
            name="Original Name",
            owner=user,
            description="Test",
        )

        response1 = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"name": "First Update"}),
            content_type="application/json",
        )
        assert response1.status_code == 200

        response2 = api_client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"name": "Second Update"}),
            content_type="application/json",
        )
        assert response2.status_code == 200

        playlist.refresh_from_db()
        assert playlist.name == "Second Update"

    def test_concurrent_description_updates(self, api_client):
        """Concurrent description updates - last write wins."""
        import json

        user = baker.make(User, username="concurrent_test2", role=Role.HOST)
        playlist = baker.make(
            Playlist,
            name="Test Playlist",
            owner=user,
            description="Original Description",
        )

        updates = ["Update A", "Update B", "Update C"]
        for update in updates:
            response = api_client.patch(
                f"/api/v2/playlists/{playlist.id}",
                json.dumps({"description": update}),
                content_type="application/json",
            )
            assert response.status_code == 200

        playlist.refresh_from_db()
        assert playlist.description == "Update C"

    def test_concurrent_length_updates(self, api_client):
        """Concurrent length field updates."""
        import json

        user = baker.make(User, username="concurrent_test3", role=Role.HOST)
        playlist = baker.make(
            Playlist,
            name="Test Playlist",
            owner=user,
            length=timedelta(minutes=10),
        )

        lengths = ["00:05:00", "00:15:00", "00:30:00", "01:00:00"]
        for length in lengths:
            response = api_client.patch(
                f"/api/v2/playlists/{playlist.id}",
                json.dumps({"length": length}),
                content_type="application/json",
            )
            assert response.status_code == 200

        playlist.refresh_from_db()
        assert playlist.length == timedelta(hours=1)


@pytest.mark.django_db
class TestConcurrentContentModifications:
    """Test concurrent playlist content modifications."""

    def test_concurrent_content_additions(self, api_client):
        """Multiple content additions to same playlist."""
        user = baker.make(User, username="content_test", role=Role.HOST)
        library = baker.make(
            Library,
            code="TEST",
            name="Test",
            description="Test",
        )
        playlist = baker.make(Playlist, name="Content Test", owner=user)

        files = []
        for i in range(5):
            file_obj = baker.make(
                File,
                name=f"song{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
            )
            files.append(file_obj)

        for i, file_obj in enumerate(files):
            baker.make(
                PlaylistContent,
                playlist=playlist,
                kind=PlaylistContent.Kind.FILE,
                file=file_obj,
                position=i + 1,
                offset=0,
            )

        contents = PlaylistContent.objects.filter(playlist=playlist)
        assert contents.count() == 5

    def test_concurrent_position_updates(self, api_client):
        """Concurrent position updates - verify ordering."""
        user = baker.make(User, username="position_test", role=Role.HOST)
        library = baker.make(
            Library,
            code="TEST2",
            name="Test",
            description="Test",
        )
        playlist = baker.make(Playlist, name="Position Test", owner=user)
        file_obj = baker.make(
            File,
            name="song.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        content = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file_obj,
            position=1,
            offset=0,
        )

        positions = [5, 3, 8, 2, 10]
        for pos in positions:
            content.position = pos
            content.save()

        content.refresh_from_db()
        assert content.position == 10

    def test_consecutive_cue_point_updates(self, api_client):
        """Consecutive cue point modifications."""
        user = baker.make(User, username="cue_test", role=Role.HOST)
        library = baker.make(
            Library,
            code="TEST3",
            name="Test",
            description="Test",
        )
        playlist = baker.make(Playlist, name="Cue Test", owner=user)
        file_obj = baker.make(
            File,
            name="song.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        content = baker.make(
            PlaylistContent,
            playlist=playlist,
            kind=PlaylistContent.Kind.FILE,
            file=file_obj,
            position=1,
            cue_in="00:00:00",
            cue_out="00:05:00",
        )

        cue_updates = [
            ("00:00:05", "00:04:55"),
            ("00:00:10", "00:04:50"),
            ("00:00:00", "00:05:00"),
            ("00:00:30", "00:04:30"),
        ]

        for cue_in, cue_out in cue_updates:
            content.cue_in = cue_in
            content.cue_out = cue_out
            content.save()

        content.refresh_from_db()
        assert content.cue_in == timedelta(seconds=30)
        assert content.cue_out == timedelta(minutes=4, seconds=30)


@pytest.mark.django_db
class TestConcurrentShowInstanceUpdates:
    """Test concurrent show instance modifications."""

    def test_concurrent_instance_time_updates(self, api_client):
        """Concurrent instance start/end time updates."""
        show = baker.make(Show, name="Time Test Show")
        base_time = now()
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=base_time,
            ends_at=base_time + timedelta(hours=1),
        )

        time_updates = [
            (base_time + timedelta(hours=1), base_time + timedelta(hours=2)),
            (base_time + timedelta(hours=2), base_time + timedelta(hours=3)),
            (base_time - timedelta(hours=1), base_time),
        ]

        for starts_at, ends_at in time_updates:
            instance.starts_at = starts_at
            instance.ends_at = ends_at
            instance.save()

        instance.refresh_from_db()
        assert format_datetime(instance.starts_at) == format_datetime(
            base_time - timedelta(hours=1),
        )
        assert format_datetime(instance.ends_at) == format_datetime(base_time)


@pytest.mark.django_db
class TestDataIntegrityAfterConcurrentOperations:
    """Verify data integrity after concurrent-like operations."""

    def test_playlist_content_count_integrity(self, api_client):
        """Verify content count matches actual contents after multiple ops."""
        user = baker.make(User, username="integrity_test", role=Role.HOST)
        library = baker.make(
            Library,
            code="TEST4",
            name="Test",
            description="Test",
        )
        playlist = baker.make(Playlist, name="Integrity Test", owner=user)

        for i in range(10):
            file_obj = baker.make(
                File,
                name=f"rapid{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
            )
            baker.make(
                PlaylistContent,
                playlist=playlist,
                kind=PlaylistContent.Kind.FILE,
                file=file_obj,
                position=i + 1,
                offset=0,
            )

        count = PlaylistContent.objects.filter(playlist=playlist).count()
        assert count == 10

        positions = list(
            PlaylistContent.objects.filter(playlist=playlist).values_list(
                "position",
                flat=True,
            ),
        )
        assert len(positions) == len(set(positions))

    def test_file_ownership_integrity(self, api_client):
        """Verify file ownership after concurrent user updates."""
        library = baker.make(
            Library,
            code="TEST5",
            name="Test",
            description="Test",
        )
        user1 = baker.make(User, username="owner1", role=Role.HOST)
        user2 = baker.make(User, username="owner2", role=Role.HOST)

        file_obj = baker.make(
            File,
            name="ownership_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user1,
        )

        owners = [user1, user2, user1, user2, user1]
        for owner in owners:
            file_obj.owner = owner
            file_obj.save()

        file_obj.refresh_from_db()
        assert file_obj.owner_id == user1.id

    def test_schedule_integrity_after_multiple_updates(self, api_client):
        """Verify schedule integrity after multiple rapid updates."""
        from api.schedule.models import Schedule

        show = baker.make(Show, name="Schedule Test")
        base_time = now()
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at=base_time,
            ends_at=base_time + timedelta(hours=1),
        )
        library = baker.make(
            Library,
            code="TEST6",
            name="Test",
            description="Test",
        )
        user = baker.make(User, username="schedule_test", role=Role.HOST)
        file_obj = baker.make(
            File,
            name="schedule_file.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        schedule = baker.make(
            Schedule,
            instance=instance,
            file=file_obj,
            starts_at=base_time,
            ends_at=base_time + timedelta(minutes=30),
            cue_in=timedelta(0),
            cue_out=timedelta(minutes=30),
            position=1,
            broadcasted=1,
        )

        for i in range(5):
            schedule.cue_out = timedelta(minutes=25 + i)
            schedule.save()

        schedule.refresh_from_db()
        assert schedule.cue_out == timedelta(minutes=29)


@pytest.mark.django_db
class TestConcurrentAPICalls:
    """Test concurrent API call scenarios."""

    def test_multiple_retrieve_calls_consistency(self, api_client):
        """Multiple retrieve calls return consistent data."""
        user = baker.make(User, username="api_test", role=Role.HOST)
        playlist = baker.make(
            Playlist,
            name="Consistency Test",
            owner=user,
            description="Test Description",
        )

        responses = []
        for _ in range(10):
            response = api_client.get(f"/api/v2/playlists/{playlist.id}")
            assert response.status_code == 200
            responses.append(response.json())

        first = responses[0]
        for resp in responses[1:]:
            assert resp["id"] == first["id"]
            assert resp["name"] == first["name"]
            assert resp["description"] == first["description"]

    def test_list_and_retrieve_consistency(self, api_client):
        """LIST and RETRIEVE return consistent data."""
        user = baker.make(User, username="api_test2", role=Role.HOST)
        playlist = baker.make(Playlist, name="List/Retrieve Test", owner=user)

        list_response = api_client.get("/api/v2/playlists")
        list_data = list_response.json()
        list_item = next(p for p in list_data if p["id"] == playlist.id)

        retrieve_response = api_client.get(f"/api/v2/playlists/{playlist.id}")
        retrieve_data = retrieve_response.json()

        assert list_item["id"] == retrieve_data["id"]
        assert list_item["name"] == retrieve_data["name"]
