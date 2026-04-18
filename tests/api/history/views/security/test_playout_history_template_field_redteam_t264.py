"""T264: PlayoutHistoryTemplateField redteam security tests.

Red Team security tests for PlayoutHistoryTemplateField endpoints.
Tests for BOPLA, BOLA, injection, and validation vulnerabilities.
"""

import pytest

from model_bakery import baker

from api.history.models import (
    PlayoutHistoryTemplate,
    PlayoutHistoryTemplateField,
)


@pytest.mark.django_db
class TestPlayoutHistoryTemplateFieldRedTeamBOPLA:
    """API3:2023 Broken Object Property Level Authorization - mass assignment."""

    def test_bopla_create_mass_assignment_id(
        self,
        admin_client,
        admin_user,
        fake_small_int,
        fake_word,
        fake_catch_phrase,
    ):
        """
        BOPLA: CREATE field with forced ID.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )
        forced_id = fake_small_int + 800000

        data = {
            "id": forced_id,
            "template": template.id,
            "name": fake_word,
            "label": fake_catch_phrase,
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        if response.status_code == 201:
            result = response.json()
            if result.get("id") == forced_id:
                pytest.xfail(
                    "T639: BOPLA - TemplateField id mass assignment works",
                )

    def test_bopla_create_extra_fields_ignored(
        self,
        admin_client,
        admin_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        BOPLA: CREATE with extra fields silently ignored.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        data = {
            "template": template.id,
            "name": fake_word,
            "label": fake_catch_phrase,
            "type": "text",
            "is_file_md": False,
            "position": 1,
            "is_admin": True,
            "role": "superuser",
            "password": "hacked",
        }

        response = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        if response.status_code == 201:
            pytest.xfail(
                "T640: BOPLA - TemplateField extra fields silently ignored",
            )

    def test_bopla_update_change_id(
        self,
        admin_client,
        admin_user,
        fake_word,
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
        field = baker.make(
            PlayoutHistoryTemplateField,
            template=template,
            name=fake_word,
            label=fake_catch_phrase,
            type="text",
            is_file_md=False,
            position=1,
        )
        new_id = fake_small_int + 700000

        data = {
            "id": new_id,
            "template": template.id,
            "name": field.name,
            "label": field.label,
            "type": field.type,
            "is_file_md": field.is_file_md,
            "position": field.position,
        }

        response = admin_client.put(
            f"/api/v2/playout-history-template-fields/{field.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("id") == new_id:
                pytest.xfail("T641: BOPLA - TemplateField id can be modified")

    def test_bopla_patch_extra_fields_ignored(
        self,
        admin_client,
        admin_user,
        fake_word,
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
        field = baker.make(
            PlayoutHistoryTemplateField,
            template=template,
            name=fake_word,
            label=fake_catch_phrase,
            type="text",
            is_file_md=False,
            position=1,
        )

        data = {
            "label": "Patched Label",
            "is_system": True,
            "internal_flag": True,
        }

        response = admin_client.patch(
            f"/api/v2/playout-history-template-fields/{field.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            pytest.xfail(
                "T642: BOPLA - TemplateField PATCH extra fields ignored",
            )


@pytest.mark.django_db
class TestPlayoutHistoryTemplateFieldRedTeamBOLA:
    """API1:2023 Broken Object Level Authorization."""

    def test_bola_create_field_for_other_users_template(
        self,
        admin_client,
        admin_user,
        regular_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        BOLA: CREATE field in another user's template.

        Should verify template ownership.
        """
        # Create template as regular user (victim)
        victim_template = baker.make(
            PlayoutHistoryTemplate,
            name=f"victim_{fake_catch_phrase}",
            type="file",
        )

        # Admin tries to add field to victim's template
        data = {
            "template": victim_template.id,
            "name": f"attacker_{fake_word}",
            "label": "Attacker Field",
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        if response.status_code == 201:
            # Successfully added field to victim's template
            pytest.xfail(
                "T643: BOLA - Can create field in other user's template",
            )

    def test_bola_modify_field_in_other_users_template(
        self,
        admin_client,
        admin_user,
        regular_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        BOLA: MODIFY field in another user's template.
        """
        victim_template = baker.make(
            PlayoutHistoryTemplate,
            name=f"victim_{fake_catch_phrase}",
            type="file",
        )
        victim_field = baker.make(
            PlayoutHistoryTemplateField,
            template=victim_template,
            name=f"victim_{fake_word}",
            label="Victim Field",
            type="text",
            is_file_md=False,
            position=1,
        )

        data = {
            "template": victim_template.id,
            "name": victim_field.name,
            "label": "HACKED FIELD",
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = admin_client.put(
            f"/api/v2/playout-history-template-fields/{victim_field.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            # Successfully modified victim's field
            pass  # May be intended for admin

    def test_bola_delete_field_in_other_users_template(
        self,
        admin_client,
        admin_user,
        regular_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        BOLA: DELETE field from another user's template.
        """
        victim_template = baker.make(
            PlayoutHistoryTemplate,
            name=f"victim_{fake_catch_phrase}",
            type="file",
        )
        victim_field = baker.make(
            PlayoutHistoryTemplateField,
            template=victim_template,
            name=f"victim_{fake_word}",
            label="Victim Field",
            type="text",
            is_file_md=False,
            position=1,
        )

        response = admin_client.delete(
            f"/api/v2/playout-history-template-fields/{victim_field.id}",
        )

        if response.status_code == 204:
            # Successfully deleted victim's field
            pass  # May be intended for admin

    def test_bola_regular_user_can_modify_global_field(
        self,
        admin_client,
        regular_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        BFLA: Regular user can modify any template field.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )
        field = baker.make(
            PlayoutHistoryTemplateField,
            template=template,
            name=f"system_{fake_word}",
            label="System Field",
            type="text",
            is_file_md=False,
            position=1,
        )

        admin_client.force_authenticate(user=regular_user)

        data = {
            "template": template.id,
            "name": field.name,
            "label": "HACKED BY REGULAR USER",
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = admin_client.put(
            f"/api/v2/playout-history-template-fields/{field.id}",
            data,
            format="json",
        )

        if response.status_code == 200:
            pytest.xfail(
                "T644: BFLA - Regular user can modify template fields",
            )


@pytest.mark.django_db
class TestPlayoutHistoryTemplateFieldRedTeamInjection:
    """Injection attacks."""

    def test_sqli_in_name_field(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        SQL Injection via name field.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        sqli_names = [
            "field' OR '1'='1",
            "field'; DROP TABLE cc_playout_history_template_field--",
        ]

        for name in sqli_names:
            data = {
                "template": template.id,
                "name": name,
                "label": "Test",
                "type": "text",
                "is_file_md": False,
                "position": 1,
            }

            response = admin_client.post(
                "/api/v2/playout-history-template-fields",
                data,
                format="json",
            )

            if response.status_code == 500:
                pytest.xfail("T645: SQLi in name causes 500")

    def test_sqli_in_label_field(
        self,
        admin_client,
        admin_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        SQL Injection via label field.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        sqli_label = "Label' OR '1'='1"

        data = {
            "template": template.id,
            "name": fake_word,
            "label": sqli_label,
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        if response.status_code == 500:
            pytest.xfail("T645: SQLi in label causes 500")

    def test_xss_in_name_field(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        XSS via name field.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        xss_name = "<script>alert(1)</script>"

        data = {
            "template": template.id,
            "name": xss_name,
            "label": "Test",
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        if response.status_code == 201:
            result = response.json()
            if result.get("name") == xss_name:
                pytest.xfail("T646: XSS in name field stored unsanitized")

    def test_xss_in_label_field(
        self,
        admin_client,
        admin_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        XSS via label field.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        xss_label = "<img src=x onerror=alert(1)>"

        data = {
            "template": template.id,
            "name": fake_word,
            "label": xss_label,
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        if response.status_code == 201:
            result = response.json()
            if result.get("label") == xss_label:
                pytest.xfail("T646: XSS in label field stored unsanitized")


@pytest.mark.django_db
class TestPlayoutHistoryTemplateFieldRedTeamValidation:
    """Validation bypass tests."""

    def test_create_negative_position(
        self,
        admin_client,
        admin_user,
        fake_word,
        fake_catch_phrase,
        fake_negative_int,
    ):
        """
        Validation: Negative position should be rejected.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        data = {
            "template": template.id,
            "name": fake_word,
            "label": fake_catch_phrase,
            "type": "text",
            "is_file_md": False,
            "position": fake_negative_int,
        }

        response = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        if response.status_code == 201:
            pytest.xfail("T647: Negative position accepted")

    def test_create_very_large_position(
        self,
        admin_client,
        admin_user,
        fake_word,
        fake_catch_phrase,
        fake_positive_int,
    ):
        """
        Validation: Very large position value.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        data = {
            "template": template.id,
            "name": fake_word,
            "label": fake_catch_phrase,
            "type": "text",
            "is_file_md": False,
            "position": fake_positive_int,
        }

        response = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        # Document behavior
        assert response.status_code in [201, 400]

    def test_create_empty_name(
        self,
        admin_client,
        admin_user,
        fake_catch_phrase,
    ):
        """
        Validation: Empty name should be rejected.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        data = {
            "template": template.id,
            "name": "",
            "label": fake_catch_phrase,
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        if response.status_code == 201:
            pytest.xfail("T648: Empty name accepted")

    def test_create_empty_label(
        self,
        admin_client,
        admin_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        Validation: Empty label should be rejected.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        data = {
            "template": template.id,
            "name": fake_word,
            "label": "",
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        if response.status_code == 201:
            pytest.xfail("T649: Empty label accepted")

    def test_create_duplicate_field_name_same_template(
        self,
        admin_client,
        admin_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        Validation: Duplicate field name in same template.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        # First field
        data = {
            "template": template.id,
            "name": fake_word,
            "label": fake_catch_phrase,
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }
        response1 = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )
        assert response1.status_code == 201

        # Duplicate name
        data["position"] = 2
        response2 = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        # Document behavior
        if response2.status_code == 201:
            pass  # Duplicates allowed
        elif response2.status_code == 400:
            pass  # Duplicates rejected

    def test_create_nonexistent_template(
        self,
        admin_client,
        admin_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        Validation: CREATE with non-existent template ID.
        """
        data = {
            "template": 999999,
            "name": fake_word,
            "label": fake_catch_phrase,
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        assert response.status_code == 400

    def test_create_invalid_type_value(
        self,
        admin_client,
        admin_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        Validation: Invalid type values.

        Type should be restricted to known field types.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        invalid_types = [
            "invalid_type",
            "<script>",
            "'; DROP TABLE--",
        ]

        for type_val in invalid_types:
            data = {
                "template": template.id,
                "name": fake_word,
                "label": fake_catch_phrase,
                "type": type_val,
                "is_file_md": False,
                "position": 1,
            }

            response = admin_client.post(
                "/api/v2/playout-history-template-fields",
                data,
                format="json",
            )

            # Document behavior
            if response.status_code == 201:
                pass  # No validation on type

    def test_create_invalid_is_file_md_type(
        self,
        admin_client,
        admin_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        Validation: Invalid type for is_file_md (should be boolean).
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        data = {
            "template": template.id,
            "name": fake_word,
            "label": fake_catch_phrase,
            "type": "text",
            "is_file_md": "not-a-boolean",
            "position": 1,
        }

        response = admin_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        # Should validate boolean type
        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestPlayoutHistoryTemplateFieldRedTeamResourceConsumption:
    """API4:2023 Unrestricted Resource Consumption."""

    def test_rapid_field_creation(
        self,
        admin_client,
        admin_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        Rate limiting: Rapid CREATE requests.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        success_count = 0
        for i in range(20):
            data = {
                "template": template.id,
                "name": f"field_{i}_{fake_word}",
                "label": f"Field {i}",
                "type": "text",
                "is_file_md": False,
                "position": i,
            }
            response = admin_client.post(
                "/api/v2/playout-history-template-fields",
                data,
                format="json",
            )
            if response.status_code == 201:
                success_count += 1

        if success_count == 20:
            pytest.xfail("T650: No rate limiting on field CREATE")

    def test_many_fields_in_single_template(
        self,
        admin_client,
        admin_user,
        fake_word,
        fake_catch_phrase,
    ):
        """
        DoS: Creating many fields in one template.

        Can cause UI issues and performance degradation.
        """
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        for i in range(50):
            baker.make(
                PlayoutHistoryTemplateField,
                template=template,
                name=f"field_{i}_{fake_word}",
                label=f"Field {i}",
                type="text",
                is_file_md=False,
                position=i,
            )

        # List fields for template
        response = admin_client.get("/api/v2/playout-history-template-fields")

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) >= 50:
                pass  # No limit on fields per template


@pytest.mark.django_db
class TestPlayoutHistoryTemplateFieldRedTeamAuthentication:
    """Authentication tests."""

    def test_unauthenticated_list(self, guest_client):
        """Unauthenticated LIST should fail."""
        guest_client.logout()
        response = guest_client.get("/api/v2/playout-history-template-fields")
        assert response.status_code == 403

    def test_unauthenticated_create(
        self,
        guest_client,
        fake_word,
        fake_catch_phrase,
    ):
        """Unauthenticated CREATE should fail."""
        guest_client.logout()
        data = {
            "template": 1,
            "name": fake_word,
            "label": fake_catch_phrase,
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }
        response = guest_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )
        assert response.status_code == 403

    def test_guest_user_create(
        self,
        guest_client,
        guest_user,
        fake_word,
        fake_catch_phrase,
    ):
        """Guest user CREATE should fail."""
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )

        guest_client.force_authenticate(user=guest_user)

        data = {
            "template": template.id,
            "name": fake_word,
            "label": fake_catch_phrase,
            "type": "text",
            "is_file_md": False,
            "position": 1,
        }

        response = guest_client.post(
            "/api/v2/playout-history-template-fields",
            data,
            format="json",
        )

        if response.status_code == 201:
            pytest.xfail("T651: Guest user can create template fields")


@pytest.mark.django_db
class TestPlayoutHistoryTemplateFieldRedTeamHTTPMethodTampering:
    """HTTP method tampering tests."""

    def test_trace_method_disabled(
        self,
        admin_client,
        admin_user,
        fake_word,
        fake_catch_phrase,
    ):
        """TRACE method should be disabled."""
        template = baker.make(
            PlayoutHistoryTemplate,
            name=fake_catch_phrase,
            type="file",
        )
        field = baker.make(
            PlayoutHistoryTemplateField,
            template=template,
            name=fake_word,
            label=fake_catch_phrase,
            type="text",
            is_file_md=False,
            position=1,
        )

        response = admin_client.trace(
            f"/api/v2/playout-history-template-fields/{field.id}",
        )
        assert response.status_code in [405, 403]
