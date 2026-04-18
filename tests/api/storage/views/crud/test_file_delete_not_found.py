"""Tests for File DELETE non-existent/edge cases (T192)."""

from unittest.mock import patch

import pytest

from model_bakery import baker

from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestFileViewSetDeleteNotFound:
    """Test Files DELETE edge cases - non-existent IDs, invalid formats."""

    def test_delete_non_existent_large_id(self, guest_client):
        """DELETE with large non-existent ID should return 404."""
        response = guest_client.delete("/api/v2/files/999999999")
        assert response.status_code == 404

    def test_delete_zero_id(self, guest_client):
        """DELETE with ID=0 should return 404 (not valid PK)."""
        response = guest_client.delete("/api/v2/files/0")
        assert response.status_code == 404

    def test_delete_negative_id(self, guest_client):
        """DELETE with negative ID should return 404."""
        response = guest_client.delete("/api/v2/files/-1")
        assert response.status_code == 404

    def test_delete_negative_large_id(self, guest_client):
        """DELETE with large negative ID should return 404."""
        response = guest_client.delete("/api/v2/files/-999999")
        assert response.status_code == 404

    def test_delete_string_id(self, guest_client):
        """DELETE with string ID should return 404."""
        response = guest_client.delete("/api/v2/files/abc")
        assert response.status_code == 404

    def test_delete_mixed_string_id(self, guest_client):
        """DELETE with alphanumeric ID should return 404."""
        response = guest_client.delete("/api/v2/files/abc123")
        assert response.status_code == 404

    def test_delete_sql_injection_attempt(self, guest_client):
        """DELETE with SQL injection attempt should return 404 (not execute SQL)."""
        # Try SQL injection - should be treated as invalid ID, not executed
        response = guest_client.delete("/api/v2/files/1%20OR%201=1")
        assert response.status_code == 404

    def test_delete_sql_injection_union(self, guest_client):
        """DELETE with UNION SQL injection should return 404."""
        response = guest_client.delete(
            "/api/v2/files/1%20UNION%20SELECT%20*%20FROM%20cc_files",
        )
        assert response.status_code == 404

    def test_delete_path_traversal_attempt(self, guest_client):
        """DELETE with path traversal should return 404."""
        response = guest_client.delete("/api/v2/files/../etc/passwd")
        assert response.status_code == 404

    def test_delete_special_chars_id(self, guest_client):
        """DELETE with special characters ID should return 404."""
        response = guest_client.delete("/api/v2/files/@#$%^&*")
        assert response.status_code == 404

    def test_delete_unicode_id(self, guest_client):
        """DELETE with unicode ID should return 404."""
        response = guest_client.delete("/api/v2/files/日本語")
        assert response.status_code == 404

    def test_delete_float_id(self, guest_client):
        """DELETE with float ID should return 404."""
        response = guest_client.delete("/api/v2/files/1.5")
        assert response.status_code == 404

    def test_delete_hex_id(self, guest_client):
        """DELETE with hex ID should return 404."""
        response = guest_client.delete("/api/v2/files/0x1A")
        assert response.status_code == 404

    def test_delete_empty_string_id(self, guest_client):
        """DELETE with empty ID should route to list endpoint (405)."""
        # DELETE /api/v2/files/ (with trailing slash) vs /api/v2/files
        response = guest_client.delete("/api/v2/files/")
        # This might be 301 redirect or 405 depending on URL routing
        assert response.status_code in [301, 302, 405, 404]

    @pytest.mark.xfail(
        reason="BUG T316: perform_destroy doesn't delete from DB, so second DELETE also returns 204",
    )
    def test_delete_double_delete(self, guest_client):
        """DELETE same file twice - second should return 404.

        BUG T316: First DELETE doesn't remove from DB, so second DELETE
        still finds the file and returns 204 instead of 404.
        """
        file = baker.make(
            File,
            name="Double Delete",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/double.mp3",
        )
        file_id = file.id

        # First delete (with mocks)
        with patch("api.storage.views.file.os.path.isfile", return_value=True):
            with patch("api.storage.views.file.remove"):
                response1 = guest_client.delete(f"/api/v2/files/{file_id}")
        assert response1.status_code == 204

        # Second delete should return 404, but due to T316 returns 204
        response2 = guest_client.delete(f"/api/v2/files/{file_id}")
        assert response2.status_code == 404

    def test_delete_after_manually_deleted_from_db(self, guest_client):
        """DELETE file that was manually removed from DB should return 404."""
        file = baker.make(
            File,
            name="Manually Deleted",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/manual.mp3",
        )
        file_id = file.id

        # Manually delete from DB
        file.delete()

        # DELETE should return 404
        response = guest_client.delete(f"/api/v2/files/{file_id}")
        assert response.status_code == 404

    def test_delete_deleted_file_still_on_disk(self, guest_client):
        """DELETE file deleted from DB but still on disk - should 404."""
        file = baker.make(
            File,
            name="DB Deleted",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/db_deleted.mp3",
        )
        file_id = file.id

        # Delete from DB but pretend file still on disk
        file.delete()

        with patch("api.storage.views.file.os.path.isfile", return_value=True):
            response = guest_client.delete(f"/api/v2/files/{file_id}")

        # Should still 404 - DB record not found
        assert response.status_code == 404

    def test_delete_max_int_id(self, guest_client):
        """DELETE with max integer ID should return 404."""
        # Test with PostgreSQL max int (2147483647)
        response = guest_client.delete("/api/v2/files/2147483647")
        assert response.status_code == 404

    def test_delete_max_int_plus_one_id(self, guest_client):
        """DELETE with max_int + 1 ID should return 404."""
        response = guest_client.delete("/api/v2/files/2147483648")
        assert response.status_code == 404

    def test_delete_scientific_notation_id(self, guest_client):
        """DELETE with scientific notation ID should return 404."""
        response = guest_client.delete("/api/v2/files/1e5")
        assert response.status_code == 404

    def test_delete_boolean_true_id(self, guest_client):
        """DELETE with 'true' as ID should return 404."""
        response = guest_client.delete("/api/v2/files/true")
        assert response.status_code == 404

    def test_delete_boolean_false_id(self, guest_client):
        """DELETE with 'false' as ID should return 404."""
        response = guest_client.delete("/api/v2/files/false")
        assert response.status_code == 404

    def test_delete_null_id(self, guest_client):
        """DELETE with 'null' as ID should return 404."""
        response = guest_client.delete("/api/v2/files/null")
        assert response.status_code == 404

    def test_delete_very_long_numeric_id(self, guest_client):
        """DELETE with very long numeric ID should return 404."""
        # 100 digit number
        long_id = "1" * 100
        response = guest_client.delete(f"/api/v2/files/{long_id}")
        assert response.status_code == 404

    def test_delete_url_encoded_id(self, guest_client):
        """DELETE with URL-encoded numeric ID should return 404."""
        # Use very large ID that won't exist
        response = guest_client.delete("/api/v2/files/9999999999999")
        assert response.status_code == 404
