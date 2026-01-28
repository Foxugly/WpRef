from __future__ import annotations

from django.test import TestCase
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from django.contrib.auth import get_user_model

from domain.models import Domain
from domain.serializers import (
    DomainDetailSerializer,
    DomainPartialSerializer,
    DomainReadSerializer,
    DomainWriteSerializer,
)
from subject.models import Subject
from language.models import Language

User = get_user_model()


class DomainSerializersTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()

        cls.owner = User.objects.create_user(username="owner", password="x")
        cls.staff1 = User.objects.create_user(username="staff1", password="x")
        cls.staff2 = User.objects.create_user(username="staff2", password="x")

        cls.lang_fr = Language.objects.create(code="fr", name="Français", active=True)
        cls.lang_nl = Language.objects.create(code="nl", name="Nederlands", active=True)
        cls.lang_en_inactive = Language.objects.create(code="en", name="English", active=False)

        cls.domain = Domain.objects.create(owner=cls.owner, active=True)
        cls.domain.allowed_languages.set([cls.lang_fr, cls.lang_nl, cls.lang_en_inactive])
        cls.domain.staff.set([cls.staff1, cls.staff2])

        # Parler translations
        cls.domain.set_current_language("fr")
        cls.domain.name = "Domaine FR"
        cls.domain.description = "Desc FR"
        cls.domain.save()

        cls.domain.set_current_language("nl")
        cls.domain.name = "Domein NL"
        cls.domain.description = "Desc NL"
        cls.domain.save()

    # -------------------------
    # DomainReadSerializer
    # -------------------------
    def test_domain_read_serializer_outputs_expected_fields(self):
        s = DomainReadSerializer(instance=self.domain, context={"request": self.factory.get("/")})
        data = s.data

        expected_fields = {
            "id",
            "translations",
            "allowed_languages",
            "active",
            "owner",
            "staff",
            "created_at",
            "updated_at",
        }
        self.assertSetEqual(set(data.keys()), expected_fields)

        # translations
        self.assertIn("fr", data["translations"])
        self.assertIn("nl", data["translations"])
        self.assertEqual(data["translations"]["fr"]["name"], "Domaine FR")
        self.assertEqual(data["translations"]["nl"]["name"], "Domein NL")

        # owner/staff
        self.assertEqual(data["owner"]["id"], self.owner.id)
        self.assertEqual(data["owner"]["username"], self.owner.username)

        staff_usernames = {u["username"] for u in data["staff"]}
        self.assertSetEqual(staff_usernames, {self.staff1.username, self.staff2.username})

    def test_domain_read_serializer_allowed_languages_filters_active(self):
        s = DomainReadSerializer(instance=self.domain, context={"request": self.factory.get("/")})
        data = s.data

        # serializer filters active=True and orders by id
        returned_codes = [lang["code"] for lang in data["allowed_languages"]]
        self.assertIn("fr", returned_codes)
        self.assertIn("nl", returned_codes)
        self.assertNotIn("en", returned_codes)

    def test_domain_read_serializer_is_read_only(self):
        s = DomainReadSerializer(data={"active": False}, context={"request": self.factory.get("/")})
        self.assertFalse(s.is_valid())
        self.assertIn("non_field_errors", s.errors)

    # -------------------------
    # DomainWriteSerializer - validation
    # -------------------------
    def test_domain_write_serializer_requires_translations(self):
        payload = {
            "allowed_languages": [self.lang_fr.id],
            "active": True,
            "staff": [self.staff1.id],
        }
        request = self.factory.post("/", payload, format="json")
        request.user = self.owner

        s = DomainWriteSerializer(data=payload, context={"request": request})
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)

    def test_domain_write_serializer_rejects_unknown_translation_codes(self):
        payload = {
            "allowed_languages": [self.lang_fr.id],
            "translations": {"xx": {"name": "X", "description": ""}},
            "active": True,
            "staff": [self.staff1.id],
        }
        request = self.factory.post("/", payload, format="json")
        request.user = self.owner

        s = DomainWriteSerializer(data=payload, context={"request": request})
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)

    def test_domain_write_serializer_requires_missing_translations_for_allowed_languages(self):
        payload = {
            "allowed_languages": [self.lang_fr.id, self.lang_nl.id],
            "translations": {"fr": {"name": "FR", "description": ""}},  # missing nl
            "active": True,
            "staff": [self.staff1.id],
        }
        request = self.factory.post("/", payload, format="json")
        request.user = self.owner

        s = DomainWriteSerializer(data=payload, context={"request": request})
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)

    def test_domain_write_serializer_rejects_empty_allowed_languages(self):
        payload = {
            "allowed_languages": [],
            "translations": {"fr": {"name": "FR", "description": ""}},
            "active": True,
            "staff": [self.staff1.id],
        }
        request = self.factory.post("/", payload, format="json")
        request.user = self.owner

        s = DomainWriteSerializer(data=payload, context={"request": request})
        self.assertFalse(s.is_valid())
        self.assertIn("allowed_languages", s.errors)

    def test_domain_write_serializer_dedups_allowed_languages(self):
        payload = {
            "allowed_languages": [self.lang_fr.id, self.lang_fr.id, self.lang_nl.id],
            "translations": {
                "fr": {"name": "FR", "description": ""},
                "nl": {"name": "NL", "description": ""},
            },
            "active": True,
            "staff": [self.staff1.id],
        }
        request = self.factory.post("/", payload, format="json")
        request.user = self.owner

        s = DomainWriteSerializer(data=payload, context={"request": request})
        self.assertTrue(s.is_valid(), s.errors)
        obj = s.save()

        self.assertEqual(obj.allowed_languages.count(), 2)

    # -------------------------
    # DomainWriteSerializer - create / update
    # -------------------------
    def test_domain_write_serializer_can_create(self):
        payload = {
            "allowed_languages": [self.lang_fr.id, self.lang_nl.id],
            "translations": {
                "fr": {"name": "New FR", "description": "D FR"},
                "nl": {"name": "New NL", "description": "D NL"},
            },
            "active": True,
            "staff": [self.staff1.id, self.staff2.id],
        }
        request = self.factory.post("/", payload, format="json")
        request.user = self.owner

        s = DomainWriteSerializer(data=payload, context={"request": request})
        self.assertTrue(s.is_valid(), s.errors)
        obj = s.save()

        self.assertEqual(obj.owner_id, self.owner.id)
        self.assertTrue(obj.active)
        self.assertEqual(obj.staff.count(), 2)
        self.assertEqual(obj.allowed_languages.count(), 2)

        obj.set_current_language("fr")
        self.assertEqual(obj.name, "New FR")
        self.assertEqual(obj.description, "D FR")

        obj.set_current_language("nl")
        self.assertEqual(obj.name, "New NL")
        self.assertEqual(obj.description, "D NL")

    def test_domain_write_serializer_can_update(self):
        payload = {
            "allowed_languages": [self.lang_fr.id],
            "translations": {"fr": {"name": "Updated FR", "description": "Updated"}},
            "active": False,
            "staff": [self.staff1.id],
        }
        request = self.factory.put("/", payload, format="json")
        request.user = self.owner

        s = DomainWriteSerializer(instance=self.domain, data=payload, context={"request": request})
        self.assertTrue(s.is_valid(), s.errors)
        obj = s.save()

        self.assertFalse(obj.active)
        self.assertEqual(list(obj.allowed_languages.values_list("code", flat=True)), ["fr"])
        self.assertEqual(list(obj.staff.values_list("username", flat=True)), ["staff1"])

        obj.set_current_language("fr")
        self.assertEqual(obj.name, "Updated FR")
        self.assertEqual(obj.description, "Updated")

    def test_domain_write_serializer_requires_owner_in_context(self):
        payload = {
            "allowed_languages": [self.lang_fr.id],
            "translations": {"fr": {"name": "FR", "description": ""}},
            "active": True,
            "staff": [self.staff1.id],
        }

        request = self.factory.post("/", payload, format="json")
        # Simule un utilisateur anonyme (ou non authentifié)
        request.user = type("Anon", (), {"is_anonymous": True})()

        s = DomainWriteSerializer(data=payload, context={"request": request})

        # Le serializer est valide côté champs/format
        self.assertTrue(s.is_valid(), s.errors)

        # Mais la création doit refuser car owner (request.user) invalide
        with self.assertRaises(ValidationError):
            s.save()

    # -------------------------
    # DomainPartialSerializer
    # -------------------------
    def test_domain_partial_serializer_can_update_only_active(self):
        payload = {"active": False}
        request = self.factory.patch("/", payload, format="json")
        request.user = self.owner

        s = DomainPartialSerializer(instance=self.domain, data=payload, partial=True, context={"request": request})
        self.assertTrue(s.is_valid(), s.errors)
        obj = s.save()
        self.assertFalse(obj.active)

    def test_domain_partial_serializer_can_update_allowed_languages_only_without_translations(self):
        payload = {"allowed_languages": [self.lang_fr.id]}
        request = self.factory.patch("/", payload, format="json")
        request.user = self.owner

        s = DomainPartialSerializer(instance=self.domain, data=payload, partial=True, context={"request": request})
        self.assertTrue(s.is_valid(), s.errors)
        obj = s.save()

        self.assertEqual(list(obj.allowed_languages.values_list("code", flat=True)), ["fr"])

        # Existing translations should remain untouched
        obj.set_current_language("nl")
        self.assertEqual(obj.name, "Domein NL")

    def test_domain_partial_serializer_rejects_empty_allowed_languages(self):
        payload = {"allowed_languages": []}
        request = self.factory.patch("/", payload, format="json")
        request.user = self.owner

        s = DomainPartialSerializer(instance=self.domain, data=payload, partial=True, context={"request": request})
        self.assertFalse(s.is_valid())
        self.assertIn("allowed_languages", s.errors)

    def test_domain_partial_serializer_when_translations_present_applies_full_rules(self):
        # allowed: fr + nl, but only provide fr translation -> should fail (missing nl)
        payload = {
            "allowed_languages": [self.lang_fr.id, self.lang_nl.id],
            "translations": {"fr": {"name": "Only FR", "description": ""}},
        }
        request = self.factory.patch("/", payload, format="json")
        request.user = self.owner

        s = DomainPartialSerializer(instance=self.domain, data=payload, partial=True, context={"request": request})
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)

    # -------------------------
    # DomainDetailSerializer
    # -------------------------
    def test_domain_detail_serializer_outputs_subjects_key_and_filters_active(self):
        # Create 2 subjects: 1 active, 1 inactive
        s_active = Subject.objects.create(domain=self.domain, active=True)
        s_active.set_current_language("fr")
        s_active.name = "Sujet actif"
        s_active.description = "Desc"
        s_active.save()

        s_inactive = Subject.objects.create(domain=self.domain, active=False)
        s_inactive.set_current_language("fr")
        s_inactive.name = "Sujet inactif"
        s_inactive.save()

        serializer = DomainDetailSerializer(instance=self.domain, context={"request": self.factory.get("/")})
        data = serializer.data

        self.assertIn("subjects", data)
        self.assertIsInstance(data["subjects"], list)
        self.assertEqual(len(data["subjects"]), 1)

        # SubjectReadSerializer structure assumed to include translations
        # We'll assert at least that it's the active one by checking its translated name
        only_subject = data["subjects"][0]
        self.assertIn("translations", only_subject)
        self.assertIn("fr", only_subject["translations"])
        self.assertEqual(only_subject["translations"]["fr"]["name"], "Sujet actif")

    def test_domain_detail_serializer_subjects_ordered_by_id(self):
        # serializer uses obj.subjects.filter(active=True).order_by("id")
        s1 = Subject.objects.create(domain=self.domain, active=True)
        s1.set_current_language("fr")
        s1.name = "S1"
        s1.save()

        s2 = Subject.objects.create(domain=self.domain, active=True)
        s2.set_current_language("fr")
        s2.name = "S2"
        s2.save()

        serializer = DomainDetailSerializer(instance=self.domain, context={"request": self.factory.get("/")})
        subjects = serializer.data["subjects"]

        # Should be ascending by id => first should be s1
        self.assertGreater(len(subjects), 1)
        first = subjects[0]
        second = subjects[1]
        self.assertEqual(first["id"], s1.id)
        self.assertEqual(second["id"], s2.id)

    def test_domain_detail_serializer_is_read_only(self):
        s = DomainDetailSerializer(data={"active": False}, context={"request": self.factory.get("/")})
        self.assertFalse(s.is_valid())
        self.assertIn("non_field_errors", s.errors)
