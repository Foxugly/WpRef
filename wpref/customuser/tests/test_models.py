# users/tests/test_models_custom_user.py
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from domain.models import Domain
from language.models import Language

User = get_user_model()


@override_settings(LANGUAGES=(("fr", "Français"), ("nl", "Nederlands"), ("en", "English")))
class CustomUserModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Langues (utile si tes Domain.clean / DomainWriteSerializer s'y réfèrent)
        cls.lang_fr = Language.objects.create(code="fr", name="Français", active=True)
        cls.lang_nl = Language.objects.create(code="nl", name="Nederlands", active=True)
        cls.lang_en = Language.objects.create(code="en", name="English", active=True)

        cls.superuser = User.objects.create_user(
            username="su", password="pass", is_superuser=True, is_staff=True
        )
        cls.global_staff = User.objects.create_user(
            username="staff", password="pass", is_staff=True, is_superuser=False
        )
        cls.owner = User.objects.create_user(username="owner", password="pass")
        cls.other = User.objects.create_user(username="other", password="pass")

        # Domains
        cls.d_active_owned = Domain.objects.create(owner=cls.owner, active=True)
        cls.d_active_owned.allowed_languages.set([cls.lang_fr, cls.lang_nl])
        cls.d_active_owned.set_current_language("fr")
        cls.d_active_owned.name = "Alpha"
        cls.d_active_owned.description = ""
        cls.d_active_owned.save()

        cls.d_active_staffed = Domain.objects.create(owner=cls.other, active=True)
        cls.d_active_staffed.allowed_languages.set([cls.lang_fr])
        cls.d_active_staffed.set_current_language("fr")
        cls.d_active_staffed.name = "Beta"
        cls.d_active_staffed.description = ""
        cls.d_active_staffed.save()
        cls.d_active_staffed.staff.add(cls.owner)  # owner user est aussi staff de ce domain

        cls.d_inactive_owned = Domain.objects.create(owner=cls.owner, active=False)
        cls.d_inactive_owned.allowed_languages.set([cls.lang_fr])
        cls.d_inactive_owned.set_current_language("fr")
        cls.d_inactive_owned.name = "Gamma"
        cls.d_inactive_owned.description = ""
        cls.d_inactive_owned.save()

        cls.d_other_only = Domain.objects.create(owner=cls.other, active=True)
        cls.d_other_only.allowed_languages.set([cls.lang_fr])
        cls.d_other_only.set_current_language("fr")
        cls.d_other_only.name = "Delta"
        cls.d_other_only.description = ""
        cls.d_other_only.save()

    # ---------------------------------------------------------------------
    # _domain_model (apps.get_model) — éviter imports circulaires
    # ---------------------------------------------------------------------
    def test_domain_model_returns_domain_class(self):
        DomainModel = User._domain_model()
        self.assertIs(DomainModel, Domain)

    # ---------------------------------------------------------------------
    # __str__ / get_display_name
    # ---------------------------------------------------------------------
    def test_get_display_name_with_first_last(self):
        u = User.objects.create_user(username="u", password="pass", first_name="Renaud", last_name="Vilain")
        self.assertEqual(u.get_display_name(), "Renaud Vilain (u)")
        self.assertEqual(str(u), "Renaud Vilain (u)")

    def test_get_display_name_fallback_username(self):
        u = User.objects.create_user(username="u2", password="pass", first_name="", last_name="")
        self.assertEqual(u.get_display_name(), "u2")
        self.assertEqual(str(u), "u2")

    # ---------------------------------------------------------------------
    # can_manage_domain
    # ---------------------------------------------------------------------
    def test_can_manage_domain_false_when_domain_none(self):
        self.assertFalse(self.owner.can_manage_domain(None))

    def test_can_manage_domain_true_for_superuser(self):
        self.assertTrue(self.superuser.can_manage_domain(self.d_other_only))

    def test_can_manage_domain_true_for_global_staff(self):
        self.assertTrue(self.global_staff.can_manage_domain(self.d_other_only))

    def test_can_manage_domain_true_for_owner(self):
        self.assertTrue(self.owner.can_manage_domain(self.d_active_owned))

    def test_can_manage_domain_true_for_domain_staff_membership(self):
        # owner user est membre de Domain.staff de d_active_staffed
        self.assertTrue(self.owner.can_manage_domain(self.d_active_staffed))

    def test_can_manage_domain_false_when_not_owner_nor_staff(self):
        self.assertFalse(self.owner.can_manage_domain(self.d_other_only))

    def test_can_manage_domain_uses_domain_owner_id_attribute(self):
        # Domain-like object sans model: owner_id présent
        domain_like = SimpleNamespace(id=999, owner_id=self.owner.id, staff=SimpleNamespace())
        self.assertTrue(self.owner.can_manage_domain(domain_like))

    def test_can_manage_domain_falls_back_to_managed_domains_relation(self):
        # On force le chemin final: managed_domains.filter(id=domain.id).exists()
        domain_like = SimpleNamespace(id=self.d_active_staffed.id, owner_id=self.other.id)
        with patch.object(User, "managed_domains") as rel:
            rel.filter.return_value.exists.return_value = True
            self.assertTrue(self.owner.can_manage_domain(domain_like))
            rel.filter.assert_called_once_with(id=self.d_active_staffed.id)

    # ---------------------------------------------------------------------
    # get_manageable_domains / get_visible_domains
    # ---------------------------------------------------------------------
    def test_get_manageable_domains_for_superuser_returns_all(self):
        qs = self.superuser.get_manageable_domains(active_only=False)
        self.assertEqual(set(qs.values_list("id", flat=True)), set(Domain.objects.values_list("id", flat=True)))

    def test_get_manageable_domains_for_staff_returns_all(self):
        qs = self.global_staff.get_manageable_domains(active_only=False)
        self.assertEqual(set(qs.values_list("id", flat=True)), set(Domain.objects.values_list("id", flat=True)))

    def test_get_manageable_domains_active_only_filters_active(self):
        qs = self.superuser.get_manageable_domains(active_only=True)
        self.assertTrue(all(Domain.objects.get(pk=i).active for i in qs.values_list("id", flat=True)))
        self.assertNotIn(self.d_inactive_owned.id, set(qs.values_list("id", flat=True)))

    def test_get_manageable_domains_for_normal_user_filters_owner_or_staff(self):
        qs = self.owner.get_manageable_domains(active_only=False)
        ids = set(qs.values_list("id", flat=True))
        self.assertIn(self.d_active_owned.id, ids)  # owner
        self.assertIn(self.d_inactive_owned.id, ids)  # owner même si inactive car active_only=False
        self.assertIn(self.d_active_staffed.id, ids)  # staff membership
        self.assertNotIn(self.d_other_only.id, ids)  # pas visible

    def test_get_visible_domains_is_alias_of_get_manageable_domains(self):
        qs1 = self.owner.get_manageable_domains(active_only=True)
        qs2 = self.owner.get_visible_domains(active_only=True)
        self.assertEqual(list(qs1.values_list("id", flat=True)), list(qs2.values_list("id", flat=True)))

    # ---------------------------------------------------------------------
    # set_current_domain
    # ---------------------------------------------------------------------
    def test_set_current_domain_none_allowed_resets_and_saves(self):
        u = User.objects.create_user(username="u3", password="pass")
        u.current_domain = self.d_other_only
        u.save(update_fields=["current_domain"])

        u.set_current_domain(None, allow_none=True, save=True)
        u.refresh_from_db()
        self.assertIsNone(u.current_domain)

    def test_set_current_domain_none_not_allowed_raises_value_error(self):
        u = User.objects.create_user(username="u4", password="pass")
        with self.assertRaises(ValueError):
            u.set_current_domain(None, allow_none=False, save=False)

    def test_set_current_domain_non_manageable_raises_permission_error(self):
        u = self.owner
        with self.assertRaises(PermissionError):
            u.set_current_domain(self.d_other_only, save=False)

    def test_set_current_domain_manageable_sets_and_saves(self):
        u = self.owner
        u.set_current_domain(self.d_active_owned, save=True)
        u.refresh_from_db()
        self.assertEqual(u.current_domain_id, self.d_active_owned.id)

    def test_set_current_domain_save_false_does_not_persist(self):
        u = User.objects.create_user(username="u5", password="pass")
        self.d_active_owned.staff.add(u)
        u.set_current_domain(None, save=False)
        self.assertIsNone(u.current_domain_id)
        u.set_current_domain(self.d_active_owned, save=False)
        self.assertEqual(u.current_domain_id, self.d_active_owned.id)
        u.refresh_from_db()
        self.assertIsNone(u.current_domain_id)

    # ---------------------------------------------------------------------
    # ensure_current_domain_is_valid + auto_fix
    # ---------------------------------------------------------------------
    def test_ensure_current_domain_is_valid_when_none_returns_true(self):
        u = User.objects.create_user(username="u6", password="pass")
        self.assertTrue(u.ensure_current_domain_is_valid(auto_fix=False))

    def test_ensure_current_domain_is_valid_when_inactive_and_active_only_true(self):
        u = self.owner
        u.current_domain = self.d_inactive_owned
        u.save(update_fields=["current_domain"])

        ok = u.ensure_current_domain_is_valid(auto_fix=False, active_only=True)
        self.assertFalse(ok)

    def test_ensure_current_domain_is_valid_when_inactive_autofix_picks_new(self):
        u = self.owner
        u.current_domain = self.d_inactive_owned
        u.save(update_fields=["current_domain"])

        ok = u.ensure_current_domain_is_valid(auto_fix=True, active_only=True)
        self.assertFalse(ok)  # l'état initial est invalide

        u.refresh_from_db()
        # doit avoir choisi un domaine actif visible (Alpha ou Beta)
        self.assertIn(u.current_domain_id, {self.d_active_owned.id, self.d_active_staffed.id})

    def test_ensure_current_domain_is_valid_when_not_manageable(self):
        u = self.owner
        u.current_domain = self.d_other_only
        u.save(update_fields=["current_domain"])

        ok = u.ensure_current_domain_is_valid(auto_fix=False, active_only=True)
        self.assertFalse(ok)

    def test_ensure_current_domain_is_valid_when_not_manageable_autofix(self):
        u = self.owner
        u.current_domain = self.d_other_only
        u.save(update_fields=["current_domain"])

        ok = u.ensure_current_domain_is_valid(auto_fix=True, active_only=True)
        self.assertFalse(ok)

        u.refresh_from_db()
        self.assertIn(u.current_domain_id, {self.d_active_owned.id, self.d_active_staffed.id})

    def test_ensure_current_domain_is_valid_when_manageable_and_active(self):
        u = self.owner
        u.current_domain = self.d_active_staffed
        u.save(update_fields=["current_domain"])
        self.assertTrue(u.ensure_current_domain_is_valid(auto_fix=False, active_only=True))

    # ---------------------------------------------------------------------
    # pick_default_current_domain
    # ---------------------------------------------------------------------
    def test_pick_default_current_domain_orders_by_name_and_returns_first(self):
        # owner voit Alpha (owned) et Beta (staff). alpha < beta => Alpha
        u = self.owner
        chosen = u.pick_default_current_domain(save=True, active_only=True)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.id, self.d_active_owned.id)  # Alpha

        u.refresh_from_db()
        self.assertEqual(u.current_domain_id, self.d_active_owned.id)

    def test_pick_default_current_domain_returns_none_when_no_visible(self):
        u = User.objects.create_user(username="u7", password="pass")
        chosen = u.pick_default_current_domain(save=False, active_only=True)
        self.assertIsNone(chosen)
        self.assertIsNone(u.current_domain_id)

    # ---------------------------------------------------------------------
    # clean()
    # ---------------------------------------------------------------------
    def test_clean_allows_current_domain_none(self):
        u = User.objects.create_user(username="u8", password="pass")
        u.current_domain = None
        # ne doit pas lever
        u.clean()

    def test_clean_raises_validation_error_when_current_domain_not_manageable(self):
        u = self.owner
        u.current_domain = self.d_other_only
        with self.assertRaises(ValidationError) as ctx:
            u.clean()
        self.assertIn("current_domain", ctx.exception.message_dict)

    def test_clean_allows_when_manageable(self):
        u = self.owner
        u.current_domain = self.d_active_staffed  # manageable via staff
        u.clean()  # ne doit pas lever

    def test_clean_allows_staff_global_even_if_not_owner_or_staff(self):
        u = self.global_staff
        u.current_domain = self.d_other_only
        u.clean()  # staff global => can_manage_domain True

    # ---------------------------------------------------------------------
    # QoL properties
    # ---------------------------------------------------------------------
    def test_current_domain_id_safe_and_has_current_domain(self):
        u = User.objects.create_user(username="u9", password="pass")
        self.assertIsNone(u.current_domain_id_safe)
        self.assertFalse(u.has_current_domain)

        u.current_domain = self.d_active_owned
        u.save(update_fields=["current_domain"])
        u.refresh_from_db()

        self.assertEqual(u.current_domain_id_safe, self.d_active_owned.id)
        self.assertTrue(u.has_current_domain)
