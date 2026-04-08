from __future__ import annotations


def compute_answer_score(answer) -> tuple[float, float, bool]:
    """
    Calcule (earned_score, max_score, is_correct) pour une QuizQuestionAnswer.
    Suppose que answer_options et selected_options sont prefetch_related.
    """
    correct_ids = {
        opt.id for opt in answer.quizquestion.question.answer_options.all()
        if opt.is_correct
    }
    selected_ids = {opt.id for opt in answer.selected_options.all()}
    weight = float(answer.quizquestion.weight or 0)
    is_correct = bool(correct_ids and selected_ids == correct_ids)
    earned_score = weight if is_correct else 0.0
    return earned_score, weight, is_correct
