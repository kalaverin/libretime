"""Tests for SmartBlocks DELETE endpoint (T237)."""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import (
    SmartBlock,
    SmartBlockContent,
    SmartBlockCriteria,
)
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestSmartBlockViewSetDelete:
    """Test SmartBlocks DELETE endpoint - DELETE /api/v2/smart-blocks/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockCriteria.objects.all().delete()
        SmartBlockContent.objects.all().delete()
        SmartBlock.objects.all().delete()
        File.objects.all().delete()
        User.objects.filter(username__startswith="testsb").delete()

    def test_delete_block_success_returns_204(self, api_client):
        """DELETE should return 204 on success."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Test Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.delete(f"/api/v2/smart-blocks/{block.id}")
        assert response.status_code == 204

    def test_delete_block_removes_from_db(self, api_client):
        """DELETE should remove block from database."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Test Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        api_client.delete(f"/api/v2/smart-blocks/{block.id}")
        assert SmartBlock.objects.filter(id=block.id).count() == 0

    def test_delete_block_not_found_returns_404(self, api_client):
        """DELETE non-existent block should return 404."""
        response = api_client.delete("/api/v2/smart-blocks/999999")
        assert response.status_code == 404

    def test_delete_block_no_auth_fails(self, client):
        """DELETE without auth should return 403."""
        response = client.delete("/api/v2/smart-blocks/1")
        assert response.status_code == 403

    def test_delete_block_double_delete_returns_404(self, api_client):
        """DELETE already deleted block should return 404."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Test Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        api_client.delete(f"/api/v2/smart-blocks/{block.id}")
        response = api_client.delete(f"/api/v2/smart-blocks/{block.id}")
        assert response.status_code == 404

    def test_delete_block_returns_empty_body(self, api_client):
        """DELETE should return empty response body."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Test Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.delete(f"/api/v2/smart-blocks/{block.id}")
        assert response.content == b""

    def test_delete_one_block_others_remain(self, api_client):
        """DELETE one block should leave others."""
        user = baker.make(User, username="testsb_user")
        block1 = baker.make(
            SmartBlock,
            name="Block 1",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        block2 = baker.make(
            SmartBlock,
            name="Block 2",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )
        block3 = baker.make(
            SmartBlock,
            name="Block 3",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        api_client.delete(f"/api/v2/smart-blocks/{block2.id}")

        assert SmartBlock.objects.filter(id=block1.id).exists()
        assert not SmartBlock.objects.filter(id=block2.id).exists()
        assert SmartBlock.objects.filter(id=block3.id).exists()

    def test_delete_block_with_content_cascade(self, api_client):
        """DELETE static block should cascade delete contents."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )
        content = baker.make(
            SmartBlockContent,
            block=block,
            file=file_obj,
            position=1,
            offset=0,
        )

        api_client.delete(f"/api/v2/smart-blocks/{block.id}")
        assert not SmartBlockContent.objects.filter(id=content.id).exists()

    def test_delete_block_with_criteria_cascade(self, api_client):
        """DELETE dynamic block should cascade delete criteria."""
        user = baker.make(User, username="testsb_user")
        block = baker.make(
            SmartBlock,
            name="Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )

        api_client.delete(f"/api/v2/smart-blocks/{block.id}")
        assert not SmartBlockCriteria.objects.filter(id=criteria.id).exists()

    def test_delete_block_id_zero_returns_404(self, api_client):
        """DELETE with id=0 should return 404."""
        response = api_client.delete("/api/v2/smart-blocks/0")
        assert response.status_code == 404

    def test_delete_block_negative_id_returns_404(self, api_client):
        """DELETE with negative id should return 404."""
        response = api_client.delete("/api/v2/smart-blocks/-1")
        assert response.status_code == 404
