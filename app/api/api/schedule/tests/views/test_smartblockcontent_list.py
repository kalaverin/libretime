"""Tests for SmartBlockContents LIST endpoint (T239)."""

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockContent
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestSmartBlockContentViewSetList:
    """Test SmartBlockContents LIST endpoint - GET /api/v2/smart-block-contents."""

    def setup_method(self):
        """Clean up before each test."""
        SmartBlockContent.objects.all().delete()
        SmartBlock.objects.all().delete()
        File.objects.all().delete()
        User.objects.filter(username__startswith="testsbc").delete()

    def test_list_empty_returns_200(self, api_client):
        """LIST empty should return 200 with empty list."""
        response = api_client.get("/api/v2/smart-block-contents")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_content(self, api_client):
        """LIST should return single content with correct fields."""
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
        content = baker.make(
            SmartBlockContent,
            block=block,
            file=file_obj,
            position=1,
            offset=0,
        )

        response = api_client.get("/api/v2/smart-block-contents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["block"] == block.id
        assert data[0]["file"] == file_obj.id
        assert data[0]["position"] == 1

    def test_list_multiple_contents(self, api_client):
        """LIST should return multiple contents."""
        user = baker.make(User, username="testsbc_user")
        block = baker.make(
            SmartBlock,
            name="Static Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        file1 = baker.make(
            File,
            name="file1.mp3",
            mime="audio/mp3",
            owner=user,
        )
        file2 = baker.make(
            File,
            name="file2.mp3",
            mime="audio/mp3",
            owner=user,
        )

        baker.make(
            SmartBlockContent,
            block=block,
            file=file1,
            position=1,
            offset=0,
        )
        baker.make(
            SmartBlockContent,
            block=block,
            file=file2,
            position=2,
            offset=0,
        )

        response = api_client.get("/api/v2/smart-block-contents")
        assert response.status_code == 200
        assert len(response.json()) == 2

    @pytest.mark.xfail(reason="T328: filter by block not implemented")
    def test_list_filter_by_block(self, api_client):
        """LIST should filter by block parameter."""
        user = baker.make(User, username="testsbc_user")
        block1 = baker.make(
            SmartBlock,
            name="Block 1",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        block2 = baker.make(
            SmartBlock,
            name="Block 2",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        file1 = baker.make(
            File,
            name="file1.mp3",
            mime="audio/mp3",
            owner=user,
        )
        file2 = baker.make(
            File,
            name="file2.mp3",
            mime="audio/mp3",
            owner=user,
        )

        baker.make(
            SmartBlockContent,
            block=block1,
            file=file1,
            position=1,
            offset=0,
        )
        baker.make(
            SmartBlockContent,
            block=block2,
            file=file2,
            position=1,
            offset=0,
        )

        response = api_client.get(
            f"/api/v2/smart-block-contents?block={block1.id}",
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["block"] == block1.id

    @pytest.mark.xfail(reason="T329: ordering by position not implemented")
    def test_list_contents_ordered_by_position(self, api_client):
        """LIST should be ordered by position."""
        user = baker.make(User, username="testsbc_user")
        block = baker.make(
            SmartBlock,
            name="Static Block",
            kind=SmartBlock.Kind.STATIC,
            owner=user,
        )
        file1 = baker.make(
            File,
            name="file1.mp3",
            mime="audio/mp3",
            owner=user,
        )
        file2 = baker.make(
            File,
            name="file2.mp3",
            mime="audio/mp3",
            owner=user,
        )
        file3 = baker.make(
            File,
            name="file3.mp3",
            mime="audio/mp3",
            owner=user,
        )

        baker.make(
            SmartBlockContent,
            block=block,
            file=file1,
            position=3,
            offset=0,
        )
        baker.make(
            SmartBlockContent,
            block=block,
            file=file2,
            position=1,
            offset=0,
        )
        baker.make(
            SmartBlockContent,
            block=block,
            file=file3,
            position=2,
            offset=0,
        )

        response = api_client.get("/api/v2/smart-block-contents")
        assert response.status_code == 200
        positions = [item["position"] for item in response.json()]
        assert positions == [1, 2, 3]

    def test_list_no_auth_fails(self, client):
        """LIST without auth should return 403."""
        response = client.get("/api/v2/smart-block-contents")
        assert response.status_code == 403

    def test_list_returns_all_fields(self, api_client):
        """LIST should return all serializer fields."""
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

        baker.make(
            SmartBlockContent,
            block=block,
            file=file_obj,
            position=1,
            offset=0.5,
            cue_in="00:00:05",
            cue_out="00:03:30",
        )

        response = api_client.get("/api/v2/smart-block-contents")
        assert response.status_code == 200
        data = response.json()[0]
        expected_fields = {
            "id",
            "block",
            "file",
            "position",
            "offset",
            "length",
            "cue_in",
            "cue_out",
            "fade_in",
            "fade_out",
        }
        assert set(data.keys()) == expected_fields

    def test_list_with_cue_points(self, api_client):
        """LIST should include cue point fields."""
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

        baker.make(
            SmartBlockContent,
            block=block,
            file=file_obj,
            position=1,
            offset=0,
            cue_in="00:00:10",
            cue_out="00:04:00",
        )

        response = api_client.get("/api/v2/smart-block-contents")
        data = response.json()[0]
        assert data["cue_in"] == "00:00:10"
        assert data["cue_out"] == "00:04:00"
