from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from domain.models import Domain
from language.models import Language
from quiz.models import Quiz, QuizTemplate

from ..serializers import (
    CustomUserAdminUpdateSerializer,
    CustomUserCreateSerializer,
    CustomUserProfileUpdateSerializer,
    CustomUserReadSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    QuizSimpleSerializer,
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
            {
                "id",
                "username",
                "email",
                "first_name",
                "last_name",
                "language",
                "email_confirmed",
                "password_change_required",
                "is_staff",
                "is_superuser",
                "is_active",
                "current_domain",
                "current_domain_title",
                "owned_domain_ids",
                "managed_domain_ids",
            },
        )
        self.assertEqual(data["username"], "u1")

    def test_read_serializer_does_not_expose_password(self):
        data = CustomUserReadSerializer(instance=self.user).data
        self.assertNotIn("password", data)

    def test_read_only_fields_are_read_only(self):
        serializer = CustomUserReadSerializer()
        self.assertTrue(serializer.get_fields()["id"].read_only)
        self.assertTrue(serializer.get_fields()["email_confirmed"].read_only)
        self.assertTrue(serializer.get_fields()["password_change_required"].read_only)
        self.assertTrue(serializer.get_fields()["is_staff"].read_only)
        self.assertTrue(serializer.get_fields()["is_superuser"].read_only)
        self.assertTrue(serializer.get_fields()["is_active"].read_only)


class CustomUserCreateSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.lang_fr = Language.objects.create(code="fr", name="Francais", active=True)
        cls.owner = User.objects.create_user(username="owner", password="OwnerPass123!")
        cls.domain = Domain.objects.create(owner=cls.owner, active=True)
        cls.domain.allowed_languages.set([cls.lang_fr])
        cls.domain.set_current_language("fr")
        cls.domain.name = "Alpha"
        cls.domain.description = ""
        cls.domain.save()

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
        self.assertFalse(user.email_confirmed)
        self.assertTrue(user.check_password("SecretPass123!"))

    def test_create_serializer_links_managed_domains_when_provided(self):
        payload = {
            "username": "linkeduser",
            "email": "linked@example.com",
            "first_name": "Linked",
            "last_name": "User",
            "password": "SecretPass123!",
            "managed_domain_ids": [self.domain.id],
        }

        serializer = CustomUserCreateSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(list(user.linked_domains.values_list("id", flat=True)), [self.domain.id])
        self.assertEqual(user.current_domain_id, self.domain.id)

    def test_create_serializer_password_is_write_only(self):
        user = User.objects.create_user(username="u2", password="SecretPass123!")
        data = CustomUserCreateSerializer(instance=user).data
        self.assertNotIn("password", data)

    def test_create_serializer_requires_password(self):
        payload = {"username": "no-pass"}
        serializer = CustomUserCreateSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_create_serializer_validates_password(self):
        payload = {
            "username": "newuser",
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "SecretPass123!",
        }
        with patch("customuser.serializers.validate_password") as mock_validate:
            serializer = CustomUserCreateSerializer(data=payload)
            self.assertTrue(serializer.is_valid(), serializer.errors)
            mock_validate.assert_called_once_with("SecretPass123!")


class CustomUserProfileUpdateSerializerTests(TestCase):
    def setUp(self):
        self.lang_fr = Language.objects.create(code="fr", name="Francais", active=True)
        self.user = User.objects.create_user(
            username="u3",
            password="OldPass123!",
            email="old@example.com",
            first_name="Old",
            last_name="Name",
            is_active=True,
        )
        self.domain_owner = User.objects.create_user(username="domain-owner", password="DomainPass123!")
        self.domain = Domain.objects.create(owner=self.domain_owner, active=True)
        self.domain.allowed_languages.set([self.lang_fr])
        self.domain.set_current_language("fr")
        self.domain.name = "Beta"
        self.domain.description = ""
        self.domain.save()

    def test_profile_update_serializer_updates_non_sensitive_fields(self):
        payload = {
            "email": "new@example.com",
            "first_name": "NewFirst",
            "last_name": "NewLast",
            "language": "fr",
        }
        serializer = CustomUserProfileUpdateSerializer(instance=self.user, data=payload, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.first_name, "NewFirst")
        self.assertEqual(user.last_name, "NewLast")
        self.assertEqual(user.language, "fr")
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("OldPass123!"))

    def test_profile_update_serializer_updates_managed_domains(self):
        payload = {"managed_domain_ids": [self.domain.id]}
        serializer = CustomUserProfileUpdateSerializer(instance=self.user, data=payload, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(list(user.linked_domains.values_list("id", flat=True)), [self.domain.id])
        self.assertEqual(user.current_domain_id, self.domain.id)


class CustomUserAdminUpdateSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="u4",
            password="OldPass123!",
            email="old@example.com",
            first_name="Old",
            last_name="Name",
            is_active=True,
        )

    def test_admin_update_serializer_updates_fields_without_password(self):
        payload = {
            "email": "new@example.com",
            "first_name": "NewFirst",
            "last_name": "NewLast",
            "language": "fr",
            "is_active": False,
        }
        serializer = CustomUserAdminUpdateSerializer(instance=self.user, data=payload, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.first_name, "NewFirst")
        self.assertEqual(user.last_name, "NewLast")
        self.assertEqual(user.language, "fr")
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password("OldPass123!"))

    def test_admin_update_serializer_updates_password_when_provided(self):
        payload = {"password": "BrandNewPass123!"}
        serializer = CustomUserAdminUpdateSerializer(instance=self.user, data=payload, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertTrue(user.check_password("BrandNewPass123!"))
        self.assertFalse(user.check_password("OldPass123!"))
        self.assertTrue(user.must_change_password)

    def test_admin_update_serializer_can_clear_password_change_required(self):
        self.user.must_change_password = True
        self.user.save(update_fields=["must_change_password"])

        serializer = CustomUserAdminUpdateSerializer(
            instance=self.user,
            data={"password_change_required": False},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertFalse(user.must_change_password)

    def test_admin_update_serializer_validates_password(self):
        with patch("customuser.serializers.validate_password") as mock_validate:
            serializer = CustomUserAdminUpdateSerializer(
                instance=self.user,
                data={"password": "BrandNewPass123!"},
                partial=True,
            )
            self.assertTrue(serializer.is_valid(), serializer.errors)
            mock_validate.assert_called_once_with("BrandNewPass123!", user=self.user)


class QuizSimpleSerializerTests(TestCase):
    def test_quiz_simple_serializer_reads_title_from_quiz_template(self):
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
