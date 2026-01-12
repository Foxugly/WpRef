# subject/tests/test_views.py
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from domain.models import Domain
from rest_framework import status
from rest_framework.test import APITestCase
from subject.models import Subject

User = get_user_model()


class SubjectViewSetTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username="admin", password="adminpass", is_staff=True, is_superuser=True
        )
        cls.user = User.objects.create_user(username="user", password="userpass")

        cls.owner = User.objects.create_user(username="owner", password="ownerpass")
        cls.domain = Domain.objects.create(owner=cls.owner, active=True)
        cls.domain.set_current_language("fr")
        cls.domain.name = "Domaine FR"
        cls.domain.description = ""
        cls.domain.save()

        # Subjects de base (avec traductions)
        cls.s1 = Subject.objects.create(domain=cls.domain)
        cls.s1.set_current_language("fr")
        cls.s1.name = "Mathématiques"
        cls.s1.description = "Les maths"
        cls.s1.save()

        cls.s2 = Subject.objects.create(domain=None)
        cls.s2.set_current_language("fr")
        cls.s2.name = "Philosophie"
        cls.s2.description = "Pensée"
        cls.s2.save()

        cls.s3 = Subject.objects.create(domain=cls.domain)
        cls.s3.set_current_language("nl")
        cls.s3.name = "Wiskunde"
        cls.s3.description = "NL desc"
        cls.s3.save()

    # -------------------------
    # helpers
    # -------------------------
    def _list_url(self):
        return reverse("api:subject-api:subject-list")

    def _detail_url(self, subject_or_id):
        subject_id = subject_or_id.id if hasattr(subject_or_id, "id") else int(subject_or_id)
        return reverse("api:subject-api:subject-detail", kwargs={"subject_id": subject_id})

    def _extract_items(self, resp_json):
        # pagination ou pas
        if isinstance(resp_json, dict) and "results" in resp_json:
            return resp_json["results"]
        return resp_json

    # -------------------------
    # permissions: list/retrieve = IsAuthenticated
    # -------------------------
    def test_list_requires_authentication(self):
        r = self.client.get(self._list_url())
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_requires_authentication(self):
        r = self.client.get(self._detail_url(self.s1))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_list(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get(self._list_url())
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_authenticated_user_can_retrieve(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get(self._detail_url(self.s1))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    # -------------------------
    # permissions: create/update/patch/delete = IsAdminUser
    # -------------------------
    def test_create_requires_admin(self):
        payload = {
            "domain": self.domain.id,
            "translations": {"fr": {"name": "Histoire", "description": "Desc"}},
        }

        # non auth
        r = self.client.post(self._list_url(), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        # auth mais pas admin
        self.client.force_authenticate(user=self.user)
        r = self.client.post(self._list_url(), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_requires_admin(self):
        payload = {"domain": None, "translations": {"fr": {"name": "X", "description": ""}}}

        r = self.client.put(self._detail_url(self.s1), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)
        r = self.client.put(self._detail_url(self.s1), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_requires_admin(self):
        payload = {"translations": {"fr": {"name": "Y", "description": ""}}}

        r = self.client.patch(self._detail_url(self.s1), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)
        r = self.client.patch(self._detail_url(self.s1), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_requires_admin(self):
        r = self.client.delete(self._detail_url(self.s1))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)
        r = self.client.delete(self._detail_url(self.s1))
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    # -------------------------
    # list behavior: search, pagination/no pagination
    # -------------------------
    def test_list_returns_subjects_for_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get(self._list_url())
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        items = self._extract_items(r.json())
        # on a au moins ceux créés
        ids = {it["id"] for it in items}
        self.assertTrue(self.s1.id in ids)
        self.assertTrue(self.s2.id in ids)
        self.assertTrue(self.s3.id in ids)

    def test_list_search_filters_on_translations_name_icontains(self):
        self.client.force_authenticate(user=self.user)

        r = self.client.get(self._list_url(), {"search": "math"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        items = self._extract_items(r.json())
        self.assertTrue(any(it["id"] == self.s1.id for it in items))
        # idéalement, ne contient pas philo
        self.assertFalse(any(it["id"] == self.s2.id for it in items))

    def test_list_search_distinct_avoids_duplicates(self):
        """
        distinct() est appelé -> pas de doublons même si plusieurs traductions match.
        On crée un sujet avec 2 langues qui matchent "bio".
        """
        s = Subject.objects.create(domain=None)
        s.set_current_language("fr")
        s.name = "Bio"
        s.description = ""
        s.save()
        s.set_current_language("nl")
        s.name = "Bio"
        s.description = ""
        s.save()

        self.client.force_authenticate(user=self.user)
        r = self.client.get(self._list_url(), {"search": "bio"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        items = self._extract_items(r.json())

        hits = [it for it in items if it["id"] == s.id]
        self.assertEqual(len(hits), 1)

    # -------------------------
    # retrieve behavior: 200 / 404
    # -------------------------
    def test_retrieve_returns_404_for_missing(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get(self._detail_url(999999))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------
    # create behavior (admin): 201 + object created
    # -------------------------
    def test_admin_can_create_subject(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "domain": self.domain.id,
            "translations": {
                "fr": {"name": "Histoire", "description": "Desc histoire"},
                "nl": {"name": "Geschiedenis", "description": ""},
            },
        }

        r = self.client.post(self._list_url(), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        data = r.json()
        self.assertIn("id", data)
        self.assertIn("name", data)  # read serializer
        self.assertIn("description", data)  # read serializer
        self.assertEqual(data["domain"], self.domain.id)

        created = Subject.objects.get(pk=data["id"])
        created.set_current_language("fr")
        self.assertEqual(created.name, "Histoire")

    def test_admin_create_validation_error(self):
        """
        translations requis -> 400
        """
        self.client.force_authenticate(user=self.admin)
        r = self.client.post(self._list_url(), {"domain": self.domain.id}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("translations", r.json())

    # -------------------------
    # update/patch behavior (admin): 200 + read serializer output
    # -------------------------
    def test_admin_can_put_update_subject(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "domain": None,
            "translations": {"fr": {"name": "Maths (maj)", "description": "nouveau"}},
        }

        r = self.client.put(self._detail_url(self.s1), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertEqual(data["id"], self.s1.id)
        self.assertEqual(data["domain"], None)
        self.assertIn("name", data)
        self.assertIn("description", data)

        self.s1.refresh_from_db()
        self.s1.set_current_language("fr")
        self.assertEqual(self.s1.name, "Maths (maj)")
        self.assertEqual(self.s1.description, "nouveau")

    def test_admin_can_patch_subject(self):
        self.client.force_authenticate(user=self.admin)
        payload = {"translations": {"fr": {"name": "Philo (maj)", "description": "d"}}}

        r = self.client.patch(self._detail_url(self.s2), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        self.s2.refresh_from_db()
        self.s2.set_current_language("fr")
        self.assertEqual(self.s2.name, "Philo (maj)")

    def test_admin_update_404(self):
        self.client.force_authenticate(user=self.admin)
        payload = {"domain": None, "translations": {"fr": {"name": "X", "description": ""}}}
        r = self.client.put(self._detail_url(999999), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------
    # destroy behavior (admin)
    # -------------------------
    def test_admin_can_delete_subject(self):
        self.client.force_authenticate(user=self.admin)

        s = Subject.objects.create(domain=None)
        s.set_current_language("fr")
        s.name = "Temp"
        s.description = ""
        s.save()

        r = self.client.delete(self._detail_url(s))
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Subject.objects.filter(pk=s.pk).exists())

    def test_admin_delete_404(self):
        self.client.force_authenticate(user=self.admin)
        r = self.client.delete(self._detail_url(999999))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------
    # cover get_queryset() retrieve branch: prefetch_related is called
    # -------------------------
    def test_retrieve_uses_prefetch_related_branch(self):
        """
        On ne veut pas tester 'questions__...' réellement (ça dépend de tes relations),
        mais au moins couvrir la branche action=='retrieve' sans crash.
        """
        self.client.force_authenticate(user=self.user)
        r = self.client.get(self._detail_url(self.s1))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    # -------------------------
    # cover that _log_call() is invoked in list/create/update/patch/destroy
    # -------------------------
    def test_log_call_is_invoked_on_list(self):
        self.client.force_authenticate(user=self.user)
        # patch sur la classe, car MyModelViewSet fournit _log_call
        with patch("subject.views.SubjectViewSet._log_call") as mocked:
            r = self.client.get(self._list_url())
            self.assertEqual(r.status_code, status.HTTP_200_OK)
            mocked.assert_called()

    def test_log_call_is_invoked_on_create(self):
        self.client.force_authenticate(user=self.admin)
        payload = {"domain": None, "translations": {"fr": {"name": "Créé", "description": ""}}}

        with patch("subject.views.SubjectViewSet._log_call") as mocked:
            r = self.client.post(self._list_url(), payload, format="json")
            self.assertEqual(r.status_code, status.HTTP_201_CREATED)
            mocked.assert_called()

    def test_log_call_is_invoked_on_update_patch_destroy(self):
        self.client.force_authenticate(user=self.admin)

        s = Subject.objects.create(domain=None)
        s.set_current_language("fr")
        s.name = "Loggable"
        s.description = ""
        s.save()

        with patch("subject.views.SubjectViewSet._log_call") as mocked_update:
            r = self.client.put(
                self._detail_url(s),
                {"domain": None, "translations": {"fr": {"name": "Loggable2", "description": ""}}},
                format="json",
            )
            self.assertEqual(r.status_code, status.HTTP_200_OK)
            mocked_update.assert_called()

        with patch("subject.views.SubjectViewSet._log_call") as mocked_patch:
            r = self.client.patch(
                self._detail_url(s),
                {"translations": {"fr": {"name": "Loggable3", "description": ""}}},
                format="json",
            )
            self.assertEqual(r.status_code, status.HTTP_200_OK)
            mocked_patch.assert_called()

        with patch("subject.views.SubjectViewSet._log_call") as mocked_destroy:
            r = self.client.delete(self._detail_url(s))
            self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
            mocked_destroy.assert_called()
