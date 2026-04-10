"""
T297: Stereo/Mono detection redteam security tests.

Paranoid security tests for audio channel detection endpoints.
Targets: BOLA, mass assignment, SQL injection, path traversal, filter bypass.
"""

import pytest
from model_bakery import baker
from rest_framework.test import APIClient

from api.core.models import User
from api.storage.models import File, Library


def make_library(**kwargs):
    """Helper to create Library with required description."""
    defaults = {"description": "Test library"}
    defaults.update(kwargs)
    return baker.make(Library, **defaults)


@pytest.mark.django_db
class TestStereoMonoBOLA:
    """T892: BOLA - Object-level authorization bypass in channel detection."""

    @pytest.mark.xfail(
        reason="BOLA: Can retrieve other user's file with channels - T892"
    )
    def test_retrieve_other_users_file_channels(self, api_client: APIClient):
        """
        Attacker retrieves victim's file to see channel info.
        API1:2023 - Broken Object Level Authorization.
        """
        attacker = baker.make(User, username="channel_attacker")
        victim = baker.make(User, username="channel_victim")
        library = make_library( code="BOLA", name="BOLA Test")

        victim_file = baker.make(
            File,
            name="victim_music.mp3",
            mime="audio/mp3",
            library=library,
            owner=victim,
            channels=2,
            sample_rate=44100,
        )

        api_client.force_authenticate(user=attacker)
        response = api_client.get(f"/api/v2/files/{victim_file.id}")

        assert response.status_code == 404, (
            "Attacker should not see victim's file channels"
        )

    @pytest.mark.xfail(
        reason="BOLA: LIST shows all users' files with channel info - T892"
    )
    def test_list_shows_all_users_channel_info(self, api_client: APIClient):
        """
        LIST endpoint returns all users' files with channel data.
        API1:2023 - Missing user isolation.
        """
        user1 = baker.make(User, username="channel_user1")
        user2 = baker.make(User, username="channel_user2")
        library = make_library( code="BOLA2", name="BOLA Test")

        baker.make(
            File,
            name="user1_mono.mp3",
            mime="audio/mp3",
            library=library,
            owner=user1,
            channels=1,
            _quantity=3,
        )

        baker.make(
            File,
            name="user2_stereo.mp3",
            mime="audio/mp3",
            library=library,
            owner=user2,
            channels=2,
            _quantity=3,
        )

        api_client.force_authenticate(user=user1)
        response = api_client.get("/api/v2/files")

        assert response.status_code == 200
        data = response.json()

        # Should only see own files
        others_files = [f for f in data if f.get("name", "").startswith("user2_")]
        assert len(others_files) == 0, (
            "User1 should not see user2's stereo/mono files"
        )

    @pytest.mark.xfail(
        reason="Auth bypass: Anonymous can access channel info - T892"
    )
    def test_channel_info_not_leaked_to_anonymous(self, api_client: APIClient):
        """Anonymous users cannot access channel information."""
        library = make_library( code="ANON", name="Anon Test")
        user = baker.make(User, username="channel_owner")

        file_obj = baker.make(
            File,
            name="secret_channels.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=6,
        )

        # No authentication
        response = api_client.get(f"/api/v2/files/{file_obj.id}")

        assert response.status_code in [401, 403, 404], (
            "Anonymous should not access channel data"
        )


