"""
BOLA (Broken Object Level Authorization) Prevention Tests for SmartBlock Components

These tests verify API1:2023 compliance for:
- SmartBlock (T829, T830, T831, T832)
- SmartBlockContent (T475, T476)
- SmartBlockCriteria (T488, T489, T496, T505, T506, T507)

Pattern: HOST users can only access their OWN resources
         MANAGER/ADMIN can access any resources
         ANONYMOUS users get 403
"""

import pytest
from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role
from api.schedule.models import SmartBlock, SmartBlockContent, SmartBlockCriteria
from api.storage.models import File


@pytest.mark.django_db
class TestBolaSmartBlockPrevention:
    """BOLA prevention tests for SmartBlock resource (T829, T830, T831, T832)."""

    def test_anonymous_get_smartblock_returns_403(self, anonymous_client):
        """Anonymous GET /smart-blocks returns 403."""
        response = anonymous_client.get("/api/v2/smart-blocks")
        assert response.status_code == 403

    def test_anonymous_post_smartblock_returns_403(self, anonymous_client):
        """Anonymous POST /smart-blocks returns 403."""
        response = anonymous_client.post("/api/v2/smart-blocks", {"name": "test"})
        assert response.status_code == 403

    def test_host_cannot_retrieve_other_host_smartblock(self, host_client, host_user, faker):
        """CRITICAL T829: HOST cannot RETRIEVE another HOST's SmartBlock."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_block = baker.make(
            SmartBlock,
            name=f"Other Block {faker.uuid4()[:8]}",
            owner=other_host,
            kind="static",
        )

        response = host_client.get(f"/api/v2/smart-blocks/{other_block.id}")

        assert response.status_code in [403, 404], (
            f"BOLA T829: HOST retrieved another HOST's SmartBlock! Status: {response.status_code}"
        )

    def test_host_list_smartblocks_only_shows_own(self, host_client, host_user, faker):
        """CRITICAL T830: HOST LIST should only show own SmartBlocks."""
        # Create blocks for other users
        for _ in range(3):
            other_host = baker.make(
                User,
                username=f"other_{faker.uuid4()[:8]}",
                email=f"o_{faker.uuid4()[:8]}@test.com",
                role=Role.HOST,
            )
            baker.make(SmartBlock, owner=other_host, kind="static")

        # Create own block
        own_block = baker.make(SmartBlock, owner=host_user, kind="static")

        response = host_client.get("/api/v2/smart-blocks")
        assert response.status_code == 200

        data = response.json()
        # Handle both paginated and non-paginated responses
        if isinstance(data, list):
            results = data
        else:
            results = data.get("results", data)
        
        # Should only see own block
        result_ids = [r["id"] for r in results]
        assert own_block.id in result_ids, "HOST should see own SmartBlock"
        
        # Count should be 1 (only own block)
        assert len(results) == 1, (
            f"BOLA T830: HOST sees {len(results)} SmartBlocks, expected 1 (own)!"
        )

    def test_host_cannot_update_other_host_smartblock(self, host_client, host_user, faker):
        """CRITICAL T831: HOST cannot UPDATE another HOST's SmartBlock."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_block = baker.make(
            SmartBlock,
            name=f"Other Block {faker.uuid4()[:8]}",
            owner=other_host,
            kind="static",
        )
        original_name = other_block.name

        response = host_client.patch(
            f"/api/v2/smart-blocks/{other_block.id}",
            {"name": "HACKED BY HOST"},
            format="json",
        )

        assert response.status_code in [403, 404], (
            f"BOLA T831: HOST updated another HOST's SmartBlock! Status: {response.status_code}"
        )

        # Verify not modified
        other_block.refresh_from_db()
        assert other_block.name == original_name

    def test_host_cannot_delete_other_host_smartblock(self, host_client, host_user, faker):
        """CRITICAL T832: HOST cannot DELETE another HOST's SmartBlock."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_block = baker.make(
            SmartBlock,
            name=f"Other Block {faker.uuid4()[:8]}",
            owner=other_host,
            kind="static",
        )
        other_block_id = other_block.id

        response = host_client.delete(f"/api/v2/smart-blocks/{other_block_id}")

        assert response.status_code in [403, 404], (
            f"BOLA T832: HOST deleted another HOST's SmartBlock! Status: {response.status_code}"
        )

        # Verify still exists
        assert SmartBlock.objects.filter(id=other_block_id).exists()

    def test_manager_can_update_any_host_smartblock(self, manager_client, faker):
        """MANAGER can UPDATE any HOST's SmartBlock (expected, not BOLA)."""
        other_host = baker.make(
            User,
            username=f"other_host_{faker.uuid4()[:8]}",
            email=f"other_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_block = baker.make(
            SmartBlock,
            name=f"Other Block {faker.uuid4()[:8]}",
            owner=other_host,
            kind="static",
        )
        new_name = f"Manager Updated {faker.uuid4()[:8]}"

        response = manager_client.patch(
            f"/api/v2/smart-blocks/{other_block.id}",
            {"name": new_name},
            format="json",
        )

        assert response.status_code == 200, (
            f"MANAGER should be able to update any SmartBlock! Status: {response.status_code}"
        )

        other_block.refresh_from_db()
        assert other_block.name == new_name


