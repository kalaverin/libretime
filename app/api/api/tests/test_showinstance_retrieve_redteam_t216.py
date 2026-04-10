"""
RED TEAM: T216 - ShowInstances RETRIEVE endpoint security tests.

Attack vectors:
- Anonymous RETRIEVE (authentication bypass)
- BOLA: retrieve other users' show instances
- ID manipulation (sequential ID enumeration)
- Information disclosure via error messages
"""

import pytest

from model_bakery import baker

from api.schedule.models import Show, ShowInstance


@pytest.mark.django_db(transaction=True)
class TestShowInstanceRetrieveAuthentication:
    """RETRIEVE authentication tests."""

    @pytest.mark.xfail(
        reason="T397: Anonymous RETRIEVE show instances allowed",
    )
    def test_retrieve_without_auth(self, api_client):
        """Anonymous RETRIEVE should fail."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)

        response = api_client.get(f"/api/v2/show-instances/{instance.id}")
        assert response.status_code in [
            401,
            403,
        ], "Anonymous can retrieve show instances"


@pytest.mark.django_db(transaction=True)
class TestShowInstanceRetrieveBOLA:
    """RETRIEVE BOLA tests."""

    @pytest.mark.xfail(reason="T398: No owner filtering on ShowInstance")
    def test_retrieve_other_user_instance(
        self, api_client, regular_user, admin_user,
    ):
        """Retrieve another user's show instance."""
        show = baker.make(Show, name="Admin Show")
        instance = baker.make(ShowInstance, show=show)

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/show-instances/{instance.id}")
        assert response.status_code in [
            403,
            404,
        ], "Can retrieve other user's instance (BOLA)"


@pytest.mark.django_db(transaction=True)
class TestShowInstanceRetrieveEnumeration:
    """ID enumeration attacks."""

    def test_enumerate_sequential_ids(self, api_client, admin_user):
        """Test if sequential IDs allow enumeration."""
        api_client.force_authenticate(user=admin_user)

        # Create a few instances
        show = baker.make(Show, name="Test Show")
        instances = [baker.make(ShowInstance, show=show) for _ in range(3)]

        # Try to access non-existent IDs around valid ones
        max_id = max(i.id for i in instances)

        for test_id in [max_id + 1, max_id + 2, max_id + 100]:
            response = api_client.get(f"/api/v2/show-instances/{test_id}")
            assert (
                response.status_code == 404
            ), f"ID enumeration possible at {test_id}"

    def test_id_type_confusion(self, api_client, admin_user):
        """Test ID type confusion attacks."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        api_client.force_authenticate(user=admin_user)

        # Try various ID formats
        test_ids = [
            f"{instance.id}'",
            f"{instance.id}--",
            f"{instance.id}abc",
            str(instance.id),
            float(instance.id),
        ]

        for test_id in test_ids:
            response = api_client.get(f"/api/v2/show-instances/{test_id}")
            assert response.status_code in [
                200,
                404,
            ], f"Unexpected status for ID: {test_id}"


@pytest.mark.django_db(transaction=True)
class TestShowInstanceRetrieveInformationDisclosure:
    """Information disclosure attacks."""

    @pytest.mark.xfail(reason="T400: 404 leaks query keyword")
    def test_404_leakage(self, api_client, admin_user):
        """Check if 404 leaks information about existence."""
        api_client.force_authenticate(user=admin_user)

        # Access non-existent ID
        response = api_client.get("/api/v2/show-instances/99999")

        if response.status_code == 404:
            content = response.content.decode()
            # Should not reveal DB details
            leaked_terms = [
                "cc_show_instances",
                "sql",
                "query",
                "doesnotexist",
            ]
            for term in leaked_terms:
                if term.lower() in content.lower():
                    pytest.fail(f"BUG: 404 leaks info: {term}")

    def test_error_on_invalid_id_format(self, api_client, admin_user):
        """Check error handling for invalid ID format."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(
            "/api/v2/show-instances/invalid'union select",
        )

        if response.status_code == 500:
            content = response.content.decode()
            # Should not expose stack traces
            leaked_terms = ["traceback", "exception", "line", "file"]
            for term in leaked_terms:
                if term.lower() in content.lower():
                    pytest.fail(f"BUG: Error exposes stack trace: {term}")


@pytest.mark.django_db(transaction=True)
class TestShowInstanceRetrieveFields:
    """Field-level security tests."""

    def test_retrieve_internal_fields(self, api_client, admin_user):
        """Check if internal fields are exposed."""
        show = baker.make(Show, name="Test Show")
        instance = baker.make(ShowInstance, show=show)
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(f"/api/v2/show-instances/{instance.id}")
        assert response.status_code == 200

        data = response.json()

        # Check for fields that should NOT be exposed
        sensitive_fields = ["password", "secret", "token", "internal"]
        for field in sensitive_fields:
            assert field not in data, f"Sensitive field exposed: {field}"
