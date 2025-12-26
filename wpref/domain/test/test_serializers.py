from django.contrib.auth import get_user_model
from django.test import TestCase

from domain.models import Domain
from domain.serializers import DomainSerializer

User = get_user_model()


class DomainSerializerTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.u2 = User.objects.create_user(username="u2", password="pass")

    def test_validate_allowed_languages_rejects_invalid(self):
        data = {
            "title": "Water-polo",
            "description": "desc",
            "allowed_languages": ["fr", "xx"],
            "active": True,
            "staff_ids": [self.u2.id],
        }
        ser = DomainSerializer(data=data)
        self.assertFalse(ser.is_valid())
        self.assertIn("allowed_languages", ser.errors)

    def test_validate_allowed_languages_dedup(self):
        data = {
            "name": "Water-polo",
            "description": "desc",
            "allowed_languages": ["fr", "fr"],
            "active": True,
        }
        ser = DomainSerializer(data=data)
        self.assertTrue(ser.is_valid(), ser.errors)
        self.assertEqual(ser.validated_data["allowed_languages"], ["fr"])

    def test_staff_ids_write_sets_staff(self):
        data = {
            "name": "Water-polo",
            "allowed_languages": ["fr"],
            "active": True,
            "staff_ids": [self.u2.id],
        }
        ser = DomainSerializer(data=data)
        self.assertTrue(ser.is_valid(), ser.errors)

        # owner est read-only et normalement fourni par perform_create.
        # Pour un test serializer pur, on le passe via save(owner=...)
        domain = ser.save(owner=self.owner)

        self.assertTrue(domain.staff.filter(id=self.u2.id).exists())

    def test_owner_is_read_only_on_update(self):
        d = Domain.objects.create(name="WP", owner=self.owner, allowed_languages=["fr"])
        other_owner = User.objects.create_user(username="other", password="pass")

        ser = DomainSerializer(
            instance=d,
            data={"owner": other_owner.id, "name": "WP2"},
            partial=True,
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        d2 = ser.save()

        # owner ne doit pas changer
        self.assertEqual(d2.owner_id, self.owner.id)
        self.assertEqual(d2.name, "WP2")
