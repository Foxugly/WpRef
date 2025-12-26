from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from subject.models import Subject

User = get_user_model()


class SubjectAPITestCase(APITestCase):
    """
    Tests API SubjectViewSet:
      - list/retrieve: IsAuthenticated
      - create/update/partial_update/destroy: IsAdminUser
      - search + DjangoFilterBackend (name)
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="adminpass", is_staff=True, is_superuser=True
        )
        self.u1 = User.objects.create_user(username="u1", password="u1pass")

        self.list_url = reverse("api:subject-api:subject-list")

        self.s1 = Subject.objects.create(name="Mathématiques", description="desc")
        self.s2 = Subject.objects.create(name="Histoire", description="desc")
        self.s3 = Subject.objects.create(name="Physique", description="desc")

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def _detail_url(self, subject_id: int) -> str:
        return reverse("api:subject-api:subject-detail", kwargs={"subject_id": subject_id})

    # ------------------------------------------------------------
    # LIST (IsAuthenticated)
    # ------------------------------------------------------------
    def test_list_requires_auth(self):
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_authenticated_ok(self):
        self._auth(self.u1)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.data
        ids = [item["id"] for item in data]
        self.assertIn(self.s1.id, ids)

    def test_list_search_filters_name_icontains(self):
        self._auth(self.u1)
        res = self.client.get(self.list_url + "?search=hist")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.data
        names = [item["name"] for item in data]

        self.assertIn("Histoire", names)
        self.assertNotIn("Mathématiques", names)


    def test_list_filter_by_name_exact(self):
        self._auth(self.u1)

        res = self.client.get(self.list_url + "?name=Physique")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.s3.id)

    # ------------------------------------------------------------
    # RETRIEVE (IsAuthenticated)
    # ------------------------------------------------------------
    def test_retrieve_requires_auth(self):
        url = self._detail_url(self.s1.id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_authenticated_ok(self):
        self._auth(self.u1)
        url = self._detail_url(self.s1.id)

        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data["id"], self.s1.id)
        self.assertEqual(res.data["name"], self.s1.name)
        self.assertEqual(res.data["slug"], self.s1.slug)

    def test_retrieve_404(self):
        self._auth(self.u1)
        url = self._detail_url(999999)

        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------
    # CREATE (IsAdminUser)
    # ------------------------------------------------------------
    def test_create_requires_admin(self):
        self._auth(self.u1)
        res = self.client.post(self.list_url, {"name": "Bio"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_admin_ok_and_slug_generated(self):
        self._auth(self.admin)

        payload = {"name": "Biologie", "description": "desc"}
        res = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        sid = res.data["id"]
        s = Subject.objects.get(pk=sid)

        self.assertEqual(s.name, "Biologie")
        self.assertTrue(s.slug)  # auto slug
        self.assertEqual(res.data["slug"], s.slug)

    def test_create_admin_duplicate_name_returns_400(self):
        self._auth(self.admin)

        # name unique=True => DRF doit renvoyer 400
        res = self.client.post(self.list_url, {"name": "Histoire"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------
    # UPDATE / PATCH (IsAdminUser)
    # ------------------------------------------------------------
    def test_update_requires_admin(self):
        self._auth(self.u1)
        url = self._detail_url(self.s1.id)
        res = self.client.put(url, {"name": "Nouveau", "slug": self.s1.slug, "description": ""}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_admin_ok(self):
        self._auth(self.admin)
        url = self._detail_url(self.s1.id)

        payload = {
            "name": "Maths",
            "slug": self.s1.slug,  # ton serializer autorise slug en write
            "description": "new",
        }
        res = self.client.put(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.s1.refresh_from_db()
        self.assertEqual(self.s1.name, "Maths")
        self.assertEqual(self.s1.description, "new")

    def test_patch_admin_ok(self):
        self._auth(self.admin)
        url = self._detail_url(self.s2.id)

        res = self.client.patch(url, {"description": "updated"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.s2.refresh_from_db()
        self.assertEqual(self.s2.description, "updated")

    # ------------------------------------------------------------
    # DELETE (IsAdminUser)
    # ------------------------------------------------------------
    def test_delete_requires_admin(self):
        self._auth(self.u1)
        url = self._detail_url(self.s3.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_admin_ok(self):
        self._auth(self.admin)
        url = self._detail_url(self.s3.id)

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Subject.objects.filter(pk=self.s3.id).exists())
