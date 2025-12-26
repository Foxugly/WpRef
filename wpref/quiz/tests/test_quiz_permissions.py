from django.contrib.auth import get_user_model
from django.urls import reverse
from quiz.models import Quiz, QuizTemplate
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class QuizPermissionsTest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin", "a@a.com", "pass", is_staff=True, is_superuser=True)
        self.u1 = User.objects.create_user("u1", "u1@u1.com", "pass")
        self.u2 = User.objects.create_user("u2", "u2@u2.com", "pass")

        self.qt = QuizTemplate.objects.create(title="T1", permanent=True, active=True)
        self.quiz_u1 = Quiz.objects.create(quiz_template=self.qt, user=self.u1, active=False)

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_start_owner_ok(self):
        self._auth(self.u1)
        url = reverse("api:quiz-api:quiz-start", kwargs={"quiz_id": self.quiz_u1.id})
        res = self.client.post(url, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_start_other_user_forbidden_or_404(self):
        self._auth(self.u2)
        url = reverse("api:quiz-api:quiz-start", kwargs={"quiz_id": self.quiz_u1.id})
        res = self.client.post(url, format="json")

        # Selon ton design: soit 404 (caché via queryset filtré) soit 403 (permission explicite)
        self.assertIn(res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_start_admin_ok(self):
        self._auth(self.admin)
        url = reverse("api:quiz-api:quiz-start", kwargs={"quiz_id": self.quiz_u1.id})
        res = self.client.post(url, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
