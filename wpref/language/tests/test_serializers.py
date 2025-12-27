from django.test import TestCase
from rest_framework.exceptions import ValidationError

from language.models import Language
from language.serializers import LanguageReadSerializer, LanguageWriteSerializer


class LangSerializersTests(TestCase):
    # -------------------------
    # LangReadSerializer
    # -------------------------
    def test_read_serializer_fields_and_read_only(self):
        lang = Language.objects.create(code="fr", name="Français", active=True)

        s = LanguageReadSerializer(lang)
        self.assertEqual(set(s.data.keys()), {"id", "code", "name", "active"})
        # read_only_fields = fields (tous)
        self.assertEqual(set(s.Meta.read_only_fields), set(s.Meta.fields))

    # -------------------------
    # LangWriteSerializer: OK
    # -------------------------
    def test_write_serializer_valid_creates_and_normalizes_code(self):
        payload = {"code": "  FR  ", "name": "Français", "active": True}

        s = LanguageWriteSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

        obj = s.save()
        self.assertIsNotNone(obj.id)
        self.assertEqual(obj.code, "fr")  # strip + lower
        self.assertEqual(obj.name, "Français")
        self.assertEqual(obj.active, True)

    def test_write_serializer_allows_active_omitted_defaults_true(self):
        # active a un default=True côté modèle
        payload = {"code": "en", "name": "English"}

        s = LanguageWriteSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

        obj = s.save()
        self.assertEqual(obj.active, True)

    # -------------------------
    # LangWriteSerializer: validate_code boundaries
    # -------------------------
    def test_validate_code_rejects_too_short(self):
        payload = {"code": "f", "name": "Français", "active": True}
        s = LanguageWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("code", s.errors)
        self.assertIn("Code de langue invalide", str(s.errors["code"][0]))

    def test_validate_code_rejects_too_long(self):
        payload = {"code": "x" * 11, "name": "Too long", "active": True}
        s = LanguageWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("code", s.errors)
        self.assertIn("no more than 10 characters", str(s.errors["code"][0]).lower())

    def test_validate_code_handles_null(self):
        payload = {"code": None, "name": "No code", "active": True}
        s = LanguageWriteSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("code", s.errors)
        self.assertIn("may not be null", str(s.errors["code"][0]).lower())

    # -------------------------
    # read_only_fields id
    # -------------------------
    def test_write_serializer_id_is_read_only_and_ignored_on_create(self):
        payload = {"id": 999, "code": "nl", "name": "Nederlands", "active": True}
        s = LanguageWriteSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

        obj = s.save()
        self.assertNotEqual(obj.id, 999)  # l'id fourni doit être ignoré
        self.assertEqual(obj.code, "nl")

    def test_write_serializer_update_normalizes_code(self):
        lang = Language.objects.create(code="fr", name="Français", active=True)

        s = LanguageWriteSerializer(instance=lang, data={"code": "  EN  ", "name": "English", "active": False})
        self.assertTrue(s.is_valid(), s.errors)

        obj = s.save()
        obj.refresh_from_db()
        self.assertEqual(obj.code, "en")
        self.assertEqual(obj.name, "English")
        self.assertEqual(obj.active, False)

    # -------------------------
    # extra: direct call validate_code for coverage clarity
    # -------------------------
    def test_validate_code_direct_call_ok(self):
        s = LanguageWriteSerializer()
        self.assertEqual(s.validate_code("  FR  "), "fr")

    def test_validate_code_direct_call_raises(self):
        s = LanguageWriteSerializer()
        with self.assertRaises(ValidationError):
            s.validate_code("f")
