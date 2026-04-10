"""
RED TEAM: T204 - Show RETRIEVE endpoint security tests.

Attack vectors:
- ID enumeration
- SQL injection in path
- Path traversal
- Information disclosure via error messages
- BOLA (access other users' shows)
- Mass assignment via GET
"""

import pytest
from model_bakery import baker
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestShowRetrieveIDEnumeration:
    """ID enumeration attacks."""

    def test_sequential_id_access(self, api_client, admin_user):
        """Try to enumerate shows by sequential IDs."""
        api_client.force_authenticate(user=admin_user)
        
        # Try to access sequential IDs
        for i in range(1, 10):
            response = api_client.get(f"/api/v2/shows/{i}")
            # Should return 404 for non-existent, not reveal existence
            assert response.status_code in [200, 404]

    def test_negative_id(self, api_client, admin_user):
        """Try to retrieve with negative ID."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/shows/-1")
        
        # Should return 404, not crash
        assert response.status_code in [404, 400]

    def test_zero_id(self, api_client, admin_user):
        """Try to retrieve with zero ID."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/shows/0")
        
        assert response.status_code in [404, 400]

    def test_very_large_id(self, api_client, admin_user):
        """Try to retrieve with very large ID."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/shows/999999999999999999")
        
        assert response.status_code in [404, 400]

    def test_float_id(self, api_client, admin_user):
        """Try to retrieve with float ID."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/shows/1.5")
        
        assert response.status_code in [404, 400]


@pytest.mark.django_db
class TestShowRetrieveSQLInjection:
    """SQL injection in path attacks."""

    def test_sql_injection_in_id(self, api_client, admin_user):
        """Try SQL injection in show ID."""
        api_client.force_authenticate(user=admin_user)
        
        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_show;--",
            "1 UNION SELECT * FROM cc_subjs",
            "1' UNION SELECT username,password FROM cc_subjs--",
        ]
        
        for payload in sqli_payloads:
            response = api_client.get(f"/api/v2/shows/{payload}")
            # Should not crash or return data
            if response.status_code == 500:
                pytest.fail(f"BAG: SQL injection causes crash: {payload}")
            assert response.status_code in [404, 400]

    def test_sql_injection_union(self, api_client, admin_user):
        """Try UNION-based SQL injection."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/shows/1%20UNION%20SELECT%20*%20FROM%20cc_subjs")
        
        if response.status_code == 200:
            pytest.fail("BAG: UNION SQL injection returns data")

    def test_sql_injection_error_message(self, api_client, admin_user):
        """Check if SQL errors leak information."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/shows/1'\"")
        
        if response.status_code == 500:
            content = response.content.decode()
            leaked_terms = ["sql", "syntax", "error", "cc_show", "column"]
            for term in leaked_terms:
                if term.lower() in content.lower():
                    pytest.fail(f"BAG: Error message leaks info: {term}")


@pytest.mark.django_db
class TestShowRetrievePathTraversal:
    """Path traversal attacks."""

    def test_path_traversal_dots(self, api_client, admin_user):
        """Try path traversal with dots."""
        api_client.force_authenticate(user=admin_user)
        
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd",
        ]
        
        for path in traversal_paths:
            response = api_client.get(f"/api/v2/shows/{path}")
            assert response.status_code in [404, 400]

    def test_null_byte_injection(self, api_client, admin_user):
        """Try null byte injection."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/shows/1%00../../../etc/passwd")
        
        assert response.status_code in [404, 400, 500]


@pytest.mark.django_db
class TestShowRetrieveBOLA:
    """Broken Object Level Authorization."""

    def test_access_other_user_show(self, api_client, admin_user, regular_user):
        """Try to access another user's show."""
        show = baker.make("schedule.Show", name="Admin Show")

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/shows/{show.id}")

        # Should be 404 (not found) or 403 (forbidden)
        # 200 means BOLA vulnerability
        if response.status_code == 200:
            pytest.fail("CRITICAL BAG: Can access other user's show (BOLA)")

    def test_access_show_via_idor(self, api_client, admin_user, regular_user):
        """Try IDOR by guessing sequential IDs."""
        # Create show
        show = baker.make("schedule.Show", name="Private Show")
        
        # Regular user tries to access
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/shows/{show.id}")

        if response.status_code == 200:
            pytest.fail("CRITICAL BAG: IDOR - can access show by ID")


@pytest.mark.django_db
class TestShowRetrieveInformationDisclosure:
    """Information disclosure attacks."""

    def test_error_message_on_invalid_id(self, api_client, admin_user):
        """Check error messages for information leakage."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/shows/invalid")
        
        if response.status_code == 404:
            content = response.content.decode()
            leaked_terms = [
                "cc_show",
                "column",
                "table",
                "database",
                "django",
                "sql",
            ]
            for term in leaked_terms:
                if term.lower() in content.lower():
                    pytest.fail(f"BAG: 404 leaks implementation details: {term}")

    def test_stack_trace_disclosure(self, api_client, admin_user):
        """Check if stack traces are exposed."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/shows/☃")  # Unicode snowman
        
        if response.status_code == 500:
            content = response.content.decode()
            if "traceback" in content.lower() or "stack" in content.lower():
                pytest.fail("BAG: Stack trace exposed in error")

    def test_timing_disclosure(self, api_client, admin_user):
        """Check for timing-based information disclosure."""
        import time

        api_client.force_authenticate(user=admin_user)

        # Request existing show
        show = baker.make("schedule.Show", name="Test Show")
        start = time.time()
        response1 = api_client.get(f"/api/v2/shows/{show.id}")
        time_existing = time.time() - start

        # Request non-existing show
        start = time.time()
        response2 = api_client.get("/api/v2/shows/99999")
        time_nonexisting = time.time() - start

        # Times should be similar
        diff = abs(time_existing - time_nonexisting)
        assert diff < 0.5, f"Possible timing attack: diff={diff}s"


@pytest.mark.django_db
class TestShowRetrieveMassAssignment:
    """Mass assignment via GET."""

    def test_get_with_body_params(self, api_client, admin_user):
        """Try to send body params in GET request."""
        show = baker.make("schedule.Show", name="Test Show")
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(
            f"/api/v2/shows/{show.id}",
            {"name": "Hacked Name"},  # Should be ignored
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Show"  # Should not be modified


@pytest.mark.django_db
class TestShowRetrieveBusinessLogic:
    """Business logic bypasses."""

    def test_retrieve_without_auth(self, api_client):
        """Try to retrieve show without authentication."""
        show = baker.make("schedule.Show", name="Test Show")
        
        response = api_client.get(f"/api/v2/shows/{show.id}")
        
        if response.status_code == 200:
            pytest.fail("CRITICAL BAG: Anonymous can retrieve shows")

    def test_retrieve_deleted_show(self, api_client, admin_user):
        """Try to retrieve deleted show."""
        show = baker.make("schedule.Show", name="Deleted Show")
        show_id = show.id
        show.delete()

        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f"/api/v2/shows/{show_id}")
        
        # Should return 404
        assert response.status_code == 404

    def test_retrieve_with_special_chars_in_url(self, api_client, admin_user):
        """Try to retrieve with special characters."""
        api_client.force_authenticate(user=admin_user)
        
        special_chars = [
            "/api/v2/shows/test",
            "/api/v2/shows/ test ",
            "/api/v2/shows/test%20id",
            "/api/v2/shows/test&id=1",
        ]
        
        for url in special_chars:
            response = api_client.get(url)
            assert response.status_code in [404, 400]
