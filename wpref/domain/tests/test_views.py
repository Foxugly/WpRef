from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from domain.models import Domain
from domain.views import DomainViewSet
from language.models import Language
from subject.models import Subject

User = get_user_model()


def _get_results(data):
    """
    Helper: DRF peut renvoyer une liste (pas de pagination)
    ou un dict paginé {"count":..., "results":[...]}.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data


class DomainViewSetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()

        # Users
        cls.owner = User.objects.create_user(username="owner", password="pwd")
        cls.other = User.objects.create_user(username="other", password="pwd")
        cls.global_staff = User.objects.create_user(username="staff", password="pwd", is_staff=True)

        # Languages
        cls.lang_fr = Language.objects.create(code="fr", name="Français", active=True)
        cls.lang_en = Language.objects.create(code="en", name="English", active=True)

        # Domains
        cls.domain_active = Domain.objects.create(owner=cls.owner, active=True)
        cls.domain_active.allowed_languages.set([cls.lang_fr, cls.lang_en])
        cls.domain_active.staff.add(cls.other)
        cls.domain_active.set_current_language("fr")
        cls.domain_active.name = "Domaine Actif"
        cls.domain_active.description = "desc"
        cls.domain_active.save()

        cls.domain_inactive = Domain.objects.create(owner=cls.owner, active=False)
        cls.domain_inactive.allowed_languages.set([cls.lang_fr])
        cls.domain_inactive.set_current_language("fr")
        cls.domain_inactive.name = "Domaine Inactif"
        cls.domain_inactive.save()

        cls.domain_other_active = Domain.objects.create(owner=cls.other, active=True)
        cls.domain_other_active.allowed_languages.set([cls.lang_fr])
        cls.domain_other_active.set_current_language("fr")
        cls.domain_other_active.name = "Autre Domaine"
        cls.domain_other_active.save()

        # Subjects for details()
        cls.subject_active = Subject.objects.create(domain=cls.domain_active, active=True)
        cls.subject_active.set_current_language("fr")
        cls.subject_active.name = "Sujet Actif"
        cls.subject_active.description = ""
        cls.subject_active.save()

        cls.subject_inactive = Subject.objects.create(domain=cls.domain_active, active=False)
        cls.subject_inactive.set_current_language("fr")
        cls.subject_inactive.name = "Sujet Inactif"
        cls.subject_inactive.save()

    # ----------------------------
    # LIST
    # ----------------------------
    def test_list_anonymous_returns_only_active_domains(self):
        view = DomainViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/domain/")
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = _get_results(response.data)
        ids = {item["id"] for item in results}

        # anonyme => active=True uniquement, mais pas filtré sur owner/staff
        self.assertIn(self.domain_active.id, ids)
        self.assertIn(self.domain_other_active.id, ids)
        self.assertNotIn(self.domain_inactive.id, ids)

    def test_list_authenticated_user_returns_only_owned_or_staff(self):
        view = DomainViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/domain/")
        force_authenticate(request, user=self.owner)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = _get_results(response.data)
        ids = {item["id"] for item in results}

        # owner voit ses domaines (actif + inactif), mais pas l'autre domaine (où il n'est pas staff)
        self.assertIn(self.domain_active.id, ids)
        self.assertIn(self.domain_inactive.id, ids)
        self.assertNotIn(self.domain_other_active.id, ids)

    def test_list_global_staff_sees_all(self):
        view = DomainViewSet.as_view({"get": "list"})
        request = self.factory.get("/api/domain/")
        force_authenticate(request, user=self.global_staff)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = _get_results(response.data)
        ids = {item["id"] for item in results}

        self.assertIn(self.domain_active.id, ids)
        self.assertIn(self.domain_inactive.id, ids)
        self.assertIn(self.domain_other_active.id, ids)

    # ----------------------------
    # RETRIEVE
    # ----------------------------
    def test_retrieve_anonymous_active_ok(self):
        view = DomainViewSet.as_view({"get": "retrieve"})
        request = self.factory.get(f"/api/domain/{self.domain_active.id}/")
        response = view(request, domain_id=self.domain_active.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.domain_active.id)

    def test_retrieve_anonymous_inactive_404(self):
        view = DomainViewSet.as_view({"get": "retrieve"})
        request = self.factory.get(f"/api/domain/{self.domain_inactive.id}/")
        response = view(request, domain_id=self.domain_inactive.id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------
    # DETAILS (custom action)
    # ----------------------------
    def test_details_anonymous_active_ok_and_subjects_filtered(self):
        view = DomainViewSet.as_view({"get": "details"})
        request = self.factory.get(f"/api/domain/{self.domain_active.id}/details/")
        response = view(request, domain_id=self.domain_active.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.domain_active.id)
        self.assertIn("subjects", response.data)

        subjects = response.data["subjects"]
        subject_ids = {s["id"] for s in subjects}
        self.assertIn(self.subject_active.id, subject_ids)
        self.assertNotIn(self.subject_inactive.id, subject_ids)

    def test_details_anonymous_inactive_404(self):
        view = DomainViewSet.as_view({"get": "details"})
        request = self.factory.get(f"/api/domain/{self.domain_inactive.id}/details/")
        response = view(request, domain_id=self.domain_inactive.id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------
    # CREATE
    # ----------------------------
    def test_create_requires_authentication(self):
        view = DomainViewSet.as_view({"post": "create"})
        payload = {
            "translations": {"fr": {"name": "Nouveau", "description": ""}},
            "allowed_languages": [self.lang_fr.id],
            "active": True,
            "staff": [self.other.id],
        }
        request = self.factory.post("/api/domain/", payload, format="json")
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_authenticated_ok_and_adds_owner_to_staff(self):
        view = DomainViewSet.as_view({"post": "create"})
        payload = {
            "translations": {"fr": {"name": "Nouveau", "description": "X"}},
            "allowed_languages": [self.lang_fr.id],
            "active": True,
            "staff": [self.other.id],  # volontairement sans owner
        }
        request = self.factory.post("/api/domain/", payload, format="json")
        force_authenticate(request, user=self.owner)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_id = response.data["id"]

        domain = Domain.objects.get(pk=created_id)
        self.assertEqual(domain.owner_id, self.owner.id)

        staff_ids = set(domain.staff.values_list("id", flat=True))
        self.assertIn(self.owner.id, staff_ids)  # ajouté par perform_create()
        self.assertIn(self.other.id, staff_ids)

        allowed_ids = set(domain.allowed_languages.values_list("id", flat=True))
        self.assertEqual(allowed_ids, {self.lang_fr.id})

        # translations appliquées
        domain.set_current_language("fr")
        self.assertEqual(domain.name, "Nouveau")
        self.assertEqual(domain.description, "X")

    # ----------------------------
    # UPDATE (PUT)
    # ----------------------------
    def test_update_put_owner_ok(self):
        view = DomainViewSet.as_view({"put": "update"})
        payload = {
            "translations": {"fr": {"name": "Modifié", "description": "ZZ"}},
            "allowed_languages": [self.lang_fr.id],
            "active": False,
            "staff": [self.other.id],
        }
        request = self.factory.put(f"/api/domain/{self.domain_active.id}/", payload, format="json")
        force_authenticate(request, user=self.owner)
        response = view(request, domain_id=self.domain_active.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.domain_active.refresh_from_db()
        self.domain_active.set_current_language("fr")
        self.assertEqual(self.domain_active.name, "Modifié")
        self.assertFalse(self.domain_active.active)

    # ----------------------------
    # PARTIAL UPDATE (PATCH)
    # ----------------------------
    def test_partial_update_patch_active_only_owner_ok(self):
        view = DomainViewSet.as_view({"patch": "partial_update"})
        payload = {"active": True}
        request = self.factory.patch(f"/api/domain/{self.domain_inactive.id}/", payload, format="json")
        force_authenticate(request, user=self.owner)
        response = view(request, domain_id=self.domain_inactive.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.domain_inactive.refresh_from_db()
        self.assertTrue(self.domain_inactive.active)

    # ----------------------------
    # DESTROY
    # ----------------------------
    def test_destroy_owner_ok(self):
        view = DomainViewSet.as_view({"delete": "destroy"})
        domain = Domain.objects.create(owner=self.owner, active=True)
        domain.set_current_language("fr")
        domain.name = "A supprimer"
        domain.save()

        request = self.factory.delete(f"/api/domain/{domain.id}/")
        force_authenticate(request, user=self.owner)
        response = view(request, domain_id=domain.id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Domain.objects.filter(pk=domain.id).exists())
