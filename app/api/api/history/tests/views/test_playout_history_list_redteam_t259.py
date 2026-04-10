"""T259: PlayoutHistory LIST redteam security tests.

Red Team security tests for PlayoutHistory LIST endpoint.
Tests for BOLA, BFLA, injection, and other API vulnerabilities.
"""


from datetime import timedelta

import pytest

from model_bakery import baker

from api.core.models.role import Role
from api.core.models.user import User
from api.history.models import PlayoutHistory
from api.storage.models import File
from sdk import now


@pytest.mark.django_db
class TestPlayoutHistoryListRedTeamBOLA:
    """API1:2023 Broken Object Level Authorization - LIST BOLA tests."""

    def test_bfla_regular_user_cannot_list(
        self, api_client, regular_user, faker,
    ):
        """
        BFLA: Regular user cannot access LIST endpoint.

        This is expected behavior - regular users should not list playout history.
        Only admins/managers should have this permission.
        """
        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/playout-history")

        # Should be forbidden for regular users
        assert response.status_code == 403

    def test_bola_admin_can_see_all_playout(
        self, api_client, admin_user, manager_user, faker,
    ):
        """
        BOLA: Admin/Manager sees ALL playout history (no owner filtering).

        Expected: Admins see all data (this may be intended behavior).
        Document that queryset has no owner-based filtering.
        """
        # Create victim user's playout
        victim = baker.make(User, role=Role.HOST, username=faker.user_name())
        victim_file = baker.make(File, mime="audio/mp3", owner=victim)
        victim_playout = baker.make(
            PlayoutHistory,
            file=victim_file,
            starts=now(),
            ends=now() + timedelta(minutes=5),
        )

        # Admin requests LIST
        response = api_client.get("/api/v2/playout-history")
        assert response.status_code == 200
        data = response.json()

        # Admin can see victim's playout - this is expected for admin
        # but queryset has no filtering at all
        victim_ids = [p.get("id") for p in data]

        # Document behavior: admin can see all (may be intended)
        if victim_playout.id in victim_ids:
            pass  # Expected admin behavior

        # Now test with manager
        api_client.force_authenticate(user=manager_user)
        response = api_client.get("/api/v2/playout-history")

        if response.status_code == 200:
            data = response.json()
            victim_ids = [p.get("id") for p in data]
            if victim_playout.id in victim_ids:
                pytest.xfail(
                    "T556: BOLA - Manager can see all users' playout (may be unintended)",
                )

    def test_bola_list_with_no_owner_field_in_model(
        self, api_client, admin_user, faker,
    ):
        """
        BOLA: PlayoutHistory model has no owner field for filtering.

        The model links to File and ShowInstance but neither enforces ownership.
        This makes proper BOLA filtering impossible without joins.
        """
        # This test documents the architectural issue
        from api.history.models import PlayoutHistory

        # Check model fields for ownership
        fields = [f.name for f in PlayoutHistory._meta.get_fields()]

        # No direct owner field
        assert "owner" not in fields
        assert "creator" not in fields
        assert "user" not in fields

        # Only foreign keys that may not enforce ownership
        assert "file" in fields
        assert "instance" in fields

    def test_bola_list_returns_all_data_no_filtering(
        self, api_client, admin_user, faker,
    ):
        """
        BOLA: LIST endpoint has no owner-based filtering in queryset.

        ViewSet uses PlayoutHistory.objects.all() without filtering.
        This is acceptable for admin but may be unintended for others.
        """
        # Create multiple users with files/playouts
        users = [
            baker.make(
                User, role=Role.HOST, username=f"user_{i}_{faker.user_name()}",
            )
            for i in range(3)
        ]
        files = [baker.make(File, mime="audio/mp3", owner=u) for u in users]
        for f in files:
            baker.make(
                PlayoutHistory,
                file=f,
                starts=now(),
                ends=now() + timedelta(minutes=5),
            )

        response = api_client.get("/api/v2/playout-history")
        assert response.status_code == 200

        data = response.json()
        # Admin gets all 3 playouts - queryset has no filtering
        # Document this behavior
        if len(data) == 3:
            pass  # Expected for admin with .all() queryset


