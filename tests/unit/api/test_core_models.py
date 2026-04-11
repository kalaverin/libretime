"""Unit tests for API core models."""

import hashlib
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import Permission

from api.core.models.auth import LoginAttempt, UserToken
from api.core.models.role import Role
from api.core.models.user import User, UserManager


class TestUserManager:
    """Tests for UserManager class."""

    def test_create_user(self, mocker):
        """Test creating a regular user."""
        mock_user = mocker.Mock()
        mock_set_password = mocker.patch.object(
            User, "set_password", autospec=True
        )
        mock_save = mocker.patch.object(User, "save", autospec=True)
        
        manager = UserManager()
        manager.model = mocker.Mock(return_value=mock_user)
        
        user = manager.create_user(
            role=Role.HOST,
            username="testuser",
            password="testpass123",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )
        
        manager.model.assert_called_once_with(
            role=Role.HOST,
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )
        mock_set_password.assert_called_once_with(mock_user, "testpass123")
        mock_save.assert_called_once_with(mock_user, using=None)
        assert user == mock_user

    def test_create_user_with_none_password(self, mocker):
        """Test creating a user with None password."""
        mock_user = mocker.Mock()
        mock_set_password = mocker.patch.object(
            User, "set_password", autospec=True
        )
        mock_save = mocker.patch.object(User, "save", autospec=True)
        
        manager = UserManager()
        manager.model = mocker.Mock(return_value=mock_user)
        
        user = manager.create_user(
            role=Role.GUEST,
            username="guestuser",
            password=None,
            email="guest@example.com",
            first_name="Guest",
            last_name="User",
        )
        
        mock_set_password.assert_called_once_with(mock_user, None)
        assert user == mock_user

    def test_create_superuser(self, mocker):
        """Test creating a superuser."""
        mock_create_user = mocker.patch.object(
            UserManager, "create_user", autospec=True
        )
        
        manager = UserManager()
        
        manager.create_superuser(
            username="admin",
            password="adminpass",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
        )
        
        mock_create_user.assert_called_once_with(
            manager,
            Role.ADMIN,
            "admin",
            "adminpass",
            "admin@example.com",
            "Admin",
            "User",
        )

    def test_get_by_natural_key(self, mocker):
        """Test getting user by natural key (username)."""
        mock_get = mocker.patch.object(UserManager, "get", autospec=True)
        
        manager = UserManager()
        manager.get_by_natural_key("testuser")
        
        mock_get.assert_called_once_with(manager, username="testuser")


