"""
API v2 test fixtures and utilities.
"""

# Import role-based fixtures to make them available to all API tests
from tests.api.fixtures.role_fixtures import (  # noqa: F401
    admin_client,
    admin_user,
    guest_client,
    guest_user,
    host_and_guest_users,
    host_and_manager_users,
    host_client,
    host_user,
    manager_client,
    manager_user,
    session_client,
    two_host_users,
)

import pytest

# Backward-compatible aliases for fixtures removed from api/conftest.py
@pytest.fixture
def regular_user(host_user):
    """Alias for host_user (backward compatibility)."""
    return host_user


@pytest.fixture
def authenticated_client(admin_client):
    """Alias for admin_client (backward compatibility)."""
    return admin_client


@pytest.fixture
def anonymous_client():
    """Anonymous API client - no authentication."""
    return APIClient()


from django.conf import settings
from model_bakery import baker
from rest_framework.test import APIClient
from sdk.faker import faker as _faker

from sdk import now

# Configure model_bakery to generate timezone-aware datetimes using sdk.now
baker.generators.add("django.db.models.DateTimeField", now)
baker.generators.add("api.fields.TimezoneAwareDateTimeField", now)


@pytest.fixture
def faker():
    """Faker instance for generating fake data."""
    return _faker


@pytest.fixture
def fake_uuid(faker):
    """Generate a fake UUID."""
    return faker.uuid4()


@pytest.fixture
def fake_name(faker):
    """Generate a fake name."""
    return faker.name()


@pytest.fixture
def fake_first_name(faker):
    """Generate a fake first name."""
    return faker.first_name()


@pytest.fixture
def fake_last_name(faker):
    """Generate a fake last name."""
    return faker.last_name()


@pytest.fixture
def fake_email(faker):
    """Generate a fake email with fake TLD."""
    return faker.fake_email()


@pytest.fixture
def fake_username(faker):
    """Generate a fake username."""
    return faker.user_name()


@pytest.fixture
def fake_password(faker):
    """Generate a fake password."""
    return faker.password()


@pytest.fixture
def fake_phone(faker):
    """Generate a fake phone number."""
    return faker.phone_number()


@pytest.fixture
def fake_sentence(faker):
    """Generate a fake sentence."""
    return faker.sentence()


@pytest.fixture
def fake_paragraph(faker):
    """Generate a fake paragraph."""
    return faker.paragraph()


@pytest.fixture
def fake_word(faker):
    """Generate a fake word."""
    return faker.word()


@pytest.fixture
def fake_catch_phrase(faker):
    """Generate a fake catch phrase (for show/playlist names)."""
    return faker.catch_phrase()


@pytest.fixture
def fake_company(faker):
    """Generate a fake company name."""
    return faker.company()


@pytest.fixture
def fake_city(faker):
    """Generate a fake city."""
    return faker.city()


@pytest.fixture
def fake_country(faker):
    """Generate a fake country."""
    return faker.country()


@pytest.fixture
def fake_address(faker):
    """Generate a fake address."""
    return faker.address()


@pytest.fixture
def fake_job(faker):
    """Generate a fake job title."""
    return faker.job()


@pytest.fixture
def fake_domain(faker):
    """Generate a fake domain name."""
    return faker.domain_name()


@pytest.fixture
def fake_url(faker):
    """Generate a fake URL."""
    return faker.url()


@pytest.fixture
def fake_date(faker):
    """Generate a fake date."""
    return faker.date()


@pytest.fixture
def fake_datetime(faker):
    """Generate a fake datetime."""
    return faker.date_time()


@pytest.fixture
def fake_file_name(faker):
    """Generate a fake file name."""
    return faker.file_name()


@pytest.fixture
def fake_mime_type(faker):
    """Generate a fake MIME type."""
    return faker.mime_type()


@pytest.fixture
def fake_ipv4(faker):
    """Generate a fake IPv4 address."""
    return faker.ipv4()


@pytest.fixture
def fake_ipv6(faker):
    """Generate a fake IPv6 address."""
    return faker.ipv6()


@pytest.fixture
def fake_ip(faker):
    """Generate a fake IP address (IPv4 or IPv6)."""
    return faker.ip4() if faker.boolean() else faker.ipv6()


@pytest.fixture
def fake_port(faker):
    """Generate a fake port number."""
    return faker.port_number()


@pytest.fixture
def fake_int(faker):
    """Generate a fake integer."""
    return faker.random_int()


@pytest.fixture
def fake_small_int(faker):
    """Generate a fake small positive integer (1-100)."""
    return faker.random_int(min=1, max=100)


@pytest.fixture
def fake_positive_int(faker):
    """Generate a fake positive integer."""
    return faker.random_int(min=1, max=99999999)


@pytest.fixture
def fake_negative_int(faker):
    """Generate a fake negative integer."""
    return -faker.random_int(min=1, max=99999999)


@pytest.fixture
def fake_float(faker):
    """Generate a fake float."""
    return faker.pyfloat(positive=True)


@pytest.fixture
def fake_lat(faker):
    """Generate a fake latitude."""
    return faker.latitude()


@pytest.fixture
def fake_lon(faker):
    """Generate a fake longitude."""
    return faker.longitude()


@pytest.fixture
def fake_slug(faker):
    """Generate a fake slug."""
    return faker.slug()


@pytest.fixture
def fake_color(faker):
    """Generate a fake color hex code."""
    return faker.hex_color()


@pytest.fixture
def fake_text(faker, max_chars=100):
    """Generate fake text."""
    return faker.text(max_nb_chars=max_chars)


@pytest.fixture
def api_client() -> APIClient:
    """API client with Api-Key auth."""
    obj = APIClient()
    obj.credentials(
        HTTP_AUTHORIZATION=f"Api-Key {settings.CONFIG.general.api_key}",
    )
    return obj





# Allow Mock/MagicMock assignment to ForeignKey/ManyToMany fields in unit tests
from unittest.mock import Mock, MagicMock
from django.db.models.fields.related_descriptors import (
    ForwardManyToOneDescriptor,
    ReverseManyToOneDescriptor,
)


@pytest.fixture(autouse=True)
def disable_fk_validation_for_mocks(mocker):
    """Disable FK/M2M validation when Mock/MagicMock is assigned."""
    _original_fwd = ForwardManyToOneDescriptor.__set__
    _original_rev = ReverseManyToOneDescriptor.__set__

    def _fwd_set(self, instance, value):
        if isinstance(value, (Mock, MagicMock)):
            instance.__dict__[self.field.attname] = 1
            instance._state.fields_cache[self.field.get_cache_name()] = value
            return
        return _original_fwd(self, instance, value)

    def _rev_set(self, instance, value):
        if isinstance(value, (Mock, MagicMock)):
            instance.__dict__[self.field.name] = value
            return
        return _original_rev(self, instance, value)

    mocker.patch.object(ForwardManyToOneDescriptor, "__set__", _fwd_set)
    mocker.patch.object(ReverseManyToOneDescriptor, "__set__", _rev_set)
