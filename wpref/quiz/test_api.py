# quiz/tests/test_api.py

from rest_framework.test import APITestCase
from django.urls import reverse
from customuser.models import CustomUser
from question.models import Question
from quiz.models import Quiz, QuizQuestion


class QuizApiTests(APITestCase):
    def setUp(self):
        # user
        self.user = CustomUser.objects.create_user(
            username="player",
            email="player@example.com",
            password="Pass1234",
        )
        # quiz + question
        self.quiz = Quiz.objects.create(title="Quiz Scrum", max_questions=1)
        self.q1 = Question.objects.create(
            title="Combien de rôles en Scrum ?",
            description="QCM",
        )
        QuizQuestion.objects.create(quiz=self.quiz, question=self.q1, sort_order=1)

    def test_full_quiz_flow(self):
        # 1) start quiz
        url_start = reverse("api:quiz:quiz-start", kwargs={"slug": self.quiz.slug})
        self.client.force_authenticate(self.user)
        resp_start = self.client.post(url_start, format="json")
        self.assertEqual(resp_start.status_code, 201)
        quiz_id = resp_start.data["id"]

        # 2) answer question 1
        url_attempt = reverse(
            "api:quiz:quiz-attempt",
            kwargs={"quiz_id": quiz_id, "question_order": 1},
        )
        resp_attempt = self.client.post(
            url_attempt,
            {"given_answer": "A"},
            format="json",
        )
        self.assertEqual(resp_attempt.status_code, 200)
        self.assertEqual(resp_attempt.data["question_order"], 1)
        self.assertEqual(resp_attempt.data["given_answer"], "A")

        # 3) summary
        url_summary = reverse(
            "api:quiz:quiz-summary",
            kwargs={"quiz_id": quiz_id},
        )
        resp_summary = self.client.get(url_summary)
        self.assertEqual(resp_summary.status_code, 200)
        self.assertEqual(resp_summary.data["total_questions"], 1)
        self.assertEqual(resp_summary.data["answered_questions"], 1)
