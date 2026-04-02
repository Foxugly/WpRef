from django.test import TestCase

from core.mailers import send_password_reset_email
from core.models import OutboundEmail
from customuser.models import CustomUser


class CoreMailerTests(TestCase):
    def test_send_password_reset_email_enqueues_outbound_email(self):
        user = CustomUser.objects.create_user(
            username="mail-user",
            password="Pass1234!",
            email="mail-user@example.com",
        )

        send_password_reset_email(user)

        outbound = OutboundEmail.objects.get()
        self.assertEqual(outbound.recipients, ["mail-user@example.com"])
        self.assertIn("reinitialisation du mot de passe", outbound.subject.lower())
