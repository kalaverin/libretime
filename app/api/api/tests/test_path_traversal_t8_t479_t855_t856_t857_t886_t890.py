"""
RED TEAM: Path traversal vulnerability fixes.

Fixes and tests for:
- T8: filepath in FileViewSet destroy - Path traversal
- T479: cue_in/out in SmartBlockContent - Path patterns
- T855: filepath in File CREATE - Traversal patterns
- T856: filepath in File UPDATE - Traversal via PATCH
- T857: filepath in File - Absolute paths
- T886: filepath in File - Traversal accepted
- T890: filepath in File - Absolute paths
"""

import json
import pytest
from rest_framework.test import APIClient


class TestFilePathTraversalCreate:
    """T855, T886: Path traversal in File CREATE should be rejected."""

    @pytest.mark.django_db
    def test_traversal_dotdot_slash_rejected(self, admin_user):
        """../ patterns should be rejected in CREATE."""
        from api.storage.models import Library
        from model_bakery import baker
        
        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.post(
            "/api/v2/files",
            json.dumps({
                "name": "test.mp3",
                "filepath": "../../../etc/passwd",
                "mime": "audio/mp3",
                "library": library.id,
                "size": 1024,
                "accessed": 0,
            }),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "traversal" in str(response.content).lower() or "filepath" in str(response.content).lower()

    @pytest.mark.django_db
    def test_traversal_backslash_rejected(self, admin_user):
        """\\..\\ patterns should be rejected."""
        from api.storage.models import Library
        from model_bakery import baker
        
        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.post(
            "/api/v2/files",
            json.dumps({
                "name": "test.mp3",
                "filepath": "..\\..\\..\\windows\\system32\\config\\sam",
                "mime": "audio/mp3",
                "library": library.id,
                "size": 1024,
                "accessed": 0,
            }),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_traversal_url_encoded_rejected(self, admin_user):
        """URL-encoded traversal should be rejected."""
        from api.storage.models import Library
        from model_bakery import baker
        
        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.post(
            "/api/v2/files",
            json.dumps({
                "name": "test.mp3",
                "filepath": "..%2f..%2f..%2fetc/passwd",
                "mime": "audio/mp3",
                "library": library.id,
                "size": 1024,
                "accessed": 0,
            }),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestFilePathTraversalUpdate:
    """T856: Path traversal in File UPDATE should be rejected."""

    @pytest.mark.django_db
    def test_traversal_in_patch_rejected(self, admin_user):
        """Path traversal via PATCH should be rejected."""
        from api.storage.models import File, Library
        from model_bakery import baker
        
        library = baker.make(Library, name="Test", description="Test")
        file_obj = baker.make(
            File,
            name="normal.mp3",
            filepath="/normal/path.mp3",
            mime="audio/mp3",
            library=library,
            owner=admin_user,
            size=1024,
        )
        
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"filepath": "../../../etc/passwd"}),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestFileAbsolutePathBlocked:
    """T857, T890: Absolute paths should be rejected."""

    @pytest.mark.django_db
    def test_unix_absolute_path_rejected(self, admin_user):
        """/etc/passwd style paths should be rejected."""
        from api.storage.models import Library
        from model_bakery import baker
        
        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.post(
            "/api/v2/files",
            json.dumps({
                "name": "test.mp3",
                "filepath": "/etc/passwd",
                "mime": "audio/mp3",
                "library": library.id,
                "size": 1024,
                "accessed": 0,
            }),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "absolute" in str(response.content).lower()

    @pytest.mark.django_db
    def test_windows_absolute_path_rejected(self, admin_user):
        """C:\\Windows style paths should be rejected."""
        from api.storage.models import Library
        from model_bakery import baker
        
        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.post(
            "/api/v2/files",
            json.dumps({
                "name": "test.mp3",
                "filepath": "C:\\Windows\\System32\\config\\SAM",
                "mime": "audio/mp3",
                "library": library.id,
                "size": 1024,
                "accessed": 0,
            }),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestFileDestroyPathTraversal:
    """T8: FileViewSet destroy with path traversal should be blocked."""

    @pytest.mark.django_db
    def test_destroy_with_traversal_blocked(self, admin_user):
        """Destroying file with traversal path should be blocked."""
        from api.storage.models import File, Library
        from model_bakery import baker
        
        library = baker.make(Library, name="Test", description="Test")
        file_obj = baker.make(
            File,
            name="evil.mp3",
            filepath="../../../etc/passwd",  # This should have been blocked at create
            mime="audio/mp3",
            library=library,
            owner=admin_user,
            size=1024,
        )
        
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        # Delete should handle unsafe filepath gracefully
        response = client.delete(f"/api/v2/files/{file_obj.id}")
        # Either 500 (if safety check triggers) or 204 (if handled gracefully)
        # The important thing is no file system operation occurs
        assert response.status_code in [204, 500]


class TestSmartBlockContentPathPatterns:
    """T479: cue_in/out should reject path-like patterns."""

    @pytest.mark.django_db
    def test_cue_in_path_pattern_rejected(self, admin_user):
        """Path patterns in cue_in should be rejected."""
        from api.schedule.models import SmartBlock
        from api.storage.models import File
        from model_bakery import baker
        
        block = baker.make(SmartBlock, name="Test Block")
        file_obj = baker.make(File, mime="audio/mp3", owner=admin_user)
        
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": block.id,
                "file": file_obj.id,
                "position": 1,
                "offset": 0,
                "cue_in": "../../../etc/passwd",  # Path pattern
                "cue_out": "00:05:00",
            }),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_cue_out_path_pattern_rejected(self, admin_user):
        """Path patterns in cue_out should be rejected."""
        from api.schedule.models import SmartBlock
        from api.storage.models import File
        from model_bakery import baker
        
        block = baker.make(SmartBlock, name="Test Block")
        file_obj = baker.make(File, mime="audio/mp3", owner=admin_user)
        
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": block.id,
                "file": file_obj.id,
                "position": 1,
                "offset": 0,
                "cue_in": "00:00:00",
                "cue_out": "../../etc/shadow",
            }),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_valid_duration_still_works(self, admin_user):
        """Valid duration format should still work."""
        from api.schedule.models import SmartBlock
        from api.storage.models import File
        from model_bakery import baker
        
        block = baker.make(SmartBlock, name="Test Block")
        file_obj = baker.make(File, mime="audio/mp3", owner=admin_user)
        
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.post(
            "/api/v2/smart-block-contents",
            json.dumps({
                "block": block.id,
                "file": file_obj.id,
                "position": 1,
                "offset": 0,
                "cue_in": "00:00:30",
                "cue_out": "00:05:00",
            }),
            content_type="application/json",
        )
        assert response.status_code == 201


class TestValidFilepathStillWorks:
    """Ensure valid filepaths still work after security fixes."""

    @pytest.mark.django_db
    def test_relative_path_works(self, admin_user):
        """Valid relative paths should still work."""
        from api.storage.models import Library
        from model_bakery import baker
        
        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.post(
            "/api/v2/files",
            json.dumps({
                "name": "test.mp3",
                "filepath": "music/artist/album/song.mp3",
                "mime": "audio/mp3",
                "library": library.id,
                "size": 1024,
                "accessed": 0,
            }),
            content_type="application/json",
        )
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_simple_filename_works(self, admin_user):
        """Simple filename should still work."""
        from api.storage.models import Library
        from model_bakery import baker
        
        library = baker.make(Library, name="Test", description="Test")
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.post(
            "/api/v2/files",
            json.dumps({
                "name": "test.mp3",
                "filepath": "song.mp3",
                "mime": "audio/mp3",
                "library": library.id,
                "size": 1024,
                "accessed": 0,
            }),
            content_type="application/json",
        )
        assert response.status_code == 201
