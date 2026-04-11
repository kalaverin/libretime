from os import environ, getenv

import structlog

from api import PACKAGE, VERSION

API_VERSION = "2.0.0"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = getenv("LIBRETIME_DEBUG", "false").lower() == "true"

# Application definition

INSTALLED_APPS = [
    "api.legacy",
    "api.core",
    "api.history",
    "api.storage",
    "api.podcasts",
    "api.schedule",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
]

MIDDLEWARE = [
    "api.middlewares.RequestLoggingMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "api.wsgi.application"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/api/v2/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Logging
# https://docs.djangoproject.com/en/3.2/topics/logging/#configuring-logging


def setup_logger(log_filepath: str | None):
    from sdk.structlog import configure

    configure(level="debug", is_textual=True)
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json_formatter": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
            },
            "plain_console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(),
            },
            "key_value": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.KeyValueRenderer(
                    key_order=["timestamp", "level", "event", "logger"],
                ),
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "plain_console",
            },
            "json_file": {
                "class": "logging.handlers.WatchedFileHandler",
                "filename": "log/api.log",
                "formatter": "json_formatter",
            },
        },
        "loggers": {
            "django_structlog": {
                "handlers": ["console", "json_file"],
                "level": "INFO",
            },
            "api": {
                "handlers": ["console", "json_file"],
                "level": "INFO",
            },
        },
    }


# Rest Framework
# https://www.django-rest-framework.org/api-guide/settings/

renderer_classes = ["rest_framework.renderers.JSONRenderer"]
if DEBUG:
    renderer_classes += ["rest_framework.renderers.BrowsableAPIRenderer"]

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": renderer_classes,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "api.permissions.SafeSessionAuthentication",
        "api.permissions.SafeBasicAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "api.permissions.IsSystemTokenOrUser",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "URL_FIELD_NAME": "item_url",
}

# Auth
# https://docs.djangoproject.com/en/3.2/topics/auth/customizing/#substituting-a-custom-user-model

AUTH_USER_MODEL = "core.User"

# Spectacular
# https://drf-spectacular.readthedocs.io/en/latest/settings.html

SPECTACULAR_ENUM_NAME_OVERRIDES = {
    "FileImportStatusEnum": "api.storage.models.File.ImportStatus",
    "PlaylistContentKindEnum": "api.schedule.models.PlaylistContent.Kind",
    "SmartBlockKindEnum": "api.schedule.models.SmartBlock.Kind",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "LibreTime API",
    "DESCRIPTION": "Radio Broadcast & Automation Platform",
    "VERSION": API_VERSION,
    "ENUM_NAME_OVERRIDES": SPECTACULAR_ENUM_NAME_OVERRIDES,
}

# Sentry
# https://docs.sentry.io/platforms/python/guides/django/
if "SENTRY_DSN" in environ:
    # pylint: disable=import-outside-toplevel
    import sentry_sdk

    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        traces_sample_rate=1.0,
        release=f"{PACKAGE}@{VERSION}",
        integrations=[
            DjangoIntegration(),
        ],
    )
