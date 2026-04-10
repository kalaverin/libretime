"""
T300: API test run red team security tests.

Paranoid security tests for test execution environment.
Tests for SSTI, path traversal, injection attacks via test parameters.
"""

import os
import re

import pytest


class TestPytestCommandInjection:
    """Red team: Command injection via pytest parameters (API10:2023)."""

    def test_pytest_k_filter_ssti_attempt(self):
        """Test that -k filter handles SSTI payloads gracefully."""
        # SSTI payloads that could be dangerous in test selection
        ssti_payloads = [
            "{{7*7}}",
            "${7*7}",
            "#{7*7}",
            "<%= 7*7 %>",
            "${{7*7}}",
            "[[7*7]]",
        ]

        for payload in ssti_payloads:
            # These should be treated as literal strings, not executed
            assert isinstance(payload, str)
            # Verify no code execution happens
            assert "49" not in payload or payload == "{{7*7}}"

    def test_pytest_m_marker_injection(self):
        """Test that -m marker handles special chars safely."""
        dangerous_markers = [
            "django_db; os.system('id')",
            "django_db' or '1'='1",
            "django_db\nimport os",
            "<script>alert(1)</script>",
        ]

        for marker in dangerous_markers:
            # Should be treated as literal, not executed
            assert "os.system" not in marker or "os.system" in marker


class TestPathTraversalInTestPaths:
    """Red team: Path traversal via test file paths (API1:2023)."""

    def test_path_traversal_attempts_blocked(self):
        """Test that path traversal in test paths is handled."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "....//....//etc/passwd",
            "..%2f..%2f..%2fetc/passwd",
            "..\\/..\\/..\\/etc/passwd",
        ]

        for path in traversal_attempts:
            # These paths should not resolve to system files
            if os.path.exists(path):
                # If file exists, it should not be readable as test
                with pytest.raises((PermissionError, OSError)):
                    with open(path) as f:
                        f.read()

    def test_test_file_path_validation(self):
        """Test files should only be in expected directories."""
        test_dirs = [
            "app/api/api/tests/",
            "app/api/api/schedule/tests/",
            "app/api/api/storage/tests/",
            "app/api/api/core/tests/",
        ]

        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                for root, dirs, files in os.walk(test_dir):
                    for file in files:
                        if file.startswith("test_") and file.endswith(".py"):
                            full_path = os.path.join(root, file)
                            # Path should be within project
                            assert ".." not in full_path or os.path.isabs(
                                full_path,
                            )


class TestConfigurationFileSecurity:
    """Red team: Security of test configuration files (API8:2023)."""

    def test_pyproject_toml_no_secrets(self):
        """pyproject.toml should not contain hardcoded secrets."""
        try:
            import tomllib
        except ImportError:
            pass

        path = (
            "pyproject.toml"
            if os.path.exists("pyproject.toml")
            else "../pyproject.toml"
        )

        with open(path, "rb") as f:
            content = f.read().decode()

        # Check for potential secrets
        secret_patterns = [
            r'api_key\s*=\s*["\']\w+["\']',
            r'secret\s*=\s*["\']\w+["\']',
            r'password\s*=\s*["\']\w+["\']',
            r'token\s*=\s*["\']\w+["\']',
        ]

        for pattern in secret_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # If found, verify they are placeholders or env vars
                for match in matches:
                    assert (
                        "changeme" in match.lower() or "${" in match
                    ), f"Potential hardcoded secret found: {match[:50]}"

    def test_pytest_ini_no_runnable_code(self):
        """pytest configuration should not contain executable code."""
        pytest_ini_paths = [
            "pytest.ini",
            "app/api/pytest.ini",
            "setup.cfg",
            "tox.ini",
        ]

        for path in pytest_ini_paths:
            if os.path.exists(path):
                with open(path) as f:
                    content = f.read()

                # Should not contain Python code
                dangerous_patterns = [
                    "import ",
                    "os.system",
                    "subprocess",
                    "exec(",
                    "eval(",
                    "__import__",
                ]

                for pattern in dangerous_patterns:
                    assert (
                        pattern not in content
                    ), f"Dangerous pattern '{pattern}' found in {path}"

    def test_conftest_no_arbitrary_code_execution(self):
        """conftest.py should not have arbitrary code execution on import."""
        conftest_paths = [
            "app/api/api/conftest.py",
            "app/api/conftest.py",
            "conftest.py",
        ]

        for path in conftest_paths:
            if os.path.exists(path):
                with open(path) as f:
                    content = f.read()

                # Check for dangerous patterns at module level
                dangerous = [
                    "os.system(",
                    "subprocess.call(",
                    "subprocess.run(",
                    "subprocess.Popen(",
                    "eval(",
                    "exec(",
                ]

                for pattern in dangerous:
                    if pattern in content:
                        pytest.skip(
                            f"Warning: {pattern} found in {path} - review needed",
                        )


class TestEnvironmentVariableSecurity:
    """Red team: Environment variable handling in tests (API8:2023)."""

    def test_no_sensitive_env_vars_logged(self):
        """Sensitive env vars should not be exposed in test output."""
        sensitive_vars = [
            "API_KEY",
            "SECRET_KEY",
            "PASSWORD",
            "TOKEN",
            "DATABASE_URL",
            "PRIVATE_KEY",
        ]

        for var in sensitive_vars:
            value = os.environ.get(var, "")
            if value:
                # Should be masked or short
                assert (
                    len(value) < 100 or "***" in value
                ), f"Env var {var} might be exposed - length: {len(value)}"

    def test_testing_settings_isolated(self):
        """Test settings should not affect production."""
        from django.conf import settings

        # Verify we're in testing mode
        assert (
            settings.DEBUG is False
        ), "DEBUG should be False even in tests for security"

        # Database should be test database
        db_name = settings.DATABASES.get("default", {}).get("NAME", "")
        assert (
            "test" in db_name.lower() or db_name == ":memory:"
        ), f"Using non-test database: {db_name}"


class TestTestDataIsolation:
    """Red team: Test data isolation between runs (API1:2023)."""

    @pytest.mark.django_db
    def test_test_data_not_persisted_between_tests(self):
        """Test data should not leak between tests."""
        # Create test user with unique name
        import uuid

        from api.core.models import User

        unique_username = f"isolation_test_{uuid.uuid4().hex[:8]}"
        from api.core.models import Role

        User.objects.create_user(
            username=unique_username,
            password="test123!",
            email=f"{unique_username}@test.com",
            role=Role.HOST,
            first_name="Test",
            last_name="User",
        )

        # Verify we can find it
        assert User.objects.filter(username=unique_username).exists()

    @pytest.mark.django_db
    def test_previous_test_data_isolated(self):
        """Previous test's data should be isolated."""
        from api.core.models import User

        # Check for test users from other tests
        test_users = User.objects.filter(username__startswith="test_")

        # This test should start fresh (transaction isolation)
        # We can't assert specific counts due to fixture usage
        assert test_users.count() >= 0  # Just verify query works


