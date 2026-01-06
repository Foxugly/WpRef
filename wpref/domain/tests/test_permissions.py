# domain/tests/test_permissions.py

from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APITestCase, APIRequestFactory

from domain.models import Domain
from domain.permissions import IsDomainOwnerOrStaff

User = get_user_model()


class IsDomainOwnerOrStaffTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="owner", password="pass")
        cls.staff_global = User.objects.create_user(
            username="staff_global", password="pass", is_staff=True
        )
        cls.superuser = User.objects.create_user(
            username="admin", password="pass", is_superuser=True
        )
        cls.staff_member = User.objects.create_user(username="staff_member", password="pass")
        cls.other = User.objects.create_user(username="other", password="pass")

        cls.domain = Domain.objects.create(owner=cls.owner, active=True)
        cls.domain.staff.add(cls.staff_member)

    def setUp(self):
        self.factory = APIRequestFactory()
        self.perm = IsDomainOwnerOrStaff()
        self.view = SimpleNamespace()  # view factice (non utilisé ici)

    def _req_with_user(self, user):
        req = self.factory.get("/fake/")
        req.user = user
        return req

    # -------------------------
    # has_object_permission
    # -------------------------
    def test_denies_when_user_missing(self):
        """
        Si request.user est None -> False
        """
        req = self.factory.get("/fake/")
        req.user = None
        self.assertFalse(self.perm.has_object_permission(req, self.view, self.domain))

    def test_denies_when_user_anonymous(self):
        """
        AnonymousUser.is_authenticated == False -> False
        """
        req = self._req_with_user(AnonymousUser())
        self.assertFalse(self.perm.has_object_permission(req, self.view, self.domain))

    def test_allows_superuser(self):
        req = self._req_with_user(self.superuser)
        self.assertTrue(self.perm.has_object_permission(req, self.view, self.domain))

    def test_allows_staff_global(self):
        req = self._req_with_user(self.staff_global)
        self.assertTrue(self.perm.has_object_permission(req, self.view, self.domain))

    def test_allows_domain_owner(self):
        req = self._req_with_user(self.owner)
        self.assertTrue(self.perm.has_object_permission(req, self.view, self.domain))

    def test_allows_domain_staff_member(self):
        req = self._req_with_user(self.staff_member)
        self.assertTrue(self.perm.has_object_permission(req, self.view, self.domain))

    def test_denies_other_user_not_owner_not_staff(self):
        req = self._req_with_user(self.other)
        self.assertFalse(self.perm.has_object_permission(req, self.view, self.domain))
