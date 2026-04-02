from customuser.models import CustomUser
from django.urls import reverse
from rest_framework.test import APITestCase
from unittest.mock import patch


class CustomUserApiTests(APITestCase):
    @patch("customuser.views.send_registration_confirmation_email")
    def test_create_user(self, send_registration_confirmation_email):
        url = reverse("api:user-api:api-root")  # /api/user/
        payload = {
            "username": "JohnDoe",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "SuperSecret123",
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(CustomUser.objects.count(), 1)
        user = CustomUser.objects.get(username="JohnDoe")
        self.assertEqual(user.email, "john@example.com")
        send_registration_confirmation_email.assert_called_once_with(user)


class CustomUserListTests(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="AdminPass123",
        )
        self.url = reverse("api:user-api:api-root")  # GET sur /api/user/

    def test_list_users_anonymous_forbidden(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)  # pas de token

    def test_list_users_as_admin(self):
        # on force l'authentification avec le client de test
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)
