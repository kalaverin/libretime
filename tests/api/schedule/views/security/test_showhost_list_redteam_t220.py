"""
RED TEAM: T220 - ShowHosts LIST endpoint security tests.

Attack vectors:
- Anonymous LIST (authentication bypass)
- BOLA: list other users' show host assignments
- Filter injection (SQLi through show/user params)
- Information disclosure via error messages
- User enumeration via filter
"""

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowHost


@pytest.mark.django_db(transaction=True)
class TestShowHostListAuthentication:
    """LIST authentication tests."""

    @pytest.mark.xfail(reason="T407: Anonymous LIST show hosts allowed")
    def test_list_without_auth(self, admin_client):
        """Anonymous LIST should fail."""
        response = admin_client.get("/api/v2/show-hosts")
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can list show hosts"


@pytest.mark.django_db(transaction=True)
class TestShowHostListBOLA:
    """LIST BOLA tests."""

    @pytest.mark.xfail(reason="BOLA: LIST shows all show hosts")
    def test_list_shows_only_own_hosts(
        self,
        admin_client,
        admin_user,
        regular_user,
    ):
        """BOLA FIX: List returns only user's own show host assignments."""
        show1 = baker.make(Show, name="Admin Show")
        show2 = baker.make(Show, name="User Show")

        # Create host assignments - regular_user is only host of show2
        baker.make(ShowHost, show=show1, user=admin_user)
        host2 = baker.make(ShowHost, show=show2, user=regular_user)

        admin_client.force_authenticate(user=regular_user)
        response = admin_client.get("/api/v2/show-hosts")

        assert response.status_code == 200
        data = response.json()
        host_ids = [d["id"] for d in data]

        # Should only see own assignment (host2), not admin's
        assert (
            len(host_ids) == 1
        ), f"Expected 1 assignment, got {len(host_ids)}"
        assert host2.id in host_ids, "Own assignment not found"


@pytest.mark.django_db(transaction=True)
class TestShowHostListUserEnumeration:
    """User enumeration via filter tests."""

    @pytest.mark.xfail(reason="BOLA: Filter by user does not scope to requesting user")
    def test_filter_by_other_user_id_returns_only_own(
        self,
        admin_client,
        regular_user,
        admin_user,
    ):
        """BOLA FIX: Filter by other user ID only returns own assignments."""
        # Create show host assignments
        admin_show = baker.make(Show, name="Admin Show")
        user_show = baker.make(Show, name="User Show")
        baker.make(ShowHost, show=admin_show, user=admin_user)
        baker.make(ShowHost, show=user_show, user=regular_user)

        admin_client.force_authenticate(user=regular_user)
        # Try to filter by admin's user ID - should only see own assignments
        response = admin_client.get(f"/api/v2/show-hosts?user={admin_user.id}")

        assert response.status_code == 200
        data = response.json()
        # Even with filter for admin, only sees own assignments
        assert (
            len(data) == 1
        ), "Can enumerate other user's shows via filter (BOLA)"

    def test_filter_by_invalid_user_id(self, admin_client, admin_user):
        """Try filter by invalid user_id."""
        admin_client.force_authenticate(user=admin_user)

        response = admin_client.get("/api/v2/show-hosts?user=invalid")
        if response.status_code == 500:
            pytest.fail("BUG: Filter crash on invalid user_id")


@pytest.mark.django_db(transaction=True)
class TestShowHostFilterInjection:
    """Filter parameter injection attacks."""

    def test_filter_by_invalid_show_id(self, admin_client, admin_user):
        """Try to filter by invalid show_id."""
        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/show-hosts?show=invalid")

        if response.status_code == 500:
            pytest.fail("BUG: Filter crashes on invalid show_id")
        assert response.status_code in [200, 400]

    def test_filter_by_sql_injection(self, admin_client, admin_user):
        """Try SQL injection in show filter."""
        admin_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_show_host;--",
            "1 UNION SELECT * FROM cc_subjs",
        ]

        for payload in sqli_payloads:
            response = admin_client.get(f"/api/v2/show-hosts?show={payload}")
            if response.status_code == 500:
                pytest.fail(f"BUG: SQL injection causes crash: {payload}")

    def test_filter_by_negative_show_id(self, admin_client, admin_user):
        """Try to filter by negative show_id."""
        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/show-hosts?show=-1")

        assert response.status_code in [200, 400]

    def test_filter_sqli_in_user_param(self, admin_client, admin_user):
        """Try SQL injection in user filter."""
        admin_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_subjs;--",
        ]

        for payload in sqli_payloads:
            response = admin_client.get(f"/api/v2/show-hosts?user={payload}")
            if response.status_code == 500:
                pytest.fail(f"BUG: SQLi in user filter: {payload}")


@pytest.mark.django_db(transaction=True)
class TestShowHostListInformationDisclosure:
    """Information disclosure attacks."""

    def test_error_message_on_invalid_filter(self, admin_client, admin_user):
        """Check if error messages leak information."""
        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/show-hosts?show=invalid")

        if response.status_code == 400:
            content = response.content.decode()
            leaked_terms = ["cc_show_host", "column", "sql", "table"]
            for term in leaked_terms:
                if term.lower() in content.lower():
                    pytest.fail(f"BUG: Error leaks info: {term}")


@pytest.mark.django_db(transaction=True)
class TestShowHostListMassAssignment:
    """Mass assignment via GET attacks."""

    def test_get_with_extra_parameters(self, admin_client, admin_user):
        """Try GET with extra/malicious parameters."""
        admin_client.force_authenticate(user=admin_user)

        # Try various malicious query params
        malicious_params = [
            "?id=99999&admin=true",
            "?__proto__=test",
        ]

        for params in malicious_params:
            response = admin_client.get(f"/api/v2/show-hosts{params}")
            assert response.status_code in [200, 400]
