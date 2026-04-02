from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import OutboundEmail


class Command(BaseCommand):
    help = "Send queued outbound emails."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        limit = max(1, options["limit"])
        sent = 0

        while sent < limit:
            with transaction.atomic():
                email = (
                    OutboundEmail.objects
                    .select_for_update(skip_locked=True)
                    .filter(sent_at__isnull=True, available_at__lte=timezone.now())
                    .order_by("created_at", "id")
                    .first()
                )
                if email is None:
                    break

                email.mark_attempt()
                try:
                    send_mail(
                        email.subject,
                        email.body,
                        settings.DEFAULT_FROM_EMAIL,
                        email.recipients,
                        fail_silently=False,
                    )
                except Exception as exc:  # pragma: no cover - relies on SMTP failure
                    email.last_error = str(exc)
                    email.save(update_fields=["attempts", "last_error"])
                    self.stderr.write(f"FAILED {email.id}: {exc}")
                    continue

                email.sent_at = timezone.now()
                email.last_error = ""
                email.save(update_fields=["attempts", "sent_at", "last_error"])
                sent += 1
                self.stdout.write(f"SENT {email.id}")

        self.stdout.write(self.style.SUCCESS(f"Processed {sent} email(s)."))
