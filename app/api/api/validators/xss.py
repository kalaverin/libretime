"""
XSS protection validators.

Sanitizes user input to prevent stored XSS attacks.
"""

import re

from typing import Any

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Dangerous HTML tags that should never be allowed
DANGEROUS_TAGS = frozenset(
    [
        "script",
        "iframe",
        "object",
        "embed",
        "form",
        "input",
        "textarea",
        "button",
        "link",
        "style",
        "meta",
        "base",
        "head",
        "body",
        "html",
        "title",
        "noscript",
        "template",
        "slot",
        "frame",
        "frameset",
        "applet",
        "marquee",
    ],
)

# JavaScript event handlers
JS_EVENT_HANDLERS = frozenset(
    [
        "onabort",
        "onactivate",
        "onafterprint",
        "onafterscriptexecute",
        "onafterupdate",
        "onanimationcancel",
        "onanimationend",
        "onanimationiteration",
        "onanimationstart",
        "onariarequest",
        "onautocomplete",
        "onautocompleteerror",
        "onbeforeactivate",
        "onbeforecopy",
        "onbeforecut",
        "onbeforedeactivate",
        "onbeforeeditfocus",
        "onbeforepaste",
        "onbeforeprint",
        "onbeforescriptexecute",
        "onbeforeunload",
        "onbeforeupdate",
        "onbegin",
        "onblur",
        "onbounce",
        "oncanplay",
        "oncanplaythrough",
        "oncellchange",
        "onchange",
        "onclick",
        "onclose",
        "oncontextmenu",
        "oncontrolselect",
        "oncopy",
        "oncuechange",
        "oncut",
        "ondblclick",
        "ondeactivate",
        "ondrag",
        "ondragdrop",
        "ondragend",
        "ondragenter",
        "ondragleave",
        "ondragover",
        "ondragstart",
        "ondrop",
        "ondurationchange",
        "onemptied",
        "onend",
        "onended",
        "onerror",
        "onerrorupdate",
        "onfilterchange",
        "onfinish",
        "onfocus",
        "onfocusin",
        "onfocusout",
        "onformchange",
        "onforminput",
        "onfullscreenchange",
        "onfullscreenerror",
        "ongesturechange",
        "ongesturedoubletap",
        "ongestureend",
        "ongesturestart",
        "ongotpointercapture",
        "onhashchange",
        "onhelp",
        "oninput",
        "oninvalid",
        "onkeydown",
        "onkeypress",
        "onkeyup",
        "onlanguagechange",
        "onlayoutcomplete",
        "onload",
        "onloadeddata",
        "onloadedmetadata",
        "onloadend",
        "onloadstart",
        "onlosecapture",
        "onlostpointercapture",
        "onmessage",
        "onmousedown",
        "onmouseenter",
        "onmouseleave",
        "onmousemove",
        "onmouseout",
        "onmouseover",
        "onmouseup",
        "onmousewheel",
        "onmove",
        "onmoveend",
        "onmovestart",
        "onmozfullscreenchange",
        "onmozfullscreenerror",
        "onmozpointerlockchange",
        "onmozpointerlockerror",
        "onmscontentzoom",
        "onmsfullscreenchange",
        "onmsfullscreenerror",
        "onmsgesturechange",
        "onmsgesturedoubletap",
        "onmsgestureend",
        "onmsgesturehold",
        "onmsgesturestart",
        "onmsgesturetap",
        "onmsgotpointercapture",
        "onmsinertiastart",
        "onmslostpointercapture",
        "onmsmanipulationstatechanged",
        "onmspointercancel",
        "onmspointerdown",
        "onmspointerenter",
        "onmspointerleave",
        "onmspointermove",
        "onmspointerout",
        "onmspointerover",
        "onmspointerup",
        "onmssitemodejumplistitemremoved",
        "onmsthumbnailclick",
        "onoffline",
        "ononline",
        "onoutofsync",
        "onpage",
        "onpagehide",
        "onpageshow",
        "onpaste",
        "onpause",
        "onplay",
        "onplaying",
        "onpointercancel",
        "onpointerdown",
        "onpointerenter",
        "onpointerleave",
        "onpointerlockchange",
        "onpointerlockerror",
        "onpointermove",
        "onpointerout",
        "onpointerover",
        "onpointerup",
        "onpopstate",
        "onprogress",
        "onpropertychange",
        "onreadystatechange",
        "onreceived",
        "onrepeat",
        "onreset",
        "onresize",
        "onresizeend",
        "onresizestart",
        "onrowenter",
        "onrowexit",
        "onrowsdelete",
        "onrowsinserted",
        "onscroll",
        "onsearch",
        "onseek",
        "onseeked",
        "onseeking",
        "onselect",
        "onselectionchange",
        "onselectstart",
        "onstart",
        "onstop",
        "onstorage",
        "onsubmit",
        "onsuspend",
        "onsynchrestored",
        "ontimeerror",
        "ontimeupdate",
        "ontoggle",
        "ontouchcancel",
        "ontouchend",
        "ontouchforcechange",
        "ontouchmove",
        "ontouchstart",
        "ontransitioncancel",
        "ontransitionend",
        "ontransitionrun",
        "ontransitionstart",
        "onunload",
        "onurlflip",
        "onuserproximity",
        "onvolumechange",
        "onwaiting",
        "onwebkitanimationend",
        "onwebkitanimationiteration",
        "onwebkitanimationstart",
        "onwebkitfullscreenchange",
        "onwebkitfullscreenerror",
        "onwebkitkeyadded",
        "onwebkitkeyerror",
        "onwebkitkeymessage",
        "onwebkitneedkey",
        "onwebkitpointerlockchange",
        "onwebkitpointerlockerror",
        "onwebkittransitionend",
        "onwheel",
    ],
)

