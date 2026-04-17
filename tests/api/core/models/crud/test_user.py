from rest_framework.test import APITestCase
from sdk.faker import faker

from api.core.models import Role, User
from api.permission_constants import GROUPS


class TestUserManager(APITestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            role=Role.HOST,
            username=faker.user_name(),
            password=faker.password(),
            email=faker.fake_email(),
            first_name=faker.first_name(),
            last_name=faker.last_name(),
        )
        db_user = User.objects.get(pk=user.pk)
        self.assertEqual(db_user.username, user.username)

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            username=faker.user_name(),
            password=faker.password(),
            email=faker.fake_email(),
            first_name=faker.first_name(),
            last_name=faker.last_name(),
        )
        db_user = User.objects.get(pk=user.pk)
        self.assertEqual(db_user.username, user.username)
        self.assertEqual(db_user.role, Role.ADMIN)


class TestUser(APITestCase):
    def test_guest_get_group_perms(self):
        user = User.objects.create_user(
            role=Role.GUEST,
            username=faker.user_name(),
            password=faker.password(),
            email=faker.fake_email(),
            first_name=faker.first_name(),
            last_name=faker.last_name(),
        )

        permissions = user.get_group_permissions()
        # APIRoot permission hardcoded in the check as it isn't a Permission object
        str_perms = [p.codename for p in permissions] + ["view_apiroot"]
        self.assertCountEqual(str_perms, GROUPS[Role.GUEST.value])
