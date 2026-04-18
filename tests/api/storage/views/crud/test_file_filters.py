"""Tests for File LIST filters (T187)."""

import pytest

from model_bakery import baker

from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestFileViewSetFilters:
    """Test Files LIST filters - GET /api/v2/files?md5=xxx&genre=xxx."""

    def setup_method(self):
        """Clean up files before each test."""
        File.objects.all().delete()

    def test_filter_by_md5_exact_match(self, guest_client):
        """Filter by md5 should return only matching file."""
        # Use full 32-char MD5 (max_length of field)
        target_file = baker.make(
            File,
            name="Target",
            mime="audio/mpeg",
            md5="abc123def45678901234567890123456",
        )
        other_file = baker.make(
            File,
            name="Other",
            mime="audio/mpeg",
            md5="xyz789uvw01234567890123456789012",
        )

        response = guest_client.get(
            "/api/v2/files?md5=abc123def45678901234567890123456",
        )
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]["id"] == target_file.id

    def test_filter_by_md5_no_match(self, guest_client):
        """Filter by non-existent md5 should return empty list."""
        baker.make(File, name="File", mime="audio/mpeg", md5="abc123")

        response = guest_client.get("/api/v2/files?md5=nonexistent")
        data = response.json()

        assert response.status_code == 200
        assert data == []

    def test_filter_by_md5_partial_not_supported(self, guest_client):
        """Partial md5 match should not work (exact match only)."""
        baker.make(File, name="File", mime="audio/mpeg", md5="abc123def456")

        response = guest_client.get("/api/v2/files?md5=abc123")
        data = response.json()

        # Should not match partial
        assert len(data) == 0

    def test_filter_by_genre_exact_match(self, guest_client):
        """Filter by genre should return only matching files."""
        rock_file1 = baker.make(
            File,
            name="Rock 1",
            mime="audio/mpeg",
            genre="Rock",
        )
        rock_file2 = baker.make(
            File,
            name="Rock 2",
            mime="audio/mpeg",
            genre="Rock",
        )
        jazz_file = baker.make(
            File,
            name="Jazz",
            mime="audio/mpeg",
            genre="Jazz",
        )

        response = guest_client.get("/api/v2/files?genre=Rock")
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 2
        genres = {item["genre"] for item in data}
        assert genres == {"Rock"}

    def test_filter_by_genre_no_match(self, guest_client):
        """Filter by non-existent genre should return empty list."""
        baker.make(File, name="File", mime="audio/mpeg", genre="Rock")

        response = guest_client.get("/api/v2/files?genre=NonExistent")
        data = response.json()

        assert response.status_code == 200
        assert data == []

    def test_filter_by_genre_case_sensitive(self, guest_client):
        """Genre filter should be case-sensitive."""
        baker.make(File, name="File", mime="audio/mpeg", genre="Rock")

        response = guest_client.get("/api/v2/files?genre=rock")
        data = response.json()

        # Case-sensitive: 'rock' != 'Rock'
        assert len(data) == 0

    def test_filter_by_genre_with_special_chars(self, guest_client):
        """Filter by genre with special characters (R&B)."""
        rnb_file = baker.make(
            File,
            name="R&B Song",
            mime="audio/mpeg",
            genre="R&B",
        )
        rock_file = baker.make(
            File,
            name="Rock Song",
            mime="audio/mpeg",
            genre="Rock",
        )

        response = guest_client.get("/api/v2/files?genre=R%26B")  # URL encoded
        data = response.json()

        assert len(data) == 1
        assert data[0]["genre"] == "R&B"

    def test_filter_by_genre_null_excluded(self, guest_client):
        """Files with null genre should be excluded when filtering."""
        null_genre_file = baker.make(
            File,
            name="No Genre",
            mime="audio/mpeg",
            genre=None,
        )
        rock_file = baker.make(
            File,
            name="Rock",
            mime="audio/mpeg",
            genre="Rock",
        )

        response = guest_client.get("/api/v2/files?genre=Rock")
        data = response.json()

        assert len(data) == 1
        assert data[0]["id"] == rock_file.id

    def test_filter_by_genre_empty_string(self, guest_client):
        """Filter by empty genre should match empty strings."""
        # Create files - this test may see files from other tests due to transaction isolation
        empty_genre_file = baker.make(
            File,
            name="Empty Genre Test",
            mime="audio/mpeg",
            genre="",
        )
        rock_file = baker.make(
            File,
            name="Rock Test",
            mime="audio/mpeg",
            genre="Rock",
        )

        response = guest_client.get("/api/v2/files?genre=")
        data = response.json()

        # Empty string filter - should find at least our file
        empty_genres = [item for item in data if item["genre"] == ""]
        assert len(empty_genres) >= 1
        assert any(item["name"] == "Empty Genre Test" for item in empty_genres)

    def test_filter_combined_md5_and_genre(self, guest_client):
        """Combined filters should work with AND logic."""
        target = baker.make(
            File,
            name="Target",
            mime="audio/mpeg",
            md5="abc123",
            genre="Rock",
        )
        same_md5 = baker.make(
            File,
            name="Same MD5",
            mime="audio/mpeg",
            md5="abc123",
            genre="Jazz",
        )
        same_genre = baker.make(
            File,
            name="Same Genre",
            mime="audio/mpeg",
            md5="xyz789",
            genre="Rock",
        )

        response = guest_client.get("/api/v2/files?md5=abc123&genre=Rock")
        data = response.json()

        assert len(data) == 1
        assert data[0]["id"] == target.id

    def test_filter_combined_no_match(self, guest_client):
        """Combined filters with no intersection should return empty."""
        baker.make(
            File,
            name="File",
            mime="audio/mpeg",
            md5="abc123",
            genre="Rock",
        )

        response = guest_client.get("/api/v2/files?md5=abc123&genre=Jazz")
        data = response.json()

        assert len(data) == 0

    def test_filter_invalid_param_ignored(self, guest_client):
        """Invalid filter parameters should be ignored."""
        file = baker.make(File, name="File", mime="audio/mpeg")

        response = guest_client.get("/api/v2/files?invalid_param=value")
        data = response.json()

        # Should return all files, ignoring invalid filter
        assert len(data) >= 1

    def test_filter_with_unicode_genre(self, guest_client):
        """Filter by genre with unicode characters."""
        unicode_file = baker.make(
            File,
            name="Unicode",
            mime="audio/mpeg",
            genre="日本語ジャズ",
        )

        response = guest_client.get("/api/v2/files?genre=日本語ジャズ")
        data = response.json()

        assert len(data) == 1
        assert data[0]["genre"] == "日本語ジャズ"

    def test_filter_by_md5_case_sensitive(self, guest_client):
        """MD5 filter should be case-sensitive (hex strings)."""
        baker.make(File, name="File", mime="audio/mpeg", md5="abcdef123456")

        response = guest_client.get("/api/v2/files?md5=ABCDEF123456")
        data = response.json()

        # Case-sensitive: uppercase != lowercase
        assert len(data) == 0

    def test_filter_without_params_returns_all(self, guest_client):
        """Request without filters should return all files."""
        for i in range(5):
            baker.make(File, name=f"File {i}", mime="audio/mpeg")

        response = guest_client.get("/api/v2/files")
        data = response.json()

        assert len(data) == 5
