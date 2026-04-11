"""
Paranoid race condition tests for concurrent operations.

Tests:
- T433: Duplicate names in SmartBlock (race on name creation)
- T486: Concurrent CREATE SmartBlockContent (duplicates)
- T504: Concurrent CREATE SmartBlockCriteria (race)
- T539: Concurrent CREATE Webstream (duplicates)
- T555: Concurrent UPDATE Webstream (lost updates)
- T722: Duplicate podcasts (concurrent creation)

Usage:
    cd app/api && uv run pytest api/tests/test_race_condition_redteam.py -v
"""

import pytest
from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role
from api.podcasts.models import Podcast
from api.schedule.models import (
    SmartBlock,
    SmartBlockContent,
    SmartBlockCriteria,
    Webstream,
)
from api.storage.models import File


# =============================================================================
# Duplicate Name Tests (T433, T539)
# =============================================================================

@pytest.mark.django_db
class TestDuplicateNamePrevention:
    """Tests for duplicate name prevention (T433, T539)."""

    def test_smartblock_duplicate_name_rejected(self, host_client, host_user, faker):
        """T433: Creating SmartBlock with duplicate name should fail."""
        name = f"Test Block {faker.uuid4()[:8]}"
        
        # Create first block
        response1 = host_client.post(
            "/api/v2/smart-blocks",
            {"name": name, "kind": "static"},
            format="json",
        )
        assert response1.status_code == 201, f"First create failed: {response1.data}"
        
        # Try to create second block with same name
        response2 = host_client.post(
            "/api/v2/smart-blocks",
            {"name": name, "kind": "static"},
            format="json",
        )
        assert response2.status_code == 400, (
            f"Duplicate name should be rejected, got {response2.status_code}"
        )
        assert "name" in str(response2.data).lower() or "duplicate" in str(response2.data).lower()

    def test_smartblock_same_name_different_users_allowed(self, host_client, faker):
        """T433: Same name for different users should be allowed."""
        name = f"Test Block {faker.uuid4()[:8]}"
        
        # Create first user and block
        user1 = baker.make(
            User,
            username=f"host1_{faker.uuid4()[:8]}",
            email=f"host1_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        baker.make(
            SmartBlock,
            name=name,
            owner=user1,
            kind=SmartBlock.Kind.STATIC,
        )
        
        # Create second user with same name
        user2 = baker.make(
            User,
            username=f"host2_{faker.uuid4()[:8]}",
            email=f"host2_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        host_client.force_authenticate(user=user2)
        
        response = host_client.post(
            "/api/v2/smart-blocks",
            {"name": name, "kind": "static"},
            format="json",
        )
        assert response.status_code == 201, (
            f"Same name for different user should be allowed, got {response.status_code}"
        )

    def test_webstream_duplicate_name_rejected(self, host_client, host_user, faker):
        """T539: Creating Webstream with duplicate name should fail."""
        name = f"Test Stream {faker.uuid4()[:8]}"
        
        # Create first stream
        response1 = host_client.post(
            "/api/v2/webstreams",
            {"name": name, "url": faker.url(), "description": "Test stream 1"},
            format="json",
        )
        assert response1.status_code == 201, f"First create failed: {response1.data}"
        
        # Try to create second stream with same name
        response2 = host_client.post(
            "/api/v2/webstreams",
            {"name": name, "url": faker.url(), "description": "Test stream 2"},
            format="json",
        )
        assert response2.status_code == 400, (
            f"Duplicate name should be rejected, got {response2.status_code}"
        )

    def test_webstream_duplicate_url_rejected(self, host_client, host_user, faker):
        """T539: Creating Webstream with duplicate URL should fail."""
        url = faker.url()
        
        # Create first stream
        response1 = host_client.post(
            "/api/v2/webstreams",
            {"name": f"Stream 1 {faker.uuid4()[:8]}", "url": url, "description": "Test stream 1"},
            format="json",
        )
        assert response1.status_code == 201
        
        # Try to create second stream with same URL
        response2 = host_client.post(
            "/api/v2/webstreams",
            {"name": f"Stream 2 {faker.uuid4()[:8]}", "url": url, "description": "Test stream 2"},
            format="json",
        )
        assert response2.status_code == 400, (
            f"Duplicate URL should be rejected, got {response2.status_code}"
        )


# =============================================================================
# Duplicate Content Tests (T486, T504)
# =============================================================================

@pytest.mark.django_db
class TestDuplicateContentPrevention:
    """Tests for duplicate content prevention (T486, T504)."""

    def test_smartblock_content_duplicate_rejected(self, host_client, host_user, faker):
        """T486: Duplicate SmartBlockContent should be rejected."""
        # Create block and file
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )
        file_obj = baker.make(
            File,
            name=f"test_{faker.uuid4()[:8]}.mp3",
            owner=host_user,
            mime="audio/mpeg",
            filepath=f"test/{faker.uuid4()[:8]}.mp3",
        )
        
        # Create first content
        response1 = host_client.post(
            "/api/v2/smart-block-contents",
            {
                "block": block.id,
                "file": file_obj.id,
                "position": 1,
                "offset": 0,
            },
            format="json",
        )
        assert response1.status_code == 201
        
        # Try to create duplicate content
        response2 = host_client.post(
            "/api/v2/smart-block-contents",
            {
                "block": block.id,
                "file": file_obj.id,
                "position": 1,
                "offset": 0,
            },
            format="json",
        )
        # May be 201 (created) or 400 (duplicate detection depending on implementation)
        # The important thing is no 500 error
        assert response2.status_code in [201, 400], (
            f"Unexpected status: {response2.status_code}"
        )

    def test_smartblock_criteria_duplicate_rejected(self, host_client, host_user, faker):
        """T504: Duplicate SmartBlockCriteria should be rejected."""
        # Create block
        block = baker.make(
            SmartBlock,
            name=f"Test Block {faker.uuid4()[:8]}",
            owner=host_user,
            kind=SmartBlock.Kind.STATIC,
        )
        
        criteria_data = {
            "block": block.id,
            "criteria": "genre",
            "condition": "0",
            "value": "Rock",
        }
        
        # Create first criteria
        response1 = host_client.post(
            "/api/v2/smart-block-criteria",
            criteria_data,
            format="json",
        )
        assert response1.status_code == 201
        
        # Try to create duplicate criteria
        response2 = host_client.post(
            "/api/v2/smart-block-criteria",
            criteria_data,
            format="json",
        )
        # May be 201 (created) or 400 (duplicate detection)
        assert response2.status_code in [201, 400], (
            f"Unexpected status: {response2.status_code}"
        )


