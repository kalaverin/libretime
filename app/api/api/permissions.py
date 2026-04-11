from collections.abc import Sequence
from contextlib import suppress
from secrets import compare_digest
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from typing_extensions import override

from api.core.models import Role, User
from api.schedule.models import Show

if TYPE_CHECKING:
    from rest_framework.views import APIView

REQUEST_PERMISSION_TYPE_MAP = {
    "GET": "view",
    "HEAD": "view",
    "OPTIONS": "view",
    "POST": "add",
    "PUT": "change",
    "DELETE": "delete",
    "PATCH": "change",
}


PermissionsType = Sequence[type[BasePermission]]


class SafeSessionAuthentication(authentication.SessionAuthentication):
    """
    SessionAuthentication that safely handles malformed headers.

    Fixes:
    - T376, T793: UnicodeEncodeError on non-ASCII Authorization header
    """

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except UnicodeEncodeError:
            # Reject requests with non-ASCII characters in Authorization header
            return None


class SafeBasicAuthentication(authentication.BasicAuthentication):
    """
    BasicAuthentication that safely handles malformed headers.

    Fixes:
    - T376, T793: UnicodeEncodeError on non-ASCII Authorization header
    """

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except UnicodeEncodeError:
            # Reject requests with non-ASCII characters in Authorization header
            return None


def get_own_obj(request: Request, view: "APIView") -> str:
    """
    Determine if HOST user should use 'own_' permission prefix.

    For HOST role with modify operations (PUT/PATCH/DELETE) on existing
    objects, use 'own_' prefix. Object-level ownership check happens in
    has_object_permission().

    Note: POST (create) uses regular permission without 'own_' prefix,
    because the creator automatically becomes the owner.
    """
    user = request.user
    if user is None or user.role != Role.HOST:
        return ""

    # POST (create) doesn't use own_* - creator becomes owner automatically
    # GET/HEAD/OPTIONS are view operations
    if request.method in ("GET", "HEAD", "OPTIONS", "POST"):
        return ""

    # HOST gets own_* prefix for update/delete operations
    return "own_"


def get_permission_for_view(
    request: Request,
    view: "APIView",
) -> str | None:

    with suppress(AttributeError):
        permission_type = REQUEST_PERMISSION_TYPE_MAP[request.method]
        if view.__class__.__name__ == "APIRootView":
            return f"{permission_type}_apiroot"

        model = view.model_permission_name
        own_obj = get_own_obj(request, view)
        return f"{permission_type}_{own_obj}{model}"

    return None


def check_authorization_header(request: Request) -> bool:
    """
    Validate API-Key authorization header.

    Security considerations:
    - Strict case-sensitivity: only "Api-Key" prefix accepted (T459, T753)
    - Whitespace handling: single space required after prefix
    - Injection protection: rejects newlines, CR, null bytes (T912, T913)
    - Unicode handling: rejects non-ASCII characters (T376, T749, T793)
    - Empty token: properly rejected without crash (T460, T341)
    """
    try:
        auth_header = request.headers.get("authorization", "")
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Handle unicode encoding errors in header (T376, T793)
        return False

    # Handle None or non-string values
    if not isinstance(auth_header, str):
        return False

    # Reject headers with non-ASCII characters (T376, T749, T793)
    # This prevents UnicodeEncodeError in subsequent processing
    try:
        auth_header.encode('ascii')
    except UnicodeEncodeError:
        return False

    # Reject headers with control characters (injection protection: T912, T913)
    # This includes newlines (\n, \r), null bytes (\x00), and other control chars
    if any(ord(c) < 32 for c in auth_header):
        return False

    # Strict case-sensitive prefix check (T459, T753)
    # Only exact "Api-Key" prefix is accepted - not "api-key", "API-KEY", etc.
    if not auth_header.startswith("Api-Key"):
        return False

    # Extract the remainder after "Api-Key"
    remainder = auth_header[7:]  # len("Api-Key") == 7

    # Must start with a single space (T460 - strict format)
    if not remainder.startswith(" "):
        return False

    # Extract token (strip only the single required space, not all whitespace)
    token = remainder[1:]

    # Reject empty token (T460, T341)
    if not token:
        return False

    # Reject tokens with leading/trailing whitespace (T460 variants)
    if token != token.strip():
        return False

    # Reject tokens containing whitespace (multiple tokens, injection attempts)
    if any(c.isspace() for c in token):
        return False

    # Reject non-ASCII tokens (T376, T749)
    try:
        token.encode('ascii')
    except UnicodeEncodeError:
        return False

    # Constant-time comparison to prevent timing attacks
    expected_key = settings.CONFIG.general.api_key
    if not isinstance(expected_key, str):
        expected_key = str(expected_key)

    return compare_digest(token, expected_key)


