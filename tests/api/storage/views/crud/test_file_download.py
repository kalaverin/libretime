"""Tests for File DOWNLOAD action (T193)."""

import pytest

from model_bakery import baker

from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestFileViewSetDownload:
    """Test Files DOWNLOAD action - GET /api/v2/files/{id}/download."""

    def test_download_success(self, api_client):
        """DOWNLOAD existing file should return 200 with X-Accel-Redirect."""
        file = baker.make(
            File,
            name="Downloadable Track",
            mime="audio/mpeg",
            size=10_000_000,
            accessed=0,
            filepath="audio/test_file.mp3",
        )
        response = api_client.get(f"/api/v2/files/{file.id}/download")

        assert response.status_code == 200
        assert "X-Accel-Redirect" in response

    def test_download_x_accel_redirect_header_format(self, api_client):
        """X-Accel-Redirect should point to /api/_media/{filepath}."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/library/song.mp3",
        )
        response = api_client.get(f"/api/v2/files/{file.id}/download")

        redirect = response["X-Accel-Redirect"]
        assert redirect.startswith("/api/_media/")
        assert "audio/library/song.mp3" in redirect

    def test_download_not_found(self, api_client):
        """DOWNLOAD non-existent file should return 404."""
        response = api_client.get("/api/v2/files/999999/download")
        assert response.status_code == 404

    def test_download_no_auth_returns_403(self, client):
        """DOWNLOAD should return 403 without authentication."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        response = client.get(f"/api/v2/files/{file.id}/download")
        assert response.status_code == 403

    def test_download_zero_id(self, api_client):
        """DOWNLOAD with ID=0 should return 404."""
        response = api_client.get("/api/v2/files/0/download")
        assert response.status_code == 404

    def test_download_negative_id(self, api_client):
        """DOWNLOAD with negative ID should return 404."""
        response = api_client.get("/api/v2/files/-1/download")
        assert response.status_code == 404

    def test_download_invalid_id_format(self, api_client):
        """DOWNLOAD with invalid ID format should return 404."""
        response = api_client.get("/api/v2/files/abc/download")
        assert response.status_code == 404

    def test_download_unicode_filepath(self, api_client):
        """DOWNLOAD with unicode filepath should handle URL encoding."""
        file = baker.make(
            File,
            name="Unicode Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/日本語/曲.mp3",
        )
        response = api_client.get(f"/api/v2/files/{file.id}/download")

        assert response.status_code == 200
        # X-Accel-Redirect should be USASCII encoded
        redirect = response["X-Accel-Redirect"]
        assert "/api/_media/" in redirect

    def test_download_special_chars_filepath(self, api_client):
        """DOWNLOAD with special chars in filepath should handle encoding."""
        file = baker.make(
            File,
            name="Special Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/special & chars/file.mp3",
        )
        response = api_client.get(f"/api/v2/files/{file.id}/download")

        assert response.status_code == 200
        # filepath_to_uri should encode special chars
        redirect = response["X-Accel-Redirect"]
        assert "/api/_media/" in redirect

    def test_download_long_filepath(self, api_client):
        """DOWNLOAD with very long filepath should work."""
        long_path = (
            "audio/"
            + "/".join(["dir" + str(i) for i in range(20)])
            + "/file.mp3"
        )
        file = baker.make(
            File,
            name="Deep Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath=long_path,
        )
        response = api_client.get(f"/api/v2/files/{file.id}/download")

        assert response.status_code == 200
        assert len(response["X-Accel-Redirect"]) > len(long_path)

    @pytest.mark.xfail(
        reason="BUG T317: download crashes with TypeError when filepath is None",
    )
    def test_download_no_filepath(self, api_client):
        """DOWNLOAD file without filepath should handle gracefully.

        BUG T317: os.path.join crashes with TypeError when filepath is None.
        Should return 400 or handle gracefully instead of 500.
        """
        file = baker.make(
            File,
            name="No Path Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath=None,
        )
        response = api_client.get(f"/api/v2/files/{file.id}/download")

        # Should handle None filepath gracefully
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            assert "X-Accel-Redirect" in response

    def test_download_empty_filepath(self, api_client):
        """DOWNLOAD file with empty filepath."""
        file = baker.make(
            File,
            name="Empty Path Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="",
        )
        response = api_client.get(f"/api/v2/files/{file.id}/download")

        assert response.status_code == 200
        redirect = response["X-Accel-Redirect"]
        assert redirect == "/api/_media/"

    def test_download_path_traversal_attempt(self, api_client):
        """DOWNLOAD with path traversal in filepath should handle it."""
        file = baker.make(
            File,
            name="Malicious Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="../../../etc/passwd",
        )
        response = api_client.get(f"/api/v2/files/{file.id}/download")

        # Returns 200 but the path should be handled carefully
        # filepath_to_uri doesn't prevent path traversal
        assert response.status_code == 200
        redirect = response["X-Accel-Redirect"]
        assert "/api/_media/" in redirect

    def test_download_response_has_no_body(self, api_client):
        """DOWNLOAD response should have empty body (nginx serves file)."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        response = api_client.get(f"/api/v2/files/{file.id}/download")

        assert response.status_code == 200
        # Response body should be empty - nginx handles the actual file serving
        assert response.content == b""

    def test_download_post_not_allowed(self, api_client):
        """POST on download action should return 405."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        response = api_client.post(f"/api/v2/files/{file.id}/download")
        assert response.status_code == 405

    def test_download_put_not_allowed(self, api_client):
        """PUT on download action should return 405."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        response = api_client.put(f"/api/v2/files/{file.id}/download")
        assert response.status_code == 405

    def test_download_patch_not_allowed(self, api_client):
        """PATCH on download action should return 405."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        response = api_client.patch(f"/api/v2/files/{file.id}/download")
        assert response.status_code == 405

    def test_download_delete_not_allowed(self, api_client):
        """DELETE on download action should return 405."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        response = api_client.delete(f"/api/v2/files/{file.id}/download")
        assert response.status_code == 405

    @pytest.mark.xfail(
        reason="URL routing: /download/ returns 404, should redirect or work",
    )
    def test_download_url_with_trailing_slash(self, api_client):
        """DOWNLOAD with trailing slash in URL should work or redirect."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        response = api_client.get(f"/api/v2/files/{file.id}/download/")
        # Might be 301 redirect or 200 depending on URL config
        assert response.status_code in [200, 301, 302]
