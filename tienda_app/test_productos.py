from django.test import TestCase
from .models import Libro, Inventario


class ProductosTests(TestCase):
    def test_catalogo_serializa_stock(self):
        libro = Libro.objects.create(titulo="Coexistencia", precio="150.00")
        Inventario.objects.create(libro=libro, cantidad=10)
        response = self.client.get("/api/v1/productos/", HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Backend"], "Django-v1")
        self.assertEqual(response.json(), [{"id": libro.pk, "titulo": "Coexistencia", "precio": "150.00", "stock_actual": 10}])
        self.assertEqual(Inventario.objects.get().cantidad, 10)

    def test_catalogo_vacio(self):
        self.assertEqual(self.client.get("/api/v1/productos/").json(), [])

    def test_catalogo_no_admite_post(self):
        self.assertEqual(self.client.post("/api/v1/productos/").status_code, 405)
