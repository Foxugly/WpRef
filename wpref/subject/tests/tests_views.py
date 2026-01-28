# subject/tests/test_views.py
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import translation
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from domain.models import Domain
from question.models import Question, QuestionSubject
from subject.models import Subject
from subject.views import SubjectViewSet

User = get_user_model()


class SubjectViewSetTestCase(TestCase):
    """
    Couvre le fichier views.py de SubjectViewSet :
    - permissions (IsAuthenticated vs IsAdminUser)
    - list avec filters + search + pagination (si activée)
    - retrieve
    - details (action)
    - create / update / partial_update / destroy
    """

    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()

        cls.user = User.objects.create_user(username="u1", password="pwd")
        cls.admin = User.objects.create_user(username="admin", password="pwd", is_staff=True)

        # Domain (parler): créer puis poser une traduction si tu veux tester domain_name
        cls.domain = Domain.objects.create(owner=cls.admin, active=True)
        cls.domain.set_current_language("fr")
        cls.domain.name = "Domaine FR"
        cls.domain.description = ""
        cls.domain.save()

        # Subjects
        cls.subj1 = Subject.objects.create(domain=cls.domain, active=True)
        cls.subj1.set_current_language("fr")
        cls.subj1.name = "Math"
        cls.subj1.description = "Desc"
        cls.subj1.save()

        cls.subj2 = Subject.objects.create(domain=cls.domain, active=False)
        cls.subj2.set_current_language("fr")
        cls.subj2.name = "Physique"
        cls.subj2.description = ""
        cls.subj2.save()

        # Questions (pour details)
        cls.q1 = Question.objects.create(domain=cls.domain, active=True)
        cls.q1.set_current_language("fr")
        cls.q1.title = "Question 1"
        cls.q1.description = ""
        cls.q1.explanation = ""
        cls.q1.save()

        cls.q2 = Question.objects.create(domain=cls.domain, active=False)  # inactive => doit être filtrée
        cls.q2.set_current_language("fr")
        cls.q2.title = "Question 2"
        cls.q2.description = ""
        cls.q2.explanation = ""
        cls.q2.save()

        QuestionSubject.objects.create(question=cls.q1, subject=cls.subj1, sort_order=0)
        QuestionSubject.objects.create(question=cls.q2, subject=cls.subj1, sort_order=1)

    def setUp(self):
        translation.activate("fr")

    def tearDown(self):
        translation.deactivate_all()

    # ----------------------------
    # helpers
    # ----------------------------
    def _call(self, method: str, action: str, user=None, *, path="/api/subject/", data=None, query=None, subject_id=None):
        view = SubjectViewSet.as_view({method: action})

        if query:
            qs = "&".join([f"{k}={v}" for k, v in query.items()])
            path = f"{path}?{qs}"

        req = getattr(self.factory, method)(path, data=data or {}, format="json")
        if user is not None:
            force_authenticate(req, user=user)

        kwargs = {}
        if subject_id is not None:
            kwargs["subject_id"] = subject_id

        return view(req, **kwargs)

    def _extract_results(self, resp):
        """
        Si pagination activée => resp.data["results"]
        Sinon => resp.data directement (liste)
        """
        data = resp.data
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        return data

    # ----------------------------
    # permissions
    # ----------------------------
    def test_list_requires_authentication(self):
        resp = self._call("get", "list", user=None)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_requires_authentication(self):
        resp = self._call("get", "retrieve", user=None, subject_id=self.subj1.pk, path=f"/api/subject/{self.subj1.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_details_requires_authentication(self):
        resp = self._call("get", "details", user=None, subject_id=self.subj1.pk, path=f"/api/subject/{self.subj1.pk}/details/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_requires_admin(self):
        payload = {"domain": self.domain.pk, "active": True, "translations": {"fr": {"name": "Bio", "description": ""}}}
        resp = self._call("post", "create", user=self.user, data=payload)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_requires_admin(self):
        payload = {"domain": self.domain.pk, "active": True, "translations": {"fr": {"name": "Math2", "description": ""}}}
        resp = self._call("put", "update", user=self.user, subject_id=self.subj1.pk, path=f"/api/subject/{self.subj1.pk}/", data=payload)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_requires_admin(self):
        resp = self._call("delete", "destroy", user=self.user, subject_id=self.subj1.pk, path=f"/api/subject/{self.subj1.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ----------------------------
    # list
    # ----------------------------
    def test_list_returns_items(self):
        resp = self._call("get", "list", user=self.user)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        items = self._extract_results(resp)
        self.assertTrue(isinstance(items, list))
        self.assertGreaterEqual(len(items), 2)

    def test_list_filter_active(self):
        resp = self._call("get", "list", user=self.user, query={"active": "true"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        items = self._extract_results(resp)
        ids = {it["id"] for it in items}
        self.assertIn(self.subj1.pk, ids)
        self.assertNotIn(self.subj2.pk, ids)

    def test_list_filter_domain(self):
        resp = self._call("get", "list", user=self.user, query={"domain": str(self.domain.pk)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        items = self._extract_results(resp)
        self.assertTrue(all(it["domain"] == self.domain.pk for it in items))

    def test_list_search_on_translated_name(self):
        resp = self._call("get", "list", user=self.user, query={"search": "ath"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        items = self._extract_results(resp)
        ids = {it["id"] for it in items}
        self.assertIn(self.subj1.pk, ids)

    # ----------------------------
    # retrieve
    # ----------------------------
    def test_retrieve_returns_read_serializer_shape(self):
        resp = self._call("get", "retrieve", user=self.user, subject_id=self.subj1.pk, path=f"/api/subject/{self.subj1.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("id", resp.data)
        self.assertIn("domain", resp.data)
        self.assertIn("active", resp.data)
        self.assertIn("translations", resp.data)
        self.assertIn("fr", resp.data["translations"])

    # ----------------------------
    # details
    # ----------------------------
    def test_details_returns_questions_only_active(self):
        resp = self._call("get", "details", user=self.user, subject_id=self.subj1.pk, path=f"/api/subject/{self.subj1.pk}/details/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("questions", resp.data)
        q_ids = {q["id"] for q in resp.data["questions"]}
        self.assertIn(self.q1.pk, q_ids)
        self.assertNotIn(self.q2.pk, q_ids)  # inactive filtered

    # ----------------------------
    # create / update / patch / delete (admin)
    # ----------------------------
    def test_create_as_admin(self):
        payload = {"domain": self.domain.pk, "active": True, "translations": {"fr": {"name": "Bio", "description": ""}}}
        resp = self._call("post", "create", user=self.admin, data=payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["domain"], self.domain.pk)
        self.assertTrue(resp.data["active"])
        self.assertIn("fr", resp.data["translations"])
        self.assertEqual(resp.data["translations"]["fr"]["name"], "Bio")

    def test_update_as_admin_returns_read_serializer(self):
        payload = {"domain": self.domain.pk, "active": False, "translations": {"fr": {"name": "Math v2", "description": "x"}}}
        resp = self._call("put", "update", user=self.admin, subject_id=self.subj1.pk, path=f"/api/subject/{self.subj1.pk}/", data=payload)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], self.subj1.pk)
        self.assertFalse(resp.data["active"])
        self.assertEqual(resp.data["translations"]["fr"]["name"], "Math v2")

    def test_partial_update_as_admin(self):
        payload = {"active": True, "translations": {"fr": {"name": "Math v3", "description": ""}}, "domain": self.domain.pk}
        resp = self._call("patch", "partial_update", user=self.admin, subject_id=self.subj2.pk, path=f"/api/subject/{self.subj2.pk}/", data=payload)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], self.subj2.pk)
        self.assertTrue(resp.data["active"])
        self.assertEqual(resp.data["translations"]["fr"]["name"], "Math v3")

    def test_destroy_as_admin(self):
        s = Subject.objects.create(domain=self.domain, active=True)
        s.set_current_language("fr")
        s.name = "Temp"
        s.description = ""
        s.save()

        resp = self._call("delete", "destroy", user=self.admin, subject_id=s.pk, path=f"/api/subject/{s.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Subject.objects.filter(pk=s.pk).exists())
