# quiz/tests/test_models.py
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from question.models import Question, AnswerOption
from quiz.constants import (
    VISIBILITY_IMMEDIATE,
    VISIBILITY_NEVER,
    VISIBILITY_SCHEDULED,
)
from quiz.models import QuizTemplate, QuizQuestion, Quiz, QuizQuestionAnswer

User = get_user_model()


class QuizModelsTestCase(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username="u1", password="u1pass")

        self.qt = QuizTemplate.objects.create(
            title="Mon Template",
            mode=QuizTemplate.MODE_EXAM,
            max_questions=10,
            permanent=True,
            active=True,
            with_duration=True,
            duration=10,
        )

        self.q1 = self._create_question("Q1")
        self.q2 = self._create_question("Q2")

        self.qq1 = QuizQuestion.objects.create(quiz=self.qt, question=self.q1, sort_order=1, weight=2)
        self.qq2 = QuizQuestion.objects.create(quiz=self.qt, question=self.q2, sort_order=2, weight=3)

        self.quiz = Quiz.objects.create(quiz_template=self.qt, user=self.u1, active=False)

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _create_question(self, title: str) -> Question:
        """
        Crée une question minimale + 2 options (1 correcte).
        ⚠️ Adapte si ton modèle Question a d'autres champs obligatoires.
        """
        q = Question.objects.create(
            title=title,
            description="desc",
            explanation="expl",
            active=True,
            allow_multiple_correct=False,
            is_mode_practice=True,
            is_mode_exam=True,
        )
        AnswerOption.objects.create(question=q, content="A", is_correct=True, sort_order=1)
        AnswerOption.objects.create(question=q, content="B", is_correct=False, sort_order=2)
        return q

    # ---------------------------------------------------------------------
    # QuizTemplate
    # ---------------------------------------------------------------------
    def test_quiztemplate_slug_is_generated_and_unique(self):
        qt1 = QuizTemplate.objects.create(title="Titre Unique", permanent=True, active=True)
        qt2 = QuizTemplate.objects.create(title="Titre Unique", permanent=True, active=True)

        self.assertTrue(qt1.slug)
        self.assertTrue(qt2.slug)
        self.assertNotEqual(qt1.slug, qt2.slug)

    def test_quiztemplate_questions_count(self):
        # qt a 2 quiz_questions => questions_count doit être 2
        self.assertEqual(self.qt.questions_count, 2)

    def test_quiztemplate_can_answer_permanent_active(self):
        self.qt.permanent = True
        self.qt.active = True
        self.qt.started_at = None
        self.qt.ended_at = None
        self.qt.save()

        self.assertTrue(self.qt.can_answer)

    def test_quiztemplate_can_answer_inactive(self):
        self.qt.active = False
        self.qt.save()
        self.assertFalse(self.qt.can_answer)

    def test_quiztemplate_can_answer_non_permanent_requires_started_at(self):
        self.qt.permanent = False
        self.qt.active = True
        self.qt.started_at = None
        self.qt.ended_at = None
        self.qt.save()
        self.assertFalse(self.qt.can_answer)

    def test_quiztemplate_can_answer_non_permanent_open_end(self):
        self.qt.permanent = False
        self.qt.active = True
        self.qt.started_at = timezone.now() - timedelta(hours=1)
        self.qt.ended_at = None
        self.qt.save()
        self.assertTrue(self.qt.can_answer)

    def test_quiztemplate_can_answer_non_permanent_window(self):
        now = timezone.now()
        self.qt.permanent = False
        self.qt.active = True
        self.qt.started_at = now - timedelta(hours=1)
        self.qt.ended_at = now + timedelta(hours=1)
        self.qt.save()
        self.assertTrue(self.qt.can_answer)

        self.qt.started_at = now - timedelta(hours=2)
        self.qt.ended_at = now - timedelta(hours=1)
        self.qt.save()
        self.assertFalse(self.qt.can_answer)

    def test_quiztemplate_can_show_result_practice_always_true(self):
        self.qt.mode = QuizTemplate.MODE_PRACTICE
        self.qt.result_visibility = VISIBILITY_NEVER
        self.qt.save()
        self.assertTrue(self.qt.can_show_result())

    def test_quiztemplate_can_show_result_exam_never(self):
        self.qt.mode = QuizTemplate.MODE_EXAM
        self.qt.result_visibility = VISIBILITY_NEVER
        self.qt.save()
        self.assertFalse(self.qt.can_show_result())

    def test_quiztemplate_can_show_result_exam_immediate(self):
        self.qt.mode = QuizTemplate.MODE_EXAM
        self.qt.result_visibility = VISIBILITY_IMMEDIATE
        self.qt.save()
        self.assertTrue(self.qt.can_show_result())

    def test_quiztemplate_can_show_result_exam_scheduled(self):
        now = timezone.now()
        self.qt.mode = QuizTemplate.MODE_EXAM
        self.qt.result_visibility = VISIBILITY_SCHEDULED

        self.qt.result_available_at = None
        self.qt.save()
        self.assertFalse(self.qt.can_show_result(now))

        self.qt.result_available_at = now + timedelta(minutes=10)
        self.qt.save()
        self.assertFalse(self.qt.can_show_result(now))

        self.qt.result_available_at = now - timedelta(minutes=10)
        self.qt.save()
        self.assertTrue(self.qt.can_show_result(now))

    def test_quiztemplate_can_show_details_practice_always_true(self):
        self.qt.mode = QuizTemplate.MODE_PRACTICE
        self.qt.detail_visibility = VISIBILITY_NEVER
        self.qt.save()
        self.assertTrue(self.qt.can_show_details())

    def test_quiztemplate_can_show_details_exam_scheduled(self):
        now = timezone.now()
        self.qt.mode = QuizTemplate.MODE_EXAM
        self.qt.detail_visibility = VISIBILITY_SCHEDULED

        self.qt.detail_available_at = None
        self.qt.save()
        self.assertFalse(self.qt.can_show_details(now))

        self.qt.detail_available_at = now + timedelta(minutes=5)
        self.qt.save()
        self.assertFalse(self.qt.can_show_details(now))

        self.qt.detail_available_at = now - timedelta(minutes=5)
        self.qt.save()
        self.assertTrue(self.qt.can_show_details(now))

    def test_quiztemplate_get_ordered_questions_respects_sort_order_and_max_questions(self):
        self.qt.max_questions = 1
        self.qt.save()

        ordered = list(self.qt.get_ordered_questions())
        self.assertEqual(len(ordered), 1)
        self.assertEqual(ordered[0].id, self.q1.id)

        self.qt.max_questions = 2
        self.qt.save()
        ordered2 = list(self.qt.get_ordered_questions())
        self.assertEqual([q.id for q in ordered2], [self.q1.id, self.q2.id])

    # ---------------------------------------------------------------------
    # Quiz
    # ---------------------------------------------------------------------
    def test_quiz_can_answer_requires_active_and_started_at(self):
        self.quiz.active = False
        self.quiz.started_at = timezone.now()
        self.quiz.save()
        self.assertFalse(self.quiz.can_answer)

        self.quiz.active = True
        self.quiz.started_at = None
        self.quiz.save()
        self.assertFalse(self.quiz.can_answer)

    def test_quiz_can_answer_false_if_template_cannot_answer(self):
        self.quiz.active = True
        self.quiz.started_at = timezone.now()
        self.quiz.save()

        self.assertTrue(self.quiz.can_answer)

        self.qt.active = False
        self.qt.save()

        self.quiz.refresh_from_db()
        self.assertFalse(self.quiz.can_answer)

    def test_quiz_save_sets_ended_at_when_with_duration(self):
        self.quiz.active = True
        self.quiz.started_at = timezone.now()
        self.quiz.ended_at = None
        self.quiz.save()

        self.quiz.refresh_from_db()
        self.assertIsNotNone(self.quiz.ended_at)

        expected_min = self.quiz.started_at + timedelta(minutes=self.qt.duration)
        # ended_at peut être exactement expected_min
        self.assertEqual(self.quiz.ended_at, expected_min)

    def test_quiz_save_caps_ended_at_by_template_ended_at(self):
        now = timezone.now()
        self.qt.with_duration = True
        self.qt.duration = 60
        self.qt.ended_at = now + timedelta(minutes=10)  # fin template avant la durée
        self.qt.save()

        quiz = Quiz.objects.create(quiz_template=self.qt, user=self.u1, active=True, started_at=now)
        quiz.refresh_from_db()

        # capped à template.ended_at
        self.assertEqual(quiz.ended_at, self.qt.ended_at)

    # ---------------------------------------------------------------------
    # QuizQuestionAnswer
    # ---------------------------------------------------------------------
    def test_answer_clean_blocks_when_quiz_cannot_answer(self):
        # quiz non répondable
        self.quiz.active = False
        self.quiz.started_at = timezone.now()
        self.quiz.save()

        a = QuizQuestionAnswer(
            quiz=self.quiz,
            quizquestion=self.qq1,
            question_order=1,
        )
        with self.assertRaises(ValidationError):
            a.full_clean()

    def test_answer_save_runs_full_clean(self):
        # quiz répondable
        self.quiz.active = True
        self.quiz.started_at = timezone.now()
        self.quiz.save()

        a = QuizQuestionAnswer(
            quiz=self.quiz,
            quizquestion=self.qq1,
            question_order=1,
        )
        # doit passer (full_clean dans save)
        a.save()
        self.assertIsNotNone(a.pk)

    def test_answer_compute_score_correct(self):
        self.quiz.active = True
        self.quiz.started_at = timezone.now()
        self.quiz.save()

        a = QuizQuestionAnswer.objects.create(
            quiz=self.quiz,
            quizquestion=self.qq1,
            question_order=1,
        )
        correct_option = self.q1.answer_options.get(is_correct=True)
        a.selected_options.set([correct_option])

        earned, max_score = a.compute_score(save=True)
        a.refresh_from_db()

        self.assertEqual(max_score, float(self.qq1.weight))
        self.assertEqual(earned, float(self.qq1.weight))
        self.assertTrue(a.is_correct)
        self.assertEqual(a.earned_score, float(self.qq1.weight))
        self.assertEqual(a.max_score, float(self.qq1.weight))

    def test_answer_compute_score_wrong(self):
        self.quiz.active = True
        self.quiz.started_at = timezone.now()
        self.quiz.save()

        a = QuizQuestionAnswer.objects.create(
            quiz=self.quiz,
            quizquestion=self.qq1,
            question_order=1,
        )
        wrong_option = self.q1.answer_options.get(is_correct=False)
        a.selected_options.set([wrong_option])

        earned, max_score = a.compute_score(save=True)
        a.refresh_from_db()

        self.assertEqual(max_score, float(self.qq1.weight))
        self.assertEqual(earned, 0.0)
        self.assertFalse(a.is_correct)
        self.assertEqual(a.earned_score, 0.0)
        self.assertEqual(a.max_score, float(self.qq1.weight))

    def test_answer_compute_score_no_correct_options_returns_wrong(self):
        """
        Cas limite : si une question n'a aucune option correcte,
        compute_score() doit donner earned=0 et is_correct=False (ton code le fait).
        """
        self.quiz.active = True
        self.quiz.started_at = timezone.now()
        self.quiz.save()

        q = self._create_question("Q3")
        # rendre toutes les options incorrectes
        q.answer_options.update(is_correct=False)

        qq = QuizQuestion.objects.create(quiz=self.qt, question=q, sort_order=3, weight=1)
        a = QuizQuestionAnswer.objects.create(quiz=self.quiz, quizquestion=qq, question_order=3)
        a.selected_options.set(list(q.answer_options.all()))

        earned, max_score = a.compute_score(save=True)
        a.refresh_from_db()

        self.assertEqual(max_score, 1.0)
        self.assertEqual(earned, 0.0)
        self.assertFalse(a.is_correct)
