"""T264: PlayoutHistoryTemplateField endpoint tests."""

import pytest

from model_bakery import baker

from api.history.models import (
    PlayoutHistoryTemplate,
    PlayoutHistoryTemplateField,
)


@pytest.mark.django_db
class TestPlayoutHistoryTemplateFieldViewSet:
    """Test PlayoutHistoryTemplateField LIST/CREATE/RETRIEVE/UPDATE/DELETE."""

    @pytest.fixture(autouse=True)
    def setup(self, admin_client, admin_user):
        """Set up test fixtures."""
        self.admin_client = admin_client
        self.user = admin_user
        self.template = baker.make(
            PlayoutHistoryTemplate,
            name="Test",
            type="standard",
        )

    # === LIST Tests ===

    def test_list_empty_returns_200(self):
        """LIST empty should return 200 with empty list."""
        response = self.admin_client.get(
            "/api/v2/playout-history-template-fields",
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_field(self):
        """LIST should return single field."""
        field = baker.make(
            PlayoutHistoryTemplateField,
            template=self.template,
            name="artist",
            label="Artist Name",
            type="text",
            is_file_md=True,
            position=1,
        )

        response = self.admin_client.get(
            "/api/v2/playout-history-template-fields",
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "artist"
        assert data[0]["label"] == "Artist Name"

    def test_list_multiple_fields(self):
        """LIST should return multiple fields."""
        baker.make(
            PlayoutHistoryTemplateField,
            template=self.template,
            name="artist",
            label="Artist",
            type="text",
            is_file_md=True,
            position=1,
        )
        baker.make(
            PlayoutHistoryTemplateField,
            template=self.template,
            name="title",
            label="Title",
            type="text",
            is_file_md=True,
            position=2,
        )

        response = self.admin_client.get(
            "/api/v2/playout-history-template-fields",
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_no_auth_fails(self):
        """LIST without auth should fail."""
        self.admin_client.logout()
        response = self.admin_client.get(
            "/api/v2/playout-history-template-fields",
        )
        assert response.status_code == 403

    # === CREATE Tests ===

    def test_create_field_success(self):
        """Successfully create field."""
        data = {
            "template": self.template.id,
            "name": "album",
            "label": "Album Name",
            "type": "text",
            "is_file_md": True,
            "position": 1,
        }

        response = self.admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "album"
        assert data["label"] == "Album Name"
        assert data["type"] == "text"
        assert data["is_file_md"] is True
        assert data["position"] == 1

    def test_create_missing_template_fails(self):
        """Create without template should fail."""
        data = {
            "name": "test",
            "label": "Test",
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = self.admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_invalid_template_fails(self):
        """Create with non-existent template should fail."""
        data = {
            "template": 99999,
            "name": "test",
            "label": "Test",
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = self.admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_missing_name_fails(self):
        """Create without name should fail."""
        data = {
            "template": self.template.id,
            "label": "Test",
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = self.admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_no_auth_fails(self):
        """Create without auth should fail."""
        self.admin_client.logout()
        data = {
            "template": self.template.id,
            "name": "test",
            "label": "Test",
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = self.admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )
        assert response.status_code == 403

    # === RETRIEVE Tests ===

    def test_retrieve_field_success(self):
        """Successfully retrieve field."""
        field = baker.make(
            PlayoutHistoryTemplateField,
            template=self.template,
            name="genre",
            label="Genre",
            type="text",
            is_file_md=True,
            position=3,
        )

        response = self.admin_client.get(
            f"/api/v2/playout-history-template-fields/{field.id}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == field.id
        assert data["name"] == "genre"
        assert data["position"] == 3

    def test_retrieve_not_found(self):
        """Return 404 for non-existent field."""
        response = self.admin_client.get(
            "/api/v2/playout-history-template-fields/99999",
        )
        assert response.status_code == 404

    # === UPDATE Tests ===

    def test_update_position_success(self):
        """Successfully update field position."""
        field = baker.make(
            PlayoutHistoryTemplateField,
            template=self.template,
            name="test",
            label="Test",
            type="text",
            is_file_md=False,
            position=1,
        )

        data = {
            "template": self.template.id,
            "name": "test",
            "label": "Test",
            "type": "text",
            "is_file_md": False,
            "position": 5,
        }

        response = self.admin_client.put(
            f"/api/v2/playout-history-template-fields/{field.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["position"] == 5

    def test_update_partial_label(self):
        """Partial update label with PATCH."""
        field = baker.make(
            PlayoutHistoryTemplateField,
            template=self.template,
            name="test",
            label="Old Label",
            type="text",
            is_file_md=False,
            position=1,
        )

        data = {"label": "New Label"}

        response = self.admin_client.patch(
            f"/api/v2/playout-history-template-fields/{field.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "New Label"
        assert data["name"] == "test"  # Unchanged

    # === DELETE Tests ===

    def test_delete_field_success(self):
        """Successfully delete field."""
        field = baker.make(
            PlayoutHistoryTemplateField,
            template=self.template,
            name="todelete",
            label="To Delete",
            type="text",
            is_file_md=False,
            position=1,
        )

        response = self.admin_client.delete(
            f"/api/v2/playout-history-template-fields/{field.id}",
        )

        assert response.status_code == 204
        assert (
            PlayoutHistoryTemplateField.objects.filter(id=field.id).count()
            == 0
        )

    def test_delete_not_found(self):
        """Delete non-existent returns 404."""
        response = self.admin_client.delete(
            "/api/v2/playout-history-template-fields/99999",
        )
        assert response.status_code == 404

    def test_delete_no_auth_fails(self):
        """Delete without auth fails."""
        field = baker.make(
            PlayoutHistoryTemplateField,
            template=self.template,
            name="test",
            label="Test",
            type="text",
            is_file_md=False,
            position=1,
        )

        self.admin_client.logout()
        response = self.admin_client.delete(
            f"/api/v2/playout-history-template-fields/{field.id}",
        )
        assert response.status_code == 403