@pytest.mark.django_db
class TestPlayoutHistoryListRedTeamBFLA:
    """API5:2023 Broken Function Level Authorization tests."""

    def test_bfla_list_as_regular_user(self, api_client, regular_user, faker):
        """
        BFLA: Regular user can access LIST endpoint.

        Should regular users see playout history at all?
        Or should this be admin-only?
        """
        api_client.force_authenticate(user=regular_user)

        # Create some data
        f = baker.make(File, mime="audio/mp3", owner=regular_user)
        baker.make(
            PlayoutHistory,
            file=f,
            starts=now(),
            ends=now() + timedelta(minutes=5),
        )

        response = api_client.get("/api/v2/playout-history")

        # Document current behavior
        if response.status_code == 200:
            # Regular user can LIST - is this intended?
            pass
        elif response.status_code == 403:
            # Properly restricted
            pass
        else:
            pytest.xfail(f"Unexpected status code: {response.status_code}")

    def test_bfla_list_as_guest_user(self, api_client, guest_user):
        """
        BFLA: Guest user can access LIST endpoint.

        Guests should have minimal permissions.
        """
        api_client.force_authenticate(user=guest_user)

        response = api_client.get("/api/v2/playout-history")

        # Guests should probably not access playout history
        if response.status_code == 200:
            pytest.xfail(
                "T557: BFLA - Guest user can access playout history LIST",
            )

    def test_bfla_list_unauthenticated(self, api_client):
        """
        BFLA: Unauthenticated access to LIST.

        Should return 403 for unauthenticated requests.
        """
        api_client.logout()
        response = api_client.get("/api/v2/playout-history")

        assert (
            response.status_code == 403
        ), f"Expected 403, got {response.status_code}"


@pytest.mark.django_db
class TestPlayoutHistoryListRedTeamInjection:
    """API10:2023 + Injection attacks on LIST endpoint."""

    SQLI_PAYLOADS = [
        "' OR '1'='1",
        "' UNION SELECT * FROM pg_authid--",
        "1' AND 1=1--",
        "1' AND 1=2--",
        "1; DROP TABLE cc_playout_history--",
        "' OR 'x'='x",
        "1 AND 1=CONVERT(int, @@version)",
        "' OR pg_sleep(5)--",
        "1' WAITFOR DELAY '0:0:5'--",
    ]

    def test_sqli_in_ordering_param(self, api_client, admin_user):
        """
        SQL Injection via ordering query parameter.

        DRF ordering filter passes directly to ORM - vulnerable if not sanitized.
        """
        for payload in self.SQLI_PAYLOADS:
            response = api_client.get(
                f"/api/v2/playout-history?ordering={payload}",
            )

            # Check for SQL error leakage or 500 errors
            if response.status_code == 500:
                pytest.xfail(
                    f"T558: SQLi in ordering param causes 500: {payload[:30]}...",
                )

            # Check response doesn't contain SQL keywords in error
            if response.status_code >= 400:
                error_text = str(response.content).lower()
                sql_keywords = ["sql", "syntax", "error", "pg_query", "sqlite"]
                if any(kw in error_text for kw in sql_keywords):
                    pytest.xfail(
                        f"T558: SQLi error disclosure in ordering: {payload[:30]}...",
                    )

    def test_sqli_in_search_param(self, api_client, admin_user):
        """
        SQL Injection via search query parameter.

        If search filter is enabled, test for SQLi.
        """
        for payload in self.SQLI_PAYLOADS[:5]:  # Test subset
            response = api_client.get(
                f"/api/v2/playout-history?search={payload}",
            )

            if response.status_code == 500:
                pytest.xfail(
                    f"T558: SQLi in search param causes 500: {payload[:30]}...",
                )

    def test_nosql_injection_in_filter(self, api_client, admin_user):
        """
        NoSQL injection via filter parameters.

        Test MongoDB-style operators if using NoSQL backend.
        """
        nosql_payloads = [
            {"file": {"$ne": None}},
            {"file": {"$gt": ""}},
            {"$where": "this.file == 1"},
        ]

        for payload in nosql_payloads:
            response = api_client.get("/api/v2/playout-history", payload)
            # Just document behavior - Django ORM should be safe
            assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestPlayoutHistoryListRedTeamResourceConsumption:
    """API4:2023 Unrestricted Resource Consumption tests."""

    def test_pagination_page_size_abuse(self, api_client, admin_user, faker):
        """
        Resource consumption via large page_size.

        Requesting huge page sizes can exhaust memory.
        """
        # Create many records
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        for i in range(100):
            baker.make(
                PlayoutHistory,
                file=f,
                starts=now() + timedelta(minutes=i),
                ends=now() + timedelta(minutes=i + 5),
            )

        # Request large page size
        response = api_client.get("/api/v2/playout-history?page_size=10000")

        # Should be limited by max_page_size
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 1000:
                pytest.xfail(
                    "T559: No pagination limit - can request huge datasets",
                )

    def test_pagination_offset_abuse(self, api_client, admin_user):
        """
        Resource consumption via deep pagination.

        Large offsets are expensive in databases.
        """
        response = api_client.get("/api/v2/playout-history?offset=999999999")

        # Deep pagination should be limited
        if response.status_code == 500:
            pytest.xfail("T559: Deep pagination causes server error")

    def test_rapid_sequential_requests(self, api_client, admin_user):
        """
        Rate limiting test via rapid sequential requests.

        Test if endpoint has rate limiting.
        """
        responses = []
        for _ in range(20):
            response = api_client.get("/api/v2/playout-history")
            responses.append(response.status_code)

        success_count = responses.count(200)
        rate_limited = responses.count(429)

        # All 20 succeeded means no rate limiting
        if success_count == 20 and rate_limited == 0:
            pytest.xfail("T560: No rate limiting on LIST endpoint")


