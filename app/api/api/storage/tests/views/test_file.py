import os

from unittest.mock import patch

from django.conf import settings
from model_bakery import baker
from rest_framework.test import APITestCase

from api._fixtures import AUDIO_FILENAME
from api.storage.models import File


class TestFileViewSet(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.token = settings.CONFIG.general.api_key

    def test_download_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.token}")
        file_id = "1"
        response = self.client.get(f"/api/v2/files/{file_id}/download")
        self.assertEqual(response.status_code, 404)

    def test_download(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.token}")
        file: File = baker.make(
            "storage.File",
            mime="audio/mp3",
            filepath=AUDIO_FILENAME,
        )
        response = self.client.get(f"/api/v2/files/{file.id}/download")
        self.assertEqual(response.status_code, 200)

    def test_destroy_not_allowed(self):
        """File deletion is not allowed - returns 409 Conflict."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.token}")
        file: File = baker.make(
            "storage.File",
            mime="audio/mp3",
            filepath=AUDIO_FILENAME,
        )

        response = self.client.delete(f"/api/v2/files/{file.id}")

        # File deletion is not allowed for anyone (409 Conflict)
        self.assertEqual(response.status_code, 409)
        # Verify file was NOT deleted
        self.assertTrue(File.objects.filter(id=file.id).exists())

    def test_destroy_no_file_still_not_allowed(self):
        """File deletion is not allowed even if file doesn't exist on disk."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.token}")
        file = baker.make(
            "storage.File",
            mime="audio/mp3",
            filepath="invalid.mp3",
        )
        response = self.client.delete(f"/api/v2/files/{file.id}")
        # File deletion is not allowed (409 Conflict)
        self.assertEqual(response.status_code, 409)

    def test_destroy_invalid_file(self):
        """Deleting non-existent file returns 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.token}")
        file_id = "99999"  # Non-existent ID
        response = self.client.delete(f"/api/v2/files/{file_id}")
        self.assertEqual(response.status_code, 404)

    def test_filters(self):
        file = baker.make(
            "storage.File",
            mime="audio/mp3",
            filepath=AUDIO_FILENAME,
            genre="Soul",
            md5="5a11ffe0e6c6d70fcdbad1b734be6482",
        )
        baker.make(
            "storage.File",
            mime="audio/mp3",
            filepath=AUDIO_FILENAME,
            genre="R&B",
            md5="5a11ffe0e6c6d70fcdbad1b734be6483",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.token}")

        path = "/api/v2/files"
        results = self.client.get(path).json()
        self.assertEqual(len(results), 2)

        path = f"/api/v2/files?md5={file.md5}"
        results = self.client.get(path).json()
        self.assertEqual(len(results), 1)

        path = "/api/v2/files?genre=Soul"
        results = self.client.get(path).json()
        self.assertEqual(len(results), 1)

        path = "/api/v2/files?genre=R%26B"
        results = self.client.get(path).json()
        self.assertEqual(len(results), 1)
