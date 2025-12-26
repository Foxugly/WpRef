# quiz/tests/test_serializers_modelserializers.py

from django.contrib.auth import get_user_model
from django.test import TestCase
from question.models import Question, AnswerOption
from quiz.constants import VISIBILITY_IMMEDIATE, VISIBILITY_NEVER
from quiz.models import QuizTemplate, QuizQuestion, Quiz, QuizQuestionAnswer
from quiz.serializers import (
    QuizQuestionSerializer,
    QuizTemplateSerializer,
    QuizQuestionWriteSerializer,
    QuizSerializer,
)
from rest_framework.test import APIRequestFactory

User = get_user_model()


# -----------------------
# Helpers
# -----------------------
def make_question(title="Q", active=True):
    # ⚠️ adapte si ton modèle Question impose d'autres champs
    return Question.objects.create(title=title, active=active)


def make_option(question, content="A"):
    return AnswerOption.objects.create(question=question, content=content)


def make_template(**kwargs):
    defaults = dict(
        title="Template",
        mode=QuizTemplate.MODE_PRACTICE,
        description="",
        max_questions=10,
        permanent=True,
        started_at=None,
        ended_at=None,
        with_duration=True,
        duration=10,
        active=True,
        result_visibility=VISIBILITY_IMMEDIATE,
        result_available_at=None,
        detail_visibility=VISIBILITY_IMMEDIATE,
        detail_available_at=None,
    )
    defaults.update(kwargs)
    return QuizTemplate.objects.create(**defaults)


def make_quiz(qt, user):
    # ⚠️ adapte si ton modèle Quiz impose d'autres champs
    return Quiz.objects.create(
        quiz_template=qt,
        user=user,
        active=True,
        started_at=None,
        ended_at=None,
    )


# ==========================================================
# 1) QuizQuestionSerializer
# ==========================================================
class QuizQuestionSerializerTests(TestCase):
    def setUp(self):
        self.qt = make_template(title="T1")
        self.q1 = make_question("Q1", active=True)
        self.qq = QuizQuestion.objects.create(quiz=self.qt, question=self.q1, sort_order=1, weight=2)

    def test_serialization_contains_expected_fields(self):
        data = QuizQuestionSerializer(self.qq).data

        # champs exposés
        self.assertIn("id", data)
        self.assertIn("quiz", data)
        self.assertIn("question", data)
        self.assertIn("sort_order", data)
        self.assertIn("weight", data)

        # question_id est write_only => pas en output
        self.assertNotIn("question_id", data)

    def test_question_id_is_write_only_and_maps_to_question(self):
        payload = {"question_id": self.q1.id, "sort_order": 5, "weight": 1}
        s = QuizQuestionSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

        # grâce à source="question" on doit retrouver la Question dans validated_data
        self.assertIn("question", s.validated_data)
        self.assertEqual(s.validated_data["question"].id, self.q1.id)

    def test_read_only_fields_quiz_and_question(self):
        """
        quiz & question sont read_only dans Meta.read_only_fields,
        donc on ne doit pas pouvoir les écrire directement.
        """
        payload = {
            "quiz": self.qt.id,
            "question": self.q1.id,
            "question_id": self.q1.id,
            "sort_order": 1,
            "weight": 1,
        }
        s = QuizQuestionSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

        # quiz / question ne doivent pas arriver comme champs écrits (write)
        self.assertNotIn("quiz", s.validated_data)
        # question est injectée via question_id (source="question"), donc elle existe bien
        self.assertIn("question", s.validated_data)


# ==========================================================
# 2) QuizTemplateSerializer
# ==========================================================
class QuizTemplateSerializerTests(TestCase):
    def setUp(self):
        self.qt = make_template(title="Template X", permanent=True, active=True)
        self.q1 = make_question("Q1", active=True)
        self.q2 = make_question("Q2", active=True)

        QuizQuestion.objects.create(quiz=self.qt, question=self.q1, sort_order=1, weight=1)
        QuizQuestion.objects.create(quiz=self.qt, question=self.q2, sort_order=2, weight=1)

    def test_serialization_includes_readonly_computed_fields(self):
        data = QuizTemplateSerializer(self.qt).data
        self.assertIn("questions_count", data)
        self.assertIn("can_answer", data)
        self.assertEqual(data["questions_count"], 2)
        self.assertTrue(data["can_answer"])

    def test_serialization_includes_quiz_questions_nested(self):
        data = QuizTemplateSerializer(self.qt).data
        self.assertIn("quiz_questions", data)
        self.assertEqual(len(data["quiz_questions"]), 2)

    def test_read_only_fields_are_not_writable(self):
        """
        slug, created_at, questions_count, can_answer sont read_only.
        On vérifie qu'ils ne sont pas acceptés en input.
        """
        payload = {
            "title": "Nouvel intitulé",
            "slug": "hacked",
            "questions_count": 999,
            "can_answer": False,
        }
        s = QuizTemplateSerializer(instance=self.qt, data=payload, partial=True)
        self.assertTrue(s.is_valid(), s.errors)

        obj = s.save()
        # slug ne doit pas être forcé par l'input
        self.assertNotEqual(obj.slug, "hacked")


