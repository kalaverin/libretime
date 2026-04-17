"""Tests for SmartBlockCriteria UPDATE endpoint (T243)."""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockCriteria


@pytest.mark.django_db(transaction=True)
class TestSmartBlockCriteriaViewSetUpdate:
    """Test SmartBlockCriteria UPDATE endpoint - PATCH/PUT /api/v2/smart-block-criteria/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockCriteria.objects.all().delete()
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testsbcr").delete()

    def test_patch_update_value_success(self, api_client):
        """PATCH value should update criteria."""
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

        response = api_client.patch(
            f"/api/v2/smart-block-criteria/{criteria.id}",
            json.dumps({"value": "Rock"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["value"] == "Rock"

    def test_patch_update_condition(self, api_client):
        """PATCH condition should update criteria."""
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

        response = api_client.patch(
            f"/api/v2/smart-block-criteria/{criteria.id}",
            json.dumps({"condition": "starts"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["condition"] == "starts"

    def test_patch_update_criteria(self, api_client):
        """PATCH criteria field should update."""
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

        response = api_client.patch(
            f"/api/v2/smart-block-criteria/{criteria.id}",
            json.dumps({"criteria": "artist"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["criteria"] == "artist"

    def test_patch_partial_does_not_affect_other_fields(self, api_client):
        """PATCH should only update specified fields."""
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

        response = api_client.patch(
            f"/api/v2/smart-block-criteria/{criteria.id}",
            json.dumps({"value": "Rock"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "Rock"
        assert data["criteria"] == "genre"
        assert data["condition"] == "contains"

    def test_put_full_update_success(self, api_client):
        """PUT should update all fields."""
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

        response = api_client.put(
            f"/api/v2/smart-block-criteria/{criteria.id}",
            json.dumps(
                {
                    "block": block.id,
                    "criteria": "artist",
                    "condition": "starts",
                    "value": "The",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["criteria"] == "artist"
        assert data["condition"] == "starts"
        assert data["value"] == "The"

    def test_update_not_found_returns_404(self, api_client):
        """UPDATE non-existent criteria should return 404."""
        response = api_client.patch(
            "/api/v2/smart-block-criteria/999999",
            json.dumps({"value": "Rock"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_update_no_auth_fails(self, client):
        """UPDATE without auth should return 403."""
        response = client.patch(
            "/api/v2/smart-block-criteria/1",
            json.dumps({"value": "Rock"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_update_change_block(self, api_client):
        """PATCH to change block should work."""
        user = baker.make(User, username="testsbcr_user")
        block1 = baker.make(
            SmartBlock,
            name="Block 1",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )
        block2 = baker.make(
            SmartBlock,
            name="Block 2",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )
        criteria = baker.make(
            SmartBlockCriteria,
            block=block1,
            criteria="genre",
            condition="contains",
            value="Jazz",
        )

        response = api_client.patch(
            f"/api/v2/smart-block-criteria/{criteria.id}",
            json.dumps({"block": block2.id}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["block"] == block2.id

    def test_update_empty_value_fails(self, api_client):
        """UPDATE with empty value should fail."""
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

        response = api_client.patch(
            f"/api/v2/smart-block-criteria/{criteria.id}",
            json.dumps({"value": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400
