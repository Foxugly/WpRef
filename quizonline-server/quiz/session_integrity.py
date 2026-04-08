from __future__ import annotations

from quiz.models import Quiz, QuizQuestionAnswer
from quiz.scoring import compute_answer_score


def synchronize_closed_quiz_answers(quiz: Quiz) -> Quiz:
    if quiz.started_at is None or quiz.active:
        return quiz

    quiz_questions = list(
        quiz.quiz_template.quiz_questions
        .select_related("question")
        .prefetch_related("question__answer_options")
        .order_by("sort_order", "id")
    )

    existing_answers = list(
        quiz.answers
        .select_related("quizquestion__question")
        .prefetch_related(
            "selected_options",
            "quizquestion__question__answer_options",
        )
    )
    existing_answer_ids = {answer.quizquestion_id for answer in existing_answers}

    missing_answers = [
        QuizQuestionAnswer(
            quiz=quiz,
            quizquestion=quiz_question,
            question_order=quiz_question.sort_order,
        )
        for quiz_question in quiz_questions
        if quiz_question.id not in existing_answer_ids
    ]
    if missing_answers:
        QuizQuestionAnswer.objects.bulk_create(missing_answers)
        existing_answers = list(
            quiz.answers
            .select_related("quizquestion__question")
            .prefetch_related(
                "selected_options",
                "quizquestion__question__answer_options",
            )
        )

    to_update = []
    for answer in existing_answers:
        earned_score, max_score, is_correct = compute_answer_score(answer)
        if (
            float(answer.max_score or 0) != max_score
            or float(answer.earned_score or 0) != earned_score
            or answer.is_correct != is_correct
        ):
            answer.max_score = max_score
            answer.earned_score = earned_score
            answer.is_correct = is_correct
            to_update.append(answer)

    if to_update:
        QuizQuestionAnswer.objects.bulk_update(
            to_update,
            ["earned_score", "max_score", "is_correct"],
        )

    if hasattr(quiz, "_prefetched_objects_cache"):
        quiz._prefetched_objects_cache = {}
    if hasattr(quiz, "_answers_cache"):
        delattr(quiz, "_answers_cache")

    return quiz
