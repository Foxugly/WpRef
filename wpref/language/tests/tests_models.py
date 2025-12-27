from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from language.models import Language


class LangModelTests(TestCase):
    def test_defaults(self):
        l = Language.objects.create(code="fr", name="Français")
        self.assertEqual(l.active, True)

    def test_str(self):
        l = Language.objects.create(code="nl", name="Nederlands")
        self.assertEqual(str(l), "nl — Nederlands")

    def test_meta_ordering(self):
        Language.objects.create(code="nl", name="Nederlands")
        Language.objects.create(code="en", name="English")
        Language.objects.create(code="fr", name="Français")

        codes = list(Language.objects.all().values_list("code", flat=True))
        self.assertEqual(codes, ["en", "fr", "nl"])  # ordering = ["code"]

    def test_meta_verbose_names(self):
        self.assertEqual(Language._meta.verbose_name, "Language")
        self.assertEqual(Language._meta.verbose_name_plural, "Languages")

    def test_code_unique_constraint(self):
        Language.objects.create(code="fr", name="Français")
        with self.assertRaises(IntegrityError):
            Language.objects.create(code="fr", name="French (duplicate)")

    def test_code_required(self):
        l = Language(code="", name="Français")
        with self.assertRaises(ValidationError) as ctx:
            l.full_clean()  # valide blank/constraints
        self.assertIn("code", ctx.exception.message_dict)

    def test_name_required(self):
        l = Language(code="fr", name="")
        with self.assertRaises(ValidationError) as ctx:
            l.full_clean()
        self.assertIn("name", ctx.exception.message_dict)

    def test_code_max_length(self):
        # max_length=10 => 11 doit échouer au full_clean
        l = Language(code="x" * 11, name="Too long")
        with self.assertRaises(ValidationError) as ctx:
            l.full_clean()
        self.assertIn("code", ctx.exception.message_dict)

    def test_name_max_length(self):
        # max_length=100 => 101 doit échouer au full_clean
        l = Language(code="fr", name="x" * 101)
        with self.assertRaises(ValidationError) as ctx:
            l.full_clean()
        self.assertIn("name", ctx.exception.message_dict)

    def test_active_can_be_false(self):
        l = Language.objects.create(code="en", name="English", active=False)
        l.refresh_from_db()
        self.assertEqual(l.active, False)

    def test_help_texts_exist(self):
        code_field = Language._meta.get_field("code")
        name_field = Language._meta.get_field("name")
        active_field = Language._meta.get_field("active")

        self.assertTrue(code_field.help_text)
        self.assertTrue(name_field.help_text)
        self.assertTrue(active_field.help_text)
