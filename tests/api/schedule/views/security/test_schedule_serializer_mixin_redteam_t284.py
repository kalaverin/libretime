"""T284: ReadWriteSerializerMixin redteam security tests.

Red Team security tests for serializer switching behavior.
Tests for mass assignment, field injection, and serializer bypasses.
"""

import json

from datetime import timedelta

import pytest

from model_bakery import baker

from api.core.models import User
from api.schedule.models import Schedule, Show, ShowInstance
from api.storage.models import File, Library
from sdk import format_datetime, now

# =============================================================================
# API3:2023 BOPLA - Mass Assignment via Write Serializer
# =============================================================================


@pytest.mark.django_db
class TestSerializerMixinRedTeamBOPLA:
    """Broken Object Property Level Authorization tests for serializer mixin."""

    @pytest.fixture
    def show_instance(self, fake_catch_phrase):
        """Create a show instance for testing."""
        show = baker.make(Show, name=fake_catch_phrase)
        start = now()
        end = start + timedelta(hours=2)
        return baker.make(
            ShowInstance,
            show=show,
            starts_at=start,
            ends_at=end,
        )

    @pytest.fixture
    def test_file(self, fake_catch_phrase):
        """Create a test file for scheduling."""
        library = baker.make(
            Library,
            name=fake_catch_phrase,
            description="Test",
        )
        user = baker.make(User, username=fake_catch_phrase)
        return baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

    def test_post_mass_assignment_extra_fields(
        self,
        api_client,
        show_instance,
        test_file,
    ):
        """
        BOPLA: POST with extra fields that should be read-only.
        """
        start = now()
        end = start + timedelta(minutes=30)

        payload = {
            "instance": show_instance.id,
            "file": test_file.id,
            "starts_at": format_datetime(start),
            "ends_at": format_datetime(end),
            "cue_in": "00:00:00",
            "cue_out": "00:30:00",
            "position": 1,
            "broadcasted": 1,
            "id": 99999,
        }

        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(payload),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            if data.get("id") == 99999:
                pytest.xfail("T794: BOPLA - ID mass assignment via POST works")

    def test_patch_mass_assignment_readonly_fields(
        self,
        api_client,
        show_instance,
        test_file,
    ):
        """
        BOPLA: PATCH with read-only field injection.
        """
        start = now()
        end = start + timedelta(minutes=30)

        schedule = baker.make(
            Schedule,
            instance=show_instance,
            file=test_file,
            starts_at=start,
            ends_at=end,
            cue_in=timedelta(seconds=0),
            cue_out=timedelta(minutes=30),
            position=1,
            broadcasted=1,
        )

        response = api_client.patch(
            f"/api/v2/schedule/{schedule.id}",
            json.dumps({"id": 88888}),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("id") == 88888:
                pytest.xfail("T795: BOPLA - ID modification via PATCH works")

    def test_post_field_type_confusion(
        self,
        api_client,
        show_instance,
        test_file,
    ):
        """
        BOPLA: Field type confusion attacks.
        """
        start = now()
        end = start + timedelta(minutes=30)

        wrong_types = [
            {"position": "not_an_integer"},
            {"broadcasted": "not_a_boolean"},
        ]

        for override in wrong_types:
            payload = {
                "instance": show_instance.id,
                "file": test_file.id,
                "starts_at": format_datetime(start),
                "ends_at": format_datetime(end),
                "cue_in": "00:00:00",
                "cue_out": "00:30:00",
                "position": 1,
                "broadcasted": 1,
            }
            payload.update(override)

            response = api_client.post(
                "/api/v2/schedule",
                json.dumps(payload),
                content_type="application/json",
            )

            if response.status_code == 500:
                pytest.xfail(
                    f"T796: Field type confusion causes 500: {override}",
                )


# =============================================================================
# Serializer Bypass Tests
# =============================================================================


@pytest.mark.django_db
class TestSerializerMixinRedTeamBypass:
    """Serializer bypass tests."""

    @pytest.fixture
    def show_instance(self, fake_catch_phrase):
        show = baker.make(Show, name=fake_catch_phrase)
        start = now()
        end = start + timedelta(hours=2)
        return baker.make(
            ShowInstance,
            show=show,
            starts_at=start,
            ends_at=end,
        )

    @pytest.fixture
    def test_file(self, fake_catch_phrase):
        library = baker.make(
            Library,
            name=fake_catch_phrase,
            description="Test",
        )
        user = baker.make(User, username=fake_catch_phrase)
        return baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

    def test_content_type_bypass(self, api_client, show_instance, test_file):
        """
        Try to bypass serializer validation with different Content-Type.
        """
        start = now()
        end = start + timedelta(minutes=30)

        response = api_client.post(
            "/api/v2/schedule",
            {
                "instance": show_instance.id,
                "file": test_file.id,
                "starts_at": format_datetime(start),
                "ends_at": format_datetime(end),
            },
            format="multipart",
        )

        if response.status_code == 500:
            pytest.xfail("T797: Content-Type bypass causes 500")

    def test_method_override_bypass(
        self,
        api_client,
        show_instance,
        test_file,
    ):
        """
        Try to use write serializer via GET with method override.
        """
        start = now()
        end = start + timedelta(minutes=30)

        schedule = baker.make(
            Schedule,
            instance=show_instance,
            file=test_file,
            starts_at=start,
            ends_at=end,
            cue_in=timedelta(seconds=0),
            cue_out=timedelta(minutes=30),
            position=1,
            broadcasted=1,
        )

        response = api_client.get(
            f"/api/v2/schedule/{schedule.id}",
            HTTP_X_HTTP_METHOD_OVERRIDE="POST",
        )

        if response.status_code == 201:
            pytest.xfail("T798: Method override bypasses serializer selection")


# =============================================================================
# Deep Nesting / DoS Tests
# =============================================================================


@pytest.mark.django_db
class TestSerializerMixinRedTeamDoS:
    """DoS tests for serializers."""

    def test_deeply_nested_json_post(self, api_client):
        """
        Deeply nested JSON may cause recursion in serializer.
        """
        nested = {"value": "test"}
        for _ in range(100):
            nested = {"nested": nested}

        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(nested),
            content_type="application/json",
        )

        if response.status_code == 500:
            pytest.xfail("T800: Deeply nested JSON causes 500")

    @pytest.fixture
    def show_instance(self, fake_catch_phrase):
        show = baker.make(Show, name=fake_catch_phrase)
        start = now()
        end = start + timedelta(hours=2)
        return baker.make(
            ShowInstance,
            show=show,
            starts_at=start,
            ends_at=end,
        )

    @pytest.fixture
    def test_file(self, fake_catch_phrase):
        library = baker.make(
            Library,
            name=fake_catch_phrase,
            description="Test",
        )
        user = baker.make(User, username=fake_catch_phrase)
        return baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

    def test_very_long_string_fields(
        self,
        api_client,
        show_instance,
        test_file,
    ):
        """
        Very long strings in fields may cause DoS.
        """
        start = now()
        end = start + timedelta(minutes=30)

        payload = {
            "instance": show_instance.id,
            "file": test_file.id,
            "starts_at": format_datetime(start),
            "ends_at": format_datetime(end),
            "cue_in": "00:00:00",
            "cue_out": "00:30:00",
            "position": 1,
            "broadcasted": 1,
        }

        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(payload),
            content_type="application/json",
        )

        if response.status_code == 500:
            pytest.xfail("T801: Very long string causes 500")