@pytest.mark.django_db
class TestBolaSmartBlockContentPrevention:
    """BOLA prevention tests for SmartBlockContent (T475, T476)."""

    def test_anonymous_get_content_returns_403(self, anonymous_client):
        """Anonymous GET /smart-block-contents returns 403."""
        response = anonymous_client.get("/api/v2/smart-block-contents")
        assert response.status_code == 403

    def test_anonymous_post_content_returns_403(self, anonymous_client):
        """Anonymous POST /smart-block-contents returns 403."""
        response = anonymous_client.post("/api/v2/smart-block-contents", {})
        assert response.status_code == 403

    def test_host_cannot_create_content_in_other_host_block(self, host_client, host_user, faker):
        """CRITICAL T475: HOST cannot CREATE content in another HOST's SmartBlock."""
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"o_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_block = baker.make(
            SmartBlock,
            name=f"Other Block {faker.uuid4()[:8]}",
            owner=other_host,
            kind="static",
        )
        own_file = baker.make(
            File,
            name=f"Own File {faker.uuid4()[:8]}",
            owner=host_user,
        )

        response = host_client.post(
            "/api/v2/smart-block-contents",
            {
                "block": other_block.id,
                "file": own_file.id,
                "position": 1,
                "offset": 0,
            },
            format="json",
        )

        assert response.status_code in [403, 400], (
            f"BOLA T475: HOST created content in another HOST's block! Status: {response.status_code}"
        )

    def test_host_cannot_create_content_with_other_host_file(self, host_client, host_user, faker):
        """CRITICAL T476: HOST cannot CREATE content using another HOST's File."""
        own_block = baker.make(
            SmartBlock,
            name=f"Own Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind="static",
        )
        other_host = baker.make(
            User,
            username=f"other_{faker.uuid4()[:8]}",
            email=f"o_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        other_file = baker.make(
            File,
            name=f"Other File {faker.uuid4()[:8]}",
            owner=other_host,
        )

        response = host_client.post(
            "/api/v2/smart-block-contents",
            {
                "block": own_block.id,
                "file": other_file.id,
                "position": 1,
                "offset": 0,
            },
            format="json",
        )

        assert response.status_code in [403, 400], (
            f"BOLA T476: HOST created content with another HOST's file! Status: {response.status_code}"
        )

    def test_host_list_content_only_shows_own(self, host_client, host_user, faker):
        """HOST LIST content should only show content from own blocks."""
        # Create own block with content
        own_block = baker.make(SmartBlock, owner=host_user, kind="static")
        own_file = baker.make(File, owner=host_user)
        own_content = baker.make(SmartBlockContent, block=own_block, file=own_file, position=1)

        # Create other host's block with content
        other_host = baker.make(User, role=Role.HOST)
        other_block = baker.make(SmartBlock, owner=other_host, kind="static")
        other_file = baker.make(File, owner=other_host)
        other_content = baker.make(SmartBlockContent, block=other_block, file=other_file, position=1)

        response = host_client.get("/api/v2/smart-block-contents")
        assert response.status_code == 200

        data = response.json()
        # Handle both paginated and non-paginated responses
        if isinstance(data, list):
            results = data
        else:
            results = data.get("results", data)
        result_ids = [r["id"] for r in results]

        # Should see own content
        assert own_content.id in result_ids, "HOST should see own SmartBlockContent"
        
        # Should NOT see other content
        assert other_content.id not in result_ids, (
            f"BOLA: HOST sees other user's SmartBlockContent in LIST!"
        )


