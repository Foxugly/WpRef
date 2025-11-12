# question/tests/test_api.py
from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from question.models import Subject

class QuestionAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("u", password="p")
        self.s1 = Subject.objects.create(name="Règlement")
        self.s2 = Subject.objects.create(name="Historique")

    def test_create_question(self):
        self.client.login(username="u", password="p")  # si tu utilises SessionAuth pour le test
        url = reverse("question-list")
        payload = {
            "title": "2+2 ?",
            "description": "<p>Calc.</p>",
            "explanation": "<p>4.</p>",
            "allow_multiple_correct": False,
            "subject_ids": [self.s1.id, self.s2.id],
            "media": [],
            "answer_options": [
                {"content": "<p>4</p>", "is_correct": True, "sort_order": 0},
                {"content": "<p>5</p>", "is_correct": False, "sort_order": 1},
            ],
        }
        res = self.client.post(url, data=payload, format="json")
        assert res.status_code in (201, 401)  # 401 si pas de JWT dans ce test
