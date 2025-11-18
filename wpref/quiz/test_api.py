# quiz/tests/test_quiz_api.py

from uuid import UUID

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from quiz.models import Quiz, QuizQuestion, QuizSession, QuizAttempt
from question.models import Question, AnswerOption


class QuizAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

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
        return reverse(
            "api:quiz:quiz-question-detail",
            kwargs={"quiz_id": session.id, "question_order": order},
        )

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
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        url = self._attempt_url(session, order=1)
        payload = {"given_answer": "Paris"}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        attempt = QuizAttempt.objects.get(session=session, question_order=1)
        self.assertEqual(attempt.given_answer, "Paris")

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
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=self.admin)
        url = self._attempt_url(session, order=1)
        payload = {"given_answer": "Paris"}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

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

        url = self._question_detail_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_get_question_detail(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=self.user2)
        url = self._question_detail_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_get_question_detail(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=self.admin)
        url = self._question_detail_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_get_question_detail(self):
        session = self._start_session_for_quiz(self.quiz_exam, self.user1)

        self.client.force_authenticate(user=None)
        url = self._question_detail_url(session, order=1)
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

        url = self._question_detail_url(session, order=1)
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

        url = self._question_detail_url(session, order=1)
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

        url = self._question_detail_url(session, order=1)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        options = resp.data.get("options", [])
        self.assertGreater(len(options), 0)
        for opt in options:
            self.assertIn("is_correct", opt)
