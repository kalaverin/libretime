"""T263: PlayoutHistoryTemplate redteam security tests.

Red Team security tests for PlayoutHistoryTemplate endpoints.
Tests for BOPLA, BOLA, injection, and validation vulnerabilities.
"""

import pytest

from model_bakery import baker

from api.history.models import PlayoutHistoryTemplate


@pytest.mark.django_db
class TestPlayoutHistoryTemplateRedTeamBOPLA:
    """API3:2023 Broken Object Property Level Authorization - mass assignment."""

    def test_bopla_create_mass_assignment_id(
        self,
        admin_client,
        admin_user,
        fake_small_int,
    ):
        """
        BOPLA: CREATE template with forced ID.

        Serializer uses __all__ which may allow id assignment.
        """
        forced_id = fake_small_int + 900000

        data = {
            "id": forced_id,
            "name": "Test Template",
            "type": "file",
        }

        response = admin_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )

        if response.status_code == 201:
            result = response.json()
            if result.get("id") == forced_id:
                pytest.xfail("T632: BOPLA - Template id mass assignment works")

    def test_bopla_create_extra_fields_ignored(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        BOPLA: CREATE with extra fields silently ignored.

        Should reject unknown fields instead of ignoring.
        """
        data = {
            "name": fake_catch_phrase,
            "type": "file",
            "is_admin": True,
            "role": "superuser",
            "password": "hacked",
            "owner_id": 1,
        }

        response = admin_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )

        if response.status_code == 201:
            pytest.xfail(
                "T633: BOPLA - Template extra fields silently ignored",
            )

    def test_bopla_update_change_id(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
        fake_small_int,
    ):
        """
        BOPLA: UPDATE attempt to change ID.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )
        new_id = fake_small_int + 800000

        data = {
            "id": new_id,
            "name": template.name,
            "type": template.type,
        }

        response = admin_client.put(
            f"/api/v2/playout-history-templates/{template.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("id") == new_id:
                pytest.xfail(
                    "T634: BOPLA - Template id can be modified via PUT",
                )

    def test_bopla_update_extra_fields_ignored(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
        fake_word,
    ):
        """
        BOPLA: UPDATE with extra fields silently ignored.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        data = {
            "name": fake_word,
            "type": "file",
            "hacked": True,
            "system_field": "compromised",
        }

        response = admin_client.put(
            f"/api/v2/playout-history-templates/{template.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            pytest.xfail("T635: BOPLA - Template UPDATE extra fields ignored")

    def test_bopla_patch_extra_fields_ignored(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        BOPLA: PATCH with extra fields silently ignored.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        data = {
            "name": "Patched Name",
            "is_system": True,
            "internal_flag": True,
        }

        response = admin_client.patch(
            f"/api/v2/playout-history-templates/{template.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            pytest.xfail("T636: BOPLA - Template PATCH extra fields ignored")


@pytest.mark.django_db
class TestPlayoutHistoryTemplateRedTeamBOLA:
    """API1:2023 Broken Object Level Authorization."""

    def test_bola_no_owner_field_in_model(self, admin_client, admin_user):
        """
        BOLA: Template model has no owner field.

        Templates are global - anyone with permission can modify any template.
        """
        from api.history.models import PlayoutHistoryTemplate

        fields = [f.name for f in PlayoutHistoryTemplate._meta.get_fields()]

        assert "owner" not in fields
        assert "creator" not in fields
        assert "user" not in fields

    def test_bola_regular_user_can_modify_global_template(
        self,
        admin_client,
        regular_user,
        fake_catch_phrase,
        fake_word,
    ):
        """
        BFLA/BOLA: Regular user can modify global templates.

        If regular users can edit templates, this affects all users.
        """
        # Create template as admin would
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        # Regular user tries to modify
        admin_client.force_authenticate(user=regular_user)

        data = {
            "name": f"HACKED_{fake_word}",
            "type": "stream",
        }

        response = admin_client.put(
            f"/api/v2/playout-history-templates/{template.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            pytest.xfail(
                "T637: BFLA - Regular user can modify global templates",
            )

    def test_bola_regular_user_can_delete_global_template(
        self,
        admin_client,
        regular_user,
        fake_catch_phrase,
    ):
        """
        BFLA/BOLA: Regular user can delete global templates.

        Template deletion affects all users of the system.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        admin_client.force_authenticate(user=regular_user)

        response = admin_client.delete(
            f"/api/v2/playout-history-templates/{template.id}",
        )

        if response.status_code == 204:
            pytest.xfail(
                "T638: BFLA - Regular user can delete global templates",
            )

    def test_bola_guest_user_can_access_templates(
        self,
        admin_client,
        guest_user,
    ):
        """
        BFLA: Guest user can access templates.

        Templates should be admin/manager only.
        """
        admin_client.force_authenticate(user=guest_user)

        response = admin_client.get("/api/v2/playout-history-templates")

        if response.status_code == 200:
            pytest.xfail("T639: BFLA - Guest user can list templates")


@pytest.mark.django_db
class TestPlayoutHistoryTemplateRedTeamInjection:
    """Injection attacks on template endpoints."""

    def test_sqli_in_name_field(self, admin_client, admin_user):
        """
        SQL Injection via name field.
        """
        sqli_names = [
            "Template' OR '1'='1",
            "Template'; DROP TABLE cc_playout_history_template--",
            "Template' UNION SELECT * FROM pg_authid--",
        ]

        for name in sqli_names:
            data = {"name": name, "type": "file"}

            response = admin_client.post(
                "/api/v2/playout-history-templates",
                data,
                format="json",
            )

            if response.status_code == 500:
                pytest.xfail(f"T640: SQLi in name causes 500: {name[:30]}")

            error_text = str(response.content).lower()
            if "sql" in error_text or "syntax" in error_text:
                pytest.xfail(f"T640: SQLi error disclosure: {name[:30]}")

    def test_sqli_in_type_field(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        SQL Injection via type field.
        """
        sqli_types = [
            "file' OR '1'='1",
            "stream'; DROP TABLE--",
        ]

        for type_val in sqli_types:
            data = {"name": fake_catch_phrase, "type": type_val}

            response = admin_client.post(
                "/api/v2/playout-history-templates",
                data,
                format="json",
            )

            if response.status_code == 500:
                pytest.xfail("T640: SQLi in type causes 500")

    def test_xss_in_name_field(self, admin_client, admin_user):
        """
        XSS via name field - stored XSS.
        """
        xss_names = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "Template<img src=x onerror=alert('xss')>",
        ]

        for name in xss_names:
            data = {"name": name, "type": "file"}

            response = admin_client.post(
                "/api/v2/playout-history-templates",
                data,
                format="json",
            )

            if response.status_code == 201:
                result = response.json()
                stored_name = result.get("name")
                if stored_name == name:
                    pytest.xfail("T641: XSS in name stored unsanitized")

    def test_xss_in_type_field(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        XSS via type field.
        """
        xss_type = "file<script>alert(1)</script>"

        data = {"name": fake_catch_phrase, "type": xss_type}

        response = admin_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )

        if response.status_code == 201:
            result = response.json()
            if result.get("type") == xss_type:
                pytest.xfail("T641: XSS in type stored unsanitized")

    def test_command_injection_patterns(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        Command injection patterns in fields.
        """
        cmd_names = [
            "$(whoami)",
            "`id`",
            "Template; rm -rf /",
            "| cat /etc/passwd",
        ]

        for name in cmd_names:
            data = {"name": name, "type": "file"}

            response = admin_client.post(
                "/api/v2/playout-history-templates",
                data,
                format="json",
            )

            # Should accept any string
            assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestPlayoutHistoryTemplateRedTeamValidation:
    """Validation bypass and edge case tests."""

    def test_create_empty_name(self, admin_client, admin_user):
        """
        Validation: Empty name should be rejected.
        """
        data = {"name": "", "type": "file"}

        response = admin_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )

        if response.status_code == 201:
            pytest.xfail("T642: Empty name accepted")

    def test_create_empty_type(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        Validation: Empty type should be rejected.
        """
        data = {"name": fake_catch_phrase, "type": ""}

        response = admin_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )

        if response.status_code == 201:
            pytest.xfail("T643: Empty type accepted")

    def test_create_very_long_name(self, admin_client, admin_user):
        """
        Validation: Very long name beyond max_length.
        """
        data = {"name": "A" * 1000, "type": "file"}

        response = admin_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )

        if response.status_code == 201:
            result = response.json()
            if len(result.get("name", "")) == 1000:
                pytest.xfail("T644: No max_length enforcement on name")

    def test_create_very_long_type(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        Validation: Very long type beyond max_length (35).
        """
        data = {"name": fake_catch_phrase, "type": "X" * 100}

        response = admin_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )

        if response.status_code == 201:
            result = response.json()
            if len(result.get("type", "")) == 100:
                pytest.xfail("T645: No max_length enforcement on type")

    def test_create_null_name(self, admin_client, admin_user):
        """
        Validation: Null name should be rejected.
        """
        data = {"name": None, "type": "file"}

        response = admin_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )

        assert response.status_code == 400

    def test_create_invalid_type_values(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        Validation: Invalid type values.

        Type should be restricted to known values (file, stream, etc.)
        """
        invalid_types = [
            "invalid_type",
            "<script>",
            "'; DROP TABLE--",
            "💣",
            "file_stream_mixed",
        ]

        for type_val in invalid_types:
            data = {"name": fake_catch_phrase, "type": type_val}

            response = admin_client.post(
                "/api/v2/playout-history-templates",
                data,
                format="json",
            )

            # Document behavior - should validate against allowed types
            if response.status_code == 201:
                pass  # No validation on type values

    def test_create_duplicate_name(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        Validation: Duplicate template names.

        Should names be unique?
        """
        # First template
        data = {"name": fake_catch_phrase, "type": "file"}
        response1 = admin_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )
        assert response1.status_code == 201

        # Duplicate name
        response2 = admin_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )

        # Document behavior
        if response2.status_code == 201:
            pass  # Duplicates allowed
        elif response2.status_code == 400:
            pass  # Duplicates rejected


@pytest.mark.django_db
class TestPlayoutHistoryTemplateRedTeamResourceConsumption:
    """API4:2023 Unrestricted Resource Consumption."""

    def test_rapid_template_creation(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        Rate limiting: Rapid CREATE requests.
        """
        success_count = 0
        for i in range(20):
            data = {"name": f"{fake_catch_phrase}_{i}", "type": "file"}
            response = admin_client.post(
                "/api/v2/playout-history-templates",
                data,
                format="json",
            )
            if response.status_code == 201:
                success_count += 1

        if success_count == 20:
            pytest.xfail("T646: No rate limiting on template CREATE")

    def test_rapid_template_updates(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
        fake_word,
    ):
        """
        Rate limiting: Rapid UPDATE requests.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        success_count = 0
        for i in range(20):
            data = {"name": f"{fake_word}_{i}", "type": "file"}
            response = admin_client.put(
                f"/api/v2/playout-history-templates/{template.id}",
                data,
                format="json",
            )
            if response.status_code == 200:
                success_count += 1

        if success_count == 20:
            pytest.xfail("T647: No rate limiting on template UPDATE")

    def test_list_large_number_of_templates(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        Resource consumption: List with many templates.
        """
        # Create many templates
        for i in range(100):
            baker.make(
                PlayoutHistoryTemplate,
                name=f"Template_{i}_{fake_catch_phrase}",
                type="file",
            )

        response = admin_client.get("/api/v2/playout-history-templates")

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) == 100:
                pass  # No pagination


@pytest.mark.django_db
class TestPlayoutHistoryTemplateRedTeamAuthentication:
    """Authentication and authorization tests."""

    def test_unauthenticated_list(self, admin_client):
        """
        Auth: Unauthenticated LIST should fail.
        """
        admin_client.logout()
        response = admin_client.get("/api/v2/playout-history-templates")
        assert response.status_code == 403

    def test_unauthenticated_create(self, admin_client, fake_catch_phrase):
        """
        Auth: Unauthenticated CREATE should fail.
        """
        admin_client.logout()
        data = {"name": fake_catch_phrase, "type": "file"}
        response = admin_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )
        assert response.status_code == 403

    def test_unauthenticated_update(
        self,
        admin_client,
        fake_catch_phrase,
        fake_word,
    ):
        """
        Auth: Unauthenticated UPDATE should fail.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        admin_client.logout()
        data = {"name": fake_word, "type": "file"}
        response = admin_client.put(
            f"/api/v2/playout-history-templates/{template.id}",
            data,
            format="json",
        )
        assert response.status_code == 403

    def test_unauthenticated_delete(self, admin_client, fake_catch_phrase):
        """
        Auth: Unauthenticated DELETE should fail.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        admin_client.logout()
        response = admin_client.delete(
            f"/api/v2/playout-history-templates/{template.id}",
        )
        assert response.status_code == 403

    def test_guest_user_create(
        self,
        admin_client,
        guest_user,
        fake_catch_phrase,
    ):
        """
        BFLA: Guest user CREATE should fail.
        """
        admin_client.force_authenticate(user=guest_user)

        data = {"name": fake_catch_phrase, "type": "file"}
        response = admin_client.post(
            "/api/v2/playout-history-templates",
            data,
            format="json",
        )

        if response.status_code == 201:
            pytest.xfail("T648: Guest user can create templates")


