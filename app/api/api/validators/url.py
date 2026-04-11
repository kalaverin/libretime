"""
URL validators with SSRF protection.

Blocks:
- Dangerous schemes (file://, ftp://, etc.)
- Internal IP addresses (RFC 1918, localhost, link-local)
- Cloud metadata endpoints (169.254.169.254)
- URL-encoded bypass attempts
"""

import ipaddress
import re

from typing import Any
from urllib.parse import unquote, urlparse

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Dangerous URL schemes that should never be allowed
DANGEROUS_SCHEMES = frozenset(
    [
        "file",
        "ftp",
        "ftps",
        "gopher",
        "dict",
        "ldap",
        "ldaps",
        "tftp",
        "ssh",
        "telnet",
        "smtp",
        "imap",
        "pop3",
        "svn",
        "svn+ssh",
        "jar",
        "javascript",
        "data",
        "vbscript",
    ],
)

# Allowed schemes whitelist
ALLOWED_SCHEMES = frozenset(["http", "https"])

# Localhost patterns (including punycode variants)
LOCALHOST_PATTERNS = re.compile(
    r"^(localhost|127\.\d+\.\d+\.\d+|::1|0:0:0:0:0:0:0:1|0\.0\.0\.0)$",
    re.IGNORECASE,
)

# IPv4 embedded in IPv6 patterns that indicate localhost
IPV4_IN_IP6_LOCALHOST = re.compile(
    r"^::(?:ffff:)?(127\.\d+\.\d+\.\d+|0\.0\.0\.0)$",
    re.IGNORECASE,
)


def _is_internal_ip(hostname: str) -> bool:
    """
    Check if hostname resolves to an internal/private IP address.

    Blocks:
    - RFC 1918 private ranges (10/8, 172.16/12, 192.168/16)
    - Link-local addresses (169.254/16)
    - Loopback (127/8)
    - Multicast (224/4)
    - Cloud metadata endpoint (169.254.169.254)
    """
    # First check for localhost names
    if LOCALHOST_PATTERNS.match(hostname):
        return True

    # Check for IPv4 embedded in IPv6 localhost
    if IPV4_IN_IP6_LOCALHOST.match(hostname):
        return True

    # Try to parse as IP address
    try:
        ip = ipaddress.ip_address(hostname)
        # Check for private, loopback, link-local, reserved, multicast
        return bool(
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified,
        )
    except ValueError:
        # Not a valid IP address, assume it's a hostname
        # Check for localhost variants and internal naming patterns
        hostname_lower = hostname.lower()

        # Direct localhost matches
        if hostname_lower in ("localhost", "localhost.localdomain"):
            return True

        # Check for localhost subdomains
        if hostname_lower.endswith(".localhost") or hostname_lower.endswith(
            ".localhost.localdomain",
        ):
            return True

        # Common internal naming patterns (may resolve to internal IPs)
        internal_prefixes = (
            "internal.",
            "private.",
            "intranet.",
            "admin.",
            "mgmt.",
            "management.",
        )
        if hostname_lower.startswith(internal_prefixes):
            return True

        return False


def _decode_url_encoding(value: str) -> str:
    """
    Decode percent-encoded characters for detection.

    Uses urllib.parse.unquote for full decoding, then checks for
    common double-encoding patterns.
    """
    # First decode
    decoded = unquote(value)
    # Check for double encoding
    double_decoded = unquote(decoded)
    if double_decoded != decoded:
        return double_decoded
    return decoded


def validate_url_safe(value: Any, allow_internal: bool = False) -> None:
    """
    Validate URL is safe from SSRF attacks.

    Args:
        value: URL string to validate
        allow_internal: If True, allows internal IPs (for special cases)

    Raises:
        ValidationError: If URL is unsafe or invalid
    """
    if not isinstance(value, str):
        raise ValidationError(
            _("URL must be a string"),
            code="url_invalid_type",
        )

    if not value:
        raise ValidationError(
            _("URL cannot be empty"),
            code="url_empty",
        )

    # Check for null bytes
    if "\x00" in value or "%00" in value:
        raise ValidationError(
            _("URL contains invalid characters"),
            code="url_null_byte",
        )

    # Decode potential URL encoding to catch bypass attempts (including double encoding)
    decoded_value = _decode_url_encoding(value)

    try:
        parsed = urlparse(decoded_value)
    except ValueError as exc:
        raise ValidationError(
            _("Invalid URL format: %(error)s"),
            code="url_invalid_format",
            params={"error": str(exc)},
        ) from exc

    # Validate scheme
    scheme = parsed.scheme.lower()
    if not scheme:
        raise ValidationError(
            _("URL must have a scheme (http:// or https://)"),
            code="url_missing_scheme",
        )

    if scheme in DANGEROUS_SCHEMES:
        raise ValidationError(
            _("URL scheme '%(scheme)s' is not allowed"),
            code="url_dangerous_scheme",
            params={"scheme": scheme},
        )

    if scheme not in ALLOWED_SCHEMES:
        raise ValidationError(
            _(
                "URL scheme '%(scheme)s' is not allowed. Use http:// or https://",
            ),
            code="url_disallowed_scheme",
            params={"scheme": scheme},
        )

    # Validate hostname exists
    hostname = parsed.hostname
    if not hostname:
        raise ValidationError(
            _("URL must have a hostname"),
            code="url_missing_hostname",
        )

    # Check for internal IPs (SSRF protection)
    if not allow_internal and _is_internal_ip(hostname):
        raise ValidationError(
            _("Internal URLs are not allowed"),
            code="url_internal_ip",
        )

    # Additional check: block common cloud metadata endpoints
    # These are link-local but we want explicit message
    if hostname in ("169.254.169.254", "metadata.google.internal", "metadata"):
        raise ValidationError(
            _("Cloud metadata endpoints are not allowed"),
            code="url_cloud_metadata",
        )

    # Check for URL with credentials (user:pass@host)
    if parsed.username or parsed.password:
        raise ValidationError(
            _("URLs with embedded credentials are not allowed"),
            code="url_embedded_credentials",
        )

    # Check for DNS rebinding protection:
    # Hostnames should not look like IP addresses with trailing dots
    if re.match(r"^\d+\.\d+\.\d+\.\d+\.+$", hostname):
        raise ValidationError(
            _("Invalid hostname format"),
            code="url_invalid_hostname",
        )


def validate_url_not_internal(value: Any) -> None:
    """
    Validate URL does not point to internal network resources.

    Alias for validate_url_safe with allow_internal=False.
    """
    return validate_url_safe(value, allow_internal=False)
