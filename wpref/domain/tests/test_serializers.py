from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from domain.models import Domain
from domain.serializers import DomainReadSerializer, DomainWriteSerializer
from language.models import Language

User = get_user_model()


@override_settings(LANGUAGES=(("fr", "Français"), ("nl", "Nederlands"), ("en", "English")))
class DomainSerializersTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.staff1 = User.objects.create_user(username="staff1", password="pass")
        self.staff2 = User.objects.create_user(username="staff2", password="pass")

        self.lang_fr = Language.objects.create(code="fr", name="Français", active=True)
        self.lang_nl = Language.objects.create(code="nl", name="Nederlands", active=True)
        self.lang_en = Language.objects.create(code="en", name="English", active=True)

    # -------------------------
    # DomainReadSerializer
    # -------------------------
    def test_read_serializer_returns_name_description_or_empty_and_allowed_languages(self):
        d = Domain.objects.create(owner=self.owner, active=True)
        d.allowed_languages.set([self.lang_fr])

        data = DomainReadSerializer(d).data
        self.assertEqual(data["name"], "")
        self.assertEqual(data["description"], "")

        self.assertEqual(len(data["allowed_languages"]), 1)
        self.assertEqual(data["allowed_languages"][0]["code"], "fr")

        d.set_current_language("fr")
        d.name = "Domaine FR"
        d.description = "Desc FR"
        d.save()

        data = DomainReadSerializer(d).data
        self.assertEqual(data["name"], "Domaine FR")
        self.assertEqual(data["description"], "Desc FR")

    def test_read_serializer_owner_username_and_staff_usernames(self):
        d = Domain.objects.create(owner=self.owner, active=True)
        d.allowed_languages.set([self.lang_fr, self.lang_nl])
        d.staff.add(self.staff1, self.staff2)

        data = DomainReadSerializer(d).data
        self.assertEqual(data["owner_username"], "owner")
        self.assertEqual(set(data["staff_usernames"]), {"staff1", "staff2"})

    # -------------------------
    # validate_allowed_language_codes
    # -------------------------
    def test_validate_allowed_language_codes_dedup_and_lower_strip(self):
        payload = {
            "translations": {
                "fr": {"name": "N", "description": ""},
                "nl": {"name": "N", "description": ""},
                "en": {"name": "N", "description": ""},
            },
            "allowed_language_codes": [" FR ", "nl", "fr", "en", "NL"],
            "active": True,
            "staff_ids": [self.staff1.pk],
        }
        s = DomainWriteSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["allowed_language_codes"], ["fr", "nl", "en"])

    def test_validate_allowed_language_codes_invalid_raises(self):
        payload = {
            "translations": {"fr": {"name": "N", "description": ""}},
            "allowed_language_codes": ["fr", "xx"],
            "active": True,
        }
        s = DomainWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("allowed_language_codes", s.errors)
        self.assertIn("Invalid language code(s): xx", str(s.errors["allowed_language_codes"][0]))

    # -------------------------
    # validate
    # -------------------------
    def test_validate_requires_translations_field(self):
        payload = {"allowed_language_codes": ["fr"], "active": True}
        s = DomainWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)
        # required=True -> DRF
        self.assertIn("required", str(s.errors["translations"][0]).lower())

    def test_validate_requires_translations_not_empty(self):
        payload = {"translations": {}, "allowed_language_codes": ["fr"], "active": True}
        s = DomainWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)
        self.assertEqual(str(s.errors["translations"][0]), "Au moins une traduction est requise.")

    def test_validate_missing_translation_for_allowed_language_codes(self):
        payload = {
            "translations": {"fr": {"name": "Nom", "description": ""}},
            "allowed_language_codes": ["fr", "nl"],
            "active": True,
        }
        s = DomainWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)
        msg = str(s.errors["translations"][0])
        self.assertIn("Traductions manquantes pour:", msg)
        self.assertIn("nl", msg)

    # -------------------------
    # create
    # -------------------------
    def test_create_creates_domain_applies_translations_sets_m2m_languages_and_staff(self):
        payload = {
            "translations": {
                "fr": {"name": "Domaine FR", "description": "Desc FR"},
                "nl": {"name": "Domein NL", "description": "Desc NL"},
            },
            "allowed_language_codes": ["fr", "nl", "fr"],
            "active": False,
            "staff_ids": [self.staff1.pk],
        }
        s = DomainWriteSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

        d = s.save(owner=self.owner)

        self.assertFalse(d.active)
        self.assertEqual(set(d.staff.values_list("username", flat=True)), {"staff1"})
        self.assertEqual(set(d.allowed_languages.values_list("code", flat=True)), {"fr", "nl"})

        d.set_current_language("fr")
        self.assertEqual(d.name, "Domaine FR")
        self.assertEqual(d.description, "Desc FR")

        d.set_current_language("nl")
        self.assertEqual(d.name, "Domein NL")
        self.assertEqual(d.description, "Desc NL")

    # -------------------------
    # update
    # -------------------------
    def test_update_updates_active_staff_and_languages_and_translations(self):
        d = Domain.objects.create(owner=self.owner, active=True)
        d.allowed_languages.set([self.lang_fr])
        d.staff.add(self.staff1)

        d.set_current_language("fr")
        d.name = "Avant"
        d.description = "AvantDesc"
        d.save()

        payload = {
            "translations": {
                "fr": {"name": "Après", "description": "AprèsDesc"},
                "en": {"name": "After", "description": "AfterDesc"},
            },
            "allowed_language_codes": ["fr", "en"],
            "active": False,
            "staff_ids": [self.staff2.pk],
        }
        s = DomainWriteSerializer(instance=d, data=payload, partial=False)
        self.assertTrue(s.is_valid(), s.errors)
        d2 = s.save()

        self.assertFalse(d2.active)
        self.assertEqual(set(d2.staff.values_list("username", flat=True)), {"staff2"})
        self.assertEqual(set(d2.allowed_languages.values_list("code", flat=True)), {"fr", "en"})

        d2.set_current_language("fr")
        self.assertEqual(d2.name, "Après")
        self.assertEqual(d2.description, "AprèsDesc")

    def test_partial_update_missing_translations_field_fails_custom_message(self):
        d = Domain.objects.create(owner=self.owner, active=True)
        payload = {"active": False}
        s = DomainWriteSerializer(instance=d, data=payload, partial=True)
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)
        self.assertEqual(str(s.errors["translations"][0]), "Au moins une traduction est requise.")
