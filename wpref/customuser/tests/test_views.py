from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

# ⚠️ adapte si ton CustomUser est dans une autre app
from ..models import CustomUser  # noqa

User = get_user_model()


class UserViewsTests(APITestCase):
    # URLs alignées sur tes docstrings
    USER_LIST_CREATE_URL = "/api/user/"
    USER_DETAIL_URL = lambda self, user_id: f"/api/user/{user_id}/"
    USER_QUIZ_LIST_URL = lambda self, user_id: f"/api/user/{user_id}/quizzes/"

    PASSWORD_RESET_REQUEST_URL = "/api/user/password/reset/"
    PASSWORD_RESET_CONFIRM_URL = "/api/user/password/reset/confirm/"
    PASSWORD_CHANGE_URL = "/api/user/password/change/"
    ME_URL = "/api/user/me/"

    def setUp(self):
        self.u1 = User.objects.create_user(
            username="u1", password="u1pass123!", email="u1@example.com", first_name="U", last_name="One"
        )
        self.u2 = User.objects.create_user(
            username="u2", password="u2pass123!", email="u2@example.com", first_name="U", last_name="Two"
        )
        self.staff = User.objects.create_user(
            username="staff", password="staffpass123!", email="staff@example.com", is_staff=True
        )
        self.superuser = User.objects.create_user(
            username="admin", password="adminpass123!", email="admin@example.com", is_superuser=True, is_staff=True
        )

    def _as_list(self, data):
        # support pagination DRF
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        return data

    # ------------------------------------------------------------------
    # CustomUserViewSet
    # ------------------------------------------------------------------

    def test_user_list_requires_admin(self):
        # unauth -> 401 (ou parfois 403 selon config auth)
        res = self.client.get(self.USER_LIST_CREATE_URL)
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        # normal user -> 403
        self.client.force_authenticate(user=self.u1)
        res = self.client.get(self.USER_LIST_CREATE_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # staff -> 200
        self.client.force_authenticate(user=self.staff)
        res = self.client.get(self.USER_LIST_CREATE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(self._as_list(res.data), list)

    def test_user_create_is_public_and_hashes_password(self):
        payload = {
            "username": "newbie",
            "email": "newbie@example.com",
            "first_name": "New",
            "last_name": "Bie",
            "password": "SecretPass123!",
        }
        res = self.client.post(self.USER_LIST_CREATE_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["username"], "newbie")

        created = User.objects.get(username="newbie")
        self.assertTrue(created.check_password("SecretPass123!"))

    def test_user_retrieve_requires_self_or_staff(self):
        # unauth
        res = self.client.get(self.USER_DETAIL_URL(self.u1.id))
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        # other user -> 403
        self.client.force_authenticate(user=self.u2)
        res = self.client.get(self.USER_DETAIL_URL(self.u1.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # self -> 200
        self.client.force_authenticate(user=self.u1)
        res = self.client.get(self.USER_DETAIL_URL(self.u1.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["username"], "u1")

        # staff -> 200
        self.client.force_authenticate(user=self.staff)
        res = self.client.get(self.USER_DETAIL_URL(self.u1.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_user_update_patch_requires_self_or_staff(self):
        url = self.USER_DETAIL_URL(self.u1.id)

        # other user -> 403
        self.client.force_authenticate(user=self.u2)
        res = self.client.patch(url, {"email": "hacked@example.com"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # self -> 200
        self.client.force_authenticate(user=self.u1)
        res = self.client.patch(url, {"email": "newu1@example.com"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.u1.refresh_from_db()
        self.assertEqual(self.u1.email, "newu1@example.com")

        # staff -> 200
        self.client.force_authenticate(user=self.staff)
        res = self.client.patch(url, {"first_name": "StaffEdited"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_user_update_patch_can_change_password_if_serializer_allows(self):
        """
        Ton CustomUserUpdateSerializer permet password (write_only, required=False).
        Donc PATCH doit changer le password si fourni.
        """
        url = self.USER_DETAIL_URL(self.u1.id)
        self.client.force_authenticate(user=self.u1)

        res = self.client.patch(url, {"password": "BrandNewPass123!"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.u1.refresh_from_db()
        self.assertTrue(self.u1.check_password("BrandNewPass123!"))

    # ------------------------------------------------------------------
    # UserQuizListView
    # ------------------------------------------------------------------

    def test_user_quiz_list_forbidden_for_other_non_staff(self):
        self.client.force_authenticate(user=self.u2)
        res = self.client.get(self.USER_QUIZ_LIST_URL(self.u1.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_quiz_list_allowed_for_self_and_staff(self):
        """
        On patch le queryset Quiz.objects.filter(...).distinct() pour éviter
        de dépendre de la structure exacte de tes modèles (sessions__user).
        """
        # ⚠️ adapte le module patch si ton fichier views n'est pas user.views
        with patch("customuser.views.Quiz.objects.filter") as mock_filter:
            mock_qs = MagicMock()
            mock_qs.distinct.return_value = []
            mock_filter.return_value = mock_qs

            # self -> 200, liste vide
            self.client.force_authenticate(user=self.u1)
            res = self.client.get(self.USER_QUIZ_LIST_URL(self.u1.id))
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data, [])

            # staff -> 200
            self.client.force_authenticate(user=self.staff)
            res = self.client.get(self.USER_QUIZ_LIST_URL(self.u1.id))
            self.assertEqual(res.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # PasswordResetRequestView
    # ------------------------------------------------------------------

    def test_password_reset_request_invalid_email_returns_400(self):
        res = self.client.post(self.PASSWORD_RESET_REQUEST_URL, {"email": "not-an-email"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(DEFAULT_FROM_EMAIL="noreply@example.com")
    def test_password_reset_request_always_returns_200_and_calls_form_save_if_valid(self):
        """
        Le code doit toujours répondre 200 pour ne pas révéler si l'email existe.
        Si PasswordResetForm.is_valid() est True -> save() est appelé.
        """
        # ⚠️ adapte le module patch si besoin
        with patch("customuser.views.PasswordResetForm") as MockForm:
            instance = MockForm.return_value
            instance.is_valid.return_value = True

            res = self.client.post(self.PASSWORD_RESET_REQUEST_URL, {"email": "u1@example.com"}, format="json")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIn("detail", res.data)

            instance.save.assert_called_once()

    def test_password_reset_request_returns_200_even_if_form_invalid(self):
        with patch("customuser.views.PasswordResetForm") as MockForm:
            instance = MockForm.return_value
            instance.is_valid.return_value = False

            res = self.client.post(self.PASSWORD_RESET_REQUEST_URL, {"email": "u1@example.com"}, format="json")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            instance.save.assert_not_called()

    # ------------------------------------------------------------------
    # PasswordResetConfirmView
    # ------------------------------------------------------------------

    def test_password_reset_confirm_invalid_uid_returns_400(self):
        """
        Si uid decode échoue -> 400 "Lien invalide."
        """
        with patch("customuser.views.urlsafe_base64_decode", side_effect=ValueError("bad")):
            res = self.client.post(
                self.PASSWORD_RESET_CONFIRM_URL,
                {"uid": "bad", "token": "tkn", "new_password1": "NewPass123!Aa", "new_password2": "NewPass123!Aa", },
                format="json",
            )
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("detail", res.data)

    def test_password_reset_confirm_invalid_token_returns_400(self):
        """
        uid ok, user ok, mais token invalide.
        """
        uid_bytes = str(self.u1.pk).encode("utf-8")
        with patch("customuser.views.urlsafe_base64_decode", return_value=uid_bytes), \
                patch("customuser.views.default_token_generator.check_token", return_value=False):
            res = self.client.post(
                self.PASSWORD_RESET_CONFIRM_URL,
                {"uid": "encoded", "token": "bad", "new_password1": "NewPass123!Aa",
                 "new_password2": "NewPass123!Aa", },
                format="json",
            )
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("detail", res.data)

    def test_password_reset_confirm_success_changes_password(self):
        uid_bytes = str(self.u1.pk).encode("utf-8")
        new_pw = "NewPass123!Aa"
        with patch("customuser.views.urlsafe_base64_decode", return_value=uid_bytes), \
                patch("customuser.views.default_token_generator.check_token", return_value=True):
            res = self.client.post(
                self.PASSWORD_RESET_CONFIRM_URL,
                {"uid": "encoded", "token": "ok", "new_password1": new_pw, "new_password2": new_pw, },
                format="json",
            )
            self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.u1.refresh_from_db()
        self.assertTrue(self.u1.check_password(new_pw))

    # ------------------------------------------------------------------
    # PasswordChangeView
    # ------------------------------------------------------------------

    def test_password_change_requires_auth(self):
        res = self.client.post(
            self.PASSWORD_CHANGE_URL,
            {"old_password": "x", "new_password": "y"},
            format="json",
        )
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_password_change_wrong_old_password_returns_400(self):
        self.client.force_authenticate(user=self.u1)
        res = self.client.post(
            self.PASSWORD_CHANGE_URL,
            {"old_password": "WRONG", "new_password": "NewPass123!"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", res.data)

    def test_password_change_success(self):
        self.client.force_authenticate(user=self.u1)
        res = self.client.post(
            self.PASSWORD_CHANGE_URL,
            {"old_password": "u1pass123!", "new_password": "NewPass123!"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.u1.refresh_from_db()
        self.assertTrue(self.u1.check_password("NewPass123!"))

    # ------------------------------------------------------------------
    # MeView
    # ------------------------------------------------------------------

    def test_me_requires_auth(self):
        res = self.client.get(self.ME_URL)
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_me_get_returns_current_user(self):
        self.client.force_authenticate(user=self.u1)
        res = self.client.get(self.ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["username"], "u1")

    def test_me_patch_updates_profile_but_not_username(self):
        self.client.force_authenticate(user=self.u1)
        res = self.client.patch(self.ME_URL, {"email": "me-new@example.com"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.u1.refresh_from_db()
        self.assertEqual(self.u1.email, "me-new@example.com")
        self.assertEqual(self.u1.username, "u1")
