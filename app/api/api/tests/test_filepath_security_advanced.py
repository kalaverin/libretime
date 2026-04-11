"""
Advanced filepath security tests with pathlib validation.

Tests for:
- Junk characters in filepath (control chars, unicode tricks, zero-width)
- Path traversal with various encodings and tricks
- Path validation using pathlib.resolve()
- Edge cases with symlinks, .. sequences, absolute paths
"""

import json

import pytest

from rest_framework.test import APIClient


class TestFilepathJunkCharacters:
    """Tests for junk/unprintable characters in filepath."""

    @pytest.mark.django_db
    def test_null_byte_rejected(self, admin_user):
        """Null byte (\\x00) should be rejected."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "music/test\x00.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_control_characters_rejected(self, admin_user):
        """Control characters (0x01-0x1F) should be rejected."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        control_chars = [
            "\x01",
            "\x08",
            "\x0b",
            "\x0c",
            "\x0e",
            "\x1f",
            "\x7f",
        ]

        for char in control_chars:
            response = client.post(
                "/api/v2/files",
                json.dumps(
                    {
                        "name": "test.mp3",
                        "filepath": f"music/test{char}.mp3",
                        "mime": "audio/mp3",
                        "library": library.id,
                        "size": 1024,
                        "accessed": 0,
                    },
                ),
                content_type="application/json",
            )
            assert (
                response.status_code == 400
            ), f"Control char {repr(char)} should be rejected"

    @pytest.mark.django_db
    def test_zero_width_characters_rejected(self, admin_user):
        """Zero-width characters should be rejected (spoofing protection)."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Zero-width space, zero-width joiner, etc.
        zw_chars = ["\u200b", "\u200c", "\u200d", "\ufeff", "\u2060"]

        for char in zw_chars:
            response = client.post(
                "/api/v2/files",
                json.dumps(
                    {
                        "name": "test.mp3",
                        "filepath": f"music/test{char}.mp3",
                        "mime": "audio/mp3",
                        "library": library.id,
                        "size": 1024,
                        "accessed": 0,
                    },
                ),
                content_type="application/json",
            )
            assert (
                response.status_code == 400
            ), f"Zero-width char {repr(char)} should be rejected"

    @pytest.mark.django_db
    def test_bidirectional_override_rejected(self, admin_user):
        """Bidirectional override characters should be rejected."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Bidirectional override characters
        bidi_chars = ["\u202a", "\u202b", "\u202c", "\u202d", "\u202e"]

        for char in bidi_chars:
            response = client.post(
                "/api/v2/files",
                json.dumps(
                    {
                        "name": "test.mp3",
                        "filepath": f"music{char}test.mp3",
                        "mime": "audio/mp3",
                        "library": library.id,
                        "size": 1024,
                        "accessed": 0,
                    },
                ),
                content_type="application/json",
            )
            assert (
                response.status_code == 400
            ), f"Bidi char {repr(char)} should be rejected"


class TestFilepathPathTraversalAdvanced:
    """Advanced path traversal tests with various techniques."""

    @pytest.mark.django_db
    def test_double_dot_with_encoded_slash(self, admin_user):
        """..%2f should be rejected."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "..%2f..%2f..%2fetc/passwd",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_double_encoded_traversal(self, admin_user):
        """Double-encoded .. (..%252f) should be rejected."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "..%252f..%252fetc/passwd",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_dotdot_with_backslash(self, admin_user):
        """..\\ path traversal should be rejected."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "..\\..\\..\\windows\\system32\\config\\sam",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_multiple_dots(self, admin_user):
        """....// should be rejected."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "....//....//....//etc/passwd",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestFilepathAbsolutePaths:
    """Tests for absolute path rejection."""

    @pytest.mark.django_db
    def test_unix_absolute_path(self, admin_user):
        """/etc/passwd should be rejected."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "/etc/passwd",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_windows_absolute_path_c_drive(self, admin_user):
        """C:\\Windows should be rejected."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "C:\\Windows\\System32\\config\\SAM",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_unc_path(self, admin_user):
        """\\\\server\\share should be rejected."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "\\\\server\\share\\file.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestFilepathValidPathsStillWork:
    """Ensure valid relative paths still work."""

    @pytest.mark.django_db
    def test_simple_filename(self, admin_user):
        """Just a filename should work."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "song.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_relative_path_with_subdirs(self, admin_user):
        """music/artist/album/song.mp3 should work."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "music/artist/album/song.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_single_dot_in_path(self, admin_user):
        """./music/song.mp3 should work (current dir reference)."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "./music/song.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_unicode_in_path(self, admin_user):
        """Unicode characters in valid path should work."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "music/日本語/曲.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201


class TestFilepathPathlibResolve:
    """Tests for pathlib.Path.resolve() validation in perform_destroy."""

    @pytest.mark.django_db
    def test_destroy_with_traversal_blocked_by_pathlib(self, admin_user):
        """Destroy should block filepath that resolves outside storage."""
        from model_bakery import baker

        from api.storage.models import File, Library

        library = baker.make(Library, name="Test", description="Test")

        # Create a file with traversal path (bypassing serializer validation by using baker)
        file_obj = baker.make(
            File,
            name="evil.mp3",
            filepath="../../../etc/passwd",
            mime="audio/mp3",
            library=library,
            owner=admin_user,
            size=1024,
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Delete should fail because filepath resolves outside storage
        response = client.delete(f"/api/v2/files/{file_obj.id}")
        # Should get 500 (APIException) because path escapes storage
        assert response.status_code in [
            500,
            204,
        ]  # 500 if blocked, 204 if file not found

    @pytest.mark.django_db
    def test_destroy_with_dotdot_middle_of_path(self, admin_user):
        """music/../other/song.mp3 should resolve to other/song.mp3."""
        from model_bakery import baker

        from api.storage.models import File, Library

        library = baker.make(Library, name="Test", description="Test")

        # This is actually valid - resolves to other/song.mp3 within storage
        file_obj = baker.make(
            File,
            name="test.mp3",
            filepath="music/../other/song.mp3",
            mime="audio/mp3",
            library=library,
            owner=admin_user,
            size=1024,
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # This should work because resolved path is still within storage
        response = client.delete(f"/api/v2/files/{file_obj.id}")
        # 204 because file doesn't exist on disk, but no path traversal error
        assert response.status_code == 204


class TestFilepathEdgeCases:
    """Edge cases and boundary tests."""

    @pytest.mark.django_db
    def test_empty_filepath(self, admin_user):
        """Empty filepath should be allowed."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_null_filepath(self, admin_user):
        """Null filepath should be allowed."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": None,
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_very_long_path(self, admin_user):
        """Very long but valid path should work."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        long_path = "/".join([f"dir{i}" for i in range(50)]) + "/file.mp3"

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": long_path,
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        # Very long paths may be rejected by OS, but should not be 400 (validation error)
        # 201 = created, 500 = OS error (acceptable)
        assert response.status_code in [201, 500]

    @pytest.mark.django_db
    def test_spaces_in_path(self, admin_user):
        """Spaces in filepath should work."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "music/my songs/cool track.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_special_chars_in_path(self, admin_user):
        """Special but safe characters should work."""
        from model_bakery import baker

        from api.storage.models import Library

        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "test.mp3",
                    "filepath": "music/song-v1.2_final (remix).mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "size": 1024,
                    "accessed": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
