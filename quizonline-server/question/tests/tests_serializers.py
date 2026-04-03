# subject/tests/tests_serializers.py
from __future__ import annotations

import hashlib
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils import translation
from rest_framework import serializers

from domain.models import Domain
from language.models import Language
from subject.models import Subject

from question.models import (
    Question,
    AnswerOption,
    MediaAsset,
    QuestionMedia,
)
from question.serializers import (
    QuestionLiteSerializer,
    MediaAssetSerializer,
    QuestionMediaReadSerializer,
    MediaAssetUploadSerializer,
    _sha256_file,
    _infer_kind_from_upload,
    QuestionAnswerOptionPublicReadSerializer,
    QuestionAnswerOptionReadSerializer,
    QuestionAnswerOptionWriteSerializer,
    QuestionInQuizQuestionSerializer,
    QuestionReadSerializer,
    QuestionWriteSerializer,
    _upsert_translations,
)
from question.answer_option_sync import sync_question_answer_options

User = get_user_model()


class QuestionSerializersTestCase(TestCase):
    """
    Tests stables:
    - aucun état mutable partagé entre tests (pas de setUpTestData pour Domain/Subject/Question)
    - création Parler robuste (initialize=True) + refresh DB
    - langue Django reset à chaque test
    """

    # ---------------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------------
    def setUp(self):
        translation.activate("fr")

        # Users
        self.owner = User.objects.create_user(username="owner", password="pwd")
        self.staff = User.objects.create_user(username="staff", password="pwd", is_staff=True)
        self.outsider = User.objects.create_user(username="outsider", password="pwd")

        # Languages (doivent correspondre à settings.LANGUAGES)
        self.lang_fr = Language.objects.create(code="fr", name="Français", active=True)
        self.lang_en = Language.objects.create(code="en", name="English", active=True)

        # Domain + allowed languages
        self.domain = Domain.objects.create(active=True, owner=self.owner)
        self.domain.allowed_languages.set([self.lang_fr, self.lang_en])
        self._set_parler_translation(self.domain, "fr", name="Domaine FR", description="")
        self._set_parler_translation(self.domain, "en", name="Domain EN", description="")

        self.other_domain = Domain.objects.create(active=True, owner=self.owner)
        self.other_domain.allowed_languages.set([self.lang_fr, self.lang_en])
        self._set_parler_translation(self.other_domain, "fr", name="Autre domaine FR", description="")
        self._set_parler_translation(self.other_domain, "en", name="Other domain EN", description="")

        # Subjects
        self.subj1 = Subject.objects.create(domain=self.domain, active=True)
        self._set_parler_translation(self.subj1, "fr", name="Sujet 1 FR", description="")
        self._set_parler_translation(self.subj1, "en", name="Subject 1 EN", description="")

        self.subj2 = Subject.objects.create(domain=self.domain, active=True)
        self._set_parler_translation(self.subj2, "fr", name="Sujet 2 FR", description="")
        self._set_parler_translation(self.subj2, "en", name="Subject 2 EN", description="")

        self.other_subj = Subject.objects.create(domain=self.other_domain, active=True)
        self._set_parler_translation(self.other_subj, "fr", name="Sujet autre FR", description="")
        self._set_parler_translation(self.other_subj, "en", name="Other subject EN", description="")

        # Refetch "clean" (évite caches parler)
        self.domain = Domain.objects.get(pk=self.domain.pk)
        self.other_domain = Domain.objects.get(pk=self.other_domain.pk)
        self.subj1 = Subject.objects.get(pk=self.subj1.pk)
        self.subj2 = Subject.objects.get(pk=self.subj2.pk)
        self.other_subj = Subject.objects.get(pk=self.other_subj.pk)

    def tearDown(self):
        translation.deactivate_all()
        super().tearDown()

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _set_parler_translation(self, obj, lang: str, **fields):
        """
        Helper parler robuste:
        - initialize=True force la création de la traduction si absente
        - refresh_from_db pour éviter tout cache “sale”
        """
        translation_model = obj._parler_meta.root_model
        translation_model.objects.update_or_create(
            master_id=obj.pk,
            language_code=lang,
            defaults=fields,
        )
        obj.refresh_from_db()
        return obj

    def _mk_question_with_translations(self, *, allow_multiple=False) -> Question:
        q = Question.objects.create(domain=self.domain, allow_multiple_correct=allow_multiple)

        self._set_parler_translation(
            q,
            "fr",
            title="Titre FR",
            description="Desc FR",
            explanation="Expl FR",
        )
        self._set_parler_translation(
            q,
            "en",
            title="Title EN",
            description="Desc EN",
            explanation="Expl EN",
        )

        return (
            Question.objects
            .prefetch_related("translations")
            .get(pk=q.pk)
        )

    def _mk_answer_option(self, q: Question, *, is_correct: bool, sort_order: int, fr: str, en: str) -> AnswerOption:
        ao = AnswerOption.objects.create(question=q, is_correct=is_correct, sort_order=sort_order)
        self._set_parler_translation(ao, "fr", content=fr)
        self._set_parler_translation(ao, "en", content=en)
        return AnswerOption.objects.get(pk=ao.pk)

    def _mk_external_asset(self, url="https://www.youtube.com/watch?v=dQw4w9WgXcQ") -> MediaAsset:
        return MediaAsset.objects.create(kind=MediaAsset.EXTERNAL, external_url=url)

    def _mk_image_upload(self, name="img.png", content=b"pngbytes") -> SimpleUploadedFile:
        return SimpleUploadedFile(name=name, content=content, content_type="image/png")

    def _mk_video_upload(self, name="vid.mp4", content=b"mp4bytes") -> SimpleUploadedFile:
        return SimpleUploadedFile(name=name, content=content, content_type="video/mp4")

    # ---------------------------------------------------------------------
    # MediaAssetUploadSerializer
    # ---------------------------------------------------------------------
    def test_media_asset_upload_serializer_requires_exactly_one_of_file_or_url(self):
        s = MediaAssetUploadSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("non_field_errors", s.errors)

        s = MediaAssetUploadSerializer(data={"file": self._mk_image_upload(), "external_url": "https://x.com"})
        self.assertFalse(s.is_valid())
        self.assertIn("non_field_errors", s.errors)

        s = MediaAssetUploadSerializer(data={"external_url": "https://x.com"})
        self.assertTrue(s.is_valid(), s.errors)

        s = MediaAssetUploadSerializer(data={"file": self._mk_image_upload()})
        self.assertTrue(s.is_valid(), s.errors)

    @override_settings(MAX_UPLOAD_FILE_SIZE=4)
    def test_media_asset_upload_serializer_rejects_file_too_large(self):
        s = MediaAssetUploadSerializer(data={"file": self._mk_image_upload(content=b"12345")})
        self.assertFalse(s.is_valid())
        self.assertIn("file", s.errors)
        self.assertIn("Maximum allowed size", str(s.errors["file"]))

    # ---------------------------------------------------------------------
    # _sha256_file / _infer_kind_from_upload
    # ---------------------------------------------------------------------
    def test_sha256_file_matches_expected(self):
        up = SimpleUploadedFile("a.bin", b"hello", content_type="application/octet-stream")
        got = _sha256_file(up)
        exp = hashlib.sha256(b"hello").hexdigest()
        self.assertEqual(got, exp)

    def test_infer_kind_from_upload_image(self):
        up = self._mk_image_upload()
        self.assertEqual(_infer_kind_from_upload(up), MediaAsset.IMAGE)

    def test_infer_kind_from_upload_video(self):
        up = self._mk_video_upload()
        self.assertEqual(_infer_kind_from_upload(up), MediaAsset.VIDEO)

    def test_infer_kind_from_upload_unsupported(self):
        up = SimpleUploadedFile("x.bin", b"x", content_type="application/octet-stream")
        with self.assertRaises(serializers.ValidationError) as ctx:
            _infer_kind_from_upload(up)
        self.assertIn("Unsupported file type", str(ctx.exception.detail))

    # ---------------------------------------------------------------------
    # Read serializers basics
    # ---------------------------------------------------------------------
    def test_question_lite_serializer_title_in_any_language(self):
        q = self._mk_question_with_translations()
        data = QuestionLiteSerializer(q).data
        self.assertEqual(data["id"], q.id)
        self.assertIn(data["title"], ["Titre FR", "Title EN"])

    def test_media_asset_serializer_read_only_fields(self):
        asset = self._mk_external_asset()
        data = MediaAssetSerializer(asset).data
        self.assertEqual(data["kind"], MediaAsset.EXTERNAL)
        self.assertEqual(data["external_url"], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_question_media_read_serializer_nests_asset(self):
        q = self._mk_question_with_translations()
        asset = self._mk_external_asset()
        link = QuestionMedia.objects.create(question=q, asset=asset, sort_order=0)
        data = QuestionMediaReadSerializer(link).data
        self.assertEqual(data["sort_order"], 0)
        self.assertEqual(data["asset"]["external_url"], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    # ---------------------------------------------------------------------
    # Answer option serializers
    # ---------------------------------------------------------------------
    def test_answer_option_public_read_serializer_hides_is_correct(self):
        q = self._mk_question_with_translations()
        ao = self._mk_answer_option(q, is_correct=True, sort_order=0, fr="A FR", en="A EN")
        data = QuestionAnswerOptionPublicReadSerializer(ao).data
        self.assertNotIn("is_correct", data)
        self.assertEqual(data["content"], "A FR")

    def test_answer_option_read_serializer_includes_is_correct(self):
        q = self._mk_question_with_translations()
        ao = self._mk_answer_option(q, is_correct=True, sort_order=0, fr="A FR", en="A EN")
        data = QuestionAnswerOptionReadSerializer(ao, context={"show_correct": True}).data
        self.assertIn("is_correct", data)
        self.assertTrue(data["is_correct"])
        self.assertEqual(data["translations"]["fr"]["content"], "A FR")
        self.assertEqual(data["translations"]["en"]["content"], "A EN")

    def test_answer_option_write_serializer_validate_translations_shape(self):
        payload = {"is_correct": True, "sort_order": 0, "translations": {"fr": {"content": "A"}, "en": {"content": "A"}}}
        s = QuestionAnswerOptionWriteSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

        s = QuestionAnswerOptionWriteSerializer(data={"is_correct": True, "sort_order": 0, "translations": "oops"})
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)

        s = QuestionAnswerOptionWriteSerializer(data={"is_correct": True, "sort_order": 0, "translations": {"fr": "oops"}})
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)

    # ---------------------------------------------------------------------
    # QuestionInQuizQuestionSerializer: switch show_correct + swagger
    # ---------------------------------------------------------------------
    def test_question_in_quiz_serializer_switches_answer_option_serializer(self):
        q = self._mk_question_with_translations()
        self._mk_answer_option(q, is_correct=True, sort_order=0, fr="A", en="A")
        self._mk_answer_option(q, is_correct=False, sort_order=1, fr="B", en="B")

        q = Question.objects.prefetch_related("answer_options__translations", "translations").get(pk=q.pk)

        view = SimpleNamespace(swagger_fake_view=False)

        s = QuestionInQuizQuestionSerializer(q, context={"show_correct": False, "view": view})
        self.assertNotIn("is_correct", s.data["answer_options"][0])

        s2 = QuestionInQuizQuestionSerializer(q, context={"show_correct": True, "view": view})
        self.assertIn("is_correct", s2.data["answer_options"][0])

        view_swagger = SimpleNamespace(swagger_fake_view=True)
        s3 = QuestionInQuizQuestionSerializer(q, context={"show_correct": False, "view": view_swagger})
        self.assertIn("is_correct", s3.data["answer_options"][0])

    # ---------------------------------------------------------------------
    # QuestionReadSerializer: translations + media + switch answer_options
    # ---------------------------------------------------------------------
    def test_question_read_serializer_translations_media_and_answer_options_switch(self):
        q = self._mk_question_with_translations()
        self._mk_answer_option(q, is_correct=True, sort_order=0, fr="A", en="A")
        self._mk_answer_option(q, is_correct=False, sort_order=1, fr="B", en="B")

        asset = self._mk_external_asset("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        QuestionMedia.objects.create(question=q, asset=asset, sort_order=0)

        # Refetch clean + prefetched
        q = (
            Question.objects
            .prefetch_related("translations", "answer_options__translations", "media__asset")
            .get(pk=q.pk)
        )

        view = SimpleNamespace(swagger_fake_view=False)

        s = QuestionReadSerializer(q, context={"show_correct": False, "view": view})
        data = s.data

        self.assertIn("translations", data)
        self.assertIn("fr", data["translations"])
        self.assertEqual(data["translations"]["fr"]["title"], "Titre FR")

        self.assertEqual(data["media"][0]["asset"]["external_url"], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertNotIn("is_correct", data["answer_options"][0])

        s2 = QuestionReadSerializer(q, context={"show_correct": True, "view": view})
        data2 = s2.data
        self.assertIn("is_correct", data2["answer_options"][0])
        self.assertEqual(data2["answer_options"][0]["translations"]["fr"]["content"], "A")
        self.assertEqual(data2["answer_options"][1]["translations"]["en"]["content"], "B")

    def test_question_read_serializer_hides_correctness_without_explicit_context(self):
        q = self._mk_question_with_translations()
        self._mk_answer_option(q, is_correct=True, sort_order=0, fr="A", en="A")
        self._mk_answer_option(q, is_correct=False, sort_order=1, fr="B", en="B")
        q = (
            Question.objects
            .prefetch_related("translations", "answer_options__translations", "media__asset")
            .get(pk=q.pk)
        )

        data = QuestionReadSerializer(q, context={}).data

        self.assertNotIn("is_correct", data["answer_options"][0])

    # ---------------------------------------------------------------------
    # QuestionWriteSerializer: validate + create
    # ---------------------------------------------------------------------
    def _base_question_payload(self):
        return {
            "domain": self.domain.id,
            "translations": {
                "fr": {"title": "Titre FR", "description": "Desc FR", "explanation": "Expl FR"},
                "en": {"title": "Title EN", "description": "Desc EN", "explanation": "Expl EN"},
            },
            "allow_multiple_correct": False,
            "active": True,
            "is_mode_practice": True,
            "is_mode_exam": False,
            "subject_ids": [self.subj1.id, self.subj2.id],
            "answer_options": [
                {"is_correct": True, "sort_order": 0, "translations": {"fr": {"content": "A"}, "en": {"content": "A"}}},
                {"is_correct": False, "sort_order": 1, "translations": {"fr": {"content": "B"}, "en": {"content": "B"}}},
            ],
        }

    def test_question_write_serializer_validate_answer_options_translations_shape(self):
        payload = self._base_question_payload()
        payload["answer_options"][0]["translations"] = "oops"
        s = QuestionWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("answer_options[0].translations", s.errors)

    def test_question_write_serializer_validate_answer_options_missing_lang(self):
        payload = self._base_question_payload()
        payload["answer_options"][0]["translations"].pop("en")
        s = QuestionWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("answer_options[0].translations", s.errors)
        self.assertIn("Langues manquantes", str(s.errors["answer_options[0].translations"]))

    def test_question_write_serializer_rejects_subject_from_other_domain(self):
        payload = self._base_question_payload()
        payload["subject_ids"] = [self.subj1.id, self.other_subj.id]

        s = QuestionWriteSerializer(data=payload, context={"request": SimpleNamespace(user=self.owner)})
        self.assertFalse(s.is_valid())
        self.assertIn("subject_ids", s.errors)
        self.assertIn("Subjects hors domain", str(s.errors["subject_ids"]))

    def test_question_write_serializer_rejects_unmanageable_domain(self):
        payload = self._base_question_payload()
        payload["domain"] = self.other_domain.id

        s = QuestionWriteSerializer(data=payload, context={"request": SimpleNamespace(user=self.outsider)})
        self.assertFalse(s.is_valid())
        self.assertIn("domain", s.errors)
        self.assertIn("Vous ne pouvez pas gerer ce domaine", str(s.errors["domain"]))

    def test_question_write_serializer_rejects_domain_change_if_existing_subjects_do_not_match(self):
        q = self._mk_question_with_translations()
        q.subjects.set([self.subj1])

        payload = {"domain": self.other_domain.id}
        s = QuestionWriteSerializer(instance=q, data=payload, partial=True)

        self.assertFalse(s.is_valid())
        self.assertIn("subject_ids", s.errors)
        self.assertIn("nouveau domain", str(s.errors["subject_ids"]))

    def test_question_write_serializer_create_full(self):
        a1 = self._mk_external_asset("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        a2 = self._mk_external_asset("https://www.youtube.com/watch?v=9bZkp7q19f0")

        payload = self._base_question_payload()
        payload["media_asset_ids"] = [a1.id, a2.id, a1.id]  # duplicate => dedup

        s = QuestionWriteSerializer(data=payload, context={"request": SimpleNamespace(user=self.owner)})
        self.assertTrue(s.is_valid(), s.errors)
        q = s.save()

        q = (
            Question.objects
            .prefetch_related("translations", "answer_options__translations", "media__asset", "subjects")
            .get(pk=q.pk)
        )

        self.assertEqual(q.safe_translation_getter("title", language_code="fr"), "Titre FR")
        self.assertEqual(set(q.subjects.values_list("id", flat=True)), {self.subj1.id, self.subj2.id})

        media_urls = list(q.media.order_by("sort_order").values_list("asset__external_url", flat=True))
        self.assertEqual(
            media_urls,
            [
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "https://www.youtube.com/watch?v=9bZkp7q19f0",
            ],
        )

    def test_question_write_serializer_create_media_asset_ids_missing_raises(self):
        payload = self._base_question_payload()
        payload["media_asset_ids"] = [999999]

        s = QuestionWriteSerializer(data=payload, context={"request": SimpleNamespace(user=self.owner)})
        self.assertTrue(s.is_valid(), s.errors)
        with self.assertRaises(serializers.ValidationError) as ctx:
            s.save()
        self.assertIn("media_asset_ids", ctx.exception.detail)

    def test_question_write_serializer_update_preserves_existing_answer_option_ids(self):
        q = self._mk_question_with_translations()
        first = self._mk_answer_option(q, is_correct=True, sort_order=0, fr="A FR", en="A EN")
        second = self._mk_answer_option(q, is_correct=False, sort_order=1, fr="B FR", en="B EN")

        payload = {
            "allow_multiple_correct": True,
            "answer_options": [
                {
                    "id": first.id,
                    "is_correct": False,
                    "sort_order": 2,
                    "translations": {"fr": {"content": "A2 FR"}, "en": {"content": "A2 EN"}},
                },
                {
                    "id": second.id,
                    "is_correct": True,
                    "sort_order": 1,
                    "translations": {"fr": {"content": "B2 FR"}, "en": {"content": "B2 EN"}},
                },
            ]
        }

        s = QuestionWriteSerializer(instance=q, data=payload, partial=True, context={"request": SimpleNamespace(user=self.owner)})
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()

        option_ids = list(updated.answer_options.order_by("id").values_list("id", flat=True))
        self.assertEqual(option_ids, [first.id, second.id])
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.sort_order, 2)
        self.assertFalse(first.is_correct)
        self.assertEqual(first.safe_translation_getter("content", language_code="fr"), "A2 FR")
        self.assertTrue(second.is_correct)
        self.assertEqual(second.safe_translation_getter("content", language_code="en"), "B2 EN")

    def test_question_write_serializer_update_rejects_removal_of_answer_option_used_in_quiz(self):
        from quiz.models import Quiz, QuizQuestion, QuizQuestionAnswer, QuizTemplate

        q = self._mk_question_with_translations()
        first = self._mk_answer_option(q, is_correct=True, sort_order=0, fr="A FR", en="A EN")
        second = self._mk_answer_option(q, is_correct=False, sort_order=1, fr="B FR", en="B EN")

        template = QuizTemplate.objects.create(title="Serializer Quiz", created_by=self.owner)
        quiz_question = QuizQuestion.objects.create(quiz=template, question=q, sort_order=1, weight=1)
        quiz = Quiz.objects.create(
            quiz_template=template,
            user=self.owner,
            active=True,
            started_at=timezone.now(),
        )
        answer = QuizQuestionAnswer.objects.create(quiz=quiz, quizquestion=quiz_question, question_order=1)
        answer.selected_options.set([second])

        payload = {
            "allow_multiple_correct": True,
            "answer_options": [
                {
                    "id": first.id,
                    "is_correct": True,
                    "sort_order": 0,
                    "translations": {"fr": {"content": "A FR"}, "en": {"content": "A EN"}},
                }
            ]
        }

        s = QuestionWriteSerializer(instance=q, data=payload, partial=True, context={"request": SimpleNamespace(user=self.owner)})
        self.assertTrue(s.is_valid(), s.errors)
        with self.assertRaises(serializers.ValidationError) as ctx:
            s.save()
        self.assertIn("answer_options", ctx.exception.detail)
        self.assertIn("deja utilisees", str(ctx.exception.detail["answer_options"]))

    def test_sync_question_answer_options_rejects_invalid_final_state(self):
        q = self._mk_question_with_translations()
        first = self._mk_answer_option(q, is_correct=True, sort_order=0, fr="A FR", en="A EN")
        self._mk_answer_option(q, is_correct=False, sort_order=1, fr="B FR", en="B EN")

        with self.assertRaises(serializers.ValidationError) as ctx:
            sync_question_answer_options(
                question=q,
                answer_options_data=[
                    {
                        "id": first.id,
                        "is_correct": True,
                        "sort_order": 0,
                        "translations": {"fr": {"content": "A FR"}, "en": {"content": "A EN"}},
                    }
                ],
                allowed_langs={"fr", "en"},
                upsert_translations=_upsert_translations,
            )

        self.assertIn("answer_options", ctx.exception.detail)
        self.assertIn("Au moins 2 réponses", str(ctx.exception.detail["answer_options"]))

    def test_sync_question_answer_options_does_not_query_final_state_when_no_removal(self):
        q = self._mk_question_with_translations()
        first = self._mk_answer_option(q, is_correct=True, sort_order=0, fr="A FR", en="A EN")
        second = self._mk_answer_option(q, is_correct=False, sort_order=1, fr="B FR", en="B EN")

        manager_type = type(q.answer_options)
        with patch.object(manager_type, "exclude", side_effect=AssertionError("exclude should not be called")):
            sync_question_answer_options(
                question=q,
                answer_options_data=[
                    {
                        "id": first.id,
                        "is_correct": True,
                        "sort_order": 0,
                        "translations": {"fr": {"content": "A FR mod"}, "en": {"content": "A EN mod"}},
                    },
                    {
                        "id": second.id,
                        "is_correct": False,
                        "sort_order": 1,
                        "translations": {"fr": {"content": "B FR mod"}, "en": {"content": "B EN mod"}},
                    },
                ],
                allowed_langs={"fr", "en"},
                upsert_translations=_upsert_translations,
            )

    def test_question_write_serializer_update_allows_text_change_for_answer_option_used_in_quiz(self):
        from quiz.models import Quiz, QuizQuestion, QuizQuestionAnswer, QuizTemplate

        q = self._mk_question_with_translations()
        first = self._mk_answer_option(q, is_correct=True, sort_order=0, fr="A FR", en="A EN")
        second = self._mk_answer_option(q, is_correct=False, sort_order=1, fr="B FR", en="B EN")

        template = QuizTemplate.objects.create(title="Serializer Quiz", created_by=self.owner)
        quiz_question = QuizQuestion.objects.create(quiz=template, question=q, sort_order=1, weight=1)
        quiz = Quiz.objects.create(
            quiz_template=template,
            user=self.owner,
            active=True,
            started_at=timezone.now(),
        )
        answer = QuizQuestionAnswer.objects.create(quiz=quiz, quizquestion=quiz_question, question_order=1)
        answer.selected_options.set([second])

        payload = {
            "is_mode_exam": True,
            "answer_options": [
                {
                    "id": first.id,
                    "is_correct": True,
                    "sort_order": 0,
                    "translations": {"fr": {"content": "A FR mod"}, "en": {"content": "A EN mod"}},
                },
                {
                    "id": second.id,
                    "is_correct": False,
                    "sort_order": 1,
                    "translations": {"fr": {"content": "B FR mod"}, "en": {"content": "B EN mod"}},
                },
            ],
        }

        s = QuestionWriteSerializer(instance=q, data=payload, partial=True, context={"request": SimpleNamespace(user=self.owner)})
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()

        updated.refresh_from_db()
        second.refresh_from_db()
        self.assertTrue(updated.is_mode_exam)
        self.assertEqual(second.safe_translation_getter("content", language_code="fr"), "B FR mod")
        self.assertFalse(second.is_correct)

    def test_question_write_serializer_update_rejects_correctness_change_for_answer_option_used_in_quiz(self):
        from quiz.models import Quiz, QuizQuestion, QuizQuestionAnswer, QuizTemplate

        q = self._mk_question_with_translations()
        first = self._mk_answer_option(q, is_correct=True, sort_order=0, fr="A FR", en="A EN")
        second = self._mk_answer_option(q, is_correct=False, sort_order=1, fr="B FR", en="B EN")

        template = QuizTemplate.objects.create(title="Serializer Quiz", created_by=self.owner)
        quiz_question = QuizQuestion.objects.create(quiz=template, question=q, sort_order=1, weight=1)
        quiz = Quiz.objects.create(
            quiz_template=template,
            user=self.owner,
            active=True,
            started_at=timezone.now(),
        )
        answer = QuizQuestionAnswer.objects.create(quiz=quiz, quizquestion=quiz_question, question_order=1)
        answer.selected_options.set([second])

        payload = {
            "allow_multiple_correct": True,
            "answer_options": [
                {
                    "id": first.id,
                    "is_correct": True,
                    "sort_order": 0,
                    "translations": {"fr": {"content": "A FR"}, "en": {"content": "A EN"}},
                },
                {
                    "id": second.id,
                    "is_correct": True,
                    "sort_order": 1,
                    "translations": {"fr": {"content": "B FR"}, "en": {"content": "B EN"}},
                },
            ]
        }

        s = QuestionWriteSerializer(instance=q, data=payload, partial=True, context={"request": SimpleNamespace(user=self.owner)})
        self.assertTrue(s.is_valid(), s.errors)
        with self.assertRaises(serializers.ValidationError) as ctx:
            s.save()
        self.assertIn("answer_options", ctx.exception.detail)
        self.assertIn("correcte/incorrecte", str(ctx.exception.detail["answer_options"]))

    def test_question_read_serializer_uses_prefetched_question_translations(self):
        q = self._mk_question_with_translations()
        self._mk_answer_option(q, is_correct=True, sort_order=0, fr="A FR", en="A EN")
        self._mk_answer_option(q, is_correct=False, sort_order=1, fr="B FR", en="B EN")

        prefetched = (
            Question.objects
            .prefetch_related("translations", "answer_options__translations", "media__asset")
            .get(pk=q.pk)
        )
        serializer = QuestionReadSerializer()

        with self.assertNumQueries(0):
            translations = serializer.get_translations(prefetched)

        self.assertEqual(translations["fr"]["title"], "Titre FR")
        self.assertEqual(translations["en"]["title"], "Title EN")
