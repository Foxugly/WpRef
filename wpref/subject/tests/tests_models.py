# subject/tests/test_models.py
from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils.translation import activate

from domain.models import Domain
from subject.models import Subject

User = get_user_model()


class SubjectModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="owner", password="pass")
        cls.domain = Domain.objects.create(owner=cls.owner, active=True)
        cls.domain.set_current_language("fr")
        cls.domain.name = "Domaine FR"
        cls.domain.description = ""
        cls.domain.save()

    def test_subject_creation_with_translation(self):
        s = Subject.objects.create(domain=self.domain)

        s.set_current_language("fr")
        s.name = "Mathématiques"
        s.description = "Les maths"
        s.save()

        s.refresh_from_db()
        # en parler, accéder à s.name dépend de la langue courante
        s.set_current_language("fr")
        self.assertEqual(s.name, "Mathématiques")
        self.assertEqual(s.description, "Les maths")
        self.assertEqual(s.domain_id, self.domain.id)

    def test_domain_is_optional(self):
        s = Subject.objects.create()
        s.set_current_language("fr")
        s.name = "Sans domaine"
        s.description = ""
        s.save()

        s.refresh_from_db()
        self.assertIsNone(s.domain)

    def test_str_returns_translated_name(self):
        s = Subject.objects.create()
        s.set_current_language("fr")
        s.name = "Philosophie"
        s.description = ""
        s.save()

        # __str__ utilise safe_translation_getter(any_language=True)
        self.assertEqual(str(s), "Philosophie")

    def test_str_fallback_when_no_translation(self):
        s = Subject.objects.create(domain=self.domain)

        # supprime toutes les traductions parler
        s.translations.all().delete()
        s2 = Subject.objects.get(pk=s.pk)

        self.assertEqual(s2.translations.count(), 0)
        self.assertEqual(str(s2), f"Subject#{s2.pk}")

    def test_safe_translation_getter_any_language_returns_one_available_translation(self):
        s = Subject.objects.create()

        s.set_current_language("fr")
        s.name = "Mathématiques"
        s.description = ""
        s.save()

        s.set_current_language("nl")
        s.name = "Wiskunde"
        s.description = ""
        s.save()

        # Force une langue courante qui n'a PAS de traduction sur l'objet
        activate("en")

        # Recharge pour éviter le cache parler
        s2 = Subject.objects.get(pk=s.pk)

        self.assertIn(
            s2.safe_translation_getter("name", any_language=True),
            {"Mathématiques", "Wiskunde"},
        )

        # Et test “strict” par langue
        self.assertEqual(s2.safe_translation_getter("name", language_code="nl"), "Wiskunde")
        self.assertEqual(s2.safe_translation_getter("name", language_code="fr"), "Mathématiques")

    def test_ordering_is_by_minus_pk(self):
        s1 = Subject.objects.create()
        s1.set_current_language("fr")
        s1.name = "Premier"
        s1.description = ""
        s1.save()

        s2 = Subject.objects.create()
        s2.set_current_language("fr")
        s2.name = "Deuxième"
        s2.description = ""
        s2.save()

        subjects = list(Subject.objects.all())  # Meta ordering = ["-pk"]
        self.assertEqual(subjects[0].pk, s2.pk)
        self.assertEqual(subjects[1].pk, s1.pk)

    def test_domain_protect_on_delete(self):
        """
        FK Domain -> Subject est en PROTECT: supprimer le domain doit lever ProtectedError
        si un Subject le référence.
        """
        s = Subject.objects.create(domain=self.domain)
        s.set_current_language("fr")
        s.name = "Sujet lié"
        s.description = ""
        s.save()

        with self.assertRaises(ProtectedError):
            self.domain.delete()