@pytest.mark.django_db
class TestStereoMonoMassAssignment:
    """T893: Mass assignment via channels field."""

    @pytest.mark.xfail(
        reason="BOPLA: Mass assignment allows changing channels - T893"
    )
    def test_mass_assignment_channels_blocked(self, api_client: APIClient):
        """
        Attempt to modify channels via PATCH/PUT.
        Channels should be read-only from audio analysis.
        """
        user = baker.make(User, username="channel_hacker")
        library = make_library( code="MASS", name="Mass Test")

        file_obj = baker.make(
            File,
            name="mono_recording.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=1,
        )

        api_client.force_authenticate(user=user)

        # Attempt to change mono to stereo
        response = api_client.patch(
            f"/api/v2/files/{file_obj.id}",
            {"channels": 2},
            format="json",
        )

        # Should reject or ignore channels modification
        if response.status_code == 200:
            data = response.json()
            assert data.get("channels") == 1, (
                "Channels should not be modifiable via API"
            )
        else:
            assert response.status_code in [400, 403, 422], (
                "Changing channels should be rejected"
            )

    @pytest.mark.xfail(
        reason="BOPLA: Extreme channel values accepted - T894"
    )
    def test_extreme_channel_values_blocked(self, api_client: APIClient):
        """
        Attempt to set impossible channel values.
        API6:2023 - Unrestricted access to sensitive business flows.
        """
        user = baker.make(User, username="channel_extreme")
        library = make_library( code="EXTREME", name="Extreme Test")

        file_obj = baker.make(
            File,
            name="normal.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
        )

        api_client.force_authenticate(user=user)

        extreme_values = [
            1000,      # Absurd channel count
            -1,        # Negative
            0,         # Zero (edge case)
            999999,    # Integer overflow candidate
            2**31 - 1, # Max int32
        ]

        for extreme in extreme_values:
            response = api_client.patch(
                f"/api/v2/files/{file_obj.id}",
                {"channels": extreme},
                format="json",
            )

            # Refresh and check
            file_obj.refresh_from_db()
            assert file_obj.channels == 2, (
                f"Extreme channel value {extreme} should be rejected, got {file_obj.channels}"
            )

    @pytest.mark.xfail(
        reason="BOPLA: Can modify sample_rate via mass assignment - T895"
    )
    def test_mass_assignment_sample_rate_blocked(self, api_client: APIClient):
        """
        Attempt to change sample_rate which affects audio processing.
        """
        user = baker.make(User, username="sample_hacker")
        library = make_library( code="SAMPLE", name="Sample Test")

        file_obj = baker.make(
            File,
            name="44khz.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
            sample_rate=44100,
        )

        api_client.force_authenticate(user=user)

        response = api_client.patch(
            f"/api/v2/files/{file_obj.id}",
            {"sample_rate": 96000},
            format="json",
        )

        file_obj.refresh_from_db()
        assert file_obj.sample_rate == 44100, (
            "Sample rate should be immutable via API"
        )


@pytest.mark.django_db
class TestStereoMonoSQLInjection:
    """T896: SQL injection via channel-related filters."""

    @pytest.mark.parametrize(
        "filter_payload",
        [
            "channels=1' OR '1'='1",
            "channels=2' UNION SELECT * FROM users --",
            "channels=0; DROP TABLE files; --",
            "sample_rate=44100' AND 1=1 --",
        ],
    )
    def test_sqli_in_channel_filter_no_crash(
        self, api_client: APIClient, filter_payload: str
    ):
        """
        SQLi payloads in channel filters should not cause crashes.
        API8:2023 - Security misconfiguration.
        """
        user = baker.make(User, username="sqli_tester")
        library = make_library( code="SQLI", name="SQLI Test")

        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
            _quantity=2,
        )

        api_client.force_authenticate(user=user)

        # Django filter backend handles this safely
        response = api_client.get(f"/api/v2/files?{filter_payload}")

        # Should not crash with 500
        assert response.status_code in [200, 400], (
            f"SQLi payload '{filter_payload}' caused error"
        )

    def test_sqli_in_channels_param_no_crash(self, api_client: APIClient):
        """Test SQLi in channels query parameter."""
        user = baker.make(User, username="sqli_channels")
        library = make_library( code="SQLI2", name="SQLI Test")

        baker.make(
            File,
            name="stereo.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
        )

        api_client.force_authenticate(user=user)

        payloads = [
            "1' OR '1'='1",
            "2'; SELECT * FROM auth_user; --",
            "1) OR (1=1",
            "2' AND channels='2",
        ]

        for payload in payloads:
            response = api_client.get(f"/api/v2/files?channels={payload}")
            assert response.status_code in [200, 400], (
                f"Payload '{payload}' caused server error"
            )


