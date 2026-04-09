"""Tests for SmartBlockContents CREATE endpoint (T240)."""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockContent
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestSmartBlockContentViewSetCreate:
    """Test SmartBlockContents CREATE endpoint - POST /api/v2/smart-block-contents."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockContent.objects.all().delete()
        SmartBlock.objects.all().delete()
        File.objects.all().delete()
        User.objects.filter(username__startswith="testsbc").delete()

    def test_create_content_success(self, api_client):
        """CREATE content should return 201."""
        user = baker.make(User, username="testsbc_user")
        block = baker.make(
            SmartBlock,
            name="Static Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps(
                {
                    "block": block.id,
                    "file": file_obj.id,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["block"] == block.id
        assert data["file"] == file_obj.id
        assert data["position"] == 1

    def test_create_without_position_uses_null(self, api_client):
        """CREATE without position should default to null."""
        user = baker.make(User, username="testsbc_user")
        block = baker.make(
            SmartBlock,
            name="Static Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps(
                {
                    "block": block.id,
                    "file": file_obj.id,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["position"] is None

    def test_create_with_cue_points(self, api_client):
        """CREATE with cue points should succeed."""
        user = baker.make(User, username="testsbc_user")
        block = baker.make(
            SmartBlock,
            name="Static Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps(
                {
                    "block": block.id,
                    "file": file_obj.id,
                    "position": 1,
                    "offset": 0,
                    "cue_in": "00:00:05",
                    "cue_out": "00:03:30",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["cue_in"] == "00:00:05"
        assert data["cue_out"] == "00:03:30"

    @pytest.mark.xfail(reason="T330: missing block not validated")
    def test_create_missing_block_fails(self, api_client):
        """CREATE without block should return 400."""
        user = baker.make(User, username="testsbc_user")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps(
                {
                    "file": file_obj.id,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.xfail(reason="T331: missing file not validated")
    def test_create_missing_file_fails(self, api_client):
        """CREATE without file should return 400."""
        user = baker.make(User, username="testsbc_user")
        block = baker.make(
            SmartBlock,
            name="Static Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps(
                {
                    "block": block.id,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_invalid_block_fails(self, api_client):
        """CREATE with non-existent block should return 400."""
        user = baker.make(User, username="testsbc_user")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps(
                {
                    "block": 999999,
                    "file": file_obj.id,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_invalid_file_fails(self, api_client):
        """CREATE with non-existent file should return 400."""
        user = baker.make(User, username="testsbc_user")
        block = baker.make(
            SmartBlock,
            name="Static Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )

        response = api_client.post(
            "/api/v2/smart-block-contents",
            json.dumps(
                {
                    "block": block.id,
                    "file": 999999,
                    "position": 1,
                    "offset": 0,
                },
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_no_auth_fails(self, client):
        """CREATE without auth should return 403."""
        response = client.post(
            "/api/v2/smart-block-contents",
            json.dumps({"position": 1}),
            content_type="application/json",
        )
        assert response.status_code == 403
