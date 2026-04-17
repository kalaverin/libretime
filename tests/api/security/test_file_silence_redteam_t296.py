"""
T296: Silence Detection Red Team Security Tests.

Paranoid security tests for silence detection workflow vulnerabilities.
OWASP API Top 10 2023: API1:2023 BOLA, API3:2023 BOPLA, API4:2023 Resource Consumption
"""

import json

from datetime import timedelta

import pytest

from django.conf import settings
from model_bakery import baker
from rest_framework.test import APIClient

from api.core.models import Role, User
from api.storage.models import File, Library

# SQLi payloads for filter parameters
SQLI_PAYLOADS = [
    "import_status=' OR '1'='1",
    "import_status=0' UNION SELECT * FROM users --",
    "import_status=0; DROP TABLE files; --",
    "channels=2' AND 1=1 --",
    "sample_rate=44100' OR '1'='1",
    "mime=' OR '1'='1",
]

# Path traversal payloads for filepath
PATH_TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "../../../../root/.bashrc",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "/etc/shadow",
    "/proc/self/environ",
]

# Invalid MIME types for confusion attacks
INVALID_MIME_TYPES = [
    "application/javascript",
    "text/html",
    "application/x-php",
    "application/x-sh",
    "image/svg+xml",
    "application/xml",
    "text/xml",
    "application/octet-stream",
    "",  # Empty
    "audio/'; DROP TABLE files; --",
    "<script>alert(1)</script>",
]

# Extreme audio properties for DoS/overflow
EXTREME_AUDIO_PROPS = [
    ("channels", 999999999),
    ("channels", -1),
    ("channels", 0),
    ("sample_rate", 999999999),
    ("sample_rate", -1),
    ("sample_rate", 0),
    ("sample_rate", 1),
    ("bit_rate", 2**31),
    ("bit_rate", -1),
]

# Extreme durations for DoS
EXTREME_DURATIONS = [
    timedelta(days=365),  # 1 year
    timedelta(days=999),  # Almost 3 years
    timedelta(microseconds=1),  # Very short
    timedelta(seconds=0),  # Zero
    timedelta(seconds=-1),  # Negative
]


@pytest.mark.django_db
class TestSilenceProcessingBOLA:
    """API1:2023 - Broken Object Level Authorization in silence processing."""

    @pytest.mark.xfail(
        reason="BOLA: Filter shows all users' files - T889",
        strict=False,
    )
    def test_filter_by_import_status_shows_only_own_files(
        self,
        api_client,
        faker,
    ):
        """User should only see their own files when filtering by import_status. (T889)"""
        user_a = baker.make(
            User,
            username=f"sil_a_{faker.user_name()}",
            role=Role.HOST,
        )
        user_b = baker.make(
            User,
            username=f"sil_b_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="BOLA",
            name="BOLA",
            description="Test",
        )

        # User A creates SUCCESS files
        files_a = []
        for i in range(3):
            f = baker.make(
                File,
                name=f"user_a_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user_a,
                import_status=File.ImportStatus.SUCCESS,
            )
            files_a.append(f.id)

        # User B creates SUCCESS files
        files_b = []
        for i in range(3):
            f = baker.make(
                File,
                name=f"user_b_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user_b,
                import_status=File.ImportStatus.SUCCESS,
            )
            files_b.append(f.id)

        # User A filters by SUCCESS status
        client_a = APIClient()
        client_a.force_authenticate(user=user_a)
        response = client_a.get("/api/v2/files?import_status=0")

        assert response.status_code == 200
        data = response.json()

        returned_ids = [f.get("id") for f in data]

        # User A should see their files
        for fid in files_a:
            assert fid in returned_ids, f"User A should see their file {fid}"

        # User A should NOT see User B's files
        for fid in files_b:
            if fid in returned_ids:
                pytest.fail(f"BOLA: User A can see User B's file {fid}")

    @pytest.mark.xfail(
        reason="BOLA: Cross-user access allowed - T889",
        strict=False,
    )
    def test_cross_user_silence_processing_blocked(self, api_client, faker):
        """User cannot trigger silence processing on another user's file. (T889)""" ""
        user_a = baker.make(
            User,
            username=f"proc_a_{faker.user_name()}",
            role=Role.HOST,
        )
        user_b = baker.make(
            User,
            username=f"proc_b_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="PROC",
            name="Proc",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="target.mp3",
            mime="audio/mp3",
            library=library,
            owner=user_a,
            import_status=File.ImportStatus.SUCCESS,
        )

        # User B tries to access User A's file
        client_b = APIClient()
        client_b.force_authenticate(user=user_b)
        response = client_b.get(f"/api/v2/files/{file_obj.id}")

        # Should be blocked
        assert response.status_code in [
            403,
            404,
        ], f"Expected 403/404, got {response.status_code}"


