# question/tests/test_api.py
import json

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from question.models import Question, AnswerOption, QuestionMedia
from rest_framework import status
from rest_framework.test import APITestCase
from subject.models import Subject

User = get_user_model()


class QuestionAPITestCase(APITestCase):
    """
    Tests API pour QuestionViewSet (admin only):
      - GET /api/question/ (list + search)
      - GET /api/question/{id}/ (retrieve)
      - POST /api/question/ (create JSON / multipart)
      - PUT/PATCH /api/question/{id}/ (update)
      - DELETE /api/question/{id}/ (delete)
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="adminpass", is_staff=True, is_superuser=True
        )
        self.u1 = User.objects.create_user(username="u1", password="u1pass")

        self.s1 = Subject.objects.create(name="Math", slug="math")
        self.s2 = Subject.objects.create(name="History", slug="history")

        # urls
        self.question_list_url = reverse("api:question-api:question-list")
        # detail url via reverse(..., kwargs={"pk": id}) dans les tests

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def _create_question_in_db(self, title="Q1") -> Question:
        q = Question.objects.create(
            title=title,
            description="desc",
            explanation="expl",
            allow_multiple_correct=False,
            active=True,
            is_mode_practice=True,
            is_mode_exam=True,
        )
        q.subjects.add(self.s1)
        AnswerOption.objects.create(question=q, content="A", is_correct=True, sort_order=1)
        AnswerOption.objects.create(question=q, content="B", is_correct=False, sort_order=2)
        return q

    # ------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------
    def test_list_forbidden_for_non_admin(self):
        self._auth(self.u1)
        res = self.client.get(self.question_list_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_forbidden_for_non_admin(self):
        self._auth(self.u1)
        payload = {"title": "Nope"}
        res = self.client.post(self.question_list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list(self):
        self._auth(self.admin)
        self._create_question_in_db("Q1")
        self._create_question_in_db("Q2")
        res = self.client.get(self.question_list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------
    # List + search
    # ------------------------------------------------------------
    def test_list_search_filters_title_icontains(self):
        self._auth(self.admin)
        self._create_question_in_db("Capitaine Haddock")
        self._create_question_in_db("Tintin")

        res = self.client.get(self.question_list_url + "?search=hadd")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.data
        titles = [item["title"] for item in data]
        self.assertIn("Capitaine Haddock", titles)
        self.assertNotIn("Tintin", titles)

    # ------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------
    def test_retrieve_admin_ok(self):
        self._auth(self.admin)
        q = self._create_question_in_db("Q-Retrieve")

        url = reverse("api:question-api:question-detail", kwargs={"question_id": q.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], q.id)
        self.assertEqual(res.data["title"], "Q-Retrieve")

    # ------------------------------------------------------------
    # Create JSON
    # ------------------------------------------------------------
    def test_create_json_creates_subjects_and_answer_options(self):
        self._auth(self.admin)

        payload = {
            "title": "Q-JSON",
            "description": "desc",
            "explanation": "expl",
            "allow_multiple_correct": False,
            "active": True,
            "is_mode_practice": True,
            "is_mode_exam": True,
            "subject_ids": [self.s1.id, self.s2.id],
            "answer_options": [
                {"content": "A", "is_correct": True, "sort_order": 1},
                {"content": "B", "is_correct": False, "sort_order": 2},
            ],
        }
        res = self.client.post(self.question_list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        qid = res.data["id"]
        q = Question.objects.get(pk=qid)

        self.assertEqual(q.title, "Q-JSON")
        self.assertEqual(set(q.subjects.values_list("id", flat=True)), {self.s1.id, self.s2.id})
        opts = list(q.answer_options.order_by("sort_order").values_list("content", "is_correct", "sort_order"))
        self.assertEqual(opts, [("A", True, 1), ("B", False, 2)])

        # media gérés par la vue : ici aucun => 0
        self.assertEqual(q.media.count(), 0)

    # ------------------------------------------------------------
    # Create multipart (coercion + media upload)
    # ------------------------------------------------------------
    def test_create_multipart_coerces_json_fields_and_uploads_media(self):
        self._auth(self.admin)

        image = SimpleUploadedFile(
            name="img.png",
            content=b"\x89PNG\r\n\x1a\nfakepngcontent",
            content_type="image/png",
        )

        payload = {
            "title": "Q-MP",
            "description": "desc",
            "explanation": "expl",
            "allow_multiple_correct": "false",
            "active": "true",
            "is_mode_practice": "true",
            "is_mode_exam": "true",

            # IMPORTANT: en multipart, DRF transforme une liste en getlist côté QueryDict
            "subject_ids": [str(self.s1.id), str(self.s2.id)],

            # JSON string parsé par _coerce_json_fields()
            "answer_options": json.dumps([
                {"content": "A", "is_correct": True, "sort_order": 1},
                {"content": "B", "is_correct": False, "sort_order": 2},
            ]),

            # media externes (JSON string)
            "media": json.dumps([
                {"kind": "external", "external_url": "https://example.com/video", "sort_order": 5}
            ]),

            # fichier : la vue lit request.FILES peu importe la clé => on respecte la convention
            "media[0][file]": image,
        }

        res = self.client.post(self.question_list_url, payload, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)

        q = Question.objects.get(pk=res.data["id"])

        # subjects bien set
        self.assertEqual(set(q.subjects.values_list("id", flat=True)), {self.s1.id, self.s2.id})

        # options bien créées
        self.assertEqual(q.answer_options.count(), 2)

        # médias: 1 image + 1 external
        self.assertEqual(q.media.count(), 2)
        kinds = list(q.media.order_by("sort_order").values_list("kind", flat=True))
        self.assertIn(QuestionMedia.IMAGE, kinds)
        self.assertIn(QuestionMedia.EXTERNAL, kinds)

    # ------------------------------------------------------------
    # Update / Partial update (wipe+recreate options + reset media)
    # ------------------------------------------------------------
    def test_patch_updates_subjects_and_replaces_answer_options(self):
        self._auth(self.admin)
        q = self._create_question_in_db("Q-PATCH")

        # ajouter un media initial pour vérifier qu'il est supprimé au PATCH
        QuestionMedia.objects.create(
            question=q, kind=QuestionMedia.EXTERNAL, external_url="https://old.example.com", sort_order=1
        )
        self.assertEqual(q.media.count(), 1)
        self.assertEqual(q.answer_options.count(), 2)
        self.assertEqual(set(q.subjects.values_list("id", flat=True)), {self.s1.id})

        url = reverse("api:question-api:question-detail", kwargs={"question_id": q.id})

        patch_payload = {
            "subject_ids": [self.s2.id],  # remplace sujets
            "answer_options": [
                {"content": "X", "is_correct": True, "sort_order": 1},
                {"content": "Y", "is_correct": False, "sort_order": 2},
            ],
            # remplace médias : on envoie 1 external nouveau + aucun fichier => _handle_media_upload delete+recreate
            "media": [
                {"kind": "external", "external_url": "https://new.example.com", "sort_order": 1}
            ],
        }

        res = self.client.patch(url, patch_payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)

        q.refresh_from_db()

        # sujets remplacés
        self.assertEqual(set(q.subjects.values_list("id", flat=True)), {self.s2.id})

        # options remplacées (wipe + recreate)
        opts = list(q.answer_options.order_by("sort_order").values_list("content", "is_correct"))
        self.assertEqual(opts, [("X", True), ("Y", False)])

        # médias reset : ancien supprimé, nouveau présent
        self.assertEqual(q.media.count(), 1)
        self.assertEqual(q.media.first().external_url, "https://new.example.com")

    def test_update_forbidden_for_non_admin(self):
        """
        PUT /api/question/{id}/ doit être interdit si pas admin.
        """
        self._auth(self.u1)
        q = self._create_question_in_db("Q1")

        url = reverse("api:question-api:question-detail", kwargs={"question_id": q.id})
        payload = {
            "title": "Updated",
            "description": "new desc",
            "explanation": "new expl",
            "allow_multiple_correct": False,
            "active": True,
            "is_mode_practice": True,
            "is_mode_exam": True,
            "subject_ids": [self.s2.id],
            "answer_options": [
                {"content": "A1", "is_correct": True, "sort_order": 1},
                {"content": "B1", "is_correct": False, "sort_order": 2},
            ],
        }

        res = self.client.put(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_returns_404_if_not_found(self):
        """
        PUT /api/question/{id}/ -> 404 si question inexistante.
        """
        self._auth(self.admin)
        url = reverse("api:question-api:question-detail", kwargs={"question_id": 999999})

        payload = {
            "title": "Updated",
            "description": "new desc",
            "explanation": "new expl",
            "allow_multiple_correct": False,
            "active": True,
            "is_mode_practice": True,
            "is_mode_exam": True,
            "subject_ids": [self.s1.id],
            "answer_options": [
                {"content": "A1", "is_correct": True, "sort_order": 1},
                {"content": "B1", "is_correct": False, "sort_order": 2},
            ],
        }

        res = self.client.put(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_success_replaces_subjects_and_answer_options(self):
        """
        PUT /api/question/{id}/ :
        - met à jour les champs simples
        - remplace subjects via subject_ids
        - wipe + recreate answer_options
        - retourne 200
        """
        self._auth(self.admin)
        q = self._create_question_in_db("Q1")

        url = reverse("api:question-api:question-detail", kwargs={"question_id": q.id})

        payload = {
            "title": "Q1 updated",
            "description": "desc updated",
            "explanation": "expl updated",
            "allow_multiple_correct": False,
            "active": True,
            "is_mode_practice": True,
            "is_mode_exam": True,
            "subject_ids": [self.s2.id],  # change subjects
            "answer_options": [
                {"content": "New A", "is_correct": True, "sort_order": 1},
                {"content": "New B", "is_correct": False, "sort_order": 2},
            ],
            # media : ici on laisse vide; _handle_media_upload va delete/recreate
            "media": [],
        }

        res = self.client.put(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)

        q.refresh_from_db()

        # champs simples
        self.assertEqual(q.title, "Q1 updated")
        self.assertEqual(q.description, "desc updated")
        self.assertEqual(q.explanation, "expl updated")

        # subjects remplacés
        self.assertEqual(list(q.subjects.values_list("id", flat=True)), [self.s2.id])

        # answer_options remplacées (wipe + recreate)
        opts = list(q.answer_options.order_by("sort_order").values_list("content", "is_correct"))
        self.assertEqual(opts, [("New A", True), ("New B", False)])

        # réponse API cohérente
        self.assertEqual(res.data["id"], q.id)
        self.assertEqual(res.data["title"], "Q1 updated")
        self.assertEqual([s["id"] for s in res.data["subjects"]], [self.s2.id])

    def test_update_400_if_invalid_answer_options(self):
        """
        PUT doit renvoyer 400 si answer_options ne respecte pas Question.clean():
        - au moins 2 options
        - au moins 1 correcte
        - si allow_multiple_correct=False => exactement 1 correcte
        """
        self._auth(self.admin)
        q = self._create_question_in_db("Q1")

        url = reverse("api:question-api:question-detail", kwargs={"question_id": q.id})

        # cas invalide: 1 seule option
        payload = {
            "title": "Q1 updated",
            "description": "desc updated",
            "explanation": "expl updated",
            "allow_multiple_correct": False,
            "active": True,
            "is_mode_practice": True,
            "is_mode_exam": True,
            "subject_ids": [self.s1.id],
            "answer_options": [
                {"content": "Only one", "is_correct": True, "sort_order": 1},
            ],
        }

        res = self.client.put(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST, res.data)

        # Optionnel: vérifier que la DB n’a pas été cassée (question toujours valide)
        q.refresh_from_db()
        self.assertEqual(q.title, "Q1")
        self.assertEqual(q.answer_options.count(), 2)

    # ------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------
    def test_delete_admin_ok(self):
        self._auth(self.admin)
        q = self._create_question_in_db("Q-DEL")

        url = reverse("api:question-api:question-detail", kwargs={"question_id": q.id})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Question.objects.filter(pk=q.id).exists())

        # ------------------------------------------------------------
        # Permissions
        # ------------------------------------------------------------
        def test_update_requires_admin(self):
            self._auth(self.u1)
            payload = {
                "title": "NEW",
                "description": "",
                "explanation": "",
                "allow_multiple_correct": False,
                "active": True,
                "is_mode_practice": True,
                "is_mode_exam": True,
                "subject_ids": [self.s1.id],
                "answer_options": [
                    {"content": "X", "is_correct": True, "sort_order": 1},
                    {"content": "Y", "is_correct": False, "sort_order": 2},
                ],
            }
            res = self.client.put(self.detail_url, payload, format="json")
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # ------------------------------------------------------------
        # PUT JSON : champs + subjects + wipe/recreate options + media reset
        # ------------------------------------------------------------
        def test_update_put_json_replaces_subjects_and_answer_options_and_media(self):
            self._auth(self.admin)

            payload = {
                "title": "Q1 UPDATED",
                "description": "new desc",
                "explanation": "new expl",
                "allow_multiple_correct": False,
                "active": True,
                "is_mode_practice": True,
                "is_mode_exam": True,

                # subjects via serializer
                "subject_ids": [self.s2.id],

                # wipe+recreate dans serializer.update()
                "answer_options": [
                    {"content": "X", "is_correct": True, "sort_order": 1},
                    {"content": "Y", "is_correct": False, "sort_order": 2},
                ],

                # media: ton update appelle _handle_media_upload => delete + recreate
                "media": [
                    {"kind": "external", "external_url": "https://new.example.com", "sort_order": 1},
                ],
            }

            res = self.client.put(self.detail_url, payload, format="json")
            self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)

            self.q.refresh_from_db()

            # champs simples
            self.assertEqual(self.q.title, "Q1 UPDATED")
            self.assertEqual(self.q.description, "new desc")
            self.assertEqual(self.q.explanation, "new expl")

            # subjects remplacés
            self.assertEqual(set(self.q.subjects.values_list("id", flat=True)), {self.s2.id})

            # options remplacées (wipe+recreate)
            opts = list(self.q.answer_options.order_by("sort_order").values_list("content", "is_correct"))
            self.assertEqual(opts, [("X", True), ("Y", False)])

            # media reset: ancien supprimé, nouveau présent
            self.assertEqual(self.q.media.count(), 1)
            m = self.q.media.first()
            self.assertEqual(m.kind, QuestionMedia.EXTERNAL)
            self.assertEqual(m.external_url, "https://new.example.com")

        # ------------------------------------------------------------
        # PUT multipart : coercion + fichiers media
        # ------------------------------------------------------------
        def test_update_put_multipart_coerces_answer_options_and_uploads_file_media(self):
            self._auth(self.admin)

            image = SimpleUploadedFile(
                name="img.png",
                content=b"\x89PNG\r\n\x1a\nfakepngcontent",
                content_type="image/png",
            )

            payload = {
                "title": "Q1 MP",
                "description": "d",
                "explanation": "e",
                "allow_multiple_correct": "false",
                "active": "true",
                "is_mode_practice": "true",
                "is_mode_exam": "true",

                # en multipart: list -> QueryDict.getlist()
                "subject_ids": [str(self.s1.id), str(self.s2.id)],

                # JSON string -> _coerce_json_fields
                "answer_options": json.dumps([
                    {"content": "C", "is_correct": True, "sort_order": 1},
                    {"content": "D", "is_correct": False, "sort_order": 2},
                ]),

                # media externes en JSON string
                "media": json.dumps([
                    {"kind": "external", "external_url": "https://ext.example.com", "sort_order": 10}
                ]),

                # fichier
                "media[0][file]": image,
            }

            res = self.client.put(self.detail_url, payload, format="multipart")
            self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)

            self.q.refresh_from_db()

            # subjects remplacés
            self.assertEqual(set(self.q.subjects.values_list("id", flat=True)), {self.s1.id, self.s2.id})

            # options remplacées
            self.assertEqual(self.q.answer_options.count(), 2)
            opts = list(self.q.answer_options.order_by("sort_order").values_list("content", "is_correct"))
            self.assertEqual(opts, [("C", True), ("D", False)])

            # media: 1 external + 1 image (et l'ancien media supprimé)
            self.assertEqual(self.q.media.count(), 2)
            kinds = set(self.q.media.values_list("kind", flat=True))
            self.assertIn(QuestionMedia.EXTERNAL, kinds)
            self.assertIn(QuestionMedia.IMAGE, kinds)

        # ------------------------------------------------------------
        # Validation error => 400
        # ------------------------------------------------------------
        def test_update_returns_400_on_invalid_payload(self):
            """
            Exemple: payload incomplet en PUT (si ton serializer exige certains champs).
            Ici on force un cas invalide simple: title vide.
            """
            self._auth(self.admin)

            payload = {
                "title": "",  # invalide
                "description": "x",
                "explanation": "x",
                "allow_multiple_correct": False,
                "active": True,
                "is_mode_practice": True,
                "is_mode_exam": True,
                "subject_ids": [self.s1.id],
                "answer_options": [
                    {"content": "A", "is_correct": True, "sort_order": 1},
                    {"content": "B", "is_correct": False, "sort_order": 2},
                ],
            }

            res = self.client.put(self.detail_url, payload, format="json")
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
