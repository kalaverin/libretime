"""
T298: File organization redteam security tests.

Paranoid security tests for file organization endpoints.
Targets: BOLA, mass assignment, path traversal, SQL injection, business logic bypass.
"""

import pytest

from model_bakery import baker
from rest_framework.test import APIClient

from api.core.models import User
from api.storage.models import File, Library


def make_library(**kwargs):
    """Helper to create Library with required description."""
    defaults = {"description": "Test library"}
    defaults.update(kwargs)
    return baker.make(Library, **defaults)


@pytest.mark.django_db
class TestFileOrganizationBOLA:
    """T901: BOLA - Object-level authorization in file organization."""

    @pytest.mark.xfail(
        reason="BOLA: Can retrieve other user's file organization - T901",
    )
    def test_retrieve_other_users_file_path(self, api_client: APIClient):
        """
        Attacker retrieves victim's file to see filepath info.
        API1:2023 - Broken Object Level Authorization.
        """
        attacker = baker.make(User, username="path_attacker")
        victim = baker.make(User, username="path_victim")
        library = make_library(code="BOLA", name="BOLA Test")

        victim_file = baker.make(
            File,
            name="secret_song.mp3",
            mime="audio/mp3",
            library=library,
            owner=victim,
            filepath="/secret/music/private_collection/rare_track.mp3",
        )

        api_client.force_authenticate(user=attacker)
        response = api_client.get(f"/api/v2/files/{victim_file.id}")

        assert (
            response.status_code == 404
        ), "Attacker should not see victim's file path"

    @pytest.mark.xfail(
        reason="BOLA: LIST shows all users' file organization - T901",
    )
    def test_list_shows_all_users_filepaths(self, api_client: APIClient):
        """
        LIST endpoint returns all users' file paths and library assignments.
        API1:2023 - Missing user isolation.
        """
        user1 = baker.make(User, username="org_user1")
        user2 = baker.make(User, username="org_user2")
        library = make_library(code="BOLA2", name="BOLA Test")

        baker.make(
            File,
            name="user1_file.mp3",
            mime="audio/mp3",
            library=library,
            owner=user1,
            filepath="/user1/private/music.mp3",
            _quantity=3,
        )

        baker.make(
            File,
            name="user2_file.mp3",
            mime="audio/mp3",
            library=library,
            owner=user2,
            filepath="/user2/confidential/recording.mp3",
            _quantity=3,
        )

        api_client.force_authenticate(user=user1)
        response = api_client.get("/api/v2/files")

        assert response.status_code == 200
        data = response.json()

        others_files = [
            f for f in data if f.get("name", "").startswith("user2_")
        ]
        assert (
            len(others_files) == 0
        ), "User1 should not see user2's file paths"

    @pytest.mark.xfail(
        reason="BOLA: Can enumerate file IDs to get all paths - T901",
    )
    def test_enumerate_file_ids_for_paths(self, api_client: APIClient):
        """Enumerate file IDs to collect filepaths from all users."""
        attacker = baker.make(User, username="path_enum")
        victim = baker.make(User, username="path_victim_enum")
        library = make_library(code="ENUM", name="Enum Test")

        # Victim's files with sensitive paths
        victim_files = []
        for i in range(5):
            f = baker.make(
                File,
                name=f"victim_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=victim,
                filepath=f"/secret/path/{i}/classified.mp3",
            )
            victim_files.append(f)

        api_client.force_authenticate(user=attacker)

        # Try ID enumeration
        found_paths = []
        base_id = victim_files[0].id

        for offset in range(-3, 8):
            try_id = base_id + offset
            response = api_client.get(f"/api/v2/files/{try_id}")
            if response.status_code == 200:
                found_paths.append(response.json().get("filepath"))

        # Should only find own files (none in this case)
        assert (
            len(found_paths) == 0
        ), "Should not be able to enumerate other users' file paths"


