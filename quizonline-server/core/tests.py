from unittest.mock import MagicMock, patch

from kombu.exceptions import OperationalError

from django.core.exceptions import ValidationError
from django.conf import settings
from django.test import TestCase
from django.core import mail

from core.mailers import send_password_reset_email, send_quiz_assignment_email
from core.models import OutboundEmail
from customuser.models import CustomUser
from domain.models import Domain
from quiz.models import Quiz, QuizTemplate


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
        self.assertEqual(outbound.subject, f"{settings.NAME_APP} - password reset")

    def test_outbound_email_rejects_invalid_recipients_payload(self):
        with self.assertRaises(ValidationError) as ctx:
            OutboundEmail.objects.create(
                subject="Invalid",
                body="Body",
                recipients=["valid@example.com", "not-an-email", 123],
            )

        self.assertIn("recipients", ctx.exception.message_dict)

    @patch("core.mailers._common.transaction.on_commit")
    def test_send_password_reset_email_registers_automatic_delivery(self, on_commit):
        user = CustomUser.objects.create_user(
            username="mail-user-2",
            password="Pass1234!",
            email="mail-user-2@example.com",
        )

        send_password_reset_email(user)

        self.assertTrue(OutboundEmail.objects.filter(recipients=["mail-user-2@example.com"]).exists())
        on_commit.assert_called_once()

    def test_password_reset_email_uses_recipient_language(self):
        user = CustomUser.objects.create_user(
            username="mail-user-nl",
            password="Pass1234!",
            email="mail-user-nl@example.com",
            language="nl",
        )

        send_password_reset_email(user)

        outbound = OutboundEmail.objects.order_by("-id").first()
        self.assertEqual(outbound.subject, f"{settings.NAME_APP} - wachtwoord opnieuw instellen")
        self.assertIn("Hallo", outbound.body)

    def test_quiz_assignment_email_localizes_subject_and_deadline(self):
        owner = CustomUser.objects.create_user(username="owner", password="Pass1234!")
        user = CustomUser.objects.create_user(
            username="quiz-user",
            password="Pass1234!",
            email="quiz-user@example.com",
            language="fr",
        )
        domain = Domain.objects.create(owner=owner, name="Domaine", description="", active=True)
        template = QuizTemplate.objects.create(
            domain=domain,
            title="Quiz FR",
            permanent=True,
            active=True,
            created_by=owner,
        )
        quiz = Quiz.objects.create(quiz_template=template, user=user, active=True)

        send_quiz_assignment_email(quiz)

        outbound = OutboundEmail.objects.order_by("-id").first()
        self.assertEqual(outbound.subject, f"{settings.NAME_APP} - nouveau quiz a completer")
        self.assertIn("Bonjour", outbound.body)
        self.assertIn("Lien", outbound.body)

    @patch("core.mailers._common.transaction.on_commit", side_effect=lambda callback: callback())
    @patch("core.tasks.deliver_outbound_emails_task.delay", side_effect=OperationalError("broker down"))
    def test_send_password_reset_email_tolerates_broker_dispatch_failure(self, _delay, _on_commit):
        user = CustomUser.objects.create_user(
            username="mail-user-broker",
            password="Pass1234!",
            email="mail-user-broker@example.com",
        )

        send_password_reset_email(user)

        outbound = OutboundEmail.objects.get(recipients=["mail-user-broker@example.com"])
        self.assertIsNotNone(outbound.sent_at)
        self.assertEqual(len(mail.outbox), 1)

    @patch("core.mailers._common.transaction.on_commit", side_effect=lambda callback: callback())
    @patch("core.tasks.deliver_outbound_emails_task.delay", side_effect=OperationalError("broker down"))
    @patch("core.delivery.logger.warning")
    def test_send_password_reset_email_logs_and_falls_back_when_broker_is_down(
        self,
        logger_warning: MagicMock,
        _delay,
        _on_commit,
    ):
        user = CustomUser.objects.create_user(
            username="mail-user-broker-log",
            password="Pass1234!",
            email="mail-user-broker-log@example.com",
        )

        send_password_reset_email(user)

        logger_warning.assert_called()
        outbound = OutboundEmail.objects.get(recipients=["mail-user-broker-log@example.com"])
        self.assertIsNotNone(outbound.sent_at)
