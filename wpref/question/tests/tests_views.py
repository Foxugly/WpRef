# question/tests/test_views.py
import json
import uuid

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from domain.models import Domain
from language.models import Language
from subject.models import Subject
from question.models import Question, MediaAsset, QuestionMedia

User = get_user_model()


class QuestionViewSetTests(APITestCase):
    # -------------------------
    # URL helpers
    # -------------------------
    def _list_url(self):
        return reverse("api:question-api:question-list")

    def _detail_url(self, q: Question):
        # ViewSet lookup_url_kwarg="question_id"
        return reverse("api:question-api:question-detail", kwargs={"question_id": q.pk})

    def _media_url(self):
        return reverse("api:question-api:question-media")

    # -------------------------
    # builders
    # -------------------------
    def _mk_user(self, *, is_staff: bool) -> User:
        return User.objects.create_user(
            username=f"u_{uuid.uuid4().hex[:8]}",
            password="pass",
            is_staff=is_staff,
        )

    def _mk_language(self, code: str) -> Language:
        obj, _ = Language.objects.get_or_create(code=code)
        return obj

    def _mk_domain(self, owner: User, allowed_codes=("fr", "nl")) -> Domain:
        d = Domain.objects.create(owner=owner, active=True)

        # parler translations
        d.set_current_language("fr")
        d.name = "Domain FR"
        d.description = ""
        d.save()

        langs = [self._mk_language(c) for c in allowed_codes]
        d.allowed_languages.set(langs)
        return d

    def _mk_subject(self, domain: Domain, *, name_fr="Math") -> Subject:
        s = Subject.objects.create(domain=domain, active=True)
        s.set_current_language("fr")
        s.name = name_fr
        s.description = ""
        s.save()
        return s

    def _payload_create(self, domain: Domain, *, subject_ids=None, media_asset_ids=None):
        subject_ids = subject_ids or []
        media_asset_ids = media_asset_ids or []

        return {
            "domain": domain.pk,
            "translations": {
                "fr": {"title": "Titre FR", "description": "Desc FR", "explanation": "Expl FR"},
                "nl": {"title": "Titel NL", "description": "Desc NL", "explanation": "Expl NL"},
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
            "media_asset_ids": media_asset_ids,
        }

    def _payload_to_multipart(self, payload: dict) -> dict:
        out = dict(payload)

        # stringify nested JSON
        if isinstance(out.get("translations"), dict):
            out["translations"] = json.dumps(out["translations"])
        if isinstance(out.get("answer_options"), list):
            out["answer_options"] = json.dumps(out["answer_options"])

        # subject_ids / media_asset_ids: on veut un QueryDict.getlist() côté viewset
        # DRF le fait si on passe une liste.
        out["domain"] = str(out["domain"])
        out["subject_ids"] = [str(x) for x in out.get("subject_ids", [])]
        out["media_asset_ids"] = [str(x) for x in out.get("media_asset_ids", [])]

        return out

    def _upload_external(self, url: str) -> MediaAsset:
        self.client.force_authenticate(self.staff)
        resp = self.client.post(self._media_url(), data={"external_url": url}, format="json")
        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK), resp.json())
        return MediaAsset.objects.get(pk=resp.json()["id"])

    def _upload_image(self, name="x.png", content=b"fakepng") -> MediaAsset:
        self.client.force_authenticate(self.staff)
        f = SimpleUploadedFile(name, content, content_type="image/png")
        resp = self.client.post(self._media_url(), data={"file": f}, format="multipart")
        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK), getattr(resp, "data", None))
        return MediaAsset.objects.get(pk=resp.json()["id"])

    # -------------------------
    # setup
    # -------------------------
    def setUp(self):
        self.staff = self._mk_user(is_staff=True)
        self.user = self._mk_user(is_staff=False)
        self.domain_owner = self._mk_user(is_staff=False)
        self.domain_staff = self._mk_user(is_staff=False)
        self.domain_member = self._mk_user(is_staff=False)
        self.outsider = self._mk_user(is_staff=False)
        self.domain = self._mk_domain(self.staff, allowed_codes=("fr", "nl"))
        self.other_domain = self._mk_domain(self.staff, allowed_codes=("fr", "nl"))
        self.domain.owner = self.domain_owner
        self.domain.save(update_fields=["owner"])
        self.domain.staff.add(self.domain_staff)
        self.domain.members.add(self.domain_member)
        self.domain_owner.current_domain = self.domain
        self.domain_owner.save(update_fields=["current_domain"])
        self.domain_staff.current_domain = self.domain
        self.domain_staff.save(update_fields=["current_domain"])
        self.domain_member.current_domain = self.domain
        self.domain_member.save(update_fields=["current_domain"])

    # =========================================================
    # Permissions
    # =========================================================
    def test_permissions_list_forbidden_for_anonymous(self):
        resp = self.client.get(self._list_url())
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_permissions_list_returns_empty_for_user_without_visible_domain(self):
        self.client.force_authenticate(self.outsider)
        resp = self.client.get(self._list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertEqual(items, [])

    def test_permissions_list_ok_for_domain_owner(self):
        self.client.force_authenticate(self.domain_owner)
        resp = self.client.get(self._list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_permissions_list_ok_for_domain_staff(self):
        self.client.force_authenticate(self.domain_staff)
        resp = self.client.get(self._list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_permissions_list_ok_for_linked_domain_member(self):
        self.client.force_authenticate(self.domain_member)
        resp = self.client.get(self._list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_permissions_list_returns_empty_for_staff_without_linked_domain(self):
        self.client.force_authenticate(self.staff)
        resp = self.client.get(self._list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertEqual(items, [])

    def test_staff_without_linked_domain_does_not_see_other_domain_questions(self):
        foreign_owner = self._mk_user(is_staff=False)
        self.other_domain.owner = foreign_owner
        self.other_domain.save(update_fields=["owner"])

        visible = Question.objects.create(domain=self.domain, active=True, is_mode_practice=True, is_mode_exam=True)
        visible.set_current_language("fr")
        visible.title = "Domain A"
        visible.save()

        other = Question.objects.create(domain=self.other_domain, active=True, is_mode_practice=True, is_mode_exam=True)
        other.set_current_language("fr")
        other.title = "Domain B"
        other.save()

        self.client.force_authenticate(self.staff)
        resp = self.client.get(self._list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        returned_ids = {item["id"] for item in items}
        self.assertNotIn(visible.id, returned_ids)
        self.assertNotIn(other.id, returned_ids)

    def test_list_only_returns_questions_from_visible_domains(self):
        visible = Question.objects.create(domain=self.domain, active=True, is_mode_practice=True, is_mode_exam=True)
        visible.set_current_language("fr")
        visible.title = "Visible"
        visible.save()

        foreign_owner = self._mk_user(is_staff=False)
        foreign_domain = self._mk_domain(foreign_owner, allowed_codes=("fr", "nl"))
        hidden = Question.objects.create(domain=foreign_domain, active=True, is_mode_practice=True, is_mode_exam=True)
        hidden.set_current_language("fr")
        hidden.title = "Hidden"
        hidden.save()

        self.client.force_authenticate(self.domain_staff)
        resp = self.client.get(self._list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        returned_ids = {item["id"] for item in items}
        self.assertIn(visible.id, returned_ids)
        self.assertNotIn(hidden.id, returned_ids)

    def test_stale_current_domain_does_not_grant_question_access(self):
        visible = Question.objects.create(domain=self.domain, active=True, is_mode_practice=True, is_mode_exam=True)
        visible.set_current_language("fr")
        visible.title = "Visible"
        visible.save()

        self.outsider.current_domain = self.domain
        self.outsider.save(update_fields=["current_domain"])
        self.domain.owner = self.domain_owner
        self.domain.save(update_fields=["owner"])

        self.client.force_authenticate(self.outsider)
        resp = self.client.get(self._list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertEqual(items, [])

    # =========================================================
    # Media endpoint
    # =========================================================
    def test_media_external_creates_or_returns_existing(self):
        self.client.force_authenticate(self.staff)

        resp1 = self.client.post(self._media_url(), data={"external_url": "https://example.com/ok"}, format="json")
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        resp2 = self.client.post(self._media_url(), data={"external_url": "https://example.com/ok"}, format="json")
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)

        self.assertEqual(resp1.json()["id"], resp2.json()["id"])

    def test_media_external_youtube_url_is_normalized(self):
        self.client.force_authenticate(self.staff)

        resp = self.client.post(
            self._media_url(),
            data={"external_url": "https://youtu.be/dQw4w9WgXcQ?t=43"},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.json())
        self.assertEqual(
            resp.json()["external_url"],
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )

    def test_media_external_invalid_youtube_url_is_rejected(self):
        self.client.force_authenticate(self.staff)

        resp = self.client.post(
            self._media_url(),
            data={"external_url": "https://www.youtube.com/watch?feature=share"},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("external_url", resp.json())

    def test_media_file_dedup_by_sha256_returns_200_on_second_upload(self):
        self.client.force_authenticate(self.staff)

        f1 = SimpleUploadedFile("a.png", b"same-content", content_type="image/png")
        r1 = self.client.post(self._media_url(), data={"file": f1}, format="multipart")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)

        f2 = SimpleUploadedFile("b.png", b"same-content", content_type="image/png")
        r2 = self.client.post(self._media_url(), data={"file": f2}, format="multipart")
        self.assertEqual(r2.status_code, status.HTTP_200_OK)

        self.assertEqual(r1.json()["id"], r2.json()["id"])

    def test_media_file_rejects_unsupported_content_type(self):
        self.client.force_authenticate(self.staff)
        f = SimpleUploadedFile("x.txt", b"abc", content_type="text/plain")
        r = self.client.post(self._media_url(), data={"file": f}, format="multipart")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    # =========================================================
    # LIST + search
    # =========================================================
    def test_list_search_filters_by_title_translation_icontains(self):
        q1 = Question.objects.create(domain=self.domain, active=True, is_mode_practice=True, is_mode_exam=True)
        q1.set_current_language("fr")
        q1.title = "UniqueFoo"
        q1.save()

        q2 = Question.objects.create(domain=self.domain, active=True, is_mode_practice=True, is_mode_exam=True)
        q2.set_current_language("fr")
        q2.title = "Bar"
        q2.save()

        self.client.force_authenticate(self.domain_owner)
        resp = self.client.get(self._list_url(), {"search": "foo"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()
        items = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertEqual(len(items), 1)

        self.assertIn("translations", items[0])
        self.assertIn("fr", items[0]["translations"])
        self.assertEqual(items[0]["translations"]["fr"]["title"], "UniqueFoo")

    # =========================================================
    # CREATE (JSON)
    # =========================================================
    def test_create_json_full_with_subjects_options_and_media_assets(self):
        s1 = self._mk_subject(self.domain, name_fr="S1")
        s2 = self._mk_subject(self.domain, name_fr="S2")

        a_ext = self._upload_external("https://example.com/v1")
        a_img = self._upload_image("img.png", b"img-content")

        payload = self._payload_create(
            self.domain,
            subject_ids=[s1.pk, s2.pk],
            media_asset_ids=[a_ext.pk, a_img.pk, a_ext.pk],  # duplicate -> dedup in serializer helper
        )

        self.client.force_authenticate(self.domain_owner)
        resp = self.client.post(self._list_url(), data=payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.json())

        qid = resp.json()["id"]
        q = (
            Question.objects
            .prefetch_related("subjects", "answer_options", "media__asset", "translations")
            .get(pk=qid)
        )

        self.assertEqual(q.subjects.count(), 2)
        self.assertEqual(q.answer_options.count(), 2)

        linked_asset_ids = list(q.media.order_by("sort_order").values_list("asset_id", flat=True))
        self.assertEqual(linked_asset_ids, [a_ext.pk, a_img.pk])  # dedup + order kept

        # show_correct=True for staff => is_correct present
        self.assertIn("answer_options", resp.json())
        self.assertIn("is_correct", resp.json()["answer_options"][0])
        self.assertEqual(
            resp.json()["answer_options"][0]["translations"]["fr"]["content"],
            "A",
        )

    def test_create_rejects_subject_from_other_domain(self):
        valid_subject = self._mk_subject(self.domain, name_fr="S1")
        foreign_subject = self._mk_subject(self.other_domain, name_fr="Foreign S")

        payload = self._payload_create(
            self.domain,
            subject_ids=[valid_subject.pk, foreign_subject.pk],
        )

        self.client.force_authenticate(self.domain_owner)
        resp = self.client.post(self._list_url(), data=payload, format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("subject_ids", resp.json())

    def test_create_rejects_domain_not_manageable_by_user(self):
        payload = self._payload_create(self.other_domain)

        self.client.force_authenticate(self.domain_owner)
        resp = self.client.post(self._list_url(), data=payload, format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("domain", resp.json())

    # =========================================================
    # CREATE (multipart) - ensures _coerce_json_fields works
    # =========================================================
    def test_create_multipart_coerces_ids_and_json_strings(self):
        s1 = self._mk_subject(self.domain, name_fr="S1")
        s2 = self._mk_subject(self.domain, name_fr="S2")

        a1 = self._upload_external("https://example.com/a1")
        a2 = self._upload_external("https://example.com/a2")

        payload = self._payload_create(
            self.domain,
            subject_ids=[s1.pk, s2.pk],
            media_asset_ids=[a1.pk, a2.pk],
        )
        mp = self._payload_to_multipart(payload)

        self.client.force_authenticate(self.domain_owner)
        resp = self.client.post(self._list_url(), data=mp, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.json())

        q = Question.objects.get(pk=resp.json()["id"])
        self.assertEqual(q.subjects.count(), 2)
        self.assertEqual(q.media.count(), 2)

    # =========================================================
    # UPDATE (PUT) - replace media when media_asset_ids provided
    # =========================================================
    def test_update_put_replaces_media_when_media_asset_ids_present(self):
        # initial question
        q = Question.objects.create(domain=self.domain, active=True, is_mode_practice=True, is_mode_exam=True)
        q.set_current_language("fr")
        q.title = "Old"
        q.save()

        # attach old media
        old_ext = self._upload_external("https://example.com/old")
        QuestionMedia.objects.create(question=q, asset=old_ext, sort_order=0)
        self.assertEqual(q.media.count(), 1)

        # new media
        new_ext = self._upload_external("https://example.com/new")
        new_img = self._upload_image("new.png", b"zzz")

        payload = self._payload_create(self.domain, media_asset_ids=[new_ext.pk, new_img.pk])
        self.client.force_authenticate(self.domain_owner)
        resp = self.client.put(self._detail_url(q), data=payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.json())

        q.refresh_from_db()
        new_ids = list(q.media.order_by("sort_order").values_list("asset_id", flat=True))
        self.assertEqual(new_ids, [new_ext.pk, new_img.pk])
        self.assertFalse(q.media.filter(asset_id=old_ext.pk).exists())

    # =========================================================
    # PATCH - does not touch media if media_asset_ids absent
    # =========================================================
    def test_patch_without_media_asset_ids_does_not_replace_media(self):
        q = Question.objects.create(domain=self.domain, active=True, is_mode_practice=True, is_mode_exam=True)
        q.set_current_language("fr")
        q.title = "Keep"
        q.save()

        old_ext = self._upload_external("https://example.com/keep")
        QuestionMedia.objects.create(question=q, asset=old_ext, sort_order=0)

        self.client.force_authenticate(self.domain_owner)
        resp = self.client.patch(self._detail_url(q), data={"active": False}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.json())

        q.refresh_from_db()
        self.assertFalse(q.active)
        self.assertTrue(q.media.filter(asset_id=old_ext.pk).exists())
        self.assertEqual(q.media.count(), 1)

    # =========================================================
    # PATCH - replaces media if media_asset_ids present
    # =========================================================
    def test_patch_with_media_asset_ids_replaces_media(self):
        q = Question.objects.create(domain=self.domain, active=True, is_mode_practice=True, is_mode_exam=True)
        q.set_current_language("fr")
        q.title = "Old"
        q.save()

        old_ext = self._upload_external("https://example.com/old")
        QuestionMedia.objects.create(question=q, asset=old_ext, sort_order=0)

        new_ext = self._upload_external("https://example.com/new")

        self.client.force_authenticate(self.domain_owner)
        resp = self.client.patch(
            self._detail_url(q),
            data={"media_asset_ids": [new_ext.pk]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.json())

        q.refresh_from_db()
        ids = list(q.media.values_list("asset_id", flat=True))
        self.assertEqual(ids, [new_ext.pk])
        self.assertFalse(q.media.filter(asset_id=old_ext.pk).exists())

    def test_patch_rejects_domain_change_when_existing_subjects_belong_to_other_domain(self):
        q = Question.objects.create(domain=self.domain, active=True, is_mode_practice=True, is_mode_exam=True)
        q.set_current_language("fr")
        q.title = "Keep domain consistency"
        q.save()

        subject = self._mk_subject(self.domain, name_fr="Current S")
        q.subjects.set([subject])

        self.domain.staff.add(self.staff)
        self.staff.current_domain = self.domain
        self.staff.save(update_fields=["current_domain"])

        self.client.force_authenticate(self.staff)
        resp = self.client.patch(
            self._detail_url(q),
            data={"domain": self.other_domain.pk},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("subject_ids", resp.json())

    # =========================================================
    # DESTROY
    # =========================================================
    def test_destroy_deletes_question(self):
        q = Question.objects.create(domain=self.domain, active=True, is_mode_practice=True, is_mode_exam=True)
        q.set_current_language("fr")
        q.title = "ToDel"
        q.save()

        self.client.force_authenticate(self.domain_owner)
        resp = self.client.delete(self._detail_url(q))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_retrieve_hidden_for_user_outside_domain(self):
        q = Question.objects.create(domain=self.domain, active=True, is_mode_practice=True, is_mode_exam=True)
        q.set_current_language("fr")
        q.title = "Hidden"
        q.save()

        self.client.force_authenticate(self.outsider)
        resp = self.client.get(self._detail_url(q))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(Question.objects.filter(pk=q.pk).exists())
