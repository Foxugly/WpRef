from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from language.models import Language
from domain.models import Domain
from domain.views import DomainViewSet


User = get_user_model()


@override_settings(LANGUAGES=(("fr", "Français"), ("nl", "Nederlands"), ("en", "English")))
class DomainViewSetTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.owner = User.objects.create_user(username="owner", password="pass")
        cls.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        cls.superuser = User.objects.create_user(username="admin", password="pass", is_superuser=True)
        cls.user = User.objects.create_user(username="user", password="pass")
        cls.other = User.objects.create_user(username="other", password="pass")

        # Languages (DB)
        cls.lang_fr = Language.objects.create(code="fr", name="Français", active=True)
        cls.lang_nl = Language.objects.create(code="nl", name="Nederlands", active=True)
        cls.lang_en = Language.objects.create(code="en", name="English", active=True)

        # Domains
        cls.d_owned = Domain.objects.create(owner=cls.owner, active=True)
        cls.d_owned.allowed_languages.set([cls.lang_fr, cls.lang_nl])
        cls.d_owned.set_current_language("fr")
        cls.d_owned.name = "Owned FR"
        cls.d_owned.description = ""
        cls.d_owned.save()
        cls.d_owned.staff.add(cls.owner)  # pour coller au comportement create()

        cls.d_staffed = Domain.objects.create(owner=cls.other, active=True)
        cls.d_staffed.allowed_languages.set([cls.lang_fr])
        cls.d_staffed.set_current_language("fr")
        cls.d_staffed.name = "Staffed FR"
        cls.d_staffed.description = ""
        cls.d_staffed.save()
        cls.d_staffed.staff.add(cls.user)

        cls.d_other = Domain.objects.create(owner=cls.other, active=True)
        cls.d_other.allowed_languages.set([cls.lang_fr])
        cls.d_other.set_current_language("fr")
        cls.d_other.name = "Other FR"
        cls.d_other.description = ""
        cls.d_other.save()

    # -------------------------
    # Helpers URL
    # -------------------------
    def _list_url(self):
        return reverse("api:domain-api:list")

    def _detail_url(self, domain_or_id):
        domain_id = domain_or_id.id if hasattr(domain_or_id, "id") else int(domain_or_id)
        return reverse("api:domain-api:domain-detail", kwargs={"domain_id": domain_id})

    def _create_payload(self):
        # translations obligatoire, + allowed_language_codes optionnel
        return {
            "translations": {
                "fr": {"name": "Nouveau FR", "description": "Desc"},
                "nl": {"name": "Nieuw NL", "description": ""},
            },
            "allowed_language_codes": ["fr", "nl"],
            "active": True,
            "staff_ids": [],  # optionnel
        }

    # -------------------------
    # get_serializer_class
    # -------------------------
    def test_get_serializer_class_list_and_retrieve_use_read(self):
        factory = APIRequestFactory()
        req = factory.get("/fake/")
        force_authenticate(req, user=self.user)

        view = DomainViewSet()
        view.request = req

        view.action = "list"
        self.assertEqual(view.get_serializer_class().__name__, "DomainReadSerializer")

        view.action = "retrieve"
        self.assertEqual(view.get_serializer_class().__name__, "DomainReadSerializer")

    def test_get_serializer_class_create_update_use_write(self):
        factory = APIRequestFactory()
        req = factory.post("/fake/")
        force_authenticate(req, user=self.user)

        view = DomainViewSet()
        view.request = req

        view.action = "create"
        self.assertEqual(view.get_serializer_class().__name__, "DomainWriteSerializer")

        view.action = "update"
        self.assertEqual(view.get_serializer_class().__name__, "DomainWriteSerializer")

        view.action = "partial_update"
        self.assertEqual(view.get_serializer_class().__name__, "DomainWriteSerializer")

    # -------------------------
    # get_queryset branches
    # -------------------------
    def test_get_queryset_swagger_fake_view_returns_none(self):
        factory = APIRequestFactory()
        req = factory.get("/fake/")
        force_authenticate(req, user=self.user)

        view = DomainViewSet()
        view.request = req
        view.swagger_fake_view = True

        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    def test_list_requires_authentication(self):
        r = self.client.get(self._list_url())
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_as_superuser_sees_all(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(self._list_url())
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        ids = {d["id"] for d in r.json()}
        self.assertTrue(self.d_owned.id in ids)
        self.assertTrue(self.d_staffed.id in ids)
        self.assertTrue(self.d_other.id in ids)

    def test_list_as_staff_sees_all(self):
        self.client.force_authenticate(user=self.staff)
        r = self.client.get(self._list_url())
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        ids = {d["id"] for d in r.json()}
        self.assertTrue(self.d_owned.id in ids)
        self.assertTrue(self.d_staffed.id in ids)
        self.assertTrue(self.d_other.id in ids)

    def test_list_as_normal_user_sees_only_owned_or_staffed(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get(self._list_url())
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        ids = {d["id"] for d in r.json()}
        # user n'est pas owner de d_owned
        self.assertFalse(self.d_owned.id in ids)
        # user est staff sur d_staffed
        self.assertTrue(self.d_staffed.id in ids)
        # user n'a aucun accès à d_other
        self.assertFalse(self.d_other.id in ids)

    # -------------------------
    # retrieve behaviour: 200 / 404 (car queryset filtré)
    # -------------------------
    def test_retrieve_visible_domain_ok(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get(self._detail_url(self.d_staffed))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["id"], self.d_staffed.id)

    def test_retrieve_invisible_domain_returns_404(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get(self._detail_url(self.d_other))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------
    # create override: owner forced + owner added to staff + response is read serializer
    # -------------------------
    def test_create_requires_authentication(self):
        r = self.client.post(self._list_url(), self._create_payload(), format="json")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_as_authenticated_forces_owner_and_adds_staff(self):
        self.client.force_authenticate(user=self.user)
        payload = self._create_payload()

        r = self.client.post(self._list_url(), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        data = r.json()
        # Read serializer fields
        self.assertIn("id", data)
        self.assertIn("name", data)
        self.assertIn("description", data)
        self.assertIn("owner", data)
        self.assertIn("owner_username", data)
        self.assertIn("staff_usernames", data)

        created = Domain.objects.get(pk=data["id"])
        self.assertEqual(created.owner_id, self.user.id)
        self.assertTrue(created.staff.filter(id=self.user.id).exists())  # auto add

    # -------------------------
    # update / partial_update: permissions + response read serializer
    # -------------------------
    def test_update_forbidden_for_non_owner_non_staff(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "translations": {"fr": {"name": "X", "description": ""}},
            "allowed_language_codes": ["fr"],
            "active": False,
            "staff_ids": [],
        }
        r = self.client.put(self._detail_url(self.d_other), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)  # invisible => 404 (get_queryset filtre)

    def test_update_allowed_for_owner_returns_read_serializer(self):
        self.client.force_authenticate(user=self.owner)

        payload = {
            "translations": {"fr": {"name": "Owned UPDATED", "description": "D"},
                             "nl": {"name": "Owned NL", "description": ""},},
            "allowed_language_codes": ["fr", "nl"],
            "active": False,
            "staff_ids": [self.owner.pk],  # ok
        }

        r = self.client.put(self._detail_url(self.d_owned), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        data = r.json()
        # read serializer output
        self.assertIn("name", data)
        self.assertIn("description", data)
        self.assertEqual(data["id"], self.d_owned.id)

        self.d_owned.refresh_from_db()
        self.assertFalse(self.d_owned.active)
        self.d_owned.set_current_language("fr")
        self.assertEqual(self.d_owned.name, "Owned UPDATED")

    def test_partial_update_calls_update_path_and_returns_read_serializer(self):
        self.client.force_authenticate(user=self.owner)

        payload = {
            "translations": {"fr": {"name": "Owned PATCHED", "description": ""}},
            "active": True,
        }
        r = self.client.patch(self._detail_url(self.d_owned), payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        data = r.json()
        self.assertIn("name", data)
        self.assertEqual(data["id"], self.d_owned.id)

        self.d_owned.refresh_from_db()
        self.assertTrue(self.d_owned.active)
        self.d_owned.set_current_language("fr")
        self.assertEqual(self.d_owned.name, "Owned PATCHED")

    # -------------------------
    # destroy: allowed for owner/staff/superuser
    # -------------------------
    def test_destroy_requires_authentication(self):
        r = self.client.delete(self._detail_url(self.d_owned))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy_invisible_returns_404_for_normal_user(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.delete(self._detail_url(self.d_other))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_destroy_allowed_for_owner(self):
        d = Domain.objects.create(owner=self.owner, active=True)
        d.allowed_languages.set([self.lang_fr])
        d.set_current_language("fr")
        d.name = "To delete"
        d.description = ""
        d.save()
        d.staff.add(self.owner)

        self.client.force_authenticate(user=self.owner)
        r = self.client.delete(self._detail_url(d))
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Domain.objects.filter(pk=d.pk).exists())

    def test_destroy_allowed_for_superuser(self):
        d = Domain.objects.create(owner=self.other, active=True)
        d.allowed_languages.set([self.lang_fr])
        d.set_current_language("fr")
        d.name = "To delete 2"
        d.description = ""
        d.save()

        self.client.force_authenticate(user=self.superuser)
        r = self.client.delete(self._detail_url(d))
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Domain.objects.filter(pk=d.pk).exists())
