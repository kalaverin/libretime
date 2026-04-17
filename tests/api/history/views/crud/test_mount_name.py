"""T267: MountName endpoint tests."""

import pytest

from model_bakery import baker

from api.history.models import MountName


@pytest.mark.django_db
class TestMountNameViewSet:
    """Test MountName LIST/CREATE/RETRIEVE/UPDATE/DELETE."""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_user):
        """Set up test fixtures."""
        self.api_client = api_client
        self.user = admin_user

    # === LIST Tests ===

    def test_list_empty_returns_200(self):
        """LIST empty should return 200 with empty list."""
        response = self.api_client.get("/api/v2/mount-names")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_mount(self):
        """LIST should return single mount name."""
        mount = baker.make(MountName, mount_name="/main")

        response = self.api_client.get("/api/v2/mount-names")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["mount_name"] == "/main"

    def test_list_multiple_mounts(self):
        """LIST should return multiple mount names."""
        baker.make(MountName, mount_name="/main")
        baker.make(MountName, mount_name="/live")
        baker.make(MountName, mount_name="/autodj")

        response = self.api_client.get("/api/v2/mount-names")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_unicode_mount_name(self):
        """LIST should handle unicode mount names."""
        mount = baker.make(MountName, mount_name="/поток-юникод")

        response = self.api_client.get("/api/v2/mount-names")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["mount_name"] == "/поток-юникод"

    def test_list_no_auth_fails(self):
        """LIST without auth should fail."""
        self.api_client.logout()
        response = self.api_client.get("/api/v2/mount-names")
        assert response.status_code == 403

    # === CREATE Tests ===

    def test_create_mount_success(self):
        """Successfully create mount name."""
        data = {
            "mount_name": "/new-mount",
        }

        response = self.api_client.post(
            "/api/v2/mount-names",
            data,
            format="json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["mount_name"] == "/new-mount"

    def test_create_missing_name_fails(self):
        """Create without mount_name should fail."""
        data = {}

        response = self.api_client.post(
            "/api/v2/mount-names",
            data,
            format="json",
        )
        assert response.status_code == 400

    def test_create_duplicate_name_allowed(self):
        """Create with duplicate name may be allowed."""
        baker.make(MountName, mount_name="/duplicate")

        data = {
            "mount_name": "/duplicate",
        }

        response = self.api_client.post(
            "/api/v2/mount-names",
            data,
            format="json",
        )
        # No unique constraint in model
        assert response.status_code == 201

    def test_create_no_auth_fails(self):
        """Create without auth should fail."""
        self.api_client.logout()
        data = {
            "mount_name": "/test",
        }

        response = self.api_client.post(
            "/api/v2/mount-names",
            data,
            format="json",
        )
        assert response.status_code == 403

    # === RETRIEVE Tests ===

    def test_retrieve_mount_success(self):
        """Successfully retrieve mount name."""
        mount = baker.make(MountName, mount_name="/retrieve-test")

        response = self.api_client.get(f"/api/v2/mount-names/{mount.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mount.id
        assert data["mount_name"] == "/retrieve-test"

    def test_retrieve_not_found(self):
        """Return 404 for non-existent mount."""
        response = self.api_client.get("/api/v2/mount-names/99999")
        assert response.status_code == 404

    # === UPDATE Tests ===

    def test_update_mount_name_success(self):
        """Successfully update mount name."""
        mount = baker.make(MountName, mount_name="/old-name")

        data = {
            "mount_name": "/new-name",
        }

        response = self.api_client.put(
            f"/api/v2/mount-names/{mount.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["mount_name"] == "/new-name"

    def test_update_partial_name(self):
        """Partial update with PATCH."""
        mount = baker.make(MountName, mount_name="/old")

        data = {"mount_name": "/new"}

        response = self.api_client.patch(
            f"/api/v2/mount-names/{mount.id}",
            data,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["mount_name"] == "/new"

    # === DELETE Tests ===

    def test_delete_mount_success(self):
        """Successfully delete mount name."""
        mount = baker.make(MountName, mount_name="/to-delete")

        response = self.api_client.delete(f"/api/v2/mount-names/{mount.id}")

        assert response.status_code == 204
        assert MountName.objects.filter(id=mount.id).count() == 0

    def test_delete_not_found(self):
        """Delete non-existent returns 404."""
        response = self.api_client.delete("/api/v2/mount-names/99999")
        assert response.status_code == 404

    def test_delete_no_auth_fails(self):
        """Delete without auth fails."""
        mount = baker.make(MountName, mount_name="/test")

        self.api_client.logout()
        response = self.api_client.delete(f"/api/v2/mount-names/{mount.id}")
        assert response.status_code == 403