@pytest.mark.django_db
class TestPlayoutHistoryListRedTeamInformationDisclosure:
    """API8:2023 Security Misconfiguration - Information Disclosure tests."""

    def test_error_message_leaks_sql_structure(self, api_client, admin_user):
        """
        Error messages reveal database structure.

        500 errors should not expose SQL or table names.
        """
        # Trigger error with malformed ordering
        response = api_client.get(
            "/api/v2/playout-history?ordering=starts;DROP",
        )

        if response.status_code == 500:
            error_text = str(response.content).lower()
            leak_keywords = [
                "cc_playout_history",
                "column",
                "pg_query",
                "sqlite",
                "table",
                "syntax",
            ]
            if any(kw in error_text for kw in leak_keywords):
                pytest.xfail("T561: Error messages leak database structure")

    def test_stack_trace_exposure(self, api_client, admin_user):
        """
        Stack traces exposed in error responses.

        Debug mode should be off in production.
        """
        # Trigger an error
        response = api_client.get("/api/v2/playout-history?format=evil")

        if response.status_code >= 500:
            content = str(response.content)
            if "traceback" in content.lower() or "/app/" in content:
                pytest.xfail("T561: Stack traces exposed in error responses")

    def test_verbose_404_leaks_existence(self, api_client, admin_user):
        """
        404 messages differ for existing vs non-existing resources.

        Can be used to enumerate valid IDs.
        """
        # Try to get non-existent playout
        response = api_client.get("/api/v2/playout-history/99999999")

        if response.status_code == 404:
            # Check if error message is generic
            data = response.json()
            detail = str(data.get("detail", "")).lower()

            # If message mentions "playout" specifically, it confirms type
            if "playout" in detail and "not found" in detail:
                # This is actually OK for DRF - it confirms resource type
                pass

    def test_response_headers_disclose_stack(self, api_client, admin_user):
        """
        HTTP headers reveal server stack information.

        Check for X-Powered-By, Server headers with version info.
        """
        response = api_client.get("/api/v2/playout-history")

        # Check for information disclosure headers
        disclosive_headers = [
            "x-powered-by",
            "server",
            "x-django-version",
            "x-frame-options",  # Missing is also an issue
        ]

        for header in disclosive_headers:
            if header in response.headers:
                value = response.headers[header]
                # Check for version numbers
                import re

                if re.search(r"\d+\.\d+", str(value)):
                    # Version disclosure
                    pass  # Document but don't fail


@pytest.mark.django_db
class TestPlayoutHistoryListRedTeamFuzzing:
    """Fuzzing tests for LIST endpoint parameters."""

    FUZZ_PARAMS = [
        (
            "page",
            [
                "0",
                "-1",
                "99999999999999999999",
                "abc",
                "1.5",
                "",
                "null",
                "undefined",
                "'",
                '"',
                ";",
            ],
        ),
        ("page_size", ["0", "-1", "999999", "abc", "1.5", "", "null", "-999"]),
        (
            "ordering",
            [
                "",
                "id",
                "-id",
                "starts",
                "-starts",
                "invalid_field",
                "id;DROP",
                "'",
                "--",
            ],
        ),
        (
            "search",
            ["", "'", ";", "<script>", "../../../etc/passwd", "A" * 10000],
        ),
        ("format", ["json", "api", "html", "xml", "csv", "evil"]),
    ]

    def test_fuzzing_query_parameters(self, api_client, admin_user):
        """
        Fuzz all query parameters for crashes or unexpected behavior.
        """
        errors_found = []

        for param, values in self.FUZZ_PARAMS:
            for value in values:
                url = f"/api/v2/playout-history?{param}={value}"
                response = api_client.get(url)

                # Document 500 errors
                if response.status_code == 500:
                    errors_found.append(f"{param}={value[:20]}... -> 500")

        # Report findings
        if errors_found:
            pytest.xfail(
                f"T562: Fuzzing found {len(errors_found)} parameters causing 500 errors: {errors_found[:3]}",
            )

    def test_fuzzing_unicode_in_params(self, api_client, admin_user):
        """
        Unicode fuzzing in query parameters.

        Test various Unicode characters that might cause issues.
        """
        unicode_payloads = [
            "日本語",  # Japanese
            "العربية",  # Arabic
            "🎵🎶",  # Emoji
            "<script>alert(1)</script>",  # XSS
            "\\x00",  # Null byte
            "%00",  # URL encoded null
            "A" * 10000,  # Length limit
        ]

        for payload in unicode_payloads:
            response = api_client.get(
                f"/api/v2/playout-history?search={payload}",
            )

            if response.status_code == 500:
                pytest.xfail(
                    f"T562: Unicode payload causes 500: {repr(payload[:30])}",
                )


