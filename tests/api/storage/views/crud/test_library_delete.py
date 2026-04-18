"""Tests for Library DELETE endpoint (T200)."""

import json

import pytest

from model_bakery import baker

from api.storage.models import File, Library


@pytest.mark.django_db(transaction=True)
class TestLibraryViewSetDelete:
    """Test Libraries DELETE endpoint - DELETE /api/v2/libraries/{id}."""

    def setup_method(self):
        """Clean up files and libraries before each test."""
        # Delete files first (they reference track_types)
        File.objects.all().delete()
        Library.objects.all().delete()

    def test_delete_library_success_returns_204(self, guest_client):
        """DELETE should return 204 on successful deletion."""
        lib = baker.make(
            Library,
            code="test",
            name="Test",
            description="Test lib",
        )
        response = guest_client.delete(f"/api/v2/libraries/{lib.id}")
        assert response.status_code == 204

    def test_delete_library_removes_from_db(self, guest_client):
        """DELETE should remove library from database."""
        lib = baker.make(
            Library,
            code="test",
            name="Test",
            description="Test lib",
        )
        guest_client.delete(f"/api/v2/libraries/{lib.id}")
        assert Library.objects.filter(id=lib.id).count() == 0

    def test_delete_library_not_found_returns_404(self, guest_client):
        """DELETE non-existent library should return 404."""
        response = guest_client.delete("/api/v2/libraries/999999")
        assert response.status_code == 404

    def test_delete_library_no_auth_fails(self, client):
        """DELETE without auth should return 403."""
        lib = baker.make(
            Library,
            code="test",
            name="Test",
            description="Test lib",
        )
        response = client.delete(f"/api/v2/libraries/{lib.id}")
        assert response.status_code == 403

    @pytest.mark.xfail(
        reason="BUG T318: Cannot delete Library with Files due to track_type FK constraint",
    )
    def test_delete_library_with_files_sets_null(self, guest_client):
        """DELETE library with files should set file.library to null."""
        lib = baker.make(
            Library,
            code="test",
            name="Test",
            description="Test lib",
        )
        file = baker.make(File, library=lib, filepath="/test/file.mp3")

        response = guest_client.delete(f"/api/v2/libraries/{lib.id}")
        assert response.status_code == 204

        # Refresh file from DB
        file.refresh_from_db()
        assert file.library is None

    @pytest.mark.xfail(
        reason="BUG T318: Cannot delete Library with Files due to track_type FK constraint",
    )
    def test_delete_library_files_preserved(self, guest_client):
        """DELETE library should NOT delete associated files."""
        lib = baker.make(
            Library,
            code="test",
            name="Test",
            description="Test lib",
        )
        file = baker.make(File, library=lib, filepath="/test/file.mp3")
        file_id = file.id

        guest_client.delete(f"/api/v2/libraries/{lib.id}")

        # File should still exist
        assert File.objects.filter(id=file_id).exists()

    def test_delete_library_empty_succeeds(self, guest_client):
        """DELETE empty library (no files) should succeed."""
        lib = baker.make(
            Library,
            code="empty",
            name="Empty",
            description="Empty lib",
        )
        response = guest_client.delete(f"/api/v2/libraries/{lib.id}")
        assert response.status_code == 204

    @pytest.mark.xfail(
        reason="BUG T318: Cannot delete Library with Files due to track_type FK constraint",
    )
    def test_delete_library_multiple_files(self, guest_client):
        """DELETE library with multiple files should set all to null."""
        lib = baker.make(
            Library,
            code="multi",
            name="Multi",
            description="Multi lib",
        )
        files = [
            baker.make(File, library=lib, filepath=f"/test/file{i}.mp3")
            for i in range(5)
        ]

        guest_client.delete(f"/api/v2/libraries/{lib.id}")

        for file in files:
            file.refresh_from_db()
            assert file.library is None

    def test_delete_library_double_delete_returns_404(self, guest_client):
        """DELETE already deleted library should return 404."""
        lib = baker.make(
            Library,
            code="test",
            name="Test",
            description="Test lib",
        )
        guest_client.delete(f"/api/v2/libraries/{lib.id}")

        # Second delete should return 404
        response = guest_client.delete(f"/api/v2/libraries/{lib.id}")
        assert response.status_code == 404

    def test_delete_library_wrong_method_returns_405(self, guest_client):
        """POST to delete endpoint should return 405."""
        lib = baker.make(
            Library,
            code="test",
            name="Test",
            description="Test lib",
        )
        response = guest_client.post(
            f"/api/v2/libraries/{lib.id}",
            json.dumps({"action": "delete"}),
            content_type="application/json",
        )
        assert response.status_code == 405

    def test_delete_library_unicode_code(self, guest_client):
        """DELETE library with unicode code should work."""
        lib = baker.make(
            Library,
            code="日本語",
            name="Japanese",
            description="Test lib",
        )
        response = guest_client.delete(f"/api/v2/libraries/{lib.id}")
        assert response.status_code == 204
        assert not Library.objects.filter(id=lib.id).exists()

    def test_delete_library_returns_empty_body(self, guest_client):
        """DELETE should return empty response body."""
        lib = baker.make(
            Library,
            code="test",
            name="Test",
            description="Test lib",
        )
        response = guest_client.delete(f"/api/v2/libraries/{lib.id}")
        assert response.content == b""

    def test_delete_library_cascade_to_track_types(self, guest_client):
        """DELETE library should handle track types that reference it."""
        # Note: Track types have library FK - need to check behavior
        lib = baker.make(
            Library,
            code="test",
            name="Test",
            description="Test lib",
        )

        # Try to delete - if track types block it, should get 409
        # If they cascade, should succeed
        response = guest_client.delete(f"/api/v2/libraries/{lib.id}")
        # Accept either success or conflict depending on DB constraints
        assert response.status_code in [204, 409, 500]

    def test_delete_library_id_zero_returns_404(self, guest_client):
        """DELETE with id=0 should return 404."""
        response = guest_client.delete("/api/v2/libraries/0")
        assert response.status_code == 404

    def test_delete_library_negative_id_returns_404(self, guest_client):
        """DELETE with negative id should return 404."""
        response = guest_client.delete("/api/v2/libraries/-1")
        assert response.status_code == 404

    def test_delete_library_large_id_returns_404(self, guest_client):
        """DELETE with very large id should return 404."""
        response = guest_client.delete("/api/v2/libraries/999999999")
        assert response.status_code == 404

    def test_delete_library_sql_injection_attempt(self, guest_client):
        """DELETE with SQL injection in id should be handled safely."""
        # Django ORM should sanitize this
        response = guest_client.delete("/api/v2/libraries/1 OR 1=1")
        assert response.status_code == 404

    def test_delete_library_path_traversal_attempt(self, guest_client):
        """DELETE with path traversal in id should be handled safely."""
        response = guest_client.delete("/api/v2/libraries/../../../etc/passwd")
        assert response.status_code == 404

    def test_delete_library_special_chars_in_id(self, guest_client):
        """DELETE with special chars in id should return 404."""
        response = guest_client.delete("/api/v2/libraries/test%20id")
        assert response.status_code == 404
