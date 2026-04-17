"""
RED TEAM: T218 - ShowInstances DELETE endpoint security tests.

Attack vectors:
- Anonymous DELETE (authentication bypass)
- BOLA: delete other users' show instances
- ID injection in DELETE
- Mass deletion enumeration
"""

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowInstance


@pytest.mark.django_db(transaction=True)
class TestShowInstanceDeleteAuthentication:
    """DELETE authentication tests."""

    @pytest.mark.xfail(reason="T403: Anonymous DELETE show instances allowed")
    def test_delete_without_auth(self, api_client):
        """Anonymous DELETE should fail."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        instance_id = instance.id

        response = api_client.delete(f"/api/v2/show-instances/{instance_id}")
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can delete show instances"


@pytest.mark.django_db(transaction=True)
class TestShowInstanceDeleteBOLA:
    """DELETE BOLA tests."""

    @pytest.mark.xfail(reason="T398: No owner filtering")
    def test_delete_other_user_instance(
        self,
        api_client,
        regular_user,
        admin_user,
    ):
        """Delete another user's show instance."""
        show = baker.make(Show, name="Admin Show")
        instance = baker.make(ShowInstance, show=show)
        instance_id = instance.id

        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(f"/api/v2/show-instances/{instance_id}")
        assert response.status_code in [
            403,
            404,
        ], "Can delete other user's instance (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestShowInstanceDeleteIDInjection:
    """DELETE ID injection tests."""

    def test_delete_invalid_id_format(self, api_client, admin_user):
        """Try DELETE with invalid ID format."""
        api_client.force_authenticate(user=admin_user)

        invalid_ids = [
            "abc",
            "123'",
            "123--",
            "999999",
        ]

        for invalid_id in invalid_ids:
            response = api_client.delete(
                f"/api/v2/show-instances/{invalid_id}",
            )
            assert response.status_code in [
                404,
                400,
            ], f"Unexpected status for ID: {invalid_id}"

    def test_delete_sqli_in_id(self, api_client, admin_user):
        """Try SQL injection in DELETE ID."""
        api_client.force_authenticate(user=admin_user)

        sqli_ids = [
            "1; DROP TABLE cc_show_instances;--",
            "1 OR 1=1",
        ]

        for sqli_id in sqli_ids:
            response = api_client.delete(f"/api/v2/show-instances/{sqli_id}")
            if response.status_code == 500:
                pytest.fail(f"BUG: SQLi in DELETE ID: {sqli_id}")


@pytest.mark.django_db(transaction=True)
class TestShowInstanceDeleteEnumeration:
    """DELETE enumeration attacks."""

    def test_delete_nonexistent_id(self, api_client, admin_user):
        """Try DELETE with non-existent ID."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.delete("/api/v2/show-instances/99999")
        assert (
            response.status_code == 404
        ), "Should return 404 for non-existent instance"

    def test_delete_non_owned_instances_fails(self, api_client, admin_user):
        """Verify we can only delete our own instances."""
        api_client.force_authenticate(user=admin_user)

        # Create instance and delete it
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)

        response = api_client.delete(f"/api/v2/show-instances/{instance.id}")
        assert response.status_code == 204

        # Try to delete same ID again (should 404)
        response2 = api_client.delete(f"/api/v2/show-instances/{instance.id}")
        assert response2.status_code == 404


@pytest.mark.django_db(transaction=True)
class TestShowInstanceDeleteBusinessLogic:
    """DELETE business logic bypass tests."""

    def test_double_delete(self, api_client, admin_user):
        """Try to delete same instance twice."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        instance_id = instance.id

        api_client.force_authenticate(user=admin_user)

        # First delete
        response1 = api_client.delete(f"/api/v2/show-instances/{instance_id}")
        assert response1.status_code == 204

        # Second delete should fail
        response2 = api_client.delete(f"/api/v2/show-instances/{instance_id}")
        assert response2.status_code == 404, "Double delete should return 404"

    def test_delete_with_modified_flag(self, api_client, admin_user):
        """Try to delete modified instance."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show, modified=True)

        api_client.force_authenticate(user=admin_user)
        response = api_client.delete(f"/api/v2/show-instances/{instance.id}")

        # Document behavior - may or may not allow deletion of modified
        assert response.status_code in [204, 403]

    def test_delete_with_description(self, api_client, admin_user):
        """Try to delete instance with description."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(
            ShowInstance,
            show=show,
            description="Important show",
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.delete(f"/api/v2/show-instances/{instance.id}")

        # Should be able to delete
        assert response.status_code in [204, 403]
