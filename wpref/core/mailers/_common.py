import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from core.models import OutboundEmail

logger = logging.getLogger(__name__)


def frontend_url(path: str) -> str:
    return f"{settings.FRONTEND_BASE_URL.rstrip('/')}/{path.lstrip('/')}"


def build_user_token_link(path_prefix: str, user) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return frontend_url(f"{path_prefix.rstrip('/')}/{uid}/{token}")


def format_datetime(value) -> str:
    if not value:
        return ""
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M:%S %Z")


def queue_plaintext_email(subject: str, body: str, recipients: list[str]) -> None:
    to = [email for email in recipients if email]
    if not to:
        return
    OutboundEmail.objects.create(subject=subject, body=body, recipients=to)
    logger.info("email.enqueued", extra={"subject": subject, "recipients": to})


def send_plaintext_email(subject: str, body: str, recipients: list[str]) -> None:
    queue_plaintext_email(subject, body, recipients)