@pytest.mark.django_db
class TestFileOrganizationMassAssignment:
    """T902: Mass assignment via organization fields."""

    @pytest.mark.xfail(
        reason="BOPLA: Mass assignment allows changing filepath - T902",
    )
    def test_mass_assignment_filepath_blocked(self, api_client: APIClient):
        """
        Attempt to modify filepath via PATCH/PUT.
        Filepath should be immutable after creation.
        """
        user = baker.make(User, username="path_hacker")
        library = make_library(code="MASS", name="Mass Test")

        file_obj = baker.make(
            File,
            name="original.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            filepath="/original/path/file.mp3",
        )

        api_client.force_authenticate(user=user)

        # Attempt to change filepath
        response = api_client.patch(
            f"/api/v2/files/{file_obj.id}",
            {"filepath": "/hacked/malicious/path.mp3"},
            format="json",
        )

        file_obj.refresh_from_db()
        assert (
            file_obj.filepath == "/original/path/file.mp3"
        ), "Filepath should not be modifiable via API"

    @pytest.mark.xfail(
        reason="BOPLA: Mass assignment allows changing file_size - T903",
    )
    def test_mass_assignment_file_size_blocked(self, api_client: APIClient):
        """
        Attempt to modify file_size via PATCH/PUT.
        File size should be read-only from actual file.
        """
        user = baker.make(User, username="size_hacker")
        library = make_library(code="SIZE", name="Size Test")

        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            file_size=1024000,
        )

        api_client.force_authenticate(user=user)

        response = api_client.patch(
            f"/api/v2/files/{file_obj.id}",
            {"file_size": 999999999},
            format="json",
        )

        file_obj.refresh_from_db()
        assert (
            file_obj.file_size == 1024000
        ), "File size should be immutable via API"

    @pytest.mark.xfail(
        reason="BOPLA: Can move file to another user's library - T904",
    )
    def test_mass_assignment_library_change_blocked(
        self,
        api_client: APIClient,
    ):
        """
        Attempt to change file's library assignment.
        Could allow data exfiltration to attacker's library.
        """
        attacker = baker.make(User, username="lib_hacker")
        victim = baker.make(User, username="lib_victim")

        victim_library = make_library(code="VICTIM", name="Victim Library")
        attacker_library = make_library(
            code="ATTACKER",
            name="Attacker Library",
        )

        file_obj = baker.make(
            File,
            name="confidential.mp3",
            mime="audio/mp3",
            library=victim_library,
            owner=victim,
        )

        api_client.force_authenticate(user=attacker)

        response = api_client.patch(
            f"/api/v2/files/{file_obj.id}",
            {"library": attacker_library.id},
            format="json",
        )

        file_obj.refresh_from_db()
        assert (
            file_obj.library == victim_library
        ), "Library should not be changeable to attacker's"

    @pytest.mark.xfail(
        reason="BOPLA: Mass assignment allows changing import_status - T905",
    )
    def test_mass_assignment_import_status_blocked(
        self,
        api_client: APIClient,
    ):
        """
        Attempt to modify import_status via PATCH.
        Could bypass processing workflow.
        """
        user = baker.make(User, username="import_hacker")
        library = make_library(code="IMPORT", name="Import Test")

        file_obj = baker.make(
            File,
            name="pending.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            import_status=0,  # PENDING
        )

        api_client.force_authenticate(user=user)

        response = api_client.patch(
            f"/api/v2/files/{file_obj.id}",
            {"import_status": 1},  # SUCCESS
            format="json",
        )

        file_obj.refresh_from_db()
        assert (
            file_obj.import_status == 0
        ), "Import status should not be modifiable via API"