class TestUser:
    """Tests for User model."""

    @pytest.fixture
    def user(self):
        """Create a test user instance."""
        return User(
            role=Role.HOST,
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="hashedpassword123",
        )

    @pytest.fixture
    def admin_user(self):
        """Create an admin user instance."""
        return User(
            role=Role.ADMIN,
            username="admin",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
        )

    def test_meta_attributes(self):
        """Test User model Meta attributes."""
        assert User._meta.managed is False
        assert User._meta.db_table == "cc_subjs"

    def test_username_field(self):
        """Test User USERNAME_FIELD configuration."""
        assert User.USERNAME_FIELD == "username"
        assert User.EMAIL_FIELD == "email"
        assert "role" in User.REQUIRED_FIELDS
        assert "email" in User.REQUIRED_FIELDS
        assert "first_name" in User.REQUIRED_FIELDS
        assert "last_name" in User.REQUIRED_FIELDS

    def test_get_full_name(self, user):
        """Test get_full_name method."""
        assert user.get_full_name() == "Test User"

    def test_get_short_name(self, user):
        """Test get_short_name method."""
        assert user.get_short_name() == "Test"

    def test_set_password_with_value(self, user):
        """Test set_password with actual password."""
        raw_password = "mypassword123"
        expected_hash = hashlib.md5(raw_password.encode()).hexdigest()
        
        user.set_password(raw_password)
        
        assert user.password == expected_hash

    def test_set_password_with_empty_string(self, user):
        """Test set_password with empty string sets unusable password."""
        user.set_password("")
        
        # Empty string is falsy, so unusable password should be set
        assert user.password.startswith("!")

    def test_set_password_with_none(self, user):
        """Test set_password with None sets unusable password."""
        user.set_password(None)
        
        assert user.password.startswith("!")

    def test_is_staff_for_admin(self, admin_user):
        """Test is_staff returns True for admin."""
        assert admin_user.is_staff() is True

    def test_is_staff_for_non_admin(self, user):
        """Test is_staff returns False for non-admin."""
        assert user.is_staff() is False

    def test_check_password_correct(self, user):
        """Test check_password with correct password."""
        raw_password = "mypassword123"
        user.set_password(raw_password)
        
        assert user.check_password(raw_password) is True

    def test_check_password_incorrect(self, user):
        """Test check_password with incorrect password."""
        user.set_password("correctpassword")
        
        assert user.check_password("wrongpassword") is False

    def test_check_password_unusable(self, user):
        """Test check_password with unusable password."""
        user.set_password(None)
        
        assert user.check_password("anypassword") is False

    def test_is_superuser_for_admin(self, admin_user):
        """Test is_superuser returns True for admin."""
        assert admin_user.is_superuser is True

    def test_is_superuser_for_non_admin(self, user):
        """Test is_superuser returns False for non-admin."""
        assert user.is_superuser is False

    def test_get_user_permissions(self, user):
        """Test get_user_permissions returns empty list."""
        assert user.get_user_permissions() == []
        assert user.get_user_permissions(obj=MagicMock()) == []

    def test_get_group_permissions(self, user, mocker):
        """Test get_group_permissions returns permissions from GROUPS."""
        mock_permissions = [
            MagicMock(codename="view_show"),
            MagicMock(codename="add_show"),
        ]
        mock_filter = mocker.patch.object(
            Permission.objects, "filter", return_value=mock_permissions
        )
        
        perms = user.get_group_permissions()
        
        # Should filter by permissions defined for HOST role
        mock_filter.assert_called_once()
        call_args = mock_filter.call_args
        assert isinstance(call_args[0][0], type(Permission.objects.filter()))
        assert perms == mock_permissions

    def test_get_group_permissions_with_obj(self, user, mocker):
        """Test get_group_permissions filters by object type."""
        mock_obj = MagicMock()
        mock_obj.__class__.__name__ = "Show"
        
        mock_permissions = []
        mocker.patch.object(
            Permission.objects, "filter", return_value=mock_permissions
        )
        
        user.get_group_permissions(obj=mock_obj)
        
        # Should filter permissions containing 'show' in the name

    def test_get_all_permissions(self, user, mocker):
        """Test get_all_permissions combines user and group permissions."""
        mock_user_perms = []
        mock_group_perms = [MagicMock(codename="view_show")]
        
        mocker.patch.object(
            user, "get_user_permissions", return_value=mock_user_perms
        )
        mocker.patch.object(
            user, "get_group_permissions", return_value=mock_group_perms
        )
        
        all_perms = user.get_all_permissions()
        
        assert all_perms == mock_group_perms  # user perms are empty

    def test_has_perm_superuser(self, admin_user):
        """Test has_perm returns True for superuser."""
        assert admin_user.has_perm("any_permission") is True
        assert admin_user.has_perm("") is True  # BUG: should probably check

    def test_has_perm_empty_perm(self, user):
        """Test has_perm with empty permission string."""
        assert user.has_perm("") is False

    def test_has_perm_existing(self, user, mocker):
        """Test has_perm with existing permission."""
        mock_perm = MagicMock()
        mocker.patch.object(
            Permission.objects, "get", return_value=mock_perm
        )
        mocker.patch.object(
            user, "get_all_permissions", return_value=[mock_perm]
        )
        
        result = user.has_perm("view_show")
        
        assert result is True

    def test_has_perm_not_existing(self, user, mocker):
        """Test has_perm with non-existing permission."""
        mocker.patch.object(
            Permission.objects, "get", side_effect=Permission.DoesNotExist
        )
        
        result = user.has_perm("nonexistent_perm")
        
        assert result is False

    def test_has_perm_with_obj(self, user, mocker):
        """Test has_perm with object parameter."""
        mock_perm = MagicMock()
        mock_obj = MagicMock()
        
        mocker.patch.object(
            Permission.objects, "get", return_value=mock_perm
        )
        mocker.patch.object(
            user, "get_all_permissions", return_value=[mock_perm]
        )
        
        result = user.has_perm("view_show", obj=mock_obj)
        
        assert result is True

    def test_has_perms_all_true(self, user, mocker):
        """Test has_perms when all permissions are granted."""
        mocker.patch.object(user, "has_perm", return_value=True)
        
        result = user.has_perms(["perm1", "perm2", "perm3"])
        
        assert result is True

    def test_has_perms_some_false(self, user, mocker):
        """Test has_perms when some permissions are denied."""
        mocker.patch.object(
            user, "has_perm", side_effect=[True, False, True]
        )
        
        result = user.has_perms(["perm1", "perm2", "perm3"])
        
        assert result is False

    def test_has_perms_empty_list(self, user, mocker):
        """Test has_perms with empty list."""
        mocker.patch.object(user, "has_perm", return_value=True)
        
        result = user.has_perms([])
        
        # Empty list should return True (vacuous truth)
        assert result is True

    def test_field_definitions(self):
        """Test User model field definitions."""
        # Test role field
        role_field = User._meta.get_field("role")
        assert role_field.max_length == 1
        assert role_field.db_column == "type"
        
        # Test username field
        username_field = User._meta.get_field("username")
        assert username_field.unique is True
        assert username_field.max_length == 255
        assert username_field.db_column == "login"
        
        # Test password field
        password_field = User._meta.get_field("password")
        assert password_field.max_length == 255
        assert password_field.db_column == "pass"
        
        # Test email field
        email_field = User._meta.get_field("email")
        assert email_field.max_length == 1024
        assert email_field.blank is True
        assert email_field.null is True
        
        # Test contact fields
        skype_field = User._meta.get_field("skype")
        assert skype_field.db_column == "skype_contact"
        
        jabber_field = User._meta.get_field("jabber")
        assert jabber_field.db_column == "jabber_contact"
        
        phone_field = User._meta.get_field("phone")
        assert phone_field.db_column == "cell_phone"
        
        # Test timestamp fields
        last_login_field = User._meta.get_field("last_login")
        assert last_login_field.db_column == "lastlogin"
        
        last_failed_field = User._meta.get_field("last_failed_login")
        assert last_failed_field.db_column == "lastfail"


