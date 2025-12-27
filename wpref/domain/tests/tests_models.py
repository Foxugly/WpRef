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

    def test_str_fallback_when_translation_removed(self):
        d = Domain.objects.create(owner=self.owner, active=True)

        d.set_current_language("fr")
        d.name = "Bonjour"
        d.description = ""
        d.save()

        self.assertIn("Bonjour", str(d))  # sanity

        d.translations.all().delete()
        d2 = Domain.objects.get(pk=d.pk)

        self.assertEqual(d2.translations.count(), 0)
        self.assertEqual(str(d2), f"Domain#{d2.pk}")

    def test_str_fallback_when_no_translation(self):
        d = Domain.objects.create(owner=self.owner, active=True)
        d.translations.all().delete()
        self.assertEqual(d.translations.count(), 0)
        d2 = Domain.objects.get(pk=d.pk)
        self.assertEqual(d2.translations.count(), 0)
        self.assertEqual(str(d2), f"Domain#{d2.pk}")
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
    def test_clean_ok_when_allowed_languages_are_in_settings(self):
        fr = Language.objects.create(code="fr", name="Français", active=True)
        nl = Language.objects.create(code="nl", name="Nederlands", active=True)

        d = Domain.objects.create(owner=self.owner, active=True)
        d.allowed_languages.add(fr, nl)

        # doit passer sans ValidationError
        d.clean()

    def test_clean_raises_when_allowed_language_not_in_settings(self):
        # 'xx' n'est pas dans settings.LANGUAGES
        xx = Language.objects.create(code="xx", name="Xx", active=True)

        d = Domain.objects.create(owner=self.owner, active=True)
        d.allowed_languages.add(xx)

        with self.assertRaises(ValidationError) as ctx:
            d.clean()

        err = ctx.exception
        self.assertIn("allowed_languages", err.message_dict)
        self.assertIn("Invalid language code(s):", " ".join(err.message_dict["allowed_languages"]))

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
