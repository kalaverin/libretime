"""
RED TEAM: T220 - ShowHosts LIST endpoint security tests.

Attack vectors:
- Anonymous LIST (authentication bypass)
- BOLA: list other users' show host assignments
- Filter injection (SQLi through show/user params)
- Information disclosure via error messages
- User enumeration via filter
"""

import json
import pytest
from model_bakery import baker

from api.schedule.models import Show, ShowHost


@pytest.mark.django_db(transaction=True)
class TestShowHostListAuthentication:
    """LIST authentication tests."""

    @pytest.mark.xfail(reason="T407: Anonymous LIST show hosts allowed")
    def test_list_without_auth(self, api_client):
        """Anonymous LIST should fail."""
        response = api_client.get("/api/v2/show-hosts")
        assert response.status_code in [401, 403], "Anonymous can list show hosts"


@pytest.mark.django_db(transaction=True)
class TestShowHostListBOLA:
    """LIST BOLA tests."""

    @pytest.mark.xfail(reason="T408: No owner filtering on ShowHost")
    def test_list_shows_only_own_hosts(self, api_client, admin_user, regular_user):
        """Verify list returns only user's own show hosts."""
        show1 = baker.make(Show, name="Admin Show")
        show2 = baker.make(Show, name="User Show")
        
        host1 = baker.make(ShowHost, show=show1)
        host2 = baker.make(ShowHost, show=show2)

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/show-hosts")

        assert response.status_code == 200
        data = response.json()
        host_ids = [d["id"] for d in data]
        
        assert host1.id not in host_ids, "List shows other users' show hosts (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestShowHostListUserEnumeration:
    """User enumeration via filter tests."""

    @pytest.mark.xfail(reason="T408: No owner filtering")
    def test_filter_by_other_user_id(self, api_client, regular_user, admin_user):
        """Try to filter by another user's ID to enumerate their shows."""
        # Create show host for admin
        show = baker.make(Show, name="Admin Show")
        host = baker.make(ShowHost, show=show)
        
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/show-hosts?user={admin_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0, "Can enumerate other user's shows via filter"

    def test_filter_by_invalid_user_id(self, api_client, admin_user):
        """Try filter by invalid user_id."""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get("/api/v2/show-hosts?user=invalid")
        if response.status_code == 500:
            pytest.fail("BUG: Filter crash on invalid user_id")


@pytest.mark.django_db(transaction=True)
class TestShowHostFilterInjection:
    """Filter parameter injection attacks."""

    def test_filter_by_invalid_show_id(self, api_client, admin_user):
        """Try to filter by invalid show_id."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/show-hosts?show=invalid")
        
        if response.status_code == 500:
            pytest.fail("BUG: Filter crashes on invalid show_id")
        assert response.status_code in [200, 400]

    def test_filter_by_sql_injection(self, api_client, admin_user):
        """Try SQL injection in show filter."""
        api_client.force_authenticate(user=admin_user)
        
        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_show_host;--",
            "1 UNION SELECT * FROM cc_subjs",
        ]
        
        for payload in sqli_payloads:
            response = api_client.get(f"/api/v2/show-hosts?show={payload}")
            if response.status_code == 500:
                pytest.fail(f"BUG: SQL injection causes crash: {payload}")

    def test_filter_by_negative_show_id(self, api_client, admin_user):
        """Try to filter by negative show_id."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/show-hosts?show=-1")
        
        assert response.status_code in [200, 400]

    def test_filter_sqli_in_user_param(self, api_client, admin_user):
        """Try SQL injection in user filter."""
        api_client.force_authenticate(user=admin_user)
        
        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_subjs;--",
        ]
        
        for payload in sqli_payloads:
            response = api_client.get(f"/api/v2/show-hosts?user={payload}")
            if response.status_code == 500:
                pytest.fail(f"BUG: SQLi in user filter: {payload}")


@pytest.mark.django_db(transaction=True)
class TestShowHostListInformationDisclosure:
    """Information disclosure attacks."""

    def test_error_message_on_invalid_filter(self, api_client, admin_user):
        """Check if error messages leak information."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v2/show-hosts?show=invalid")
        
        if response.status_code == 400:
            content = response.content.decode()
            leaked_terms = ["cc_show_host", "column", "sql", "table"]
            for term in leaked_terms:
                if term.lower() in content.lower():
                    pytest.fail(f"BUG: Error leaks info: {term}")


@pytest.mark.django_db(transaction=True)
class TestShowHostListMassAssignment:
    """Mass assignment via GET attacks."""

    def test_get_with_extra_parameters(self, api_client, admin_user):
        """Try GET with extra/malicious parameters."""
        api_client.force_authenticate(user=admin_user)
        
        # Try various malicious query params
        malicious_params = [
            "?id=99999&admin=true",
            "?__proto__=test",
        ]
        
        for params in malicious_params:
            response = api_client.get(f"/api/v2/show-hosts{params}")
            assert response.status_code in [200, 400]