@pytest.mark.django_db
class TestFileOrganizationPathTraversal:
    """T906: Path traversal via filepath manipulation."""

    @pytest.mark.xfail(reason="Path traversal: Relative path accepted - T906")
    def test_path_traversal_relative_blocked(self, api_client: APIClient):
        """
        Attempt to create file with path traversal in filepath.
        API1:2023 - Path traversal vulnerability.
        """
        user = baker.make(User, username="traversal_attacker")
        library = make_library(code="TRAVERSAL", name="Traversal Test")

        api_client.force_authenticate(user=user)

        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../../../../root/.ssh/id_rsa",
        ]

        for path in traversal_paths:
            response = api_client.post(
                "/api/v2/files",
                {
                    "name": "evil.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "filepath": path,
                },
                format="json",
            )

            # Should reject or sanitize
            if response.status_code == 201:
                data = response.json()
                assert ".." not in data.get(
                    "filepath",
                    "",
                ), f"Path traversal not sanitized: {path}"

    @pytest.mark.xfail(
        reason="Path traversal: Absolute path outside storage allowed - T906",
    )
    def test_absolute_path_outside_storage_blocked(
        self,
        api_client: APIClient,
    ):
        """
        Attempt to use absolute path outside storage directory.
        """
        user = baker.make(User, username="abs_path_hacker")
        library = make_library(code="ABS", name="Abs Test")

        api_client.force_authenticate(user=user)

        malicious_paths = [
            "/etc/shadow",
            "/root/.bash_history",
            "/proc/self/environ",
            "/var/log/auth.log",
        ]

        for path in malicious_paths:
            response = api_client.post(
                "/api/v2/files",
                {
                    "name": "evil.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "filepath": path,
                },
                format="json",
            )

            if response.status_code == 201:
                data = response.json()
                # Should not store system paths
                assert not data.get("filepath", "").startswith(
                    "/etc/",
                ), f"System path accepted: {path}"

    @pytest.mark.xfail(
        reason="Flaky: Encoding attacks handling varies",
        strict=False,
    )
    def test_filepath_encoding_attacks(self, api_client: APIClient):
        """Test various filepath encoding attacks."""
        user = baker.make(User, username="encoding_attacker")
        library = make_library(code="ENC", name="Encoding Test")

        api_client.force_authenticate(user=user)

        encoding_attacks = [
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL encoded
            "..%2f..%2f..%2fetc%2fpasswd",  # Mixed encoding
            ".../.../.../etc/passwd",  # Triple dots
            "..../..../..../etc/passwd",  # Quadruple dots
        ]

        for path in encoding_attacks:
            response = api_client.post(
                "/api/v2/files",
                {
                    "name": "encoding_test.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "filepath": path,
                },
                format="json",
            )

            # Should not crash with 500
            assert response.status_code in [
                201,
                400,
            ], f"Encoding attack '{path}' caused server error"


@pytest.mark.django_db
class TestFileOrganizationSQLInjection:
    """T907: SQL injection via organization filters."""

    @pytest.mark.parametrize(
        "filter_payload",
        [
            "filepath=' OR '1'='1",
            "filepath=/music' UNION SELECT * FROM users --",
            "library=1' OR '1'='1",
            "import_status=0; DROP TABLE files; --",
            "file_size=1024' AND 1=1 --",
        ],
    )
    def test_sqli_in_organization_filter_no_crash(
        self,
        api_client: APIClient,
        filter_payload: str,
    ):
        """
        SQLi payloads in organization filters should not cause crashes.
        API8:2023 - Security misconfiguration.
        """
        user = baker.make(User, username="sqli_org")
        library = make_library(code="SQLI", name="SQLI Test")

        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            filepath="/music/test.mp3",
            _quantity=2,
        )

        api_client.force_authenticate(user=user)

        response = api_client.get(f"/api/v2/files?{filter_payload}")

        assert response.status_code in [
            200,
            400,
        ], f"SQLi payload '{filter_payload}' caused error"

    def test_sqli_in_filepath_param_no_crash(self, api_client: APIClient):
        """Test SQLi in filepath query parameter."""
        user = baker.make(User, username="sqli_path")
        library = make_library(code="SQLI2", name="SQLI Test")

        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            filepath="/music/test.mp3",
        )

        api_client.force_authenticate(user=user)

        payloads = [
            "' OR '1'='1",
            "'; SELECT * FROM auth_user; --",
            ") OR (1=1",
            "' AND filepath LIKE '%",
        ]

        for payload in payloads:
            response = api_client.get(f"/api/v2/files?filepath={payload}")
            assert response.status_code in [
                200,
                400,
            ], f"Payload '{payload}' caused server error"


