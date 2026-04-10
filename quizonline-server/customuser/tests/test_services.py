from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from customuser.services import change_password, confirm_password_reset

User = get_user_model()


class CustomUserServicesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="service-user",
            password="OldPass123!",
            email="service@example.com",
        )

    def test_change_password_revokes_refresh_tokens(self):
        with patch("customuser.services.revoke_user_refresh_tokens") as revoke_tokens:
            changed = change_password(self.user, "OldPass123!", "NewPass123!")

        self.assertTrue(changed)
        revoke_tokens.assert_called_once_with(self.user)

    def test_confirm_password_reset_revokes_refresh_tokens(self):
        with patch("customuser.services.resolve_user_from_uid", return_value=self.user), patch(
            "customuser.services.token_is_valid",
            return_value=True,
        ), patch("customuser.services.revoke_user_refresh_tokens") as revoke_tokens:
            user = confirm_password_reset("uid", "token", "AnotherPass123!")

        self.assertEqual(user, self.user)
        revoke_tokens.assert_called_once_with(self.user)
