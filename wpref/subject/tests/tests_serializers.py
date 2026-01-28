# subject/tests/test_serializers.py
from __future__ import annotations

from django.test import TestCase, override_settings
from django.utils import translation

from django.contrib.auth import get_user_model
from rest_framework import serializers

from domain.models import Domain
from subject.models import Subject
from subject.serializers import (
    QuestionInSubjectSerializer,
    SubjectWriteSerializer,
    SubjectReadSerializer,
    SubjectDetailSerializer,
)

from question.models import Question, QuestionSubject

User = get_user_model()


@override_settings(LANGUAGES=(("fr", "Français"), ("nl", "Nederlands"), ("en", "English")))
class SubjectSerializersTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="owner", password="pwd")

        # Domain (Parler)
        cls.domain = Domain.objects.create(owner=cls.owner, active=True)
        cls._set_parler(cls.domain, "fr", name="Domaine FR", description="Desc FR")
        cls._set_parler(cls.domain, "nl", name="Domein NL", description="Desc NL")

        # Subject (Parler)
        cls.subject = Subject.objects.create(domain=cls.domain, active=True)
        cls._set_parler(cls.subject, "fr", name="Sujet FR", description="SDesc FR")
        cls._set_parler(cls.subject, "nl", name="Onderwerp NL", description="SDesc NL")

    def setUp(self):
        translation.activate("fr")

    def tearDown(self):
        translation.deactivate_all()
        super().tearDown()

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    @staticmethod
    def _set_parler(obj, lang: str, **fields):
        obj.set_current_language(lang)
        for k, v in fields.items():
            setattr(obj, k, v)
        obj.save()
        return obj

    def _make_question_linked_to_subject(
        self,
        *,
        subject: Subject,
        active: bool = True,
        titles: dict[str, str] | None = None,
        sort_order: int = 0,
    ) -> Question:
        """
        Question requires domain + Parler translations(title).
        Subject link is via through model QuestionSubject.
        """
        titles = titles or {"fr": "Q FR", "nl": "Q NL"}

        q = Question.objects.create(domain=subject.domain, active=active)

        # Parler title translations
        for lang, title in titles.items():
            q.set_current_language(lang)
            q.title = title
            q.save()

        QuestionSubject.objects.create(question=q, subject=subject, sort_order=sort_order)
        return q

    # ---------------------------------------------------------------------
    # QuestionInSubjectSerializer
    # ---------------------------------------------------------------------
    def test_question_in_subject_serializer_returns_titles_by_language(self):
        q = self._make_question_linked_to_subject(
            subject=self.subject,
            active=True,
            titles={"fr": "Titre FR", "nl": "Titel NL"},
        )
        data = QuestionInSubjectSerializer(q).data

        self.assertEqual(data["id"], q.id)
        self.assertIn("fr", data["title"])
        self.assertEqual(data["title"]["fr"]["title"], "Titre FR")
        self.assertEqual(data["title"]["nl"]["title"], "Titel NL")

    # ---------------------------------------------------------------------
    # SubjectWriteSerializer - validate
    # ---------------------------------------------------------------------
    def test_subject_write_serializer_requires_translations(self):
        s = SubjectWriteSerializer(data={"domain": self.domain.id, "active": True})
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)

    def test_subject_write_serializer_rejects_unknown_language_codes(self):
        payload = {
            "domain": self.domain.id,
            "active": True,
            "translations": {"xx": {"name": "Bad", "description": ""}},
        }
        s = SubjectWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)
        self.assertIn("Langues inconnues", str(s.errors["translations"][0]))

    def test_subject_write_serializer_requires_at_least_one_name(self):
        payload = {
            "domain": self.domain.id,
            "active": True,
            "translations": {"fr": {"name": "", "description": ""}, "nl": {"description": "x"}},
        }
        s = SubjectWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)
        self.assertIn("Au moins un 'name' est requis", str(s.errors["translations"][0]))

    # ---------------------------------------------------------------------
    # SubjectWriteSerializer - create
    # ---------------------------------------------------------------------
    def test_subject_write_serializer_create_applies_translations(self):
        payload = {
            "domain": self.domain.id,
            "active": True,
            "translations": {
                "fr": {"name": "Math", "description": "Desc FR"},
                "nl": {"name": "Wiskunde", "description": "Desc NL"},
            },
        }
        s = SubjectWriteSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

        obj = s.save()
        obj.refresh_from_db()

        obj.set_current_language("fr")
        self.assertEqual(obj.name, "Math")
        self.assertEqual(obj.description, "Desc FR")

        obj.set_current_language("nl")
        self.assertEqual(obj.name, "Wiskunde")
        self.assertEqual(obj.description, "Desc NL")

    # ---------------------------------------------------------------------
    # SubjectWriteSerializer - update
    # ---------------------------------------------------------------------
    def test_subject_write_serializer_update_can_change_active_and_translations(self):
        subj = Subject.objects.create(domain=self.domain, active=True)
        self._set_parler(subj, "fr", name="Avant", description="")

        payload = {
            "domain": self.domain.id,
            "active": False,
            "translations": {"fr": {"name": "Après", "description": "Nouvelle desc"}},
        }
        s = SubjectWriteSerializer(instance=subj, data=payload)
        self.assertTrue(s.is_valid(), s.errors)

        obj = s.save()
        obj.refresh_from_db()

        self.assertFalse(obj.active)
        obj.set_current_language("fr")
        self.assertEqual(obj.name, "Après")
        self.assertEqual(obj.description, "Nouvelle desc")

    def test_subject_write_serializer_update_without_translations_keeps_existing_translations(self):
        subj = Subject.objects.create(domain=self.domain, active=True)
        self._set_parler(subj, "fr", name="Titre FR", description="D")

        s = SubjectWriteSerializer(instance=subj, data={"domain": self.domain.id, "active": False, "translations": {"fr": {"name": "Titre FR"}}})
        self.assertTrue(s.is_valid(), s.errors)
        s.save()

        subj.refresh_from_db()
        subj.set_current_language("fr")
        self.assertEqual(subj.name, "Titre FR")
        self.assertFalse(subj.active)

    # ---------------------------------------------------------------------
    # SubjectReadSerializer
    # ---------------------------------------------------------------------
    def test_subject_read_serializer_outputs_domain_name_per_translation_language(self):
        data = SubjectReadSerializer(self.subject).data

        self.assertEqual(data["id"], self.subject.id)
        self.assertEqual(data["domain"], self.domain.id)
        self.assertTrue(data["active"])

        self.assertIn("fr", data["translations"])
        self.assertEqual(data["translations"]["fr"]["name"], "Sujet FR")
        self.assertEqual(data["translations"]["fr"]["domain_name"], "Domaine FR")

        self.assertIn("nl", data["translations"])
        self.assertEqual(data["translations"]["nl"]["name"], "Onderwerp NL")
        self.assertEqual(data["translations"]["nl"]["domain_name"], "Domein NL")

    # ---------------------------------------------------------------------
    # SubjectDetailSerializer
    # ---------------------------------------------------------------------
    def test_subject_detail_serializer_filters_questions_active_only(self):
        q1 = self._make_question_linked_to_subject(subject=self.subject, active=True, titles={"fr": "Q1", "nl": "V1"}, sort_order=1)
        q2 = self._make_question_linked_to_subject(subject=self.subject, active=False, titles={"fr": "Q2", "nl": "V2"}, sort_order=2)
        q3 = self._make_question_linked_to_subject(subject=self.subject, active=True, titles={"fr": "Q3", "nl": "V3"}, sort_order=3)

        data = SubjectDetailSerializer(self.subject).data

        ids = [q["id"] for q in data["questions"]]
        self.assertIn(q1.id, ids)
        self.assertIn(q3.id, ids)
        self.assertNotIn(q2.id, ids)

    def test_subject_detail_serializer_orders_questions_by_id(self):
        # On force un ordre via création ; serializer trie par id
        q1 = self._make_question_linked_to_subject(subject=self.subject, active=True, titles={"fr": "A"}, sort_order=10)
        q2 = self._make_question_linked_to_subject(subject=self.subject, active=True, titles={"fr": "B"}, sort_order=5)
        q3 = self._make_question_linked_to_subject(subject=self.subject, active=True, titles={"fr": "C"}, sort_order=0)

        data = SubjectDetailSerializer(self.subject).data
        ids = [q["id"] for q in data["questions"]]
        self.assertEqual(ids, sorted(ids))

    def test_subject_detail_serializer_includes_question_titles(self):
        q = self._make_question_linked_to_subject(
            subject=self.subject,
            active=True,
            titles={"fr": "Titre FR", "nl": "Titel NL"},
        )

        data = SubjectDetailSerializer(self.subject).data
        item = next(x for x in data["questions"] if x["id"] == q.id)

        self.assertIn("fr", item["title"])
        self.assertEqual(item["title"]["fr"]["title"], "Titre FR")
        self.assertEqual(item["title"]["nl"]["title"], "Titel NL")
