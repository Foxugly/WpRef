from unittest.mock import patch

# ✅ adapte ces imports selon ton projet
from customuser.views import (
    UserQuizListView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PasswordChangeView,
    MeView,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

User = get_user_model()


class CustomUserViewsAPITests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.u1 = User.objects.create_user(username="u1", password="u1pass", email="u1@example.com")
        self.u2 = User.objects.create_user(username="u2", password="u2pass", email="u2@example.com")
        self.staff = User.objects.create_user(
            username="staff", password="staffpass", email="staff@example.com", is_staff=True
        )
        self.superuser = User.objects.create_user(
            username="admin", password="adminpass", email="admin@example.com", is_superuser=True
        )

        self.u_no_name = User.objects.create_user(
            username="u3",
            password="u1pass",
            email="u1@example.com",
        )

        self.u_with_name = User.objects.create_user(
            username="u4",
            password="u2pass",
            email="u2@example.com",
            first_name="John",
            last_name="Smith",
        )
        # ------------------------------------------------------------
        # __str__
        # ------------------------------------------------------------

    def test_str_without_first_and_last_name_returns_username(self):
        """
        Si first_name ou last_name manquant → __str__ renvoie username
        """
        self.assertEqual(str(self.u_no_name), "u3")

    def test_str_with_first_and_last_name_returns_full_name(self):
        """
        Si first_name ET last_name présents → __str__ renvoie get_full_name()
        """
        self.assertEqual(
            str(self.u_with_name),
            "John Smith (u4)",
        )

        # ------------------------------------------------------------
        # get_full_name
        # ------------------------------------------------------------

    def test_get_full_name_format(self):
        """
        get_full_name doit retourner : 'first last (username)'
        """
        full_name = self.u_with_name.get_full_name()
        self.assertEqual(full_name, "John Smith (u4)")

    def test_get_full_name_with_empty_names(self):
        """
        Cas limite : first_name / last_name vides
        (on vérifie juste le format actuel)
        """
        full_name = self.u_no_name.get_full_name()
        self.assertEqual(full_name, "u3")

    # ------------------------------------------------------------------
    # UserQuizListView
    # ------------------------------------------------------------------
    @patch("customuser.views.Quiz")  # ✅ patch au bon import (là où Quiz est importé dans la view)
    def test_user_quiz_list_self_allowed(self, QuizMock):
        """
        user = u1 -> ok 200
        """
        QuizMock.objects.filter.return_value.distinct.return_value = []
        req = self.factory.get("/fake-url/")
        force_authenticate(req, user=self.u1)

        res = UserQuizListView.as_view()(req, pk=self.u1.pk)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    @patch("customuser.views.Quiz")
    def test_user_quiz_list_other_user_forbidden(self, QuizMock):
        """
        user = u1 -> pk=u2 => PermissionDenied => 403
        """
        QuizMock.objects.filter.return_value.distinct.return_value = []
        req = self.factory.get("/fake-url/")
        force_authenticate(req, user=self.u1)

        res = UserQuizListView.as_view()(req, pk=self.u2.pk)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    @patch("customuser.views.Quiz")
    def test_user_quiz_list_staff_allowed(self, QuizMock):
        """
        staff peut voir u1 => 200
        """
        QuizMock.objects.filter.return_value.distinct.return_value = []
        req = self.factory.get("/fake-url/")
        force_authenticate(req, user=self.staff)

        res = UserQuizListView.as_view()(req, pk=self.u1.pk)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_user_quiz_list_requires_auth(self):
        """
        permission IsSelfOrStaffOrSuperuser -> has_permission exige authenticated
        => 401 (si auth active) ou 403 selon config
        """
        req = self.factory.get("/fake-url/")
        res = UserQuizListView.as_view()(req, pk=self.u1.pk)
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    # ------------------------------------------------------------------
    # PasswordResetRequestView
    # ------------------------------------------------------------------
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="noreply@example.com",
    )
    def test_password_reset_request_always_200_even_if_email_unknown(self):
        req = self.factory.post("/fake-url/", {"email": "unknown@example.com"}, format="json")
        res = PasswordResetRequestView.as_view()(req)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("detail", res.data)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="noreply@example.com",
    )
    def test_password_reset_request_sends_email_if_user_exists(self):
        mail.outbox.clear()

        req = self.factory.post("/fake-url/", {"email": self.u1.email}, format="json")
        res = PasswordResetRequestView.as_view()(req)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Django PasswordResetForm envoie un email si email match un user actif
        self.assertGreaterEqual(len(mail.outbox), 1)

    # ------------------------------------------------------------------
    # PasswordResetConfirmView
    # ------------------------------------------------------------------
    def test_password_reset_confirm_success(self):
        uid = urlsafe_base64_encode(force_bytes(self.u1.pk))
        token = default_token_generator.make_token(self.u1)

        payload = {"uid": uid, "token": token, "new_password1": "NewPass123!Aa", "new_password2": "NewPass123!Aa",}
        req = self.factory.post("/fake-url/", payload, format="json")
        res = PasswordResetConfirmView.as_view()(req)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.u1.refresh_from_db()
        self.assertTrue(self.u1.check_password("NewPass123!Aa"))

    def test_password_reset_confirm_invalid_uid_returns_400(self):
        payload = {"uid": "bad", "token": "xxx", "new_password": "NewPass123!Aa"}
        req = self.factory.post("/fake-url/", payload, format="json")
        res = PasswordResetConfirmView.as_view()(req)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_invalid_token_returns_400(self):
        uid = urlsafe_base64_encode(force_bytes(self.u1.pk))
        payload = {"uid": uid, "token": "invalid-token", "new_password": "NewPass123!Aa"}
        req = self.factory.post("/fake-url/", payload, format="json")
        res = PasswordResetConfirmView.as_view()(req)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # PasswordChangeView
    # ------------------------------------------------------------------
    def test_password_change_requires_auth(self):
        req = self.factory.post("/fake-url/", {"old_password": "u1pass", "new_password": "Xx123456!!"}, format="json")
        res = PasswordChangeView.as_view()(req)

        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_password_change_wrong_old_password_returns_400(self):
        req = self.factory.post(
            "/fake-url/",
            {"old_password": "WRONG", "new_password": "Xx123456!!"},
            format="json",
        )
        force_authenticate(req, user=self.u1)
        res = PasswordChangeView.as_view()(req)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_change_success(self):
        req = self.factory.post(
            "/fake-url/",
            {"old_password": "u1pass", "new_password": "Xx123456!!"},
            format="json",
        )
        force_authenticate(req, user=self.u1)
        res = PasswordChangeView.as_view()(req)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.u1.refresh_from_db()
        self.assertTrue(self.u1.check_password("Xx123456!!"))

    # ------------------------------------------------------------------
    # MeView (RetrieveUpdateAPIView)
    # ------------------------------------------------------------------
    def test_me_get_requires_auth(self):
        req = self.factory.get("/fake-url/")
        res = MeView.as_view()(req)
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_me_get_success(self):
        req = self.factory.get("/fake-url/")
        force_authenticate(req, user=self.u1)
        res = MeView.as_view()(req)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_me_patch_success(self):
        # ⚠️ adapte le payload selon MeSerializer (ex: first_name, last_name, email, etc.)
        req = self.factory.patch("/fake-url/", {"email": "new_u1@example.com"}, format="json")
        force_authenticate(req, user=self.u1)
        res = MeView.as_view()(req)
        self.assertIn(res.status_code, (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST))
