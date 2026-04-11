"""
BOLA (Broken Object Level Authorization) Tests for Podcast and File

Tests for:
- T663: Podcast LIST shows all podcasts
- T727: Podcast RETRIEVE other user's podcast
- T850: File RETRIEVE other user's file
- T853: File DELETE other user's file
"""

import pytest

from model_bakery import baker

from api.core.models import User
from api.core.models.role import Role
from api.podcasts.models import Podcast
from api.storage.models import File, Library


@pytest.mark.django_db
class TestBolaPodcastPrevention:
    """BOLA prevention tests for Podcast (T663, T727)."""

    def test_anonymous_get_podcasts_returns_403(self, anonymous_client):
        """Anonymous GET /podcasts returns 403."""
        response = anonymous_client.get("/api/v2/podcasts")
        assert response.status_code == 403

    def test_anonymous_post_podcasts_returns_403(self, anonymous_client):
        """Anonymous POST /podcasts returns 403."""
        response = anonymous_client.post("/api/v2/podcasts", {})
        assert response.status_code == 403

    def test_bola_list_podcasts_only_shows_own(
        self, host_client, host_user, faker, fake_url,
    ):
        """BOLA T663: HOST LIST should only show own podcasts."""
        # Create victim user with private podcast
        victim = baker.make(
            User,
            username=f"victim_{faker.uuid4()[:8]}",
            email=f"victim_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        victim_podcast = baker.make(
            Podcast,
            url=fake_url,
            title=f"Victim Podcast {faker.uuid4()[:8]}",
            description=faker.sentence(),
            owner=victim,
        )

        # Create own podcast
        own_podcast = baker.make(
            Podcast,
            url=fake_url,
            title=f"Own Podcast {faker.uuid4()[:8]}",
            owner=host_user,
        )

        response = host_client.get("/api/v2/podcasts")
        assert response.status_code == 200

        data = response.json()
        if isinstance(data, list):
            results = data
        else:
            results = data.get("results", data)

        result_ids = [p["id"] for p in results]

        # Should see own podcast
        assert own_podcast.id in result_ids, "HOST should see own podcast"

        # Should NOT see victim's podcast
        assert (
            victim_podcast.id not in result_ids
        ), "BOLA T663: HOST can see victim's podcast in LIST!"

    def test_bola_retrieve_other_host_podcast(
        self, host_client, host_user, faker, fake_url,
    ):
        """BOLA T727: HOST cannot RETRIEVE another HOST's podcast."""
        victim = baker.make(
            User,
            username=f"victim_{faker.uuid4()[:8]}",
            email=f"victim_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        victim_podcast = baker.make(
            Podcast,
            url=fake_url,
            title=f"Victim Podcast {faker.uuid4()[:8]}",
            description=faker.sentence(),
            owner=victim,
        )

        response = host_client.get(f"/api/v2/podcasts/{victim_podcast.id}")

        assert response.status_code in [
            403,
            404,
        ], f"BOLA T727: HOST retrieved victim's podcast, got {response.status_code}"


@pytest.mark.django_db
class TestBolaFilePrevention:
    """BOLA prevention tests for File (T850, T853)."""

    def test_anonymous_get_files_returns_403(self, anonymous_client):
        """Anonymous GET /files returns 403."""
        response = anonymous_client.get("/api/v2/files")
        assert response.status_code == 403

    def test_anonymous_post_files_returns_403(self, anonymous_client):
        """Anonymous POST /files returns 403."""
        response = anonymous_client.post("/api/v2/files", {})
        assert response.status_code == 403

    def test_bola_retrieve_other_host_file(
        self, host_client, host_user, faker,
    ):
        """BOLA T850: HOST cannot RETRIEVE another HOST's file."""
        victim = baker.make(
            User,
            username=f"victim_{faker.uuid4()[:8]}",
            email=f"victim_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            name=f"Lib {faker.uuid4()[:8]}",
            description=faker.sentence(),
        )
        victim_file = baker.make(
            File,
            name=f"victim_file_{faker.uuid4()[:8]}.mp3",
            filepath=f"/private/victim/{faker.uuid4()[:8]}.mp3",
            library=library,
            owner=victim,
        )

        response = host_client.get(f"/api/v2/files/{victim_file.id}")

        assert response.status_code in [
            403,
            404,
        ], f"BOLA T850: HOST retrieved victim's file, got {response.status_code}"

    def test_bola_delete_other_host_file(self, host_client, host_user, faker):
        """BOLA T853: HOST cannot DELETE another HOST's file."""
        victim = baker.make(
            User,
            username=f"victim_{faker.uuid4()[:8]}",
            email=f"victim_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            name=f"Lib {faker.uuid4()[:8]}",
            description=faker.sentence(),
        )
        victim_file = baker.make(
            File,
            name=f"victim_file_{faker.uuid4()[:8]}.mp3",
            filepath=f"/private/victim/{faker.uuid4()[:8]}.mp3",
            library=library,
            owner=victim,
        )
        victim_file_id = victim_file.id

        response = host_client.delete(f"/api/v2/files/{victim_file_id}")

        assert response.status_code in [
            403,
            404,
        ], f"BOLA T853: HOST deleted victim's file, got {response.status_code}"

        # Verify still exists
        assert File.objects.filter(id=victim_file_id).exists()

    def test_bola_list_files_only_shows_own(
        self, host_client, host_user, faker,
    ):
        """BOLA: HOST LIST should only show own files."""
        # Create victim user with private file
        victim = baker.make(
            User,
            username=f"victim_{faker.uuid4()[:8]}",
            email=f"victim_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        library = baker.make(
            Library,
            name=f"Lib {faker.uuid4()[:8]}",
            description=faker.sentence(),
        )
        victim_file = baker.make(
            File,
            name=f"victim_file_{faker.uuid4()[:8]}.mp3",
            filepath=f"/private/victim/{faker.uuid4()[:8]}.mp3",
            library=library,
            owner=victim,
        )

        # Create own file
        own_file = baker.make(
            File,
            name=f"own_file_{faker.uuid4()[:8]}.mp3",
            filepath=f"/private/own/{faker.uuid4()[:8]}.mp3",
            library=library,
            owner=host_user,
        )

        response = host_client.get("/api/v2/files")
        assert response.status_code == 200

        data = response.json()
        if isinstance(data, list):
            results = data
        else:
            results = data.get("results", data)

        result_ids = [f["id"] for f in results]

        # Should see own file
        assert own_file.id in result_ids, "HOST should see own file"

        # Should NOT see victim's file
        assert (
            victim_file.id not in result_ids
        ), "BOLA: HOST can see victim's file in LIST!"
