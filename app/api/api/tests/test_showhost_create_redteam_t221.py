"""
RED TEAM: T221 - ShowHosts CREATE endpoint security tests.

Attack vectors:
- Anonymous CREATE (authentication bypass)
- BOLA: create host for other user's show
- Mass assignment: id manipulation
- Duplicate assignment abuse
- Self-assignment vs admin assignment
"""

import json

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowHost


@pytest.mark.django_db(transaction=True)
class TestShowHostCreateAuthentication:
    """CREATE authentication tests."""

    @pytest.mark.xfail(reason="T409: Anonymous CREATE show host allowed")
    def test_create_without_auth(self, api_client):
        """Anonymous CREATE should fail."""
        show = baker.make(Show, name="Test Show")
        user = baker.make("core.User")

        data = {"show": show.id, "user": user.id}
        response = api_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can create show hosts"


@pytest.mark.django_db(transaction=True)
class TestShowHostCreateBOLA:
    """CREATE BOLA tests."""

    @pytest.mark.xfail(reason="T408: No owner filtering")
    def test_create_for_other_user_show(
        self, api_client, regular_user, admin_user,
    ):
        """Create host for another user's show."""
        show = baker.make(Show, name="Admin Show")

        api_client.force_authenticate(user=regular_user)
        data = {"show": show.id, "user": regular_user.id}
        response = api_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            403,
            400,
        ], "Can create host for other user's show (BOLA)"

    @pytest.mark.xfail(reason="T408: No owner filtering")
    def test_assign_other_user_as_host(
        self, api_client, regular_user, admin_user,
    ):
        """Assign another user as host without their consent."""
        show = baker.make(Show, name="User Show")

        api_client.force_authenticate(user=regular_user)
        data = {"show": show.id, "user": admin_user.id}  # Assign admin as host
        response = api_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            403,
            400,
        ], "Can assign other user as host without consent"


@pytest.mark.django_db(transaction=True)
class TestShowHostCreateMassAssignment:
    """CREATE mass assignment tests."""

    def test_create_with_id_field(self, api_client):
        """Try to set id during CREATE."""
        show = baker.make(Show, name="Test Show")
        user = baker.make("core.User")
        api_client.force_authenticate(user=baker.make("core.User"))

        data = {"id": 99999, "show": show.id, "user": user.id}
        response = api_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 201:
            result = response.json()
            assert result.get("id") != 99999, "ID was set via mass assignment"


@pytest.mark.django_db(transaction=True)
class TestShowHostCreateDuplicateAbuse:
    """Duplicate assignment abuse tests."""

    @pytest.mark.xfail(reason="T320: Duplicate entries allowed")
    def test_create_duplicate_host_assignment(self, api_client):
        """Try to create duplicate host assignment."""
        show = baker.make(Show, name="Test Show")
        user = baker.make("core.User")
        api_client.force_authenticate(user=baker.make("core.User"))

        # Create first assignment
        baker.make(ShowHost, show=show, user=user)

        # Try to create duplicate
        data = {"show": show.id, "user": user.id}
        response = api_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            400,
            409,
        ], "Duplicate host assignment allowed"

    def test_create_multiple_hosts_for_show(self, api_client):
        """Create many hosts for same show."""
        show = baker.make(Show, name="Test Show")
        api_client.force_authenticate(user=baker.make("core.User"))

        created = 0
        for i in range(50):  # Try to create 50 hosts
            user = baker.make("core.User")
            data = {"show": show.id, "user": user.id}
            response = api_client.post(
                "/api/v2/show-hosts",
                json.dumps(data),
                content_type="application/json",
            )
            if response.status_code == 201:
                created += 1

        # Should allow multiple different hosts
        assert created == 50, f"Only created {created} hosts, expected 50"


@pytest.mark.django_db(transaction=True)
class TestShowHostCreateValidation:
    """CREATE validation bypass tests."""

    def test_create_with_null_show(self, api_client):
        """Try CREATE with null show."""
        user = baker.make("core.User")
        api_client.force_authenticate(user=baker.make("core.User"))

        data = {"show": None, "user": user.id}
        response = api_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Null show accepted")

    def test_create_with_null_user(self, api_client):
        """Try CREATE with null user."""
        show = baker.make(Show, name="Test Show")
        api_client.force_authenticate(user=baker.make("core.User"))

        data = {"show": show.id, "user": None}
        response = api_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Null user accepted")

    def test_create_with_nonexistent_show(self, api_client):
        """Try CREATE with non-existent show."""
        user = baker.make("core.User")
        api_client.force_authenticate(user=baker.make("core.User"))

        data = {"show": 99999, "user": user.id}
        response = api_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Non-existent show accepted")

    def test_create_with_nonexistent_user(self, api_client):
        """Try CREATE with non-existent user."""
        show = baker.make(Show, name="Test Show")
        api_client.force_authenticate(user=baker.make("core.User"))

        data = {"show": show.id, "user": 99999}
        response = api_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Non-existent user accepted")


@pytest.mark.django_db(transaction=True)
class TestShowHostCreateSelfAssignment:
    """Self-assignment vs admin assignment tests."""

    def test_self_assign_as_host(self, api_client, regular_user):
        """User assigns themselves as host."""
        show = baker.make(Show, name="Test Show")

        api_client.force_authenticate(user=regular_user)
        data = {"show": show.id, "user": regular_user.id}
        response = api_client.post(
            "/api/v2/show-hosts",
            json.dumps(data),
            content_type="application/json",
        )
        # Document behavior - may or may not allow self-assignment
        assert response.status_code in [201, 403]
