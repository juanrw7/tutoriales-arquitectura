from django.test import TestCase


class SaludTests(TestCase):
    def test_salud_sin_consultas(self):
        with self.assertNumQueries(0):
            response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_salud_no_admite_post(self):
        self.assertEqual(self.client.post("/health/").status_code, 405)
