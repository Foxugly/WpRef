# quiz/tests/test_serializers_modelserializers.py

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from django.utils import translation
from unittest.mock import patch
from domain.models import Domain
from question.models import Question, AnswerOption
from quiz.constants import VISIBILITY_IMMEDIATE, VISIBILITY_NEVER
from quiz.models import QuizTemplate, QuizQuestion, Quiz, QuizQuestionAnswer
from quiz.serializers import (
    GenerateFromSubjectsInputSerializer,
    BulkCreateFromTemplateInputSerializer,
    CreateQuizInputSerializer,
    QuizListSerializer,
    QuizQuestionSerializer,
    QuizTemplateSerializer,
    QuizTemplateWriteSerializer,
    QuizQuestionWriteSerializer,
    QuizQuestionAnswerSerializer,
    QuizQuestionReadSerializer,
    QuizSerializer,
    QuizQuestionAnswerWriteSerializer,
    QuizQuestionAnswerPartialSerializer,
)
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

User = get_user_model()


class LocalizedTestCase(TestCase):
    def setUp(self):
        super().setUp()
        translation.activate("fr")

    def tearDown(self):
        translation.deactivate_all()
        super().tearDown()


# -----------------------
# Helpers (compatibles avec tes modèles Parler + Domain obligatoire)
# -----------------------
def make_user(username="u", is_staff=False, is_superuser=False):
    return User.objects.create_user(username=username, password="pass", is_staff=is_staff, is_superuser=is_superuser)


def make_domain(owner, name="Test domain", description=""):
    # Domain est TranslatableModel, on peut passer name/description directement
    if translation.get_language() is None:
        translation.activate("fr")
    return Domain.objects.create(owner=owner, name=name, description=description, active=True)


def make_question(domain, title="Q", active=True):
    # Question est TranslatableModel + domain NOT NULL
    if translation.get_language() is None:
        translation.activate("fr")
    q = Question.objects.create(
        domain=domain,
        title=title,
        description="desc",
        explanation="expl",
        active=active,
        allow_multiple_correct=False,
        is_mode_practice=True,
        is_mode_exam=True,
    )
    return q


def make_option(question, content="A", is_correct=False, sort_order=1):
    # AnswerOption est TranslatableModel
    if translation.get_language() is None:
        translation.activate("fr")
    return AnswerOption.objects.create(question=question, content=content, is_correct=is_correct, sort_order=sort_order)


def make_template(domain, **kwargs):
    if translation.get_language() is None:
        translation.activate("fr")
    defaults = dict(
        domain=domain,
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


def make_quiz(qt, user, active=True, started=True):
    # IMPORTANT: QuizQuestionAnswer.save() appelle full_clean() => quiz.can_answer doit être True
    started_at = timezone.now() if started else None
    quiz = Quiz.objects.create(
        quiz_template=qt,
        user=user,
        active=active,
        started_at=started_at,
        ended_at=None,
    )
    return quiz


# ==========================================================
# 0) Simple Input Serializers
# ==========================================================
class InputSerializersTests(LocalizedTestCase):
    def test_generate_from_subjects_input_serializer_valid(self):
        s = GenerateFromSubjectsInputSerializer(
            data={"title": "T", "subject_ids": [1, 2, 3], "max_questions": 5}
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["title"], "T")
        self.assertEqual(s.validated_data["subject_ids"], [1, 2, 3])
        self.assertEqual(s.validated_data["max_questions"], 5)

    def test_generate_from_subjects_input_serializer_default_max_questions(self):
        s = GenerateFromSubjectsInputSerializer(data={"title": "T", "subject_ids": [1]})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["max_questions"], 10)

    def test_generate_from_subjects_input_serializer_rejects_empty_subject_ids(self):
        s = GenerateFromSubjectsInputSerializer(data={"title": "T", "subject_ids": []})
        self.assertFalse(s.is_valid())
        self.assertIn("subject_ids", s.errors)

    def test_bulk_create_from_template_input_serializer_valid(self):
        s = BulkCreateFromTemplateInputSerializer(data={"quiz_template_id": 12, "user_ids": [1, 2]})
        self.assertTrue(s.is_valid(), s.errors)

    def test_bulk_create_from_template_input_serializer_rejects_empty_user_ids(self):
        s = BulkCreateFromTemplateInputSerializer(data={"quiz_template_id": 12, "user_ids": []})
        self.assertFalse(s.is_valid())
        self.assertIn("user_ids", s.errors)

    def test_create_quiz_input_serializer_valid(self):
        s = CreateQuizInputSerializer(data={"quiz_template_id": 99})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["quiz_template_id"], 99)