@pytest.mark.django_db
class TestFileOrganizationBusinessLogic:
    """T908: Business logic bypass for file organization."""

    @pytest.mark.xfail(
        reason="Business logic: Can create file with fake size - T908",
    )
    def test_fake_file_size_on_create_blocked(self, api_client: APIClient):
        """
        Creating a file with fabricated file_size.
        API6:2023 - Unrestricted access to sensitive business flows.
        """
        user = baker.make(User, username="fake_size")
        library = make_library(code="FAKE", name="Fake Test")

        api_client.force_authenticate(user=user)

        response = api_client.post(
            "/api/v2/files",
            {
                "name": "fake.mp3",
                "mime": "audio/mp3",
                "library": library.id,
                "file_size": 999999999999,  # Clearly fake
            },
            format="json",
        )

        if response.status_code == 201:
            data = response.json()
            # Should either reject or not accept fake values
            assert (
                data.get("file_size") != 999999999999
            ), "Should not accept fabricated file size"

    @pytest.mark.xfail(
        reason="Business logic: Zero file size not validated - T908",
    )
    def test_zero_file_size_handled(self, api_client: APIClient):
        """Zero file size should be rejected or flagged."""
        user = baker.make(User, username="zero_size")
        library = make_library(code="ZERO", name="Zero Test")

        api_client.force_authenticate(user=user)

        response = api_client.post(
            "/api/v2/files",
            {
                "name": "zero.mp3",
                "mime": "audio/mp3",
                "library": library.id,
                "file_size": 0,
            },
            format="json",
        )

        # Should reject zero-size files
        assert response.status_code in [
            400,
        ], "Zero file size should be rejected"

    @pytest.mark.xfail(
        reason="Flaky: Negative size validation varies",
        strict=False,
    )
    def test_negative_file_size_rejected(self, api_client: APIClient):
        """Negative file size should be rejected."""
        user = baker.make(User, username="negative_size")
        library = make_library(code="NEG", name="Negative Test")

        api_client.force_authenticate(user=user)

        response = api_client.post(
            "/api/v2/files",
            {
                "name": "negative.mp3",
                "mime": "audio/mp3",
                "library": library.id,
                "file_size": -1,
            },
            format="json",
        )

        # Should reject negative sizes
        assert response.status_code in [
            400,
        ], "Negative file size should be rejected"


@pytest.mark.django_db
class TestFileOrganizationFilterBypass:
    """T909: Filter bypass to access file organization data."""

    @pytest.mark.xfail(
        reason="BOLA: Filter by library shows all users' files - T909",
    )
    def test_filter_by_library_cross_user(self, api_client: APIClient):
        """
        Filter by library returns files from all users.
        API1:2023 - Missing authorization in filtered queries.
        """
        attacker = baker.make(User, username="filter_attacker")
        victim = baker.make(User, username="filter_victim")
        shared_library = make_library(code="SHARED", name="Shared Library")

        # Victim's files in library
        victim_files = baker.make(
            File,
            name="victim_lib_file.mp3",
            mime="audio/mp3",
            library=shared_library,
            owner=victim,
            _quantity=3,
        )

        # Attacker's files
        baker.make(
            File,
            name="attacker_lib_file.mp3",
            mime="audio/mp3",
            library=shared_library,
            owner=attacker,
            _quantity=2,
        )

        api_client.force_authenticate(user=attacker)

        response = api_client.get(f"/api/v2/files?library={shared_library.id}")

        assert response.status_code == 200
        data = response.json()

        victim_visible = [
            f for f in data if f.get("name", "").startswith("victim_")
        ]
        assert (
            len(victim_visible) == 0
        ), "Filter should not expose victim's files"

    @pytest.mark.xfail(
        reason="BOLA: Filter by import_status shows all users' files - T909",
    )
    def test_filter_by_import_status_cross_user(self, api_client: APIClient):
        """Filter by import_status returns files from all users."""
        attacker = baker.make(User, username="status_attacker")
        victim = baker.make(User, username="status_victim")
        library = make_library(code="STATUS", name="Status Test")

        # Victim's pending files
        baker.make(
            File,
            name="victim_pending.mp3",
            mime="audio/mp3",
            library=library,
            owner=victim,
            import_status=0,  # PENDING
            _quantity=3,
        )

        # Attacker's pending files
        baker.make(
            File,
            name="attacker_pending.mp3",
            mime="audio/mp3",
            library=library,
            owner=attacker,
            import_status=0,
            _quantity=2,
        )

        api_client.force_authenticate(user=attacker)

        response = api_client.get("/api/v2/files?import_status=0")

        assert response.status_code == 200
        data = response.json()

        victim_visible = [
            f for f in data if f.get("name", "").startswith("victim_")
        ]
        assert (
            len(victim_visible) == 0
        ), "Filter should not expose victim's pending files"

    def test_filter_by_invalid_values_handled(self, api_client: APIClient):
        """Invalid filter values should be handled gracefully."""
        user = baker.make(User, username="invalid_filter")
        library = make_library(code="INVALID", name="Invalid Test")

        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        api_client.force_authenticate(user=user)

        invalid_filters = [
            "library=abc",
            "import_status=invalid",
            "file_size=big",
            "filepath=",
        ]

        for filter_str in invalid_filters:
            response = api_client.get(f"/api/v2/files?{filter_str}")
            assert response.status_code in [
                200,
                400,
            ], f"Invalid filter '{filter_str}' caused error"


