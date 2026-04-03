from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone, translation
from domain.models import Domain
from question.models import AnswerOption, Question, QuestionSubject
from quiz.constants import VISIBILITY_IMMEDIATE
from quiz.models import Quiz, QuizAlertThread, QuizQuestion, QuizTemplate
from quiz.services import create_quizzes_from_template
from rest_framework import status
from rest_framework.test import APITestCase
from subject.models import Subject

User = get_user_model()


class QuizAlertsApiTestCase(APITestCase):
    @staticmethod
    def _as_list(data):
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        return data

    def setUp(self):
        super().setUp()
        translation.activate("fr")
        self.owner = User.objects.create_user(username="owner", password="pass", is_staff=True)
        self.reporter = User.objects.create_user(username="reporter", password="pass", language="fr")
        self.other = User.objects.create_user(username="other", password="pass")
        self.domain = Domain.objects.create(owner=self.owner, name="D1", description="", active=True)
        self.subject = self._make_subject("Sujet")
        self.question = self._make_question("Question 1")
        self.template = QuizTemplate.objects.create(
            domain=self.domain,
            title="Quiz alerte",
            mode=QuizTemplate.MODE_EXAM,
            description="",
            max_questions=10,
            permanent=True,
            with_duration=False,
            duration=10,
            is_public=True,
            active=True,
            result_visibility=VISIBILITY_IMMEDIATE,
            detail_visibility=VISIBILITY_IMMEDIATE,
            created_by=self.owner,
        )
        self.quizquestion = QuizQuestion.objects.create(
            quiz=self.template,
            question=self.question,
            sort_order=1,
            weight=1,
        )
        self.quiz = Quiz.objects.create(
            domain=self.domain,
            quiz_template=self.template,
            user=self.reporter,
            active=True,
            started_at=timezone.now(),
        )

    def tearDown(self):
        translation.deactivate_all()
        super().tearDown()

    def _make_subject(self, name: str) -> Subject:
        try:
            return Subject.objects.create(domain=self.domain, name=name)
        except TypeError:
            return Subject.objects.create(name=name)

    def _make_question(self, title: str) -> Question:
        question = Question.objects.create(
            domain=self.domain,
            title=title,
            description="desc",
            explanation="exp",
            allow_multiple_correct=False,
            active=True,
            is_mode_practice=True,
            is_mode_exam=True,
        )
        QuestionSubject.objects.create(question=question, subject=self.subject, sort_order=1)
        AnswerOption.objects.create(question=question, content="A", is_correct=True, sort_order=1)
        AnswerOption.objects.create(question=question, content="B", is_correct=False, sort_order=2)
        return question

    def _rev(self, name: str, **kwargs) -> str:
        for candidate in (f"api:quiz-api:{name}", f"quiz-api:{name}"):
            try:
                return reverse(candidate, kwargs=kwargs)
            except Exception:
                continue
        raise AssertionError(f"Route introuvable: {name}")

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_reporter_can_create_alert_and_owner_sees_it_unread(self):
        self._auth(self.reporter)
        create_url = self._rev("quiz-alert-list")
        res = self.client.post(
            create_url,
            {
                "quiz_id": self.quiz.id,
                "question_id": self.question.id,
                "body": "Le libellé me semble ambigu.",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        thread_id = res.data["id"]
        thread = QuizAlertThread.objects.get(pk=thread_id)
        self.assertEqual(thread.reporter_id, self.reporter.id)
        self.assertEqual(thread.owner_id, self.owner.id)
        self.assertEqual(thread.reported_language, "fr")
        self.assertEqual(thread.messages.count(), 1)

        self._auth(self.owner)
        list_res = self.client.get(create_url)
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        results = self._as_list(list_res.data)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["unread"])

        unread_url = self._rev("quiz-alert-unread-count")
        unread_res = self.client.get(unread_url)
        self.assertEqual(unread_res.status_code, status.HTTP_200_OK)
        self.assertEqual(unread_res.data["count"], 1)

    def test_retrieve_marks_thread_as_read_for_current_user(self):
        thread = QuizAlertThread.objects.create(
            quiz=self.quiz,
            quizquestion=self.quizquestion,
            reporter=self.reporter,
            owner=self.owner,
            reported_language="fr",
        )
        thread.messages.create(author=self.reporter, body="Question sur la réponse.")

        self._auth(self.owner)
        url = self._rev("quiz-alert-detail", alert_id=thread.id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        thread.refresh_from_db()
        self.assertIsNotNone(thread.owner_last_read_at)

    def test_unread_count_only_tracks_new_incoming_messages(self):
        thread = QuizAlertThread.objects.create(
            quiz=self.quiz,
            quizquestion=self.quizquestion,
            reporter=self.reporter,
            owner=self.owner,
            reported_language="fr",
        )
        first = thread.messages.create(author=self.reporter, body="Premier message")

        self._auth(self.owner)
        detail_url = self._rev("quiz-alert-detail", alert_id=thread.id)
        self.client.get(detail_url)
        thread.refresh_from_db()
        first_read_at = thread.owner_last_read_at
        self.assertIsNotNone(first_read_at)
        self.assertEqual(thread.unread_count_for(self.owner), 0)

        second = thread.messages.create(author=self.reporter, body="Deuxième message")
        thread.refresh_from_db()
        self.assertEqual(thread.unread_count_for(self.owner), 1)
        self.assertTrue(thread.unread_for(self.owner))
        self.assertGreater(second.created_at, first.created_at)

    def test_reporter_cannot_reply_until_owner_allows_it(self):
        thread = QuizAlertThread.objects.create(
            quiz=self.quiz,
            quizquestion=self.quizquestion,
            reporter=self.reporter,
            owner=self.owner,
            reported_language="fr",
            reporter_reply_allowed=False,
        )
        thread.messages.create(author=self.reporter, body="Message initial")

        message_url = self._rev("quiz-alert-message", alert_id=thread.id)

        self._auth(self.reporter)
        blocked = self.client.post(message_url, {"body": "Puis-je préciser ?"}, format="json")
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)

        self._auth(self.owner)
        detail_url = self._rev("quiz-alert-detail", alert_id=thread.id)
        patch_res = self.client.patch(detail_url, {"reporter_reply_allowed": True}, format="json")
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)

        self._auth(self.reporter)
        allowed = self.client.post(message_url, {"body": "Je donne un exemple précis."}, format="json")
        self.assertEqual(allowed.status_code, status.HTTP_201_CREATED)
        thread.refresh_from_db()
        self.assertEqual(thread.messages.count(), 2)

    def test_owner_can_reply_and_close_conversation(self):
        thread = QuizAlertThread.objects.create(
            quiz=self.quiz,
            quizquestion=self.quizquestion,
            reporter=self.reporter,
            owner=self.owner,
            reported_language="fr",
        )
        thread.messages.create(author=self.reporter, body="Message initial")

        self._auth(self.owner)
        message_url = self._rev("quiz-alert-message", alert_id=thread.id)
        reply_res = self.client.post(message_url, {"body": "Merci, nous corrigeons."}, format="json")
        self.assertEqual(reply_res.status_code, status.HTTP_201_CREATED)

        close_url = self._rev("quiz-alert-close", alert_id=thread.id)
        close_res = self.client.post(close_url, {}, format="json")
        self.assertEqual(close_res.status_code, status.HTTP_200_OK)

        thread.refresh_from_db()
        self.assertEqual(thread.status, QuizAlertThread.STATUS_CLOSED)
        self.assertIsNotNone(thread.closed_at)
        self.assertEqual(thread.closed_by_id, self.owner.id)

    def test_only_owner_can_reopen_closed_conversation(self):
        thread = QuizAlertThread.objects.create(
            quiz=self.quiz,
            quizquestion=self.quizquestion,
            reporter=self.reporter,
            owner=self.owner,
            reported_language="fr",
            status=QuizAlertThread.STATUS_CLOSED,
            closed_at=timezone.now(),
            closed_by=self.owner,
        )
        thread.messages.create(author=self.reporter, body="Message initial")

        reopen_url = self._rev("quiz-alert-reopen", alert_id=thread.id)
        message_url = self._rev("quiz-alert-message", alert_id=thread.id)

        self._auth(self.reporter)
        reporter_reopen = self.client.post(reopen_url, {}, format="json")
        self.assertEqual(reporter_reopen.status_code, status.HTTP_403_FORBIDDEN)

        reporter_message = self.client.post(message_url, {"body": "Je relance."}, format="json")
        self.assertEqual(reporter_message.status_code, status.HTTP_400_BAD_REQUEST)

        self._auth(self.owner)
        owner_reopen = self.client.post(reopen_url, {}, format="json")
        self.assertEqual(owner_reopen.status_code, status.HTTP_200_OK)
        self.assertEqual(owner_reopen.data["status"], QuizAlertThread.STATUS_OPEN)
        self.assertTrue(owner_reopen.data["can_reply"])

        toggle_url = self._rev("quiz-alert-detail", alert_id=thread.id)
        toggle_res = self.client.patch(toggle_url, {"reporter_reply_allowed": True}, format="json")
        self.assertEqual(toggle_res.status_code, status.HTTP_200_OK)
        self.assertTrue(toggle_res.data["reporter_reply_allowed"])

        owner_message = self.client.post(message_url, {"body": "Conversation rouverte."}, format="json")
        self.assertEqual(owner_message.status_code, status.HTTP_201_CREATED)

        close_url = self._rev("quiz-alert-close", alert_id=thread.id)
        close_res = self.client.post(close_url, {}, format="json")
        self.assertEqual(close_res.status_code, status.HTTP_200_OK)
        self.assertEqual(close_res.data["status"], QuizAlertThread.STATUS_CLOSED)

    def test_non_participant_cannot_access_thread(self):
        thread = QuizAlertThread.objects.create(
            quiz=self.quiz,
            quizquestion=self.quizquestion,
            reporter=self.reporter,
            owner=self.owner,
            reported_language="fr",
        )
        thread.messages.create(author=self.reporter, body="Message initial")

        self._auth(self.other)
        detail_url = self._rev("quiz-alert-detail", alert_id=thread.id)
        res = self.client.get(detail_url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_assigning_quiz_creates_unread_assignment_alert_in_recipient_language(self):
        self.reporter.language = "fr"
        self.reporter.save(update_fields=["language"])

        with self.captureOnCommitCallbacks(execute=True):
            created = create_quizzes_from_template(
                quiz_template=self.template,
                users=[self.reporter],
                validate_target_user=lambda _template, _user: None,
                assigned_by=self.owner,
            )

        self.assertEqual(len(created), 1)
        thread = QuizAlertThread.objects.get(quiz=created[0], kind=QuizAlertThread.KIND_ASSIGNMENT)
        self.assertEqual(thread.reporter_id, self.reporter.id)
        self.assertEqual(thread.owner_id, self.owner.id)
        self.assertEqual(thread.reported_language, "fr")
        self.assertIsNone(thread.quizquestion_id)
        self.assertTrue(thread.unread_for(self.reporter))
        self.assertEqual(thread.unread_count_for(self.reporter), 1)
        self.assertFalse(thread.can_user_reply(self.reporter))
        self.assertEqual(thread.question_title, "Nouveau quiz assigne")
        self.assertIn("/quiz/", thread.messages.first().body)
