"""
T290: Cascade deletes tests.

Tests for cascade behaviors: show->instances, playlist->contents, etc.
"""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Playlist, PlaylistContent, Show, ShowInstance
from api.storage.models import File, Library


@pytest.mark.django_db
class TestShowCascadeDelete:
    """Test cascade delete for Show -> ShowInstance."""

    def test_delete_show_cascades_to_instances(self):
        """Deleting a show should delete its instances."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)

        instance_id = instance.id
        show.delete()

        # Instance should be deleted
        assert not ShowInstance.objects.filter(id=instance_id).exists()

    def test_delete_show_keeps_other_instances(self):
        """Deleting one show shouldn't affect other shows' instances."""
        show1 = baker.make(Show, name="Show 1")
        show2 = baker.make(Show, name="Show 2")
        instance1 = baker.make(ShowInstance, show=show1)
        instance2 = baker.make(ShowInstance, show=show2)

        show1.delete()

        # instance2 should still exist
        assert ShowInstance.objects.filter(id=instance2.id).exists()
        assert not ShowInstance.objects.filter(id=instance1.id).exists()


@pytest.mark.django_db
class TestPlaylistCascadeDelete:
    """Test cascade delete for Playlist -> PlaylistContent."""

    def test_delete_playlist_cascades_to_contents(self):
        """Deleting a playlist should delete its contents."""
        user = baker.make(User, username="testuser")
        playlist = baker.make(Playlist, name="Test Playlist", owner=user)
        content = baker.make(PlaylistContent, playlist=playlist, position=1)

        content_id = content.id
        playlist.delete()

        # Content should be deleted
        assert not PlaylistContent.objects.filter(id=content_id).exists()

    def test_delete_playlist_keeps_other_contents(self):
        """Deleting one playlist shouldn't affect other playlists' contents."""
        user = baker.make(User, username="testuser")
        playlist1 = baker.make(Playlist, name="Playlist 1", owner=user)
        playlist2 = baker.make(Playlist, name="Playlist 2", owner=user)
        content1 = baker.make(PlaylistContent, playlist=playlist1, position=1)
        content2 = baker.make(PlaylistContent, playlist=playlist2, position=1)

        playlist1.delete()

        # content2 should still exist
        assert PlaylistContent.objects.filter(id=content2.id).exists()
        assert not PlaylistContent.objects.filter(id=content1.id).exists()


@pytest.mark.django_db
class TestLibraryFileBehavior:
    """Test library deletion behavior with files."""

    def test_delete_library_blocked_by_file_reference(self):
        """Deleting library fails if files reference it (DB constraint)."""
        library = baker.make(
            Library,
            code="TESTLIB",
            name="Test Library",
            description="Test",
        )
        user = baker.make(User, username="testuser")
        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        # This should fail with IntegrityError due to DB constraint
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            library.delete()


@pytest.mark.django_db
class TestUserFileBehavior:
    """Test user deletion behavior with files."""

    def test_delete_user_blocked_by_file_reference(self):
        """Deleting user fails if files reference it (DB constraint)."""
        library = baker.make(
            Library,
            code="TESTLIB2",
            name="Test Library",
            description="Test",
        )
        user = baker.make(User, username="testuser")
        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        # This should fail with IntegrityError due to DB constraint
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            user.delete()


@pytest.mark.django_db
class TestShowAutoPlaylistRelation:
    """Test Show and Playlist relations."""

    def test_delete_show_does_not_delete_auto_playlist(self):
        """Deleting Show should not delete linked auto_playlist (DO_NOTHING)."""
        user = baker.make(User, username="testuser")
        playlist = baker.make(Playlist, name="Show Playlist", owner=user)
        show = baker.make(Show, name="Test Show", auto_playlist=playlist)

        playlist_id = playlist.id
        show.delete()

        # Playlist should still exist
        assert Playlist.objects.filter(id=playlist_id).exists()
