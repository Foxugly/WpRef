# quiz/tests/test_models.py
from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from domain.models import Domain
from question.models import Question, AnswerOption
from quiz.constants import VISIBILITY_IMMEDIATE, VISIBILITY_NEVER, VISIBILITY_SCHEDULED
from quiz.models import Quiz, QuizQuestion, QuizQuestionAnswer, QuizTemplate

User = get_user_model()


def make_domain(*, owner: User, name: str = "Domaine FR") -> Domain:
    d = Domain.objects.create(owner=owner, active=True)
    d.set_current_language("fr")
    d.name = name
    d.description = ""
    d.save()
    return d


def make_question(*, domain: Domain, title: str = "Q?") -> Question:
    """
    Question nécessite:
    - domain (FK non-null)
    - translations.title (obligatoire)
    """
    q = Question.objects.create(domain=domain)
    q.set_current_language("fr")
    q.title = title
    q.description = ""
    q.explanation = ""
    q.save()
    return q


def make_answer_option(*, question: Question, content: str, is_correct: bool, sort_order: int = 0) -> AnswerOption:
    """
    AnswerOption nécessite:
    - question FK
    - translations.content (obligatoire)
    """
    opt = AnswerOption.objects.create(question=question, is_correct=is_correct, sort_order=sort_order)
    opt.set_current_language("fr")
    opt.content = content
    opt.save()
    return opt


class QuizModelsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass123!")
        self.user = User.objects.create_user(username="u1", password="pass123!")
        self.domain = make_domain(owner=self.owner)

    # ------------------------------------------------------------------
    # QuizTemplate: __str__, Meta.ordering
    # ------------------------------------------------------------------
    def test_quiztemplate_str_and_ordering(self):
        qt = QuizTemplate.objects.create(title="Alpha", domain=self.domain)
        self.assertEqual(str(qt), "Alpha")
        self.assertEqual(QuizTemplate._meta.ordering, ["title"])

    # ------------------------------------------------------------------
    # QuizTemplate._make_unique_title + save() (title unique + slug)
    # ------------------------------------------------------------------
    def test_make_unique_title_appends_suffix_when_collision(self):
        QuizTemplate.objects.create(title="Mon Quiz", domain=self.domain)
        qt2 = QuizTemplate.objects.create(title="Mon Quiz", domain=self.domain)
        self.assertEqual(qt2.title, "Mon Quiz (1)")

        qt3 = QuizTemplate.objects.create(title="Mon Quiz", domain=self.domain)
        self.assertEqual(qt3.title, "Mon Quiz (2)")

    def test_make_unique_title_ignores_self_pk_on_update(self):
        qt = QuizTemplate.objects.create(title="Unique", domain=self.domain)
        old_title = qt.title
        qt.description = "changed"
        qt.save()
        qt.refresh_from_db()
        self.assertEqual(qt.title, old_title)

    def test_save_generates_slug_and_handles_slug_collision(self):
        qt1 = QuizTemplate.objects.create(title="Mon Super Quiz", domain=self.domain)
        self.assertTrue(qt1.slug)
        self.assertIn("mon-super-quiz", qt1.slug)

        # title collision => title suffix + slug différent
        qt2 = QuizTemplate.objects.create(title="Mon Super Quiz", domain=self.domain)
        self.assertNotEqual(qt1.slug, qt2.slug)

        # slug collision volontaire : on crée un quiz dont le slugify(title) retombe sur custom-slug
        qt3 = QuizTemplate.objects.create(title="Custom Slug", domain=self.domain)
        qt3.slug = "custom-slug"
        qt3.save()

        qt4 = QuizTemplate.objects.create(title="Custom Slug", domain=self.domain)
        # le 2e "Custom Slug" devient "Custom Slug (1)" au titre, slug distinct aussi
        self.assertNotEqual(qt3.slug, qt4.slug)

    # ------------------------------------------------------------------
    # QuizTemplate.questions_count, ordering questions/qquestions, slicing max_questions
    # ------------------------------------------------------------------
    def test_questions_count_and_get_ordered(self):
        qt = QuizTemplate.objects.create(title="QPool", domain=self.domain, max_questions=10)

        q1 = make_question(domain=self.domain, title="Q1")
        q2 = make_question(domain=self.domain, title="Q2")
        q3 = make_question(domain=self.domain, title="Q3")

        QuizQuestion.objects.create(quiz=qt, question=q2, sort_order=2, weight=1)
        QuizQuestion.objects.create(quiz=qt, question=q1, sort_order=1, weight=1)
        QuizQuestion.objects.create(quiz=qt, question=q3, sort_order=3, weight=1)

        self.assertEqual(qt.questions_count, 3)

        ordered_qquestions = list(qt.get_ordered_qquestions())
        self.assertEqual([qq.sort_order for qq in ordered_qquestions], [1, 2, 3])

        ordered_questions = list(qt.get_ordered_questions())
        self.assertEqual([q.pk for q in ordered_questions], [q1.pk, q2.pk, q3.pk])

    def test_get_ordered_questions_applies_max_questions_slice(self):
        qt = QuizTemplate.objects.create(title="Slice", domain=self.domain, max_questions=2)

        q1 = make_question(domain=self.domain, title="Q1")
        q2 = make_question(domain=self.domain, title="Q2")
        q3 = make_question(domain=self.domain, title="Q3")

        QuizQuestion.objects.create(quiz=qt, question=q1, sort_order=1, weight=1)
        QuizQuestion.objects.create(quiz=qt, question=q2, sort_order=2, weight=1)
        QuizQuestion.objects.create(quiz=qt, question=q3, sort_order=3, weight=1)

        ordered = list(qt.get_ordered_questions())
        self.assertEqual(len(ordered), 2)
        self.assertEqual([q.pk for q in ordered], [q1.pk, q2.pk])

    # ------------------------------------------------------------------
    # QuizTemplate.can_answer branches
    # ------------------------------------------------------------------
    def test_quiztemplate_can_answer_inactive_false(self):
        qt = QuizTemplate.objects.create(title="Inactive", domain=self.domain, active=False, permanent=True)
        self.assertFalse(qt.can_answer)

    def test_quiztemplate_can_answer_permanent_true(self):
        qt = QuizTemplate.objects.create(title="Perm", domain=self.domain, active=True, permanent=True)
        self.assertTrue(qt.can_answer)

    def test_quiztemplate_can_answer_not_permanent_started_at_none_false(self):
        qt = QuizTemplate.objects.create(title="Sched", domain=self.domain, active=True, permanent=False,
                                         started_at=None)
        self.assertFalse(qt.can_answer)

    def test_quiztemplate_can_answer_not_permanent_no_ended_at_true(self):
        qt = QuizTemplate.objects.create(
            title="OpenEnd",
            domain=self.domain,
            active=True,
            permanent=False,
            started_at=timezone.now() - timedelta(hours=1),
            ended_at=None,
        )
        self.assertTrue(qt.can_answer)

    def test_quiztemplate_can_answer_in_window_true_and_outside_false(self):
        now = timezone.now()
        qt = QuizTemplate.objects.create(
            title="Window",
            domain=self.domain,
            active=True,
            permanent=False,
            started_at=now - timedelta(minutes=30),
            ended_at=now + timedelta(minutes=30),
        )
        self.assertTrue(qt.can_answer)

        qt2 = QuizTemplate.objects.create(
            title="Past",
            domain=self.domain,
            active=True,
            permanent=False,
            started_at=now - timedelta(hours=2),
            ended_at=now - timedelta(hours=1),
        )
        self.assertFalse(qt2.can_answer)

    # ------------------------------------------------------------------
    # QuizTemplate.can_show_result + can_show_details
    # ------------------------------------------------------------------
    def test_can_show_result_practice_always_true(self):
        qt = QuizTemplate.objects.create(title="P", domain=self.domain, mode=QuizTemplate.MODE_PRACTICE)
        qt.result_visibility = VISIBILITY_NEVER
        qt.save()
        self.assertTrue(qt.can_show_result())

    def test_can_show_details_practice_always_true(self):
        qt = QuizTemplate.objects.create(title="PD", domain=self.domain, mode=QuizTemplate.MODE_PRACTICE)
        qt.detail_visibility = VISIBILITY_NEVER
        qt.save()
        self.assertTrue(qt.can_show_details())

    def test_exam_visibility_never_false(self):
        qt = QuizTemplate.objects.create(title="E1", domain=self.domain, mode=QuizTemplate.MODE_EXAM)
        qt.result_visibility = VISIBILITY_NEVER
        qt.detail_visibility = VISIBILITY_NEVER
        qt.save()
        self.assertFalse(qt.can_show_result())
        self.assertFalse(qt.can_show_details())

    def test_exam_visibility_immediate_true(self):
        qt = QuizTemplate.objects.create(title="E2", domain=self.domain, mode=QuizTemplate.MODE_EXAM)
        qt.result_visibility = VISIBILITY_IMMEDIATE
        qt.detail_visibility = VISIBILITY_IMMEDIATE
        qt.save()
        self.assertTrue(qt.can_show_result())
        self.assertTrue(qt.can_show_details())

    def test_exam_visibility_scheduled_requires_date_and_compares_when(self):
        now = timezone.now()
        qt = QuizTemplate.objects.create(title="E3", domain=self.domain, mode=QuizTemplate.MODE_EXAM)

        qt.result_visibility = VISIBILITY_SCHEDULED
        qt.result_available_at = None
        qt.save()
        self.assertFalse(qt.can_show_result(when=now))

        qt.result_available_at = now + timedelta(minutes=10)
        qt.save()
        self.assertFalse(qt.can_show_result(when=now))
        self.assertTrue(qt.can_show_result(when=now + timedelta(minutes=11)))

        qt.detail_visibility = VISIBILITY_SCHEDULED
        qt.detail_available_at = None
        qt.save()
        self.assertFalse(qt.can_show_details(when=now))

        qt.detail_available_at = now + timedelta(minutes=5)
        qt.save()
        self.assertFalse(qt.can_show_details(when=now))
        self.assertTrue(qt.can_show_details(when=now + timedelta(minutes=6)))

    # ------------------------------------------------------------------
    # QuizQuestion: __str__, ordering, unique constraints
    # ------------------------------------------------------------------
    def test_quizquestion_str_and_ordering(self):
        qt = QuizTemplate.objects.create(title="QQ", domain=self.domain)
        q = make_question(domain=self.domain, title="QX")
        qq = QuizQuestion.objects.create(quiz=qt, question=q, sort_order=7, weight=3)

        self.assertIn("ord:7", str(qq))
        self.assertIn("w:3", str(qq))
        self.assertEqual(QuizQuestion._meta.ordering, ["sort_order"])

    def test_quizquestion_unique_together_enforced(self):
        qt = QuizTemplate.objects.create(title="uniq", domain=self.domain)
        q = make_question(domain=self.domain, title="Q1")
        QuizQuestion.objects.create(quiz=qt, question=q, sort_order=1, weight=1)

        # 1) même (quiz, question) -> IntegrityError
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                QuizQuestion.objects.create(quiz=qt, question=q, sort_order=2, weight=1)

        # transaction OK après le rollback du savepoint
        q2 = make_question(domain=self.domain, title="Q2")

        # 2) même (quiz, sort_order) -> IntegrityError
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                QuizQuestion.objects.create(quiz=qt, question=q2, sort_order=1, weight=1)

    # ------------------------------------------------------------------
    # Quiz: __str__, start(), save() ended_at calc, can_answer branches
    # ------------------------------------------------------------------
    def test_quiz_str(self):
        qt = QuizTemplate.objects.create(title="T", domain=self.domain)
        quiz = Quiz.objects.create(quiz_template=qt, user=self.user, domain=self.domain)
        self.assertIn("Quiz", str(quiz))
        self.assertIn("T", str(quiz))

    def test_quiz_start_sets_active_and_started_at(self):
        qt = QuizTemplate.objects.create(title="Start", domain=self.domain)
        quiz = Quiz.objects.create(quiz_template=qt, user=self.user, domain=self.domain)

        self.assertFalse(quiz.active)
        self.assertIsNone(quiz.started_at)

        quiz.start()
        quiz.refresh_from_db()
        self.assertTrue(quiz.active)
        self.assertIsNotNone(quiz.started_at)

    def test_quiz_save_sets_ended_at_with_duration_and_template_end(self):
        now = timezone.now()
        qt = QuizTemplate.objects.create(
            title="Dur",
            domain=self.domain,
            with_duration=True,
            duration=10,
            ended_at=now + timedelta(minutes=5),  # template end plus tôt
        )
        quiz = Quiz.objects.create(quiz_template=qt, user=self.user, domain=self.domain)
        quiz.started_at = now
        quiz.save()
        quiz.refresh_from_db()
        self.assertEqual(quiz.ended_at, qt.ended_at)

    def test_quiz_save_sets_ended_at_with_duration_no_template_end(self):
        now = timezone.now()
        qt = QuizTemplate.objects.create(title="Dur2", domain=self.domain, with_duration=True, duration=10,
                                         ended_at=None)
        quiz = Quiz.objects.create(quiz_template=qt, user=self.user, domain=self.domain)
        quiz.started_at = now
        quiz.save()
        quiz.refresh_from_db()
        self.assertEqual(quiz.ended_at, now + timedelta(minutes=10))

    def test_quiz_save_does_not_set_ended_at_if_no_duration(self):
        now = timezone.now()
        qt = QuizTemplate.objects.create(title="NoDur", domain=self.domain, with_duration=False, duration=10)
        quiz = Quiz.objects.create(quiz_template=qt, user=self.user, domain=self.domain)
        quiz.started_at = now
        quiz.save()
        quiz.refresh_from_db()
        self.assertIsNone(quiz.ended_at)

    def test_quiz_can_answer_branches(self):
        now = timezone.now()
        qt = QuizTemplate.objects.create(title="CA", domain=self.domain, active=True, permanent=True)

        quiz = Quiz.objects.create(quiz_template=qt, user=self.user, domain=self.domain)

        quiz.active = False
        quiz.started_at = now
        quiz.save()
        self.assertFalse(quiz.can_answer)

        quiz.active = True
        quiz.started_at = None
        quiz.ended_at = None
        quiz.save()
        self.assertFalse(quiz.can_answer)

        qt.active = False
        qt.save()
        quiz.started_at = now
        quiz.save()
        self.assertFalse(quiz.can_answer)

        qt.active = True
        qt.save()
        quiz.ended_at = None
        quiz.save()
        self.assertTrue(quiz.can_answer)

        quiz.ended_at = now + timedelta(minutes=1)
        quiz.save()
        self.assertTrue(quiz.can_answer)

        quiz.ended_at = now - timedelta(minutes=1)
        quiz.save()
        self.assertFalse(quiz.can_answer)

    # ------------------------------------------------------------------
    # QuizQuestionAnswer: clean/save/full_clean, properties, uniqueness, compute_score
    # ------------------------------------------------------------------
    def _setup_quiz_for_answers(self, *, weight=2) -> tuple[Quiz, QuizQuestion]:
        qt = QuizTemplate.objects.create(title=f"Ans-{timezone.now().timestamp()}", domain=self.domain, permanent=True)
        q = make_question(domain=self.domain, title="ScoreQ")
        qq = QuizQuestion.objects.create(quiz=qt, question=q, sort_order=1, weight=weight)

        quiz = Quiz.objects.create(
            quiz_template=qt,
            user=self.user,
            domain=self.domain,
            active=True,
            started_at=timezone.now(),
        )
        return quiz, qq

    def test_quizquestionanswer_clean_blocks_if_quiz_cannot_answer(self):
        quiz, qq = self._setup_quiz_for_answers()
        quiz.active = False
        quiz.save()

        a = QuizQuestionAnswer(quiz=quiz, quizquestion=qq, question_order=1)
        with self.assertRaises(ValidationError):
            a.full_clean()

    def test_quizquestionanswer_save_calls_full_clean(self):
        quiz, qq = self._setup_quiz_for_answers()
        a = QuizQuestionAnswer(quiz=quiz, quizquestion=qq, question_order=1)
        a.save()
        self.assertIsNotNone(a.pk)

    def test_quizquestionanswer_properties_index_and_quiz_template(self):
        quiz, qq = self._setup_quiz_for_answers(weight=5)
        a = QuizQuestionAnswer.objects.create(quiz=quiz, quizquestion=qq, question_order=1)
        self.assertEqual(a.index, 1)  # sort_order
        self.assertEqual(a.quiz_template, quiz.quiz_template)

    def test_quizquestionanswer_uniqueness_constraints(self):
        quiz, qq = self._setup_quiz_for_answers()
        QuizQuestionAnswer.objects.create(quiz=quiz, quizquestion=qq, question_order=1)

        # 1) Unicité (quiz, quizquestion) -> ValidationError (détecté par full_clean())
        with self.assertRaises(ValidationError) as ctx1:
            QuizQuestionAnswer.objects.create(quiz=quiz, quizquestion=qq, question_order=2)
        self.assertIn("already exists", str(ctx1.exception).lower())

        # 2) Unicité (quiz, question_order) -> ValidationError aussi
        q2 = make_question(domain=self.domain, title="Q2")
        qt = quiz.quiz_template
        qq2 = QuizQuestion.objects.create(quiz=qt, question=q2, sort_order=2, weight=1)

        obj = QuizQuestionAnswer(quiz=quiz, quizquestion=qq2, question_order=1)  # même order que la 1ère réponse
        with self.assertRaises(ValidationError) as ctx2:
            obj.full_clean()
        self.assertIn("already exists", str(ctx2.exception).lower())

    def test_compute_score_correct_incorrect_and_no_correct_opts(self):
        quiz, qq = self._setup_quiz_for_answers(weight=3)
        q = qq.question

        o1 = make_answer_option(question=q, content="A", is_correct=True, sort_order=1)
        o2 = make_answer_option(question=q, content="B", is_correct=True, sort_order=2)
        o3 = make_answer_option(question=q, content="C", is_correct=False, sort_order=3)

        a = QuizQuestionAnswer.objects.create(quiz=quiz, quizquestion=qq, question_order=1)

        a.selected_options.set([o1, o2])
        earned, max_score = a.compute_score(save=True)
        a.refresh_from_db()
        self.assertEqual(max_score, 3.0)
        self.assertEqual(earned, 3.0)
        self.assertTrue(a.is_correct)

        a.selected_options.set([o1, o3])
        earned, max_score = a.compute_score(save=True)
        a.refresh_from_db()
        self.assertEqual(earned, 0.0)
        self.assertFalse(a.is_correct)

        # Edge: aucune option correcte => même si selected == set() => incorrect (len(correct_opts)==0)
        quiz2, qq2 = self._setup_quiz_for_answers(weight=2)
        q_empty = qq2.question
        make_answer_option(question=q_empty, content="X", is_correct=False, sort_order=1)
        make_answer_option(question=q_empty, content="Y", is_correct=False, sort_order=2)

        a2 = QuizQuestionAnswer.objects.create(quiz=quiz2, quizquestion=qq2, question_order=1)
        a2.selected_options.set([])
        earned2, max2 = a2.compute_score(save=True)
        a2.refresh_from_db()
        self.assertEqual(max2, 2.0)
        self.assertEqual(earned2, 0.0)
        self.assertFalse(a2.is_correct)

    def test_compute_score_save_false_does_not_persist(self):
        quiz, qq = self._setup_quiz_for_answers(weight=4)
        q = qq.question
        o1 = make_answer_option(question=q, content="A", is_correct=True, sort_order=1)
        # pour éviter le "len(correct_opts)==0" edge, on s’assure qu’il y a bien au moins 1 correct
        make_answer_option(question=q, content="B", is_correct=False, sort_order=2)

        a = QuizQuestionAnswer.objects.create(quiz=quiz, quizquestion=qq, question_order=1)
        a.selected_options.set([o1])

        earned, max_score = a.compute_score(save=False)
        self.assertEqual(earned, 4.0)
        self.assertEqual(max_score, 4.0)

        a_db = QuizQuestionAnswer.objects.get(pk=a.pk)
        self.assertEqual(a_db.earned_score, 0)
        self.assertEqual(a_db.max_score, 0)
        self.assertIsNone(a_db.is_correct)
