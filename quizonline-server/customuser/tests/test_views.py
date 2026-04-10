from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from domain.models import Domain
from language.models import Language
from rest_framework import status
from rest_framework.test import APITestCase

from customuser.throttling import (
    EmailConfirmRateThrottle,
    PasswordResetConfirmRateThrottle,
    PasswordResetRateThrottle,
    TokenObtainRateThrottle,
)

User = get_user_model()


class UserViewsTests(APITestCase):
    USER_LIST_CREATE_URL = "/api/user/"
    PASSWORD_RESET_REQUEST_URL = "/api/user/password/reset/"
    PASSWORD_RESET_CONFIRM_URL = "/api/user/password/reset/confirm/"
    EMAIL_CONFIRM_URL = "/api/user/email/confirm/"
    PASSWORD_CHANGE_URL = "/api/user/password/change/"
    ME_URL = "/api/user/me/"
    TOKEN_URL = "/api/token/"

    def USER_DETAIL_URL(self, user_id):
        return f"/api/user/{user_id}/"

    def USER_QUIZ_LIST_URL(self, user_id):
        return f"/api/user/{user_id}/quizzes/"

    def setUp(self):
        cache.clear()
        self.lang_fr = Language.objects.create(code="fr", name="Francais", active=True)
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
        self.domain = Domain.objects.create(owner=self.staff, active=True)
        self.domain.allowed_languages.set([self.lang_fr])
        self.domain.set_current_language("fr")
        self.domain.name = "Alpha"
        self.domain.description = ""
        self.domain.save()

    def tearDown(self):
        cache.clear()
        super().tearDown()

    def _as_list(self, data):
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        return data

    def test_user_list_requires_admin(self):
        res = self.client.get(self.USER_LIST_CREATE_URL)
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        self.client.force_authenticate(user=self.u1)
        res = self.client.get(self.USER_LIST_CREATE_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

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

    def test_user_create_can_link_managed_domains(self):
        payload = {
            "username": "domain-newbie",
            "email": "domain-newbie@example.com",
            "first_name": "New",
            "last_name": "Bie",
            "password": "SecretPass123!",
            "managed_domain_ids": [self.domain.id],
        }

        res = self.client.post(self.USER_LIST_CREATE_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        created = User.objects.get(username="domain-newbie")
        self.assertEqual(list(created.linked_domains.values_list("id", flat=True)), [self.domain.id])
        self.assertEqual(created.current_domain_id, self.domain.id)

    def test_user_retrieve_requires_self_or_staff(self):
        res = self.client.get(self.USER_DETAIL_URL(self.u1.id))
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        self.client.force_authenticate(user=self.u2)
        res = self.client.get(self.USER_DETAIL_URL(self.u1.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.u1)
        res = self.client.get(self.USER_DETAIL_URL(self.u1.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["username"], "u1")

        self.client.force_authenticate(user=self.staff)
        res = self.client.get(self.USER_DETAIL_URL(self.u1.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_user_update_patch_requires_self_or_staff(self):
        url = self.USER_DETAIL_URL(self.u1.id)

        self.client.force_authenticate(user=self.u2)
        res = self.client.patch(url, {"email": "hacked@example.com"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.u1)
        res = self.client.patch(url, {"email": "newu1@example.com", "language": "fr"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.u1.refresh_from_db()
        self.assertEqual(self.u1.email, "newu1@example.com")
        self.assertEqual(self.u1.language, "fr")

        self.client.force_authenticate(user=self.staff)
        res = self.client.patch(url, {"first_name": "StaffEdited"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_user_update_patch_self_cannot_change_password_or_is_active(self):
        url = self.USER_DETAIL_URL(self.u1.id)
        self.client.force_authenticate(user=self.u1)

        res = self.client.patch(url, {"password": "BrandNewPass123!"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        res = self.client.patch(url, {"is_active": False}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        self.u1.refresh_from_db()
        self.assertTrue(self.u1.check_password("u1pass123!"))
        self.assertTrue(self.u1.is_active)

    def test_user_update_patch_staff_can_change_password_and_is_active(self):
        url = self.USER_DETAIL_URL(self.u1.id)
        self.client.force_authenticate(user=self.staff)

        res = self.client.patch(url, {"password": "BrandNewPass123!", "is_active": False}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.u1.refresh_from_db()
        self.assertTrue(self.u1.check_password("BrandNewPass123!"))
        self.assertFalse(self.u1.is_active)

    def test_only_superuser_can_change_nb_domain_max(self):
        url = self.USER_DETAIL_URL(self.u1.id)

        self.client.force_authenticate(user=self.staff)
        res = self.client.patch(url, {"nb_domain_max": 5}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(user=self.superuser)
        res = self.client.patch(url, {"nb_domain_max": 5}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.u1.refresh_from_db()
        self.assertEqual(self.u1.nb_domain_max, 5)

    def test_user_destroy_requires_superuser(self):
        url = self.USER_DETAIL_URL(self.u2.id)

        self.client.force_authenticate(user=self.staff)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.superuser)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.u2.pk).exists())

    def test_user_quiz_list_forbidden_for_other_non_staff(self):
        self.client.force_authenticate(user=self.u2)
        res = self.client.get(self.USER_QUIZ_LIST_URL(self.u1.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_quiz_list_allowed_for_self_and_staff(self):
        with patch("customuser.views.Quiz.objects.filter") as mock_filter:
            mock_qs = MagicMock()
            mock_qs.distinct.return_value = []
            mock_filter.return_value = mock_qs

            self.client.force_authenticate(user=self.u1)
            res = self.client.get(self.USER_QUIZ_LIST_URL(self.u1.id))
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data, [])

            self.client.force_authenticate(user=self.staff)
            res = self.client.get(self.USER_QUIZ_LIST_URL(self.u1.id))
            self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_password_reset_request_invalid_email_returns_400(self):
        res = self.client.post(self.PASSWORD_RESET_REQUEST_URL, {"email": "not-an-email"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_BASE_URL="http://127.0.0.1:4200",
        PASSWORD_RESET_FRONTEND_PATH_PREFIX="/reset-password",
    )
    def test_password_reset_request_always_returns_200_and_enqueues_password_reset_mail(self):
        with patch("customuser.services.send_password_reset_email") as send_password_reset_email:
            res = self.client.post(self.PASSWORD_RESET_REQUEST_URL, {"email": "u1@example.com"}, format="json")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIn("detail", res.data)
            send_password_reset_email.assert_called_once_with(self.u1)

    def test_password_reset_request_returns_200_even_if_form_invalid(self):
        with patch("customuser.services.send_password_reset_email") as send_password_reset_email:
            res = self.client.post(self.PASSWORD_RESET_REQUEST_URL, {"email": "u1@example.com"}, format="json")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            send_password_reset_email.assert_called_once_with(self.u1)

    def test_password_reset_request_marks_user_as_password_change_required(self):
        self.assertFalse(self.u1.must_change_password)

        with patch("customuser.services.send_password_reset_email"):
            res = self.client.post(self.PASSWORD_RESET_REQUEST_URL, {"email": "u1@example.com"}, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.u1.refresh_from_db()
        self.assertTrue(self.u1.must_change_password)

    def test_password_reset_confirm_invalid_uid_returns_400(self):
        with patch("customuser.services.resolve_user_from_uid", return_value=None):
            res = self.client.post(
                self.PASSWORD_RESET_CONFIRM_URL,
                {"uid": "bad", "token": "tkn", "new_password1": "NewPass123!Aa", "new_password2": "NewPass123!Aa"},
                format="json",
            )
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("detail", res.data)

    def test_password_reset_confirm_invalid_token_returns_400(self):
        uid = "encoded"
        with patch("customuser.services.resolve_user_from_uid", return_value=self.u1), patch(
            "customuser.services.token_is_valid",
            return_value=False,
        ):
            res = self.client.post(
                self.PASSWORD_RESET_CONFIRM_URL,
                {"uid": uid, "token": "bad", "new_password1": "NewPass123!Aa", "new_password2": "NewPass123!Aa"},
                format="json",
            )
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("detail", res.data)

    def test_password_reset_confirm_success_changes_password(self):
        new_pw = "NewPass123!Aa"
        self.u1.must_change_password = True
        self.u1.save(update_fields=["must_change_password"])
        with patch("customuser.services.resolve_user_from_uid", return_value=self.u1), patch(
            "customuser.services.token_is_valid",
            return_value=True,
        ):
            res = self.client.post(
                self.PASSWORD_RESET_CONFIRM_URL,
                {"uid": "encoded", "token": "ok", "new_password1": new_pw, "new_password2": new_pw},
                format="json",
            )
            self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.u1.refresh_from_db()
        self.assertTrue(self.u1.check_password(new_pw))
        self.assertFalse(self.u1.must_change_password)

    def test_email_confirm_success_marks_user_as_confirmed(self):
        uid = urlsafe_base64_encode(force_bytes(self.u1.pk))
        token = default_token_generator.make_token(self.u1)

        res = self.client.post(
            self.EMAIL_CONFIRM_URL,
            {"uid": uid, "token": token},
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.u1.refresh_from_db()
        self.assertTrue(self.u1.email_confirmed)

    def test_email_confirm_invalid_token_returns_400(self):
        uid = urlsafe_base64_encode(force_bytes(self.u1.pk))

        res = self.client.post(
            self.EMAIL_CONFIRM_URL,
            {"uid": uid, "token": "bad-token"},
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_obtain_pair_rejects_unconfirmed_email(self):
        self.u1.email_confirmed = False
        self.u1.save(update_fields=["email_confirmed"])

        res = self.client.post(
            self.TOKEN_URL,
            {"username": "u1", "password": "u1pass123!"},
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(res.data["detail"], "Confirmez votre adresse email avant de vous connecter.")

    def test_token_obtain_pair_accepts_confirmed_email(self):
        self.u1.email_confirmed = True
        self.u1.save(update_fields=["email_confirmed"])

        res = self.client.post(
            self.TOKEN_URL,
            {"username": "u1", "password": "u1pass123!"},
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_token_obtain_pair_is_rate_limited(self):
        self.u1.email_confirmed = True
        self.u1.save(update_fields=["email_confirmed"])

        with patch.object(TokenObtainRateThrottle, "rate", "2/min", create=True):
            for _ in range(2):
                res = self.client.post(
                    self.TOKEN_URL,
                    {"username": "u1", "password": "u1pass123!"},
                    format="json",
                )
                self.assertEqual(res.status_code, status.HTTP_200_OK)

            res = self.client.post(
                self.TOKEN_URL,
                {"username": "u1", "password": "u1pass123!"},
                format="json",
            )
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_password_change_requires_auth(self):
        res = self.client.post(
            self.PASSWORD_CHANGE_URL,
            {"old_password": "x", "new_password": "y"},
            format="json",
        )
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_password_reset_request_is_rate_limited(self):
        with patch.object(PasswordResetRateThrottle, "rate", "2/hour", create=True), patch(
            "customuser.services.send_password_reset_email"
        ):
            for _ in range(2):
                res = self.client.post(self.PASSWORD_RESET_REQUEST_URL, {"email": "u1@example.com"}, format="json")
                self.assertEqual(res.status_code, status.HTTP_200_OK)

            res = self.client.post(self.PASSWORD_RESET_REQUEST_URL, {"email": "u1@example.com"}, format="json")

        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_password_reset_confirm_is_rate_limited(self):
        with patch.object(PasswordResetConfirmRateThrottle, "rate", "2/hour", create=True), patch(
            "customuser.services.resolve_user_from_uid",
            return_value=self.u1,
        ), patch("customuser.services.token_is_valid", return_value=False):
            for _ in range(2):
                res = self.client.post(
                    self.PASSWORD_RESET_CONFIRM_URL,
                    {"uid": "encoded", "token": "bad", "new_password1": "NewPass123!Aa", "new_password2": "NewPass123!Aa"},
                    format="json",
                )
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

            res = self.client.post(
                self.PASSWORD_RESET_CONFIRM_URL,
                {"uid": "encoded", "token": "bad", "new_password1": "NewPass123!Aa", "new_password2": "NewPass123!Aa"},
                format="json",
            )

        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_email_confirm_is_rate_limited(self):
        with patch.object(EmailConfirmRateThrottle, "rate", "2/hour", create=True):
            for _ in range(2):
                res = self.client.post(
                    self.EMAIL_CONFIRM_URL,
                    {"uid": "bad", "token": "bad"},
                    format="json",
                )
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

            res = self.client.post(
                self.EMAIL_CONFIRM_URL,
                {"uid": "bad", "token": "bad"},
                format="json",
            )

        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

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
        self.u1.must_change_password = True
        self.u1.save(update_fields=["must_change_password"])
        res = self.client.post(
            self.PASSWORD_CHANGE_URL,
            {"old_password": "u1pass123!", "new_password": "NewPass123!"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.u1.refresh_from_db()
        self.assertTrue(self.u1.check_password("NewPass123!"))
        self.assertFalse(self.u1.must_change_password)

    def test_me_requires_auth(self):
        res = self.client.get(self.ME_URL)
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_me_get_returns_current_user(self):
        self.client.force_authenticate(user=self.u1)
        self.u1.must_change_password = True
        self.u1.save(update_fields=["must_change_password"])
        res = self.client.get(self.ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["username"], "u1")
        self.assertTrue(res.data["password_change_required"])

    def test_me_patch_updates_profile_but_not_sensitive_fields(self):
        self.client.force_authenticate(user=self.u1)
        res = self.client.patch(self.ME_URL, {"email": "me-new@example.com", "language": "fr"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.u1.refresh_from_db()
        self.assertEqual(self.u1.email, "me-new@example.com")
        self.assertEqual(self.u1.language, "fr")
        self.assertEqual(self.u1.username, "u1")

        res = self.client.patch(self.ME_URL, {"current_domain": 999}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        res = self.client.patch(self.ME_URL, {"password": "Nope12345!"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_patch_can_update_managed_domains(self):
        self.client.force_authenticate(user=self.u1)

        res = self.client.patch(self.ME_URL, {"managed_domain_ids": [self.domain.id]}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.u1.refresh_from_db()
        self.assertEqual(list(self.u1.linked_domains.values_list("id", flat=True)), [self.domain.id])
        self.assertEqual(self.u1.current_domain_id, self.domain.id)
