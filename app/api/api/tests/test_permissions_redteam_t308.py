"""
RED TEAM: T308 - IsAdminOrOwnUser permission security tests.

Attack vectors:
- Type confusion on user objects
- Attribute injection/manipulation
- Boundary condition bypasses
- Object comparison exploitation
"""

from unittest.mock import MagicMock

import pytest

from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory

from api.permissions import IsAdminOrOwnUser


class TestIsAdminOrOwnUserTypeConfusion:
    """Type confusion attacks on permission check."""

    def test_user_without_is_authenticated_attribute(self):
        """User object missing is_authenticated attribute - raises AttributeError."""
        request = APIRequestFactory().get("/api/v2/users")
        # Object without is_authenticated
        request.user = object()

        # This raises AttributeError - permission class assumes User-like object
        with pytest.raises(AttributeError):
            IsAdminOrOwnUser().has_permission(request, None)

    def test_user_with_none_is_authenticated(self):
        """User with is_authenticated=None - treated as falsy."""
        request = APIRequestFactory().get("/api/v2/users")
        user = MagicMock()
        user.is_authenticated = None
        request.user = user

        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is False

    def test_user_is_authenticated_not_bool(self):
        """is_authenticated as string 'True' - truthy but not boolean."""
        request = APIRequestFactory().get("/api/v2/users")
        user = MagicMock()
        user.is_authenticated = "True"  # Truthy string
        user.is_superuser.return_value = True
        request.user = user

        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is True  # String is truthy

    def test_user_is_authenticated_zero(self):
        """is_authenticated=0 - falsy."""
        request = APIRequestFactory().get("/api/v2/users")
        user = MagicMock()
        user.is_authenticated = 0
        request.user = user

        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is False

    def test_user_is_authenticated_empty_list(self):
        """is_authenticated=[] - falsy."""
        request = APIRequestFactory().get("/api/v2/users")
        user = MagicMock()
        user.is_authenticated = []
        request.user = user

        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is False


class TestIsAdminOrOwnUserAttributeManipulation:
    """Attribute manipulation attacks."""

    def test_is_superuser_as_property_not_method(self):
        """is_superuser as property (not callable) - should crash or fail."""
        request = APIRequestFactory().get("/api/v2/users")
        user = MagicMock()
        user.is_authenticated = True
        # Make is_superuser a property (bool), not method
        user.is_superuser = True  # Not callable!
        request.user = user

        # This will raise TypeError: 'bool' object is not callable
        # This is the original T308 bug scenario
        with pytest.raises(TypeError):
            IsAdminOrOwnUser().has_permission(request, None)

    def test_is_superuser_returns_string_true(self):
        """is_superuser() returns 'True' string - bool() converts to True."""
        request = APIRequestFactory().get("/api/v2/users")
        user = MagicMock()
        user.is_authenticated = True
        user.is_superuser.return_value = "True"  # String
        request.user = user

        result = IsAdminOrOwnUser().has_permission(request, None)
        # bool("True") is True
        assert result is True

    def test_is_superuser_returns_non_empty_string(self):
        """is_superuser() returns any non-empty string - truthy."""
        request = APIRequestFactory().get("/api/v2/users")
        user = MagicMock()
        user.is_authenticated = True
        user.is_superuser.return_value = "admin"
        request.user = user

        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is True

    def test_is_superuser_returns_empty_string(self):
        """is_superuser() returns '' - falsy."""
        request = APIRequestFactory().get("/api/v2/users")
        user = MagicMock()
        user.is_authenticated = True
        user.is_superuser.return_value = ""
        request.user = user

        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is False

    def test_is_superuser_returns_one(self):
        """is_superuser() returns 1 - truthy."""
        request = APIRequestFactory().get("/api/v2/users")
        user = MagicMock()
        user.is_authenticated = True
        user.is_superuser.return_value = 1
        request.user = user

        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is True

    def test_is_superuser_returns_list(self):
        """is_superuser() returns non-empty list - truthy."""
        request = APIRequestFactory().get("/api/v2/users")
        user = MagicMock()
        user.is_authenticated = True
        user.is_superuser.return_value = ["admin"]
        request.user = user

        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is True

    def test_is_superuser_raises_exception(self):
        """is_superuser() raises exception - should propagate."""
        request = APIRequestFactory().get("/api/v2/users")
        user = MagicMock()
        user.is_authenticated = True
        user.is_superuser.side_effect = Exception("Permission check failed")
        request.user = user

        with pytest.raises(Exception, match="Permission check failed"):
            IsAdminOrOwnUser().has_permission(request, None)


