from __future__ import annotations

import time

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import translation
from domain.models import Domain
from language.models import Language
from subject.models import Subject

User = get_user_model()


class SubjectModelTestCase(TestCase):
    """
    Tests Subject (models.py) compatibles avec Parler.
    Notes:
    - On évite de tester __str__ sur instance non sauvegardée (Parler peut être instable sans PK).
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="owner", password="pwd")

        # Languages (utile pour Parler / cohérence globale)
        cls.lang_fr = Language.objects.create(code="fr", name="Français", active=True)
        cls.lang_en = Language.objects.create(code="en", name="English", active=True)

        # Domain minimal (évite le piège Domain.clean() M2M à la création)
        cls.domain = Domain.objects.create(owner=cls.owner, active=True)
        cls.domain.allowed_languages.set([cls.lang_fr, cls.lang_en])
        cls.domain.set_current_language("fr")
        cls.domain.name = "Domaine"
        cls.domain.description = ""
        cls.domain.save()

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

    def _mk_subject(self, *, domain=None, active=True) -> Subject:
        return Subject.objects.create(domain=domain or self.domain, active=active)

    # ---------------------------------------------------------------------
    # FK domain required (DB level)
    # ---------------------------------------------------------------------
    def test_domain_is_required_db_level(self):
        # domain FK NOT NULL => IntegrityError au niveau DB
        with self.assertRaises(IntegrityError):
            Subject.objects.create(active=True)

    # ---------------------------------------------------------------------
    # __str__ (Parler)
    # ---------------------------------------------------------------------
    def test_str_fallback_without_any_translation(self):
        s = self._mk_subject()
        self.assertEqual(str(s), f"Subject#{s.pk}")

    def test_str_uses_any_language_translation_when_available(self):
        s = self._mk_subject()
        self._set_parler(s, "fr", name="Sujet FR", description="Desc FR")

        translation.activate("fr")
        self.assertEqual(str(s), "Sujet FR")

        # any_language=True => si "en" n'existe pas, il doit trouver "fr"
        translation.activate("en")
        self.assertEqual(str(s), "Sujet FR")

    def test_str_prefers_current_language_if_exists(self):
        s = self._mk_subject()
        self._set_parler(s, "fr", name="Sujet FR", description="")
        self._set_parler(s, "en", name="Subject EN", description="")

        translation.activate("en")
        self.assertEqual(str(s), "Subject EN")

    # ---------------------------------------------------------------------
    # Meta ordering
    # ---------------------------------------------------------------------
    def test_ordering_is_by_pk_desc(self):
        s1 = self._mk_subject()
        s2 = self._mk_subject()
        s3 = self._mk_subject()

        ids = list(Subject.objects.values_list("id", flat=True))
        self.assertEqual(ids, [s3.id, s2.id, s1.id])

    # ---------------------------------------------------------------------
    # Timestamps
    # ---------------------------------------------------------------------
    def test_created_at_and_updated_at_are_set_on_create(self):
        s = self._mk_subject()
        self.assertIsNotNone(s.created_at)
        self.assertIsNotNone(s.updated_at)

    def test_updated_at_changes_on_save(self):
        s = self._mk_subject()
        old_updated = s.updated_at

        time.sleep(0.01)  # 10ms pour garantir un tick différent même sur SQLite

        s.active = not s.active
        s.save()  # laisse Django gérer auto_now
        s.refresh_from_db()

        self.assertGreater(s.updated_at, old_updated)

    # ---------------------------------------------------------------------
    # active flag (smoke)
    # ---------------------------------------------------------------------
    def test_active_default_true(self):
        s = Subject.objects.create(domain=self.domain)
        self.assertTrue(s.active)

    def test_active_can_be_false(self):
        s = self._mk_subject(active=False)
        self.assertFalse(s.active)