# JavaScript protocol
JS_PROTOCOL_PATTERN = re.compile(r"javascript:", re.IGNORECASE)

# Data URI pattern
DATA_URI_PATTERN = re.compile(r"data:text/html", re.IGNORECASE)

# VBScript protocol
VBSCRIPT_PATTERN = re.compile(r"vbscript:", re.IGNORECASE)

# HTML tag pattern
HTML_TAG_PATTERN = re.compile(r"</?[a-zA-Z][^>]*>")

# on* event handler pattern
EVENT_HANDLER_PATTERN = re.compile(
    r"\s*on\w+\s*=[\"']?[^\"']*[\"']?",
    re.IGNORECASE,
)


def _contains_dangerous_html(value: str) -> bool:
    """Check if value contains dangerous HTML tags."""
    # Check for script tags and other dangerous tags
    for tag in DANGEROUS_TAGS:
        # Build pattern that allows spaces between letters (e.g., <scr ipt>)
        # Each letter can be followed by optional whitespace
        spaced_tag = r"\s*".join(re.escape(c) for c in tag)
        # Match opening tag with possible spaces between letters
        if re.search(rf"<\s*{spaced_tag}\b", value, re.IGNORECASE):
            return True
        # Match closing tag
        if re.search(rf"<\s*/\s*{tag}\s*>", value, re.IGNORECASE):
            return True
    return False


def _contains_js_protocol(value: str) -> bool:
    """Check for javascript: protocol."""
    return bool(JS_PROTOCOL_PATTERN.search(value))


def _contains_event_handlers(value: str) -> bool:
    """Check for JavaScript event handlers."""
    return bool(EVENT_HANDLER_PATTERN.search(value))


def _contains_encoded_xss(value: str) -> bool:
    """Check for URL/hex encoded XSS attempts."""
    # Check for common encoding patterns
    encoded_patterns = [
        r"%3C\s*script",  # URL encoded <script
        r"&#x3C;\s*script",  # Hex encoded <script
        r"&#60;\s*script",  # Decimal encoded <script
        r"&lt;\s*script",  # HTML entity encoded <script
        r"%3C\s*img",  # URL encoded <img
        r"<\s*img[^>]+onerror",  # img with onerror
        r"<\s*svg[^>]+onload",  # svg with onload
    ]
    for pattern in encoded_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    return False


def validate_no_xss(value: Any) -> None:
    """
    Validate that value does not contain XSS payloads.

    Blocks:
    - <script> tags
    - JavaScript event handlers (onclick, onerror, etc.)
    - javascript: protocol
    - data:text/html URIs
    - vbscript: protocol
    - Encoded XSS attempts

    Raises:
        ValidationError: If XSS payload detected
    """
    if not isinstance(value, str):
        return

    if not value:
        return

    # Check for dangerous HTML tags
    if _contains_dangerous_html(value):
        raise ValidationError(
            _("Input contains invalid content"),
            code="xss_dangerous_html",
        )

    # Check for JavaScript protocol
    if _contains_js_protocol(value):
        raise ValidationError(
            _("Input contains invalid content"),
            code="xss_js_protocol",
        )

    # Check for event handlers
    if _contains_event_handlers(value):
        raise ValidationError(
            _("Input contains invalid content"),
            code="xss_event_handler",
        )

    # Check for encoded XSS
    if _contains_encoded_xss(value):
        raise ValidationError(
            _("Input contains invalid content"),
            code="xss_encoded",
        )

    # Check for data:text/html
    if DATA_URI_PATTERN.search(value):
        raise ValidationError(
            _("Input contains invalid content"),
            code="xss_data_uri",
        )

    # Check for vbscript
    if VBSCRIPT_PATTERN.search(value):
        raise ValidationError(
            _("Input contains invalid content"),
            code="xss_vbscript",
        )


def sanitize_text(value: str) -> str:
    """
    Sanitize text by removing dangerous content.

    This is a fallback if validation is bypassed.
    """
    if not isinstance(value, str):
        return value

    # Remove script tags
    value = re.sub(
        r"<\s*script[^>]*>.*?</\s*script\s*>",
        "",
        value,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Remove event handlers
    value = re.sub(EVENT_HANDLER_PATTERN, "", value)

    # Remove javascript protocol
    value = JS_PROTOCOL_PATTERN.sub("", value)

    return value
