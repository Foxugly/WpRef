from __future__ import annotations

from collections.abc import Iterable
from django.db import transaction

from core.mailers import send_quiz_assignment_email, send_quiz_completed_email

from .alerting import create_assignment_alert_thread


def notify_quiz_assigned(quiz, *, assigned_by=None) -> None:
    send_quiz_assignment_email(quiz)
    user = getattr(quiz, "user", None)
    owner = assigned_by or getattr(getattr(quiz, "quiz_template", None), "created_by", None)
    if not user or not owner or owner.id == user.id:
        return
    create_assignment_alert_thread(
        reporter=user,
        quiz=quiz,
        owner=owner,
    )


def notify_quizzes_assigned(quizzes: Iterable, *, assigned_by=None) -> None:
    for quiz in quizzes:
        notify_quiz_assigned(quiz, assigned_by=assigned_by)


def notify_quiz_completed(quiz) -> None:
    send_quiz_completed_email(quiz)


def notify_quiz_assigned_on_commit(quiz, *, assigned_by=None) -> None:
    transaction.on_commit(lambda: notify_quiz_assigned(quiz, assigned_by=assigned_by))


def notify_quizzes_assigned_on_commit(quizzes: Iterable, *, assigned_by=None) -> None:
    quizzes = tuple(quizzes)
    transaction.on_commit(lambda: notify_quizzes_assigned(quizzes, assigned_by=assigned_by))


def notify_quiz_completed_on_commit(quiz) -> None:
    transaction.on_commit(lambda: notify_quiz_completed(quiz))
