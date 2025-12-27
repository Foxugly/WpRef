# question/tests/test_viewset.py
import json
import uuid

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from domain.models import Domain
from language.models import Language
from question.models import Question, AnswerOption, QuestionMedia
from subject.models import Subject

User = get_user_model()


class QuestionViewSetTests(APITestCase):
    # -------------------------
    # urls helpers
    # -------------------------
    def _list_url(self):
        return reverse("api:question-api:question-list")

    def _detail_url(self, q: Question):
        return reverse("api:question-api:question-detail", kwargs={"question_id": q.pk})

    # -------------------------
    # data builders (robustes avec parler)
    # -------------------------
    def _mk_user(self, *, is_staff: bool) -> User:
        u = User.objects.create_user(
            username=f"u_{uuid.uuid4().hex[:8]}",
            password="pass",
            is_staff=is_staff,
        )
        return u

    def _mk_language(self, code: str) -> Language:
        # Au cas où ton modèle Language a d'autres champs requis, on met un fallback simple.
        # Si ton Language a déjà ces codes, get_or_create évite les collisions.
        defaults = {}
        for fname in ("name", "label", "title"):
            if hasattr(Language, fname):
                defaults[fname] = code.upper()
                break
        obj, _ = Language.objects.get_or_create(code=code, defaults=defaults)
        return obj

    def _mk_domain(self, owner: User, allowed_codes=("fr", "nl")) -> Domain:
        d = Domain.objects.create(owner=owner, active=True)
        # parler: champs traduits
        d.set_current_language("fr")
        d.name = "Domain FR"
        d.description = ""
        d.save()

        langs = [self._mk_language(c) for c in allowed_codes]
        d.allowed_languages.set(langs)
        return d

    def _mk_subject(self, *, name_fr="Math", slug_fr="math") -> Subject:
        """
        Subject chez toi semble être un TranslatableModel (slug pas en champ direct),
        donc on évite Subject.objects.create(slug=...) et on fait via parler.
        """
        s = Subject.objects.create()
        if hasattr(s, "set_current_language"):
            s.set_current_language("fr")
        # on set si les attributs existent
        if hasattr(s, "name"):
            s.name = name_fr
        if hasattr(s, "slug"):
            s.slug = slug_fr
        s.save()
        return s

    def _mk_question(
        self,
        domain: Domain,
        *,
        title_fr="Q FR",
        title_nl="Q NL",
        allow_multiple_correct=False,
        with_options=True,
        with_subjects=False,
    ) -> Question:
        q = Question.objects.create(
            domain=domain,
            allow_multiple_correct=allow_multiple_correct,
            active=True,
            is_mode_practice=True,
            is_mode_exam=True,
        )
        q.set_current_language("fr")
        q.title = title_fr
        q.description = "desc fr"
        q.explanation = "expl fr"
        q.save()

        q.set_current_language("nl")
        q.title = title_nl
        q.description = "desc nl"
        q.explanation = "expl nl"
        q.save()

        if with_subjects:
            s = self._mk_subject()
            q.subjects.add(s)

        if with_options:
            self._mk_option(q, is_correct=True, sort_order=1, fr="A", nl="A")
            self._mk_option(q, is_correct=False, sort_order=2, fr="B", nl="B")

        return q

    def _mk_option(self, q: Question, *, is_correct: bool, sort_order: int, fr: str, nl: str) -> AnswerOption:
        o = AnswerOption.objects.create(question=q, is_correct=is_correct, sort_order=sort_order)
        o.set_current_language("fr")
        o.content = fr
        o.save()
        o.set_current_language("nl")
        o.content = nl
        o.save()
        return o

    def _payload_create(self, domain: Domain, subject_ids=None, *, title_fr="T FR", title_nl="T NL"):
        subject_ids = subject_ids or []
        return {
            "domain": domain.pk,
            "translations": {
                "fr": {"title": title_fr, "description": "D FR", "explanation": "E FR"},
                "nl": {"title": title_nl, "description": "D NL", "explanation": "E NL"},
            },
            "allow_multiple_correct": False,
            "active": True,
            "is_mode_practice": True,
            "is_mode_exam": True,
            "subject_ids": subject_ids,
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

    def _payload_create_media(self, domain: Domain, subject_ids=None, *, title_fr="T FR", title_nl="T NL"):
        d = self._payload_create(domain, subject_ids)
        d["media"] = [
                {"kind": "external", "external_url": "https://example.com/1", "sort_order": 1},
            ]
        return d

    def _payload_to_multipart(self, payload: dict) -> dict:
        """
        DRF multipart: pas de dict imbriqués -> on stringify translations/answer_options/media.
        C’est EXACTEMENT ce que ton ViewSet._coerce_json_fields attend.
        """
        out = dict(payload)

        if "translations" in out and isinstance(out["translations"], dict):
            out["translations"] = json.dumps(out["translations"])
        if "answer_options" in out and isinstance(out["answer_options"], (list, dict)):
            out["answer_options"] = json.dumps(out["answer_options"])
        if "media" in out and isinstance(out["media"], (list, dict)):
            out["media"] = json.dumps(out["media"])

        # subject_ids en multipart: ton _coerce_json_fields attend une QueryDict.getlist("subject_ids")
        # MAIS dans les tests DRF, tu peux passer une liste, DRF va répéter la clé.
        return out

    def _img(self, name="x.png", content=b"fake", content_type="image/png"):
        return SimpleUploadedFile(name, content, content_type=content_type)

    # -------------------------
    # setup
    # -------------------------
    def setUp(self):
        self.staff = self._mk_user(is_staff=True)
        self.user = self._mk_user(is_staff=False)
        self.domain = self._mk_domain(self.staff, allowed_codes=("fr", "nl"))

    # =========================================================
    # Permissions
    # =========================================================
    def test_permissions_list_forbidden_for_anonymous(self):
        resp = self.client.get(self._list_url())
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_permissions_list_forbidden_for_non_staff(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(self._list_url())
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_permissions_list_ok_for_staff(self):
        self.client.force_authenticate(self.staff)
        resp = self.client.get(self._list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # =========================================================
    # LIST + search
    # =========================================================
    def test_list_returns_questions(self):
        self._mk_question(self.domain, title_fr="Alpha", title_nl="Alpha NL")
        self._mk_question(self.domain, title_fr="Beta", title_nl="Beta NL")

        self.client.force_authenticate(self.staff)
        resp = self.client.get(self._list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()
        # paginé ou non
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertGreaterEqual(len(items), 2)

    def test_list_search_filters_by_title_translation_icontains(self):
        self._mk_question(self.domain, title_fr="UniqueFoo", title_nl="Iets")
        self._mk_question(self.domain, title_fr="Bar", title_nl="Andere")

        self.client.force_authenticate(self.staff)
        resp = self.client.get(self._list_url(), {"search": "foo"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertEqual(len(items), 1)
        # QuestionReadSerializer renvoie "title" (getter any_language=True)
        self.assertIn(items[0]["title"].lower(), {"uniquefoo", "iets"})  # selon langue active / fallback

    # =========================================================
    # RETRIEVE : is_correct masqué
    # =========================================================
    def test_retrieve_hides_is_correct_in_answer_options(self):
        q = self._mk_question(self.domain, title_fr="Q", title_nl="Q NL", with_options=True)
        self.client.force_authenticate(self.staff)

        resp = self.client.get(self._detail_url(q))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()
        self.assertIn("answer_options", data)
        self.assertGreaterEqual(len(data["answer_options"]), 2)
        # par défaut, show_correct=False => is_correct doit être absent
        self.assertNotIn("is_correct", data["answer_options"][0])

    # =========================================================
    # CREATE : JSON
    # =========================================================
    def test_create_json_creates_question_and_options_and_subjects(self):
        s = self._mk_subject(name_fr="History", slug_fr="history")

        payload = self._payload_create(self.domain, subject_ids=[s.pk], title_fr="Create FR", title_nl="Create NL")

        self.client.force_authenticate(self.staff)
        resp = self.client.post(self._list_url(), data=payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        qid = resp.json()["id"]
        q = Question.objects.get(pk=qid)

        self.assertEqual(q.domain_id, self.domain.pk)
        self.assertEqual(q.subjects.count(), 1)
        self.assertEqual(q.answer_options.count(), 2)

        # en réponse create => show_correct=True => is_correct présent
        data = resp.json()
        self.assertIn("answer_options", data)
        self.assertIn("is_correct", data["answer_options"][0])

    # =========================================================
    # CREATE : multipart (coerce + media)
    # =========================================================
    def test_create_multipart_parses_json_strings_and_uploads_media(self):
        s1 = self._mk_subject(name_fr="S1", slug_fr="s1")
        s2 = self._mk_subject(name_fr="S2", slug_fr="s2")

        translations = json.dumps(
            {
                "fr": {"title": "MP FR", "description": "DFR", "explanation": "EFR"},
                "nl": {"title": "MP NL", "description": "DNL", "explanation": "ENL"},
            }
        )
        answer_options = json.dumps(
            [
                {"is_correct": True, "sort_order": 1, "translations": {"fr": {"content": "A"}, "nl": {"content": "A"}}},
                {"is_correct": False, "sort_order": 2, "translations": {"fr": {"content": "B"}, "nl": {"content": "B"}}},
            ]
        )
        media = json.dumps([{"kind": "external", "external_url": "https://example.com", "sort_order": 10}])

        img = SimpleUploadedFile("x.png", b"fakepng", content_type="image/png")

        self.client.force_authenticate(self.staff)
        resp = self.client.post(
            self._list_url(),
            data={
                "domain": str(self.domain.pk),
                "translations": translations,
                "subject_ids": [str(s1.pk), str(s2.pk)],  # QueryDict.getlist OK
                "answer_options": answer_options,
                "media": media,
                "media_files": [img],  # DRF construit FILES
            },
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        qid = resp.json()["id"]
        q = Question.objects.get(pk=qid)

        self.assertEqual(q.subjects.count(), 2)
        self.assertEqual(q.answer_options.count(), 2)

        medias = list(q.media.order_by("sort_order", "id"))
        self.assertEqual(len(medias), 2)  # 1 image + 1 external
        self.assertTrue(any(m.kind == QuestionMedia.IMAGE for m in medias))
        self.assertTrue(any(m.kind == QuestionMedia.EXTERNAL for m in medias))

    # =========================================================
    # UPDATE (PUT) : remplace media (delete + recreate)
    # =========================================================
    def test_update_put_replaces_media(self):
        """
        Ce test correspond EXACTEMENT à ton problème :
        - PUT en multipart
        - translations/answer_options/media doivent être JSON string
        - et on vérifie que le PUT remplace les médias (delete + recreate)
        """
        staff = self._mk_user(is_staff=True)
        self.client.force_authenticate(staff)

        domain = self._mk_domain(owner=staff)

        # 1) créer une question existante avec 1 media image + 1 external
        q = self._mk_question(domain=domain)
        self._mk_option(q, is_correct=True, sort_order=1, fr="A", nl="A")
        self._mk_option(q, is_correct=False, sort_order=2, fr="B", nl="B")

        QuestionMedia.objects.create(question=q, kind=QuestionMedia.EXTERNAL, external_url="https://old", sort_order=1)
        QuestionMedia.objects.create(question=q, kind=QuestionMedia.IMAGE, file=self._img("old.png"), sort_order=2)
        self.assertEqual(q.media.count(), 2)

        # 2) PUT avec payload complet + nouveaux médias (1 nouvelle image + 1 new external)

        payload = self._payload_create_media(self.domain)

        mp = self._payload_to_multipart(payload)

        img = self._img("new.png")
        resp = self.client.put(
            self._detail_url(q),
            data={**mp, "media_files": [img]},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        q.refresh_from_db()

        # 3) media remplacés : on doit retrouver 1 image (new.png) + 1 external (https://example.com/1)
        self.assertEqual(q.media.count(), 2)
        self.assertEqual(q.media.filter(kind=QuestionMedia.IMAGE).count(), 1)
        self.assertEqual(q.media.filter(kind=QuestionMedia.EXTERNAL).count(), 1)

        ext = q.media.get(kind=QuestionMedia.EXTERNAL)
        self.assertEqual(ext.external_url, "https://example.com/1")

        img_media = q.media.get(kind=QuestionMedia.IMAGE)
        # selon storage, file.name peut contenir un chemin
        self.assertIn("new.png", img_media.file.name)

    # =========================================================
    # PATCH : ne touche pas media si absent
    # =========================================================
    def test_patch_without_media_does_not_replace_media(self):
        q = self._mk_question(self.domain, title_fr="Q", title_nl="Q NL", with_options=True)
        QuestionMedia.objects.create(question=q, kind=QuestionMedia.EXTERNAL, external_url="https://keep", sort_order=1)

        self.client.force_authenticate(self.staff)
        resp = self.client.patch(self._detail_url(q), data={"active": False}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        q.refresh_from_db()
        self.assertFalse(q.active)
        self.assertTrue(QuestionMedia.objects.filter(question=q, external_url="https://keep").exists())
        self.assertEqual(q.media.count(), 1)

    # =========================================================
    # PATCH : remplace media si présent
    # =========================================================
    def test_patch_with_media_replaces_media(self):
        q = self._mk_question(self.domain, title_fr="Q", title_nl="Q NL", with_options=True)
        QuestionMedia.objects.create(question=q, kind=QuestionMedia.EXTERNAL, external_url="https://old", sort_order=1)

        self.client.force_authenticate(self.staff)
        resp = self.client.patch(
            self._detail_url(q),
            data={"media": json.dumps([{"kind": "external", "external_url": "https://new", "sort_order": 1}])},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        q.refresh_from_db()
        self.assertFalse(QuestionMedia.objects.filter(question=q, external_url="https://old").exists())
        self.assertTrue(QuestionMedia.objects.filter(question=q, external_url="https://new").exists())
        self.assertEqual(q.media.count(), 1)

    # =========================================================
    # DESTROY
    # =========================================================
    def test_destroy_deletes_question(self):
        q = self._mk_question(self.domain, title_fr="ToDel", title_nl="ToDel NL", with_options=True)

        self.client.force_authenticate(self.staff)
        resp = self.client.delete(self._detail_url(q))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Question.objects.filter(pk=q.pk).exists())
