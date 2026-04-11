"""Field validation utilities for common validation patterns."""

import re

from typing import Any

from django.core.validators import ValidationError
from django.utils.translation import gettext_lazy as _

# =============================================================================
# SQL Injection Protection
# =============================================================================

# Patterns that indicate SQL injection attempts
_SQL_INJECTION_PATTERNS = [
    # Union-based
    r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
    # Boolean-based
    r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
    # Error-based
    r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
    # Stacked queries
    r"((\%27)|(\'))union",
    r"exec(\s|\+)\(s\s*\+\s*x",
    # OR/AND based - detect OR/AND between quoted values
    r"'[^']*'\s+(or|and)\s+'[^']*'",
    r"\"[^\"]*\"\s+(or|and)\s+\"[^\"]*\"",
    r"\d+\s+(or|and)\s+\d+\s*=\s*\d+",
    # Comment-based
    r"--|/\*|\*/",
    # Common SQL keywords in context
    r"(union|select|insert|update|delete|drop|create|alter)\s+",
    r"(from|where|table|database)\s+",
]

_SQLI_REGEX = re.compile("|".join(_SQL_INJECTION_PATTERNS), re.IGNORECASE)


def validate_no_sql_injection(value: Any, field_name: str = "value") -> Any:
    """Validate that value doesn't contain SQL injection patterns."""
    if not isinstance(value, str):
        return value

    if _SQLI_REGEX.search(value):
        raise ValidationError(
            _("{field} contains invalid characters.").format(field=field_name),
            code=f"{field_name}_invalid_chars",
        )
    return value


# =============================================================================
# ID Validation
# =============================================================================


def validate_integer_id(value: Any, field_name: str = "id") -> int:
    """Validate that value is a valid integer ID (positive integer)."""
    if value is None:
        return value

    # Handle string input (from query params)
    if isinstance(value, str):
        # Check for SQL injection first
        validate_no_sql_injection(value, field_name)

        # Check for non-digit characters
        if not value.lstrip("-").isdigit():
            raise ValidationError(
                _("{field} must be an integer.").format(field=field_name),
                code=f"{field_name}_invalid",
            )
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(
                _("{field} must be an integer.").format(field=field_name),
                code=f"{field_name}_invalid",
            )

    # Must be int at this point
    if not isinstance(value, int):
        raise ValidationError(
            _("{field} must be an integer.").format(field=field_name),
            code=f"{field_name}_invalid",
        )

    # Check for positive
    if value <= 0:
        raise ValidationError(
            _("{field} must be a positive integer.").format(field=field_name),
            code=f"{field_name}_invalid",
        )

    return value


def validate_foreign_key_id(value: Any, field_name: str = "id") -> int:
    """Validate foreign key ID - positive integer, no SQLi."""
    return validate_integer_id(value, field_name)


# =============================================================================
# Negative Value Validators
# =============================================================================


def validate_non_negative_int(value: Any, field_name: str = "value") -> int:
    """Validate that integer value is non-negative."""
    if value is None:
        return value

    try:
        int_value = int(value)
    except (TypeError, ValueError):
        raise ValidationError(
            _("{field} must be an integer.").format(field=field_name),
            code=f"{field_name}_not_integer",
        )

    if int_value < 0:
        raise ValidationError(
            _("{field} cannot be negative.").format(field=field_name),
            code=f"{field_name}_negative",
        )

    return int_value


def validate_non_negative_float(
    value: Any, field_name: str = "value",
) -> float:
    """Validate that float value is non-negative."""
    if value is None:
        return value

    try:
        float_value = float(value)
    except (TypeError, ValueError):
        raise ValidationError(
            _("{field} must be a number.").format(field=field_name),
            code=f"{field_name}_not_number",
        )

    if float_value < 0:
        raise ValidationError(
            _("{field} cannot be negative.").format(field=field_name),
            code=f"{field_name}_negative",
        )

    return float_value


def validate_positive_int(value: Any, field_name: str = "value") -> int:
    """Validate that integer value is positive (greater than 0)."""
    if value is None:
        return value

    try:
        int_value = int(value)
    except (TypeError, ValueError):
        raise ValidationError(
            _("{field} must be an integer.").format(field=field_name),
            code=f"{field_name}_not_integer",
        )

    if int_value <= 0:
        raise ValidationError(
            _("{field} must be greater than 0.").format(field=field_name),
            code=f"{field_name}_not_positive",
        )

    return int_value


# =============================================================================
# Time/Duration Validators
# =============================================================================


