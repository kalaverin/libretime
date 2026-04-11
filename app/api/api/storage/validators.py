"""
Storage app validators.

Security validators for file-related fields.
"""

import re
import unicodedata

from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Pattern to detect path traversal attempts
# Matches: ../, ..\, ..%2f, ..%252f, %2e%2e, etc.
PATH_TRAVERSAL_PATTERN = re.compile(
    r"(?:\.{2,}[/\\])|"  # ../ or ..\ or .../
    r"(?:\.{2,}%2[fF])|"  # ..%2f or ..%2F
    r"(?:%2[eE]%2[eE]%2[fF])|"  # %2e%2e%2f (URL encoded ../)
    r"(?:%25{1,2}2[fF])|"  # Double-encoded %
    r"(?:[/\\]\.\.[/\\])|"  # /../ or \..\
    r"^(?:/|[a-zA-Z]:[/\\])",  # Absolute paths starting with / or C:\ etc
)

# Pattern to detect absolute paths
# Unix /, Windows C:\, UNC \, URL //
ABSOLUTE_PATH_PATTERN = re.compile(r"^(?:/|[a-zA-Z]:[/\\]|\\\\|//)")

# Pattern to detect null bytes
NULL_BYTE_PATTERN = re.compile(r"\x00|%00")

# Pattern to detect control characters (except tab, newline for valid paths)
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _contains_junk(value: str) -> bool:
    """
    Check if string contains 'junk' characters.

    Junk includes:
    - Control characters (0x00-0x1F except tab/newline)
    - DEL character (0x7F)
    - Invalid UTF-8 sequences
    - Unassigned Unicode characters
    - Bidirectional override characters
    - Zero-width characters (potential spoofing)
    """
    # Check for control characters
    if CONTROL_CHAR_PATTERN.search(value):
        return True

    # Check for null bytes
    if NULL_BYTE_PATTERN.search(value):
        return True

    # Check each character for validity
    for char in value:
        category = unicodedata.category(char)

        # Block control characters (Cc) except common whitespace
        if category == "Cc" and char not in "\t\n\r":
            return True

        # Block unassigned characters (Cn)
        if category == "Cn":
            return True

        # Block surrogate characters (Cs)
        if category == "Cs":
            return True

        # Block bidirectional override characters
        if char in "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069":
            return True

        # Block zero-width characters (potential spoofing attacks)
        if char in "\u200b\u200c\u200d\ufeff\u2060\u180e":
            return True

    return False


def validate_filepath(value: Any) -> None:
    r"""
    Validate filepath to prevent path traversal attacks.

    Security checks:
    - Block path traversal sequences (../, ..\, etc.)
    - Block absolute paths
    - Block null bytes and control characters
    - Block URL-encoded traversal attempts
    - Block junk/unprintable characters
    - Block bidirectional override characters

    Raises:
        ValidationError: If filepath contains dangerous patterns.
    """
    if value is None:
        return

    if not isinstance(value, str):
        raise ValidationError(
            _("filepath must be a string"),
            code="filepath_invalid_type",
        )

    # Empty string is allowed (represents no filepath)
    if not value:
        return

    # Check for junk characters
    if _contains_junk(value):
        raise ValidationError(
            _("filepath contains invalid characters"),
            code="filepath_invalid_chars",
        )

    # Check for null bytes
    if NULL_BYTE_PATTERN.search(value):
        raise ValidationError(
            _("filepath contains invalid characters"),
            code="filepath_null_byte",
        )

    # Normalize backslashes to forward slashes for consistent checking
    normalized = value.replace("\\", "/")

    # Check for absolute paths
    if ABSOLUTE_PATH_PATTERN.match(normalized):
        raise ValidationError(
            _("absolute paths are not allowed in filepath"),
            code="filepath_absolute",
        )

    # Check for path traversal patterns
    if PATH_TRAVERSAL_PATTERN.search(normalized):
        raise ValidationError(
            _("path traversal patterns are not allowed in filepath"),
            code="filepath_traversal",
        )

    # Additional check: ensure no component is '..' after normalization
    parts = normalized.split("/")
    for part in parts:
        if part == ".." or part.startswith(".."):
            raise ValidationError(
                _("path traversal patterns are not allowed in filepath"),
                code="filepath_traversal",
            )


def validate_filepath_resolves_within_storage(filepath: str) -> bool:
    """
    Validate that filepath resolves within storage directory using pathlib.

    This function:
    1. Joins storage path with filepath using pathlib
    2. Resolves to absolute path (removing symlinks, .., .)
    3. Checks if resolved path starts with storage root

    Args:
        filepath: The relative filepath to validate

    Returns:
        bool: True if path resolves within storage, False otherwise
    """
    if not filepath:
        return True  # Empty filepath is valid (no file)

    try:
        storage_root = Path(settings.CONFIG.storage.path).resolve()

        # Join and resolve the full path
        full_path = (storage_root / filepath).resolve()

        # Convert to string for comparison
        full_path_str = str(full_path)
        storage_root_str = str(storage_root)

        # Ensure path starts with storage root
        # Add trailing slash to prevent partial match (e.g., /storage vs /storage2)
        if (
            not full_path_str.startswith(storage_root_str + "/")
            and full_path_str != storage_root_str
        ):
            return False

        return True

    except (OSError, ValueError):
        # If resolve fails, consider it unsafe
        return False