@pytest.mark.django_db
class TestBolaSmartBlockCriteriaPrevention:
    """BOLA prevention tests for SmartBlockCriteria (T488, T489, T496, T505, T506, T507)."""

    def test_anonymous_get_criteria_returns_403(self, anonymous_client):
        """Anonymous GET /smart-block-criteria returns 403."""
        response = anonymous_client.get("/api/v2/smart-block-criteria")
        assert response.status_code == 403

    def test_anonymous_post_criteria_returns_403(self, anonymous_client):
        """Anonymous POST /smart-block-criteria returns 403."""
        response = anonymous_client.post("/api/v2/smart-block-criteria", {})
        assert response.status_code == 403

    def test_host_cannot_list_all_criteria(self, host_client, host_user, faker):
        """CRITICAL T488: HOST LIST criteria should only show own block's criteria."""
        # Create own block with criteria
        own_block = baker.make(SmartBlock, owner=host_user, kind="dynamic")
        own_criteria = baker.make(
            SmartBlockCriteria,
            block=own_block,
            criteria="title",
            condition="contains",
            value="test",
        )

        # Create other host's block with criteria
        other_host = baker.make(User, role=Role.HOST)
        other_block = baker.make(SmartBlock, owner=other_host, kind="dynamic")
        other_criteria = baker.make(
            SmartBlockCriteria,
            block=other_block,
            criteria="title",
            condition="contains",
            value="other",
        )

        response = host_client.get("/api/v2/smart-block-criteria")
        assert response.status_code == 200

        data = response.json()
        # Handle both paginated and non-paginated responses
        if isinstance(data, list):
            results = data
        else:
            results = data.get("results", data)
        result_ids = [r["id"] for r in results]

        # Should see own criteria
        assert own_criteria.id in result_ids, "HOST should see own SmartBlockCriteria"
        
        # Should NOT see other criteria
        assert other_criteria.id not in result_ids, (
            f"BOLA T488: HOST sees other user's SmartBlockCriteria in LIST!"
        )

    def test_host_cannot_filter_criteria_by_other_host_block(self, host_client, host_user, faker):
        """CRITICAL T489: HOST cannot filter criteria by another HOST's block ID."""
        other_host = baker.make(User, role=Role.HOST)
        other_block = baker.make(SmartBlock, owner=other_host, kind="dynamic")
        other_criteria = baker.make(
            SmartBlockCriteria,
            block=other_block,
            criteria="title",
            condition="contains",
            value="other",
        )

        response = host_client.get(f"/api/v2/smart-block-criteria?block={other_block.id}")
        assert response.status_code == 200

        data = response.json()
        # Handle both paginated and non-paginated responses
        if isinstance(data, list):
            results = data
        else:
            results = data.get("results", data)
        
        # Should return empty or not include other criteria
        result_ids = [r["id"] for r in results]
        assert other_criteria.id not in result_ids, (
            f"BOLA T489: HOST filtered criteria by other user's block!"
        )

    def test_host_cannot_create_criteria_for_other_host_block(self, host_client, host_user, faker):
        """CRITICAL T496: HOST cannot CREATE criteria for another HOST's block."""
        other_host = baker.make(User, role=Role.HOST)
        other_block = baker.make(SmartBlock, owner=other_host, kind="dynamic")

        response = host_client.post(
            "/api/v2/smart-block-criteria",
            {
                "block": other_block.id,
                "criteria": "title",
                "condition": 0,  # 0 = contains
                "value": "hacked",
            },
            format="json",
        )

        assert response.status_code in [403, 400], (
            f"BOLA T496: HOST created criteria for another HOST's block! Status: {response.status_code}"
        )

    def test_host_cannot_update_other_host_criteria(self, host_client, host_user, faker):
        """CRITICAL T505: HOST cannot UPDATE another HOST's criteria."""
        other_host = baker.make(User, role=Role.HOST)
        other_block = baker.make(SmartBlock, owner=other_host, kind="dynamic")
        other_criteria = baker.make(
            SmartBlockCriteria,
            block=other_block,
            criteria="title",
            condition="contains",
            value="original",
        )

        response = host_client.patch(
            f"/api/v2/smart-block-criteria/{other_criteria.id}",
            {"value": "HACKED"},
            format="json",
        )

        assert response.status_code in [403, 404], (
            f"BOLA T505: HOST updated another HOST's criteria! Status: {response.status_code}"
        )

    def test_host_cannot_delete_other_host_criteria(self, host_client, host_user, faker):
        """CRITICAL T506: HOST cannot DELETE another HOST's criteria."""
        other_host = baker.make(User, role=Role.HOST)
        other_block = baker.make(SmartBlock, owner=other_host, kind="dynamic")
        other_criteria = baker.make(
            SmartBlockCriteria,
            block=other_block,
            criteria="title",
            condition="contains",
            value="original",
        )
        criteria_id = other_criteria.id

        response = host_client.delete(f"/api/v2/smart-block-criteria/{criteria_id}")

        assert response.status_code in [403, 404], (
            f"BOLA T506: HOST deleted another HOST's criteria! Status: {response.status_code}"
        )

        # Verify still exists
        assert SmartBlockCriteria.objects.filter(id=criteria_id).exists()

    def test_host_cannot_move_criteria_to_other_host_block(self, host_client, host_user, faker):
        """CRITICAL T507: HOST cannot MOVE criteria to another HOST's block."""
        own_block = baker.make(SmartBlock, owner=host_user, kind="dynamic")
        own_criteria = baker.make(
            SmartBlockCriteria,
            block=own_block,
            criteria="title",
            condition="contains",
            value="test",
        )
        
        other_host = baker.make(User, role=Role.HOST)
        other_block = baker.make(SmartBlock, owner=other_host, kind="dynamic")

        response = host_client.patch(
            f"/api/v2/smart-block-criteria/{own_criteria.id}",
            {"block": other_block.id},
            format="json",
        )

        # Should either fail or keep the original block
        if response.status_code == 200:
            own_criteria.refresh_from_db()
            assert own_criteria.block_id == own_block.id, (
                f"BOLA T507: HOST moved criteria to another HOST's block!"
            )
        else:
            assert response.status_code in [403, 400], (
                f"Unexpected status: {response.status_code}"
            )