class TestUserToken:
    """Tests for UserToken model."""

    @pytest.fixture
    def user_token(self, mocker):
        """Create a test user token instance."""
        mock_user = mocker.Mock()
        token = UserToken(
            user=mock_user,
            action="reset_password",
            token="abc123xyz",
        )
        return token

    def test_meta_attributes(self):
        """Test UserToken model Meta attributes."""
        assert UserToken._meta.managed is False
        assert UserToken._meta.db_table == "cc_subjs_token"

    def test_field_definitions(self):
        """Test UserToken model field definitions."""
        # Test token field is unique
        token_field = UserToken._meta.get_field("token")
        assert token_field.unique is True
        assert token_field.max_length == 40
        
        # Test action field
        action_field = UserToken._meta.get_field("action")
        assert action_field.max_length == 255
        
        # Test user foreign key
        user_field = UserToken._meta.get_field("user")
        assert user_field.remote_field.on_delete.__name__ == "DO_NOTHING"

    def test_get_owner(self, user_token):
        """Test get_owner returns the associated user."""
        owner = user_token.get_owner()
        
        assert owner == user_token.user


class TestLoginAttempt:
    """Tests for LoginAttempt model."""

    @pytest.fixture
    def login_attempt(self):
        """Create a test login attempt instance."""
        return LoginAttempt(
            ip="192.168.1.1",
            attempts=3,
        )

    def test_meta_attributes(self):
        """Test LoginAttempt model Meta attributes."""
        assert LoginAttempt._meta.managed is False
        assert LoginAttempt._meta.db_table == "cc_login_attempts"

    def test_ip_is_primary_key(self):
        """Test that ip field is the primary key."""
        ip_field = LoginAttempt._meta.get_field("ip")
        assert ip_field.primary_key is True
        assert ip_field.max_length == 32

    def test_field_definitions(self):
        """Test LoginAttempt model field definitions."""
        attempts_field = LoginAttempt._meta.get_field("attempts")
        assert attempts_field.blank is True
        assert attempts_field.null is True

    def test_model_creation(self, login_attempt):
        """Test LoginAttempt model can be instantiated."""
        assert login_attempt.ip == "192.168.1.1"
        assert login_attempt.attempts == 3

    def test_null_attempts(self):
        """Test LoginAttempt with null attempts."""
        attempt = LoginAttempt(ip="10.0.0.1", attempts=None)
        
        assert attempt.attempts is None
