"""
RED TEAM: T209 - ShowDays RETRIEVE/UPDATE/DELETE security tests.

Attack vectors:
- Anonymous RUD (authentication bypass)
- BOLA: RUD other users' show days
- Mass assignment: id, created_at modification via UPDATE
- SQL injection in UPDATE fields
- Time field manipulation via PATCH
- Delete other user's show days
"""

import json

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowDays


@pytest.mark.django_db(transaction=True)
class TestShowDaysRetrieveAuthentication:
    """RETRIEVE authentication tests."""

    @pytest.mark.xfail(reason="T388: Anonymous RETRIEVE allowed")
    def test_retrieve_without_auth(self, api_client):
        """Anonymous RETRIEVE should fail."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(ShowDays, show=show)

        response = api_client.get(f"/api/v2/show-days/{show_days.id}")
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can retrieve show days"


@pytest.mark.django_db(transaction=True)
class TestShowDaysRetrieveBOLA:
    """RETRIEVE BOLA tests."""

    @pytest.mark.xfail(reason="T389: No owner filtering on ShowDays")
    def test_retrieve_other_user_show_days(
        self,
        api_client,
        regular_user,
        admin_user,
    ):
        """Retrieve another user's show days."""
        show = baker.make(Show, name="Admin Show")
        show_days = baker.make(ShowDays, show=show)

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/show-days/{show_days.id}")
        assert response.status_code in [
            403,
            404,
        ], "Can retrieve other user's show days (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestShowDaysUpdateAuthentication:
    """UPDATE authentication tests."""

    @pytest.mark.xfail(reason="T393: Anonymous UPDATE allowed")
    def test_update_without_auth(self, api_client):
        """Anonymous UPDATE should fail."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(ShowDays, show=show)

        data = {"start_time": "20:00:00"}
        response = api_client.patch(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can update show days"

    @pytest.mark.xfail(reason="T393: Anonymous PUT allowed")
    def test_put_without_auth(self, api_client):
        """Anonymous PUT should fail."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(ShowDays, show=show)

        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "20:00:00",
            "timezone": "UTC",
            "duration": "02:00:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = api_client.put(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can PUT show days"