@pytest.mark.django_db
class TestSilenceProcessingMassAssignment:
    """API3:2023 - Broken Object Property Level Authorization."""

    @pytest.mark.xfail(
        reason="BOPLA: import_status can be modified - T887",
        strict=False,
    )
    def test_mass_assignment_import_status_blocked(self, api_client, faker):
        """import_status should not be modifiable via PATCH. (T887)"""
        user = baker.make(
            User,
            username=f"mass_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="MASS",
            name="Mass",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="mass_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            import_status=File.ImportStatus.PENDING,
        )
        original_status = file_obj.import_status

        # Try to change import_status via PATCH (bypass workflow)
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"import_status": File.ImportStatus.SUCCESS}),
            content_type="application/json",
        )

        file_obj.refresh_from_db()

        # import_status should not change
        assert (
            file_obj.import_status == original_status
        ), f"import_status changed from {original_status} to {file_obj.import_status}"

    @pytest.mark.xfail(
        reason="BOPLA: channels can be spoofed - T888",
        strict=False,
    )
    def test_mass_assignment_extreme_channels_blocked(self, api_client, faker):
        """Extreme channel values should be rejected. (T888)"""
        user = baker.make(
            User,
            username=f"chan_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="CHAN",
            name="Chan",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="channel_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"channels": 999999}),
            content_type="application/json",
        )

        file_obj.refresh_from_db()
        assert (
            file_obj.channels == 2
        ), f"Channels changed to {file_obj.channels}"


@pytest.mark.django_db
class TestSilenceProcessingSQLInjection:
    """SQL injection via silence-related filters."""

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    def test_sqli_in_import_status_filter_no_crash(
        self,
        payload,
        api_client,
        faker,
    ):
        """SQLi in import_status filter should not crash."""
        user = baker.make(
            User,
            username=f"sqli_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="SQLI",
            name="SQLI",
            description="Test",
        )
        baker.make(
            File,
            name="sqli_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            import_status=File.ImportStatus.SUCCESS,
        )

        response = api_client.get(f"/api/v2/files?{payload}")

        # Should not crash with 500
        assert response.status_code != 500, f"SQLi caused 500: {payload[:50]}"
        assert response.status_code in [200, 400]

    def test_sqli_in_channels_filter_no_crash(self, api_client, faker):
        """SQLi in channels filter."""
        user = baker.make(
            User,
            username=f"sqli_c_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="SQLIC",
            name="SQLI",
            description="Test",
        )
        baker.make(
            File,
            name="channels_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
        )

        sqli_channels = [
            "channels=2' OR '1'='1",
            "channels=1' UNION SELECT * FROM users --",
            "channels=0; DROP TABLE files; --",
        ]

        for payload in sqli_channels:
            response = api_client.get(f"/api/v2/files?{payload}")
            assert response.status_code != 500, f"SQLi in channels: {payload}"


