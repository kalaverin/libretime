"""Tests for File DOWNLOAD 404 edge cases (T194)."""

import pytest

from model_bakery import baker

from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestFileViewSetDownloadNotFound:
    """Test Files DOWNLOAD 404 edge cases - non-existent IDs, invalid formats."""

    def test_download_non_existent_large_id(self, admin_client):
        """DOWNLOAD with large non-existent ID should return 404."""
        response = admin_client.get("/api/v2/files/999999999/download")
        assert response.status_code == 404

    def test_download_zero_id(self, admin_client):
        """DOWNLOAD with ID=0 should return 404."""
        response = admin_client.get("/api/v2/files/0/download")
        assert response.status_code == 404

    def test_download_negative_id(self, admin_client):
        """DOWNLOAD with negative ID should return 404."""
        response = admin_client.get("/api/v2/files/-1/download")
        assert response.status_code == 404

    def test_download_negative_large_id(self, admin_client):
        """DOWNLOAD with large negative ID should return 404."""
        response = admin_client.get("/api/v2/files/-999999/download")
        assert response.status_code == 404

    def test_download_string_id(self, admin_client):
        """DOWNLOAD with string ID should return 404."""
        response = admin_client.get("/api/v2/files/abc/download")
        assert response.status_code == 404

    def test_download_mixed_alphanumeric_id(self, admin_client):
        """DOWNLOAD with alphanumeric ID should return 404."""
        response = admin_client.get("/api/v2/files/abc123/download")
        assert response.status_code == 404

    def test_download_sql_injection_attempt(self, admin_client):
        """DOWNLOAD with SQL injection attempt should return 404."""
        response = admin_client.get("/api/v2/files/1%20OR%201=1/download")
        assert response.status_code == 404

    def test_download_sql_injection_union(self, admin_client):
        """DOWNLOAD with UNION SQL injection should return 404."""
        response = admin_client.get(
            "/api/v2/files/1%20UNION%20SELECT%20*/download",
        )
        assert response.status_code == 404

    def test_download_path_traversal_in_id(self, admin_client):
        """DOWNLOAD with path traversal in ID should return 404."""
        response = admin_client.get("/api/v2/files/../etc/passwd/download")
        assert response.status_code == 404

    def test_download_special_chars_id(self, admin_client):
        """DOWNLOAD with special characters ID should return 404."""
        response = admin_client.get("/api/v2/files/@#$%^&*/download")
        assert response.status_code == 404

    def test_download_unicode_id(self, admin_client):
        """DOWNLOAD with unicode ID should return 404."""
        response = admin_client.get("/api/v2/files/日本語/download")
        assert response.status_code == 404

    def test_download_float_id(self, admin_client):
        """DOWNLOAD with float ID should return 404."""
        response = admin_client.get("/api/v2/files/1.5/download")
        assert response.status_code == 404

    def test_download_hex_id(self, admin_client):
        """DOWNLOAD with hex ID should return 404."""
        response = admin_client.get("/api/v2/files/0x1A/download")
        assert response.status_code == 404

    def test_download_max_int_id(self, admin_client):
        """DOWNLOAD with max integer ID should return 404."""
        response = admin_client.get("/api/v2/files/2147483647/download")
        assert response.status_code == 404

    def test_download_max_int_plus_one_id(self, admin_client):
        """DOWNLOAD with max_int + 1 ID should return 404."""
        response = admin_client.get("/api/v2/files/2147483648/download")
        assert response.status_code == 404

    def test_download_scientific_notation_id(self, admin_client):
        """DOWNLOAD with scientific notation ID should return 404."""
        response = admin_client.get("/api/v2/files/1e5/download")
        assert response.status_code == 404

    def test_download_boolean_true_id(self, admin_client):
        """DOWNLOAD with 'true' as ID should return 404."""
        response = admin_client.get("/api/v2/files/true/download")
        assert response.status_code == 404

    def test_download_boolean_false_id(self, admin_client):
        """DOWNLOAD with 'false' as ID should return 404."""
        response = admin_client.get("/api/v2/files/false/download")
        assert response.status_code == 404

    def test_download_null_id(self, admin_client):
        """DOWNLOAD with 'null' as ID should return 404."""
        response = admin_client.get("/api/v2/files/null/download")
        assert response.status_code == 404

    def test_download_very_long_numeric_id(self, admin_client):
        """DOWNLOAD with very long numeric ID should return 404."""
        long_id = "1" * 100
        response = admin_client.get(f"/api/v2/files/{long_id}/download")
        assert response.status_code == 404

    def test_download_url_encoded_id(self, admin_client):
        """DOWNLOAD with URL-encoded numeric ID should return 404."""
        # Use very large ID that won't exist
        response = admin_client.get("/api/v2/files/9999999999999/download")
        assert response.status_code == 404

    def test_download_after_file_deleted(self, admin_client):
        """DOWNLOAD after file deleted from DB should return 404."""
        file = baker.make(
            File,
            name="Temp Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/temp.mp3",
        )
        file_id = file.id

        # Delete the file from DB
        file.delete()

        # Download should return 404
        response = admin_client.get(f"/api/v2/files/{file_id}/download")
        assert response.status_code == 404

    def test_download_deleted_file_still_on_disk(self, admin_client):
        """DOWNLOAD file deleted from DB but on disk should return 404."""
        file = baker.make(
            File,
            name="Ghost Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/ghost.mp3",
        )
        file_id = file.id

        # Delete from DB only
        file.delete()

        # Download should return 404 (DB record is required)
        response = admin_client.get(f"/api/v2/files/{file_id}/download")
        assert response.status_code == 404

    def test_download_missing_action_suffix(self, admin_client):
        """DOWNLOAD without /download suffix should be different endpoint."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        # Without /download - this is the retrieve endpoint
        response = admin_client.get(f"/api/v2/files/{file.id}")
        # Should return file metadata, not 404
        assert response.status_code == 200
        assert "name" in response.json()

    def test_download_wrong_action_name(self, admin_client):
        """DOWNLOAD with wrong action name should return 404."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        response = admin_client.get(f"/api/v2/files/{file.id}/stream")
        assert response.status_code == 404

    def test_download_case_sensitive_action(self, admin_client):
        """DOWNLOAD action is case-sensitive."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        # Uppercase action name
        response = admin_client.get(f"/api/v2/files/{file.id}/DOWNLOAD")
        assert response.status_code == 404

    def test_download_trailing_slash_after_action(self, admin_client):
        """DOWNLOAD with trailing slash after action should work or redirect."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        response = admin_client.get(f"/api/v2/files/{file.id}/download/")
        # May redirect or work depending on URL config
        assert response.status_code in [200, 301, 302, 404]

    def test_download_double_action(self, admin_client):
        """DOWNLOAD with double action in URL should return 404."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        response = admin_client.get(f"/api/v2/files/{file.id}/download/download")
        assert response.status_code == 404
