from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

if TYPE_CHECKING:
    from .models import Quiz, QuizAlertMessage, QuizAlertThread, QuizQuestion


def assignment_alert_copy(language: str | None) -> dict[str, str]:
    code = (language or "en").lower()
    if code == "fr":
        return {
            "title": "Nouveau quiz assigne",
            "body": "Un nouveau quiz vous a ete assigne.",
        }
    if code == "nl":
        return {
            "title": "Nieuwe quiz toegewezen",
            "body": "Er werd een nieuwe quiz aan u toegewezen.",
        }
    return {
        "title": "New assigned quiz",
        "body": "A new quiz has been assigned to you.",
    }


def is_alert_participant(thread: "QuizAlertThread", user) -> bool:
    return bool(user and user.is_authenticated and user.id in {thread.reporter_id, thread.owner_id})


def is_alert_owner(thread: "QuizAlertThread", user) -> bool:
    return bool(user and user.is_authenticated and user.id == thread.owner_id)


def is_alert_reporter(thread: "QuizAlertThread", user) -> bool:
    return bool(user and user.is_authenticated and user.id == thread.reporter_id)


def can_manage_alert(thread: "QuizAlertThread", user) -> bool:
    return is_alert_owner(thread, user)


def can_reply_to_alert(thread: "QuizAlertThread", user) -> bool:
    if not is_alert_participant(thread, user):
        return False
    if thread.status != thread.STATUS_OPEN:
        return False
    if is_alert_owner(thread, user):
        return True
    return thread.reporter_reply_allowed


def participant_last_read_at(thread: "QuizAlertThread", user):
    if is_alert_owner(thread, user):
        return thread.owner_last_read_at
    if is_alert_reporter(thread, user):
        return thread.reporter_last_read_at
    return None


def unread_messages_queryset(thread: "QuizAlertThread", user):
    if not is_alert_participant(thread, user):
        return thread.messages.none()

    queryset = thread.messages.exclude(author_id=user.id)
    last_read_at = participant_last_read_at(thread, user)
    if last_read_at is not None:
        queryset = queryset.filter(created_at__gt=last_read_at)
    return queryset


def unread_count_for_alert(thread: "QuizAlertThread", user) -> int:
    return unread_messages_queryset(thread, user).count()


def is_alert_unread(thread: "QuizAlertThread", user) -> bool:
    return unread_messages_queryset(thread, user).exists()


def mark_alert_read(thread: "QuizAlertThread", user, *, at=None, save=True) -> None:
    if not is_alert_participant(thread, user):
        return

    at = at or timezone.now()
    fields: list[str] = []
    if is_alert_owner(thread, user):
        thread.owner_last_read_at = at
        fields.append("owner_last_read_at")
    elif is_alert_reporter(thread, user):
        thread.reporter_last_read_at = at
        fields.append("reporter_last_read_at")

    if save and fields:
        thread.save(update_fields=fields)


def message_is_mine(message: "QuizAlertMessage", user) -> bool:
    return bool(user and user.is_authenticated and message.author_id == user.id)


def message_is_unread_for_user(message: "QuizAlertMessage", user) -> bool:
    if not user or not user.is_authenticated or message.author_id == user.id:
        return False
    last_read_at = participant_last_read_at(message.thread, user)
    return last_read_at is None or message.created_at > last_read_at


def alert_last_message_preview(thread: "QuizAlertThread") -> str:
    message = next(iter(getattr(thread, "prefetched_messages", []) or []), None)
    if message is None:
        message = thread.messages.order_by("-created_at").first()
    if message is None:
        return ""
    return (message.body or "").strip()[:120]


def alert_thread_queryset():
    from .models import QuizAlertThread

    return (
        QuizAlertThread.objects
        .select_related(
            "quiz",
            "quiz__quiz_template",
            "quizquestion",
            "quizquestion__question",
            "reporter",
            "owner",
            "closed_by",
        )
        .prefetch_related("messages__author")
        .order_by("-last_message_at", "-created_at")
    )


def alert_thread_queryset_for_user(user):
    queryset = alert_thread_queryset()
    if user.is_staff or user.is_superuser:
        return queryset
    return queryset.filter(models.Q(reporter=user) | models.Q(owner=user))


def unread_total_for_queryset(queryset, user) -> int:
    return sum(unread_count_for_alert(thread, user) for thread in queryset)


def require_alert_owner(thread: "QuizAlertThread", user, action_label: str) -> None:
    if not is_alert_owner(thread, user):
        raise PermissionDenied(f"Seul le créateur du quiz peut {action_label} cette conversation.")


def create_alert_thread(*, reporter, quiz: "Quiz", quizquestion: "QuizQuestion", owner, body: str, language: str, now=None):
    from .models import QuizAlertMessage, QuizAlertThread

    now = now or timezone.now()
    thread = QuizAlertThread.objects.create(
        quiz=quiz,
        kind=QuizAlertThread.KIND_QUESTION,
        quizquestion=quizquestion,
        reporter=reporter,
        owner=owner,
        reported_language=str(language),
        last_message_at=now,
        reporter_last_read_at=now,
    )
    QuizAlertMessage.objects.create(
        thread=thread,
        author=reporter,
        body=body.strip(),
    )
    return thread


def create_assignment_alert_thread(*, reporter, quiz: "Quiz", owner, link: str, now=None):
    from .models import QuizAlertMessage, QuizAlertThread

    now = now or timezone.now()
    language = getattr(reporter, "language", None)
    copy = assignment_alert_copy(language)
    body = f"{copy['body']}\n{link}".strip()
    thread = QuizAlertThread.objects.create(
        quiz=quiz,
        kind=QuizAlertThread.KIND_ASSIGNMENT,
        quizquestion=None,
        reporter=reporter,
        owner=owner,
        reported_language=str(language or "en"),
        last_message_at=now,
        owner_last_read_at=now,
    )
    QuizAlertMessage.objects.create(
        thread=thread,
        author=owner,
        body=body,
    )
    return thread


def append_alert_message(*, thread: "QuizAlertThread", author, body: str, now=None):
    from .models import QuizAlertMessage

    now = now or timezone.now()
    message = QuizAlertMessage.objects.create(
        thread=thread,
        author=author,
        body=body.strip(),
    )

    thread.last_message_at = message.created_at
    if is_alert_owner(thread, author):
        thread.owner_last_read_at = now
    elif is_alert_reporter(thread, author):
        thread.reporter_last_read_at = now

    thread.save(update_fields=["last_message_at", "owner_last_read_at", "reporter_last_read_at"])
    return message
