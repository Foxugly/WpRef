# question/tests/test_serializers.py
import logging

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import TestCase

from domain.models import Domain
from question.models import Question, AnswerOption, QuestionMedia
from question.serializers import (
    QuestionLiteSerializer,
    QuestionMediaSerializer,
    QuestionAnswerOptionReadSerializer,
    QuestionAnswerOptionWriteSerializer,
    QuestionInQuizQuestionSerializer,
    QuestionReadSerializer,
    QuestionWriteSerializer,
)
from subject.models import Subject

logger = logging.getLogger(__name__)
User = get_user_model()


class DummyView:
    def __init__(self, swagger_fake_view=False):
        self.swagger_fake_view = swagger_fake_view


class QuestionSerializersTestCase(TestCase):
    # ------------------------------------------------------------------
    # Helpers robustes
    # ------------------------------------------------------------------
    def _make_user(self, username_prefix="u"):
        n = User.objects.count() + 1
        return User.objects.create_user(
            username=f"{username_prefix}{n}",
            password="pass",
            is_staff=True,
        )

    def _auto_create_required_fields(self, model_cls, overrides=None):
        """
        Utilisé uniquement pour Language (ou modèle simple) quand on ne veut pas
        dépendre des champs exacts (name/label/etc).
        Ne gère PAS les FK requises.
        """
        from django.db import models
        overrides = overrides or {}
        data = dict(overrides)

        for f in model_cls._meta.fields:
            if f.primary_key:
                continue
            if f.name in data:
                continue
            if f.has_default():
                continue

            required = (not getattr(f, "null", False)) and (not getattr(f, "blank", False))
            if not required:
                continue

            if f.is_relation and f.many_to_one:
                raise RuntimeError(f"FK requis non géré auto: {model_cls.__name__}.{f.name}")

            if isinstance(f, (models.CharField, models.SlugField)):
                data[f.name] = "x"
            elif isinstance(f, models.TextField):
                data[f.name] = "x"
            elif isinstance(f, models.BooleanField):
                data[f.name] = True
            elif isinstance(f, (models.IntegerField, models.PositiveIntegerField, models.SmallIntegerField)):
                data[f.name] = 1
            else:
                data[f.name] = "x"

        return model_cls.objects.create(**data)

    def _make_language(self, code: str):
        """
        Essaie de créer/retourner language.Language avec code.
        Adaptation auto si le modèle a d'autres champs requis.
        """
        Language = apps.get_model("language", "Language")
        obj = Language.objects.filter(code=code).first()
        if obj:
            return obj
        # crée en remplissant les champs requis
        return self._auto_create_required_fields(Language, overrides={"code": code})

    def _make_domain(self, *, owner=None, name="Domain", allowed_codes=("fr", "nl"), lang="fr"):
        owner = owner or self._make_user("owner")
        d = Domain.objects.create(owner=owner, active=True)
        d.set_current_language(lang)
        d.name = name
        d.description = "desc"
        d.save()

        # allowed_languages
        for c in allowed_codes:
            d.allowed_languages.add(self._make_language(c))

        return d

    def _make_subject(self, name="Math", lang="fr"):
        s = Subject.objects.create()
        if hasattr(s, "set_current_language"):
            s.set_current_language(lang)
        if hasattr(s, "name"):
            s.name = name
        s.save()
        return s

    def _make_question(self, *, domain=None, title="Q1", lang="fr", allow_multiple_correct=False):
        domain = domain or self._make_domain()
        q = Question.objects.create(
            domain=domain,
            allow_multiple_correct=allow_multiple_correct,
            active=True,
            is_mode_practice=True,
            is_mode_exam=True,
        )
        q.set_current_language(lang)
        q.title = title
        q.description = "desc"
        q.explanation = "expl"
        q.save()
        return q

    def _make_option(self, q: Question, *, is_correct: bool, sort_order: int, content_fr="A", content_nl="A-nl"):
        o = AnswerOption.objects.create(question=q, is_correct=is_correct, sort_order=sort_order)
        o.set_current_language("fr")
        o.content = content_fr
        o.save()
        o.set_current_language("nl")
        o.content = content_nl
        o.save()
        return o

    # ------------------------------------------------------------------
    # Smoke tests serializers simples
    # ------------------------------------------------------------------
    def test_question_lite_serializer_title(self):
        q = self._make_question(title="Hello")
        data = QuestionLiteSerializer(q).data
        self.assertEqual(data["id"], q.id)
        self.assertEqual(data["title"], "Hello")

    def test_question_media_serializer_read_only_fields(self):
        # read_only_fields = ["id", "file", "external_url", "kind"]
        q = self._make_question()
        ser = QuestionMediaSerializer(data={"kind": "image", "external_url": "https://x", "sort_order": 1})
        # Même si "data" passe ou pas, le point important: ces champs sont read-only
        self.assertTrue(ser.fields["kind"].read_only)
        self.assertTrue(ser.fields["file"].read_only)
        self.assertTrue(ser.fields["external_url"].read_only)

    def test_answer_option_read_serializer_content(self):
        q = self._make_question()
        o = self._make_option(q, is_correct=True, sort_order=1, content_fr="FR", content_nl="NL")

        data = QuestionAnswerOptionReadSerializer(o).data
        # content = safe_translation_getter(any_language=True)
        self.assertIn(data["content"], {"FR", "NL"})
        self.assertEqual(data["is_correct"], True)
        self.assertEqual(data["sort_order"], 1)

    # ------------------------------------------------------------------
    # QuestionAnswerOptionWriteSerializer
    # ------------------------------------------------------------------
    def test_answer_option_write_serializer_create_sets_translations(self):
        q = self._make_question()
        payload = {
            "is_correct": True,
            "sort_order": 1,
            "translations": {
                "fr": {"content": "Bonjour"},
                "nl": {"content": "Hallo"},
            },
        }
        ser = QuestionAnswerOptionWriteSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)

        obj = ser.save(question=q)
        obj.refresh_from_db()

        obj.set_current_language("fr")
        self.assertEqual(obj.content, "Bonjour")
        obj.set_current_language("nl")
        self.assertEqual(obj.content, "Hallo")

    def test_answer_option_write_serializer_update_sets_translations_and_fields(self):
        q = self._make_question()
        o = self._make_option(q, is_correct=False, sort_order=2, content_fr="OldFR", content_nl="OldNL")

        payload = {
            "is_correct": True,
            "sort_order": 1,
            "translations": {
                "fr": {"content": "NewFR"},
                "nl": {"content": "NewNL"},
            },
        }
        ser = QuestionAnswerOptionWriteSerializer(instance=o, data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)

        obj = ser.save()
        obj.refresh_from_db()
        self.assertTrue(obj.is_correct)
        self.assertEqual(obj.sort_order, 1)

        obj.set_current_language("fr")
        self.assertEqual(obj.content, "NewFR")
        obj.set_current_language("nl")
        self.assertEqual(obj.content, "NewNL")

    # ------------------------------------------------------------------
    # QuestionInQuizQuestionSerializer / QuestionReadSerializer : hide/show is_correct
    # ------------------------------------------------------------------
    def test_question_in_quiz_serializer_hides_is_correct_by_default(self):
        q = self._make_question()
        self._make_option(q, is_correct=True, sort_order=1)
        self._make_option(q, is_correct=False, sort_order=2)

        ser = QuestionInQuizQuestionSerializer(
            q,
            context={"view": DummyView(swagger_fake_view=False)},
            show_correct=False,
        )
        data = ser.data
        self.assertIn("answer_options", data)
        self.assertNotIn("is_correct", data["answer_options"][0])  # masqué

    def test_question_in_quiz_serializer_shows_is_correct_when_flag_true(self):
        q = self._make_question()
        self._make_option(q, is_correct=True, sort_order=1)

        ser = QuestionInQuizQuestionSerializer(
            q,
            context={"view": DummyView(swagger_fake_view=False)},
            show_correct=True,
        )
        data = ser.data
        self.assertIn("is_correct", data["answer_options"][0])

    def test_question_read_serializer_hides_is_correct_by_default(self):
        q = self._make_question(title="T")
        self._make_option(q, is_correct=True, sort_order=1)

        ser = QuestionReadSerializer(
            q,
            context={"view": DummyView(swagger_fake_view=False)},
            show_correct=False,
        )
        data = ser.data
        self.assertEqual(data["title"], "T")
        self.assertNotIn("is_correct", data["answer_options"][0])

    def test_question_read_serializer_shows_is_correct_when_flag_true(self):
        q = self._make_question()
        self._make_option(q, is_correct=True, sort_order=1)

        ser = QuestionReadSerializer(
            q,
            context={"view": DummyView(swagger_fake_view=False)},
            show_correct=True,
        )
        data = ser.data
        self.assertIn("is_correct", data["answer_options"][0])

    # ------------------------------------------------------------------
    # QuestionWriteSerializer.validate + create/update
    # ------------------------------------------------------------------
    def test_question_write_validate_create_requires_translations(self):
        domain = self._make_domain()
        payload = {
            "domain": domain.id,
            "allow_multiple_correct": False,
            "active": True,
            "is_mode_practice": True,
            "is_mode_exam": False,
            # translations manquant
        }
        ser = QuestionWriteSerializer(data=payload, context={"view": DummyView(False)})
        self.assertFalse(ser.is_valid())
        self.assertIn("translations", ser.errors)

    def test_question_write_validate_rejects_extra_translation_language(self):
        domain = self._make_domain(allowed_codes=("fr", "nl"))
        payload = {
            "domain": domain.id,
            "translations": {
                "fr": {"title": "T"},
                "nl": {"title": "T"},
                "de": {"title": "T"},  # extra -> interdit
            },
            "allow_multiple_correct": False,
            "active": True,
            "is_mode_practice": True,
            "is_mode_exam": False,
        }
        ser = QuestionWriteSerializer(data=payload, context={"view": DummyView(False)})
        self.assertFalse(ser.is_valid())
        self.assertIn("translations", ser.errors)

    def test_question_write_validate_missing_language_only_fails_on_create(self):
        # Sur CREATE, missing doit échouer (tu as "if missing and is_create")
        domain = self._make_domain(allowed_codes=("fr", "nl"))
        payload = {
            "domain": domain.id,
            "translations": {"fr": {"title": "T"}},  # nl manquant
            "allow_multiple_correct": False,
            "active": True,
            "is_mode_practice": True,
            "is_mode_exam": False,
        }
        ser = QuestionWriteSerializer(data=payload, context={"view": DummyView(False)})
        self.assertFalse(ser.is_valid())
        self.assertIn("translations", ser.errors)

    def test_question_write_validate_answer_options_rules_on_create(self):
        domain = self._make_domain(allowed_codes=("fr", "nl"))

        # moins de 2 réponses
        payload = {
            "domain": domain.id,
            "translations": {"fr": {"title": "T"}, "nl": {"title": "T"}},
            "allow_multiple_correct": False,
            "active": True,
            "is_mode_practice": True,
            "is_mode_exam": False,
            "answer_options": [
                {"is_correct": True, "sort_order": 1, "translations": {"fr": {"content": "A"}, "nl": {"content": "A"}}}
            ],
        }
        ser = QuestionWriteSerializer(data=payload, context={"view": DummyView(False)})
        self.assertFalse(ser.is_valid())
        self.assertIn("answer_options", ser.errors)

        # 2 réponses mais 0 correct
        payload["answer_options"] = [
            {"is_correct": False, "sort_order": 1, "translations": {"fr": {"content": "A"}, "nl": {"content": "A"}}},
            {"is_correct": False, "sort_order": 2, "translations": {"fr": {"content": "B"}, "nl": {"content": "B"}}},
        ]
        ser = QuestionWriteSerializer(data=payload, context={"view": DummyView(False)})
        self.assertFalse(ser.is_valid())
        self.assertIn("answer_options", ser.errors)

        # 2 réponses, 2 correct mais allow_multiple_correct=False
        payload["answer_options"] = [
            {"is_correct": True, "sort_order": 1, "translations": {"fr": {"content": "A"}, "nl": {"content": "A"}}},
            {"is_correct": True, "sort_order": 2, "translations": {"fr": {"content": "B"}, "nl": {"content": "B"}}},
        ]
        ser = QuestionWriteSerializer(data=payload, context={"view": DummyView(False)})
        self.assertFalse(ser.is_valid())
        self.assertIn("answer_options", ser.errors)

        # OK : 1 seul correct
        payload["answer_options"] = [
            {"is_correct": True, "sort_order": 1, "translations": {"fr": {"content": "A"}, "nl": {"content": "A"}}},
            {"is_correct": False, "sort_order": 2, "translations": {"fr": {"content": "B"}, "nl": {"content": "B"}}},
        ]
        ser = QuestionWriteSerializer(data=payload, context={"view": DummyView(False)})
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_question_write_create_creates_subjects_translations_and_options(self):
        domain = self._make_domain(allowed_codes=("fr", "nl"))
        s1 = self._make_subject("Math")
        s2 = self._make_subject("History")

        payload = {
            "domain": domain.id,
            "translations": {
                "fr": {"title": "Titre FR", "description": "D", "explanation": "E"},
                "nl": {"title": "Titel NL", "description": "D", "explanation": "E"},
            },
            "allow_multiple_correct": False,
            "active": True,
            "is_mode_practice": True,
            "is_mode_exam": False,
            "subject_ids": [s1.id, s2.id],
            "answer_options": [
                {"is_correct": True, "sort_order": 1, "translations": {"fr": {"content": "A"}, "nl": {"content": "A"}}},
                {"is_correct": False, "sort_order": 2, "translations": {"fr": {"content": "B"}, "nl": {"content": "B"}}},
            ],
        }

        ser = QuestionWriteSerializer(data=payload, context={"view": DummyView(False)})
        self.assertTrue(ser.is_valid(), ser.errors)

        q = ser.save()
        self.assertEqual(q.domain_id, domain.id)
        self.assertEqual(q.subjects.count(), 2)

        q.set_current_language("fr")
        self.assertEqual(q.title, "Titre FR")
        q.set_current_language("nl")
        self.assertEqual(q.title, "Titel NL")

        self.assertEqual(q.answer_options.count(), 2)
        ao1 = q.answer_options.order_by("sort_order").first()
        ao1.set_current_language("fr")
        self.assertEqual(ao1.content, "A")

    def test_question_write_update_partial_translations_does_not_require_all_langs(self):
        # ton validate: missing languages ne doit PAS échouer sur update
        domain = self._make_domain(allowed_codes=("fr", "nl"))
        q = self._make_question(domain=domain, title="Old", allow_multiple_correct=False)

        payload = {
            "translations": {"fr": {"title": "New FR only"}},  # nl manquant OK en update
        }
        ser = QuestionWriteSerializer(instance=q, data=payload, partial=True, context={"view": DummyView(False)})
        self.assertTrue(ser.is_valid(), ser.errors)

        q2 = ser.save()
        q2.set_current_language("fr")
        self.assertEqual(q2.title, "New FR only")

    def test_question_write_validate_allow_multiple_correct_update_checks_db_options(self):
        domain = self._make_domain(allowed_codes=("fr", "nl"))
        q = self._make_question(domain=domain, allow_multiple_correct=True)
        # DB: 2 correct
        self._make_option(q, is_correct=True, sort_order=1)
        self._make_option(q, is_correct=True, sort_order=2)

        # on veut mettre allow_multiple_correct=False sans fournir answer_options => doit refuser
        payload = {"allow_multiple_correct": False}
        ser = QuestionWriteSerializer(instance=q, data=payload, partial=True, context={"view": DummyView(False)})
        self.assertFalse(ser.is_valid())
        self.assertIn("answer_options", ser.errors)
