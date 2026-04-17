"""T263: PlayoutHistoryTemplate endpoint tests."""

import pytest

from model_bakery import baker

from api.history.models import PlayoutHistoryTemplate


@pytest.mark.django_db
class TestPlayoutHistoryTemplateViewSet:
    """Test PlayoutHistoryTemplate LIST/CREATE/RETRIEVE/UPDATE/DELETE."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_user):
        """Set up test fixtures."""
        self.api_client = api_client
        self.user = admin_user

    # === LIST Tests ===

    def test_list_empty_returns_200(self):
        """LIST empty should return 200 with empty list."""
        response = self.api_client.get("/api/v2/playout-history-templates")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_template(self):
        """LIST should return single template."""
        template = baker.make(
            PlayoutHistoryTemplate,
            name="Default",
            type="standard",
        )

        response = self.api_client.get("/api/v2/playout-history-templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Default"
        assert data[0]["type"] == "standard"

    def test_list_multiple_templates(self):
        """LIST should return multiple templates."""
        baker.make(PlayoutHistoryTemplate, name="Compact", type="minimal")
        baker.make(PlayoutHistoryTemplate, name="Detailed", type="full")

        response = self.api_client.get("/api/v2/playout-history-templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_no_auth_fails(self):
        """LIST without auth should fail."""
        self.api_client.logout()
        response = self.api_client.get("/api/v2/playout-history-templates")
        assert response.status_code == 403

    # === CREATE Tests ===

    def test_create_template_success(self):
        """Successfully create template."""
        data = {
            "name": "My Template",
            "type": "custom",
        }

        response = self.api_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Template"
        assert data["type"] == "custom"

    def test_create_missing_name_fails(self):
        """Create without name should fail."""
        data = {
            "type": "custom",
        }

        response = self.api_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_missing_type_fails(self):
        """Create without type should fail."""
        data = {
            "name": "Test",
        }

        response = self.api_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_duplicate_name_allowed(self):
        """Create with duplicate name may be allowed (no unique constraint)."""
        baker.make(PlayoutHistoryTemplate, name="Duplicate", type="standard")

        data = {
            "name": "Duplicate",
            "type": "custom",
        }

        response = self.api_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )
        # Model doesn't have unique constraint, so this should work
        assert response.status_code == 201

    def test_create_no_auth_fails(self):
        """Create without auth should fail."""
        self.api_client.logout()
        data = {
            "name": "Test",
            "type": "custom",
        }

        response = self.api_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )
        assert response.status_code == 403

    # === RETRIEVE Tests ===

    def test_retrieve_template_success(self):
        """Successfully retrieve template."""
        template = baker.make(
            PlayoutHistoryTemplate,
            name="Test",
            type="standard",
        )

        response = self.api_client.get(
            f"/api/v2/playout-history-templates/{template.id}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template.id
        assert data["name"] == "Test"
        assert data["type"] == "standard"

    def test_retrieve_not_found(self):
        """Return 404 for non-existent template."""
        response = self.api_client.get(
            "/api/v2/playout-history-templates/99999",
        )
        assert response.status_code == 404

    # === UPDATE Tests ===

    def test_update_name_success(self):
        """Successfully update template name."""
        template = baker.make(
            PlayoutHistoryTemplate,
            name="Old",
            type="standard",
        )

        data = {
            "name": "New",
            "type": "standard",
        }

        response = self.api_client.put(
            f"/api/v2/playout-history-templates/{template.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New"

    def test_update_type_success(self):
        """Successfully update template type."""
        template = baker.make(
            PlayoutHistoryTemplate,
            name="Test",
            type="standard",
        )

        data = {
            "name": "Test",
            "type": "custom",
        }

        response = self.api_client.put(
            f"/api/v2/playout-history-templates/{template.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "custom"

    def test_update_partial_name(self):
        """Partial update name with PATCH."""
        template = baker.make(
            PlayoutHistoryTemplate,
            name="Old",
            type="standard",
        )

        data = {"name": "New"}

        response = self.api_client.patch(
            f"/api/v2/playout-history-templates/{template.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New"
        assert data["type"] == "standard"  # Unchanged

    # === DELETE Tests ===

    def test_delete_template_success(self):
        """Successfully delete template."""
        template = baker.make(
            PlayoutHistoryTemplate,
            name="ToDelete",
            type="standard",
        )

        response = self.api_client.delete(
            f"/api/v2/playout-history-templates/{template.id}",
        )

        assert response.status_code == 204
        assert (
            PlayoutHistoryTemplate.objects.filter(id=template.id).count() == 0
        )

    def test_delete_not_found(self):
        """Delete non-existent returns 404."""
        response = self.api_client.delete(
            "/api/v2/playout-history-templates/99999",
        )
        assert response.status_code == 404

    def test_delete_no_auth_fails(self):
        """Delete without auth fails."""
        template = baker.make(
            PlayoutHistoryTemplate,
            name="Test",
            type="standard",
        )

        self.api_client.logout()
        response = self.api_client.delete(
            f"/api/v2/playout-history-templates/{template.id}",
        )
        assert response.status_code == 403