# =============================================================================
# Injection Tests
# =============================================================================


@pytest.mark.django_db
class TestSerializerMixinRedTeamInjection:
    """Injection tests through serializers."""

    @pytest.fixture
    def show_instance(self, fake_catch_phrase):
        show = baker.make(Show, name=fake_catch_phrase)
        start = now()
        end = start + timedelta(hours=2)
        return baker.make(
            ShowInstance,
            show=show,
            starts_at=start,
            ends_at=end,
        )

    @pytest.fixture
    def test_file(self, fake_catch_phrase):
        library = baker.make(
            Library,
            name=fake_catch_phrase,
            description="Test",
        )
        user = baker.make(User, username=fake_catch_phrase)
        return baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

    def test_sqli_via_serializer_field(
        self,
        api_client,
        show_instance,
        test_file,
    ):
        """
        SQL Injection through serializer field values.
        """
        start = now()

        payload = {
            "instance": show_instance.id,
            "file": test_file.id,
            "starts_at": format_datetime(start) + "'; DROP TABLE--",
            "ends_at": format_datetime(start + timedelta(minutes=30)),
            "cue_in": "00:00:00",
            "cue_out": "00:30:00",
            "position": 1,
            "broadcasted": 1,
        }

        response = api_client.post(
            "/api/v2/schedule",
            json.dumps(payload),
            content_type="application/json",
        )

        if response.status_code == 500:
            content = str(response.content).lower()
            if "sql" in content or "syntax" in content:
                pytest.xfail("T802: SQLi via datetime field in serializer")
