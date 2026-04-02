from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from .models import Quiz, QuizQuestionAnswer
from .notifications import (
    notify_quiz_assigned_on_commit,
    notify_quiz_completed_on_commit,
)

# Backward-compatible names still referenced by some tests and patch points.
notify_quiz_assigned = notify_quiz_assigned_on_commit
notify_quiz_completed = notify_quiz_completed_on_commit


def create_quizzes_from_template(*, quiz_template, users, validate_target_user) -> list[Quiz]:
    created: list[Quiz] = []
    with transaction.atomic():
        for user in users:
            validate_target_user(quiz_template, user)
            quiz = Quiz.objects.create(
                domain=quiz_template.domain,
                quiz_template=quiz_template,
                user=user,
                active=False,
            )
            created.append(quiz)
            notify_quiz_assigned(quiz)
    return created


def close_quiz_session(*, quiz) -> Quiz:
    quiz_questions = list(
        quiz.quiz_template.quiz_questions
        .select_related("question")
        .prefetch_related("question__answer_options")
        .order_by("sort_order", "id")
    )

    existing_answer_ids = set(quiz.answers.values_list("quizquestion_id", flat=True))
    missing_answers = []
    for quiz_question in quiz_questions:
        if quiz_question.id in existing_answer_ids:
            continue
        missing_answers.append(
            QuizQuestionAnswer(
                quiz=quiz,
                quizquestion=quiz_question,
                question_order=quiz_question.sort_order,
            )
        )
    if missing_answers:
        QuizQuestionAnswer.objects.bulk_create(missing_answers)

    answers = (
        quiz.answers
        .select_related("quizquestion__question")
        .prefetch_related(
            "selected_options",
            "quizquestion__question__answer_options",
        )
    )

    to_update = []
    for answer in answers:
        correct_ids = {
            option.id for option in answer.quizquestion.question.answer_options.all()
            if option.is_correct
        }
        selected_ids = {option.id for option in answer.selected_options.all()}
        weight = float(answer.quizquestion.weight or 0)
        answer.max_score = weight

        if correct_ids and selected_ids == correct_ids:
            answer.earned_score = weight
            answer.is_correct = True
        else:
            answer.earned_score = 0.0
            answer.is_correct = False

        to_update.append(answer)

    if to_update:
        QuizQuestionAnswer.objects.bulk_update(
            to_update,
            ["earned_score", "max_score", "is_correct"],
        )

    quiz.active = False
    if not quiz.ended_at:
        quiz.ended_at = timezone.now()
    quiz.save(update_fields=["active", "ended_at"])
    notify_quiz_completed(quiz)
    return quiz