# ==========================================================
# 1) QuizQuestionSerializer
# ==========================================================
class QuizQuestionSerializerTests(LocalizedTestCase):
    def setUp(self):
        self.user = make_user("u1")
        self.domain = make_domain(self.user, "D1")
        self.qt = make_template(self.domain, title="T1")

        self.q1 = make_question(self.domain, "Q1", active=True)
        make_option(self.q1, "A", is_correct=True, sort_order=1)
        make_option(self.q1, "B", is_correct=False, sort_order=2)

        self.qq = QuizQuestion.objects.create(quiz=self.qt, question=self.q1, sort_order=1, weight=2)

    def test_serialization_contains_expected_fields(self):
        data = QuizQuestionSerializer(self.qq).data

        self.assertIn("id", data)
        self.assertIn("quiz", data)
        self.assertIn("question", data)
        self.assertIn("sort_order", data)
        self.assertIn("weight", data)
        self.assertNotIn("question_id", data)  # write_only

    def test_question_id_is_write_only_and_maps_to_question(self):
        payload = {"question_id": self.q1.id, "sort_order": 5, "weight": 1}
        s = QuizQuestionSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIn("question", s.validated_data)
        self.assertEqual(s.validated_data["question"].id, self.q1.id)

    def test_init_accepts_show_correct_flag(self):
        # On ne présume pas des champs exposés par QuestionInQuizQuestionSerializer,
        # mais on couvre le __init__ qui remplace self.fields["question"].
        _ = QuizQuestionSerializer(self.qq, show_correct=True).data
        _ = QuizQuestionSerializer(self.qq, show_correct=False).data

    def test_read_only_fields_quiz_and_question_not_writable_directly(self):
        payload = {
            "quiz": self.qt.id,
            "question": self.q1.id,  # read_only, doit être ignoré
            "question_id": self.q1.id,
            "sort_order": 1,
            "weight": 1,
        }
        s = QuizQuestionSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)
        self.assertNotIn("quiz", s.validated_data)
        self.assertIn("question", s.validated_data)  # via question_id -> source="question"