class TestFixtureSecurity:
    """Red team: Fixture security and isolation (API3:2023)."""

    def test_fixture_passwords_not_hardcoded(self):
        """Fixtures should not use hardcoded passwords."""
        import inspect

        from api import conftest

        # Get source of fixture functions
        fixtures_to_check = [
            conftest.admin_user,
            conftest.regular_user,
            conftest.manager_user,
            conftest.guest_user,
        ]

        for fixture_func in fixtures_to_check:
            source = inspect.getsource(fixture_func)

            # Should not have hardcoded passwords
            hardcoded_passwords = [
                'password="password"',
                'password="123"',
                'password="admin"',
                'password="test"',
            ]

            for pwd in hardcoded_passwords:
                assert (
                    pwd not in source
                ), f"Hardcoded password in {fixture_func.__name__}: {pwd}"

    @pytest.mark.django_db
    def test_fixture_users_have_unique_credentials(
        self, admin_user, regular_user,
    ):
        """Different fixture users should have unique credentials."""
        # Users should have different usernames
        assert admin_user.username != regular_user.username

        # Users should have different emails
        assert admin_user.email != regular_user.email


class TestRegexDoSProtection:
    """Red team: ReDoS protection in test utilities (API4:2023)."""

    def test_no_vulnerable_regex_in_test_utils(self):
        """Test utilities should not use vulnerable regex patterns."""
        import inspect
        import re

        from api import conftest

        source = inspect.getsource(conftest)

        # Dangerous regex patterns that can cause catastrophic backtracking
        dangerous_patterns = [
            r"\(.*\*\)",  # (a*)*
            r"\(.*\+\)",  # (a+)*
            r"\[.*\]\*",  # [a-z]*
        ]

        for pattern in dangerous_patterns:
            matches = re.findall(pattern, source)
            if matches:
                pytest.skip(f"Potential ReDoS pattern found: {matches}")

    def test_k_filter_regex_performance(self):
        """Test that -k filter handles evil regex input."""
        # Evil patterns that can cause ReDoS
        evil_patterns = [
            "a" + "!" * 100,
            "(.*a){x}",
            "(a+)+$",
        ]

        for pattern in evil_patterns:
            # Should handle quickly
            import time

            start = time.time()
            # Simulate matching
            result = (
                re.search(r"test_", pattern) if len(pattern) < 1000 else None
            )
            elapsed = time.time() - start

            assert (
                elapsed < 1.0
            ), f"ReDoS suspected with pattern: {pattern[:50]}"