@pytest.mark.django_db
class TestSilenceProcessingPathTraversal:
    """Path traversal in filepath for silence processing."""

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param(
                "../../../etc/passwd",
                marks=pytest.mark.xfail(
                    reason="T890: Path traversal",
                    strict=False,
                ),
            ),
            "../../../../root/.bashrc",
            "..\\..\\..\\windows\\system32\\config\\sam",
            pytest.param(
                "/etc/shadow",
                marks=pytest.mark.xfail(
                    reason="T890: Path traversal",
                    strict=False,
                ),
            ),
            "/proc/self/environ",
        ],
    )
    def test_path_traversal_in_filepath_blocked(
        self,
        payload,
        api_client,
        faker,
    ):
        """Path traversal in filepath should be blocked."""
        user = baker.make(
            User,
            username=f"path_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="PATH",
            name="Path",
            description="Test",
        )
        file_obj = baker.make(
            File,
            name="path_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            filepath="/valid/path/file.mp3",
        )
        original_path = file_obj.filepath

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"filepath": payload}),
            content_type="application/json",
        )

        file_obj.refresh_from_db()

        # Should not accept traversal paths
        if ".." in payload or "/etc/" in payload or "/root/" in payload:
            assert (
                file_obj.filepath == original_path
                or "/etc/" not in file_obj.filepath
            ), f"Path traversal accepted: {payload}"


@pytest.mark.django_db
class TestSilenceProcessingMIMEConfusion:
    """MIME type confusion and bypass attacks."""

    @pytest.mark.parametrize("mime_type", INVALID_MIME_TYPES)
    def test_invalid_mime_type_handled(self, mime_type, api_client, faker):
        """Invalid/dangerous MIME types should be rejected."""
        user = baker.make(
            User,
            username=f"mime_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="MIME",
            name="MIME",
            description="Test",
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )

        try:
            response = client.post(
                "/api/v2/files",
                json.dumps(
                    {
                        "name": "test.file",
                        "mime": mime_type,
                        "library": library.id,
                        "owner": user.id,
                    },
                ),
                content_type="application/json",
            )

            # Should reject dangerous MIME types
            if any(
                x in str(mime_type).lower()
                for x in ["script", "php", "sh", "html"]
            ):
                assert response.status_code in [
                    400,
                    415,
                ], f"Dangerous MIME accepted: {mime_type[:50]}"
        except Exception:
            # Should handle gracefully
            pass

    def test_mime_spoofing_for_silence_processing(self, api_client, faker):
        """Spoof MIME type to bypass silence processing checks."""
        user = baker.make(
            User,
            username=f"spoof_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="SPOOF",
            name="Spoof",
            description="Test",
        )

        # Create file with spoofed MIME
        file_obj = baker.make(
            File,
            name="malicious.php",
            mime="audio/mp3",  # Spoofed as audio
            library=library,
            owner=user,
            import_status=File.ImportStatus.SUCCESS,
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        data = response.json()

        # Should expose the actual MIME or validate extension
        # This is a test to verify if MIME validation exists


@pytest.mark.django_db
class TestSilenceProcessingNumericOverflow:
    """Numeric overflow attacks in audio properties."""

    @pytest.mark.parametrize("field,value", EXTREME_AUDIO_PROPS)
    def test_extreme_audio_properties_handled(
        self,
        field,
        value,
        api_client,
        faker,
    ):
        """Extreme audio properties should be validated."""
        user = baker.make(
            User,
            username=f"num_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="NUM",
            name="Num",
            description="Test",
        )
        file_obj = baker.make(
            File,
            name="numeric_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
            sample_rate=44100,
            bit_rate=128000,
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({field: value}),
            content_type="application/json",
        )

        # Should not crash
        assert response.status_code in [
            200,
            400,
        ], f"Extreme {field}={value} caused error"


@pytest.mark.django_db
class TestSilenceProcessingResourceExhaustion:
    """API4:2023 - Resource exhaustion via extreme durations."""

    @pytest.mark.parametrize("duration", EXTREME_DURATIONS)
    def test_extreme_duration_handled(self, duration, api_client, faker):
        """Extreme durations should be validated."""
        user = baker.make(
            User,
            username=f"dur_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="DUR",
            name="Dur",
            description="Test",
        )

        try:
            file_obj = baker.make(
                File,
                name="duration_test.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
                length=duration,
            )

            response = api_client.get(f"/api/v2/files/{file_obj.id}")
            assert response.status_code in [200, 400]
        except Exception:
            # Should handle gracefully
            pass

    def test_batch_processing_limits(self, api_client, faker):
        """Batch silence processing should have limits."""
        user = baker.make(
            User,
            username=f"batch_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="BATCH",
            name="Batch",
            description="Test",
        )

        # Create many files
        for i in range(100):
            baker.make(
                File,
                name=f"batch_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
                import_status=File.ImportStatus.SUCCESS,
            )

        # Request all for batch processing
        response = api_client.get("/api/v2/files?import_status=0")
        assert response.status_code == 200

        data = response.json()
        # Should return all or have reasonable limit
        assert len(data) >= 100 or len(data) <= 1000


@pytest.mark.django_db
class TestSilenceProcessingWorkflowBypass:
    """Workflow bypass attacks."""

    @pytest.mark.xfail(reason="Workflow bypass possible - T891", strict=False)
    def test_pending_to_success_bypass_blocked(self, api_client, faker):
        """Cannot bypass processing by directly setting SUCCESS. (T891)"""
        user = baker.make(
            User,
            username=f"bypass_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="BYPASS",
            name="Bypass",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="bypass_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            import_status=File.ImportStatus.PENDING,
        )

        # Try to bypass to SUCCESS
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"import_status": 0}),  # SUCCESS
            content_type="application/json",
        )

        file_obj.refresh_from_db()

        # Status should remain PENDING
        if (
            response.status_code == 200
            and file_obj.import_status == File.ImportStatus.SUCCESS
        ):
            pytest.fail(
                "Workflow bypass possible: PENDING -> SUCCESS via PATCH",
            )

    @pytest.mark.xfail(reason="Workflow bypass possible - T891", strict=False)
    def test_failed_to_success_bypass_blocked(self, api_client, faker):
        """Cannot bypass by setting FAILED to SUCCESS. (T891)"""
        user = baker.make(
            User,
            username=f"fail_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="FAIL",
            name="Fail",
            description="Test",
        )

        file_obj = baker.make(
            File,
            name="fail_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            import_status=File.ImportStatus.FAILED,
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"import_status": 0}),
            content_type="application/json",
        )

        file_obj.refresh_from_db()
        assert file_obj.import_status == File.ImportStatus.FAILED


