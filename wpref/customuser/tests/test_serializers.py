from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from quiz.models import Quiz, QuizTemplate

from ..serializers import (
    CustomUserReadSerializer,
    CustomUserCreateSerializer,
    CustomUserUpdateSerializer,
    QuizSimpleSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordChangeSerializer,
    MeSerializer,
)

User = get_user_model()


class CustomUserReadSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="u1",
            password="secret1234",
            email="u1@example.com",
            first_name="U",
            last_name="One",
            is_staff=True,
            is_superuser=False,
            is_active=True,
        )

    def test_read_serializer_contains_expected_fields(self):
        data = CustomUserReadSerializer(instance=self.user).data
        self.assertEqual(
            set(data.keys()),
            {"id", "username", "email", "first_name", "last_name", "is_staff", "is_superuser", "is_active"},
        )
        self.assertEqual(data["username"], "u1")

    def test_read_serializer_does_not_expose_password(self):
        data = CustomUserReadSerializer(instance=self.user).data
        self.assertNotIn("password", data)

    def test_read_only_fields_are_read_only(self):
        serializer = CustomUserReadSerializer()
        ro = set(serializer.get_fields()["id"].read_only for _ in [0])
        self.assertTrue(serializer.get_fields()["id"].read_only)
        self.assertTrue(serializer.get_fields()["is_staff"].read_only)
        self.assertTrue(serializer.get_fields()["is_superuser"].read_only)
        self.assertTrue(serializer.get_fields()["is_active"].read_only)


class CustomUserCreateSerializerTests(TestCase):
    def test_create_serializer_creates_user_and_hashes_password(self):
        payload = {
            "username": "newuser",
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "SecretPass123!",
        }

        serializer = CustomUserCreateSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(user.check_password("SecretPass123!"))  # set_password a bien été utilisé

    def test_create_serializer_password_is_write_only(self):
        user = User.objects.create_user(username="u2", password="SecretPass123!")
        data = CustomUserCreateSerializer(instance=user).data
        self.assertNotIn("password", data)

    def test_create_serializer_requires_password(self):
        payload = {"username": "no-pass"}
        serializer = CustomUserCreateSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)


class CustomUserUpdateSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="u3",
            password="OldPass123!",
            email="old@example.com",
            first_name="Old",
            last_name="Name",
            is_active=True,
        )

    def test_update_serializer_updates_fields_without_password(self):
        payload = {
            "email": "new@example.com",
            "first_name": "NewFirst",
            "last_name": "NewLast",
            "is_active": False,
        }
        serializer = CustomUserUpdateSerializer(instance=self.user, data=payload, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.first_name, "NewFirst")
        self.assertEqual(user.last_name, "NewLast")
        self.assertFalse(user.is_active)

        # password inchangé
        self.assertTrue(user.check_password("OldPass123!"))

    def test_update_serializer_updates_password_when_provided(self):
        payload = {"password": "BrandNewPass123!"}
        serializer = CustomUserUpdateSerializer(instance=self.user, data=payload, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertTrue(user.check_password("BrandNewPass123!"))
        self.assertFalse(user.check_password("OldPass123!"))

    def test_update_serializer_password_is_optional(self):
        serializer = CustomUserUpdateSerializer(instance=self.user, data={"email": "x@y.com"}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class QuizSimpleSerializerTests(TestCase):
    def test_quiz_simple_serializer_reads_title_from_quiz_template(self):
        # ⚠️ adapte selon tes modèles réels
        qt = QuizTemplate.objects.create(title="Template Title", slug="template-title")
        quiz = Quiz.objects.create(quiz_template=qt)

        data = QuizSimpleSerializer(instance=quiz).data
        self.assertEqual(set(data.keys()), {"id", "title"})
        self.assertEqual(data["title"], "Template Title")


class PasswordResetRequestSerializerTests(TestCase):
    def test_password_reset_request_serializer_accepts_valid_email(self):
        serializer = PasswordResetRequestSerializer(data={"email": "test@example.com"})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["email"], "test@example.com")

    def test_password_reset_request_serializer_rejects_invalid_email(self):
        serializer = PasswordResetRequestSerializer(data={"email": "not-an-email"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


class PasswordResetConfirmSerializerTests(TestCase):
    def test_validate_password_is_called_for_new_password1(self):
        payload = {"uid": "abc", "token": "tkn", "new_password1": "StrongPass123!", "new_password2": "StrongPass123!"}
        with patch("customuser.serializers.validate_password") as mock_validate:
            serializer = PasswordResetConfirmSerializer(data=payload)
            self.assertTrue(serializer.is_valid(), serializer.errors)
            mock_validate.assert_called_once_with("StrongPass123!")

    def test_passwords_must_match(self):
        payload = {"uid": "abc", "token": "tkn", "new_password1": "StrongPass123!", "new_password2": "OtherPass123!"}
        serializer = PasswordResetConfirmSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password2", serializer.errors)

    def test_missing_fields_fail(self):
        serializer = PasswordResetConfirmSerializer(data={"uid": "abc", "token": "tkn"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password1", serializer.errors)
        self.assertIn("new_password2", serializer.errors)


class PasswordChangeSerializerTests(TestCase):
    def test_password_change_serializer_calls_validate_password(self):
        payload = {"old_password": "OldPass123!", "new_password": "NewPass123!"}

        with patch("customuser.serializers.validate_password") as mock_validate:
            serializer = PasswordChangeSerializer(data=payload)
            self.assertTrue(serializer.is_valid(), serializer.errors)
            mock_validate.assert_called_once_with("NewPass123!")

    def test_password_change_serializer_requires_fields(self):
        serializer = PasswordChangeSerializer(data={"old_password": "x"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password", serializer.errors)


class MeSerializerTests(TestCase):
    def setUp(self):
        # ⚠️ si ton CustomUser est le même modèle que User, adapte l'import/creation
        self.user = User.objects.create_user(
            username="meuser",
            password="SecretPass123!",
            email="me@example.com",
            first_name="Me",
            last_name="User",
        )
        # language peut exister sur CustomUser seulement (selon ton modèle)
        if hasattr(self.user, "language"):
            self.user.language = "fr"
            self.user.save()

    def test_me_serializer_has_expected_fields(self):
        data = MeSerializer(instance=self.user).data
        self.assertEqual(set(data.keys()), {"id", "username", "email", "first_name", "last_name", "language"})

    def test_me_serializer_read_only_fields(self):
        serializer = MeSerializer()
        self.assertTrue(serializer.get_fields()["id"].read_only)
        self.assertTrue(serializer.get_fields()["username"].read_only)
