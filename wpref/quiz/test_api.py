# quiz/tests/test_quiz_api.py

from uuid import UUID

from django.contrib.auth import get_user_model
from django.urls import reverse
from question.models import Question, AnswerOption
from quiz.models import Quiz, QuizQuestion, QuizSession, QuizAttempt
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class QuizAPITestCase(APITestCase):
    """
    Tests combinés :
      - API "joueur" (start/attempt/close/summary/question)
      - API "admin" (CRUD des quiz + gestion des questions d'un quiz)
    """

    @classmethod
    def setUpTestData(cls):
        # Utilisateurs
        cls.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="password123",
        )
        cls.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="password123",
        )
        cls.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass",
            is_staff=True,
            is_superuser=True,
        )

        # Quiz EXAM
        cls.quiz_exam = Quiz.objects.create(
            title="Quiz Examen",
            description="Mode examen",
            mode=Quiz.MODE_EXAM,
        )

        # Quiz PRACTICE
        cls.quiz_practice = Quiz.objects.create(
            title="Quiz Practice",
            description="Mode practice",
            mode=Quiz.MODE_PRACTICE,
        )

        # Question + options
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

        # Lier la question aux deux quiz
        QuizQuestion.objects.create(
            quiz=cls.quiz_exam,
            question=cls.question_exam,
            sort_order=1,
            weight=1,
        )
        QuizQuestion.objects.create(
            quiz=cls.quiz_practice,
            question=cls.question_exam,
            sort_order=1,
            weight=1,
        )

    def setUp(self):
        # Par défaut, on travaille avec user1
        self.client.force_authenticate(user=self.user1)

    # -------------------------------------------------------------------------
    # Helpers génériques
    # -------------------------------------------------------------------------
    def _auth_as(self, user):
        self.client.force_authenticate(user=user)

    def _auth_as_admin(self):
        self._auth_as(self.admin)

    def _auth_as_user1(self):
        self._auth_as(self.user1)

    def _auth_as_user2(self):
        self._auth_as(self.user2)

    def _auth_anonymous(self):
        self.client.force_authenticate(user=None)

    # -------------------------------------------------------------------------
    # Helpers URLs
    # -------------------------------------------------------------------------
    @staticmethod
    def _quiz_list_url():
        return reverse("api:quiz:quiz-list")

    @staticmethod
    def _quiz_detail_url(quiz):
        return reverse("api:quiz:quiz-detail", kwargs={"slug": quiz.slug})

    @staticmethod
    def _quiz_questions_url(quiz):
        return reverse("api:quiz:quiz-questions", kwargs={"slug": quiz.slug})

    @staticmethod
    def _quiz_add_question_url(quiz):
        return reverse("api:quiz:quiz-add-question", kwargs={"slug": quiz.slug})

    @staticmethod
    def _quiz_remove_question_url(quiz, question):
        return reverse(
            "api:quiz:quiz-remove-question",
            kwargs={"slug": quiz.slug, "question_id": question.id},
        )

    @staticmethod
    def _attempt_url(session, order=1):
        return reverse(
            "api:quiz:quiz-attempt",
            kwargs={"quiz_id": session.id, "question_order": order},
        )

    @staticmethod
    def _close_url(session):
        return reverse("api:quiz:quiz-close", kwargs={"quiz_id": session.id})

    @staticmethod
    def _summary_url(session):
        return reverse("api:quiz:quiz-summary", kwargs={"quiz_id": session.id})

    # -------------------------------------------------------------------------
    # Helpers métier
    # -------------------------------------------------------------------------

    def _start_session_for_quiz(self, quiz, as_user):
        """
        Helper : démarre une session de quiz via l'API /start/.
        """
        self._auth_as(as_user)
        url = reverse("api:quiz:quiz-start", kwargs={"slug": quiz.slug})
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)
        quiz_id_str = resp.data["id"]
        # Vérification UUID valide
        UUID(quiz_id_str)
        return QuizSession.objects.get(id=quiz_id_str)

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

    # -------------------------------------------------------------------------
    # 1) Démarrage de quiz (auth obligatoire)
    # -------------------------------------------------------------------------

    def test_start_quiz_requires_authentication(self):
        self._auth_anonymous()
        url = reverse("api:quiz:quiz-start", kwargs={"slug": self.quiz_exam.slug})
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_start_quiz(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)
        self.assertEqual(session.user, self.user1)
        self.assertEqual(session.quiz, self.quiz_exam)

    # -------------------------------------------------------------------------
    # 2) Permissions pour répondre aux questions (attempt)
    # -------------------------------------------------------------------------

    def test_attempt_owner_can_answer_question(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)
        self._auth_as_user1()

        url = self._attempt_url(session, order=1)
        payload = {"selected_option_ids": [self.opt_paris.id]}

        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)

        data = resp.json()
        self.assertEqual(data["session"], str(session.id))
        self.assertEqual(data["question"], self.question_exam.id)
        self.assertEqual(data["question_order"], 1)
        self.assertEqual(data["selected_option_ids"], [self.opt_paris.id])
        self.assertTrue(data["is_correct"])

    def test_attempt_other_user_cannot_answer_question(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self._auth_as_user2()
        url = self._attempt_url(session, order=1)
        payload = {"given_answer": "Paris"}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_attempt_admin_can_answer_any_session(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self._auth_as_admin()
        url = self._attempt_url(session, order=1)
        payload = {"selected_option_ids": [self.opt_paris.id]}

        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.content)

        data = resp.json()
        self.assertEqual(data["session"], str(session.id))
        self.assertEqual(data["question"], self.question_exam.id)
        self.assertEqual(data["question_order"], 1)
        self.assertEqual(data["selected_option_ids"], [self.opt_paris.id])
        self.assertTrue(data["is_correct"])

    def test_attempt_unauthenticated_cannot_answer(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self._auth_anonymous()
        url = self._attempt_url(session, order=1)
        payload = {"given_answer": "Paris"}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------------------------------
    # 3) Permissions pour clôturer un quiz
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

        self._auth_as_user2()
        url = self._close_url(session)
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_close_any_quiz(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self._auth_as_admin()
        url = self._close_url(session)
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_close_quiz(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self._auth_anonymous()
        url = self._close_url(session)
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------------------------------
    # 4) Permissions summary
    # -------------------------------------------------------------------------

    def test_owner_can_get_quiz_summary(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

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

        self._auth_as_user2()
        url = self._summary_url(session)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_get_summary_for_any_quiz(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self._auth_as_admin()
        url = self._summary_url(session)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_get_summary(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self._auth_anonymous()
        url = self._summary_url(session)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------------------------------
    # 5) Permissions question detail (GET /attempt/)
    # -------------------------------------------------------------------------

    def test_owner_can_get_question_detail(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_get_question_detail(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self._auth_as_user2()
        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_get_question_detail(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self._auth_as_admin()
        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_get_question_detail(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self._auth_anonymous()
        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------------------------------
    # 6) Règle d'affichage de is_correct sur les options
    # -------------------------------------------------------------------------

    def test_question_detail_hides_is_correct_in_exam_mode_before_close(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        options = resp.data.get("options", [])
        for opt in options:
            self.assertNotIn("is_correct", opt)

    def test_question_detail_shows_is_correct_in_exam_mode_after_close(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)
        session.is_closed = True
        session.save()

        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        options = resp.data.get("options", [])
        self.assertGreater(len(options), 0)
        for opt in options:
            self.assertIn("is_correct", opt)

    def test_question_detail_shows_is_correct_in_practice_mode_even_if_not_closed(self):
        session = self._start_session_for_quiz(self.quiz_practice, self.user1)

        url = self._attempt_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        options = resp.data.get("options", [])
        self.assertGreater(len(options), 0)
        for opt in options:
            self.assertIn("is_correct", opt)

    # -------------------------------------------------------------------------
    # 7) Admin : CRUD des quiz
    # -------------------------------------------------------------------------

    def test_admin_can_create_quiz(self):
        self._auth_as_admin()

        payload = {
            "title": "Quiz Scrum & Django",
            "description": "Quiz d’examen sur Scrum et Django.",
            "max_questions": 10,
            "is_active": True,
        }

        resp = self.client.post(self._quiz_list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.content)

        data = resp.data
        self.assertIn("id", data)
        self.assertIn("slug", data)
        self.assertEqual(data["title"], payload["title"])
        self.assertTrue(data["slug"])
        self.assertEqual(Quiz.objects.count(), Quiz.objects.count())  # juste que ça ne plante pas

    def test_non_admin_cannot_create_quiz(self):
        self._auth_as_user1()

        payload = {
            "title": "Quiz interdit",
            "description": "",
            "max_questions": 5,
            "is_active": True,
        }

        resp = self.client.post(self._quiz_list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create_quiz(self):
        self._auth_anonymous()

        payload = {
            "title": "Quiz non authentifié",
            "description": "",
            "max_questions": 5,
            "is_active": True,
        }

        resp = self.client.post(self._quiz_list_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_list_quizzes(self):
        Quiz.objects.create(title="Quiz A", description="", max_questions=5)
        Quiz.objects.create(title="Quiz B", description="", max_questions=10)

        self._auth_as_admin()
        resp = self.client.get(self._quiz_list_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertGreaterEqual(len(resp.data), 2)
        titles = {item["title"] for item in resp.data}
        self.assertIn("Quiz A", titles)
        self.assertIn("Quiz B", titles)

    def test_non_admin_cannot_list_quizzes(self):
        Quiz.objects.create(title="Quiz A", description="", max_questions=5)

        self._auth_as_user1()
        resp = self.client.get(self._quiz_list_url())
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_list_quizzes(self):
        Quiz.objects.create(title="Quiz A", description="", max_questions=5)

        self._auth_anonymous()
        resp = self.client.get(self._quiz_list_url())
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_retrieve_quiz_by_slug(self):
        quiz = Quiz.objects.create(title="Quiz Detail", description="", max_questions=5)
        detail_url = self._quiz_detail_url(quiz)

        self._auth_as_admin()
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], quiz.id)
        self.assertEqual(resp.data["title"], "Quiz Detail")

    def test_non_admin_cannot_retrieve_quiz(self):
        quiz = Quiz.objects.create(title="Quiz Secret", description="", max_questions=5)
        detail_url = self._quiz_detail_url(quiz)

        self._auth_as_user1()
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_and_delete_quiz(self):
        quiz = Quiz.objects.create(title="Old Title", description="", max_questions=5)
        detail_url = self._quiz_detail_url(quiz)

        self._auth_as_admin()

        resp = self.client.patch(detail_url, {"title": "New Title"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        quiz.refresh_from_db()
        self.assertEqual(quiz.title, "New Title")

        resp = self.client.delete(detail_url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(id=quiz.id).exists())

    # -------------------------------------------------------------------------
    # 8) Admin : gestion des questions d'un quiz
    # -------------------------------------------------------------------------

    def test_admin_can_add_question_to_quiz(self):
        quiz, question = self._create_quiz_and_question()
        url = self._quiz_add_question_url(quiz)

        self._auth_as_admin()
        payload = {"question_id": question.id, "sort_order": 1, "weight": 2}
        resp = self.client.post(url, payload, format="json")
        self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))

        qq = QuizQuestion.objects.get(quiz=quiz, question=question)
        self.assertEqual(qq.sort_order, 1)
        self.assertEqual(qq.weight, 2)

    def test_admin_can_update_existing_question_link(self):
        quiz, question = self._create_quiz_and_question()
        QuizQuestion.objects.create(
            quiz=quiz,
            question=question,
            sort_order=1,
            weight=1,
        )
        url = self._quiz_add_question_url(quiz)

        self._auth_as_admin()
        payload = {"question_id": question.id, "sort_order": 5, "weight": 3}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        qq = QuizQuestion.objects.get(quiz=quiz, question=question)
        self.assertEqual(qq.sort_order, 5)
        self.assertEqual(qq.weight, 3)

    def test_admin_can_list_questions_of_quiz(self):
        quiz, question = self._create_quiz_and_question()
        QuizQuestion.objects.create(
            quiz=quiz,
            question=question,
            sort_order=1,
            weight=1,
        )
        url = self._quiz_questions_url(quiz)

        self._auth_as_admin()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["question"], question.id)
        self.assertEqual(resp.data[0]["sort_order"], 1)
        self.assertEqual(resp.data[0]["weight"], 1)

    def test_admin_can_remove_question_from_quiz(self):
        quiz, question = self._create_quiz_and_question()
        QuizQuestion.objects.create(
            quiz=quiz,
            question=question,
            sort_order=1,
            weight=1,
        )
        url = self._quiz_remove_question_url(quiz, question)

        self._auth_as_admin()
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            QuizQuestion.objects.filter(quiz=quiz, question=question).exists()
        )

    def test_non_admin_cannot_manage_quiz_questions(self):
        quiz, question = self._create_quiz_and_question()
        QuizQuestion.objects.create(
            quiz=quiz,
            question=question,
            sort_order=1,
            weight=1,
        )

        list_url = self._quiz_questions_url(quiz)
        add_url = self._quiz_add_question_url(quiz)
        remove_url = self._quiz_remove_question_url(quiz, question)

        self._auth_as_user1()

        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        resp = self.client.post(
            add_url,
            {"question_id": question.id, "sort_order": 2, "weight": 2},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        resp = self.client.delete(remove_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_manage_quiz_questions(self):
        quiz, question = self._create_quiz_and_question()
        QuizQuestion.objects.create(
            quiz=quiz,
            question=question,
            sort_order=1,
            weight=1,
        )

        list_url = self._quiz_questions_url(quiz)
        add_url = self._quiz_add_question_url(quiz)
        remove_url = self._quiz_remove_question_url(quiz, question)

        self._auth_anonymous()

        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        resp = self.client.post(
            add_url,
            {"question_id": question.id, "sort_order": 2, "weight": 2},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        resp = self.client.delete(remove_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
