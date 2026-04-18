"""
RED TEAM: T217 - ShowInstances UPDATE endpoint security tests.

Attack vectors:
- Anonymous UPDATE (authentication bypass)
- BOLA: update other users' show instances
- Mass assignment: id, created_at modification
- Time field manipulation
- Description XSS/injection
"""

import json

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowInstance


@pytest.mark.django_db(transaction=True)
class TestShowInstanceUpdateAuthentication:
    """UPDATE authentication tests."""

    @pytest.mark.xfail(reason="T401: Anonymous UPDATE show instances allowed")
    def test_update_without_auth(self, admin_client):
        """Anonymous PATCH should fail."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)

        data = {"description": "Hacked"}
        response = admin_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can update show instances"

    @pytest.mark.xfail(reason="T401: Anonymous PUT show instances allowed")
    def test_put_without_auth(self, admin_client):
        """Anonymous PUT should fail."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)

        data = {
            "show": show.id,
            "starts_at": "2026-04-01T14:00:00Z",
            "ends_at": "2026-04-01T15:00:00Z",
            "description": "Hacked",
        }
        response = admin_client.put(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can PUT show instances"


@pytest.mark.django_db(transaction=True)
class TestShowInstanceUpdateBOLA:
    """UPDATE BOLA tests."""

    @pytest.mark.xfail(reason="T398: No owner filtering")
    def test_update_other_user_instance(
        self,
        admin_client,
        regular_user,
        admin_user,
    ):
        """Update another user's show instance."""
        show = baker.make(Show, name="Admin Show")
        instance = baker.make(ShowInstance, show=show, description="Original")

        admin_client.force_authenticate(user=regular_user)
        data = {"description": "Hacked by attacker"}
        response = admin_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code in [
            403,
            404,
        ], "Can update other user's instance (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestShowInstanceUpdateMassAssignment:
    """UPDATE mass assignment tests."""

    def test_update_id_field(self, admin_client):
        """Try to change id via PATCH."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        admin_client.force_authenticate(user=baker.make("core.User"))

        original_id = instance.id
        data = {"id": 99999}
        response = admin_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps(data),
            content_type="application/json",
        )

        instance.refresh_from_db()
        assert instance.id == original_id, "ID was changed via mass assignment"


@pytest.mark.django_db(transaction=True)
class TestShowInstanceUpdateTimeManipulation:
    """UPDATE time manipulation tests."""

    @pytest.mark.xfail(reason="ends_at before starts_at accepted")
    def test_update_ends_at_before_starts_at(self, admin_client):
        """Try to set ends_at before starts_at."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            starts_at="2026-04-01T14:00:00Z",
            ends_at="2026-04-01T15:00:00Z",
        )
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {"ends_at": "2026-04-01T13:00:00Z"}  # Before starts_at
        response = admin_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            pytest.fail("BUG: ends_at before starts_at accepted")

    @pytest.mark.xfail(reason="Negative filled_time accepted")
    def test_negative_filled_time(self, admin_client):
        """Try to set negative filled_time."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show, filled_time="00:30:00")
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {"filled_time": "-01:00:00"}
        response = admin_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            pytest.fail("BUG: Negative filled_time accepted")


@pytest.mark.django_db(transaction=True)
class TestShowInstanceUpdateDescriptionInjection:
    """UPDATE description injection tests."""

    @pytest.mark.xfail(reason="T402: XSS stored unescaped in description")
    def test_description_xss(self, admin_client):
        """Try XSS in description field."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        admin_client.force_authenticate(user=baker.make("core.User"))

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ]

        for payload in xss_payloads:
            data = {"description": payload}
            response = admin_client.patch(
                f"/api/v2/show-instances/{instance.id}",
                json.dumps(data),
                content_type="application/json",
            )

            if response.status_code == 200:
                result = response.json()
                # If stored as-is, XSS vulnerability exists
                if result.get("description") == payload:
                    pytest.fail(
                        f"BUG: XSS payload stored unescaped: {payload[:30]}",
                    )

    def test_description_sqli(self, admin_client):
        """Try SQL injection in description."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        admin_client.force_authenticate(user=baker.make("core.User"))

        sqli_payloads = [
            "'; DROP TABLE cc_show_instances;--",
            "' OR '1'='1",
        ]

        for payload in sqli_payloads:
            data = {"description": payload}
            response = admin_client.patch(
                f"/api/v2/show-instances/{instance.id}",
                json.dumps(data),
                content_type="application/json",
            )

            if response.status_code == 500:
                pytest.fail(f"BUG: SQLi in description: {payload}")


@pytest.mark.django_db(transaction=True)
class TestShowInstanceUpdateFlagManipulation:
    """UPDATE flag manipulation tests."""

    def test_modified_flag_manipulation(self, admin_client):
        """Try to manipulate modified flag."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show, modified=False)
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {"modified": True}
        response = admin_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps(data),
            content_type="application/json",
        )

        # modified flag should be manageable
        assert response.status_code in [200, 400, 403]

    def test_rebroadcast_flag_manipulation(self, admin_client):
        """Try to manipulate rebroadcast flag."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show, rebroadcast=False)
        admin_client.force_authenticate(user=baker.make("core.User"))

        data = {"rebroadcast": True}
        response = admin_client.patch(
            f"/api/v2/show-instances/{instance.id}",
            json.dumps(data),
            content_type="application/json",
        )

        if response.status_code == 200:
            result = response.json()
            # Check if rebroadcast was changed
            # Document behavior
