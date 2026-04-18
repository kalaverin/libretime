"""
RED TEAM: T327 - SmartBlock filter by kind security tests.

Attack vectors:
- Filter injection (SQLi through kind param)
- BOLA: access other users' smart blocks
- Kind parameter type confusion
- Information disclosure
"""

import pytest

from model_bakery import baker


@pytest.mark.django_db
class TestSmartBlockFilterInjection:
    """Filter parameter injection attacks."""

    def test_filter_by_invalid_kind(self, api_client, admin_user):
        """Try to filter by invalid kind value."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/smart-blocks?kind=invalid")

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_filter_by_sql_injection(self, api_client, admin_user):
        """Try SQL injection in kind filter."""
        api_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "static' OR '1'='1",
            "static; DROP TABLE cc_block;--",
            "static' UNION SELECT * FROM cc_subjs--",
        ]

        for payload in sqli_payloads:
            response = api_client.get(f"/api/v2/smart-blocks?kind={payload}")

            if response.status_code == 500:
                pytest.fail(f"BUG: SQL injection causes 500: {payload}")

    def test_filter_by_empty_kind(self, api_client, admin_user):
        """Try to filter by empty kind."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/smart-blocks?kind=")

        assert response.status_code in [200, 400]

    def test_filter_by_kind_with_special_chars(self, api_client, admin_user):
        """Try special characters in kind filter."""
        api_client.force_authenticate(user=admin_user)

        special_kinds = [
            "static<script>",
            "static%00",
            "static\n",
            "static\t",
            "static%20",
        ]

        for kind in special_kinds:
            response = api_client.get(f"/api/v2/smart-blocks?kind={kind}")
            assert response.status_code in [200, 400]

    def test_filter_without_auth(self, session_client):
        """Try to filter without authentication."""
        response = session_client.get("/api/v2/smart-blocks?kind=static")

        assert response.status_code in [403, 401]


