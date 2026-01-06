# subject/tests/test_serializers.py
from django.contrib.auth import get_user_model
from django.test import TestCase

from domain.models import Domain
from subject.models import Subject
from subject.serializers import SubjectWriteSerializer, SubjectReadSerializer

User = get_user_model()


class SubjectSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="owner", password="pass")
        cls.domain = Domain.objects.create(owner=cls.owner, active=True)
        cls.domain.set_current_language("fr")
        cls.domain.name = "Domaine FR"
        cls.domain.description = ""
        cls.domain.save()

    # -------------------------
    # SubjectWriteSerializer.validate
    # -------------------------
    def test_write_validate_translations_field_is_required(self):
        s = SubjectWriteSerializer(data={"domain": self.domain.id})
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)
        self.assertEqual(s.errors["translations"][0].code, "required")
        self.assertEqual(str(s.errors["translations"][0]), "This field is required.")

    def test_write_validate_rejects_empty_translations_dict_with_custom_message(self):
        s = SubjectWriteSerializer(data={"translations": {}, "domain": self.domain.id})
        self.assertFalse(s.is_valid())
        self.assertIn("translations", s.errors)

        # ici, translations est présent mais vide -> ton validate() s'applique
        self.assertEqual(str(s.errors["translations"][0]), "Au moins une traduction est requise.")

    def test_write_validate_accepts_translations(self):
        payload = {
            "domain": self.domain.id,
            "translations": {"fr": {"name": "Math", "description": "Les maths"}},
        }
        s = SubjectWriteSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

    # -------------------------
    # SubjectWriteSerializer.create
    # -------------------------
    def test_write_create_creates_subject_and_applies_translations(self):
        payload = {
            "domain": self.domain.id,
            "translations": {
                "fr": {"name": "Mathématiques", "description": "Les maths"},
                "nl": {"name": "Wiskunde", "description": "Wiskunde beschrijving"},
            },
        }

        ser = SubjectWriteSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
        obj = ser.save()
        created = Subject.objects.get(pk=obj.pk)

        self.assertIsInstance(obj, Subject)
        self.assertEqual(obj.domain_id, self.domain.id)

        # Vérifie que les traductions existent réellement en DB
        obj_fr = Subject.objects.get(pk=obj.pk)
        self.assertEqual(created.safe_translation_getter("name", language_code="fr"), "Mathématiques")
        self.assertEqual(created.safe_translation_getter("name", language_code="nl"), "Wiskunde")

    def test_write_create_allows_null_domain(self):
        payload = {
            "domain": None,
            "translations": {"fr": {"name": "Sans domaine", "description": ""}},
        }
        ser = SubjectWriteSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
        obj = ser.save()

        self.assertIsNone(obj.domain)

    # -------------------------
    # SubjectWriteSerializer.update
    # -------------------------
    def test_write_update_updates_domain_without_translations(self):
        # subject initial
        s = Subject.objects.create(domain=None)
        s.set_current_language("fr")
        s.name = "Initial"
        s.description = "Desc"
        s.save()

        payload = {"domain": self.domain.id, "translations": {"fr": {"name": "Initial", "description": "Desc"}}}
        # on valide une fois via serializer (car translations requis par validate)
        ser = SubjectWriteSerializer(instance=s, data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
        obj = ser.save()

        obj.refresh_from_db()
        self.assertEqual(obj.domain_id, self.domain.id)

    def test_write_update_applies_translations_when_provided(self):
        s = Subject.objects.create(domain=self.domain)
        s.set_current_language("fr")
        s.name = "Avant"
        s.description = "Avant desc"
        s.save()

        payload = {
            "domain": self.domain.id,
            "translations": {
                "fr": {"name": "Après", "description": "Après desc"},
                "nl": {"name": "Na", "description": "Na beschrijving"},
            },
        }
        ser = SubjectWriteSerializer(instance=s, data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
        obj = ser.save()

        obj_fr = Subject.objects.get(pk=obj.pk)
        obj_fr.set_current_language("fr")
        self.assertEqual(obj_fr.name, "Après")
        self.assertEqual(obj_fr.description, "Après desc")

        obj_nl = Subject.objects.get(pk=obj.pk)
        obj_nl.set_current_language("nl")
        self.assertEqual(obj_nl.name, "Na")
        self.assertEqual(obj_nl.description, "Na beschrijving")

    def test_write_update_does_not_change_translations_if_none(self):
        """
        Ton update() fait:
          translations = validated_data.pop("translations", None)
          if translations: _apply_translations(...)
        Donc si translations=None -> aucune modif de traduction.
        """
        s = Subject.objects.create(domain=self.domain)
        s.set_current_language("fr")
        s.name = "Conserve"
        s.description = "Conserve desc"
        s.save()

        # MAIS: ton validate() exige translations.
        # Pour tester le chemin "translations=None", on appelle update() directement.
        ser = SubjectWriteSerializer()
        updated = ser.update(s, {"domain": None})  # translations absent => None

        updated.refresh_from_db()
        updated.set_current_language("fr")
        self.assertIsNone(updated.domain)
        self.assertEqual(updated.name, "Conserve")
        self.assertEqual(updated.description, "Conserve desc")

    # -------------------------
    # SubjectReadSerializer
    # -------------------------
    def test_read_serializer_returns_name_description_and_domain(self):
        s = Subject.objects.create(domain=self.domain)
        s.set_current_language("fr")
        s.name = "Philo"
        s.description = "Desc philo"
        s.save()

        # Important: ReadSerializer lit "name" et "description" via attributs,
        # donc la langue courante peut impacter. On force fr avant sérialisation.
        s.set_current_language("fr")

        data = SubjectReadSerializer(instance=s).data
        self.assertEqual(data["id"], s.id)
        self.assertEqual(data["name"], "Philo")
        self.assertEqual(data["description"], "Desc philo")
        self.assertEqual(data["domain"], self.domain.id)

    def test_read_serializer_handles_null_domain(self):
        s = Subject.objects.create(domain=None)
        s.set_current_language("fr")
        s.name = "Sans domaine"
        s.description = ""
        s.save()
        s.set_current_language("fr")

        data = SubjectReadSerializer(instance=s).data
        self.assertIsNone(data["domain"])
        self.assertEqual(data["name"], "Sans domaine")