class TestIsAdminOrOwnUserObjectPermissionBypass:
    """Object permission bypass attempts."""

    def test_object_without_username_attribute(self):
        """Object without username attribute - AttributeError."""
        request = APIRequestFactory().get("/api/v2/users/1")
        user = MagicMock()
        user.is_authenticated = True
        user.is_superuser.return_value = False
        request.user = user

        obj = object()  # No username attribute

        with pytest.raises(AttributeError):
            IsAdminOrOwnUser().has_object_permission(request, None, obj)

    def test_object_username_none(self):
        """obj.username=None compared to user - None == anything is False."""
        request = APIRequestFactory().get("/api/v2/users/1")
        user = MagicMock()
        user.is_authenticated = True
        user.is_superuser.return_value = False
        request.user = user

        obj = MagicMock()
        obj.username = None

        result = IsAdminOrOwnUser().has_object_permission(request, None, obj)
        assert result is False

    def test_object_username_matches_user_object(self):
        """obj.username is same object as request.user - reference equality."""
        request = APIRequestFactory().get("/api/v2/users/1")
        user = MagicMock()
        user.is_authenticated = True
        user.is_superuser.return_value = False
        request.user = user

        obj = MagicMock()
        obj.username = user  # Same object

        result = IsAdminOrOwnUser().has_object_permission(request, None, obj)
        assert result is True

    def test_object_username_equals_by_value(self):
        """obj.username equals request.user by value but different objects."""
        request = APIRequestFactory().get("/api/v2/users/1")

        class FakeUser:
            is_authenticated = True

            def is_superuser(self):
                return False

            def __eq__(self, other):
                return True  # Always equal!

        request.user = FakeUser()

        obj = MagicMock()
        obj.username = FakeUser()

        # Both should be equal due to __eq__
        result = IsAdminOrOwnUser().has_object_permission(request, None, obj)
        assert result is True

    def test_request_user_is_none(self):
        """request.user=None - AttributeError on is_authenticated."""
        request = APIRequestFactory().get("/api/v2/users")
        request.user = None

        with pytest.raises(AttributeError):
            IsAdminOrOwnUser().has_permission(request, None)


class TestIsAdminOrOwnUserEdgeCases:
    """Edge cases and boundary conditions."""

    def test_anonymous_user_with_mocked_is_superuser(self):
        """AnonymousUser with patched is_superuser - should still fail."""
        request = APIRequestFactory().get("/api/v2/users")
        request.user = AnonymousUser()

        # Even if we somehow patch is_superuser, is_authenticated is False
        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is False

    def test_user_with_is_authenticated_as_callable(self):
        """is_authenticated as callable property."""
        request = APIRequestFactory().get("/api/v2/users")

        class CallableBool:
            def __bool__(self):
                return True

        user = MagicMock()
        user.is_authenticated = CallableBool()
        user.is_superuser.return_value = True
        request.user = user

        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is True

    def test_permission_with_none_request(self):
        """None request object - should crash."""
        with pytest.raises(AttributeError):
            IsAdminOrOwnUser().has_permission(None, None)

    def test_permission_with_request_without_user(self):
        """Request without user attribute - raises AttributeError."""
        request = APIRequestFactory().get("/api/v2/users")

        # Create request-like object without user
        class NoUserRequest:
            pass

        no_user_req = NoUserRequest()

        with pytest.raises(AttributeError):
            IsAdminOrOwnUser().has_permission(no_user_req, None)


class TestIsAdminOrOwnUserComparisonAttacks:
    """Attacks exploiting object comparison."""

    def test_obj_username_not_equals_but_eq_overridden(self):
        """obj.username with overridden __eq__ that always returns True."""
        request = APIRequestFactory().get("/api/v2/users/1")

        class AlwaysEqual:
            is_authenticated = True

            def is_superuser(self):
                return False

            def __eq__(self, other):
                return True

            def __str__(self):
                return "different_user"

        request.user = AlwaysEqual()

        obj = MagicMock()
        obj.username = AlwaysEqual()

        result = IsAdminOrOwnUser().has_object_permission(request, None, obj)
        # Both are AlwaysEqual, so they are equal
        assert result is True

    def test_obj_username_never_equal(self):
        """obj.username with __eq__ that always returns False."""
        request = APIRequestFactory().get("/api/v2/users/1")

        class NeverEqual:
            is_authenticated = True

            def is_superuser(self):
                return False

            def __eq__(self, other):
                return False

        request.user = NeverEqual()

        obj = MagicMock()
        obj.username = NeverEqual()

        result = IsAdminOrOwnUser().has_object_permission(request, None, obj)
        assert result is False

    def test_obj_username_type_mismatch(self):
        """obj.username is string, request.user is int-like object - different types."""
        request = APIRequestFactory().get("/api/v2/users/1")

        class IntLikeUser:
            is_authenticated = True

            def is_superuser(self):
                return False

            def __eq__(self, other):
                return False  # Never equal to anything

        request.user = IntLikeUser()

        obj = MagicMock()
        obj.username = "123"  # String

        # Different types, not equal
        result = IsAdminOrOwnUser().has_object_permission(request, None, obj)
        assert result is False


class TestIsAdminOrOwnUserPrototypePollution:
    """Prototype pollution style attacks."""

    def test_user_class_monkey_patch(self):
        """Monkey-patching user class attributes - demonstrates mutability risk."""
        request = APIRequestFactory().get("/api/v2/users")

        user = MagicMock()
        user.is_authenticated = True
        user.is_superuser.return_value = False

        # Simulate prototype pollution by adding attribute
        user.__class__.polluted_attr = True
        request.user = user

        result = IsAdminOrOwnUser().has_permission(request, None)
        assert result is False

        # Cleanup
        delattr(user.__class__, "polluted_attr")

    def test_object_dunder_method_override(self):
        """Override __getattribute__ to always return True-like values."""
        request = APIRequestFactory().get("/api/v2/users")

        class EvilUser:
            def __getattribute__(self, name):
                if name == "is_authenticated":
                    return True
                if name == "is_superuser":
                    return lambda: True
                return super().__getattribute__(name)

        request.user = EvilUser()

        result = IsAdminOrOwnUser().has_permission(request, None)
        # EvilUser returns True for both checks
        assert result is True
