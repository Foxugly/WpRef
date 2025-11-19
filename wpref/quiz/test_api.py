# quiz/tests/test_quiz_api.py

from uuid import UUID

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from quiz.models import Quiz, QuizQuestion, QuizSession, QuizAttempt
from question.models import Question, AnswerOption


User = get_user_model()


class QuizAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Utilisateur "normal"
        cls.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="password123",
        )

        # Second utilisateur "normal"
        cls.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="password123",
        )

        # Admin / staff
        cls.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="password123",
            is_staff=True,
        )

        # Un quiz en mode EXAM par défaut
        cls.quiz_exam = Quiz.objects.create(
            title="Quiz Examen",
            description="Mode examen",
            mode=Quiz.MODE_EXAM,
        )

        # Un quiz en mode PRACTICE
        cls.quiz_practice = Quiz.objects.create(
            title="Quiz Practice",
            description="Mode practice",
            mode=Quiz.MODE_PRACTICE,
        )

        # Une question + réponses pour quiz_exam
        cls.question_exam = Question.objects.create(
            title="Capitale de la France ?",
            description="QCM",
            explanation="C'est Paris.",
            allow_multiple_correct=False,
        )
        cls.opt_paris = AnswerOption.objects.create(
            question=cls.question_exam,
            content="Paris",
            is_correct=True,
            sort_order=1,
        )
        cls.opt_lyon = AnswerOption.objects.create(
            question=cls.question_exam,
            content="Lyon",
            is_correct=False,
            sort_order=2,
        )
        QuizQuestion.objects.create(
            quiz=cls.quiz_exam,
            question=cls.question_exam,
            sort_order=1,
            weight=1,
        )

        # Même question pour quiz_practice, histoire d'avoir la même structure
        QuizQuestion.objects.create(
            quiz=cls.quiz_practice,
            question=cls.question_exam,
            sort_order=1,
            weight=1,
        )

    def setUp(self):
        # Par défaut, on bosse avec user1
        self.client.force_authenticate(user=self.user1)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _start_session_for_quiz(self, quiz, as_user):
        """
        Helper : démarre une session de quiz via l'API /start/.
        """
        self.client.force_authenticate(user=as_user)
        url = reverse("api:quiz:quiz-start", kwargs={"slug": quiz.slug})
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        quiz_id_str = resp.data["id"]
        # Vérification que c'est un UUID valide
        UUID(quiz_id_str)  # lève une exception si ce n'est pas un UUID
        return QuizSession.objects.get(id=quiz_id_str)

    def _question_detail_url(self, session, order=1):
        return self._attempt_url(session, order)

    def _attempt_url(self, session, order=1):
        return reverse(
            "api:quiz:quiz-attempt",
            kwargs={"quiz_id": session.id, "question_order": order},
        )

    def _close_url(self, session):
        return reverse(
            "api:quiz:quiz-close",
            kwargs={"quiz_id": session.id},
        )

    def _summary_url(self, session):
        return reverse(
            "api:quiz:quiz-summary",
            kwargs={"quiz_id": session.id},
        )

    # -------------------------------------------------------------------------
    # 1) Seul un utilisateur AUTHENTIFIÉ peut lancer un quiz
    # -------------------------------------------------------------------------

    def test_start_quiz_requires_authentication(self):
        """
        Non authentifié -> 401 sur /quiz/<slug>/start/
        """
        self.client.force_authenticate(user=None)
        url = reverse("api:quiz:quiz-start", kwargs={"slug": self.quiz_exam.slug})
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_start_quiz(self):
        """
        Utilisateur authentifié -> peut démarrer un quiz,
        la session est liée à lui.
        """
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)
        self.assertEqual(session.user, self.user1)
        self.assertEqual(session.quiz, self.quiz_exam)

    # -------------------------------------------------------------------------
    # 2) Seul l'utilisateur qui a lancé le quiz + admin peuvent répondre
    # -------------------------------------------------------------------------

    def test_attempt_owner_can_answer_question(self):
        """
        Le propriétaire de la session peut répondre à une question.
        """
        # On démarre une session pour user1 sur le quiz d'examen
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        # On s'assure que le client est authentifié en tant que user1
        self.client.force_authenticate(user=self.user1)

        url = self._attempt_url(session, order=1)

        # On répond en cochant l'option "Paris" (bonne réponse)
        payload = {
            "selected_option_ids": [self.opt_paris.id],
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)

        data = resp.json()
        self.assertEqual(data["session"], str(session.id))
        self.assertEqual(data["question"], self.question_exam.id)
        self.assertEqual(data["question_order"], 1)
        self.assertEqual(data["selected_option_ids"], [self.opt_paris.id])
        self.assertTrue(data["is_correct"])

    def test_attempt_other_user_cannot_answer_question(self):
        """
        Un autre utilisateur connecté ne peut PAS répondre
        à la session d'un autre -> 403.
        """
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=self.user2)
        url = self._attempt_url(session, order=1)
        payload = {"given_answer": "Paris"}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_attempt_admin_can_answer_any_session(self):
        """
        Un admin/staff peut répondre pour n'importe quelle session.
        """
        # On crée une session appartenant à user1
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        # On authentifie l'admin
        self.client.force_authenticate(user=self.admin)

        url = self._attempt_url(session, order=1)
        payload = {
            "selected_option_ids": [self.opt_paris.id],
        }

        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)

        data = resp.json()
        self.assertEqual(data["session"], str(session.id))
        self.assertEqual(data["question"], self.question_exam.id)
        self.assertEqual(data["question_order"], 1)
        self.assertEqual(data["selected_option_ids"], [self.opt_paris.id])
        self.assertTrue(data["is_correct"])


    def test_attempt_unauthenticated_cannot_answer(self):
        """
        Non authentifié -> 401 sur /attempt/.
        """
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=None)
        url = self._attempt_url(session, order=1)
        payload = {"given_answer": "Paris"}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------------------------------
    # 3) Seul le propriétaire + admin peuvent CLÔTURER le quiz
    # -------------------------------------------------------------------------

    def test_owner_can_close_quiz(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        url = self._close_url(session)
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        session.refresh_from_db()
        self.assertTrue(session.is_closed)

    def test_other_user_cannot_close_quiz(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=self.user2)
        url = self._close_url(session)
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_close_any_quiz(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=self.admin)
        url = self._close_url(session)
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_close_quiz(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=None)
        url = self._close_url(session)
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------------------------------
    # 4) Seul le propriétaire + admin peuvent DEMANDER LE RÉSULTAT (summary)
    # -------------------------------------------------------------------------

    def test_owner_can_get_quiz_summary(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        # simulons une réponse
        QuizAttempt.objects.create(
            session=session,
            question=self.question_exam,
            question_order=1,
            given_answer="Paris",
            is_correct=True,
        )

        url = self._summary_url(session)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["quiz_id"], str(session.id))
        self.assertEqual(resp.data["answered_questions"], 1)
        self.assertEqual(resp.data["correct_answers"], 1)

    def test_other_user_cannot_get_quiz_summary(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=self.user2)
        url = self._summary_url(session)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_get_summary_for_any_quiz(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=self.admin)
        url = self._summary_url(session)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_get_summary(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=None)
        url = self._summary_url(session)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------------------------------
    # 5) Seul le propriétaire + admin peuvent voir la QUESTION pour cette session
    # -------------------------------------------------------------------------

    def test_owner_can_get_question_detail(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_get_question_detail(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=self.user2)
        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_get_question_detail(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=self.admin)
        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_get_question_detail(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=None)
        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------------------------------
    # 6) Règle d'affichage de is_correct sur les options
    #
    # - On n'envoie is_correct que si :
    #   * le quiz est en mode practice
    #   OU
    #   * la session est clôturée
    # -------------------------------------------------------------------------

    def test_question_detail_hides_is_correct_in_exam_mode_before_close(self):
        """
        Mode EXAM + session non clôturée -> on NE renvoie PAS is_correct dans les options.
        """
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        options = resp.data.get("options", [])
        # On s'attend à ce que les options ne contiennent pas le champ is_correct
        for opt in options:
            self.assertNotIn("is_correct", opt)

    def test_question_detail_shows_is_correct_in_exam_mode_after_close(self):
        """
        Mode EXAM + session clôturée -> on renvoie is_correct dans les options.
        """
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)
        session.is_closed = True
        session.save()

        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        options = resp.data.get("options", [])
        # Cette fois, is_correct doit être présent sur les options
        self.assertGreater(len(options), 0)
        for opt in options:
            self.assertIn("is_correct", opt)

    def test_question_detail_shows_is_correct_in_practice_mode_even_if_not_closed(self):
        """
        Mode PRACTICE + session non clôturée -> on renvoie is_correct dans les options.
        """
        session = self._start_session_for_quiz(self.quiz_practice, self.user1)

        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        options = resp.data.get("options", [])
        self.assertGreater(len(options), 0)
        for opt in options:
            self.assertIn("is_correct", opt)


class QuizAdminAPITestCase(APITestCase):
    """
    Tests API pour les endpoints d'administration des quiz :

      - POST /api/quiz/           -> créer un quiz (renvoie le slug)
      - GET  /api/quiz/           -> lister les quiz
      - GET  /api/quiz/{slug}/    -> détail d'un quiz
      - PUT/PATCH/DELETE /api/quiz/{slug}/

    Gestion des questions d'un quiz :

      - GET    /api/quiz/{slug}/questions/
      - POST   /api/quiz/{slug}/add-question/
      - DELETE /api/quiz/{slug}/remove-question/{question_id}/

    Toutes ces opérations doivent être réservées aux administrateurs.
    """

    def setUp(self):
        # Admin
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass",
            is_staff=True,
            is_superuser=True,
        )

        # Utilisateur normal
        self.user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="userpass",
            is_staff=False,
            is_superuser=False,
        )

        # URL de base depuis le router DRF
        # app_name = "quiz", inclus dans "api"
        self.list_url = reverse("api:quiz:quiz-list")

    # ---------- Helpers ----------

    def _get_token(self, username: str, password: str) -> str:
        """
        Helper pour récupérer un token JWT via /api/token/
        (SimpleJWT, comme déjà utilisé ailleurs dans ton projet).
        """
        resp = self.client.post(
            "/api/token/",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)
        return resp.data["access"]

    def _auth_as_admin(self):
        token = self._get_token("admin", "adminpass")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _auth_as_user(self):
        token = self._get_token("user", "userpass")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # ---------- Tests CRUD Quiz (admin only) ----------

    def test_admin_can_create_quiz(self):
        """Un admin peut créer un quiz via POST /api/quiz/."""
        self._auth_as_admin()

        payload = {
            "title": "Quiz Scrum & Django",
            "description": "Quiz d’examen sur Scrum et Django.",
            "max_questions": 10,
            "is_active": True,
        }

        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)

        data = resp.data
        self.assertIn("id", data)
        self.assertIn("slug", data)
        self.assertEqual(data["title"], payload["title"])
        self.assertTrue(data["slug"])

        self.assertEqual(Quiz.objects.count(), 1)

    def test_non_admin_cannot_create_quiz(self):
        """Un utilisateur non admin doit recevoir 403 sur POST /api/quiz/."""
        self._auth_as_user()

        payload = {
            "title": "Quiz interdit",
            "description": "",
            "max_questions": 5,
            "is_active": True,
        }

        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create_quiz(self):
        """Un utilisateur non authentifié doit recevoir 401 sur POST /api/quiz/."""
        payload = {
            "title": "Quiz non authentifié",
            "description": "",
            "max_questions": 5,
            "is_active": True,
        }

        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_list_quizzes(self):
        """Un admin peut lister les quiz via GET /api/quiz/."""
        # On crée des Quiz directement en DB
        Quiz.objects.create(title="Quiz A", description="", max_questions=5)
        Quiz.objects.create(title="Quiz B", description="", max_questions=10)

        self._auth_as_admin()
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertGreaterEqual(len(resp.data), 2)
        titles = {item["title"] for item in resp.data}
        self.assertIn("Quiz A", titles)
        self.assertIn("Quiz B", titles)

    def test_non_admin_cannot_list_quizzes(self):
        """Un utilisateur non admin doit recevoir 403 sur GET /api/quiz/."""
        Quiz.objects.create(title="Quiz A", description="", max_questions=5)

        self._auth_as_user()
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_list_quizzes(self):
        """Un utilisateur non authentifié doit recevoir 401 sur GET /api/quiz/."""
        Quiz.objects.create(title="Quiz A", description="", max_questions=5)

        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_retrieve_quiz_by_slug(self):
        """Un admin peut récupérer le détail d’un quiz via GET /api/quiz/{slug}/."""
        quiz = Quiz.objects.create(title="Quiz Detail", description="", max_questions=5)
        detail_url = reverse("api:quiz:quiz-detail", kwargs={"slug": quiz.slug})

        self._auth_as_admin()
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertEqual(resp.data["id"], quiz.id)
        self.assertEqual(resp.data["title"], "Quiz Detail")

    def test_non_admin_cannot_retrieve_quiz(self):
        """Un utilisateur non admin doit recevoir 403 sur GET /api/quiz/{slug}/."""
        quiz = Quiz.objects.create(title="Quiz Secret", description="", max_questions=5)
        detail_url = reverse("api:quiz:quiz-detail", kwargs={"slug": quiz.slug})

        self._auth_as_user()
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_and_delete_quiz(self):
        """Un admin peut PUT/PATCH/DELETE /api/quiz/{slug}/."""
        quiz = Quiz.objects.create(title="Old Title", description="", max_questions=5)
        detail_url = reverse("api:quiz:quiz-detail", kwargs={"slug": quiz.slug})

        self._auth_as_admin()

        # PATCH
        resp = self.client.patch(detail_url, {"title": "New Title"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        quiz.refresh_from_db()
        self.assertEqual(quiz.title, "New Title")

        # DELETE
        resp = self.client.delete(detail_url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(id=quiz.id).exists())

    # ---------- Tests gestion des questions d'un quiz ----------

    def _create_quiz_and_question(self):
        """Helper : crée un quiz et une question en DB."""
        quiz = Quiz.objects.create(
            title="Quiz Questions",
            description="",
            max_questions=10,
            is_active=True,
        )
        question = Question.objects.create(
            title="Question 1",
            description="",
            explanation="",
            allow_multiple_correct=True,
        )
        return quiz, question

    def test_admin_can_add_question_to_quiz(self):
        """Un admin peut ajouter une question à un quiz via POST /api/quiz/{slug}/add-question/."""
        quiz, question = self._create_quiz_and_question()
        url = reverse("api:quiz:quiz-add-question", kwargs={"slug": quiz.slug})

        self._auth_as_admin()
        payload = {
            "question_id": question.id,
            "sort_order": 1,
            "weight": 2,
        }
        resp = self.client.post(url, payload, format="json")
        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))

        # Vérifie en DB
        qq = QuizQuestion.objects.get(quiz=quiz, question=question)
        self.assertEqual(qq.sort_order, 1)
        self.assertEqual(qq.weight, 2)

    def test_admin_can_update_existing_question_link(self):
        """Un second POST sur add-question met à jour sort_order/weight."""
        quiz, question = self._create_quiz_and_question()
        QuizQuestion.objects.create(
            quiz=quiz,
            question=question,
            sort_order=1,
            weight=1,
        )
        url = reverse("api:quiz:quiz-add-question", kwargs={"slug": quiz.slug})

        self._auth_as_admin()
        payload = {
            "question_id": question.id,
            "sort_order": 5,
            "weight": 3,
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        qq = QuizQuestion.objects.get(quiz=quiz, question=question)
        self.assertEqual(qq.sort_order, 5)
        self.assertEqual(qq.weight, 3)

    def test_admin_can_list_questions_of_quiz(self):
        """GET /api/quiz/{slug}/questions/ retourne la liste des QuizQuestion."""
        quiz, question = self._create_quiz_and_question()
        QuizQuestion.objects.create(
            quiz=quiz,
            question=question,
            sort_order=1,
            weight=1,
        )
        url = reverse("api:quiz:quiz-questions", kwargs={"slug": quiz.slug})

        self._auth_as_admin()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["question"], question.id)
        self.assertEqual(resp.data[0]["sort_order"], 1)
        self.assertEqual(resp.data[0]["weight"], 1)

    def test_admin_can_remove_question_from_quiz(self):
        """DELETE /api/quiz/{slug}/remove-question/{question_id}/ retire le lien QuizQuestion."""
        quiz, question = self._create_quiz_and_question()
        QuizQuestion.objects.create(
            quiz=quiz,
            question=question,
            sort_order=1,
            weight=1,
        )
        url = reverse(
            "api:quiz:quiz-remove-question",
            kwargs={"slug": quiz.slug, "question_id": question.id},
        )

        self._auth_as_admin()
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            QuizQuestion.objects.filter(quiz=quiz, question=question).exists()
        )

    # ---------- Permissions sur gestion des questions ----------

    def test_non_admin_cannot_manage_quiz_questions(self):
        """Un utilisateur non admin doit recevoir 403 sur les endpoints questions/add/remove."""
        quiz, question = self._create_quiz_and_question()
        QuizQuestion.objects.create(
            quiz=quiz,
            question=question,
            sort_order=1,
            weight=1,
        )

        list_url = reverse("api:quiz:quiz-questions", kwargs={"slug": quiz.slug})
        add_url = reverse("api:quiz:quiz-add-question", kwargs={"slug": quiz.slug})
        remove_url = reverse(
            "api:quiz:quiz-remove-question",
            kwargs={"slug": quiz.slug, "question_id": question.id},
        )

        self._auth_as_user()

        # GET questions
        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # POST add-question
        resp = self.client.post(
            add_url,
            {"question_id": question.id, "sort_order": 2, "weight": 2},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # DELETE remove-question
        resp = self.client.delete(remove_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_manage_quiz_questions(self):
        """Un utilisateur non authentifié doit recevoir 401 sur les endpoints questions/add/remove."""
        quiz, question = self._create_quiz_and_question()
        QuizQuestion.objects.create(
            quiz=quiz,
            question=question,
            sort_order=1,
            weight=1,
        )

        list_url = reverse("api:quiz:quiz-questions", kwargs={"slug": quiz.slug})
        add_url = reverse("api:quiz:quiz-add-question", kwargs={"slug": quiz.slug})
        remove_url = reverse(
            "api:quiz:quiz-remove-question",
            kwargs={"slug": quiz.slug, "question_id": question.id},
        )

        # GET questions
        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # POST add-question
        resp = self.client.post(
            add_url,
            {"question_id": question.id, "sort_order": 2, "weight": 2},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # DELETE remove-question
        resp = self.client.delete(remove_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)