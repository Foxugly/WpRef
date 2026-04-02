import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def _frontend_url(path: str) -> str:
    return f"{settings.FRONTEND_BASE_URL.rstrip('/')}/{path.lstrip('/')}"


def _format_datetime(value) -> str:
    if not value:
        return ""
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M:%S %Z")


def _send_email(subject: str, body: str, recipients: list[str]) -> None:
    to = [email for email in recipients if email]
    if not to:
        return
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, to, fail_silently=False)
    except Exception:
        logger.exception("email.send.failed", extra={"subject": subject, "recipients": to})


def send_registration_confirmation_email(user) -> None:
    if not getattr(user, "email", None):
        return
    body = (
        f"Bonjour {user.get_display_name()},\n\n"
        "Votre inscription sur WpRef est confirmee.\n"
        f"Connexion : {_frontend_url('/login')}\n"
    )
    _send_email("WpRef - inscription confirmee", body, [user.email])


def send_quiz_assignment_email(quiz) -> None:
    user = getattr(quiz, "user", None)
    template = getattr(quiz, "quiz_template", None)
    if not user or not template or not getattr(user, "email", None):
        return
    deadline = template.ended_at or quiz.ended_at
    deadline_line = f"Deadline : {_format_datetime(deadline)}\n" if deadline else ""
    body = (
        f"Bonjour {user.get_display_name()},\n\n"
        f"Un quiz vous a ete assigne : {template.title}\n"
        f"{deadline_line}"
        f"Lien : {_frontend_url(f'/quiz/{quiz.id}')}\n"
    )
    _send_email("WpRef - nouveau quiz a completer", body, [user.email])


def send_quiz_completed_email(quiz) -> None:
    template = getattr(quiz, "quiz_template", None)
    creator = getattr(template, "created_by", None) if template else None
    user = getattr(quiz, "user", None)
    if not creator or not user or creator.id == user.id or not getattr(creator, "email", None):
        return
    body = (
        f"Bonjour {creator.get_display_name()},\n\n"
        f"{user.get_display_name()} a cloture le quiz \"{template.title}\".\n"
        f"Lien : {_frontend_url(f'/quiz/{quiz.id}')}\n"
    )
    _send_email("WpRef - quiz cloture", body, [creator.email])
