from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .api.serializers import LibroSerializer
from .models import Inventario, Libro, Orden


class APICompraTests(TestCase):
    def setUp(self):
        self.libro = Libro.objects.create(titulo="API y HTML", precio="150.00")
        self.inv = Inventario.objects.create(libro=self.libro, cantidad=10)
        self.api = APIClient()
        self.gateway = Mock()
        self.gateway.pagar.return_value = True
        self.factory = patch("tienda_app.api.views.PaymentFactory.get_processor", return_value=self.gateway)
        self.factory.start()
        self.addCleanup(self.factory.stop)
        self.payload = {"libro_id": self.libro.pk, "direccion_envio": "Medellin"}

    def comprar(self, payload=None):
        return self.api.post("/api/v1/comprar/", self.payload if payload is None else payload, format="json")

    def test_api_201_y_cambio_visible_en_html(self):
        antes = self.client.get("/inventario/")
        self.assertContains(antes, '<td class="stock">10</td>', html=True)
        response = self.comprar()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["estado"], "exito")
        self.assertIn("178.50", response.data["mensaje"])
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.cantidad, 9)
        orden = Orden.objects.get()
        self.assertEqual(orden.direccion_envio, "Medellin")
        self.assertEqual(orden.detalles.get().cantidad, 1)
        self.assertContains(self.client.get("/inventario/"), '<td class="stock">9</td>', html=True)

    def test_html_y_api_comparten_servicio(self):
        response = self.client.post(f"/compra/{self.libro.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.comprar().status_code, 201)
        self.assertEqual(list(Orden.objects.values_list("total", flat=True)), [Decimal("178.50")]*2)
        self.assertEqual(Inventario.objects.get().cantidad, 8)

    def test_serializer_libro_con_y_sin_stock(self):
        self.assertEqual(LibroSerializer(self.libro).data["stock_actual"], 10)
        otro = Libro.objects.create(titulo="Sin inventario", precio="10.00")
        self.assertEqual(LibroSerializer(otro).data["stock_actual"], 0)

    def test_datos_invalidos_400_no_compra(self):
        casos = [{}, {"libro_id": 0, "direccion_envio": "Medellin"},
                 {"libro_id": self.libro.pk, "direccion_envio": ""},
                 {"libro_id": self.libro.pk, "direccion_envio": "x"*201},
                 dict(self.payload, cantidad=0), dict(self.payload, cantidad=-1),
                 dict(self.payload, libro_id="invalido")]
        for caso in casos:
            with self.subTest(caso=caso):
                self.assertEqual(self.comprar(caso).status_code, 400)
        self.gateway.pagar.assert_not_called()
        self.assertFalse(Orden.objects.exists())

    def test_json_malformado_400(self):
        response = self.api.post("/api/v1/comprar/", data='{"libro_id":', content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Orden.objects.exists())

    def test_sin_stock_409(self):
        self.inv.cantidad = 0
        self.inv.save()
        self.assertEqual(self.comprar().status_code, 409)
        self.assertFalse(Orden.objects.exists())
        self.gateway.pagar.assert_not_called()

    def test_inexistente_404(self):
        self.assertEqual(self.comprar(dict(self.payload, libro_id=99999)).status_code, 404)
        self.assertFalse(Orden.objects.exists())

    def test_rechazo_pago_409_revierte(self):
        self.gateway.pagar.return_value = False
        self.assertEqual(self.comprar().status_code, 409)
        self.assertFalse(Orden.objects.exists())
        self.assertEqual(Inventario.objects.get().cantidad, 10)

    def test_error_pago_500_revierte(self):
        self.gateway.pagar.side_effect = OSError("Fallo de escritura")
        with self.assertLogs("tienda_app.api.views", level="ERROR"):
            response = self.comprar()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data, {"error": "Error interno"})
        self.assertFalse(Orden.objects.exists())
        self.assertEqual(Inventario.objects.get().cantidad, 10)

    def test_compra_autenticada(self):
        usuario = get_user_model().objects.create_user(username="juan_api")
        self.api.force_authenticate(usuario)
        self.assertEqual(self.comprar().status_code, 201)
        self.assertEqual(Orden.objects.get().usuario, usuario)

    def test_api_browsable_html_y_metodos(self):
        response = self.api.get("/api/v1/comprar/", HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "libro_id", status_code=405)
        self.assertEqual(self.api.put("/api/v1/comprar/", {}, format="json").status_code, 405)
        self.assertEqual(self.api.options("/api/v1/comprar/").status_code, 200)

    def test_log_banco_real(self):
        self.factory.stop()
        with TemporaryDirectory() as carpeta, override_settings(BASE_DIR=Path(carpeta)):
            with patch.dict("os.environ", {"PAYMENT_PROVIDER": "BANCO", "ESTUDIANTE_NOMBRE": "PRUEBA API"}):
                self.assertEqual(self.comprar().status_code, 201)
            lineas = (Path(carpeta)/"pagos_locales_PRUEBA_API.log").read_text().splitlines()
            self.assertEqual(len(lineas), 1)
            self.assertIn("$178.50", lineas[0])
