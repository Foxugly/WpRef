from customuser.permissions import IsSelfOrStaffOrSuperuser  # adapte l'import
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory

User = get_user_model()


class IsSelfOrStaffOrSuperuserUnitTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.perm = IsSelfOrStaffOrSuperuser()

        self.u1 = User.objects.create_user(username="u1", password="pass")
        self.u2 = User.objects.create_user(username="u2", password="pass")
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.superuser = User.objects.create_user(username="root", password="pass", is_superuser=True)

    def test_has_permission_requires_auth(self):
        req = self.factory.get("/fake")
        req.user = type("Anon", (), {"is_authenticated": False})()  # petit stub
        self.assertFalse(self.perm.has_permission(req, None))

        req2 = self.factory.get("/fake")
        req2.user = self.u1
        self.assertTrue(self.perm.has_permission(req2, None))

    def test_object_permission_self_ok(self):
        req = self.factory.get("/fake")
        req.user = self.u1
        self.assertTrue(self.perm.has_object_permission(req, None, self.u1))

    def test_object_permission_other_user_denied(self):
        req = self.factory.get("/fake")
        req.user = self.u1
        self.assertFalse(self.perm.has_object_permission(req, None, self.u2))

    def test_object_permission_staff_ok(self):
        req = self.factory.get("/fake")
        req.user = self.staff
        self.assertTrue(self.perm.has_object_permission(req, None, self.u1))

    def test_object_permission_superuser_ok(self):
        req = self.factory.get("/fake")
        req.user = self.superuser
        self.assertTrue(self.perm.has_object_permission(req, None, self.u1))
