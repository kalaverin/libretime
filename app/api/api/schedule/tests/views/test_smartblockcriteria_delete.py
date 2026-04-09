"""Tests for SmartBlockCriteria DELETE endpoint (T244)."""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockCriteria


@pytest.mark.django_db(transaction=True)
class TestSmartBlockCriteriaViewSetDelete:
    """Test SmartBlockCriteria DELETE endpoint - DELETE /api/v2/smart-block-criteria/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockCriteria.objects.all().delete()
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testsbcr").delete()

    def test_delete_criteria_success_returns_204(self, api_client):
        """DELETE should return 204 on success."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
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

        response = api_client.delete(
            f"/api/v2/smart-block-criteria/{criteria.id}",
        )
        assert response.status_code == 204

    def test_delete_criteria_removes_from_db(self, api_client):
        """DELETE should remove criteria from database."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
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

        api_client.delete(f"/api/v2/smart-block-criteria/{criteria.id}")
        assert SmartBlockCriteria.objects.filter(id=criteria.id).count() == 0

    def test_delete_not_found_returns_404(self, api_client):
        """DELETE non-existent criteria should return 404."""
        response = api_client.delete("/api/v2/smart-block-criteria/999999")
        assert response.status_code == 404

    def test_delete_no_auth_fails(self, client):
        """DELETE without auth should return 403."""
        response = client.delete("/api/v2/smart-block-criteria/1")
        assert response.status_code == 403

    def test_delete_double_delete_returns_404(self, api_client):
        """DELETE already deleted criteria should return 404."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
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

        api_client.delete(f"/api/v2/smart-block-criteria/{criteria.id}")
        response = api_client.delete(
            f"/api/v2/smart-block-criteria/{criteria.id}",
        )
        assert response.status_code == 404

    def test_delete_returns_empty_body(self, api_client):
        """DELETE should return empty response body."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
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

        response = api_client.delete(
            f"/api/v2/smart-block-criteria/{criteria.id}",
        )
        assert response.content == b""

    def test_delete_one_criteria_others_remain(self, api_client):
        """DELETE one criteria should leave others."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )
        criteria1 = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )
        criteria2 = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="artist",
            condition="starts",
            value="Miles",
        )
        criteria3 = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="album",
            condition="ends",
            value="Collection",
        )

        api_client.delete(f"/api/v2/smart-block-criteria/{criteria2.id}")

        assert SmartBlockCriteria.objects.filter(id=criteria1.id).exists()
        assert not SmartBlockCriteria.objects.filter(id=criteria2.id).exists()
        assert SmartBlockCriteria.objects.filter(id=criteria3.id).exists()

    def test_delete_id_zero_returns_404(self, api_client):
        """DELETE with id=0 should return 404."""
        response = api_client.delete("/api/v2/smart-block-criteria/0")
        assert response.status_code == 404

    def test_delete_negative_id_returns_404(self, api_client):
        """DELETE with negative id should return 404."""
        response = api_client.delete("/api/v2/smart-block-criteria/-1")
        assert response.status_code == 404

    def test_delete_sql_injection_attempt(self, api_client):
        """DELETE with SQL injection in id should be handled safely."""
        response = api_client.delete("/api/v2/smart-block-criteria/1 OR 1=1")
        assert response.status_code == 404
