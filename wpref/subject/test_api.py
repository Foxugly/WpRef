# question/tests/test_subject_api.py

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Subject


class SubjectAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()

        # utilisateur "simple"
        cls.user = user_model.objects.create_user(
            username="user",
            email="user@example.com",
            password="password123",
        )

        # utilisateur staff/admin
        cls.admin = user_model.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="password123",
            is_staff=True,
        )

    def setUp(self):
        # Par défaut, on se connecte comme utilisateur "simple"
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse("api:subject_api:subject-list")

    # --- AUTH / PERMISSIONS ---

    def test_unauthenticated_user_cannot_access_anything(self):
        """
        Utilisateur non authentifié : pas d'accès, même pas en GET.
        """
        self.client.force_authenticate(user=None)

        # liste
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # on crée un subject pour tester le detail
        s = Subject.objects.create(name="Test", description="desc")
        detail_url = reverse("api:subject_api:subject-detail", args=[s.pk])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_simple_user_can_list_and_retrieve_but_not_modify(self):
        """
        Utilisateur authentifié non admin :
        - peut GET liste + detail
        - ne peut pas POST/PUT/PATCH/DELETE
        """
        # création d'un Subject (par admin, directement en DB)
        subject = Subject.objects.create(name="Test subject", description="desc")

        # GET liste
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # GET detail
        detail_url = reverse("api:subject_api:subject-detail", args=[subject.pk])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST (create) → refus
        payload = {"name": "New subject", "description": "new"}
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # PUT (update) → refus
        payload = {"name": "Updated", "description": "updated"}
        response = self.client.put(detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # PATCH (partial update) → refus
        payload = {"description": "patched"}
        response = self.client.patch(detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # DELETE → refus
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_crud_subject(self):
        """
        Utilisateur staff/admin :
        - peut créer, modifier, supprimer.
        """
        # on se connecte comme admin
        self.client.force_authenticate(user=self.admin)

        # CREATE
        payload = {"name": "Admin subject", "description": "created by admin"}
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Subject.objects.count(), 1)
        subject_id = response.data["id"]

        subject = Subject.objects.get(id=subject_id)
        self.assertEqual(subject.slug, "admin-subject")  # slug auto

        # UPDATE (PUT)
        detail_url = reverse("api:subject_api:subject-detail", args=[subject_id])
        payload = {"name": "Updated admin subject", "description": "new desc"}
        response = self.client.put(detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.name, "Updated admin subject")

        # PARTIAL UPDATE (PATCH)
        payload = {"description": "patched desc"}
        response = self.client.patch(detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.description, "patched desc")

        # DELETE
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Subject.objects.count(), 0)

    # --- COMPORTEMENT FONCTIONNEL SUBJECT ---

    def test_create_subject_as_admin_sets_slug(self):
        """
        Vérifie la logique de slug auto lors de la création (admin).
        """
        self.client.force_authenticate(user=self.admin)
        payload = {
            "name": "Scrum Basics",
            "description": "Intro to Scrum",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        subject = Subject.objects.get(id=response.data["id"])
        self.assertEqual(subject.slug, "scrum-basics")

    def test_name_unique_enforced(self):
        """
        Deux Subjects avec le même name doivent être refusés (admin).
        """
        self.client.force_authenticate(user=self.admin)
        Subject.objects.create(name="Unique Name", description="First")

        payload = {"name": "Unique Name", "description": "Second"}
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Subject.objects.count(), 1)

    def test_filter_by_slug_as_simple_user(self):
        """
        Un simple user peut filtrer par slug.
        """
        s1 = Subject.objects.create(name="Filter Me", description="desc")
        Subject.objects.create(name="Other", description="desc")

        response = self.client.get(self.list_url, {"slug": s1.slug})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["slug"], s1.slug)

    def test_filter_by_name_as_simple_user(self):
        s1 = Subject.objects.create(name="Exact Match", description="desc")
        Subject.objects.create(name="Other name", description="desc")

        response = self.client.get(self.list_url, {"name": "Exact Match"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], s1.name)

    def test_filter_by_id_as_simple_user(self):
        s1 = Subject.objects.create(name="By id", description="desc")
        Subject.objects.create(name="Other", description="desc")

        response = self.client.get(self.list_url, {"id": s1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], s1.id)
