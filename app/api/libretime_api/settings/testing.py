import os

from libretime_api._fixtures import fixture_path

os.environ.setdefault("LIBRETIME_DEBUG", "true")
os.environ.setdefault("LIBRETIME_GENERAL_PUBLIC_URL", "http://localhost")
os.environ.setdefault("LIBRETIME_GENERAL_API_KEY", "testing")
os.environ.setdefault("LIBRETIME_GENERAL_SECRET_KEY", "testing")
os.environ.setdefault("LIBRETIME_STORAGE_PATH", str(fixture_path))

# pylint: disable=wrong-import-position,unused-import

# Email
# https://docs.djangoproject.com/en/4.2/topics/email/

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Testing
# https://docs.djangoproject.com/en/3.2/ref/settings/#test-runner

TEST_RUNNER = "libretime_api.tests.runner.ManagedModelTestRunner"
