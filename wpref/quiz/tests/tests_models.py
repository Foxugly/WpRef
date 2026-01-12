# quiz/tests/tests_models.py
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from domain.models import Domain
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

        # ✅ Domain obligatoire pour Question.domain (NOT NULL) + Domain.owner obligatoire
        self.domain = Domain.objects.create(
            owner=self.u1,
            name="Test domain",
            description="Test description",
            active=True,
        )

        self.qt = QuizTemplate.objects.create(
            domain=self.domain,  # nullable dans QuizTemplate, mais on le met pour cohérence
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
        ✅ Contrainte: Question.domain NOT NULL
        """
        q = Question.objects.create(
            domain=self.domain,
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
    def test_quiztemplate_str(self):
        self.assertEqual(str(self.qt), "Mon Template")

    def test_quiztemplate_slug_is_generated_and_unique(self):
        qt1 = QuizTemplate.objects.create(title="Titre Unique", permanent=True, active=True)
        qt2 = QuizTemplate.objects.create(title="Titre Unique", permanent=True, active=True)

        self.assertTrue(qt1.slug)
        self.assertTrue(qt2.slug)
        self.assertNotEqual(qt1.slug, qt2.slug)

    def test_quiztemplate_save_keeps_existing_slug(self):
        qt = QuizTemplate.objects.create(title="ABC", permanent=True, active=True, slug="custom-slug")
        self.assertEqual(qt.slug, "custom-slug")

        qt.title = "ABC changed"
        qt.save()
        qt.refresh_from_db()
        self.assertEqual(qt.slug, "custom-slug")

    def test_quiztemplate_make_unique_title_default_quiz_when_blank(self):
        qt = QuizTemplate(title="   ", permanent=True, active=True)
        qt.save()
        self.assertTrue(qt.title.startswith("Quiz"))
        self.assertTrue(qt.slug)

    def test_quiztemplate_make_unique_title_excludes_self_on_update(self):
        qt = QuizTemplate.objects.create(title="SameTitle", permanent=True, active=True)
        qt.title = "SameTitle"
        qt.save()
        qt.refresh_from_db()
        self.assertEqual(qt.title, "SameTitle")

    def test_quiztemplate_make_unique_title_adds_suffix_on_collision(self):
        qt1 = QuizTemplate.objects.create(title="Collision", permanent=True, active=True)
        qt2 = QuizTemplate.objects.create(title="Collision", permanent=True, active=True)
        self.assertNotEqual(qt1.title, qt2.title)
        self.assertTrue(qt2.title.startswith("Collision"))

    def test_quiztemplate_questions_count(self):
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

    def test_quiztemplate_get_ordered_qquestions(self):
        ordered = list(self.qt.get_ordered_qquestions())
        self.assertEqual([x.id for x in ordered], [self.qq1.id, self.qq2.id])

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

    def test_quiztemplate_get_ordered_questions_when_max_questions_zero_returns_all(self):
        self.qt.max_questions = 0
        self.qt.save()
        ordered = list(self.qt.get_ordered_questions())
        self.assertEqual([q.id for q in ordered], [self.q1.id, self.q2.id])

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

    def test_quiztemplate_can_show_details_exam_never_and_immediate(self):
        self.qt.mode = QuizTemplate.MODE_EXAM

        self.qt.detail_visibility = VISIBILITY_NEVER
        self.qt.save()
        self.assertFalse(self.qt.can_show_details())

        self.qt.detail_visibility = VISIBILITY_IMMEDIATE
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

    # ---------------------------------------------------------------------
    # QuizQuestion
    # ---------------------------------------------------------------------
    def test_quizquestion_str(self):
        self.assertEqual(str(self.qq1), f"Q{self.q1.id} (ord:1, w:2)")

    def test_quizquestion_unique_together_quiz_question(self):
        with self.assertRaises(IntegrityError):
            QuizQuestion.objects.create(quiz=self.qt, question=self.q1, sort_order=99, weight=1)

    def test_quizquestion_unique_together_quiz_sort_order(self):
        q3 = self._create_question("Q3")
        with self.assertRaises(IntegrityError):
            QuizQuestion.objects.create(quiz=self.qt, question=q3, sort_order=1, weight=1)

    # ---------------------------------------------------------------------
    # Quiz
    # ---------------------------------------------------------------------
    def test_quiz_str(self):
        self.assertIn("Quiz", str(self.quiz))
        self.assertIn("u1", str(self.quiz))
        self.assertIn("Mon Template", str(self.quiz))

    def test_quiz_start_sets_active_started_at_and_ended_at(self):
        self.assertFalse(self.quiz.active)
        self.assertIsNone(self.quiz.started_at)

        self.quiz.start()
        self.quiz.refresh_from_db()

        self.assertTrue(self.quiz.active)
        self.assertIsNotNone(self.quiz.started_at)
        self.assertIsNotNone(self.quiz.ended_at)

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

    def test_quiz_can_answer_false_when_ended_at_in_past(self):
        self.quiz.active = True
        self.quiz.started_at = timezone.now() - timedelta(minutes=30)
        self.quiz.ended_at = timezone.now() - timedelta(minutes=1)
        self.quiz.save()
        self.assertFalse(self.quiz.can_answer)

    def test_quiz_can_answer_true_when_ended_at_in_future(self):
        self.quiz.active = True
        self.quiz.started_at = timezone.now() - timedelta(minutes=1)
        self.quiz.ended_at = timezone.now() + timedelta(minutes=10)
        self.quiz.save()
        self.assertTrue(self.quiz.can_answer)

    def test_quiz_save_sets_ended_at_when_with_duration(self):
        self.quiz.active = True
        self.quiz.started_at = timezone.now()
        self.quiz.ended_at = None
        self.quiz.save()

        self.quiz.refresh_from_db()
        self.assertIsNotNone(self.quiz.ended_at)

        expected = self.quiz.started_at + timedelta(minutes=self.qt.duration)
        self.assertEqual(self.quiz.ended_at, expected)

    def test_quiz_save_does_not_set_ended_at_when_with_duration_false(self):
        self.qt.with_duration = False
        self.qt.save()

        quiz = Quiz.objects.create(quiz_template=self.qt, user=self.u1, active=True, started_at=timezone.now())
        quiz.refresh_from_db()
        self.assertIsNone(quiz.ended_at)

    def test_quiz_save_caps_ended_at_by_template_ended_at(self):
        now = timezone.now()
        self.qt.with_duration = True
        self.qt.duration = 60
        self.qt.ended_at = now + timedelta(minutes=10)
        self.qt.save()

        quiz = Quiz.objects.create(quiz_template=self.qt, user=self.u1, active=True, started_at=now)
        quiz.refresh_from_db()
        self.assertEqual(quiz.ended_at, self.qt.ended_at)

    def test_quiz_save_when_template_ended_at_is_none_uses_duration(self):
        now = timezone.now()
        self.qt.with_duration = True
        self.qt.duration = 7
        self.qt.ended_at = None
        self.qt.save()

        quiz = Quiz.objects.create(quiz_template=self.qt, user=self.u1, active=True, started_at=now)
        quiz.refresh_from_db()
        self.assertEqual(quiz.ended_at, now + timedelta(minutes=7))

    # ---------------------------------------------------------------------
    # QuizQuestionAnswer
    # ---------------------------------------------------------------------
    def test_answer_clean_returns_if_no_quiz_id(self):
        a = QuizQuestionAnswer(
            quiz=None,
            quizquestion=self.qq1,
            question_order=1,
        )
        a.clean()

    def test_answer_clean_blocks_when_quiz_cannot_answer(self):
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
        self.quiz.active = True
        self.quiz.started_at = timezone.now()
        self.quiz.save()

        a = QuizQuestionAnswer(
            quiz=self.quiz,
            quizquestion=self.qq1,
            question_order=1,
        )
        a.save()
        self.assertIsNotNone(a.pk)

    def test_answer_properties_index_and_quiz_template(self):
        self.quiz.active = True
        self.quiz.started_at = timezone.now()
        self.quiz.save()

        a = QuizQuestionAnswer.objects.create(
            quiz=self.quiz,
            quizquestion=self.qq1,
            question_order=1,
        )
        self.assertEqual(a.index, self.qq1.sort_order)
        self.assertEqual(a.quiz_template, self.quiz.quiz_template)

    def test_answer_unique_constraint_one_answer_per_quiz_question(self):
        self.quiz.active = True
        self.quiz.started_at = timezone.now()
        self.quiz.save()

        QuizQuestionAnswer.objects.create(quiz=self.quiz, quizquestion=self.qq1, question_order=1)

        with self.assertRaises(ValidationError) as ctx:
            QuizQuestionAnswer.objects.create(quiz=self.quiz, quizquestion=self.qq1, question_order=2)

        # Optionnel: vérifier le message (souple)
        self.assertIn("already exists", str(ctx.exception))

    def test_answer_unique_together_quiz_question_order(self):
        self.quiz.active = True
        self.quiz.started_at = timezone.now()
        self.quiz.save()

        QuizQuestionAnswer.objects.create(quiz=self.quiz, quizquestion=self.qq1, question_order=1)
        with self.assertRaises(ValidationError) as ctx:
            QuizQuestionAnswer.objects.create(quiz=self.quiz, quizquestion=self.qq2, question_order=1)

        self.assertIn("already exists", str(ctx.exception))

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

    def test_answer_compute_score_empty_selection_is_wrong(self):
        self.quiz.active = True
        self.quiz.started_at = timezone.now()
        self.quiz.save()

        a = QuizQuestionAnswer.objects.create(
            quiz=self.quiz,
            quizquestion=self.qq1,
            question_order=1,
        )
        a.selected_options.clear()

        earned, max_score = a.compute_score(save=True)
        a.refresh_from_db()

        self.assertEqual(max_score, float(self.qq1.weight))
        self.assertEqual(earned, 0.0)
        self.assertFalse(a.is_correct)

    def test_answer_compute_score_save_false_does_not_persist_fields(self):
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

        earned, max_score = a.compute_score(save=False)
        self.assertEqual(earned, float(self.qq1.weight))
        self.assertEqual(max_score, float(self.qq1.weight))
        self.assertTrue(a.is_correct)

        a_db = QuizQuestionAnswer.objects.get(pk=a.pk)
        self.assertEqual(a_db.earned_score, 0)
        self.assertEqual(a_db.max_score, 0)
        self.assertIsNone(a_db.is_correct)

    def test_answer_compute_score_no_correct_options_returns_wrong(self):
        self.quiz.active = True
        self.quiz.started_at = timezone.now()
        self.quiz.save()

        q = self._create_question("Q3")
        q.answer_options.update(is_correct=False)

        qq = QuizQuestion.objects.create(quiz=self.qt, question=q, sort_order=3, weight=1)
        a = QuizQuestionAnswer.objects.create(quiz=self.quiz, quizquestion=qq, question_order=3)
        a.selected_options.set(list(q.answer_options.all()))

        earned, max_score = a.compute_score(save=True)
        a.refresh_from_db()

        self.assertEqual(max_score, 1.0)
        self.assertEqual(earned, 0.0)
        self.assertFalse(a.is_correct)
