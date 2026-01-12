# domain/tests/tests_models.py

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase, override_settings
from domain.models import Domain, settings_language_codes
from language.models import Language

User = get_user_model()


@override_settings(LANGUAGES=(("fr", "Français"), ("nl", "Nederlands"), ("en", "English")))
class DomainModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass")

    # -------------------------
    # settings_language_codes()
    # -------------------------
    def test_settings_language_codes_returns_codes_from_settings(self):
        self.assertEqual(settings_language_codes(), {"fr", "nl", "en"})

    @override_settings(LANGUAGES=())
    def test_settings_language_codes_handles_empty_settings(self):
        self.assertEqual(settings_language_codes(), set())

    def test_settings_language_codes_handles_missing_LANGUAGES_attr(self):
        """
        getattr(settings, "LANGUAGES", []) -> [] si attribut absent
        """
        from django.conf import settings as dj_settings

        # patch.object sur settings pour simuler absence d'attribut LANGUAGES
        # (on supprime temporairement l'attribut si présent)
        had = hasattr(dj_settings, "LANGUAGES")
        old = getattr(dj_settings, "LANGUAGES", None)
        if had:
            delattr(dj_settings, "LANGUAGES")
        try:
            self.assertEqual(settings_language_codes(), set())
        finally:
            if had:
                setattr(dj_settings, "LANGUAGES", old)

    # -------------------------
    # __str__
    # -------------------------
    def test_str_returns_translated_name_when_available(self):
        d = Domain.objects.create(owner=self.owner, active=True)
        d.set_current_language("fr")
        d.name = "Domaine FR"
        d.description = "Desc"
        d.save()

        self.assertEqual(str(d), "Domaine FR")

    def test_str_fallback_when_safe_translation_getter_returns_none(self):
        d = Domain.objects.create(owner=self.owner, active=True)
        with patch.object(Domain, "safe_translation_getter", return_value=None):
            self.assertEqual(str(d), f"Domain#{d.pk}")

    def test_str_fallback_when_safe_translation_getter_returns_empty_string(self):
        d = Domain.objects.create(owner=self.owner, active=True)
        with patch.object(Domain, "safe_translation_getter", return_value=""):
            self.assertEqual(str(d), f"Domain#{d.pk}")

    def test_str_fallback_includes_pk(self):
        """
        Vérifie explicitement le format fallback Domain#{pk}
        """
        d = Domain.objects.create(owner=self.owner, active=True)
        with patch.object(Domain, "safe_translation_getter", return_value=""):
            s = str(d)
        self.assertTrue(s.startswith("Domain#"))
        self.assertEqual(s, f"Domain#{d.pk}")

    # -------------------------
    # Meta.ordering
    # -------------------------
    def test_meta_ordering_is_id(self):
        self.assertEqual(Domain._meta.ordering, ["id"])

    def test_queryset_is_ordered_by_id(self):
        d1 = Domain.objects.create(owner=self.owner, active=True)
        d2 = Domain.objects.create(owner=self.owner, active=True)
        ids = list(Domain.objects.values_list("id", flat=True))
        self.assertEqual(ids, sorted([d1.id, d2.id]))

    # -------------------------
    # clean() + allowed_languages M2M
    # -------------------------
    def test_clean_ok_when_allowed_languages_empty(self):
        """
        Si allowed_languages est vide => codes=set() => invalid=[] => ok
        """
        d = Domain.objects.create(owner=self.owner, active=True)
        d.clean()  # ne doit pas lever

    def test_clean_ok_when_allowed_languages_are_in_settings(self):
        fr = Language.objects.create(code="fr", name="Français", active=True)
        nl = Language.objects.create(code="nl", name="Nederlands", active=True)

        d = Domain.objects.create(owner=self.owner, active=True)
        d.allowed_languages.add(fr, nl)
        d.clean()  # ne doit pas lever

    def test_clean_raises_when_allowed_language_not_in_settings(self):
        xx = Language.objects.create(code="xx", name="Xx", active=True)

        d = Domain.objects.create(owner=self.owner, active=True)
        d.allowed_languages.add(xx)

        with self.assertRaises(ValidationError) as ctx:
            d.clean()

        err = ctx.exception
        self.assertIn("allowed_languages", err.message_dict)
        msg = " ".join(err.message_dict["allowed_languages"])
        self.assertIn("Invalid language code(s): xx", msg)

    def test_clean_raises_with_multiple_invalid_codes_sorted(self):
        """
        invalid = sorted([...]) -> vérifie tri + join dans le message
        """
        xx = Language.objects.create(code="xx", name="Xx", active=True)
        aa = Language.objects.create(code="aa", name="Aa", active=True)

        d = Domain.objects.create(owner=self.owner, active=True)
        d.allowed_languages.add(xx, aa)

        with self.assertRaises(ValidationError) as ctx:
            d.clean()

        msg = " ".join(ctx.exception.message_dict["allowed_languages"])
        # tri attendu: aa, xx
        self.assertIn("Invalid language code(s): aa, xx", msg)

    def test_clean_raises_when_mix_valid_and_invalid(self):
        fr = Language.objects.create(code="fr", name="Français", active=True)
        xx = Language.objects.create(code="xx", name="Xx", active=True)

        d = Domain.objects.create(owner=self.owner, active=True)
        d.allowed_languages.add(fr, xx)

        with self.assertRaises(ValidationError) as ctx:
            d.clean()

        msg = " ".join(ctx.exception.message_dict["allowed_languages"])
        self.assertIn("Invalid language code(s): xx", msg)
        self.assertNotIn("fr", msg)

    @override_settings(LANGUAGES=())
    def test_clean_raises_when_settings_languages_empty_and_allowed_languages_not_empty(self):
        fr = Language.objects.create(code="fr", name="Français", active=True)

        d = Domain.objects.create(owner=self.owner, active=True)
        d.allowed_languages.add(fr)

        with self.assertRaises(ValidationError) as ctx:
            d.clean()

        msg = " ".join(ctx.exception.message_dict["allowed_languages"])
        self.assertIn("Invalid language code(s): fr", msg)

    # -------------------------
    # owner PROTECT
    # -------------------------
    def test_owner_protected_from_delete(self):
        Domain.objects.create(owner=self.owner, active=True)
        with self.assertRaises(ProtectedError):
            self.owner.delete()

    # -------------------------
    # staff M2M
    # -------------------------
    def test_staff_m2m_can_add_and_read(self):
        staff1 = User.objects.create_user(username="staff1", password="pass")
        staff2 = User.objects.create_user(username="staff2", password="pass")

        d = Domain.objects.create(owner=self.owner, active=True)
        d.staff.add(staff1, staff2)

        self.assertEqual(set(d.staff.values_list("username", flat=True)), {"staff1", "staff2"})
        self.assertIn(d, staff1.managed_domains.all())
        self.assertIn(d, staff2.managed_domains.all())

    def test_allowed_languages_related_name_domains(self):
        """
        Bonus coverage: related_name="domains"
        """
        fr = Language.objects.create(code="fr", name="Français", active=True)
        d = Domain.objects.create(owner=self.owner, active=True)
        d.allowed_languages.add(fr)

        self.assertIn(d, fr.domains.all())
