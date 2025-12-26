from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.permissions import SAFE_METHODS

from ..permissions import IsStaffOrReadOnly  # adapte l'import selon ton projet

User = get_user_model()


class IsStaffOrReadOnlyTests(TestCase):
    def setUp(self):
        self.perm = IsStaffOrReadOnly()
        self.view = object()  # pas utilisé ici

        self.anon = SimpleNamespace(is_authenticated=False, is_staff=False, is_superuser=False)
        self.user = User.objects.create_user(username="u1", password="pass")
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.superuser = User.objects.create_user(username="admin", password="pass", is_superuser=True)

    def _req(self, method: str, user):
        return SimpleNamespace(method=method, user=user)

    # ------------------------------------------------------------
    # SAFE METHODS : autorisé pour tout le monde (y compris anon)
    # ------------------------------------------------------------
    def test_safe_methods_allowed_for_anonymous(self):
        for method in SAFE_METHODS:
            req = self._req(method, self.anon)
            self.assertTrue(self.perm.has_permission(req, self.view), f"{method} should be allowed")

    def test_safe_methods_allowed_for_authenticated_user(self):
        for method in SAFE_METHODS:
            req = self._req(method, self.user)
            self.assertTrue(self.perm.has_permission(req, self.view), f"{method} should be allowed")

    # ------------------------------------------------------------
    # UNSAFE METHODS : interdit si pas staff/superuser
    # ------------------------------------------------------------
    def test_unsafe_methods_denied_for_anonymous(self):
        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            req = self._req(method, self.anon)
            self.assertFalse(self.perm.has_permission(req, self.view), f"{method} should be denied")

    def test_unsafe_methods_denied_for_authenticated_non_staff(self):
        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            req = self._req(method, self.user)
            self.assertFalse(self.perm.has_permission(req, self.view), f"{method} should be denied")

    def test_unsafe_methods_allowed_for_staff(self):
        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            req = self._req(method, self.staff)
            self.assertTrue(self.perm.has_permission(req, self.view), f"{method} should be allowed")

    def test_unsafe_methods_allowed_for_superuser(self):
        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            req = self._req(method, self.superuser)
            self.assertTrue(self.perm.has_permission(req, self.view), f"{method} should be allowed")
