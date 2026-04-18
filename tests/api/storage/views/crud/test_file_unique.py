"""
T289: File unique together constraint tests.

Tests for unique constraints on File model.
Note: File model has no unique_together constraints by design.
"""

import pytest

from model_bakery import baker

from api.core.models import User
from api.storage.models import File, Library


@pytest.mark.django_db
class TestFileUniqueConstraints:
    """Test File model unique constraints behavior."""

    @pytest.fixture
    def test_library(self):
        return baker.make(Library, name="Test Library", description="Test")

    def test_file_no_unique_constraint_on_filepath(self, admin_client):
        """File model allows duplicate filepaths (no unique constraint)."""
        user = baker.make(User, username="file_test")
        library = baker.make(Library, name="Test Lib", description="Test")

        # Create first file
        file1 = baker.make(
            File,
            name="song.mp3",
            filepath="/path/to/same/file.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        # Create second file with same filepath - should succeed
        file2 = baker.make(
            File,
            name="song2.mp3",
            filepath="/path/to/same/file.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        # Both files exist with same filepath
        assert file1.id != file2.id
        assert file1.filepath == file2.filepath

    def test_file_no_unique_constraint_on_name(self, admin_client):
        """File model allows duplicate names (no unique constraint)."""
        user = baker.make(User, username="file_test")
        library = baker.make(Library, name="Test Lib", description="Test")

        # Create multiple files with same name
        file1 = baker.make(
            File,
            name="same_name.mp3",
            filepath="/path/to/file1.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )
        file2 = baker.make(
            File,
            name="same_name.mp3",
            filepath="/path/to/file2.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        assert file1.id != file2.id
        assert file1.name == file2.name

    def test_file_allows_same_name_different_library(self, admin_client):
        """Same filename in different libraries is allowed."""
        user = baker.make(User, username="file_test")
        lib1 = baker.make(Library, name="Lib1", description="Test")
        lib2 = baker.make(Library, name="Lib2", description="Test")

        file1 = baker.make(
            File,
            name="shared.mp3",
            filepath="/lib1/shared.mp3",
            mime="audio/mp3",
            library=lib1,
            owner=user,
        )
        file2 = baker.make(
            File,
            name="shared.mp3",
            filepath="/lib2/shared.mp3",
            mime="audio/mp3",
            library=lib2,
            owner=user,
        )

        assert file1.id != file2.id
        assert file1.name == file2.name
        assert file1.library != file2.library

    def test_file_allows_same_name_same_library(self, admin_client):
        """Duplicate filenames in same library are allowed."""
        user = baker.make(User, username="file_test")
        library = baker.make(Library, name="Test Lib", description="Test")

        # Multiple files with same name in same library
        file1 = baker.make(
            File,
            name="duplicate.mp3",
            filepath="/path/to/file1.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )
        file2 = baker.make(
            File,
            name="duplicate.mp3",
            filepath="/path/to/file2.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        assert file1.id != file2.id
        assert file1.name == file2.name
        assert file1.library == file2.library

    def test_file_no_unique_together_on_library_name(self, admin_client):
        """No unique_together constraint on (library, name)."""
        user = baker.make(User, username="file_test")
        library = baker.make(Library, name="Test Lib", description="Test")

        # Create files that would violate unique_together if it existed
        for i in range(3):
            baker.make(
                File,
                name="repeated.mp3",
                filepath=f"/path/to/file{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
            )

        # All files created successfully
        files = File.objects.filter(name="repeated.mp3", library=library)
        assert files.count() == 3