# ==========================================================
# 2) QuizTemplateSerializer
# ==========================================================
class QuizTemplateSerializerTests(LocalizedTestCase):
    def setUp(self):
        self.user = make_user("u1")
        self.domain = make_domain(self.user, "D1")

        self.qt = make_template(self.domain, title="Template X", permanent=True, active=True)
        self.q1 = make_question(self.domain, "Q1", active=True)
        self.q2 = make_question(self.domain, "Q2", active=True)

        make_option(self.q1, "A", True, 1)
        make_option(self.q1, "B", False, 2)
        make_option(self.q2, "A", True, 1)
        make_option(self.q2, "B", False, 2)

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

    def test_serialization_exposes_translations_map(self):
        self.qt.translations = {
            "fr": {"title": "Template FR", "description": "Desc FR"},
            "en": {"title": "Template EN", "description": "Desc EN"},
        }
        self.qt.save()

        data = QuizTemplateSerializer(self.qt).data
        self.assertIn("translations", data)
        self.assertEqual(data["translations"]["fr"]["title"], "Template FR")

    def test_write_serializer_accepts_translations(self):
        payload = {
            "domain": self.domain.id,
            "title": "Template FR",
            "description": "Desc FR",
            "translations": {
                "fr": {"title": "Template FR", "description": "Desc FR"},
                "en": {"title": "Template EN", "description": "Desc EN"},
            },
            "mode": QuizTemplate.MODE_PRACTICE,
            "max_questions": 3,
            "permanent": True,
            "with_duration": False,
            "duration": 10,
            "is_public": False,
            "active": True,
            "result_visibility": VISIBILITY_IMMEDIATE,
            "detail_visibility": VISIBILITY_IMMEDIATE,
        }
        factory = APIRequestFactory()
        request = factory.post("/api/quiz/template/")
        request.user = self.user

        serializer = QuizTemplateWriteSerializer(data=payload, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()
        self.assertEqual(instance.translations["en"]["title"], "Template EN")
        self.assertEqual(instance.title, "Template FR")

    def test_write_serializer_accepts_blank_translation_description(self):
        payload = {
            "domain": self.domain.id,
            "title": "Template FR",
            "description": "",
            "translations": {
                "fr": {"title": "Template FR", "description": ""},
            },
            "mode": QuizTemplate.MODE_PRACTICE,
            "max_questions": 3,
            "permanent": True,
            "with_duration": False,
            "duration": 10,
            "is_public": False,
            "active": True,
            "result_visibility": VISIBILITY_IMMEDIATE,
            "detail_visibility": VISIBILITY_IMMEDIATE,
        }
        factory = APIRequestFactory()
        request = factory.post("/api/quiz/template/")
        request.user = self.user

        serializer = QuizTemplateWriteSerializer(data=payload, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()
        self.assertEqual(instance.translations["fr"]["description"], "")

    def test_write_serializer_returns_validation_error_on_integrity_error(self):
        payload = {
            "domain": self.domain.id,
            "title": "Template FR",
            "description": "Desc FR",
            "translations": {
                "fr": {"title": "Template FR", "description": "Desc FR"},
            },
            "mode": QuizTemplate.MODE_PRACTICE,
            "max_questions": 3,
            "permanent": True,
            "with_duration": False,
            "duration": 10,
            "is_public": False,
            "active": True,
            "result_visibility": VISIBILITY_IMMEDIATE,
            "detail_visibility": VISIBILITY_IMMEDIATE,
        }
        factory = APIRequestFactory()
        request = factory.post("/api/quiz/template/")
        request.user = self.user

        serializer = QuizTemplateWriteSerializer(data=payload, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        with patch("quiz.serializers.QuizTemplate.save", side_effect=IntegrityError("duplicate")):
            with self.assertRaises(serializers.ValidationError):
                serializer.save()

    def test_read_only_fields_are_not_writable(self):
        payload = {
            "title": "Nouvel intitulé",
            "slug": "hacked",
            "questions_count": 999,
            "can_answer": False,
        }
        s = QuizTemplateSerializer(instance=self.qt, data=payload, partial=True)
        self.assertTrue(s.is_valid(), s.errors)

        obj = s.save()
        self.assertNotEqual(obj.slug, "hacked")


# ==========================================================
# 3) QuizQuestionWriteSerializer
# ==========================================================
class QuizQuestionWriteSerializerTests(LocalizedTestCase):
    def setUp(self):
        self.user = make_user("u1")
        self.domain = make_domain(self.user, "D1")
        self.qt = make_template(self.domain, title="T Write")

        self.q_active = make_question(self.domain, "QA", active=True)
        make_option(self.q_active, "A", True, 1)
        make_option(self.q_active, "B", False, 2)

        self.q_inactive = make_question(self.domain, "QI", active=False)
        make_option(self.q_inactive, "A", True, 1)
        make_option(self.q_inactive, "B", False, 2)

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

    def test_validate_rejects_duplicate_question_in_template(self):
        QuizQuestion.objects.create(quiz=self.qt, question=self.q_active, sort_order=1, weight=1)

        s = QuizQuestionWriteSerializer(
            data={"question_id": self.q_active.id, "sort_order": 2, "weight": 1},
            context={"quiz_template": self.qt},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("question_id", s.errors)

    def test_validate_rejects_question_from_other_domain(self):
        other_domain = make_domain(self.user, "D2")
        other_question = make_question(other_domain, "Q OTHER", active=True)
        make_option(other_question, "A", True, 1)
        make_option(other_question, "B", False, 2)

        s = QuizQuestionWriteSerializer(
            data={"question_id": other_question.id, "sort_order": 2, "weight": 1},
            context={"quiz_template": self.qt},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("question_id", s.errors)

    def test_validate_allows_exam_only_question_in_practice_template(self):
        exam_only = make_question(self.domain, "Q EXAM ONLY", active=True)
        exam_only.is_mode_practice = False
        exam_only.is_mode_exam = True
        exam_only.save(update_fields=["is_mode_practice", "is_mode_exam"])
        make_option(exam_only, "A", True, 1)
        make_option(exam_only, "B", False, 2)

        s = QuizQuestionWriteSerializer(
            data={"question_id": exam_only.id, "sort_order": 2, "weight": 1},
            context={"quiz_template": self.qt},
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_validate_rejects_non_exam_question_in_exam_template(self):
        exam_template = make_template(self.domain, title="T Exam", mode=QuizTemplate.MODE_EXAM)
        practice_only = make_question(self.domain, "Q PRACTICE ONLY", active=True)
        practice_only.is_mode_practice = True
        practice_only.is_mode_exam = False
        practice_only.save(update_fields=["is_mode_practice", "is_mode_exam"])
        make_option(practice_only, "A", True, 1)
        make_option(practice_only, "B", False, 2)

        s = QuizQuestionWriteSerializer(
            data={"question_id": practice_only.id, "sort_order": 1, "weight": 1},
            context={"quiz_template": exam_template},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("question_id", s.errors)

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

    def test_partial_update_without_question_id_keeps_instance_question(self):
        qq = QuizQuestion.objects.create(quiz=self.qt, question=self.q_active, sort_order=1, weight=1)

        s = QuizQuestionWriteSerializer(
            instance=qq,
            data={"sort_order": 4, "weight": 2},
            partial=True,
            context={"quiz_template": self.qt},
        )
        self.assertTrue(s.is_valid(), s.errors)
        obj = s.save()
        self.assertEqual(obj.question_id, self.q_active.id)
        self.assertEqual(obj.sort_order, 4)
        self.assertEqual(obj.weight, 2)


# ==========================================================
# 4) QuizQuestionAnswerSerializer (read-only mapping)
# ==========================================================
class QuizQuestionAnswerSerializerTests(LocalizedTestCase):
    def setUp(self):
        self.user = make_user("u1")
        self.domain = make_domain(self.user, "D1")
        self.qt = make_template(self.domain, title="T", mode=QuizTemplate.MODE_EXAM, permanent=True, active=True)
        self.q1 = make_question(self.domain, "Q1", active=True)
        make_option(self.q1, "A", True, 1)
        make_option(self.q1, "B", False, 2)

        self.qq1 = QuizQuestion.objects.create(quiz=self.qt, question=self.q1, sort_order=1, weight=1)
        self.quiz = make_quiz(self.qt, self.user, active=True, started=True)

        self.ans = QuizQuestionAnswer.objects.create(quiz=self.quiz, quizquestion=self.qq1, question_order=1)

    def test_read_only_fields_and_ids_mapping(self):
        data = QuizQuestionAnswerSerializer(self.ans).data
        self.assertEqual(data["quiz"], self.quiz.id)
        self.assertEqual(data["quizquestion_id"], self.qq1.id)
        self.assertEqual(data["question_id"], self.q1.id)
        self.assertIn("selected_options", data)
        self.assertIn("answered_at", data)


# ==========================================================
# 5) QuizQuestionReadSerializer (init show_correct)
# ==========================================================
class QuizQuestionReadSerializerTests(LocalizedTestCase):
    def setUp(self):
        self.user = make_user("u1")
        self.domain = make_domain(self.user, "D1")
        self.qt = make_template(self.domain, title="T")
        self.q1 = make_question(self.domain, "Q1", active=True)
        make_option(self.q1, "A", True, 1)
        make_option(self.q1, "B", False, 2)
        self.qq1 = QuizQuestion.objects.create(quiz=self.qt, question=self.q1, sort_order=1, weight=2)

    def test_init_accepts_show_correct(self):
        _ = QuizQuestionReadSerializer(self.qq1, show_correct=True).data
        _ = QuizQuestionReadSerializer(self.qq1, show_correct=False).data


# ==========================================================
# 6) QuizSerializer (admin vs non-admin + cache + show_details)
# ==========================================================
class QuizSerializerTests(LocalizedTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.user = make_user("u1")
        self.staff = make_user("staff", is_staff=True)

        self.domain = make_domain(self.user, "D1")
        self.qt = make_template(
            self.domain,
            title="T Quiz",
            description="Description quiz",
            mode=QuizTemplate.MODE_EXAM,
            permanent=True,
            active=True,
            detail_visibility=VISIBILITY_NEVER,  # détails interdits
            result_visibility=VISIBILITY_NEVER,  # résultat interdit
        )

        self.q1 = make_question(self.domain, "Q1", active=True)
        self.q2 = make_question(self.domain, "Q2", active=True)

        make_option(self.q1, "A", True, 1)
        make_option(self.q1, "B", False, 2)
        make_option(self.q2, "A", True, 1)
        make_option(self.q2, "B", False, 2)

        self.qq1 = QuizQuestion.objects.create(quiz=self.qt, question=self.q1, sort_order=1, weight=2)
        self.qq2 = QuizQuestion.objects.create(quiz=self.qt, question=self.q2, sort_order=2, weight=3)

        # quiz "répondable"
        self.quiz = make_quiz(self.qt, self.user, active=True, started=True)

    def _serialize_as(self, user):
        req = self.factory.get("/fake")
        req.user = user
        return QuizSerializer(self.quiz, context={"request": req}).data

    def _serialize_list_as(self, user):
        req = self.factory.get("/fake")
        req.user = user
        return QuizListSerializer(self.quiz, context={"request": req}).data

    def test_questions_are_ordered_and_present(self):
        data = self._serialize_as(self.user)
        self.assertIn("questions", data)
        self.assertEqual(len(data["questions"]), 2)
        self.assertEqual(data["questions"][0]["sort_order"], 1)
        self.assertEqual(data["questions"][1]["sort_order"], 2)

    def test_questions_include_full_question_payload(self):
        data = self._serialize_as(self.user)

        question = data["questions"][0]["question"]
        self.assertIn("translations", question)
        self.assertIn("media", question)
        self.assertIn("subjects", question)

    def test_result_fields_hidden_when_template_forbids_and_user_not_admin(self):
        data = self._serialize_as(self.user)
        self.assertIsNone(data["total_answers"])
        self.assertIsNone(data["correct_answers"])
        self.assertIsNone(data["earned_score"])
        self.assertIsNone(data["max_score"])

    def test_result_fields_visible_for_staff_even_if_template_forbids(self):
        # Créer des réponses avec scores (ok car quiz can_answer True)
        QuizQuestionAnswer.objects.create(
            quiz=self.quiz,
            quizquestion=self.qq1,
            question_order=1,
            is_correct=True,
            earned_score=2.0,
            max_score=2.0,
        )
        QuizQuestionAnswer.objects.create(
            quiz=self.quiz,
            quizquestion=self.qq2,
            question_order=2,
            is_correct=False,
            earned_score=0.0,
            max_score=3.0,
        )

        data = self._serialize_as(self.staff)
        self.assertEqual(data["total_answers"], 2)
        self.assertEqual(data["correct_answers"], 1)
        self.assertEqual(float(data["earned_score"]), 2.0)
        self.assertEqual(float(data["max_score"]), 5.0)

    def test_answers_cache_is_used(self):
        QuizQuestionAnswer.objects.create(
            quiz=self.quiz,
            quizquestion=self.qq1,
            question_order=1,
            is_correct=True,
            earned_score=2.0,
            max_score=2.0,
        )
        self.quiz._answers_cache = self.quiz.answers.all()

        data = self._serialize_as(self.staff)
        self.assertEqual(data["total_answers"], 1)
        self.assertEqual(data["correct_answers"], 1)

    def test_is_admin_false_when_no_request_in_context(self):
        # couvre _is_admin() => False
        data = QuizSerializer(self.quiz, context={}).data
        # pas d'admin => résultat interdit par template => None
        self.assertIsNone(data["total_answers"])

    def test_list_serializer_exposes_user_summary_and_template_description(self):
        data = self._serialize_list_as(self.user)
        self.assertEqual(data["quiz_template_description"], "Description quiz")
        self.assertEqual(data["user_summary"], {"id": self.user.id, "username": self.user.username})

    def test_list_serializer_omits_detail_collections(self):
        data = self._serialize_list_as(self.user)
        self.assertNotIn("questions", data)
        self.assertNotIn("answers", data)


# ==========================================================
# 7) QuizQuestionAnswerWriteSerializer (grosse partie de la couverture)
# ==========================================================
class QuizQuestionAnswerWriteSerializerTests(LocalizedTestCase):
    def setUp(self):
        self.user = make_user("u1")
        self.other_user = make_user("u2")
        self.staff = make_user("staff", is_staff=True)

        self.domain = make_domain(self.user, "D1")
        self.qt = make_template(self.domain, title="T", mode=QuizTemplate.MODE_EXAM, permanent=True, active=True)

        self.q1 = make_question(self.domain, "Q1", active=True)
        self.q2 = make_question(self.domain, "Q2", active=True)

        self.o11 = make_option(self.q1, "A", True, 1)
        self.o12 = make_option(self.q1, "B", False, 2)

        self.o21 = make_option(self.q2, "A", True, 1)
        self.o22 = make_option(self.q2, "B", False, 2)

        self.qq1 = QuizQuestion.objects.create(quiz=self.qt, question=self.q1, sort_order=1, weight=1)
        self.qq2 = QuizQuestion.objects.create(quiz=self.qt, question=self.q2, sort_order=2, weight=1)

        self.quiz = make_quiz(self.qt, self.user, active=True, started=True)

    # ---- validate() guards
    def test_validate_requires_quiz_in_context(self):
        s = QuizQuestionAnswerWriteSerializer(data={"question_order": 1, "selected_options": []}, context={})
        self.assertFalse(s.is_valid())
        self.assertIn("quiz", str(s.errors).lower())

    def test_validate_blocks_when_quiz_cannot_answer(self):
        self.quiz.active = False
        self.quiz.save()

        s = QuizQuestionAnswerWriteSerializer(
            data={"question_order": 1, "selected_options": []},
            context={"quiz": self.quiz},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("detail", s.errors)

    def test_validate_instance_must_belong_to_quiz(self):
        # créer une réponse dans un autre quiz
        other_quiz = make_quiz(self.qt, self.other_user, active=True, started=True)
        ans = QuizQuestionAnswer.objects.create(quiz=other_quiz, quizquestion=self.qq1, question_order=1)

        s = QuizQuestionAnswerWriteSerializer(
            instance=ans,
            data={"selected_options": [self.o11.id]},
            context={"quiz": self.quiz},  # quiz courant différent
            partial=True,
        )
        self.assertFalse(s.is_valid())
        self.assertIn("hors du quiz", str(s.errors).lower())

    def test_validate_requires_question_id_or_question_order(self):
        s = QuizQuestionAnswerWriteSerializer(data={"selected_options": []}, context={"quiz": self.quiz})
        self.assertFalse(s.is_valid())
        self.assertIn("fournis au moins", str(s.errors).lower())

    def test_validate_question_id_not_in_template(self):
        # question d'un autre template
        qt2 = make_template(self.domain, title="T2", permanent=True, active=True)
        qx = make_question(self.domain, "QX", active=True)
        make_option(qx, "A", True, 1)
        make_option(qx, "B", False, 2)
        QuizQuestion.objects.create(quiz=qt2, question=qx, sort_order=1, weight=1)

        s = QuizQuestionAnswerWriteSerializer(
            data={"question_id": qx.id, "selected_options": []},
            context={"quiz": self.quiz},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("question_id", s.errors)

    def test_validate_question_order_must_be_positive(self):
        s = QuizQuestionAnswerWriteSerializer(
            data={"question_order": 0, "selected_options": []},
            context={"quiz": self.quiz},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("question_order", s.errors)

    def test_validate_question_order_not_found(self):
        s = QuizQuestionAnswerWriteSerializer(
            data={"question_order": 999, "selected_options": []},
            context={"quiz": self.quiz},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("question_order", s.errors)

    def test_validate_incoherent_question_id_and_order(self):
        s = QuizQuestionAnswerWriteSerializer(
            data={"question_id": self.q1.id, "question_order": 2, "selected_options": []},
            context={"quiz": self.quiz},
        )
        self.assertFalse(s.is_valid())
        # non_field_errors ou non_field_errors-like
        self.assertTrue("non_field_errors" in s.errors or "non_field_errors" in str(s.errors).lower())

    # ---- create()
    def test_create_with_question_id_sets_quizquestion_and_question_order(self):
        s = QuizQuestionAnswerWriteSerializer(
            data={"question_id": self.q1.id, "selected_options": [self.o11.id]},
            context={"quiz": self.quiz},
        )
        self.assertTrue(s.is_valid(), s.errors)
        ans = s.save()

        self.assertEqual(ans.quiz_id, self.quiz.id)
        self.assertEqual(ans.quizquestion_id, self.qq1.id)
        self.assertEqual(ans.question_order, 1)
        self.assertEqual(list(ans.selected_options.values_list("id", flat=True)), [self.o11.id])

    def test_create_with_question_order_sets_quizquestion(self):
        s = QuizQuestionAnswerWriteSerializer(
            data={"question_order": 2, "selected_options": [self.o21.id]},
            context={"quiz": self.quiz},
        )
        self.assertTrue(s.is_valid(), s.errors)
        ans = s.save()

        self.assertEqual(ans.quizquestion_id, self.qq2.id)
        self.assertEqual(ans.question_order, 2)

    def test_create_is_idempotent_update_or_create(self):
        # 1ère fois
        s1 = QuizQuestionAnswerWriteSerializer(
            data={"question_id": self.q1.id, "selected_options": [self.o11.id]},
            context={"quiz": self.quiz},
        )
        self.assertTrue(s1.is_valid(), s1.errors)
        a1 = s1.save()

        # 2ème fois: même quizquestion => update_or_create => même instance
        s2 = QuizQuestionAnswerWriteSerializer(
            data={"question_id": self.q1.id, "selected_options": [self.o12.id]},
            context={"quiz": self.quiz},
        )
        self.assertTrue(s2.is_valid(), s2.errors)
        a2 = s2.save()

        self.assertEqual(a1.id, a2.id)
        self.assertEqual(list(a2.selected_options.values_list("id", flat=True)), [self.o12.id])

    def test_create_rejects_selected_options_from_another_question(self):
        s = QuizQuestionAnswerWriteSerializer(
            data={"question_id": self.q1.id, "selected_options": [self.o21.id]},
            context={"quiz": self.quiz},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("selected_options", s.errors)

    # ---- update()
    def test_update_updates_selected_options_and_ignores_attempt_to_change_question(self):
        ans = QuizQuestionAnswer.objects.create(quiz=self.quiz, quizquestion=self.qq1, question_order=1)
        ans.selected_options.set([self.o11])

        s = QuizQuestionAnswerWriteSerializer(
            instance=ans,
            data={
                "selected_options": [self.o12.id],
                "question_id": self.q2.id,  # tentative de changer la question -> doit être ignoré
                "question_order": 2,  # tentative -> ignoré
            },
            context={"quiz": self.quiz},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()

        self.assertEqual(updated.quizquestion_id, self.qq1.id)  # inchangé
        self.assertEqual(updated.question_order, 1)  # inchangé
        self.assertEqual(list(updated.selected_options.values_list("id", flat=True)), [self.o12.id])

    def test_update_when_selected_options_absent_does_not_change_m2m(self):
        ans = QuizQuestionAnswer.objects.create(quiz=self.quiz, quizquestion=self.qq1, question_order=1)
        ans.selected_options.set([self.o11])

        s = QuizQuestionAnswerWriteSerializer(
            instance=ans,
            data={},  # pas de selected_options => ne change rien
            context={"quiz": self.quiz},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(list(updated.selected_options.values_list("id", flat=True)), [self.o11.id])

    def test_update_rejects_selected_options_from_another_question(self):
        ans = QuizQuestionAnswer.objects.create(quiz=self.quiz, quizquestion=self.qq1, question_order=1)

        s = QuizQuestionAnswerWriteSerializer(
            instance=ans,
            data={"selected_options": [self.o21.id]},
            context={"quiz": self.quiz},
            partial=True,
        )
        self.assertFalse(s.is_valid())
        self.assertIn("selected_options", s.errors)

    def test_partial_serializer_rejects_selected_options_from_another_question(self):
        ans = QuizQuestionAnswer.objects.create(quiz=self.quiz, quizquestion=self.qq1, question_order=1)

        s = QuizQuestionAnswerPartialSerializer(
            instance=ans,
            data={"selected_options": [self.o22.id]},
            context={"quiz": self.quiz},
            partial=True,
        )
        self.assertFalse(s.is_valid())
        self.assertIn("selected_options", s.errors)
