"""Tests for SmartBlockCriteria CREATE endpoint (T242)."""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockCriteria


@pytest.mark.django_db(transaction=True)
class TestSmartBlockCriteriaViewSetCreate:
    """Test SmartBlockCriteria CREATE endpoint - POST /api/v2/smart-block-criteria."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockCriteria.objects.all().delete()
        SmartBlock.objects.all().delete()
        User.objects.filter(username__startswith="testsbcr").delete()

    def test_create_criteria_success(self, api_client):
        """CREATE criteria should return 201."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": block.id,
                    "criteria": "genre",
                    "condition": "0",
                    "value": "Jazz",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["block"] == block.id
        assert data["criteria"] == "genre"
        assert data["condition"] == "0"
        assert data["value"] == "Jazz"

    def test_create_with_group(self, api_client):
        """CREATE with group should succeed."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": block.id,
                    "criteria": "genre",
                    "condition": "0",
                    "value": "Jazz",
                    "group": 1,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["group"] == 1

    def test_create_with_extra(self, api_client):
        """CREATE with extra should succeed."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": block.id,
                    "criteria": "genre",
                    "condition": "0",
                    "value": "Jazz",
                    "extra": "additional info",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["extra"] == "additional info"

    def test_create_missing_block_fails(self, api_client):
        """CREATE without block should return 400."""
        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "criteria": "genre",
                    "condition": "0",
                    "value": "Jazz",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_missing_criteria_fails(self, api_client):
        """CREATE without criteria should return 400."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": block.id,
                    "condition": "0",
                    "value": "Jazz",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_missing_condition_fails(self, api_client):
        """CREATE without condition should return 400."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": block.id,
                    "criteria": "genre",
                    "value": "Jazz",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_missing_value_fails(self, api_client):
        """CREATE without value should return 400."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": block.id,
                    "criteria": "genre",
                    "condition": "0",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_invalid_block_fails(self, api_client):
        """CREATE with non-existent block should return 400."""
        response = api_client.post(
            "/api/v2/smart-block-criteria",
            json.dumps(
                {
                    "block": 999999,
                    "criteria": "genre",
                    "condition": "0",
                    "value": "Jazz",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_no_auth_fails(self, client):
        """CREATE without auth should return 403."""
        response = client.post(
            "/api/v2/smart-block-criteria",
            json.dumps({"criteria": "genre"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_create_various_criteria_types(self, api_client):
        """CREATE with various criteria types should succeed."""
        user = baker.make(User, username="testsbcr_user")
        block = baker.make(
            SmartBlock,
            name="Dynamic Block",
            kind=SmartBlock.Kind.DYNAMIC,
            owner=user,
        )

        criteria_types = [
            ("genre", "0", "Rock"),
            ("artist_name", "4", "The"),
            ("album_title", "5", "Collection"),
            ("composer", "2", "Hit Song"),
        ]

        for crit, cond, val in criteria_types:
            response = api_client.post(
                "/api/v2/smart-block-criteria",
                json.dumps(
                    {
                        "block": block.id,
                        "criteria": crit,
                        "condition": cond,
                        "value": val,
                    },
                ),
                content_type="application/json",
            )
            assert response.status_code == 201, f"Failed for {crit}"
            assert response.json()["criteria"] == crit