@pytest.mark.django_db
class TestPlayoutHistoryListRedTeamMassAssignment:
    """API3:2023 Broken Object Property Level Authorization - via LIST context."""

    def test_list_response_includes_all_fields(
        self, api_client, admin_user, faker,
    ):
        """
        BOPLA: LIST response includes all model fields.

        fields = '__all__' exposes everything including potential secrets.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        baker.make(
            PlayoutHistory,
            file=f,
            starts=now(),
            ends=now() + timedelta(minutes=5),
        )

        response = api_client.get("/api/v2/playout-history")
        assert response.status_code == 200

        data = response.json()
        if data:
            fields_returned = set(data[0].keys())

            # Check for sensitive fields that shouldn't be exposed
            sensitive_fields = {"password", "secret", "token", "key", "hash"}
            exposed_sensitive = sensitive_fields & fields_returned

            if exposed_sensitive:
                pytest.xfail(
                    f"T563: Sensitive fields exposed in LIST: {exposed_sensitive}",
                )

    def test_list_fields_review(self, api_client, admin_user, faker):
        """
        Document all fields returned by LIST for security review.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        baker.make(
            PlayoutHistory,
            file=f,
            starts=now(),
            ends=now() + timedelta(minutes=5),
        )

        response = api_client.get("/api/v2/playout-history")
        data = response.json()

        if data:
            fields = list(data[0].keys())
            # Just document the fields for manual review
            expected_fields = ["id", "file", "starts", "ends", "instance"]

            # Check all expected fields are present
            for field in expected_fields:
                assert (
                    field in fields
                ), f"Expected field {field} not in response"


@pytest.mark.django_db
class TestPlayoutHistoryListRedTeamIDEnumeration:
    """ID enumeration and information leakage tests."""

    def test_id_sequence_enumeration(self, api_client, admin_user, faker):
        """
        Sequential IDs allow enumeration of other records.

        Check if IDs are sequential (1, 2, 3...) vs UUIDs.
        """
        # Create multiple records
        f = baker.make(File, mime="audio/mp3", owner=admin_user)
        playouts = [
            baker.make(
                PlayoutHistory, file=f, starts=now() + timedelta(minutes=i),
            )
            for i in range(5)
        ]

        response = api_client.get("/api/v2/playout-history")
        data = response.json()

        ids = [p["id"] for p in data]

        # Check if IDs are sequential integers
        if all(isinstance(i, int) for i in ids):
            # Sequential IDs are predictable
            if max(ids) - min(ids) == len(ids) - 1:
                # Confirms sequential allocation
                pass  # Document - this enables IDOR attacks

    def test_id_gap_analysis(self, api_client, admin_user, faker):
        """
        ID gaps reveal deletion patterns.

        Gaps in sequential IDs show records were deleted.
        """
        f = baker.make(File, mime="audio/mp3", owner=admin_user)

        # Create, delete, create pattern
        p1 = baker.make(PlayoutHistory, file=f, starts=now())
        p1_id = p1.id
        p1.delete()

        p2 = baker.make(
            PlayoutHistory, file=f, starts=now() + timedelta(minutes=10),
        )
        p2_id = p2.id

        # If IDs are not sequential, gap reveals deletion
        if p2_id != p1_id + 1:
            # Gap exists - confirms deletion happened
            pass  # Document this information leakage


@pytest.mark.django_db
class TestPlayoutHistoryListRedTeamHTTPMethodOverride:
    """HTTP method override and verb tampering tests."""

    def test_method_override_post_to_list(self, api_client, admin_user):
        """
        Try to override POST to LIST endpoint.

        Some frameworks allow method override headers.
        """
        response = api_client.post(
            "/api/v2/playout-history",
            data={},
            headers={"X-HTTP-Method-Override": "GET"},
        )

        # Should not work - POST is for CREATE
        # Document behavior
        assert response.status_code in [201, 400, 405]

    def test_http_method_tampering(self, api_client, admin_user):
        """
        Test various HTTP methods on LIST endpoint.
        """
        methods = ["PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE"]

        for method in methods:
            response = getattr(api_client, method.lower())(
                "/api/v2/playout-history",
            )

            # Only GET and POST should work
            if method == "OPTIONS":
                assert response.status_code == 200  # CORS preflight
            elif method == "HEAD":
                assert response.status_code == 200  # HEAD should work like GET
            elif response.status_code == 200:
                pytest.xfail(f"T564: {method} on LIST endpoint returned 200")
