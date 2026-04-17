"""
T298: File organization tests.

Paranoid tests for file organization (filepath, library, import status).
"""

import pytest

from model_bakery import baker

from api.core.models import User
from api.storage.models import File, Library


@pytest.mark.django_db
class TestFilePathOrganization:
    """Test file path organization."""

    def test_filepath_storage(self, api_client):
        """File path stored correctly."""
        user = baker.make(User, username="path_test")
        library = baker.make(
            Library,
            code="PATH",
            name="Path",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="song.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            filepath="/srv/libretime/music/2024/artist/album/song.mp3",
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert (
            data["filepath"]
            == "/srv/libretime/music/2024/artist/album/song.mp3"
        )

    def test_nested_directory_structure(self, api_client):
        """File in deeply nested directory."""
        user = baker.make(User, username="nested_test")
        library = baker.make(
            Library,
            code="NESTED",
            name="Nested",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="deep.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            filepath="/a/very/deep/nested/directory/structure/file.mp3",
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert "/a/very/deep/nested/" in data["filepath"]

    def test_unicode_filepath(self, api_client):
        """File path with unicode characters."""
        user = baker.make(User, username="unicode_path")
        library = baker.make(
            Library,
            code="UNICODE",
            name="Unicode",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="unicode.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            filepath="/music/日本語/アーティスト/曲.mp3",
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert "日本語" in data["filepath"]

    def test_relative_filepath(self, api_client):
        """File with relative path."""
        user = baker.make(User, username="relative_test")
        library = baker.make(
            Library,
            code="RELATIVE",
            name="Relative",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="relative.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            filepath="music/artist/album/song.mp3",
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["filepath"] == "music/artist/album/song.mp3"


@pytest.mark.django_db
class TestLibraryOrganization:
    """Test file organization by library."""

    def test_file_in_library(self, api_client):
        """File belongs to library."""
        user = baker.make(User, username="lib_test")
        library = baker.make(
            Library,
            code="MUSIC",
            name="Music",
            description="Main",
        )

        file_obj = baker.make(
            File,
            name="in_library.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["library"] == library.id

    def test_file_without_library(self, api_client):
        """File not assigned to any library."""
        user = baker.make(User, username="no_lib_test")

        file_obj = baker.make(
            File,
            name="no_library.mp3",
            mime="audio/mp3",
            library=None,
            owner=user,
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["library"] is None

    def test_files_by_library(self, api_client):
        """Filter files by library."""
        user = baker.make(User, username="lib_filter")
        lib1 = baker.make(
            Library,
            code="LIB1",
            name="Library 1",
            description="Test",
        )
        lib2 = baker.make(
            Library,
            code="LIB2",
            name="Library 2",
            description="Test",
        )

        for i in range(3):
            baker.make(
                File,
                name=f"lib1_{i}.mp3",
                mime="audio/mp3",
                library=lib1,
                owner=user,
            )

        for i in range(2):
            baker.make(
                File,
                name=f"lib2_{i}.mp3",
                mime="audio/mp3",
                library=lib2,
                owner=user,
            )

        response = api_client.get("/api/v2/files")
        assert response.status_code == 200
        data = response.json()

        lib1_files = [f for f in data if f.get("library") == lib1.id]
        lib2_files = [f for f in data if f.get("library") == lib2.id]

        assert len(lib1_files) >= 3
        assert len(lib2_files) >= 2


@pytest.mark.django_db
class TestImportStatusOrganization:
    """Test file organization by import status."""

    def test_success_status(self, api_client):
        """File with success import status."""
        user = baker.make(User, username="success_test")
        library = baker.make(
            Library,
            code="SUCCESS",
            name="Success",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="success.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            import_status=File.ImportStatus.SUCCESS,
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["import_status"] == File.ImportStatus.SUCCESS

    def test_pending_status(self, api_client):
        """File with pending import status."""
        user = baker.make(User, username="pending_test")
        library = baker.make(
            Library,
            code="PENDING",
            name="Pending",
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

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["import_status"] == File.ImportStatus.PENDING

    def test_failed_status(self, api_client):
        """File with failed import status."""
        user = baker.make(User, username="failed_test")
        library = baker.make(
            Library,
            code="FAILED",
            name="Failed",
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

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["import_status"] == File.ImportStatus.FAILED


@pytest.mark.django_db
class TestFileSizeOrganization:
    """Test file size organization."""

    def test_small_file(self, api_client):
        """Small file size."""
        user = baker.make(User, username="small_test")
        library = baker.make(
            Library,
            code="SMALL",
            name="Small",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="small.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            size=1024,  # 1KB
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["size"] == 1024

    def test_large_file(self, api_client):
        """Large file size."""
        user = baker.make(User, username="large_test")
        library = baker.make(
            Library,
            code="LARGE",
            name="Large",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="large.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            size=100 * 1024 * 1024,  # 100MB
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["size"] == 100 * 1024 * 1024

    def test_zero_size_file(self, api_client):
        """Zero size file."""
        user = baker.make(User, username="zero_test")
        library = baker.make(
            Library,
            code="ZERO",
            name="Zero",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="empty.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            size=0,
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["size"] == 0


@pytest.mark.django_db
class TestFileOrganizationUpdates:
    """Test updating file organization."""

    def test_move_to_different_library(self, api_client):
        """Move file to different library."""
        import json

        user = baker.make(User, username="move_test")
        lib1 = baker.make(
            Library,
            code="FROM",
            name="From",
            description="Test",
        )
        lib2 = baker.make(Library, code="TO", name="To", description="Test")

        file_obj = baker.make(
            File,
            name="move_me.mp3",
            mime="audio/mp3",
            library=lib1,
            owner=user,
        )

        response = api_client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"library": lib2.id}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["library"] == lib2.id

    def test_update_filepath(self, api_client):
        """Update file path with relative path."""
        import json

        user = baker.make(User, username="path_update")
        library = baker.make(
            Library,
            code="PATHUPD",
            name="PathUpd",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="relocate.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            filepath="old/path/file.mp3",
        )

        response = api_client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"filepath": "new/path/file.mp3"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filepath"] == "new/path/file.mp3"
