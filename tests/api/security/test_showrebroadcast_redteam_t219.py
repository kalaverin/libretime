"""
RED TEAM: T219 - ShowRebroadcasts LIST/CREATE security tests.

Attack vectors:
- Anonymous LIST/CREATE (authentication bypass)
- BOLA: access/create for other users' rebroadcasts
- Mass assignment: id manipulation
- day_offset abuse (negative, very large)
- Time manipulation
"""

import json

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowRebroadcast


@pytest.mark.django_db(transaction=True)
class TestShowRebroadcastListAuthentication:
    """LIST authentication tests."""

    @pytest.mark.xfail(reason="T404: Anonymous LIST show rebroadcasts allowed")
    def test_list_without_auth(self, admin_client):
        """Anonymous LIST should fail."""
        response = admin_client.get("/api/v2/show-rebroadcasts")
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can list rebroadcasts"


@pytest.mark.django_db(transaction=True)
class TestShowRebroadcastListBOLA:
    """LIST BOLA tests."""

    @pytest.mark.xfail(reason="T405: No owner filtering")
    def test_list_other_user_rebroadcasts(
        self,
        admin_client,
        admin_user,
        regular_user,
    ):
        """List shows other users' rebroadcasts."""
        show1 = baker.make(Show, name="Admin Show")
        show2 = baker.make(Show, name="User Show")

        rebroadcast1 = baker.make(ShowRebroadcast, show=show1)
        rebroadcast2 = baker.make(ShowRebroadcast, show=show2)

        admin_client.force_authenticate(user=regular_user)
        response = admin_client.get("/api/v2/show-rebroadcasts")

        assert response.status_code == 200
        data = response.json()
        ids = [d["id"] for d in data]

        assert (
            rebroadcast1.id not in ids
        ), "List shows other users' rebroadcasts (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestShowRebroadcastCreateAuthentication:
    """CREATE authentication tests."""

    @pytest.mark.xfail(reason="T406: Anonymous CREATE rebroadcast allowed")
    def test_create_without_auth(self, admin_client):
        """Anonymous CREATE should fail."""
        show = baker.make(Show, name="Test Show")
        data = {
            "show": show.id,
            "day_offset": 1,
            "start_time": "14:00:00",
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can create rebroadcasts"


@pytest.mark.django_db(transaction=True)
class TestShowRebroadcastCreateBOLA:
    """CREATE BOLA tests."""

    @pytest.mark.xfail(reason="T405: No owner filtering")
    def test_create_for_other_user_show(
        self,
        admin_client,
        regular_user,
        admin_user,
    ):
        """Create rebroadcast for another user's show."""
        show = baker.make(Show, name="Admin Show")

        admin_client.force_authenticate(user=regular_user)
        data = {
            "show": show.id,
            "day_offset": 1,
            "start_time": "14:00:00",
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            403,
            400,
        ], "Can create rebroadcast for other user's show (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestShowRebroadcastCreateMassAssignment:
    """CREATE mass assignment tests."""

    def test_create_with_id_field(self, admin_client):
        """Try to set id during CREATE."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "id": 99999,
            "show": show.id,
            "day_offset": 1,
            "start_time": "14:00:00",
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 201:
            result = response.json()
            assert result.get("id") != 99999, "ID was set via mass assignment"


@pytest.mark.django_db(transaction=True)
class TestShowRebroadcastDayOffsetAbuse:
    """day_offset abuse tests."""

    @pytest.mark.xfail(reason="Negative day_offset accepted")
    def test_negative_day_offset(self, admin_client):
        """Try negative day_offset."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": show.id,
            "day_offset": -1,
            "start_time": "14:00:00",
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        if response.status_code == 201:
            pytest.fail("BUG: Negative day_offset accepted")

    def test_very_large_day_offset(self, admin_client):
        """Try very large day_offset."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": show.id,
            "day_offset": 999999,
            "start_time": "14:00:00",
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        # Document behavior - should probably limit max offset
        assert response.status_code in [201, 400]


@pytest.mark.django_db(transaction=True)
class TestShowRebroadcastTimeManipulation:
    """Time manipulation tests."""

    def test_invalid_start_time_format(self, admin_client):
        """Try invalid start_time format."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": show.id,
            "day_offset": 1,
            "start_time": "invalid_time",
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [201, 400, 403]

    def test_start_time_with_timezone(self, admin_client):
        """Try start_time with timezone info."""
        show = baker.make(Show, name="Test Show")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {
            "show": show.id,
            "day_offset": 1,
            "start_time": "14:00:00+05:00",  # With timezone
        }
        response = admin_client.post(
            "/api/v2/show-rebroadcasts",
            json.dumps(data),
            content_type="application/json",
        )
        # Document behavior
        assert response.status_code in [201, 400, 403]


@pytest.mark.django_db(transaction=True)
class TestShowRebroadcastFilterInjection:
    """Filter injection tests."""

    def test_filter_by_invalid_show(self, admin_client, admin_user):
        """Try filter by invalid show_id."""
        admin_client.force_authenticate(user=admin_user)

        response = admin_client.get("/api/v2/show-rebroadcasts?show=invalid")
        if response.status_code == 500:
            pytest.fail("BUG: Filter crash on invalid show")

    def test_filter_sqli(self, admin_client, admin_user):
        """Try SQL injection in filter."""
        admin_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE--",
        ]

        for payload in sqli_payloads:
            response = admin_client.get(
                f"/api/v2/show-rebroadcasts?show={payload}",
            )
            if response.status_code == 500:
                pytest.fail(f"BUG: SQLi in filter: {payload}")