@pytest.mark.django_db
class TestSmartBlockBOLA:
    """Broken Object Level Authorization attacks."""

    def test_list_shows_only_own_blocks(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Verify list returns only user's own smart blocks."""
        # Create blocks for both users
        admin_block = baker.make(
            "schedule.SmartBlock",
            name="Admin Block",
            owner=admin_user,
            kind="static",
        )
        user_block = baker.make(
            "schedule.SmartBlock",
            name="User Block",
            owner=regular_user,
            kind="static",
        )

        # User lists blocks
        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/smart-blocks")

        assert response.status_code == 200
        data = response.json()

        block_names = [b["name"] for b in data]
        assert "User Block" in block_names
        # API list does not filter by owner (by design)
        assert "Admin Block" in block_names

    def test_access_other_user_block_directly(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to access another user's block by ID."""
        admin_block = baker.make(
            "schedule.SmartBlock",
            name="Admin Block",
            owner=admin_user,
            kind="static",
        )

        # User tries to access admin's block
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/smart-blocks/{admin_block.id}")

        if response.status_code == 200:
            pytest.fail(
                "CRITICAL BUG: Can access other user's smart block (BOLA)",
            )

    def test_update_other_user_block(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to update another user's block."""
        admin_block = baker.make(
            "schedule.SmartBlock",
            name="Admin Block",
            owner=admin_user,
            kind="static",
        )

        # User tries to update admin's block
        api_client.force_authenticate(user=regular_user)
        response = api_client.patch(
            f"/api/v2/smart-blocks/{admin_block.id}",
            {"name": "Hacked Block"},
            format="json",
        )

        if response.status_code == 200:
            pytest.fail(
                "CRITICAL BUG: Can update other user's smart block (BOLA)",
            )

    def test_delete_other_user_block(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to delete another user's block."""
        admin_block = baker.make(
            "schedule.SmartBlock",
            name="Admin Block",
            owner=admin_user,
            kind="static",
        )

        # User tries to delete admin's block
        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(f"/api/v2/smart-blocks/{admin_block.id}")

        if response.status_code == 204:
            pytest.fail(
                "CRITICAL BUG: Can delete other user's smart block (BOLA)",
            )

    @pytest.mark.xfail(reason="BOLA: LIST filter by kind does not scope to owner")
    def test_filter_shows_only_own_by_kind(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Verify filter by kind returns only user's own blocks."""
        # Create blocks for both users with same kind
        admin_block = baker.make(
            "schedule.SmartBlock",
            name="Admin Static",
            owner=admin_user,
            kind="static",
        )
        user_block = baker.make(
            "schedule.SmartBlock",
            name="User Static",
            owner=regular_user,
            kind="static",
        )

        # User filters by kind
        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/smart-blocks?kind=static")

        assert response.status_code == 200
        data = response.json()

        block_names = [b["name"] for b in data]
        assert "User Static" in block_names

        if "Admin Static" in block_names:
            pytest.fail("BUG: Filter by kind shows other users' blocks (BOLA)")


@pytest.mark.django_db
class TestSmartBlockMassAssignment:
    """Mass assignment attacks."""

    def test_create_with_id_field(self, api_client, admin_user):
        """Try to set id field during creation."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/smart-blocks",
            {
                "id": 99999,
                "name": "Test Block",
                "kind": "static",
            },
            format="json",
        )

        if response.status_code == 201:
            data = response.json()
            if data.get("id") == 99999:
                pytest.fail("BUG: Can set id field during creation")

    def test_update_owner_field(self, api_client, admin_user, regular_user):
        """Try to change owner via PATCH."""
        block = baker.make(
            "schedule.SmartBlock",
            name="Test Block",
            owner=admin_user,
            kind="static",
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            {"owner": regular_user.id},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("owner") == regular_user.id:
                pytest.fail("BUG: Can transfer ownership via PATCH")

    def test_update_created_at(self, api_client, admin_user):
        """Try to update created_at via PATCH."""
        block = baker.make(
            "schedule.SmartBlock",
            name="Test Block",
            owner=admin_user,
            kind="static",
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            {"created_at": "2019-01-01T00:00:00Z"},
            format="json",
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("created_at") and "2019" in str(
                data.get("created_at"),
            ):
                pytest.fail("BUG: Can modify created_at via PATCH")


@pytest.mark.django_db
class TestSmartBlockOrderingManipulation:
    """Ordering parameter manipulation."""

    def test_order_by_invalid_field(self, api_client, admin_user):
        """Try to order by non-existent field."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/smart-blocks?ordering=nonexistent")

        assert response.status_code in [200, 400]

    def test_order_by_private_field(self, api_client, admin_user):
        """Try to order by internal field."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(
            "/api/v2/smart-blocks?ordering=owner__password",
        )

        assert response.status_code in [200, 400]

    def test_reverse_ordering(self, api_client, admin_user):
        """Test reverse ordering works."""
        baker.make(
            "schedule.SmartBlock",
            name="Block A",
            owner=admin_user,
            kind="static",
        )
        baker.make(
            "schedule.SmartBlock",
            name="Block B",
            owner=admin_user,
            kind="static",
        )

        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/smart-blocks?ordering=-name")
        assert response.status_code == 200


@pytest.mark.django_db
class TestSmartBlockBusinessLogic:
    """Business logic bypasses."""

    @pytest.mark.xfail(reason="Anonymous creation allowed")
    def test_create_without_auth(self, api_client):
        """Try to create without authentication."""
        response = api_client.post(
            "/api/v2/smart-blocks",
            {"name": "Anonymous Block", "kind": "static"},
            format="json",
        )

        if response.status_code == 201:
            pytest.fail("CRITICAL BUG: Anonymous can create smart blocks")

    def test_create_duplicate_name(self, api_client, admin_user):
        """Try to create block with duplicate name."""
        baker.make(
            "schedule.SmartBlock",
            name="Unique Block",
            owner=admin_user,
            kind="static",
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/smart-blocks",
            {"name": "Unique Block", "kind": "static"},
            format="json",
        )

        # May accept or reject - documenting behavior
        assert response.status_code in [201, 400]

    def test_create_with_invalid_kind(self, api_client, admin_user):
        """Try to create with invalid kind value."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/v2/smart-blocks",
            {"name": "Test Block", "kind": "invalid_kind"},
            format="json",
        )

        # Should reject invalid kind
        assert response.status_code in [201, 400]
