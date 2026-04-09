import os

from api._fixtures import fixture_path

os.environ.setdefault("LIBRETIME_DEBUG", "true")
os.environ.setdefault("LIBRETIME_GENERAL_PUBLIC_URL", "http://localhost")
os.environ.setdefault("LIBRETIME_GENERAL_API_KEY", "testing")
os.environ.setdefault("LIBRETIME_GENERAL_SECRET_KEY", "testing")
os.environ.setdefault("LIBRETIME_STORAGE_PATH", str(fixture_path))

# pylint: disable=wrong-import-position,unused-import

# Import base settings (INSTALLED_APPS, etc.)
from api.settings._internal import *
from api.settings._schema import Config
from sdk.config import DatabaseConfig, GeneralConfig, RabbitMQConfig

# Test configuration
CONFIG = Config(
    general=GeneralConfig(
        public_url="http://localhost",
        api_key="testing",
        secret_key="testing-secret-key-for-tests-only",
    ),
    database=DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        name=os.getenv("POSTGRES_DB", "libretime_test"),
        user=os.getenv("POSTGRES_USER", "libretime"),
        password=os.getenv("POSTGRES_PASSWORD", "libretime"),
    ),
    rabbitmq=RabbitMQConfig(
        host="localhost",
        port=5672,
        user="libretime",
        password="libretime",
        vhost="/libretime",
    ),
)

SECRET_KEY = "testing-secret-key-for-tests-only"

# Timezone
# https://docs.djangoproject.com/en/4.2/topics/i18n/timezones/

TIME_ZONE = "UTC"
USE_TZ = True

# Email
# https://docs.djangoproject.com/en/4.2/topics/email/

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Testing
# https://docs.djangoproject.com/en/3.2/ref/settings/#test-runner

TEST_RUNNER = "api.tests.runner.ManagedModelTestRunner"

# Django REST Framework
# https://www.django-rest-framework.org/api-guide/settings/

REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # Inherit from _internal.py
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%SZ",
}

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "libretime_test"),
        "USER": os.getenv("POSTGRES_USER", "libretime"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "libretime"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    },
}
