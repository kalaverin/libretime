"""
RED TEAM: T215 - ShowInstances LIST endpoint security tests.

Attack vectors:
- Anonymous LIST (authentication bypass)
- BOLA: list other users' show instances
- Filter injection (SQLi through show param)
- Information disclosure via error messages
- Mass assignment via GET
"""

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowInstance


@pytest.mark.django_db(transaction=True)
class TestShowInstanceListAuthentication:
    """LIST authentication tests."""

    @pytest.mark.xfail(reason="T397: Anonymous LIST show instances allowed")
    def test_list_without_auth(self, admin_client):
        """Anonymous LIST should fail."""
        response = admin_client.get("/api/v2/show-instances")
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can list show instances"


@pytest.mark.django_db(transaction=True)
class TestShowInstanceListBOLA:
    """LIST BOLA tests."""

    @pytest.mark.xfail(reason="T398: No owner filtering on ShowInstance")
    def test_list_shows_only_own_instances(
        self,
        admin_client,
        admin_user,
        regular_user,
    ):
        """Verify list returns only user's own show instances."""
        show1 = baker.make(Show, name="Admin Show")
        show2 = baker.make(Show, name="User Show")

        instance1 = baker.make(ShowInstance, show=show1)
        instance2 = baker.make(ShowInstance, show=show2)

        admin_client.force_authenticate(user=regular_user)
        response = admin_client.get("/api/v2/show-instances")

        assert response.status_code == 200
        data = response.json()
        instance_ids = [d["id"] for d in data]

        assert (
            instance1.id not in instance_ids
        ), "List shows other users' instances (BOLA)"

    @pytest.mark.xfail(reason="T399: BOLA via show filter")
    def test_filter_by_other_user_show(
        self,
        admin_client,
        admin_user,
        regular_user,
    ):
        """Try to filter by another user's show."""
        show = baker.make(Show, name="Admin Show")
        instance = baker.make(ShowInstance, show=show)

        admin_client.force_authenticate(user=regular_user)
        response = admin_client.get(f"/api/v2/show-instances?show={show.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0, "Can filter by other user's show (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestShowInstanceFilterInjection:
    """Filter parameter injection attacks."""

    def test_filter_by_invalid_show_id(self, admin_client, admin_user):
        """Try to filter by invalid show_id."""
        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/show-instances?show=invalid")

        if response.status_code == 500:
            pytest.fail("BUG: Filter crashes on invalid show_id")
        assert response.status_code in [200, 400]

    def test_filter_by_sql_injection(self, admin_client, admin_user):
        """Try SQL injection in show filter."""
        admin_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_show_instances;--",
            "1 UNION SELECT * FROM cc_subjs",
        ]

        for payload in sqli_payloads:
            response = admin_client.get(f"/api/v2/show-instances?show={payload}")
            if response.status_code == 500:
                pytest.fail(f"BUG: SQL injection causes crash: {payload}")

    def test_filter_by_negative_show_id(self, admin_client, admin_user):
        """Try to filter by negative show_id."""
        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/show-instances?show=-1")

        assert response.status_code in [200, 400]


@pytest.mark.django_db(transaction=True)
class TestShowInstanceListInformationDisclosure:
    """Information disclosure attacks."""

    def test_error_message_on_invalid_filter(self, admin_client, admin_user):
        """Check if error messages leak information."""
        admin_client.force_authenticate(user=admin_user)
        response = admin_client.get("/api/v2/show-instances?show=invalid")

        if response.status_code == 400:
            content = response.content.decode()
            leaked_terms = ["cc_show_instances", "column", "sql", "table"]
            for term in leaked_terms:
                if term.lower() in content.lower():
                    pytest.fail(f"BUG: Error leaks info: {term}")


@pytest.mark.django_db(transaction=True)
class TestShowInstanceListMassAssignment:
    """Mass assignment via GET attacks."""

    def test_get_with_extra_parameters(self, admin_client, admin_user):
        """Try GET with extra/malicious parameters."""
        admin_client.force_authenticate(user=admin_user)

        # Try various malicious query params
        malicious_params = [
            "?id=99999&admin=true",
            "?__proto__=test",
            "?constructor=test",
        ]

        for params in malicious_params:
            response = admin_client.get(f"/api/v2/show-instances{params}")
            # Should not crash or expose unexpected data
            assert response.status_code in [200, 400]