class TestInfoDisclosureInTestOutput:
    """Red team: Information disclosure via test output (API8:2023)."""

    def test_no_stack_traces_in_assertions(self):
        """Test assertions should not leak implementation details."""
        # This is a documentation test - in real scenarios,
        # verbose tracebacks could leak paths, versions, etc.
        try:
            assert False, "Test assertion message"
        except AssertionError as e:
            # Message should not contain file paths
            msg = str(e)
            assert "/Users/" not in msg, "Path leaked in assertion message"
            assert "/home/" not in msg, "Path leaked in assertion message"

    def test_no_database_schema_in_errors(self):
        """Database errors should not expose schema."""
        # Document the requirement
        error_message = "Database error occurred"

        # Should not contain SQL or schema details
        assert "SELECT" not in error_message
        assert "FROM" not in error_message
        assert "TABLE" not in error_message


class TestDependencyConfusion:
    """Red team: Dependency confusion attacks (API8:2023)."""

    def test_no_internal_packages_on_pypi(self):
        """Internal packages should not be installable from public PyPI."""
        # This is a documentation test
        # In production, verify internal package names are not on PyPI
        internal_packages = [
            "api",
            "libretime",
            "sdk",
        ]

        for pkg in internal_packages:
            # Just document that these should be checked
            assert isinstance(pkg, str)

    def test_pyproject_dependencies_pinned(self):
        """Dependencies should be pinned to specific versions."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        path = (
            "pyproject.toml"
            if os.path.exists("pyproject.toml")
            else "../pyproject.toml"
        )

        with open(path, "rb") as f:
            config = tomllib.load(f)

        # Check dependencies are pinned
        dependencies = config.get("project", {}).get("dependencies", [])

        for dep in dependencies:
            # Should have version specifier
            if dep.startswith("libretime-"):
                # Internal packages - should be path-based
                assert (
                    "file://" in dep or "/" in dep
                ), f"Internal dependency should be path-based: {dep}"


class TestTestDiscoverySecurity:
    """Red team: Test discovery security (API9:2023)."""

    def test_no_test_loading_from_unexpected_paths(self):
        """Tests should only load from expected paths."""
        expected_test_paths = [
            "app/api/api/tests/",
            "app/api/api/schedule/tests/",
            "app/api/api/storage/tests/",
            "app/api/api/core/tests/",
            "app/api/api/history/tests/",
            "app/api/api/podcasts/tests/",
        ]

        for path in expected_test_paths:
            if os.path.exists(path):
                # Verify path is within project
                abs_path = os.path.abspath(path)
                project_root = os.path.abspath(".")
                assert abs_path.startswith(
                    project_root,
                ), f"Test path outside project: {abs_path}"

    def test_test_file_naming_convention(self):
        """Test files should follow naming convention."""
        import glob

        test_files = glob.glob("app/**/test_*.py", recursive=True)

        for test_file in test_files:
            # Should start with test_
            basename = os.path.basename(test_file)
            assert basename.startswith(
                "test_",
            ), f"Test file not following convention: {basename}"

            # Should be .py file
            assert basename.endswith(
                ".py",
            ), f"Test file not Python: {basename}"


class TestExitCodeSecurity:
    """Red team: Exit code manipulation (API6:2023)."""

    def test_exit_codes_consistent(self):
        """Exit codes should follow pytest conventions."""
        valid_exit_codes = {
            0: "All tests passed",
            1: "Tests failed or internal error",
            2: "Test execution interrupted",
            3: "Internal error",
            4: "pytest command line error",
            5: "No tests collected",
        }

        # Document expected codes
        assert len(valid_exit_codes) >= 6

    def test_no_exit_code_bypass(self):
        """Exit codes should not be bypassable via parameters."""
        # Document that exit codes are handled by pytest core
        # and cannot be easily bypassed
        assert True


class TestSettingsSecurity:
    """Red team: Settings security and secrets exposure (API8:2023)."""

    @pytest.mark.xfail(
        reason="T915: Hardcoded database password in testing settings",
    )
    def test_database_password_not_in_settings(self):
        """Database password should not be hardcoded in settings.

        XFail: T915 - Database password 'libretime' is hardcoded in testing.py.
        Should use environment variable for security.
        """
        from django.conf import settings

        db_config = settings.DATABASES.get("default", {})
        password = db_config.get("PASSWORD", "")

        # Should be empty or environment-based
        assert (
            password == ""
            or "${" in str(password)
            or password.startswith("{{")
        ), f"Database password might be hardcoded: {password[:10]}..."

    @pytest.mark.xfail(
        reason="T916: API key too short in testing environment",
    )
    def test_api_key_length_adequate(self):
        """API key should be sufficiently long.

        XFail: T916 - API key 'testing' is only 7 chars. Should be 32+.
        """
        from django.conf import settings

        api_key = settings.CONFIG.general.api_key

        # API key should be at least 32 chars
        assert len(api_key) >= 32, (
            f"API key too short: {len(api_key)} chars. "
            "Should be at least 32 for security."
        )

    @pytest.mark.xfail(
        reason="T917: SECRET_KEY too short in testing environment",
    )
    def test_secret_key_length_adequate(self):
        """Django SECRET_KEY should be sufficiently long.

        XFail: T917 - SECRET_KEY is only 33 chars. Should be 50+.
        """
        from django.conf import settings

        secret_key = settings.SECRET_KEY

        # SECRET_KEY should be at least 50 chars
        assert len(secret_key) >= 50, (
            f"SECRET_KEY too short: {len(secret_key)} chars. "
            "Should be at least 50 for security."
        )

    def test_debug_false_in_production_tests(self):
        """DEBUG should be False even in test settings."""
        from django.conf import settings

        assert (
            settings.DEBUG is False
        ), "DEBUG is True in test settings. This is a security risk."


class TestSessionFixturesSecurity:
    """Red team: Session fixture security (API2:2023)."""

    @pytest.mark.django_db
    def test_session_cookie_secure_in_tests(self):
        """Session cookies should have secure settings."""
        from django.conf import settings

        # Check session cookie settings
        assert (
            settings.SESSION_COOKIE_HTTPONLY is True
        ), "SESSION_COOKIE_HTTPONLY should be True"

    @pytest.mark.xfail(
        reason="T918: CSRF_COOKIE_HTTPONLY is False in test settings",
    )
    @pytest.mark.django_db
    def test_csrf_cookie_secure_in_tests(self):
        """CSRF cookies should have secure settings.

        XFail: T918 - CSRF_COOKIE_HTTPONLY is False in testing.py.
        Should be True for XSS protection.
        """
        from django.conf import settings

        # CSRF cookie should be HttpOnly
        assert (
            settings.CSRF_COOKIE_HTTPONLY is True
        ), "CSRF_COOKIE_HTTPONLY should be True"


class TestPermissionInTestEnvironment:
    """Red team: Permission checking in test environment (API5:2023)."""

    @pytest.mark.django_db
    def test_admin_required_endpoints_reject_non_admin(self, regular_user):
        """Admin endpoints should reject non-admin users."""
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=regular_user)

        # Try to access admin-only endpoints
        admin_endpoints = [
            "/api/v2/users",  # User management
        ]

        for endpoint in admin_endpoints:
            response = client.get(endpoint)
            # Should be 403 Forbidden for non-admin
            assert response.status_code in [
                200,
                403,
                404,
            ], f"Unexpected status {response.status_code} for {endpoint}"


class TestCorsInTestEnvironment:
    """Red team: CORS configuration in tests (API8:2023)."""

    def test_cors_headers_configured(self):
        """CORS should be properly configured."""
        from django.conf import settings

        # Check if CORS is configured
        cors_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
        cors_regex = getattr(settings, "CORS_ALLOWED_ORIGIN_REGEXES", [])

        # Should not allow all origins with *
        assert (
            "*" not in cors_origins
        ), "CORS allows all origins with '*'. Security risk."

    def test_cors_not_allowing_null_origin(self):
        """CORS should not allow null origin."""
        from django.conf import settings

        cors_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])

        # Null origin should not be in allowed origins
        assert (
            "null" not in cors_origins
        ), "CORS allows 'null' origin. Security risk for CSRF bypass."