# ==========================================================
# 3) QuizQuestionWriteSerializer
# ==========================================================
class QuizQuestionWriteSerializerTests(TestCase):
    def setUp(self):
        self.qt = make_template(title="T Write")
        self.q_active = make_question("QA", active=True)
        self.q_inactive = make_question("QI", active=False)

    def test_validate_requires_quiz_template_in_context(self):
        s = QuizQuestionWriteSerializer(data={"question_id": self.q_active.id, "sort_order": 1, "weight": 1})
        self.assertFalse(s.is_valid())
        self.assertIn("quiz_template", str(s.errors).lower())

    def test_validate_rejects_inactive_question(self):
        s = QuizQuestionWriteSerializer(
            data={"question_id": self.q_inactive.id, "sort_order": 1, "weight": 1},
            context={"quiz_template": self.qt},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("question_id", s.errors)
        self.assertIn("pas active", str(s.errors["question_id"][0]).lower())

    def test_validate_rejects_duplicate_question_in_template(self):
        QuizQuestion.objects.create(quiz=self.qt, question=self.q_active, sort_order=1, weight=1)

        s = QuizQuestionWriteSerializer(
            data={"question_id": self.q_active.id, "sort_order": 2, "weight": 1},
            context={"quiz_template": self.qt},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("déjà", str(s.errors["question_id"][0]).lower())

    def test_create_sets_quiz_from_context(self):
        s = QuizQuestionWriteSerializer(
            data={"question_id": self.q_active.id, "sort_order": 7, "weight": 3},
            context={"quiz_template": self.qt},
        )
        self.assertTrue(s.is_valid(), s.errors)
        obj = s.save()
        self.assertEqual(obj.quiz_id, self.qt.id)
        self.assertEqual(obj.question_id, self.q_active.id)
        self.assertEqual(obj.sort_order, 7)
        self.assertEqual(obj.weight, 3)

    def test_update_excludes_self_from_duplicate_check(self):
        qq = QuizQuestion.objects.create(quiz=self.qt, question=self.q_active, sort_order=1, weight=1)

        s = QuizQuestionWriteSerializer(
            instance=qq,
            data={"question_id": self.q_active.id, "sort_order": 10, "weight": 2},
            context={"quiz_template": self.qt},
        )
        self.assertTrue(s.is_valid(), s.errors)
        obj = s.save()
        self.assertEqual(obj.id, qq.id)
        self.assertEqual(obj.sort_order, 10)


# ==========================================================
# 4) QuizSerializer
# ==========================================================
class QuizSerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username="u1", password="pass")
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)

        self.qt = make_template(title="T Quiz", mode=QuizTemplate.MODE_EXAM)
        self.q1 = make_question("Q1", active=True)
        self.q2 = make_question("Q2", active=True)

        self.qq1 = QuizQuestion.objects.create(quiz=self.qt, question=self.q1, sort_order=1, weight=1)
        self.qq2 = QuizQuestion.objects.create(quiz=self.qt, question=self.q2, sort_order=2, weight=1)

        # options (pour prefetch_related du serializer)
        self.o11 = make_option(self.q1, "A1")
        self.o12 = make_option(self.q1, "A2")

        self.quiz = make_quiz(self.qt, self.user)

    def _serialize_as(self, user):
        req = self.factory.get("/fake")
        req.user = user
        return QuizSerializer(self.quiz, context={"request": req}).data

    def test_questions_are_ordered_and_present(self):
        data = self._serialize_as(self.user)
        self.assertIn("questions", data)
        self.assertEqual(len(data["questions"]), 2)
        self.assertEqual(data["questions"][0]["sort_order"], 1)
        self.assertEqual(data["questions"][1]["sort_order"], 2)

    def test_result_fields_hidden_when_template_forbids_and_user_not_admin(self):
        # template refuse résultat
        self.qt.result_visibility = VISIBILITY_NEVER
        self.qt.save()

        data = self._serialize_as(self.user)
        self.assertIsNone(data["total_answers"])
        self.assertIsNone(data["correct_answers"])
        self.assertIsNone(data["earned_score"])
        self.assertIsNone(data["max_score"])

    def test_result_fields_visible_for_staff_even_if_template_forbids(self):
        # template refuse résultat
        self.qt.result_visibility = VISIBILITY_NEVER
        self.qt.active = True
        self.qt.permanent = True
        self.qt.save()
        self.quiz.start()
        # Créer 2 réponses
        a1 = QuizQuestionAnswer.objects.create(
            quiz=self.quiz,
            quizquestion=self.qq1,
            question_order=1,
            # ⚠️ adapte si ces champs existent / sont obligatoires chez toi
            is_correct=True,
            earned_score=1.0,
            max_score=2.0,
        )
        a2 = QuizQuestionAnswer.objects.create(
            quiz=self.quiz,
            quizquestion=self.qq2,
            question_order=2,
            is_correct=False,
            earned_score=0.5,
            max_score=2.0,
        )

        data = self._serialize_as(self.staff)
        self.assertEqual(data["total_answers"], 2)
        self.assertEqual(data["correct_answers"], 1)
        self.assertEqual(float(data["earned_score"]), 1.5)
        self.assertEqual(float(data["max_score"]), 4.0)

    def test_answers_cache_is_used(self):
        """
        On ne mesure pas les queries ici (ça serait plutôt assertNumQueries),
        mais on vérifie que le serializer marche même si _answers_cache est présent.
        """

        self.qt.active = True
        self.qt.permanent = True
        self.qt.save()
        self.quiz.start()
        QuizQuestionAnswer.objects.create(
            quiz=self.quiz,
            quizquestion=self.qq1,
            question_order=1,
            is_correct=True,
            earned_score=1.0,
            max_score=2.0,
        )

        # forcer le cache
        self.quiz._answers_cache = self.quiz.answers.all()

        data = self._serialize_as(self.staff)
        # staff => peut voir
        self.assertEqual(data["total_answers"], 1)
        self.assertEqual(data["correct_answers"], 1)