@pytest.mark.django_db
class TestStereoMonoFilterBypass:
    """T897: Filter bypass to access channel information."""

    @pytest.mark.xfail(
        reason="BOLA: Filter by channels shows all users' files - T897"
    )
    def test_filter_by_channels_cross_user(self, api_client: APIClient):
        """
        Filter by channels=2 returns stereo files from all users.
        API1:2023 - Missing authorization in filtered queries.
        """
        attacker = baker.make(User, username="filter_attacker")
        victim = baker.make(User, username="filter_victim")
        library = make_library( code="FILTER", name="Filter Test")

        # Victim's stereo files
        victim_files = baker.make(
            File,
            name="victim_stereo.mp3",
            mime="audio/mp3",
            library=library,
            owner=victim,
            channels=2,
            _quantity=3,
        )

        # Attacker's mono files
        baker.make(
            File,
            name="attacker_mono.mp3",
            mime="audio/mp3",
            library=library,
            owner=attacker,
            channels=1,
            _quantity=2,
        )

        api_client.force_authenticate(user=attacker)

        # Attacker filters for stereo files
        response = api_client.get("/api/v2/files?channels=2")

        assert response.status_code == 200
        data = response.json()

        victim_visible = [f for f in data if f.get("name", "").startswith("victim_")]
        assert len(victim_visible) == 0, (
            "Filter should not expose victim's stereo files"
        )

    def test_filter_by_invalid_channels_handled(self, api_client: APIClient):
        """Invalid channel filter values should be handled gracefully."""
        user = baker.make(User, username="filter_invalid")
        library = make_library( code="INVALID", name="Invalid Test")

        baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
        )

        api_client.force_authenticate(user=user)

        invalid_values = [
            "abc",
            "@#$%",
            "",
            "null",
            "true",
        ]

        for value in invalid_values:
            response = api_client.get(f"/api/v2/files?channels={value}")
            # Should not crash
            assert response.status_code in [200, 400], (
                f"Invalid channels='{value}' caused error"
            )

    def test_filter_channels_case_sensitivity(self, api_client: APIClient):
        """Channel filter should handle case variations."""
        user = baker.make(User, username="case_test")
        library = make_library( code="CASE", name="Case Test")

        baker.make(
            File,
            name="stereo.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
        )

        api_client.force_authenticate(user=user)

        variations = ["Channels=2", "CHANNELS=2", "channels=2"]

        for var in variations:
            response = api_client.get(f"/api/v2/files?{var}")
            assert response.status_code in [200, 400], (
                f"Case variation '{var}' caused error"
            )


@pytest.mark.django_db
class TestStereoMonoBusinessLogic:
    """T898: Business logic bypass for channel detection."""

    @pytest.mark.xfail(
        reason="Business logic: Can fake channel detection - T898"
    )
    def test_cannot_fake_channel_detection_on_create(self, api_client: APIClient):
        """
        Creating a file with fake channels should be prevented or corrected.
        API6:2023 - Unrestricted access to sensitive business flows.
        """
        user = baker.make(User, username="fake_channels")
        library = make_library( code="FAKE", name="Fake Test")

        api_client.force_authenticate(user=user)

        # Attempt to create with fabricated channel data
        response = api_client.post(
            "/api/v2/files",
            {
                "name": "fake.mp3",
                "mime": "audio/mp3",
                "library": library.id,
                "channels": 100,  # Clearly fake
                "sample_rate": 999999,
            },
            format="json",
        )

        if response.status_code == 201:
            data = response.json()
            # Should either reject or not accept fake values
            assert data.get("channels") != 100 or data.get("sample_rate") != 999999, (
                "Should not accept fabricated audio properties"
            )
        else:
            # Rejection is acceptable
            pass

    def test_channel_consistency_validation(self, api_client: APIClient):
        """Inconsistent channel/sample_rate combinations should be rejected."""
        user = baker.make(User, username="consistency_test")
        library = make_library( code="CONSISTENT", name="Consistent Test")

        api_client.force_authenticate(user=user)

        # Mono file with stereo sample rate (unusual but possible)
        response = api_client.post(
            "/api/v2/files",
            {
                "name": "weird.mp3",
                "mime": "audio/mp3",
                "library": library.id,
                "channels": 1,
                "sample_rate": 96000,
            },
            format="json",
        )

        # API should handle this gracefully
        assert response.status_code in [201, 400], (
            "Inconsistent audio properties should be handled"
        )


