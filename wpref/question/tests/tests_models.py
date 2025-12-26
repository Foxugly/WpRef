# question/tests/test_models.py
import logging

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from question.models import Question, AnswerOption, QuestionMedia, QuestionSubject
from subject.models import Subject

logger = logging.getLogger(__name__)


class QuestionModelsTestCase(TestCase):
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _make_subject(self, name="Math", slug="math") -> Subject:
        return Subject.objects.create(name=name, slug=slug)

    def _make_question(self, title="Q1", *, allow_multiple_correct=False) -> Question:
        return Question.objects.create(
            title=title,
            description="desc",
            explanation="expl",
            allow_multiple_correct=allow_multiple_correct,
            active=True,
            is_mode_practice=True,
            is_mode_exam=True,
        )

    def _add_option(self, q: Question, *, is_correct: bool, sort_order: int, content="opt") -> AnswerOption:
        return AnswerOption.objects.create(
            question=q,
            content=content,
            is_correct=is_correct,
            sort_order=sort_order,
        )

    def _validate_question(self, q: Question):
        """
        Question.clean() inspecte q.answer_options.all()
        Donc on appelle q.clean() (ou q.full_clean() si tu préfères).
        """
        q.clean()

    # ------------------------------------------------------------------
    # Question.clean() rules
    # ------------------------------------------------------------------
    def test_question_clean_requires_at_least_two_answer_options(self):
        q = self._make_question("Q-min-opts")

        # 0 option
        with self.assertRaises(ValidationError) as ctx0:
            self._validate_question(q)
        self.assertIn("au moins 2", str(ctx0.exception).lower())

        # 1 option
        self._add_option(q, is_correct=True, sort_order=1)
        with self.assertRaises(ValidationError) as ctx1:
            self._validate_question(q)
        self.assertIn("au moins 2", str(ctx1.exception).lower())

    def test_question_clean_requires_at_least_one_correct(self):
        q = self._make_question("Q-no-correct")
        self._add_option(q, is_correct=False, sort_order=1)
        self._add_option(q, is_correct=False, sort_order=2)

        with self.assertRaises(ValidationError) as ctx:
            self._validate_question(q)
        self.assertIn("au moins une", str(ctx.exception).lower())
        self.assertIn("correct", str(ctx.exception).lower())

    def test_question_clean_requires_exactly_one_correct_when_multiple_not_allowed(self):
        q = self._make_question("Q-one-correct-only", allow_multiple_correct=False)
        self._add_option(q, is_correct=True, sort_order=1)
        self._add_option(q, is_correct=True, sort_order=2)

        with self.assertRaises(ValidationError) as ctx:
            self._validate_question(q)
        self.assertIn("qu'une seule", str(ctx.exception).lower())

    def test_question_clean_allows_multiple_correct_when_flag_true(self):
        q = self._make_question("Q-multi-correct", allow_multiple_correct=True)
        self._add_option(q, is_correct=True, sort_order=1)
        self._add_option(q, is_correct=True, sort_order=2)

        # doit passer
        self._validate_question(q)

    def test_question_clean_passes_for_valid_single_correct(self):
        q = self._make_question("Q-valid", allow_multiple_correct=False)
        self._add_option(q, is_correct=True, sort_order=1)
        self._add_option(q, is_correct=False, sort_order=2)

        self._validate_question(q)

    # ------------------------------------------------------------------
    # AnswerOption ordering + __str__
    # ------------------------------------------------------------------
    def test_answeroption_ordering_sort_order_then_id(self):
        q = self._make_question("Q-ordering")
        o2 = self._add_option(q, is_correct=False, sort_order=2, content="B")
        o1 = self._add_option(q, is_correct=True, sort_order=1, content="A")

        ordered = list(q.answer_options.all())
        self.assertEqual(ordered[0].id, o1.id)
        self.assertEqual(ordered[1].id, o2.id)

        self.assertIn("Option(Q", str(o1))

    # ------------------------------------------------------------------
    # M2M subjects through QuestionSubject
    # ------------------------------------------------------------------
    def test_question_subject_add_creates_through_row(self):
        s = self._make_subject("History", "history")
        q = self._make_question("Q-subjects")

        q.subjects.add(s)  # crée QuestionSubject (through)
        self.assertEqual(q.subjects.count(), 1)
        self.assertEqual(QuestionSubject.objects.filter(question=q, subject=s).count(), 1)

        link = QuestionSubject.objects.get(question=q, subject=s)
        self.assertEqual(link.sort_order, 0)
        self.assertEqual(link.weight, 1)
        self.assertIn("↔", str(link))

    def test_questionsubject_unique_together_enforced(self):
        s = self._make_subject("Geo", "geo")
        q = self._make_question("Q-unique-link")

        QuestionSubject.objects.create(question=q, subject=s)
        with self.assertRaises(IntegrityError):
            QuestionSubject.objects.create(question=q, subject=s)

    def test_questionsubject_ordering(self):
        """
        ordering = ["-id"]
        """
        s1 = self._make_subject("Aaa", "aaa")
        s2 = self._make_subject("Bbb", "bbb")
        q = self._make_question("Q-order-subject")
        qs2 = QuestionSubject.objects.create(question=q, subject=s2, sort_order=0)
        qs1 = QuestionSubject.objects.create(question=q, subject=s1, sort_order=5)
        ordered = list(QuestionSubject.objects.all())
        # d'abord subject "Aaa" (qs1b puis qs1), ensuite "Bbb"
        self.assertEqual([x.id for x in ordered], [qs1.id, qs2.id])

    # ------------------------------------------------------------------
    # QuestionMedia.clean()
    # ------------------------------------------------------------------
    def test_questionmedia_clean_requires_file_or_external_url(self):
        q = self._make_question("Q-media")

        m = QuestionMedia(question=q, kind=QuestionMedia.IMAGE, file=None, external_url=None, sort_order=0)
        with self.assertRaises(ValidationError) as ctx:
            m.clean()
        self.assertIn("fournis", str(ctx.exception).lower())

    def test_questionmedia_clean_ok_with_external_url(self):
        q = self._make_question("Q-media-url")

        m = QuestionMedia(
            question=q,
            kind=QuestionMedia.EXTERNAL,
            external_url="https://example.com/video",
            sort_order=0,
        )
        # doit passer
        m.clean()

    # ------------------------------------------------------------------
    # Question __str__ + Meta ordering sanity
    # ------------------------------------------------------------------
    def test_question_str(self):
        q = self._make_question("Ma question")
        self.assertEqual(str(q), "Ma question")

    def test_question_ordering_is_newest_first(self):
        q1 = self._make_question("Q-old")
        q2 = self._make_question("Q-new")
        ordered = list(Question.objects.all())
        # ordering = ["-created_at"]
        self.assertEqual(ordered[0].id, q2.id)
        self.assertEqual(ordered[1].id, q1.id)
