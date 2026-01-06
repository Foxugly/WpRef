# question/tests/tests_serializers.py
from __future__ import annotations

import json
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import translation
from rest_framework.exceptions import ValidationError as DRFValidationError

from domain.models import Domain
from language.models import Language
from subject.models import Subject

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

User = get_user_model()


@dataclass
class DummyView:
    swagger_fake_view: bool = False


@override_settings(LANGUAGES=(("fr", "Français"), ("nl", "Nederlands"), ("en", "English")))
class QuestionSerializersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="owner", password="pass")

        # Languages (modèle Language) + subset autorisé côté Domain
        cls.lang_fr = Language.objects.create(code="fr", name="Français", active=True)
        cls.lang_nl = Language.objects.create(code="nl", name="Nederlands", active=True)
        cls.lang_en = Language.objects.create(code="en", name="English", active=True)

        cls.domain = Domain.objects.create(owner=cls.owner, active=True)
        # autoriser fr + nl uniquement pour tester missing/extra
        cls.domain.allowed_languages.set([cls.lang_fr, cls.lang_nl])

        # Subject avec traductions
        cls.subject = Subject.objects.create(domain=cls.domain)
        cls.subject.set_current_language("fr")
        cls.subject.name = "Mathématiques"
        cls.subject.description = ""
        cls.subject.save()

        # Une question de base + traductions
        cls.q = Question.objects.create(domain=cls.domain)
        cls.q.set_current_language("fr")
        cls.q.title = "Titre FR"
        cls.q.description = "Desc FR"
        cls.q.explanation = "Expl FR"
        cls.q.save()

        # answer options (fr/nl)
        cls.ao1 = AnswerOption.objects.create(question=cls.q, is_correct=True, sort_order=1)
        cls.ao1.set_current_language("fr")
        cls.ao1.content = "A"
        cls.ao1.save()
        cls.ao1.set_current_language("nl")
        cls.ao1.content = "A (nl)"
        cls.ao1.save()

        cls.ao2 = AnswerOption.objects.create(question=cls.q, is_correct=False, sort_order=2)
        cls.ao2.set_current_language("fr")
        cls.ao2.content = "B"
        cls.ao2.save()
        cls.ao2.set_current_language("nl")
        cls.ao2.content = "B (nl)"
        cls.ao2.save()

    # ---------------------------------------------------------------------
    # Inline serializer (multipart schema)
    # ---------------------------------------------------------------------
    def test_question_multipart_write_serializer_requires_translations(self):
        ser = QuestionWriteSerializer(data={"domain": self.domain.id,})
        self.assertFalse(ser.is_valid())
        self.assertIn("translations", ser.errors)

    def test_question_write_serializer_accepts_payload(self):
        payload = {
            "domain": self.domain.id,
            "translations": {"fr": {"title": "T", "description": "", "explanation": ""},
                             "nl": {"title": "T (nl)", "description": "", "explanation": ""},},
            "subject_ids": [self.subject.id],
            "answer_options": [
                    {
                        "is_correct": True,
                        "sort_order": 1,
                        "translations": {"fr": {"content": "A"}, "nl": {"content": "A"}},
                    },
                    {
                        "is_correct": False,
                        "sort_order": 2,
                        "translations": {"fr": {"content": "B"}, "nl": {"content": "B"}},
                    },
                ],
            "media": json.dumps([{"kind": "external", "external_url": "https://example.com", "sort_order": 1}]),
            "media_files": [
                SimpleUploadedFile("img.png", b"fake", content_type="image/png"),
            ],
        }
        ser = QuestionWriteSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)

    # ---------------------------------------------------------------------
    # Lite / Media / AnswerOption serializers
    # ---------------------------------------------------------------------
    def test_question_lite_serializer_title(self):
        data = QuestionLiteSerializer(self.q).data
        self.assertEqual(data["id"], self.q.id)
        self.assertEqual(data["title"], "Titre FR")

    def test_question_media_serializer_read_only_fields_exist(self):
        # Juste pour couvrir le serializer; le modèle QuestionMedia clean est ailleurs.
        m = QuestionMedia.objects.create(question=self.q, kind=QuestionMedia.EXTERNAL, external_url="https://x", sort_order=1)
        data = QuestionMediaSerializer(m).data
        self.assertIn("id", data)
        self.assertIn("kind", data)
        self.assertIn("external_url", data)

    def test_answer_option_read_serializer_content(self):
        translation.activate("fr")
        self.ao1.set_current_language("fr")
        data = QuestionAnswerOptionReadSerializer(self.ao1).data
        self.assertEqual(data["content"], "A")
        self.assertTrue(data["is_correct"])
        self.assertEqual(data["sort_order"], 1)
        translation.deactivate()

    def test_answer_option_write_serializer_create_and_update(self):
        # create
        payload = {
            "is_correct": False,
            "sort_order": 3,
            "translations": {"fr": {"content": "C"}, "nl": {"content": "C (nl)"}},
        }
        ser = QuestionAnswerOptionWriteSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
        opt = ser.save(question=self.q)

        opt.set_current_language("fr")
        self.assertEqual(opt.content, "C")
        opt.set_current_language("nl")
        self.assertEqual(opt.content, "C (nl)")

        # update
        upd = {
            "is_correct": True,
            "sort_order": 9,
            "translations": {"fr": {"content": "C2"}, "nl": {"content": "C2 (nl)"}},
        }
        ser2 = QuestionAnswerOptionWriteSerializer(instance=opt, data=upd)
        self.assertTrue(ser2.is_valid(), ser2.errors)
        opt2 = ser2.save()

        self.assertTrue(opt2.is_correct)
        self.assertEqual(opt2.sort_order, 9)
        opt2.set_current_language("fr")
        self.assertEqual(opt2.content, "C2")

    # ---------------------------------------------------------------------
    # Masquage du champ is_correct selon show_correct + swagger_fake_view
    # ---------------------------------------------------------------------
    def test_question_in_quiz_serializer_hides_is_correct_by_default(self):
        ser = QuestionInQuizQuestionSerializer(
            self.q,
            context={"view": DummyView(swagger_fake_view=False)},
            show_correct=False,
        )
        data = ser.data
        # is_correct doit être absent
        self.assertNotIn("is_correct", data["answer_options"][0])

    def test_question_in_quiz_serializer_keeps_is_correct_if_show_correct(self):
        ser = QuestionInQuizQuestionSerializer(
            self.q,
            context={"view": DummyView(swagger_fake_view=False)},
            show_correct=True,
        )
        data = ser.data
        self.assertIn("is_correct", data["answer_options"][0])

    def test_question_in_quiz_serializer_keeps_is_correct_in_swagger(self):
        ser = QuestionInQuizQuestionSerializer(
            self.q,
            context={"view": DummyView(swagger_fake_view=True)},
            show_correct=False,
        )
        data = ser.data
        self.assertIn("is_correct", data["answer_options"][0])

    def test_question_read_serializer_hides_is_correct_by_default(self):
        ser = QuestionReadSerializer(self.q, context={"view": DummyView(swagger_fake_view=False)}, show_correct=False)
        data = ser.data
        self.assertNotIn("is_correct", data["answer_options"][0])

    def test_question_read_serializer_keeps_is_correct_in_swagger(self):
        ser = QuestionReadSerializer(self.q, context={"view": DummyView(swagger_fake_view=True)}, show_correct=False)
        data = ser.data
        self.assertIn("is_correct", data["answer_options"][0])

    # ---------------------------------------------------------------------
    # QuestionWriteSerializer.validate()
    # ---------------------------------------------------------------------
    def _base_create_payload(self):
        return {
            "domain": self.domain.id,
            "translations": {
                "fr": {"title": "Nouvelle Q", "description": "", "explanation": ""},
                "nl": {"title": "Nieuwe Q", "description": "", "explanation": ""},
            },
            "allow_multiple_correct": False,
            "active": True,
            "is_mode_practice": True,
            "is_mode_exam": False,
            "subject_ids": [self.subject.id],
            "answer_options": [
                {
                    "is_correct": True,
                    "sort_order": 1,
                    "translations": {"fr": {"content": "A"}, "nl": {"content": "A"}},
                },
                {
                    "is_correct": False,
                    "sort_order": 2,
                    "translations": {"fr": {"content": "B"}, "nl": {"content": "B"}},
                },
            ],
        }

    def test_write_validate_requires_domain(self):
        payload = self._base_create_payload()
        payload.pop("domain")
        ser = QuestionWriteSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        self.assertIn("domain", ser.errors)

    def test_write_validate_create_requires_translations(self):
        payload = self._base_create_payload()
        payload.pop("translations")
        ser = QuestionWriteSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        self.assertIn("translations", ser.errors)

    def test_write_validate_translations_missing_allowed_langs_on_create(self):
        payload = self._base_create_payload()
        payload["translations"] = {"fr": {"title": "X"}}  # manque nl
        ser = QuestionWriteSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        self.assertIn("translations", ser.errors)
        self.assertIn("Langues manquantes", str(ser.errors["translations"][0]))

    def test_write_validate_translations_extra_langs(self):
        payload = self._base_create_payload()
        payload["translations"]["en"] = {"title": "EN"}  # extra non autorisée (domain allowed fr/nl)
        ser = QuestionWriteSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        self.assertIn("translations", ser.errors)
        self.assertIn("Langues non autorisées", str(ser.errors["translations"][0]))

    def test_write_validate_answer_options_min_2_on_create(self):
        payload = self._base_create_payload()
        payload["answer_options"] = payload["answer_options"][:1]
        ser = QuestionWriteSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        self.assertIn("answer_options", ser.errors)
        self.assertIn("Au moins 2", str(ser.errors["answer_options"][0]))

    def test_write_validate_answer_options_requires_one_correct(self):
        payload = self._base_create_payload()
        payload["answer_options"][0]["is_correct"] = False
        ser = QuestionWriteSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        self.assertIn("answer_options", ser.errors)
        self.assertIn("au moins une réponse correcte", str(ser.errors["answer_options"][0]).lower())

    def test_write_validate_answer_options_only_one_correct_if_not_multiple(self):
        payload = self._base_create_payload()
        payload["answer_options"][1]["is_correct"] = True  # 2 corrects
        payload["allow_multiple_correct"] = False
        ser = QuestionWriteSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        self.assertIn("answer_options", ser.errors)
        self.assertIn("Une seule", str(ser.errors["answer_options"][0]))

    def test_write_validate_answer_options_translations_missing_lang(self):
        payload = self._base_create_payload()
        payload["answer_options"][0]["translations"] = {"fr": {"content": "A"}}  # manque nl
        ser = QuestionWriteSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        # clé dynamique answer_options[i].translations
        key = "answer_options[0].translations"
        self.assertIn(key, ser.errors)
        self.assertIn("Langues manquantes", str(ser.errors[key][0]))

    def test_write_validate_answer_options_translations_extra_lang(self):
        payload = self._base_create_payload()
        payload["answer_options"][0]["translations"]["en"] = {"content": "A"}  # extra
        ser = QuestionWriteSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        key = "answer_options[0].translations"
        self.assertIn(key, ser.errors)
        self.assertIn("Langues non autorisées", str(ser.errors[key][0]))

    # ---------------------------------------------------------------------
    # QuestionWriteSerializer.create()
    # ---------------------------------------------------------------------
    def test_write_create_creates_question_subjects_translations_and_options(self):
        payload = self._base_create_payload()
        ser = QuestionWriteSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
        q = ser.save()

        # subjects
        self.assertEqual(list(q.subjects.values_list("id", flat=True)), [self.subject.id])

        # translations
        q.set_current_language("fr")
        self.assertEqual(q.title, "Nouvelle Q")
        q.set_current_language("nl")
        self.assertEqual(q.title, "Nieuwe Q")

        # options recreated with allowed langs
        self.assertEqual(q.answer_options.count(), 2)
        opt = q.answer_options.order_by("sort_order").first()
        self.assertTrue(opt.is_correct)
        opt.set_current_language("fr")
        self.assertEqual(opt.content, "A")
        opt.set_current_language("nl")
        self.assertEqual(opt.content, "A")

    def test_write_create_raises_if_translations_missing_even_if_validate_not_called(self):
        # couvre la garde dans create() : if not translations: raise
        payload = self._base_create_payload()
        payload.pop("translations")
        ser = QuestionWriteSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        self.assertIn("translations", ser.errors)

    # ---------------------------------------------------------------------
    # QuestionWriteSerializer.update()
    # ---------------------------------------------------------------------
    def test_write_update_updates_simple_fields_subjects_translations_and_options(self):
        # question existante + subject initial
        self.q.subjects.set([self.subject])

        # nouveau subject
        s2 = Subject.objects.create(domain=self.domain)
        s2.set_current_language("fr")
        s2.name = "Physique"
        s2.description = ""
        s2.save()

        payload = {
            "domain": self.domain.id,
            "allow_multiple_correct": True,
            "subject_ids": [s2.id],
            "translations": {
                "fr": {"title": "Titre FR upd", "description": "d", "explanation": "e"},
                "nl": {"title": "Titel NL upd", "description": "", "explanation": ""},
            },
            "answer_options": [
                {
                    "is_correct": True,
                    "sort_order": 1,
                    "translations": {"fr": {"content": "X"}, "nl": {"content": "X"}},
                },
                {
                    "is_correct": True,  # multiple correct now allowed
                    "sort_order": 2,
                    "translations": {"fr": {"content": "Y"}, "nl": {"content": "Y"}},
                },
            ],
        }
        ser = QuestionWriteSerializer(instance=self.q, data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
        q2 = ser.save()

        # subjects
        self.assertEqual(list(q2.subjects.values_list("id", flat=True)), [s2.id])

        # translations updated
        q2.set_current_language("fr")
        self.assertEqual(q2.title, "Titre FR upd")

        # options wiped + recreated
        self.assertEqual(q2.answer_options.count(), 2)
        self.assertEqual(q2.answer_options.filter(is_correct=True).count(), 2)

    def test_write_update_subject_ids_none_keeps_subjects(self):
        self.q.subjects.set([self.subject])

        payload = {
            "domain": self.domain.id,
            # pas de subject_ids => None => ne touche pas aux subjects
            "translations": {
                "fr": {"title": "Keep subjects", "description": "", "explanation": ""},
                "nl": {"title": "Keep subjects", "description": "", "explanation": ""},
            },
        }
        ser = QuestionWriteSerializer(instance=self.q, data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
        q2 = ser.save()
        self.assertEqual(list(q2.subjects.values_list("id", flat=True)), [self.subject.id])

    def test_write_update_allow_multiple_correct_change_checks_db_when_no_answer_options(self):
        # force état DB: 2 corrects
        self.q.allow_multiple_correct = True
        self.q.save()
        self.q.answer_options.update(is_correct=True)

        payload = {
            "domain": self.domain.id,
            "allow_multiple_correct": False,  # interdit si DB a 2 corrects
            # pas de answer_options dans attrs => branche elif dans validate()
            "translations": {
                "fr": {"title": "X", "description": "", "explanation": ""},
                "nl": {"title": "X", "description": "", "explanation": ""},
            },
        }
        ser = QuestionWriteSerializer(instance=self.q, data=payload)
        self.assertFalse(ser.is_valid())
        self.assertIn("answer_options", ser.errors)
        self.assertIn("Une seule", str(ser.errors["answer_options"][0]))

    def test_write_update_allow_multiple_correct_change_ok_when_db_has_one_correct(self):
        # 1 seul correct
        self.q.allow_multiple_correct = True
        self.q.save()
        self.q.answer_options.update(is_correct=False)
        self.ao1.is_correct = True
        self.ao1.save(update_fields=["is_correct"])

        payload = {
            "domain": self.domain.id,
            "allow_multiple_correct": False,  # OK car DB == 1 correct
            "translations": {
                "fr": {"title": "OK", "description": "", "explanation": ""},
                "nl": {"title": "OK", "description": "", "explanation": ""},
            },
        }
        ser = QuestionWriteSerializer(instance=self.q, data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
        ser.save()