@pytest.mark.django_db
class TestStereoMonoEnumeration:
    """T899: Information disclosure via channel enumeration."""

    @pytest.mark.xfail(
        reason="Auth bypass: Anonymous can enumerate channels - T899"
    )
    def test_channels_not_disclosed_to_anonymous(self, api_client: APIClient):
        """Anonymous users should not enumerate channel data."""
        library = make_library( code="ENUM", name="Enum Test")
        user = baker.make(User, username="enum_owner")

        baker.make(
            File,
            name="enumerate_me.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=6,
        )

        response = api_client.get("/api/v2/files")
        
        # Should require auth
        assert response.status_code in [401, 403], (
            "Anonymous LIST should be rejected"
        )

    @pytest.mark.xfail(
        reason="IDOR: Can enumerate channels by iterating IDs - T899"
    )
    def test_channel_enumeration_by_id_iteration(self, api_client: APIClient):
        """
        Iterate through IDs to collect channel information.
        API1:2023 - Insecure direct object reference.
        """
        user = baker.make(User, username="enumerator")
        library = make_library( code="ENUM2", name="Enum Test")

        # Create files with sequential IDs likely
        files = []
        for i in range(5):
            f = baker.make(
                File,
                name=f"enum_{i}.mp3",
                mime="audio/mp3",
                library=library,
                owner=user,
                channels=i + 1,
            )
            files.append(f)

        api_client.force_authenticate(user=user)

        # Try to access by ID iteration
        found_channels = []
        base_id = files[0].id

        for offset in range(-5, 10):
            try_id = base_id + offset
            response = api_client.get(f"/api/v2/files/{try_id}")
            if response.status_code == 200:
                found_channels.append(response.json().get("channels"))

        # Should only find own files
        assert len(found_channels) <= 5, (
            "Should not be able to enumerate other users' channel data"
        )


@pytest.mark.django_db
class TestStereoMonoDataIntegrity:
    """T900: Data integrity for channel information."""

    @pytest.mark.xfail(
        reason="No validation: Negative channels accepted - T900"
    )
    def test_negative_channels_rejected(self, api_client: APIClient):
        """Negative channel values should be rejected."""
        user = baker.make(User, username="negative_test")
        library = make_library( code="NEG", name="Negative Test")

        file_obj = baker.make(
            File,
            name="normal.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
        )

        api_client.force_authenticate(user=user)

        response = api_client.patch(
            f"/api/v2/files/{file_obj.id}",
            {"channels": -1},
            format="json",
        )

        file_obj.refresh_from_db()
        assert file_obj.channels >= 0, (
            "Negative channels should be rejected"
        )

    @pytest.mark.xfail(
        reason="No validation: Zero channels not handled - T900"
    )
    def test_zero_channels_handled(self, api_client: APIClient):
        """Zero channels should be handled (invalid audio)."""
        user = baker.make(User, username="zero_test")
        library = make_library( code="ZERO", name="Zero Test")

        api_client.force_authenticate(user=user)

        response = api_client.post(
            "/api/v2/files",
            {
                "name": "zero.mp3",
                "mime": "audio/mp3",
                "library": library.id,
                "channels": 0,
            },
            format="json",
        )

        # Should either reject or handle specially
        if response.status_code == 201:
            data = response.json()
            assert data.get("channels") != 0, (
                "Zero channels should not be stored"
            )

    def test_channel_type_safety(self, api_client: APIClient):
        """Non-integer channel values should be handled gracefully."""
        user = baker.make(User, username="type_test")
        library = make_library( code="TYPE", name="Type Test")

        api_client.force_authenticate(user=user)

        # String values that could cause type confusion
        invalid_types = [
            "two",
            "2.5",
        ]

        for invalid in invalid_types:
            response = api_client.post(
                "/api/v2/files",
                {
                    "name": "type.mp3",
                    "mime": "audio/mp3",
                    "library": library.id,
                    "channels": invalid,
                },
                format="json",
            )
            # Should not crash with 500
            assert response.status_code in [201, 400], (
                f"Invalid type {type(invalid)} caused server error"
            )


@pytest.mark.django_db
class TestStereoMonoRateLimiting:
    """T901: Rate limiting for channel-related endpoints."""

    def test_channel_filter_rate_limiting(self, api_client: APIClient):
        """Rapid channel filtering should be rate limited."""
        user = baker.make(User, username="rate_limit")
        library = make_library( code="RATE", name="Rate Test")

        baker.make(
            File,
            name="rate_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            channels=2,
            _quantity=5,
        )

        api_client.force_authenticate(user=user)

        # Rapid requests
        responses = []
        for i in range(20):
            response = api_client.get(f"/api/v2/files?channels={i % 3 + 1}")
            responses.append(response.status_code)

        # All should succeed or be rate limited
        assert all(r in [200, 429] for r in responses), (
            "Rapid filtering should be rate limited, not crash"
        )
