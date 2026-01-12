# lang/tests/test_views.py
from django.contrib.auth import get_user_model
from django.urls import reverse
from language.models import Language
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class LanguageViewSetTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username="admin",
            password="adminpass",
            is_staff=True,
            is_superuser=True,
        )
        cls.user = User.objects.create_user(
            username="user",
            password="userpass",
            is_staff=False,
            is_superuser=False,
        )

        # données de base
        cls.lang_fr = Language.objects.create(code="fr", name="Français", active=True)
        cls.lang_nl = Language.objects.create(code="nl", name="Nederlands", active=True)
        cls.lang_en = Language.objects.create(code="en", name="English", active=False)

    # -------------------------
    # helpers
    # -------------------------
    def _list_url(self):
        return reverse("api:lang-api:lang-list")

    def _detail_url(self, lang_or_id):
        lang_id = lang_or_id.id if hasattr(lang_or_id, "id") else int(lang_or_id)
        return reverse("api:lang-api:lang-detail", kwargs={"lang_id": lang_id})

    def _extract_items(self, resp_json):
        """
        Supporte réponse paginée ({"results": [...]}) ou non ([...]).
        """
        if isinstance(resp_json, dict) and "results" in resp_json:
            return resp_json["results"]
        return resp_json

    # -------------------------
    # permissions
    # -------------------------
    def test_list_requires_admin(self):
        url = self._list_url()

        # non authentifié
        r = self.client.get(url)
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        # authentifié mais pas admin
        self.client.force_authenticate(user=self.user)
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_requires_admin(self):
        url = self._detail_url(self.lang_fr)

        r = self.client.get(url)
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        self.client.force_authenticate(user=self.user)
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_requires_admin(self):
        url = self._list_url()
        payload = {"code": "de", "name": "Deutsch", "active": True}

        r = self.client.post(url, payload, format="json")
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        self.client.force_authenticate(user=self.user)
        r = self.client.post(url, payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_requires_admin(self):
        url = self._detail_url(self.lang_fr)
        payload = {"code": "fr", "name": "FR", "active": True}

        r = self.client.put(url, payload, format="json")
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        self.client.force_authenticate(user=self.user)
        r = self.client.put(url, payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_requires_admin(self):
        url = self._detail_url(self.lang_fr)

        r = self.client.delete(url)
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        self.client.force_authenticate(user=self.user)
        r = self.client.delete(url)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    # -------------------------
    # list / retrieve
    # -------------------------
    def test_admin_can_list_languages_default_ordering_by_code(self):
        self.client.force_authenticate(user=self.admin)
        r = self.client.get(self._list_url())

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        items = self._extract_items(r.json())
        codes = [it["code"] for it in items]

        # ordering = ["code"] dans le ViewSet + Meta ordering
        self.assertEqual(codes, sorted(codes))

    def test_admin_can_retrieve_language(self):
        self.client.force_authenticate(user=self.admin)
        r = self.client.get(self._detail_url(self.lang_nl))

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertEqual(data["id"], self.lang_nl.id)
        self.assertEqual(data["code"], "nl")
        self.assertEqual(data["name"], "Nederlands")
        self.assertEqual(data["active"], True)

    def test_retrieve_404(self):
        self.client.force_authenticate(user=self.admin)
        r = self.client.get(self._detail_url(999999))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------
    # search / ordering
    # -------------------------
    def test_search_filter_on_code_or_name(self):
        self.client.force_authenticate(user=self.admin)

        # search par code
        r = self.client.get(self._list_url(), {"search": "fr"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        items = self._extract_items(r.json())
        self.assertTrue(any(it["code"] == "fr" for it in items))
        self.assertTrue(all(("fr" in it["code"]) or ("fr" in it["name"].lower()) for it in items))

        # search par name
        r = self.client.get(self._list_url(), {"search": "english"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        items = self._extract_items(r.json())
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["code"], "en")

    def test_ordering_filter(self):
        self.client.force_authenticate(user=self.admin)

        r = self.client.get(self._list_url(), {"ordering": "-name"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        items = self._extract_items(r.json())
        names = [it["name"] for it in items]
        self.assertEqual(names, sorted(names, reverse=True))

    # -------------------------
    # create
    # -------------------------
    def test_admin_can_create_language_and_code_is_normalized(self):
        self.client.force_authenticate(user=self.admin)
        payload = {"code": "  FR-BE  ", "name": "Français (Belgique)", "active": True}

        r = self.client.post(self._list_url(), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        data = r.json()
        self.assertIn("id", data)
        self.assertEqual(data["code"], "fr-be")  # validate_code: strip + lower
        self.assertEqual(data["name"], "Français (Belgique)")
        self.assertEqual(data["active"], True)

        obj = Language.objects.get(id=data["id"])
        self.assertEqual(obj.code, "fr-be")

    def test_create_invalid_code_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        payload = {"code": "x", "name": "Bad", "active": True}

        r = self.client.post(self._list_url(), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", r.json())

    def test_create_unique_code_constraint(self):
        self.client.force_authenticate(user=self.admin)
        payload = {"code": "fr", "name": "Français v2", "active": True}

        r = self.client.post(self._list_url(), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", r.json())

    # -------------------------
    # update / patch
    # -------------------------
    def test_admin_can_put_update_language(self):
        self.client.force_authenticate(user=self.admin)
        url = self._detail_url(self.lang_en)

        payload = {"code": "EN", "name": "English (updated)", "active": True}
        r = self.client.put(url, payload, format="json")

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertEqual(data["id"], self.lang_en.id)
        self.assertEqual(data["code"], "en")  # normalisé
        self.assertEqual(data["name"], "English (updated)")
        self.assertEqual(data["active"], True)

        self.lang_en.refresh_from_db()
        self.assertEqual(self.lang_en.code, "en")
        self.assertEqual(self.lang_en.name, "English (updated)")
        self.assertTrue(self.lang_en.active)

    def test_admin_can_patch_partial_update_language(self):
        self.client.force_authenticate(user=self.admin)
        url = self._detail_url(self.lang_fr)

        r = self.client.patch(url, {"active": False}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.lang_fr.refresh_from_db()
        self.assertFalse(self.lang_fr.active)

    def test_put_missing_required_fields_returns_400(self):
        """
        PUT = update complet -> si tu n'envoies pas code/name/active,
        le serializer (ModelSerializer) doit répondre 400.
        """
        self.client.force_authenticate(user=self.admin)
        url = self._detail_url(self.lang_fr)

        r = self.client.put(url, {"name": "Only name"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------
    # destroy
    # -------------------------
    def test_admin_can_delete_language(self):
        self.client.force_authenticate(user=self.admin)

        lang = Language.objects.create(code="it", name="Italiano", active=True)
        url = self._detail_url(lang)

        r = self.client.delete(url)
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Language.objects.filter(id=lang.id).exists())
