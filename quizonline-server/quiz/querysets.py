from __future__ import annotations

from django.db.models import Count, FloatField, Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from config.domain_access import manageable_domain_ids
from django.utils import timezone

from .models import Quiz, QuizQuestion, QuizQuestionAnswer, QuizTemplate


def quiz_template_queryset():
    return (
        QuizTemplate.objects
        .select_related("domain")
        .annotate(_questions_count=Count("questions", distinct=True))
        .prefetch_related("quiz_questions__question")
        .order_by("title", "pk")
    )


def available_quiz_template_filter(*, at=None) -> Q:
    if at is None:
        at = timezone.now()
    return Q(active=True) & (
        Q(permanent=True)
        | (
            Q(started_at__lte=at)
            & (Q(ended_at__isnull=True) | Q(ended_at__gte=at))
        )
    )


def accessible_quiz_template_queryset(user):
    queryset = quiz_template_queryset()
    available_filter = available_quiz_template_filter()
    if not user or not getattr(user, "is_authenticated", False):
        return queryset.filter(is_public=True).filter(available_filter)
    if user.is_superuser:
        return queryset

    manageable_ids = manageable_domain_ids(user)
    if manageable_ids:
        return queryset.filter(domain_id__in=manageable_ids).distinct().order_by("title", "pk")

    # Use a subquery instead of a JOIN on the (potentially large) Quiz table
    assigned_template_ids = (
        Quiz.objects.filter(user=user).values("quiz_template_id").distinct()
    )
    started_exam_template_ids = (
        Quiz.objects
        .filter(user=user, quiz_template__mode=QuizTemplate.MODE_EXAM)
        .exclude(started_at__isnull=True, ended_at__isnull=True)
        .values("quiz_template_id")
        .distinct()
    )
    return (
        queryset
        .filter(available_filter)
        .filter(Q(is_public=True) | Q(pk__in=assigned_template_ids))
        .exclude(pk__in=started_exam_template_ids)
        .distinct()
        .order_by("title", "pk")
    )


def quiz_queryset_for_user(user, *, include_details: bool, include_manageable_templates: bool = False):
    queryset = (
        Quiz.objects
        .select_related("quiz_template", "user")
        .annotate(
            _earned_score=Coalesce(Sum("answers__earned_score"), 0.0, output_field=FloatField()),
            _max_score=Coalesce(Sum("answers__max_score"), 0.0, output_field=FloatField()),
        )
        .order_by("-created_at", "-id")
    )
    if include_details:
        quiz_questions_prefetch = Prefetch(
            "quiz_template__quiz_questions",
            queryset=QuizQuestion.objects.select_related("question").prefetch_related(
                "question__answer_options",
                "question__media__asset",
                "question__subjects",
            ),
        )
        queryset = queryset.prefetch_related(
            "answers__selected_options",
            "answers__quizquestion__question__answer_options",
            quiz_questions_prefetch,
        )
    if user.is_staff or user.is_superuser:
        return queryset
    if include_manageable_templates:
        manageable_ids = manageable_domain_ids(user)
        if manageable_ids:
            return queryset.filter(
                Q(user=user) | Q(quiz_template__domain_id__in=manageable_ids)
            ).distinct()
    return queryset.filter(user=user)


def template_sessions_queryset(quiz_template):
    return (
        quiz_template.quiz
        .select_related("user", "quiz_template")
        .prefetch_related("answers__selected_options")
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