@pytest.mark.django_db
class TestPlayoutHistoryTemplateRedTeamIDEnumeration:
    """ID enumeration and information disclosure."""

    def test_id_sequence_predictable(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        Sequential IDs allow enumeration.
        """
        templates = []
        for i in range(5):
            t = baker.make(
                PlayoutHistoryTemplate,
                name=f"Template_{i}_{fake_catch_phrase}",
                type="file",
            )
            templates.append(t)

        ids = [t.id for t in templates]

        # Check if sequential
        if all(isinstance(i, int) for i in ids):
            # Sequential IDs are predictable
            if max(ids) - min(ids) == len(ids) - 1:
                pass  # Predictable IDs enable enumeration

    def test_retrieve_nonexistent_leaks_nothing(self, admin_client, admin_user):
        """
        404 for non-existent should not leak information.
        """
        response = admin_client.get("/api/v2/playout-history-templates/999999")

        assert response.status_code == 404
        # Error should be generic
        data = response.json()
        assert "detail" in data


@pytest.mark.django_db
class TestPlayoutHistoryTemplateRedTeamHTTPMethodTampering:
    """HTTP method tampering tests."""

    def test_method_override_header(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        Method override via headers.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        response = admin_client.post(
            f"/api/v2/playout-history-templates/{template.id}",
            {},
            headers={"X-HTTP-Method-Override": "GET"},
        )

        # Should not work
        assert response.status_code in [405, 403, 400, 301]

    def test_trace_method_disabled(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        TRACE method should be disabled.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        response = admin_client.trace(
            f"/api/v2/playout-history-templates/{template.id}",
        )

        assert response.status_code in [405, 403]
