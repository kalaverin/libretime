"""Custom model fields for LibreTime API."""

from datetime import datetime
from typing import Any

from dateutil import parser
from django.db import models
from django.utils.timezone import is_naive, make_aware
from sdk.compat import UTC
from typing_extensions import override


class TimezoneAwareDateTimeField(models.DateTimeField):
    """
    DateTimeField that ensures timezone-aware datetimes.

    - When reading from DB: converts naive datetime to UTC-aware
    - When saving: ensures datetime is aware (converts to UTC if needed)

    This field is required for legacy tables with TIMESTAMP (no timezone)
    columns to ensure Django always works with timezone-aware datetimes.
    """

    def from_db_value(
        self,
        value: datetime | None,
        expression: Any,  # noqa: ARG002
        connection: Any,  # noqa: ARG002
    ) -> datetime | None:
        """Convert naive datetime from DB to timezone-aware."""
        if value is None:
            return None
        if is_naive(value):
            # Legacy DB stores naive UTC datetime, make it aware
            return make_aware(value, UTC)
        return value

    @override
    def get_prep_value(self, value: datetime | str | None) -> datetime | None:
        """Ensure datetime is aware before saving."""
        if value is None:
            return None

        if isinstance(value, str):
            value = parser.parse(value)

        if is_naive(value):
            value = make_aware(value, UTC)

        return value.astimezone(UTC)