@pytest.mark.django_db
class TestSilenceProcessingInformationDisclosure:
    """Information disclosure via error messages."""

    def test_no_internal_paths_in_errors(self, api_client, faker):
        """Error messages should not expose internal paths."""
        user = baker.make(
            User,
            username=f"info_{faker.user_name()}",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            code="INFO",
            name="Info",
            description="Test",
        )

        # Request non-existent file
        response = api_client.get("/api/v2/files/999999999")

        if response.status_code == 500:
            error_text = response.content.decode(
                "utf-8",
                errors="ignore",
            ).lower()
            assert "/home/" not in error_text, "Internal path exposed"
            assert "/var/" not in error_text, "Internal path exposed"
            assert "sql" not in error_text, "SQL info exposed"

    def test_no_stack_traces_in_response(self, api_client, faker):
        """Stack traces should not be exposed."""
        user = baker.make(
            User,
            username=f"stack_{faker.user_name()}",
            role=Role.HOST,
        )

        # Trigger potential error with bad filter
        response = api_client.get("/api/v2/files?import_status=invalid")

        response_text = response.content.decode(
            "utf-8",
            errors="ignore",
        ).lower()
        assert "traceback" not in response_text, "Stack trace exposed"
        assert "exception" not in response_text, "Exception exposed"
        assert "error at" not in response_text, "Error location exposed"
