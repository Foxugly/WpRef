# domain/tests/tests_serializers.py
from unittest.mock import patch

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

        # patch stable des codes autorisés (car LANG_CODES est évalué à l'import)
        self._patch_lang_codes = patch("domain.serializers.LANG_CODES", {"fr", "nl", "en"})
        self._patch_lang_codes.start()
        self.addCleanup(self._patch_lang_codes.stop)

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

    def test_read_serializer_staff_usernames_empty_list_when_no_staff(self):
        d = Domain.objects.create(owner=self.owner, active=True)
        data = DomainReadSerializer(d).data
        self.assertEqual(data["staff_usernames"], [])

    # -------------------------
    # validate_allowed_language_codes
    # -------------------------
    def test_validate_allowed_language_codes_rejects_none_or_blank_items(self):
        payload = {
            "translations": {"fr": {"name": "Nom", "description": ""}},
            "allowed_language_codes": [None, "", "   "],
            "active": True,
        }
        s = DomainWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())

        self.assertIn("allowed_language_codes", s.errors)
        # DRF renvoie des erreurs indexées
        self.assertIn(0, s.errors["allowed_language_codes"])
        self.assertIn(1, s.errors["allowed_language_codes"])
        self.assertIn(2, s.errors["allowed_language_codes"])

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
    # validate() (global)
    # -------------------------
    def test_validate_requires_translations_field(self):
        payload = {"allowed_language_codes": ["fr"], "active": True}
        s = DomainWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)
        # required=True -> DRF message
        self.assertIn("required", str(s.errors["translations"][0]).lower())

    def test_validate_requires_translations_not_empty(self):
        payload = {"translations": {}, "allowed_language_codes": ["fr"], "active": True}
        s = DomainWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)
        self.assertEqual(str(s.errors["translations"][0]), "Au moins une traduction est requise.")

    def test_validate_allowed_language_codes_missing_translation_raises(self):
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

    def test_validate_no_allowed_language_codes_does_not_require_covering_translations(self):
        """
        Branche: allowed=set() -> pas de check 'missing'
        """
        payload = {
            "translations": {"fr": {"name": "Nom", "description": ""}},
            "active": True,
        }
        s = DomainWriteSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

    # -------------------------
    # _apply_translations helper
    # -------------------------
    def test_apply_translations_sets_empty_strings_when_missing_keys(self):
        d = Domain.objects.create(owner=self.owner, active=True)
        s = DomainWriteSerializer()
        s._apply_translations(d, {"fr": {"name": "X"}})

        d.refresh_from_db()
        d.set_current_language("fr")
        self.assertEqual(d.name, "X")
        self.assertEqual(d.description, "")  # clé absente => ""

    def test_apply_translations_with_none_is_noop(self):
        d = Domain.objects.create(owner=self.owner, active=True)
        s = DomainWriteSerializer()
        s._apply_translations(d, None)  # doit juste ne pas crash

    # -------------------------
    # create()
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

    def test_create_with_no_staff_and_codes_none_does_not_touch_m2m(self):
        """
        Branche:
        - staff = [] -> skip domain.staff.set
        - codes is None -> skip allowed_languages.set
        """
        payload = {
            "translations": {"fr": {"name": "Nom", "description": ""}},
            # allowed_language_codes absent => None (pop(..., None))
            # staff_ids absent => staff = []
            "active": True,
        }
        s = DomainWriteSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)
        d = s.save(owner=self.owner)

        self.assertEqual(d.staff.count(), 0)
        self.assertEqual(d.allowed_languages.count(), 0)

        d.set_current_language("fr")
        self.assertEqual(d.name, "Nom")

    def test_create_with_codes_list_filters_existing_language_objects_only(self):
        """
        Branche create(): langs = Language.objects.filter(code__in=codes)
        -> si code inexistant en DB, il est ignoré.
        """
        payload = {
            "translations": {"fr": {"name": "Nom", "description": ""}},
            "allowed_language_codes": ["fr", "zz"],  # zz n'existe pas en table Language
            "active": True,
        }
        s = DomainWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        # validate_allowed_language_codes bloque déjà zz via LANG_CODES patché {"fr","nl","en"}
        self.assertIn("allowed_language_codes", s.errors)

    # -------------------------
    # update()
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

        d2.set_current_language("en")
        self.assertEqual(d2.name, "After")
        self.assertEqual(d2.description, "AfterDesc")

    def test_update_when_staff_is_none_does_not_change_staff(self):
        """
        Branche update():
        staff = validated_data.pop("staff", None)
        if staff is not None: instance.staff.set(staff)
        """
        d = Domain.objects.create(owner=self.owner, active=True)
        d.staff.add(self.staff1)

        payload = {
            "translations": {"fr": {"name": "N", "description": ""}},
            "active": False,
            # staff_ids absent => staff=None => ne change pas
        }
        s = DomainWriteSerializer(instance=d, data=payload, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        d2 = s.save()

        self.assertFalse(d2.active)
        self.assertEqual(set(d2.staff.values_list("username", flat=True)), {"staff1"})

    def test_update_when_codes_is_none_does_not_change_allowed_languages(self):
        """
        Branche update():
        codes = validated_data.pop("allowed_language_codes", None)
        if codes is not None: instance.allowed_languages.set(...)
        """
        d = Domain.objects.create(owner=self.owner, active=True)
        d.allowed_languages.set([self.lang_fr, self.lang_nl])

        payload = {
            "translations": {"fr": {"name": "N", "description": ""}},
            "active": True,
            # allowed_language_codes absent => codes=None => ne change pas
        }
        s = DomainWriteSerializer(instance=d, data=payload, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        d2 = s.save()

        self.assertEqual(set(d2.allowed_languages.values_list("code", flat=True)), {"fr", "nl"})

    def test_update_when_translations_is_none_does_not_apply_translations(self):
        """
        Branche update(): if translations is not None -> apply
        """
        d = Domain.objects.create(owner=self.owner, active=True)
        d.set_current_language("fr")
        d.name = "Avant"
        d.description = "Desc"
        d.save()

        payload = {"active": False}  # translations absent => will fail validate() currently
        # ⚠️ Ton validate() impose translations non vide -> donc partial sans translations échoue.
        s = DomainWriteSerializer(instance=d, data=payload, partial=True)
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)
        self.assertEqual(str(s.errors["translations"][0]), "Au moins une traduction est requise.")

    def test_partial_update_missing_translations_field_fails_custom_message(self):
        d = Domain.objects.create(owner=self.owner, active=True)
        payload = {"active": False}
        s = DomainWriteSerializer(instance=d, data=payload, partial=True)
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)
        self.assertEqual(str(s.errors["translations"][0]), "Au moins une traduction est requise.")

    def test_create_codes_allowed_but_language_missing_in_db_is_ignored(self):
        with patch("domain.serializers.LANG_CODES", {"fr", "zz"}):
            payload = {
                "translations": {"fr": {"name": "Nom FR", "description": ""},
                                 "zz": {"name": "Nom ZZ", "description": ""}, },
                "allowed_language_codes": ["fr", "zz"],  # zz autorisé mais pas en DB
                "active": True,
            }
            s = DomainWriteSerializer(data=payload)
            self.assertTrue(s.is_valid(), s.errors)
            d = s.save(owner=self.owner)
            self.assertEqual(set(d.allowed_languages.values_list("code", flat=True)), {"fr"})
            d.set_current_language("fr")
            self.assertEqual(d.name, "Nom FR")

            d.set_current_language("zz")
            self.assertEqual(d.name, "Nom ZZ")