def is_authenticated(user: AnonymousUser | User) -> bool:
    """Check if user is authenticated (not anonymous)."""

    return (
        isinstance(user, User)
        and not user.is_anonymous
        and user.is_authenticated
    )


def is_superuser(user: AnonymousUser | User) -> bool:
    """Check if user is authenticated and has admin or manager role."""

    return (
        isinstance(user, User) and
        user.is_authenticated and
        (
            user.is_superuser
            or user.role in (Role.ADMIN, Role.MANAGER)
        )
    )


def request_superauthorized(request: Request) -> bool:
    """Check if request is from a superuser (admin/manager) or has valid API-Key."""

    return (
        is_superuser(request.user) or
        check_authorization_header(request)
    )


class IsAdminOrOwnUser(BasePermission):
    """
    Implements Django Rest Framework permissions. This is separate from
    Django's standard permission system. For details see
    https://www.django-rest-framework.org/api-guide/permissions/#custom-permissions
    """

    @override
    def has_permission(self, request: Request, view: Any) -> bool:
        if not request.user.is_authenticated:
            return False
        return is_superuser(request.user)

    @override
    def has_object_permission(
        self,
        request: Request,
        view: "APIView",
        obj: Any,
    ) -> bool:
        user = request.user
        return user.is_authenticated and (
            is_superuser(user) or
            obj.username == user
        )


class IsSystemTokenOrUser(BasePermission):
    """
    Implements Django Rest Framework permissions. This is separate from
    Django's standard permission system. For details see
    https://www.django-rest-framework.org/api-guide/permissions/#custom-permissions

    This permission allows services (liquidsoap, 3rd-party, etc) to connect with
    an API-Key header. All standard-users (i.e. not using the API-Key) have their
    permissions checked against Django's standard permission system.
    """

    @override
    def has_permission(self, request: Request, view: Any) -> bool:
        # API-Key auth (services) - bypass Django permissions
        if check_authorization_header(request):
            return True

        # Anonymous users without API-Key get 403
        if not request.user or not request.user.is_authenticated:
            return False

        # Authenticated users check Django permissions
        perm = get_permission_for_view(request, view)
        # Required as view_apiroot is a permission not linked to a specific
        # model. This use-case allows users to view the base of the API
        # explorer. Their assigned group permissions determine further access
        # into the explorer.

        if perm == "view_apiroot":
            return True

        # Special handling for Show: allow HOST to reach has_object_permission
        # where we check if they are assigned as host (Show uses hosts, not owner)
        if (
            perm and "own_show" in perm and
            request.user.role == Role.HOST
        ):
            return True

        return request.user.has_perm(perm)

    @override
    def has_object_permission(
        self,
        request: Request,
        view: "APIView",
        obj: Any,
    ) -> bool:
        # API-Key auth bypasses all checks
        if check_authorization_header(request):
            return True

        if request.user and request.user.is_authenticated:
            perm = get_permission_for_view(request, view)

            # For own_* permissions, check object ownership
            if perm and "own_" in perm:
                # Superuser can modify any object
                if is_superuser(request.user):
                    return True
                # Special handling for Show (uses hosts instead of owner)
                if isinstance(obj, Show):
                    return obj.hosts.filter(id=request.user.id).exists()
                # Check ownership
                if hasattr(obj, 'owner'):
                    return obj.owner == request.user
                elif hasattr(obj, 'get_owner'):
                    return obj.get_owner() == request.user
                # No ownership info - deny
                return False

            # Special handling for Show (uses hosts instead of owner)
            if perm in ("change_show", "delete_show"):
                if isinstance(obj, Show):
                    # Superuser or manager can modify any show
                    if is_superuser(request.user):
                        return True
                    from api.core.models.role import Role
                    if request.user.role == Role.MANAGER:
                        return True
                    # Host can modify if they are assigned to the show
                    if obj.hosts.filter(id=request.user.id).exists():
                        return True
                    return False

            # Regular permission check
            if perm:
                return request.user.has_perm(perm)
            return True

        return False
