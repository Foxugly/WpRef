# domain/tests/test_models.py
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.utils import translation

from domain.models import Domain, settings_language_codes
from language.models import Language

User = get_user_model()


class DomainModelTestCase(TestCase):
    """
    Tests Domain (models.py) compatibles avec Parler + ManyToMany:
    - Ne JAMAIS appeler full_clean() sur une instance Domain non sauvegardée
      (car Domain.clean() lit allowed_languages => besoin d'une PK).
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="owner", password="pwd")
        cls.staff1 = User.objects.create_user(username="staff1", password="pwd")
        cls.staff2 = User.objects.create_user(username="staff2", password="pwd")

        # Langues
        cls.lang_fr = Language.objects.create(code="fr", name="Français", active=True)
        cls.lang_en = Language.objects.create(code="en", name="English", active=True)
        cls.lang_xx = Language.objects.create(code="xx", name="Invalid", active=True)

    def setUp(self):
        translation.activate("fr")

    def tearDown(self):
        translation.deactivate_all()
        super().tearDown()

    # -----------------------
    # Helpers Parler
    # -----------------------
    def _set_parler(self, obj, lang: str, **fields):
        obj.set_current_language(lang)
        for k, v in fields.items():
            setattr(obj, k, v)
        obj.save()
        return obj

    def _mk_domain(self, *, active=True) -> Domain:
        return Domain.objects.create(owner=self.owner, active=active)

    # ---------------------------------------------------------------------
    # settings_language_codes()
    # ---------------------------------------------------------------------
    @override_settings(LANGUAGES=(("fr", "Français"), ("en", "English")))
    def test_settings_language_codes_reads_from_settings(self):
        self.assertEqual(settings_language_codes(), {"fr", "en"})

    @override_settings(LANGUAGES=())
    def test_settings_language_codes_empty_when_no_settings_languages(self):
        self.assertEqual(settings_language_codes(), set())

    # ---------------------------------------------------------------------
    # __str__ (Parler)
    # ---------------------------------------------------------------------
    def test_str_fallback_without_any_translation(self):
        d = self._mk_domain()
        self.assertEqual(str(d), f"Domain#{d.pk}")

    def test_str_uses_any_language_translation_when_available(self):
        d = self._mk_domain()
        self._set_parler(d, "fr", name="Domaine FR", description="Desc FR")

        translation.activate("fr")
        self.assertEqual(str(d), "Domaine FR")

        # any_language=True => si "en" n'existe pas, il doit trouver "fr"
        translation.activate("en")
        self.assertEqual(str(d), "Domaine FR")

    def test_str_prefers_current_language_if_exists(self):
        d = self._mk_domain()
        self._set_parler(d, "fr", name="Domaine FR", description="")
        self._set_parler(d, "en", name="Domain EN", description="")

        translation.activate("en")
        self.assertEqual(str(d), "Domain EN")

    # ---------------------------------------------------------------------
    # owner required
    # ---------------------------------------------------------------------
    def test_owner_is_required(self):
        # Avec Domain.save() qui appelle full_clean(), on attend une ValidationError (pas une IntegrityError DB)
        with self.assertRaises(ValidationError):
            Domain.objects.create(active=True)

    # ---------------------------------------------------------------------
    # clean(): validation allowed_languages (instance DOIT être sauvée)
    # ---------------------------------------------------------------------
    @override_settings(LANGUAGES=(("fr", "Français"), ("en", "English")))
    def test_clean_with_duplicate_allowed_languages_is_ok(self):
        d = self._mk_domain()
        d.allowed_languages.set([self.lang_fr, self.lang_fr, self.lang_en])
        d.full_clean()  # doit passer

    @override_settings(LANGUAGES=(("fr", "Français"), ("en", "English")))
    def test_clean_allows_only_language_codes_present_in_settings(self):
        d = self._mk_domain()
        d.allowed_languages.set([self.lang_fr, self.lang_en])

        # OK: d a une PK, allowed_languages accessible
        d.full_clean()

    @override_settings(LANGUAGES=(("fr", "Français"), ("en", "English")))
    def test_clean_rejects_language_codes_not_in_settings(self):
        d = self._mk_domain()
        d.allowed_languages.set([self.lang_fr, self.lang_xx])  # xx invalide

        with self.assertRaises(ValidationError) as ctx:
            d.full_clean()

        self.assertIn("allowed_languages", ctx.exception.message_dict)
        msg_list = ctx.exception.message_dict["allowed_languages"]
        self.assertTrue(any("Invalid language code(s)" in m for m in msg_list))
        self.assertTrue(any("xx" in m for m in msg_list))

    @override_settings(LANGUAGES=(("fr", "Français"), ("en", "English")))
    def test_clean_accepts_empty_allowed_languages(self):
        d = self._mk_domain()
        d.allowed_languages.clear()
        d.full_clean()  # ok

    @override_settings(LANGUAGES=())
    def test_clean_rejects_any_allowed_languages_when_settings_languages_empty(self):
        d = self._mk_domain()
        d.allowed_languages.set([self.lang_fr])
        with self.assertRaises(ValidationError):
            d.full_clean()

    # ---------------------------------------------------------------------
    # staff M2M (smoke)
    # ---------------------------------------------------------------------
    def test_staff_m2m_can_be_set(self):
        d = self._mk_domain()
        d.staff.set([self.staff1, self.staff2])
        self.assertEqual(set(d.staff.values_list("username", flat=True)), {"staff1", "staff2"})

    # ---------------------------------------------------------------------
    # Meta ordering
    # ---------------------------------------------------------------------
    def test_ordering_is_by_id_ascending(self):
        d1 = self._mk_domain()
        d2 = self._mk_domain()
        d3 = self._mk_domain()

        ids = list(Domain.objects.values_list("id", flat=True))
        self.assertEqual(ids, [d1.id, d2.id, d3.id])
