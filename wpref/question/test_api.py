# question/tests/test_question_api.py

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from subject.models import Subject
from .models import Question, AnswerOption, QuestionMedia, QuestionSubject


class QuestionAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()

        # Utilisateur simple (non staff)
        cls.user = user_model.objects.create_user(
            username="user",
            email="user@example.com",
            password="password123",
        )

        # Utilisateur admin/staff
        cls.admin = user_model.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="password123",
            is_staff=True,
        )

        # Deux sujets pour tester subject_ids / filters
        cls.subject1 = Subject.objects.create(name="Math", description="Sujet math")
        cls.subject2 = Subject.objects.create(name="Scrum", description="Sujet scrum")

    def setUp(self):
        # Par défaut, on se connecte comme admin (pour les tests "happy path")
        self.client.force_authenticate(user=self.admin)
        # Adapter si ton namespace interne est différent
        self.list_url = reverse("api:question:question-list")

    # -------------------------------------------------------------------------
    # PERMISSIONS
    # -------------------------------------------------------------------------

    def test_unauthenticated_user_cannot_access_questions(self):
        """
        Non authentifié : aucune action (liste et détail refusés).
        """
        self.client.force_authenticate(user=None)

        # Liste
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Détail
        q = Question.objects.create(title="Q1", description="", explanation="")
        detail_url = reverse("api:question:question-detail", args=[q.pk])
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_simple_user_cannot_access_questions(self):
        """
        Utilisateur authentifié non staff : refus (403) sur toutes les actions.
        """
        self.client.force_authenticate(user=self.user)

        q = Question.objects.create(title="Q1", description="", explanation="")
        detail_url = reverse("api:question:question-detail", args=[q.pk])

        # Liste
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Détail
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Création
        payload = {
            "title": "New Q",
            "description": "",
            "explanation": "",
            "allow_multiple_correct": False,
            "answer_options": [
                {"content": "A", "is_correct": True, "sort_order": 1},
                {"content": "B", "is_correct": False, "sort_order": 2},
            ],
            "subject_ids": [self.subject1.id],
        }
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Update
        resp = self.client.put(detail_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Delete
        resp = self.client.delete(detail_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # -------------------------------------------------------------------------
    # CRÉATION / VALIDATIONS BUSINESS
    # -------------------------------------------------------------------------

    def test_admin_can_create_valid_question(self):
        """
        Admin : peut créer une question avec réponses + sujets par ID.
        """
        payload = {
            "title": "Quelle est la capitale de la France ?",
            "description": "QCM simple",
            "explanation": "La capitale est Paris.",
            "allow_multiple_correct": False,
            "subject_ids": [self.subject1.id, self.subject2.id],
            "answer_options": [
                {"content": "Paris", "is_correct": True, "sort_order": 1},
                {"content": "Lyon", "is_correct": False, "sort_order": 2},
            ],
            "media": [
                {
                    "kind": "image",
                    "external_url": "https://example.com/image.png",
                    "caption": "Carte de France",
                    "sort_order": 0,
                }
            ],
        }

        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Question.objects.count(), 1)
        q = Question.objects.first()
        self.assertEqual(q.title, payload["title"])
        self.assertEqual(q.answer_options.count(), 2)
        self.assertEqual(q.media.count(), 1)
        # sujets via QuestionSubject
        self.assertEqual(q.subjects.count(), 2)
        self.assertEqual(QuestionSubject.objects.filter(question=q).count(), 2)

    def test_question_must_have_at_least_two_answer_options(self):
        """
        Règle métier : au moins 2 réponses possibles.
        """
        payload = {
            "title": "Q invalide",
            "description": "",
            "explanation": "",
            "allow_multiple_correct": False,
            "subject_ids": [self.subject1.id],
            "answer_options": [
                {"content": "Seulement une", "is_correct": True, "sort_order": 1},
            ],
        }

        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        # Erreur non-field (validation clean)
        self.assertIn("Une question doit avoir au moins 2 réponses possibles.", str(resp.data))

    def test_question_must_have_at_least_one_correct_answer(self):
        """
        Règle métier : au moins une réponse correcte.
        """
        payload = {
            "title": "Q sans bonne réponse",
            "description": "",
            "explanation": "",
            "allow_multiple_correct": False,
            "subject_ids": [self.subject1.id],
            "answer_options": [
                {"content": "A", "is_correct": False, "sort_order": 1},
                {"content": "B", "is_correct": False, "sort_order": 2},
            ],
        }

        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Indique au moins une réponse correcte.", str(resp.data))

    def test_single_correct_answer_when_allow_multiple_correct_is_false(self):
        """
        Règle métier : si allow_multiple_correct = False -> exactement 1 bonne réponse.
        """
        payload = {
            "title": "Q plusieurs bonnes réponses interdites",
            "description": "",
            "explanation": "",
            "allow_multiple_correct": False,
            "subject_ids": [self.subject1.id],
            "answer_options": [
                {"content": "A", "is_correct": True, "sort_order": 1},
                {"content": "B", "is_correct": True, "sort_order": 2},
            ],
        }

        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Cette question n'autorise qu'une seule bonne réponse.",
            str(resp.data),
        )

    def test_multiple_correct_answers_allowed_when_flag_true(self):
        """
        Si allow_multiple_correct = True, plusieurs bonnes réponses sont acceptées.
        """
        payload = {
            "title": "Q plusieurs bonnes réponses autorisées",
            "description": "",
            "explanation": "",
            "allow_multiple_correct": True,
            "subject_ids": [self.subject1.id],
            "answer_options": [
                {"content": "A", "is_correct": True, "sort_order": 1},
                {"content": "B", "is_correct": True, "sort_order": 2},
            ],
        }

        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Question.objects.count(), 1)

    # -------------------------------------------------------------------------
    # UPDATE / MEDIA / SUBJECTS
    # -------------------------------------------------------------------------

    def _create_valid_question(self):
        q = Question.objects.create(
            title="Q base",
            description="",
            explanation="",
            allow_multiple_correct=False,
        )
        AnswerOption.objects.create(
            question=q, content="A", is_correct=True, sort_order=1
        )
        AnswerOption.objects.create(
            question=q, content="B", is_correct=False, sort_order=2
        )
        QuestionSubject.objects.create(
            question=q, subject=self.subject1, sort_order=0
        )
        return q

    def test_admin_can_update_question_with_new_options_and_subjects(self):
        """
        PUT : remplace les réponses, les médias, et réassigne les sujets.
        """
        q = self._create_valid_question()
        detail_url = reverse("api:question:question-detail", args=[q.pk])

        payload = {
            "title": "Q modifiée",
            "description": "desc modifiée",
            "explanation": "explication modifiée",
            "allow_multiple_correct": True,
            "subject_ids": [self.subject2.id],
            "answer_options": [
                {"content": "X", "is_correct": True, "sort_order": 1},
                {"content": "Y", "is_correct": True, "sort_order": 2},
                {"content": "Z", "is_correct": False, "sort_order": 3},
            ],
            "media": [
                {
                    "kind": "video",
                    "external_url": "https://example.com/video.mp4",
                    "caption": "Vidéo explicative",
                    "sort_order": 0,
                }
            ],
        }

        resp = self.client.put(detail_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        q.refresh_from_db()
        self.assertEqual(q.title, "Q modifiée")
        self.assertEqual(q.answer_options.count(), 3)
        self.assertEqual(q.media.count(), 1)

        # sujets mis à jour
        self.assertEqual(q.subjects.count(), 1)
        self.assertEqual(q.subjects.first(), self.subject2)

    # -------------------------------------------------------------------------
    # LIST / FILTERS
    # -------------------------------------------------------------------------

    def test_list_questions_as_admin(self):
        q1 = self._create_valid_question()
        q2 = self._create_valid_question()

        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)

    def test_filter_by_subject_id(self):
        q1 = self._create_valid_question()
        # q1 lié à subject1
        q2 = Question.objects.create(
            title="Q autre",
            description="",
            explanation="",
            allow_multiple_correct=False,
        )
        AnswerOption.objects.create(
            question=q2, content="A", is_correct=True, sort_order=1
        )
        AnswerOption.objects.create(
            question=q2, content="B", is_correct=False, sort_order=2
        )
        QuestionSubject.objects.create(
            question=q2, subject=self.subject2, sort_order=0
        )

        # ?subjects=<id>
        resp = self.client.get(self.list_url, {"subjects": self.subject1.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["id"], q1.id)

    def test_filter_by_allow_multiple_correct(self):
        q1 = self._create_valid_question()  # allow_multiple_correct=False
        q2 = Question.objects.create(
            title="Q multi",
            description="",
            explanation="",
            allow_multiple_correct=True,
        )
        AnswerOption.objects.create(
            question=q2, content="A", is_correct=True, sort_order=1
        )
        AnswerOption.objects.create(
            question=q2, content="B", is_correct=True, sort_order=2
        )

        resp = self.client.get(self.list_url, {"allow_multiple_correct": True})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["id"], q2.id)
