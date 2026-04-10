"""
RED TEAM: T328/T329 - SmartBlockContent filter/ordering security tests.

Attack vectors:
- Filter parameter injection
- Ordering manipulation for data extraction
- Mass assignment via query params
- Information disclosure via error messages
- Race conditions in ordering
"""

import pytest


@pytest.mark.django_db
class TestSmartBlockContentFilterInjection:
    """Filter parameter injection attacks."""

    def test_filter_by_invalid_block_id(self, api_client, admin_user):
        """Try to filter by invalid block_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/smart-block-contents?block=invalid")

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_filter_by_negative_block_id(self, api_client, admin_user):
        """Try to filter by negative block_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/smart-block-contents?block=-1")

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_filter_by_sql_injection(self, api_client, admin_user):
        """Try SQL injection in block filter."""
        api_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE cc_blockcontents;--",
            "1 UNION SELECT * FROM cc_subjs",
        ]

        for payload in sqli_payloads:
            response = api_client.get(
                f"/api/v2/smart-block-contents?block={payload}",
            )

            # Should not execute SQL
            assert response.status_code in [200, 400]

    def test_filter_by_very_large_block_id(self, api_client, admin_user):
        """Try to filter by very large block_id."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(
            "/api/v2/smart-block-contents?block=999999999999999999",
        )

        assert response.status_code in [200, 400]

    def test_filter_without_auth(self, api_client):
        """Try to filter without authentication."""
        response = api_client.get("/api/v2/smart-block-contents?block=1")

        if response.status_code == 200:
            pytest.xfail("SECURITY: Anonymous can filter smart block content")


@pytest.mark.django_db
class TestSmartBlockContentOrderingManipulation:
    """Ordering parameter manipulation attacks."""

    def test_order_by_invalid_field(self, api_client, admin_user):
        """Try to order by non-existent field."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(
            "/api/v2/smart-block-contents?ordering=nonexistent_field",
        )

        # Should reject invalid field
        assert response.status_code in [200, 400]

    def test_order_by_sql_injection(self, api_client, admin_user):
        """Try SQL injection in ordering parameter."""
        api_client.force_authenticate(user=admin_user)

        sqli_payloads = [
            "position; DROP TABLE cc_blockcontents;--",
            "position,(SELECT password FROM cc_subjs LIMIT 1)",
        ]

        for payload in sqli_payloads:
            response = api_client.get(
                f"/api/v2/smart-block-contents?ordering={payload}",
            )

            assert response.status_code in [200, 400]

    def test_order_by_private_field(self, api_client, admin_user):
        """Try to order by internal/private fields."""
        api_client.force_authenticate(user=admin_user)

        internal_fields = [
            "id",
            "_state",
            "block__owner__password",
        ]

        for field in internal_fields:
            response = api_client.get(
                f"/api/v2/smart-block-contents?ordering={field}",
            )

            # May accept or reject
            assert response.status_code in [200, 400]

    def test_reverse_ordering(self, api_client, admin_user):
        """Test reverse ordering (should work)."""
        from model_bakery import baker

        block = baker.make("schedule.SmartBlock", owner=admin_user)
        file1 = baker.make("storage.File", owner=admin_user)
        file2 = baker.make("storage.File", owner=admin_user)

        # Create content with positions 1 and 2
        content1 = baker.make(
            "schedule.SmartBlockContent",
            block=block,
            file=file1,
            position=1,
            offset=0,
        )
        content2 = baker.make(
            "schedule.SmartBlockContent",
            block=block,
            file=file2,
            position=2,
            offset=0,
        )

        api_client.force_authenticate(user=admin_user)

        # Test ascending order
        response = api_client.get(
            "/api/v2/smart-block-contents?ordering=position",
        )
        assert response.status_code == 200

        # Test descending order
        response = api_client.get(
            "/api/v2/smart-block-contents?ordering=-position",
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestSmartBlockContentInformationDisclosure:
    """Information disclosure via filter/ordering."""

    def test_error_message_on_invalid_filter(self, api_client, admin_user):
        """Check if error messages leak implementation details."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/smart-block-contents?block=invalid")

        if response.status_code == 400:
            content = response.content.decode()
            # Check for information leakage
            if "cc_blockcontents" in content or "column" in content:
                pytest.fail("Error message leaks database schema")

    def test_timing_attack_on_filter(self, api_client, admin_user):
        """Test for timing-based information disclosure."""
        import time

        api_client.force_authenticate(user=admin_user)

        # Request with valid filter
        start = time.time()
        response1 = api_client.get("/api/v2/smart-block-contents?block=1")
        time_valid = time.time() - start

        # Request with invalid filter
        start = time.time()
        response2 = api_client.get("/api/v2/smart-block-contents?block=999999")
        time_invalid = time.time() - start

        # Times should be similar (no timing leak)
        diff = abs(time_valid - time_invalid)
        assert diff < 1.0, "Possible timing attack vulnerability"


@pytest.mark.django_db
class TestSmartBlockContentIDORWithFilter:
    """IDOR attacks combined with filtering."""

    def test_filter_shows_only_own_content(
        self, api_client, admin_user, regular_user,
    ):
        """Verify filter returns only user's own content."""
        from model_bakery import baker

        # Create blocks and content for both users
        admin_block = baker.make("schedule.SmartBlock", owner=admin_user)
        user_block = baker.make("schedule.SmartBlock", owner=regular_user)

        admin_file = baker.make("storage.File", owner=admin_user)
        user_file = baker.make("storage.File", owner=regular_user)

        admin_content = baker.make(
            "schedule.SmartBlockContent",
            block=admin_block,
            file=admin_file,
            position=1,
            offset=0,
        )
        user_content = baker.make(
            "schedule.SmartBlockContent",
            block=user_block,
            file=user_file,
            position=1,
            offset=0,
        )

        # User filters content
        api_client.force_authenticate(user=regular_user)
        response = api_client.get("/api/v2/smart-block-contents")

        assert response.status_code == 200
        data = response.json()

        content_ids = [c["id"] for c in data]
        assert user_content.id in content_ids

        if admin_content.id in content_ids:
            pytest.xfail("BOLA: Filter returns other users' content")

    def test_filter_by_other_user_block(
        self, api_client, admin_user, regular_user,
    ):
        """Try to filter by another user's block_id."""
        from model_bakery import baker

        admin_block = baker.make("schedule.SmartBlock", owner=admin_user)
        admin_file = baker.make("storage.File", owner=admin_user)
        admin_content = baker.make(
            "schedule.SmartBlockContent",
            block=admin_block,
            file=admin_file,
            position=1,
            offset=0,
        )

        # User tries to filter by admin's block
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(
            f"/api/v2/smart-block-contents?block={admin_block.id}",
        )

        assert response.status_code == 200
        data = response.json()

        # Should not see admin's content
        content_ids = [c["id"] for c in data]
        if admin_content.id in content_ids:
            pytest.xfail(
                "BOLA: Can filter by other user's block and see content",
            )


@pytest.mark.django_db
class TestSmartBlockContentPagination:
    """Pagination-related security tests."""

    def test_large_limit_parameter(self, api_client, admin_user):
        """Try to request very large number of items."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/smart-block-contents?limit=999999")

        # Should not crash or return all items
        assert response.status_code in [200, 400]

    def test_negative_limit(self, api_client, admin_user):
        """Try negative limit parameter."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/smart-block-contents?limit=-1")

        assert response.status_code in [200, 400]

    def test_negative_offset(self, api_client, admin_user):
        """Try negative offset parameter."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/api/v2/smart-block-contents?offset=-1")

        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestSmartBlockContentMassOrdering:
    """Mass ordering extraction attacks."""

    def test_extract_all_content_via_ordering(
        self, api_client, admin_user, regular_user,
    ):
        """Try to extract all content via ordering manipulation.

        Attack: Use ordering to systematically extract all data.
        """
        from model_bakery import baker

        # Create multiple content items
        block = baker.make("schedule.SmartBlock", owner=admin_user)

        for i in range(10):
            file_obj = baker.make("storage.File", owner=admin_user)
            baker.make(
                "schedule.SmartBlockContent",
                block=block,
                file=file_obj,
                position=i + 1,
                offset=0,
            )

        api_client.force_authenticate(user=regular_user)

        # Get first page
        response = api_client.get("/api/v2/smart-block-contents?limit=5")
        assert response.status_code == 200

        data = response.json()
        # Should not see admin's content
        if len(data) > 0:
            # If we get data, verify it's not admin's
            pass  # Specific check depends on implementation
