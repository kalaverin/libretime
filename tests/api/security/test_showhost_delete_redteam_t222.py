"""
RED TEAM: T222 - ShowHosts DELETE endpoint security tests.

Attack vectors:
- Anonymous DELETE (authentication bypass)
- BOLA: delete other users' show host assignments
- ID injection in DELETE
- Mass deletion
"""

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowHost


@pytest.mark.django_db(transaction=True)
class TestShowHostDeleteAuthentication:
    """DELETE authentication tests."""

    @pytest.mark.xfail(reason="T410: Anonymous DELETE show host allowed")
    def test_delete_without_auth(self, guest_client):
        """Anonymous DELETE should fail."""
        show = baker.make(Show, name="Test Show")
        user = baker.make("core.User")
        host = baker.make(ShowHost, show=show, user=user)

        response = guest_client.delete(f"/api/v2/show-hosts/{host.id}")
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can delete show hosts"


@pytest.mark.django_db(transaction=True)
class TestShowHostDeleteBOLA:
    """DELETE BOLA tests."""

    @pytest.mark.xfail(reason="T408: No owner filtering")
    def test_delete_other_user_host_assignment(
        self,
        guest_client,
        regular_user,
        admin_user,
    ):
        """Delete another user's host assignment."""
        show = baker.make(Show, name="Admin Show")
        host = baker.make(ShowHost, show=show, user=admin_user)
        host_id = host.id

        guest_client.force_authenticate(user=regular_user)
        response = guest_client.delete(f"/api/v2/show-hosts/{host_id}")
        assert response.status_code in [
            403,
            404,
        ], "Can delete other user's host assignment (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestShowHostDeleteIDInjection:
    """DELETE ID injection tests."""

    def test_delete_invalid_id_format(self, guest_client, admin_user):
        """Try DELETE with invalid ID format."""
        guest_client.force_authenticate(user=admin_user)

        invalid_ids = ["abc", "123'", "123--", "999999"]

        for invalid_id in invalid_ids:
            response = guest_client.delete(f"/api/v2/show-hosts/{invalid_id}")
            assert response.status_code in [
                404,
                400,
            ], f"Unexpected status for ID: {invalid_id}"

    def test_delete_sqli_in_id(self, guest_client, admin_user):
        """Try SQL injection in DELETE ID."""
        guest_client.force_authenticate(user=admin_user)

        sqli_ids = [
            "1; DROP TABLE cc_show_host;--",
            "1 OR 1=1",
        ]

        for sqli_id in sqli_ids:
            response = guest_client.delete(f"/api/v2/show-hosts/{sqli_id}")
            if response.status_code == 500:
                pytest.fail(f"BUG: SQLi in DELETE ID: {sqli_id}")


@pytest.mark.django_db(transaction=True)
class TestShowHostDeleteBusinessLogic:
    """DELETE business logic tests."""

    def test_double_delete(self, guest_client, admin_user):
        """Try to delete same host assignment twice."""
        show = baker.make(Show, name="Test Show")
        user = baker.make("core.User")
        host = baker.make(ShowHost, show=show, user=user)
        host_id = host.id

        guest_client.force_authenticate(user=admin_user)

        # First delete
        response1 = guest_client.delete(f"/api/v2/show-hosts/{host_id}")
        assert response1.status_code == 204

        # Second delete should fail
        response2 = guest_client.delete(f"/api/v2/show-hosts/{host_id}")
        assert response2.status_code == 404, "Double delete should return 404"

    def test_delete_preserves_other_hosts(self, guest_client, admin_user):
        """Verify deleting one host preserves others."""
        show = baker.make(Show, name="Test Show")
        user1 = baker.make("core.User")
        user2 = baker.make("core.User")

        host1 = baker.make(ShowHost, show=show, user=user1)
        host2 = baker.make(ShowHost, show=show, user=user2)

        guest_client.force_authenticate(user=admin_user)

        # Delete first host
        response = guest_client.delete(f"/api/v2/show-hosts/{host1.id}")
        assert response.status_code == 204

        # Second host should still exist
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM cc_show_hosts WHERE id = %s",
                [host2.id],
            )
            count = cursor.fetchone()[0]
            assert count == 1, "Other host was deleted"

    def test_delete_user_from_one_show_keeps_others(
        self,
        guest_client,
        admin_user,
    ):
        """Verify removing user from one show keeps other assignments."""
        show1 = baker.make(Show, name="Show 1")
        show2 = baker.make(Show, name="Show 2")
        user = baker.make("core.User")

        host1 = baker.make(ShowHost, show=show1, user=user)
        host2 = baker.make(ShowHost, show=show2, user=user)

        guest_client.force_authenticate(user=admin_user)

        # Remove from first show
        response = guest_client.delete(f"/api/v2/show-hosts/{host1.id}")
        assert response.status_code == 204

        # Second assignment should still exist
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM cc_show_hosts WHERE id = %s",
                [host2.id],
            )
            count = cursor.fetchone()[0]
            assert count == 1, "Other show assignment was deleted"
