from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from domain.models import Domain

User = get_user_model()


class DomainModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass")

    def test_str_returns_name(self):
        d = Domain.objects.create(name="Water-polo", owner=self.owner)
        self.assertEqual(str(d), "Water-polo")

    def test_clean_rejects_invalid_languages(self):
        d = Domain(name="WP", owner=self.owner, allowed_languages=["fr", "xx"])
        with self.assertRaises(ValidationError) as ctx:
            d.full_clean()  # important: triggers clean()

        self.assertIn("allowed_languages", ctx.exception.message_dict)

    def test_clean_accepts_valid_languages(self):
        d = Domain(name="WP", owner=self.owner, allowed_languages=["fr"])
        d.full_clean()  # should not raise

    def test_staff_m2m_works(self):
        staff = User.objects.create_user(username="staff", password="pass")
        d = Domain.objects.create(name="WP", owner=self.owner)
        d.staff.add(staff)

        self.assertTrue(d.staff.filter(id=staff.id).exists())
        self.assertTrue(staff.managed_domains.filter(id=d.id).exists())  # reverse name
