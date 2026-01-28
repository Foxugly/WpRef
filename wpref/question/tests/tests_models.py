from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile

from question.models import (
    Question,
    QuestionSubject,
    MediaAsset,
    QuestionMedia,
    AnswerOption,
)
from domain.models import Domain
from subject.models import Subject

from language.models import Language

User = get_user_model()

class QuestionModelsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        # ---------- User ----------
        cls.owner = User.objects.create_user(
            username="owner",
            email="owner@test.com",
            password="pass",
        )

        # ---------- Languages ----------
        cls.lang_fr = Language.objects.create(code="fr")
        cls.lang_en = Language.objects.create(code="en")

        # ---------- Domain ----------
        cls.domain = Domain.objects.create(owner=cls.owner)
        cls.domain.allowed_languages.set([cls.lang_fr, cls.lang_en])

        cls.domain.set_current_language("fr")
        cls.domain.name = "Domaine FR"
        cls.domain.description = "Description FR"
        cls.domain.save()

        # ---------- Subject ----------
        cls.subject = Subject.objects.create(domain=cls.domain, active=True)

        cls.subject.set_current_language("fr")
        cls.subject.name = "Sujet FR"
        cls.subject.description = "Description Sujet FR"
        cls.subject.save()

    # ==========================================================
    # Question
    # ==========================================================

    def test_question_str_with_translation(self):
        q = Question.objects.create(domain=self.domain)
        q.set_current_language("fr")
        q.title = "Question FR"
        q.save()

        self.assertEqual(str(q), "Question FR")

    def test_question_str_with_existing_translation(self):
        q = Question.objects.create(domain=self.domain)

        q.set_current_language("fr")
        q.title = "Question FR"
        q.save()

        self.assertEqual(str(q), "Question FR")

    def test_question_str_without_translation(self):
        q = Question.objects.create(domain=self.domain)
        q.translations.all().delete()
        self.assertIn(str(q), [f"Question#{q.pk}", 'Question FR'])

    # ==========================================================
    # QuestionSubject
    # ==========================================================

    def test_question_subject_unique_constraint(self):
        q = Question.objects.create(domain=self.domain)
        QuestionSubject.objects.create(question=q, subject=self.subject)

        with self.assertRaises(IntegrityError):
            QuestionSubject.objects.create(question=q, subject=self.subject)

    def test_question_subject_str(self):
        q = Question.objects.create(domain=self.domain)
        qs = QuestionSubject.objects.create(
            question=q,
            subject=self.subject,
            sort_order=3,
        )
        s = str(qs)
        self.assertIn("Q", s)
        self.assertIn("ord:3", s)

    # ==========================================================
    # MediaAsset.clean()
    # ==========================================================

    def test_mediaasset_external_valid(self):
        asset = MediaAsset(
            kind=MediaAsset.EXTERNAL,
            external_url="https://example.com/video",
        )
        asset.full_clean()  # ne doit pas lever

    def test_mediaasset_external_invalid_with_file(self):
        asset = MediaAsset(kind=MediaAsset.EXTERNAL, external_url="https://example.com")
        asset.file = SimpleUploadedFile("x.txt", b"abc", content_type="text/plain")

        self.assertEqual(MediaAsset.EXTERNAL, "external")
        self.assertEqual(asset.kind, "external")
        self.assertTrue(bool(asset.file))
        with self.assertRaises(ValidationError):
            asset.clean()

    def test_mediaasset_file_valid(self):
        asset = MediaAsset(
            kind=MediaAsset.IMAGE,
            file=SimpleUploadedFile("img.png", b"abc"),
            sha256="a" * 64,
        )
        asset.full_clean()

    def test_mediaasset_file_missing_sha256(self):
        asset = MediaAsset(
            kind=MediaAsset.IMAGE,
            file=SimpleUploadedFile("img.png", b"abc"),
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_mediaasset_file_with_external_url_invalid(self):
        asset = MediaAsset(
            kind=MediaAsset.VIDEO,
            file=SimpleUploadedFile("vid.mp4", b"abc"),
            external_url="https://example.com",
            sha256="b" * 64,
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_mediaasset_unique_sha256_constraint(self):
        MediaAsset.objects.create(
            kind=MediaAsset.IMAGE,
            file=SimpleUploadedFile("a.png", b"a"),
            sha256="c" * 64,
        )

        with self.assertRaises(ValidationError):
            MediaAsset.objects.create(
                kind=MediaAsset.IMAGE,
                file=SimpleUploadedFile("b.png", b"b"),
                sha256="c" * 64,
            )

    def test_mediaasset_str_external(self):
        asset = MediaAsset.objects.create(
            kind=MediaAsset.EXTERNAL,
            external_url="https://example.com",
        )
        self.assertIn("external", str(asset))

    # ==========================================================
    # QuestionMedia
    # ==========================================================

    def test_question_media_unique_constraint(self):
        q = Question.objects.create(domain=self.domain)
        asset = MediaAsset.objects.create(
            kind=MediaAsset.EXTERNAL,
            external_url="https://example.com",
        )

        QuestionMedia.objects.create(question=q, asset=asset)

        with self.assertRaises(IntegrityError):
            QuestionMedia.objects.create(question=q, asset=asset)

    def test_question_media_str(self):
        q = Question.objects.create(domain=self.domain)
        asset = MediaAsset.objects.create(
            kind=MediaAsset.EXTERNAL,
            external_url="https://example.com",
        )
        qm = QuestionMedia.objects.create(
            question=q,
            asset=asset,
            sort_order=2,
        )
        s = str(qm)
        self.assertIn("Q", s)
        self.assertIn("ord:2", s)

    # ==========================================================
    # AnswerOption
    # ==========================================================

    def test_answer_option_str_correct(self):
        q = Question.objects.create(domain=self.domain)
        ao = AnswerOption.objects.create(
            question=q,
            is_correct=True,
            sort_order=1,
        )
        ao.set_current_language("fr")
        ao.content = "Bonne réponse"
        ao.save()

        self.assertIn("✔", str(ao))

    def test_answer_option_str_incorrect(self):
        q = Question.objects.create(domain=self.domain)
        ao = AnswerOption.objects.create(
            question=q,
            is_correct=False,
            sort_order=2,
        )
        ao.set_current_language("fr")
        ao.content = "Mauvaise réponse"
        ao.save()

        self.assertIn("✗", str(ao))
