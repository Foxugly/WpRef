from __future__ import annotations

from django.db.models import Q

from .models import Quiz, QuizQuestionAnswer, QuizTemplate


def quiz_template_queryset():
    return QuizTemplate.objects.all().prefetch_related("quiz_questions__question")


def accessible_quiz_template_queryset(user):
    queryset = quiz_template_queryset()
    if user.is_staff or user.is_superuser:
        return queryset

    public_filter = Q(is_public=True)
    if user.current_domain_id is not None:
        manageable_domain_ids = list(user.get_manageable_domains(active_only=False).values_list("id", flat=True))
        visible_domain_ids = {user.current_domain_id, *manageable_domain_ids}
        public_filter &= (Q(domain_id__in=visible_domain_ids) | Q(domain__isnull=True))

    return queryset.filter(Q(quiz__user=user) | public_filter).distinct()


def quiz_queryset_for_user(user, *, include_details: bool):
    queryset = Quiz.objects.select_related("quiz_template", "user")
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
