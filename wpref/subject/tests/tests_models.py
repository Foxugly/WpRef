from django.db import IntegrityError
from django.test import TestCase

from subject.models import Subject


class SubjectModelTestCase(TestCase):

    def test_subject_creation(self):
        s = Subject.objects.create(
            name="Mathématiques",
            description="Les maths"
        )

        self.assertEqual(s.name, "Mathématiques")
        self.assertEqual(s.description, "Les maths")
        self.assertIsNotNone(s.slug)

    def test_slug_is_generated_from_name(self):
        s = Subject.objects.create(name="Sciences Humaines")

        self.assertEqual(s.slug, "sciences-humaines")

    def test_slug_is_not_overwritten_if_provided(self):
        s = Subject.objects.create(
            name="Histoire",
            slug="custom-slug"
        )

        self.assertEqual(s.slug, "custom-slug")

        # changement du name ne doit PAS modifier le slug
        s.name = "Histoire Moderne"
        s.save()
        s.refresh_from_db()

        self.assertEqual(s.slug, "custom-slug")

    def test_name_must_be_unique(self):
        Subject.objects.create(name="Géographie")

        with self.assertRaises(IntegrityError):
            Subject.objects.create(name="Géographie")

    def test_slug_must_be_unique(self):
        Subject.objects.create(name="Physique", slug="science")

        with self.assertRaises(IntegrityError):
            Subject.objects.create(name="Chimie", slug="science")

    def test_ordering_is_by_name(self):
        s2 = Subject.objects.create(name="Zoologie")
        s1 = Subject.objects.create(name="Algèbre")

        subjects = list(Subject.objects.all())
        self.assertEqual(subjects[0].name, "Algèbre")
        self.assertEqual(subjects[1].name, "Zoologie")

    def test_str_returns_name(self):
        s = Subject.objects.create(name="Philosophie")
        self.assertEqual(str(s), "Philosophie")
