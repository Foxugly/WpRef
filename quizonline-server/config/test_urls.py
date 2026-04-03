from django.test import SimpleTestCase


class HealthCheckTests(SimpleTestCase):
    def test_health_check_returns_ok(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})
