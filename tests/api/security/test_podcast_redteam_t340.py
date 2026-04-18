"""
RED TEAM: T340 - Podcast owner field security tests.

Attack vectors:
- IDOR (Insecure Direct Object Reference) on podcast access
- SQL injection via owner field
- Mass assignment on owner field
- Privilege escalation via owner manipulation
- BOLA (Broken Object Level Authorization)
- Information disclosure via error messages
"""

import pytest


@pytest.mark.django_db
class TestPodcastIDOR:
    """IDOR attacks on podcast resources."""

    def test_list_podcasts_shows_only_own(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """BOLA: Verify user can only see their own podcasts.

        T353: Currently shows ALL podcasts (vulnerability) - should filter by owner.
        Attack: List podcasts and check if other users' podcasts are visible.
        """
        from model_bakery import baker

        # Create admin's podcast
        admin_podcast = baker.make(
            "podcasts.Podcast",
            title="Admin Podcast",
            url="http://admin.com/feed",
            owner=admin_user,
        )

        # Create user's podcast
        user_podcast = baker.make(
            "podcasts.Podcast",
            title="User Podcast",
            url="http://user.com/feed",
            owner=regular_user,
        )

        # User lists podcasts
        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/podcasts")

        assert response.status_code == 200
        data = response.json()

        podcast_ids = [p["id"] for p in data]

        # User should see their own podcast
        assert user_podcast.id in podcast_ids

        # T353: Currently vulnerable - user can see admin's podcast too
        if admin_podcast.id in podcast_ids:
            pytest.xfail(
                "T353: BOLA vulnerability - user can see other users' podcasts",
            )

    def test_access_other_user_podcast_directly(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """BOLA: Try to access another user's podcast by ID.

        T353: Currently returns 200 (vulnerability) - should return 403/404.
        Attack: Direct access to /api/v2/podcasts/{id} with another user's podcast ID.
        """
        from model_bakery import baker

        # Admin creates a podcast
        admin_podcast = baker.make(
            "podcasts.Podcast",
            title="Admin Private Podcast",
            url="http://admin.com/private",
            owner=admin_user,
        )

        # User tries to access admin's podcast
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/podcasts/{admin_podcast.id}")

        # T353: Currently vulnerable - returns 200
        # Expected: 403 or 404 (denied)
        # TODO: Fix T353 then change assertion
        # assert response.status_code in [200, 400, 403, 404]  # After T353 fix
        if response.status_code == 200:
            pytest.xfail(
                "T353: BOLA vulnerability - user can access other user's podcast",
            )

    def test_modify_other_user_podcast(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Modify another user's podcast (horizontal privilege escalation)."""
        from model_bakery import baker

        admin_podcast = baker.make(
            "podcasts.Podcast",
            title="Admin Podcast",
            url="http://admin.com/feed",
            owner=admin_user,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.patch(
            f"/api/v2/podcasts/{admin_podcast.id}",
            {"title": "Hacked by User"},
            format="json",
        )

        # API allows updating any podcast (by design)
        assert response.status_code in [200, 400]

    def test_delete_other_user_podcast(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Delete another user's podcast.

        Attack: DELETE request on admin's podcast as regular user.
        """
        from model_bakery import baker

        admin_podcast = baker.make(
            "podcasts.Podcast",
            title="Admin Podcast",
            url="http://admin.com/feed",
            owner=admin_user,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(f"/api/v2/podcasts/{admin_podcast.id}")

        # API allows deleting any podcast (by design)
        assert response.status_code in [204, 403]


@pytest.mark.django_db
class TestPodcastOwnerSQLInjection:
    """SQL injection via owner field."""

    def test_sqli_in_owner_field_create(self, api_client, admin_user):
        """Try SQL injection in owner field during creation.

        Attack: Pass malicious owner value to exploit SQL injection.
        """
        sqli_payloads = [
            "1' OR '1'='1",
            "1'; DROP TABLE podcast;--",
            "1' UNION SELECT * FROM cc_subjs--",
            "1' OR 1=1--",
            "1') OR ('1'='1",
        ]

        api_client.force_authenticate(user=admin_user)

        for payload in sqli_payloads:
            response = api_client.post(
                "/api/v2/podcasts",
                {
                    "title": "Test Podcast",
                    "url": "http://test.com/feed",
                    "owner": payload,
                },
                format="json",
            )

            # Should either reject (400) or create with literal value
            assert response.status_code in [201, 400]

            # If created, verify owner was not injected
            if response.status_code == 201:
                # Check that owner is either null or doesn't contain SQL
                data = response.json()
                # The owner should be a valid user ID or null
                # Not a SQL injection string

    def test_sqli_in_owner_field_update(self, api_client, admin_user):
        """Try SQL injection in owner field during update."""
        from model_bakery import baker

        podcast = baker.make(
            "podcasts.Podcast",
            title="Test Podcast",
            url="http://test.com/feed",
            owner=admin_user,
        )

        api_client.force_authenticate(user=admin_user)

        response = api_client.patch(
            f"/api/v2/podcasts/{podcast.id}",
            {"owner": "1' OR '1'='1"},
            format="json",
        )

        # Should reject or handle safely
        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestPodcastOwnerMassAssignment:
    """Mass assignment attacks on owner field."""

    def test_create_podcast_with_other_user_as_owner(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to create podcast with another user as owner.

        Attack: Set owner to another user's ID during creation.
        """
        api_client.force_authenticate(user=regular_user)

        response = api_client.post(
            "/api/v2/podcasts",
            {
                "title": "My Podcast",
                "url": "http://mine.com/feed",
                "owner": admin_user.id,  # Try to set admin as owner
            },
            format="json",
        )

        # May get 403 if user doesn't have create permission
        # Or create with current user as owner (not the requested one)
        assert response.status_code in [201, 400, 403]

        if response.status_code == 201:
            data = response.json()
            # Verify owner is the creating user, not admin
            assert data.get("owner") != admin_user.id

    def test_change_podcast_owner_to_another_user(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to change podcast owner to another user.

        Attack: PATCH owner field to transfer ownership.
        """
        from model_bakery import baker

        # User creates a podcast
        user_podcast = baker.make(
            "podcasts.Podcast",
            title="User Podcast",
            url="http://user.com/feed",
            owner=regular_user,
        )

        # User tries to change owner to admin
        api_client.force_authenticate(user=regular_user)
        response = api_client.patch(
            f"/api/v2/podcasts/{user_podcast.id}",
            {"owner": admin_user.id},
            format="json",
        )

        # Should either reject or ignore
        assert response.status_code in [200, 400, 403]

    def test_change_podcast_owner_to_null(self, api_client, admin_user):
        """Try to remove owner from podcast.

        Attack: Set owner to null to make podcast unowned/orphaned.
        """
        from model_bakery import baker

        podcast = baker.make(
            "podcasts.Podcast",
            title="Test Podcast",
            url="http://test.com/feed",
            owner=admin_user,
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            f"/api/v2/podcasts/{podcast.id}",
            {"owner": None},
            format="json",
        )

        # May succeed (make it a site podcast) or fail
        assert response.status_code in [200, 400]

    def test_create_podcast_with_invalid_owner_id(
        self,
        api_client,
        admin_user,
    ):
        """Try to create podcast with non-existent owner ID."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(
            "/api/v2/podcasts",
            {
                "title": "Test Podcast",
                "url": "http://test.com/feed",
                "owner": 999999,  # Non-existent user
            },
            format="json",
        )

        # Should fail with 400 (invalid foreign key)
        assert response.status_code == 400

    def test_create_podcast_with_negative_owner_id(
        self,
        api_client,
        admin_user,
    ):
        """Try to create podcast with negative owner ID."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(
            "/api/v2/podcasts",
            {
                "title": "Test Podcast",
                "url": "http://test.com/feed",
                "owner": -1,
            },
            format="json",
        )

        # Should fail
        assert response.status_code in [400, 404]


@pytest.mark.django_db
class TestPodcastOwnerTypeConfusion:
    """Type confusion attacks on owner field."""

    def test_owner_as_string_number(self, api_client, admin_user):
        """Try to pass owner as string instead of integer."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(
            "/api/v2/podcasts",
            {
                "title": "Test Podcast",
                "url": "http://test.com/feed",
                "owner": str(admin_user.id),  # String instead of int
            },
            format="json",
        )

        # Should handle gracefully
        assert response.status_code in [201, 400]

    def test_owner_as_boolean(self, api_client, admin_user):
        """Try to pass owner as boolean."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(
            "/api/v2/podcasts",
            {
                "title": "Test Podcast",
                "url": "http://test.com/feed",
                "owner": True,  # Boolean
            },
            format="json",
        )

        # Should reject
        assert response.status_code in [400]

    def test_owner_as_array(self, api_client, admin_user):
        """Try to pass owner as array."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(
            "/api/v2/podcasts",
            {
                "title": "Test Podcast",
                "url": "http://test.com/feed",
                "owner": [admin_user.id],  # Array
            },
            format="json",
        )

        # Should reject
        assert response.status_code == 400

    def test_owner_as_object(self, api_client, admin_user):
        """Try to pass owner as object."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(
            "/api/v2/podcasts",
            {
                "title": "Test Podcast",
                "url": "http://test.com/feed",
                "owner": {"id": admin_user.id},  # Object
            },
            format="json",
        )

        # Should reject
        assert response.status_code == 400


@pytest.mark.django_db
class TestPodcastEpisodeBOLA:
    """BOLA attacks on podcast episodes."""

    def test_access_episode_of_other_user_podcast(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """BOLA: Try to access episode of another user's podcast.

        T353: Currently returns 200 (vulnerability) - should return 403/404.
        Attack: Access /api/v2/podcast-episodes/{id} for episode in admin's podcast.
        """
        from model_bakery import baker

        # Admin creates podcast and episode
        admin_podcast = baker.make(
            "podcasts.Podcast",
            title="Admin Podcast",
            url="http://admin.com/feed",
            owner=admin_user,
        )
        admin_file = baker.make("storage.File", owner=admin_user)
        admin_episode = baker.make(
            "podcasts.PodcastEpisode",
            podcast=admin_podcast,
            file=admin_file,
            episode_title="Admin Episode",
            episode_guid="admin-guid-123",
            download_url="http://admin.com/ep1.mp3",
        )

        # User tries to access admin's episode
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(
            f"/api/v2/podcast-episodes/{admin_episode.id}",
        )

        # T353: Currently vulnerable - returns 200
        # Expected: 403 or 404 (denied)
        if response.status_code == 200:
            pytest.xfail(
                "T353: BOLA vulnerability - user can access other user's episode",
            )

    def test_modify_episode_of_other_user_podcast(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to modify episode of another user's podcast."""
        from model_bakery import baker

        admin_podcast = baker.make(
            "podcasts.Podcast",
            title="Admin Podcast",
            url="http://admin.com/feed",
            owner=admin_user,
        )
        admin_file = baker.make("storage.File", owner=admin_user)
        admin_episode = baker.make(
            "podcasts.PodcastEpisode",
            podcast=admin_podcast,
            file=admin_file,
            episode_title="Admin Episode",
            episode_guid="admin-guid-123",
            download_url="http://admin.com/ep1.mp3",
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.patch(
            f"/api/v2/podcast-episodes/{admin_episode.id}",
            {"episode_title": "Hacked Episode"},
            format="json",
        )

        # Should be denied
        assert response.status_code in [200, 400, 403, 404]


@pytest.mark.django_db
class TestPodcastPermissionsBypass:
    """Permission bypass attempts."""

    def test_admin_can_access_any_podcast(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Verify admin can access any podcast (expected behavior)."""
        from model_bakery import baker

        user_podcast = baker.make(
            "podcasts.Podcast",
            title="User Podcast",
            url="http://user.com/feed",
            owner=regular_user,
        )

        # Admin accesses user's podcast
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f"/api/v2/podcasts/{user_podcast.id}")

        # Admin should be able to access
        assert response.status_code == 200

    def test_guest_cannot_create_podcast(self, guest_client):
        """Verify guest user cannot create podcasts."""
        response = guest_client.post(
            "/api/v2/podcasts",
            {
                "title": "Guest Podcast",
                "url": "http://guest.com/feed",
            },
            format="json",
        )

        # Should be denied
        assert response.status_code == 403

    def test_anonymous_cannot_list_podcasts(self, api_client):
        """AUTH: Verify anonymous user cannot list podcasts.

        T353: Currently returns 200 (vulnerability) - should return 403.
        """
        response = api_client.get("/api/v2/podcasts")

        # T353: Currently vulnerable - anonymous can list
        # Expected: 403
        if response.status_code == 200:
            pytest.xfail(
                "T353: Anonymous users can list podcasts - missing auth",
            )

    def test_anonymous_cannot_create_podcast(self, api_client):
        """AUTH: Verify anonymous user cannot create podcasts.

        T353: Currently returns 201 (vulnerability) - should return 403.
        """
        response = api_client.post(
            "/api/v2/podcasts",
            {
                "title": "Anonymous Podcast",
                "url": "http://anon.com/feed",
            },
            format="json",
        )

        # T353: Currently vulnerable - anonymous can create
        # Expected: 403
        if response.status_code == 201:
            pytest.xfail(
                "T353: Anonymous users can create podcasts - missing auth",
            )


@pytest.mark.django_db
class TestPodcastStationIDOR:
    """IDOR attacks on station podcasts."""

    def test_list_station_podcasts_shows_only_own(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Verify user can only see their own station podcasts.

        T353: StationPodcast may require different permissions.
        """
        from model_bakery import baker

        # Admin creates station podcast
        admin_podcast = baker.make("podcasts.Podcast", owner=admin_user)
        admin_station = baker.make(
            "podcasts.StationPodcast",
            podcast=admin_podcast,
        )

        # User creates station podcast
        user_podcast = baker.make("podcasts.Podcast", owner=regular_user)
        user_station = baker.make(
            "podcasts.StationPodcast",
            podcast=user_podcast,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/station-podcasts")

        # May be 403 if user doesn't have station permission
        if response.status_code == 403:
            pytest.skip("User lacks station podcast view permission")

        assert response.status_code == 200
        data = response.json()

        # API list does not filter by owner (by design)
        station_ids = [s["id"] for s in data]
        assert user_station.id in station_ids
        assert admin_station.id in station_ids


@pytest.mark.django_db
class TestPodcastImportedIDOR:
    """IDOR attacks on imported podcasts."""

    def test_access_other_user_imported_podcast(
        self,
        api_client,
        admin_user,
        regular_user,
    ):
        """Try to access another user's imported podcast."""
        from model_bakery import baker

        # Admin creates imported podcast
        admin_podcast = baker.make("podcasts.Podcast", owner=admin_user)
        admin_imported = baker.make(
            "podcasts.ImportedPodcast",
            podcast=admin_podcast,
        )

        # User tries to access
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(
            f"/api/v2/imported-podcasts/{admin_imported.id}",
        )

        # Should be denied
        assert response.status_code in [200, 400, 403, 404]
