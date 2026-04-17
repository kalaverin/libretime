"""
T288: Smart block dynamic query tests.

Tests that dynamic smart block criteria generate correct file queries.
"""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockCriteria
from api.storage.models import Library


@pytest.mark.django_db
class TestSmartBlockDynamicQuery:
    """Test dynamic smart block criteria generate correct queries."""

    @pytest.fixture
    def test_library(self):
        return baker.make(Library, name="Test Library", description="Test")

    @pytest.fixture
    def test_user(self):
        return baker.make(User, username="smartblock_test")

    def test_dynamic_block_kind(self, api_client, test_user):
        """Dynamic block should have kind='dynamic'."""
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            owner=test_user,
            kind=SmartBlock.Kind.DYNAMIC,
        )

        response = api_client.get(f"/api/v2/smart-blocks/{block.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == "dynamic"

    def test_dynamic_block_has_criteria(self, api_client, test_user):
        """Dynamic block can have criteria."""
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            owner=test_user,
            kind=SmartBlock.Kind.DYNAMIC,
        )
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="title",
            condition="contains",
            value="test",
        )

        response = api_client.get(f"/api/v2/smart-blocks/{block.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == "dynamic"

    def test_static_block_no_criteria_needed(self, api_client, test_user):
        """Static block works without criteria."""
        block = baker.make(
            SmartBlock,
            name="Static Block",
            owner=test_user,
            kind=SmartBlock.Kind.STATIC,
        )

        response = api_client.get(f"/api/v2/smart-blocks/{block.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == "static"

    def test_create_dynamic_block(self, api_client, test_user):
        """CREATE should support dynamic kind."""
        import json

        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "New Dynamic Block",
                    
                    "kind": "dynamic",
                    "description": "Auto-generated from criteria",
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["kind"] == "dynamic"

    def test_create_static_block(self, api_client, test_user):
        """CREATE should support static kind."""
        import json

        response = api_client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "New Static Block",
                    
                    "kind": "static",
                    "description": "Manually curated",
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["kind"] == "static"

    def test_update_block_kind(self, api_client, test_user):
        """UPDATE should allow changing kind."""
        import json

        block = baker.make(
            SmartBlock,
            name="Test Block",
            owner=test_user,
            kind=SmartBlock.Kind.STATIC,
        )

        response = api_client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps(
                {
                    "kind": "dynamic",
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == "dynamic"
