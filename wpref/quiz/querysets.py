from __future__ import annotations

from django.db.models import Q
from wpref.domain_access import manageable_domain_ids, visible_domain_ids

from .models import Quiz, QuizQuestionAnswer, QuizTemplate


def quiz_template_queryset():
    return QuizTemplate.objects.all().prefetch_related("quiz_questions__question")


def accessible_quiz_template_queryset(user):
    queryset = quiz_template_queryset()
    if not user or not getattr(user, "is_authenticated", False):
        return queryset.filter(is_public=True)
    if user.is_superuser:
        return queryset

    allowed_domain_ids = visible_domain_ids(user)
    manageable_ids = manageable_domain_ids(user)
    public_filter = Q(is_public=True, domain__isnull=True)
    if allowed_domain_ids:
        public_filter |= Q(is_public=True, domain_id__in=allowed_domain_ids)

    return queryset.filter(
        Q(domain_id__in=manageable_ids)
        | Q(created_by_id=user.id)
        | Q(quiz__user=user)
        | public_filter
    ).distinct()


def quiz_queryset_for_user(user, *, include_details: bool):
    queryset = Quiz.objects.select_related("quiz_template", "user").order_by("-created_at", "-id")
    if include_details:
        queryset = queryset.prefetch_related(
            "answers__selected_options",
            "quiz_template__quiz_questions__question__answer_options",
            "quiz_template__quiz_questions__question__media__asset",
            "quiz_template__quiz_questions__question__subjects",
        )
    if user.is_staff or user.is_superuser:
        return queryset
    return queryset.filter(user=user)


def template_sessions_queryset(quiz_template):
    return (
        quiz_template.quiz
        .select_related("user", "quiz_template")
        .prefetch_related("answers")
        .order_by("-created_at", "-id")
    )


def quiz_answer_queryset_for_user(user, quiz_id: int):
    queryset = (
        QuizQuestionAnswer.objects
        .select_related("quiz", "quizquestion__question")
        .prefetch_related("selected_options")
        .filter(quiz_id=quiz_id)
    )
    if user.is_staff or user.is_superuser:
        return queryset
    return queryset.filter(quiz__user=user)
