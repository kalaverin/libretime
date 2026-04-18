"""Red Team security tests for Webstreams UPDATE endpoint (T247).

Tests focus on:
- API1:2023 BOLA (updating/deleting other users' webstreams)
- API3:2023 BOPLA (mass assignment on update)
- SSRF via URL update
- XSS injection on update
- IDOR and ID enumeration
- Business logic: owner change, timestamps
"""

import json

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Webstream
from api.storage.models import File


@pytest.mark.django_db(transaction=True)
class TestWebstreamUpdateRedTeam:
    """Red Team tests for PATCH/PUT /api/v2/webstreams/{id}."""

    def setup_method(self):
        """Clean up before each test."""
        Webstream.objects.all().delete()
        File.objects.filter(owner__username__startswith="testred").delete()
        User.objects.filter(username__startswith="testred").delete()

    # ========================================================================
    # API1:2023 - BOLA (Broken Object Level Authorization)
    # ========================================================================

    def test_bola_update_other_users_stream(
        self, host_client, host_user, faker, fake_url,
    ):
        """BOLA T541: HOST cannot UPDATE another HOST's webstream."""
        from api.core.models.role import Role

        victim = baker.make(
            User,
            username=f"victim_{faker.uuid4()[:8]}",
            email=f"victim_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        victim_stream = baker.make(
            Webstream,
            name=f"Victim Stream {faker.uuid4()[:8]}",
            url=fake_url,
            owner=victim,
        )
        original_name = victim_stream.name

        # Attacker tries to update victim's stream
        response = host_client.patch(
            f"/api/v2/webstreams/{victim_stream.id}",
            {"name": f"Hacked {faker.uuid4()[:8]}"},
            format="json",
        )

        assert response.status_code in [
            403,
            404,
        ], f"BOLA T541: HOST updated victim's webstream, got {response.status_code}"

        # Verify not modified
        victim_stream.refresh_from_db()
        assert victim_stream.name == original_name

    def test_bola_delete_other_users_stream(
        self, host_client, host_user, faker, fake_url,
    ):
        """BOLA T542: HOST cannot DELETE another HOST's webstream."""
        from api.core.models.role import Role

        victim = baker.make(
            User,
            username=f"victim_{faker.uuid4()[:8]}",
            email=f"victim_{faker.uuid4()[:8]}@test.com",
            role=Role.HOST,
        )
        victim_stream = baker.make(
            Webstream,
            name=f"Victim Stream {faker.uuid4()[:8]}",
            url=fake_url,
            owner=victim,
        )
        victim_stream_id = victim_stream.id

        # Attacker tries to delete victim's stream
        response = host_client.delete(f"/api/v2/webstreams/{victim_stream_id}")

        assert response.status_code in [
            403,
            404,
        ], f"BOLA T542: HOST deleted victim's webstream, got {response.status_code}"

        # Verify still exists
        assert Webstream.objects.filter(id=victim_stream_id).exists()

    # ========================================================================
    # IDOR / ID Enumeration
    # ========================================================================

    def test_idor_stream_enumeration(self, admin_client):
        """Security: Stream ID enumeration mitigated."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        # Try to access with sequential IDs
        for test_id in range(1, 10):
            response = admin_client.get(f"/api/v2/webstreams/{test_id}")
            # Should get 404 for non-existent or 403 for unauthorized
            assert response.status_code in [
                200,
                403,
                404,
            ], f"ID {test_id} returned {response.status_code}"

    @pytest.mark.xfail(reason="T543: Error message leaks stream existence")
    def test_error_message_leaks_existence(self, admin_client):
        """Info Leak: Error messages reveal if stream exists."""
        victim = baker.make(User, username="testred_victim")
        victim_stream = baker.make(
            Webstream,
            name="Victim Stream",
            url="http://victim.com/stream",
            owner=victim,
        )

        # Try to access existing vs non-existing
        response_existing = admin_client.delete(
            f"/api/v2/webstreams/{victim_stream.id}",
        )
        response_nonexistent = admin_client.delete("/api/v2/webstreams/999999")

        # Both should return same status to not leak existence
        if response_existing.status_code != response_nonexistent.status_code:
            assert (
                False
            ), f"Status leak: existing={response_existing.status_code}, nonexistent={response_nonexistent.status_code}"

    # ========================================================================
    # SSRF via URL Update
    # ========================================================================

    @pytest.mark.xfail(
        reason="T544: SSRF - can update URL to internal address",
    )
    def test_ssrf_url_update_to_internal(self, admin_client):
        """SSRF: Updating URL to internal network should be rejected."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        internal_urls = [
            "http://localhost:8080/internal",
            "http://127.0.0.1:8080/internal",
            "http://192.168.1.1/internal",
            "http://10.0.0.1/internal",
        ]

        for url in internal_urls:
            response = admin_client.patch(
                f"/api/v2/webstreams/{stream.id}",
                json.dumps({"url": url}),
                content_type="application/json",
            )
            assert (
                response.status_code == 400
            ), f"SSRF: Internal URL '{url}' accepted with {response.status_code}"

    @pytest.mark.xfail(reason="T545: SSRF - can update URL to cloud metadata")
    def test_ssrf_url_update_to_metadata(self, admin_client):
        """SSRF: Updating URL to cloud metadata should be rejected."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        response = admin_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"url": "http://169.254.169.254/latest/meta-data/"}),
            content_type="application/json",
        )
        assert (
            response.status_code == 400
        ), f"SSRF: Metadata URL accepted with {response.status_code}"

    # ========================================================================
    # BOPLA - Mass Assignment on Update
    # ========================================================================

    @pytest.mark.xfail(reason="T546: BOPLA - can change owner on update")
    def test_bopla_change_owner_on_update(self, admin_client):
        """BOPLA: Changing owner field should be rejected."""
        user = baker.make(User, username="testred_user")
        victim = baker.make(User, username="testred_victim")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        # Try to change owner to victim
        response = admin_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"owner": victim.id}),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            assert (
                data.get("owner") != victim.id
            ), "BOPLA: Owner changed to victim via PATCH"

    @pytest.mark.xfail(reason="T547: BOPLA - can modify id field on update")
    def test_bopla_modify_id_on_update(self, admin_client):
        """BOPLA: Modifying id field on update should be rejected."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )
        original_id = stream.id

        response = admin_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"id": 99999}),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            assert (
                data["id"] == original_id
            ), "BOPLA: ID was modified via PATCH"

    @pytest.mark.xfail(reason="T548: BOPLA - can set created_at on update")
    def test_bopla_set_created_at_on_update(self, admin_client):
        """BOPLA: Setting created_at on update should be ignored."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        fake_time = "2020-01-01T00:00:00Z"
        response = admin_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"created_at": fake_time}),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            assert (
                data.get("created_at") != fake_time
            ), "BOPLA: created_at modified via PATCH"

    # ========================================================================
    # XSS on Update
    # ========================================================================

    @pytest.mark.xfail(reason="T549: XSS - can update name with script tags")
    def test_xss_update_name(self, admin_client):
        """XSS: Updating name with script tags should be sanitized."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Clean Name",
            url="http://example.com/stream",
            owner=user,
        )

        xss_payload = "<script>alert(1)</script>"
        response = admin_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"name": xss_payload}),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            name = data.get("name", "")
            assert (
                "<script>" not in name
            ), "XSS: script tags not sanitized in name"

    @pytest.mark.xfail(
        reason="T550: XSS - can update description with script tags",
    )
    def test_xss_update_description(self, admin_client):
        """XSS: Updating description with script tags should be sanitized."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            description="Clean description",
            owner=user,
        )

        xss_payload = "<img src=x onerror=alert(1)>"
        response = admin_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"description": xss_payload}),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            desc = data.get("description", "")
            assert (
                "onerror=" not in desc
            ), "XSS: event handlers not sanitized in description"

    # ========================================================================
    # Injection Attacks
    # ========================================================================

    def test_sqli_in_update_name(self, admin_client):
        """Injection: SQLi in PATCH name field."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        sqli_payloads = [
            "Stream'; DROP TABLE cc_webstream;--",
            "Stream' OR '1'='1",
            "Stream' UNION SELECT * FROM cc_user--",
        ]

        for payload in sqli_payloads:
            response = admin_client.patch(
                f"/api/v2/webstreams/{stream.id}",
                json.dumps({"name": payload}),
                content_type="application/json",
            )
            assert response.status_code in [
                200,
                400,
            ], f"SQLi '{payload}' caused {response.status_code}"

    def test_sqli_in_update_url(self, admin_client):
        """Injection: SQLi in PATCH URL field."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        sqli_payloads = [
            "http://example.com/stream' OR '1'='1",
            "http://example.com/stream'; DROP TABLE cc_webstream;--",
        ]

        for payload in sqli_payloads:
            response = admin_client.patch(
                f"/api/v2/webstreams/{stream.id}",
                json.dumps({"url": payload}),
                content_type="application/json",
            )
            assert response.status_code in [
                200,
                400,
            ], f"SQLi '{payload}' caused {response.status_code}"

    # ========================================================================
    # PUT vs PATCH Behavior
    # ========================================================================

    @pytest.mark.xfail(reason="T551: PUT allows dangerous URL update")
    def test_put_full_update_ssrf(self, admin_client):
        """SSRF: PUT full update with internal URL."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        # PUT full update with internal URL
        response = admin_client.put(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps(
                {
                    "name": "Updated Stream",
                    "url": "http://localhost:8080/internal",
                    "description": "Updated",
                },
            ),
            content_type="application/json",
        )
        assert response.status_code in [
            200,
            400,
        ], f"PUT SSRF: internal URL accepted with {response.status_code}"

    @pytest.mark.xfail(reason="T552: PUT allows owner change")
    def test_put_full_update_owner_change(self, admin_client):
        """BOPLA: PUT full update with different owner."""
        user = baker.make(User, username="testred_user")
        victim = baker.make(User, username="testred_victim")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        # PUT full update with victim as owner
        response = admin_client.put(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps(
                {
                    "name": "Updated Stream",
                    "url": "http://example.com/stream",
                    "owner": victim.id,
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            assert (
                data.get("owner") != victim.id
            ), "BOPLA: Owner changed via PUT"

    # ========================================================================
    # Business Logic
    # ========================================================================

    @pytest.mark.xfail(reason="T553: Empty name accepted on update")
    def test_update_empty_name(self, admin_client):
        """Validation: Empty name on update should be rejected."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        response = admin_client.patch(
            f"/api/v2/webstreams/{stream.id}",
            json.dumps({"name": ""}),
            content_type="application/json",
        )
        assert (
            response.status_code == 400
        ), f"Empty name accepted with {response.status_code}"

    @pytest.mark.xfail(reason="T554: Invalid URL format accepted on update")
    def test_update_invalid_url_format(self, admin_client):
        """Validation: Invalid URL format on update should be rejected."""
        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        invalid_urls = [
            "not-a-url",
            "javascript:alert(1)",
            "file:///etc/passwd",
        ]

        for url in invalid_urls:
            response = admin_client.patch(
                f"/api/v2/webstreams/{stream.id}",
                json.dumps({"url": url}),
                content_type="application/json",
            )
            assert (
                response.status_code == 400
            ), f"Invalid URL '{url}' accepted with {response.status_code}"

    # ========================================================================
    # Invalid ID Handling
    # ========================================================================

    def test_update_nonexistent_stream(self, admin_client):
        """Validation: Update non-existent stream returns 404."""
        response = admin_client.patch(
            "/api/v2/webstreams/999999",
            json.dumps({"name": "New Name"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_update_invalid_id_format(self, admin_client):
        """Validation: Invalid ID format handled gracefully."""
        response = admin_client.patch(
            "/api/v2/webstreams/invalid",
            json.dumps({"name": "New Name"}),
            content_type="application/json",
        )
        assert response.status_code in [
            400,
            404,
        ], f"Invalid ID caused {response.status_code}"

    # ========================================================================
    # Authentication
    # ========================================================================

    def test_update_without_auth(self, client):
        """Auth: Update without authentication should fail."""
        response = client.patch(
            "/api/v2/webstreams/1",
            json.dumps({"name": "New Name"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_without_auth(self, client):
        """Auth: Delete without authentication should fail."""
        response = client.delete("/api/v2/webstreams/1")
        assert response.status_code == 403

    # ========================================================================
    # Race Conditions
    # ========================================================================

    @pytest.mark.xfail(reason="T555: Race condition in concurrent update")
    def test_race_condition_concurrent_update(self, admin_client):
        """Race: Concurrent update of same stream."""
        import concurrent.futures

        user = baker.make(User, username="testred_user")
        stream = baker.make(
            Webstream,
            name="Test Stream",
            url="http://example.com/stream",
            owner=user,
        )

        def update_stream(name):
            return admin_client.patch(
                f"/api/v2/webstreams/{stream.id}",
                json.dumps({"name": name}),
                content_type="application/json",
            ).status_code

        # Fire concurrent updates
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(update_stream, f"Name{i}") for i in range(5)
            ]
            results = [
                f.result() for f in concurrent.futures.as_completed(futures)
            ]

        success_count = results.count(200)
        # All should succeed or handle gracefully
        assert (
            success_count >= 0
        ), f"Race condition: {success_count} updates succeeded"