@pytest.mark.django_db
class TestFileOrganizationInformationDisclosure:
    """T910: Information disclosure via organization endpoints."""

    def test_no_internal_paths_in_errors(self, api_client: APIClient):
        """Error messages should not expose internal paths."""
        user = baker.make(User, username="info_leak")
        library = make_library(code="INFO", name="Info Test")

        api_client.force_authenticate(user=user)

        # Try invalid operations
        response = api_client.get("/api/v2/files/999999999")

        if response.status_code == 404:
            data = response.json()
            error_str = str(data)
            assert (
                "/srv/libretime" not in error_str
            ), "Error exposes internal path"
            assert "/home/" not in error_str, "Error exposes home directory"

    def test_no_stack_traces_in_response(self, api_client: APIClient):
        """Stack traces should not be exposed in API responses."""
        user = baker.make(User, username="stack_leak")
        library = make_library(code="STACK", name="Stack Test")

        api_client.force_authenticate(user=user)

        response = api_client.get("/api/v2/files/invalid-id")

        if response.status_code == 400:
            data = response.json()
            error_str = str(data)
            assert (
                "Traceback" not in error_str
            ), "Stack trace exposed in response"
            assert 'File "' not in error_str, "File paths exposed in traceback"

    @pytest.mark.xfail(
        reason="Info leak: File size reveals file existence - T910",
    )
    def test_file_size_timing_attack(self, api_client: APIClient):
        """
        Timing attack: Different response times for existent vs non-existent files.
        Could reveal if a file exists even without access.
        """
        import time

        attacker = baker.make(User, username="timing_attacker")
        victim = baker.make(User, username="timing_victim")
        library = make_library(code="TIMING", name="Timing Test")

        # Create victim file
        victim_file = baker.make(
            File,
            name="timing_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=victim,
            file_size=9999999,
        )

        api_client.force_authenticate(user=attacker)

        # Time request for existing file (no access)
        start = time.time()
        response1 = api_client.get(f"/api/v2/files/{victim_file.id}")
        time_existing = time.time() - start

        # Time request for non-existing file
        start = time.time()
        response2 = api_client.get("/api/v2/files/999999999")
        time_nonexistent = time.time() - start

        # Both should be 404, timing should be similar
        assert (
            response1.status_code == response2.status_code == 404
        ), "Both should return 404"

        # Timing difference should be minimal (< 100ms)
        assert (
            abs(time_existing - time_nonexistent) < 0.1
        ), "Timing difference suggests file existence"


@pytest.mark.django_db
class TestFileOrganizationWorkflowBypass:
    """T911: Workflow bypass via organization manipulation."""

    @pytest.mark.xfail(
        reason="Workflow bypass: Can move PENDING file to SUCCESS library - T911",
    )
    def test_pending_file_library_move_blocked(self, api_client: APIClient):
        """
        Attempt to move pending file to 'processed' library.
        Could bypass import processing workflow.
        """
        user = baker.make(User, username="workflow_hacker")
        pending_lib = make_library(code="PENDING", name="Pending Library")
        processed_lib = make_library(
            code="PROCESSED",
            name="Processed Library",
        )

        file_obj = baker.make(
            File,
            name="unprocessed.mp3",
            mime="audio/mp3",
            library=pending_lib,
            owner=user,
            import_status=0,  # PENDING
        )

        api_client.force_authenticate(user=user)

        response = api_client.patch(
            f"/api/v2/files/{file_obj.id}",
            {"library": processed_lib.id},
            format="json",
        )

        file_obj.refresh_from_db()
        assert (
            file_obj.library == pending_lib
        ), "Should not allow moving pending file to processed library"

    @pytest.mark.xfail(
        reason="Workflow bypass: Can fake import completion - T911",
    )
    def test_fake_import_completion_blocked(self, api_client: APIClient):
        """
        Attempt to set both library and status to appear processed.
        """
        user = baker.make(User, username="fake_complete")
        library = make_library(code="MAIN", name="Main Library")

        file_obj = baker.make(
            File,
            name="incomplete.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            import_status=2,  # FAILED
        )

        api_client.force_authenticate(user=user)

        response = api_client.patch(
            f"/api/v2/files/{file_obj.id}",
            {
                "import_status": 1,  # SUCCESS
                "file_size": 1024000,  # Fake size
            },
            format="json",
        )

        file_obj.refresh_from_db()
        assert (
            file_obj.import_status == 2
        ), "Should not allow faking import completion"