@pytest.mark.django_db(transaction=True)
class TestShowDaysUpdateBOLA:
    """UPDATE BOLA tests."""

    @pytest.mark.xfail(reason="T389: No owner filtering")
    def test_update_other_user_show_days(
        self,
        api_client,
        regular_user,
        admin_user,
    ):
        """Update another user's show days."""
        show = baker.make(Show, name="Admin Show")
        show_days = baker.make(ShowDays, show=show, start_time="10:00:00")

        api_client.force_authenticate(user=regular_user)
        data = {"start_time": "23:59:59"}
        response = api_client.patch(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            403,
            404,
        ], "Can update other user's show days (BOLA)"

    @pytest.mark.xfail(reason="T389: No owner filtering")
    def test_put_other_user_show_days(
        self,
        api_client,
        regular_user,
        admin_user,
    ):
        """PUT another user's show days."""
        show = baker.make(Show, name="Admin Show")
        show_days = baker.make(ShowDays, show=show)

        api_client.force_authenticate(user=regular_user)
        data = {
            "show": show.id,
            "first_show_on": "2026-04-01",
            "start_time": "23:59:59",
            "timezone": "UTC",
            "duration": "00:01:00",
            "repeat_kind": ShowDays.RepeatKind.WEEKLY,
        }
        response = api_client.put(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            403,
            404,
        ], "Can PUT other user's show days (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestShowDaysUpdateMassAssignment:
    """UPDATE mass assignment tests."""

    def test_update_id_field(self, api_client):
        """Try to change id via UPDATE."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(ShowDays, show=show)
        api_client.force_authenticate(user=baker.make("core.User"))

        original_id = show_days.id
        data = {"id": 99999}
        response = api_client.patch(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )

        show_days.refresh_from_db()
        assert (
            show_days.id == original_id
        ), "ID was changed via mass assignment"

    def test_update_created_at(self, api_client):
        """Try to change created_at via UPDATE."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(ShowDays, show=show)
        api_client.force_authenticate(user=baker.make("core.User"))

        data = {"created_at": "2020-01-01T00:00:00Z"}
        response = api_client.patch(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            result = response.json()
            assert not result.get("created_at", "").startswith(
                "2020",
            ), "created_at was changed via mass assignment"


@pytest.mark.django_db(transaction=True)
class TestShowDaysUpdateSQLInjection:
    """UPDATE SQL injection tests."""

    sqli_payloads = [
        "1' OR '1'='1",
        "1; DROP TABLE cc_show_days;--",
        "1' AND 1=1--",
    ]

    def test_update_sqli_in_start_time(self, api_client, admin_user):
        """SQL injection in PATCH start_time."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(ShowDays, show=show)
        api_client.force_authenticate(user=admin_user)

        for payload in self.sqli_payloads:
            data = {"start_time": payload}
            response = api_client.patch(
                f"/api/v2/show-days/{show_days.id}",
                json.dumps(data),
                content_type="application/json",
            )
            assert (
                response.status_code != 500
            ), f"SQLi crash in start_time: {payload}"

    def test_update_sqli_in_timezone(self, api_client, admin_user):
        """SQL injection in PATCH timezone."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(ShowDays, show=show)
        api_client.force_authenticate(user=admin_user)

        for payload in self.sqli_payloads:
            data = {"timezone": payload}
            response = api_client.patch(
                f"/api/v2/show-days/{show_days.id}",
                json.dumps(data),
                content_type="application/json",
            )
            assert (
                response.status_code != 500
            ), f"SQLi crash in timezone: {payload}"


@pytest.mark.django_db(transaction=True)
class TestShowDaysUpdateTimeManipulation:
    """UPDATE time manipulation tests."""

    @pytest.mark.xfail(reason="T395: Negative duration accepted")
    def test_update_to_negative_duration(self, api_client):
        """Try to set negative duration via PATCH."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(ShowDays, show=show, duration="01:00:00")
        api_client.force_authenticate(user=baker.make("core.User"))

        data = {"duration": "-02:00:00"}
        response = api_client.patch(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            show_days.refresh_from_db()
            assert (
                show_days.duration != "-02:00:00"
            ), "Negative duration accepted"

    def test_update_invalid_week_day(self, api_client):
        """Try to set invalid week_day via PATCH."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(ShowDays, show=show, week_day=1)
        api_client.force_authenticate(user=baker.make("core.User"))

        data = {"week_day": 99}
        response = api_client.patch(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            show_days.refresh_from_db()
            assert show_days.week_day != 99, "Invalid week_day accepted"

    @pytest.mark.xfail(reason="last_show_on before first_show_on accepted via PATCH")
    def test_update_last_show_before_first(self, api_client):
        """Try to set last_show_on before first_show_on."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(
            ShowDays,
            show=show,
            first_show_on="2026-06-01",
            last_show_on="2026-08-01",
        )
        api_client.force_authenticate(user=baker.make("core.User"))

        data = {"last_show_on": "2026-01-01"}
        response = api_client.patch(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            pytest.fail(
                "BUG: last_show_on before first_show_on accepted via PATCH",
            )


@pytest.mark.django_db(transaction=True)
class TestShowDaysUpdateRepeatAbuse:
    """UPDATE repeat options abuse."""

    @pytest.mark.xfail(reason="T392: repeat_next_on mutable")
    def test_update_repeat_next_on(self, api_client):
        """Try to manipulate repeat_next_on via PATCH."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(ShowDays, show=show)
        api_client.force_authenticate(user=baker.make("core.User"))

        data = {"repeat_next_on": "2040-12-31"}
        response = api_client.patch(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            result = response.json()
            assert (
                result.get("repeat_next_on") != "2040-12-31"
            ), "repeat_next_on can be manipulated via PATCH"

    def test_update_invalid_repeat_kind(self, api_client):
        """Try to set invalid repeat_kind."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(
            ShowDays,
            show=show,
            repeat_kind=ShowDays.RepeatKind.WEEKLY,
        )
        api_client.force_authenticate(user=baker.make("core.User"))

        data = {"repeat_kind": "INVALID_KIND"}
        response = api_client.patch(
            f"/api/v2/show-days/{show_days.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            pytest.fail("BUG: Invalid repeat_kind accepted via PATCH")


@pytest.mark.django_db(transaction=True)
class TestShowDaysDeleteAuthentication:
    """DELETE authentication tests."""

    @pytest.mark.xfail(reason="T394: Anonymous DELETE allowed")
    def test_delete_without_auth(self, api_client):
        """Anonymous DELETE should fail."""
        show = baker.make(Show, name="Test Show")
        show_days = baker.make(ShowDays, show=show)

        response = api_client.delete(f"/api/v2/show-days/{show_days.id}")
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can delete show days"


@pytest.mark.django_db(transaction=True)
class TestShowDaysDeleteBOLA:
    """DELETE BOLA tests."""

    @pytest.mark.xfail(reason="T389: No owner filtering")
    def test_delete_other_user_show_days(
        self,
        api_client,
        regular_user,
        admin_user,
    ):
        """Delete another user's show days."""
        show = baker.make(Show, name="Admin Show")
        show_days = baker.make(ShowDays, show=show)
        show_days_id = show_days.id

        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(f"/api/v2/show-days/{show_days_id}")
        assert response.status_code in [
            403,
            404,
        ], "Can delete other user's show days (BOLA)"