def validate_time_order(cue_in: Any, cue_out: Any) -> None:
    """Validate that cue_out is after cue_in."""
    if cue_in is None or cue_out is None:
        return

    # Handle duration strings (HH:MM:SS.ms or ISO 8601 duration)
    from datetime import timedelta

    def parse_duration(value: Any) -> timedelta | None:
        if isinstance(value, timedelta):
            return value
        if isinstance(value, str):
            # Try HH:MM:SS.ms format
            parts = value.replace(",", ".").split(":")
            try:
                if len(parts) == 3:
                    hours = float(parts[0])
                    minutes = float(parts[1])
                    seconds = float(parts[2])
                    return timedelta(
                        hours=hours, minutes=minutes, seconds=seconds,
                    )
                if len(parts) == 2:
                    minutes = float(parts[0])
                    seconds = float(parts[1])
                    return timedelta(minutes=minutes, seconds=seconds)
            except (ValueError, TypeError):
                pass
        return None

    in_duration = parse_duration(cue_in)
    out_duration = parse_duration(cue_out)

    if in_duration is not None and out_duration is not None:
        if out_duration <= in_duration:
            raise ValidationError(
                _("cue_out must be after cue_in."),
                code="cue_out_before_cue_in",
            )


def validate_duration_format(value: Any, field_name: str = "duration") -> Any:
    """Validate duration format (HH:MM:SS or ISO 8601)."""
    if value is None:
        return value

    from datetime import timedelta

    if isinstance(value, timedelta):
        return value

    if isinstance(value, str):
        # Allow HH:MM:SS.ms format
        pattern = r"^\d{1,2}:\d{2}:\d{2}(\.\d+)?$"
        if re.match(pattern, value):
            return value

        # Allow ISO 8601 duration format
        iso_pattern = r"^P(\d+D)?(T(\d+H)?(\d+M)?(\d+(\.\d+)?S)?)?$"
        if re.match(iso_pattern, value, re.IGNORECASE):
            return value

    raise ValidationError(
        _("{field} must be in HH:MM:SS format.").format(field=field_name),
        code=f"{field_name}_invalid_format",
    )


# =============================================================================
# Color/Format Validators
# =============================================================================

_HEX_COLOR_PATTERN = re.compile(r"^[0-9A-Fa-f]{6}$")


def validate_hex_color(value: Any, field_name: str = "color") -> str:
    """Validate 6-digit hex color format (RRGGBB)."""
    if value is None:
        return value

    if not isinstance(value, str):
        raise ValidationError(
            _("{field} must be a string.").format(field=field_name),
            code=f"{field_name}_not_string",
        )

    # Remove # prefix if present
    value = value.lstrip("#")

    if not _HEX_COLOR_PATTERN.match(value):
        raise ValidationError(
            _(
                "{field} must be a valid 6-digit hex color (e.g., FF0000).",
            ).format(field=field_name),
            code=f"{field_name}_invalid_format",
        )

    return value.upper()


# =============================================================================
# Length/Size Validators
# =============================================================================


def validate_max_length(
    value: Any, max_length: int, field_name: str = "value",
) -> Any:
    """Validate that string value doesn't exceed max length."""
    if value is None:
        return value

    if isinstance(value, str) and len(value) > max_length:
        raise ValidationError(
            _("{field} must not exceed {max} characters.").format(
                field=field_name, max=max_length,
            ),
            code=f"{field_name}_too_long",
        )

    return value


def validate_url_length(
    value: Any, max_length: int = 2048, field_name: str = "url",
) -> Any:
    """Validate URL length."""
    return validate_max_length(value, max_length, field_name)


# =============================================================================
# Choice Validators
# =============================================================================


def validate_choice(
    value: Any, valid_choices: set[str], field_name: str = "value",
) -> Any:
    """Validate that value is in allowed choices."""
    if value is None:
        return value

    if str(value).lower() not in {c.lower() for c in valid_choices}:
        raise ValidationError(
            _("{field} must be one of: {choices}.").format(
                field=field_name, choices=", ".join(sorted(valid_choices)),
            ),
            code=f"{field_name}_invalid_choice",
        )

    return value


# =============================================================================
# Required Field Validators
# =============================================================================


def validate_not_null(value: Any, field_name: str = "value") -> Any:
    """Validate that value is not null/None."""
    if value is None:
        raise ValidationError(
            _("{field} is required.").format(field=field_name),
            code=f"{field_name}_required",
        )
    return value


def validate_not_empty_string(value: Any, field_name: str = "value") -> Any:
    """Validate that string value is not empty."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(
            _("{field} cannot be empty.").format(field=field_name),
            code=f"{field_name}_empty",
        )
    return value