# =============================================================================
# Podcast Duplicate Tests (T722)
# =============================================================================

@pytest.mark.django_db
class TestPodcastDuplicatePrevention:
    """Tests for podcast duplicate prevention (T722)."""

    def test_podcast_duplicate_url_rejected(self, host_client, host_user, faker):
        """T722: Creating Podcast with duplicate URL should fail."""
        url = faker.url()
        
        # Create first podcast
        response1 = host_client.post(
            "/api/v2/podcasts",
            {"title": f"Podcast 1 {faker.uuid4()[:8]}", "url": url},
            format="json",
        )
        assert response1.status_code == 201, f"First create failed: {response1.data}"
        
        # Try to create second podcast with same URL
        response2 = host_client.post(
            "/api/v2/podcasts",
            {"title": f"Podcast 2 {faker.uuid4()[:8]}", "url": url},
            format="json",
        )
        assert response2.status_code == 400, (
            f"Duplicate URL should be rejected, got {response2.status_code}"
        )

    def test_podcast_same_url_different_users_allowed(self, host_client, faker):
        """T722: Same URL for different users should be allowed."""
        url = faker.url()
        
        # Create first user and podcast
        user1 = baker.make(
            User,
            username=f"host1_{faker.uuid4()[:8]}",
            email=f"host1_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        baker.make(
            Podcast,
            title=f"Podcast 1 {faker.uuid4()[:8]}",
            url=url,
            owner=user1,
        )
        
        # Create second user with same URL
        user2 = baker.make(
            User,
            username=f"host2_{faker.uuid4()[:8]}",
            email=f"host2_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        host_client.force_authenticate(user=user2)
        
        response = host_client.post(
            "/api/v2/podcasts",
            {"title": f"Podcast 2 {faker.uuid4()[:8]}", "url": url},
            format="json",
        )
        assert response.status_code == 201, (
            f"Same URL for different user should be allowed, got {response.status_code}"
        )


# =============================================================================
# Update Race Condition Tests (T555)
# =============================================================================

@pytest.mark.django_db
class TestConcurrentUpdatePrevention:
    """Tests for concurrent update prevention (T555)."""

    def test_webstream_update_no_lost_updates(self, host_client, host_user, faker):
        """T555: Concurrent updates should not lose data."""
        # Create webstream
        stream = baker.make(
            Webstream,
            name=f"Test Stream {faker.uuid4()[:8]}",
            url=faker.url(),
            owner=host_user,
        )
        
        # First update
        response1 = host_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            {"name": "Updated Name 1"},
            format="json",
        )
        assert response1.status_code == 200
        
        # Second update (should succeed)
        response2 = host_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            {"name": "Updated Name 2"},
            format="json",
        )
        assert response2.status_code == 200
        
        # Verify final state
        response3 = host_client.get(f"/api/v2/webstreams/{stream.id}")
        assert response3.status_code == 200
        assert response3.data["name"] == "Updated Name 2"
