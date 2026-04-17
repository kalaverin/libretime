"""T270: Podcast RUD (Retrieve/Update/Delete) redteam security tests.

Red Team security tests for Podcast RUD endpoints.
Tests for BOLA (update/delete other's podcasts), BOPLA (mass assignment),
injection, and rate limiting vulnerabilities.
"""

import pytest

from api.podcasts.models import Podcast
from model_bakery import baker

# =============================================================================
# API1:2023 BOLA - Update/Delete Other Users' Podcasts
# =============================================================================


@pytest.mark.django_db
class TestPodcastRUDRedTeamBOLA:
    """BOLA: Access control on UPDATE/DELETE operations."""

    def test_bola_update_other_users_podcast(
        self,
        api_client,
        admin_user,
        regular_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        BOLA: Regular user can UPDATE admin's podcast.

        Should return 403, but if 200 - BOLA exists.
        """
        # Create admin's podcast
        admin_podcast = baker.make(
            Podcast,
            url=fake_url,
            title=f"Admin Podcast {fake_catch_phrase}",
            owner=admin_user,
        )

        # Regular user tries to update
        api_client.force_authenticate(user=regular_user)
        data = {
            "url": admin_podcast.url,
            "title": "HACKED BY REGULAR USER",
            "creator": "Attacker",
        }

        response = api_client.put(
            f"/api/v2/podcasts/{admin_podcast.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            pytest.xfail(
                "T723: BOLA - Regular user can UPDATE admin's podcast",
            )

    def test_bola_patch_other_users_podcast(
        self,
        api_client,
        admin_user,
        regular_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        BOLA: Regular user can PATCH admin's podcast.
        """
        admin_podcast = baker.make(
            Podcast,
            url=fake_url,
            title=f"Admin Podcast {fake_catch_phrase}",
            owner=admin_user,
        )

        api_client.force_authenticate(user=regular_user)
        data = {"title": "Patched by regular user"}

        response = api_client.patch(
            f"/api/v2/podcasts/{admin_podcast.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            pytest.xfail("T724: BOLA - Regular user can PATCH admin's podcast")

    def test_bola_delete_other_users_podcast(
        self,
        api_client,
        admin_user,
        regular_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        BOLA: Regular user can DELETE admin's podcast.

        CRITICAL: Data loss vulnerability.
        """
        admin_podcast = baker.make(
            Podcast,
            url=fake_url,
            title=f"Admin Podcast {fake_catch_phrase}",
            owner=admin_user,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(f"/api/v2/podcasts/{admin_podcast.id}")

        if response.status_code == 204:
            pytest.xfail(
                "T725: BOLA - Regular user can DELETE admin's podcast (CRITICAL)",
            )

    def test_bola_guest_user_update_podcast(
        self,
        api_client,
        admin_user,
        guest_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        BFLA: Guest user can UPDATE podcast.
        """
        podcast = baker.make(
            Podcast,
            url=fake_url,
            title=fake_catch_phrase,
            owner=admin_user,
        )

        api_client.force_authenticate(user=guest_user)
        data = {
            "url": podcast.url,
            "title": "Guest user hacked this",
        }

        response = api_client.put(
            f"/api/v2/podcasts/{podcast.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            pytest.xfail("T726: BFLA - Guest user can UPDATE podcast")

    def test_bola_retrieve_other_users_private_podcast(
        self,
        api_client,
        admin_user,
        regular_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        BOLA: Regular user can RETRIEVE admin's private podcast details.

        Already confirmed in LIST, but RETRIEVE may expose more fields.
        """
        admin_podcast = baker.make(
            Podcast,
            url=fake_url,
            title=f"Admin Private {fake_catch_phrase}",
            description="Secret description",
            owner=admin_user,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f"/api/v2/podcasts/{admin_podcast.id}")

        if response.status_code == 200:
            data = response.json()
            if data.get("description") == "Secret description":
                pytest.xfail(
                    "T727: BOLA - Regular user can RETRIEVE admin's private podcast",
                )


# =============================================================================
# API3:2023 BOPLA - Mass Assignment via UPDATE/PATCH
# =============================================================================


@pytest.mark.django_db
class TestPodcastRUDRedTeamBOPLA:
    """BOPLA: Mass assignment on UPDATE/PATCH."""

    def test_bopla_update_change_owner(
        self,
        api_client,
        admin_user,
        regular_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        BOPLA: Update owner_id via PUT (take ownership of podcast).

        Regular user takes ownership of admin's podcast.
        """
        admin_podcast = baker.make(
            Podcast,
            url=fake_url,
            title=f"Admin Podcast {fake_catch_phrase}",
            owner=admin_user,
        )

        api_client.force_authenticate(user=regular_user)
        data = {
            "url": admin_podcast.url,
            "title": admin_podcast.title,
            "owner": regular_user.id,  # Try to change owner
        }

        response = api_client.put(
            f"/api/v2/podcasts/{admin_podcast.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("owner") == regular_user.id:
                pytest.xfail(
                    "T728: BOPLA - Owner changed via UPDATE (privilege escalation)",
                )

    def test_bopla_patch_change_owner(
        self,
        api_client,
        admin_user,
        regular_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        BOPLA: Change owner via PATCH.
        """
        admin_podcast = baker.make(
            Podcast,
            url=fake_url,
            title=f"Admin Podcast {fake_catch_phrase}",
            owner=admin_user,
        )

        api_client.force_authenticate(user=regular_user)
        data = {"owner": regular_user.id}

        response = api_client.patch(
            f"/api/v2/podcasts/{admin_podcast.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("owner") == regular_user.id:
                pytest.xfail("T729: BOPLA - Owner changed via PATCH")

    def test_bopla_patch_extra_fields(
        self,
        api_client,
        admin_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        BOPLA: PATCH accepts unknown fields silently.
        """
        podcast = baker.make(
            Podcast,
            url=fake_url,
            title=fake_catch_phrase,
            owner=admin_user,
        )

        data = {
            "title": "Valid title",
            "is_system": True,  # Unknown field
            "internal_id": 12345,  # Unknown field
        }

        response = api_client.patch(
            f"/api/v2/podcasts/{podcast.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            pytest.xfail("T730: BOPLA - PATCH silently ignores extra fields")

    def test_bopla_update_id_field(
        self,
        api_client,
        admin_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        BOPLA: Try to change ID via UPDATE.
        """
        podcast = baker.make(
            Podcast,
            url=fake_url,
            title=fake_catch_phrase,
            owner=admin_user,
        )

        data = {
            "id": 999999,  # Try to change ID
            "url": podcast.url,
            "title": podcast.title,
        }

        response = api_client.put(
            f"/api/v2/podcasts/{podcast.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("id") == 999999:
                pytest.xfail("T731: BOPLA - ID can be changed via UPDATE")


# =============================================================================
# API8:2023 Injection in UPDATE/PATCH
# =============================================================================


@pytest.mark.django_db
class TestPodcastRUDRedTeamInjection:
    """Injection via UPDATE/PATCH fields."""

    def test_xss_via_update_title(
        self,
        api_client,
        admin_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        Stored XSS: Update title with script tag.
        """
        podcast = baker.make(
            Podcast,
            url=fake_url,
            title=fake_catch_phrase,
            owner=admin_user,
        )

        data = {
            "url": podcast.url,
            "title": "<script>alert('XSS')</script>",
        }

        response = api_client.put(
            f"/api/v2/podcasts/{podcast.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            result = response.json()
            if "<script>" in str(result.get("title", "")):
                pytest.xfail("T732: Stored XSS via UPDATE title")

    def test_xss_via_patch_description(
        self,
        api_client,
        admin_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        Stored XSS: PATCH description with script.
        """
        podcast = baker.make(
            Podcast,
            url=fake_url,
            title=fake_catch_phrase,
            owner=admin_user,
        )

        data = {"description": "<img src=x onerror=alert(1)>"}

        response = api_client.patch(
            f"/api/v2/podcasts/{podcast.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            result = response.json()
            if "onerror=" in str(result.get("description", "")):
                pytest.xfail("T733: Stored XSS via PATCH description")

    def test_sqli_via_update_fields(
        self,
        api_client,
        admin_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        SQLi: Injection in UPDATE fields.
        """
        podcast = baker.make(
            Podcast,
            url=fake_url,
            title=fake_catch_phrase,
            owner=admin_user,
        )

        data = {
            "url": podcast.url,
            "title": "'; DROP TABLE podcast--",
        }

        response = api_client.put(
            f"/api/v2/podcasts/{podcast.id}",
            data,
            format="json",
        )

        if response.status_code == 500:
            error_text = str(response.content).lower()
            if "sql" in error_text or "syntax" in error_text:
                pytest.xfail("T734: SQLi via UPDATE fields")


# =============================================================================
# API4:2023 Resource Consumption
# =============================================================================


@pytest.mark.django_db
class TestPodcastRUDRedTeamResourceConsumption:
    """Resource consumption on RUD operations."""

    def test_rapid_update_requests(
        self,
        api_client,
        admin_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        Rate limiting: Rapid UPDATE requests.
        """
        podcast = baker.make(
            Podcast,
            url=fake_url,
            title=fake_catch_phrase,
            owner=admin_user,
        )

        success_count = 0
        for i in range(30):
            data = {"title": f"Update {i}"}
            response = api_client.patch(
                f"/api/v2/podcasts/{podcast.id}",
                data,
                format="json",
            )
            if response.status_code == 200:
                success_count += 1

        if success_count == 30:
            pytest.xfail("T735: No rate limiting on Podcast UPDATE")

    def test_rapid_delete_requests(
        self,
        api_client,
        admin_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        Rate limiting: Rapid DELETE requests (DoS).
        """
        success_count = 0
        for i in range(20):
            # Create then immediately delete
            podcast = baker.make(
                Podcast,
                url=f"{fake_url}/{i}",
                title=f"{fake_catch_phrase} {i}",
                owner=admin_user,
            )
            response = api_client.delete(f"/api/v2/podcasts/{podcast.id}")
            if response.status_code == 204:
                success_count += 1

        if success_count == 20:
            pytest.xfail("T736: No rate limiting on Podcast DELETE")


# =============================================================================
# IDOR and Enumeration
# =============================================================================


@pytest.mark.django_db
class TestPodcastRUDRedTeamIDOR:
    """IDOR and enumeration tests."""

    def test_idor_sequential_id_access(
        self,
        api_client,
        admin_user,
        regular_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        IDOR: Access podcasts by sequential ID enumeration.
        """
        # Create multiple admin podcasts
        for i in range(5):
            baker.make(
                Podcast,
                url=f"{fake_url}/admin{i}",
                title=f"Admin Podcast {i}",
                owner=admin_user,
            )

        api_client.force_authenticate(user=regular_user)

        # Try to access sequential IDs
        accessible_count = 0
        for i in range(1, 10):
            response = api_client.get(f"/api/v2/podcasts/{i}")
            if response.status_code == 200:
                accessible_count += 1

        if accessible_count >= 3:
            pytest.xfail(
                f"T737: IDOR - Sequential access to {accessible_count} podcasts",
            )

    def test_error_message_enumeration(self, api_client, regular_user):
        """
        Information disclosure: Different errors for existent vs non-existent.
        """
        api_client.force_authenticate(user=regular_user)

        # Non-existent ID
        response_fake = api_client.get("/api/v2/podcasts/999999")
        # ID 0 (unlikely to exist)
        response_zero = api_client.get("/api/v2/podcasts/0")

        # If different status codes, enumeration is possible
        if response_fake.status_code != response_zero.status_code:
            pytest.xfail("T738: Error messages allow ID enumeration")


# =============================================================================
# Authentication Bypass
# =============================================================================


@pytest.mark.django_db
class TestPodcastRUDRedTeamAuthentication:
    """Authentication bypass tests."""

    def test_update_without_auth(
        self,
        api_client,
        admin_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        Unauthenticated UPDATE should fail.
        """
        podcast = baker.make(
            Podcast,
            url=fake_url,
            title=fake_catch_phrase,
            owner=admin_user,
        )

        api_client.logout()
        data = {"title": "Hacked"}

        response = api_client.patch(
            f"/api/v2/podcasts/{podcast.id}",
            data,
            format="json",
        )

        assert response.status_code == 403

    def test_delete_without_auth(
        self,
        api_client,
        admin_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        Unauthenticated DELETE should fail.
        """
        podcast = baker.make(
            Podcast,
            url=fake_url,
            title=fake_catch_phrase,
            owner=admin_user,
        )

        api_client.logout()
        response = api_client.delete(f"/api/v2/podcasts/{podcast.id}")

        assert response.status_code == 403

    def test_method_override_to_bypass_auth(
        self,
        api_client,
        admin_user,
        fake_url,
        fake_catch_phrase,
    ):
        """
        Try to bypass auth check via method override.
        """
        podcast = baker.make(
            Podcast,
            url=fake_url,
            title=fake_catch_phrase,
            owner=admin_user,
        )

        api_client.logout()
        data = {"title": "Hacked via override"}

        # Try to PATCH via GET with override header
        response = api_client.get(
            f"/api/v2/podcasts/{podcast.id}",
            HTTP_X_HTTP_METHOD_OVERRIDE="PATCH",
        )

        # Should not work without auth
        if response.status_code == 200 and "Hacked" in str(response.content):
            pytest.xfail("T739: Method override bypasses authentication")
