"""Tests for File DELETE endpoint (T191)."""

from unittest.mock import patch

import pytest

from model_bakery import baker

from api.schedule.models import Schedule
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestFileViewSetDelete:
    """Test Files DELETE endpoint - DELETE /api/v2/files/{id}."""

    def test_delete_file_success_returns_204(self, api_client):
        """DELETE existing file should return 204 (file removed from disk)."""
        file = baker.make(
            File,
            name="Track to Delete",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        with patch("api.storage.views.file.os.path.isfile", return_value=True):
            with patch("api.storage.views.file.remove") as remove_mock:
                response = api_client.delete(f"/api/v2/files/{file.id}")

        assert response.status_code == 204
        remove_mock.assert_called_once()

    @pytest.mark.xfail(
        reason="BUG T316: perform_destroy doesn't call instance.delete()",
    )
    def test_delete_file_removes_from_db(self, api_client):
        """DELETE should remove file from database.

        BUG T316: File is removed from disk but remains in DB.
        """
        file = baker.make(
            File,
            name="Track to Delete",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        with patch("api.storage.views.file.os.path.isfile", return_value=True):
            with patch("api.storage.views.file.remove"):
                response = api_client.delete(f"/api/v2/files/{file.id}")

        assert response.status_code == 204
        assert not File.objects.filter(id=file.id).exists()

    def test_delete_file_not_found(self, api_client):
        """DELETE non-existent file should return 404."""
        response = api_client.delete("/api/v2/files/999999")
        assert response.status_code == 404

    def test_delete_file_no_auth_returns_403(self, client):
        """DELETE should return 403 without authentication."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        response = client.delete(f"/api/v2/files/{file.id}")
        assert response.status_code == 403

    def test_delete_file_scheduled_future_returns_409(self, api_client):
        """DELETE file scheduled in future should return 409 Conflict."""
        file = baker.make(
            File,
            name="Scheduled Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/scheduled.mp3",
        )
        with patch.object(
            Schedule,
            "is_file_scheduled_in_the_future",
            return_value=True,
        ):
            response = api_client.delete(f"/api/v2/files/{file.id}")

        assert response.status_code == 409
        # File should still exist
        assert File.objects.filter(id=file.id).exists()

    def test_delete_file_no_filepath_logs_warning(self, api_client):
        """DELETE file without filepath should log warning and return 204."""
        file = baker.make(
            File,
            name="No Path Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath=None,
        )
        with patch("api.storage.views.file.logger") as logger_mock:
            response = api_client.delete(f"/api/v2/files/{file.id}")

        assert response.status_code == 204
        logger_mock.warning.assert_called_once()
        assert "does not have a filepath" in str(logger_mock.warning.call_args)

    def test_delete_file_not_on_disk_logs_warning(self, api_client):
        """DELETE file not existing on disk should log warning and return 204."""
        file = baker.make(
            File,
            name="Missing Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/missing.mp3",
        )
        with (
            patch(
                "api.storage.views.file.os.path.isfile",
                return_value=False,
            ),
            patch("api.storage.views.file.logger") as logger_mock,
        ):
            response = api_client.delete(f"/api/v2/files/{file.id}")

        assert response.status_code == 204
        logger_mock.warning.assert_called_once()
        assert "does not exist in storage" in str(
            logger_mock.warning.call_args,
        )

    @pytest.mark.xfail(
        reason="BUG T316: perform_destroy doesn't call instance.delete()",
    )
    def test_delete_file_removes_from_db(self, api_client):
        """DELETE should remove file from database.

        BUG T316: File is removed from disk but remains in DB.
        """
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        file_id = file.id

        with patch("api.storage.views.file.os.path.isfile", return_value=True):
            with patch("api.storage.views.file.remove"):
                api_client.delete(f"/api/v2/files/{file_id}")

        assert not File.objects.filter(id=file_id).exists()

    def test_delete_file_removes_from_storage(self, api_client):
        """DELETE should call remove on the file path."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/test_file.mp3",
        )

        with patch("api.storage.views.file.os.path.isfile", return_value=True):
            with patch("api.storage.views.file.remove") as remove_mock:
                api_client.delete(f"/api/v2/files/{file.id}")

        # Verify remove was called with correct path
        assert remove_mock.called
        call_args = remove_mock.call_args[0][0]
        assert "audio/test_file.mp3" in call_args

    def test_delete_file_invalid_id_format(self, api_client):
        """DELETE with invalid id format should return 404."""
        response = api_client.delete("/api/v2/files/invalid")
        assert response.status_code == 404

    def test_delete_file_negative_id(self, api_client):
        """DELETE with negative id should return 404."""
        response = api_client.delete("/api/v2/files/-1")
        assert response.status_code == 404

    def test_delete_file_zero_id(self, api_client):
        """DELETE with id=0 should return 404."""
        response = api_client.delete("/api/v2/files/0")
        assert response.status_code == 404

    def test_delete_file_os_error_raises_api_exception(self, api_client):
        """DELETE when os.remove raises OSError should return 500."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        with patch("api.storage.views.file.os.path.isfile", return_value=True):
            with patch(
                "api.storage.views.file.remove",
                side_effect=OSError("Permission denied"),
            ):
                response = api_client.delete(f"/api/v2/files/{file.id}")

        # Should return 500 due to APIException
        assert response.status_code == 500

    def test_delete_file_returns_empty_body(self, api_client):
        """DELETE should return empty body on success."""
        file = baker.make(
            File,
            name="Track",
            mime="audio/mpeg",
            size=1000,
            accessed=0,
            filepath="audio/file.mp3",
        )
        with patch("api.storage.views.file.os.path.isfile", return_value=True):
            with patch("api.storage.views.file.remove"):
                response = api_client.delete(f"/api/v2/files/{file.id}")

        assert response.status_code == 204
        assert response.content == b""
