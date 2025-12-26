from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from domain.models import Domain

User = get_user_model()


class DomainViewSetTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.staff_member = User.objects.create_user(username="staff_member", password="pass")
        self.other = User.objects.create_user(username="other", password="pass")

        self.global_staff = User.objects.create_user(username="global_staff", password="pass", is_staff=True)
        self.superuser = User.objects.create_superuser(username="admin", password="pass", email="admin@example.com")

        self.d1 = Domain.objects.create(name="Water-polo", owner=self.owner, allowed_languages=["fr"], active=True)
        self.d1.staff.add(self.staff_member)

        self.d2 = Domain.objects.create(name="Football", owner=self.other, allowed_languages=["fr"], active=True)

        self.list_url = reverse("api:domain-api:domain-list")
        self.detail_url = lambda pk: reverse("api:domain-api:domain-detail", kwargs={"domain_id": pk})

    def test_list_requires_auth(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_as_owner_sees_only_owned_or_staff(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        ids = {row["id"] for row in resp.data}
        self.assertIn(self.d1.id, ids)
        self.assertNotIn(self.d2.id, ids)

    def test_list_as_domain_staff_sees_domain(self):
        self.client.force_authenticate(self.staff_member)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        ids = {row["id"] for row in resp.data}
        self.assertIn(self.d1.id, ids)
        self.assertNotIn(self.d2.id, ids)

    def test_list_as_global_staff_sees_all(self):
        self.client.force_authenticate(self.global_staff)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        ids = {row["id"] for row in resp.data}
        self.assertIn(self.d1.id, ids)
        self.assertIn(self.d2.id, ids)

    def test_retrieve_forbidden_domain_returns_404_due_to_queryset_filter(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.get(self.detail_url(self.d2.id))
        # Comme get_queryset filtre, DRF ne trouve pas l'objet => 404
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_sets_owner_and_adds_owner_to_staff(self):
        self.client.force_authenticate(self.other)

        payload = {
            "name": "Basket",
            "description": "desc",
            "allowed_languages": ["fr"],
            "active": True,
            "staff_ids": [self.staff_member.id],
            # même si on tente owner, il doit être ignoré / overridden
            "owner": self.owner.id,
        }
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

        domain_id = resp.data["id"]
        d = Domain.objects.get(id=domain_id)

        # owner doit être le user courant (self.other)
        self.assertEqual(d.owner_id, self.other.id)

        # owner ajouté au staff (perform_create)
        self.assertTrue(d.staff.filter(id=self.other.id).exists())

        # staff_ids inclus aussi
        self.assertTrue(d.staff.filter(id=self.staff_member.id).exists())

    def test_update_allowed_for_owner(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.patch(self.detail_url(self.d1.id), {"description": "new"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.d1.refresh_from_db()
        self.assertEqual(self.d1.description, "new")

    def test_update_allowed_for_domain_staff(self):
        self.client.force_authenticate(self.staff_member)
        resp = self.client.patch(self.detail_url(self.d1.id), {"description": "staff edit"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.d1.refresh_from_db()
        self.assertEqual(self.d1.description, "staff edit")

    def test_update_denied_for_unrelated_user(self):
        self.client.force_authenticate(self.other)
        resp = self.client.patch(self.detail_url(self.d1.id), {"description": "hack"}, format="json")
        # filtré par queryset => 404
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_cannot_be_changed(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.patch(self.detail_url(self.d1.id), {"owner": self.other.id}, format="json")
        self.assertEqual(resp.status_code, 200)

        self.d1.refresh_from_db()
        self.assertEqual(self.d1.owner_id, self.owner.id)

    def test_delete_allowed_for_owner(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.delete(self.detail_url(self.d1.id))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Domain.objects.filter(id=self.d1.id).exists())
