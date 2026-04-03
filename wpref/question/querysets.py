from __future__ import annotations

from question.models import Question
from wpref.domain_access import visible_domain_ids


def question_queryset():
    return (
        Question.objects
        .select_related("domain")
        .prefetch_related("subjects", "translations", "answer_options__translations", "media__asset")
    )


def accessible_question_queryset(user):
    queryset = question_queryset()
    if not user or not getattr(user, "is_authenticated", False):
        return queryset.none()
    if getattr(user, "is_superuser", False):
        return queryset

    allowed_domain_ids = visible_domain_ids(user)
    if not allowed_domain_ids:
        return queryset.none()

    return queryset.filter(domain_id__in=allowed_domain_ids).distinct()
