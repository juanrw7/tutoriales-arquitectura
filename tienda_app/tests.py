from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
from django.test import TestCase, override_settings
from .models import Libro, Inventario, Orden
from .services import CompraRapidaService
from .infra.gateways import BancoNacionalProcesador


class CompraRapidaTests(TestCase):
    def setUp(self):
        self.libro = Libro.objects.create(titulo="Prueba", precio="150.00")
        self.inv = Inventario.objects.create(libro=self.libro, cantidad=10)
        self.gateway = Mock()
        self.gateway.pagar.return_value = True
        self.service = CompraRapidaService(self.gateway)

    def test_total_stock_y_orden(self):
        self.assertEqual(self.service.procesar(self.libro.pk), Decimal("178.50"))
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.cantidad, 9)
        self.assertEqual(Orden.objects.get().total, Decimal("178.50"))
        self.gateway.pagar.assert_called_once_with(Decimal("178.50"))

    def test_sin_stock_no_cobra(self):
        self.inv.cantidad = 0
        self.inv.save()
        with self.assertRaises(ValueError):
            self.service.procesar(self.libro.pk)
        self.assertFalse(Orden.objects.exists())
        self.gateway.pagar.assert_not_called()

    def test_rechazo_revierte(self):
        self.gateway.pagar.return_value = False
        with self.assertRaises(ValueError):
            self.service.procesar(self.libro.pk)
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.cantidad, 10)
        self.assertFalse(Orden.objects.exists())

    def test_error_gateway_revierte(self):
        self.gateway.pagar.side_effect = OSError("Disco no disponible")
        with self.assertRaises(OSError):
            self.service.procesar(self.libro.pk)
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.cantidad, 10)
        self.assertFalse(Orden.objects.exists())

    def test_get_no_compra(self):
        response = self.client.get(f"/compra-rapida/{self.libro.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertEqual(response.context["total"], Decimal("178.50"))
        self.assertFalse(Orden.objects.exists())

    def test_post_delega(self):
        with patch("tienda_app.views.servicio_compra", self.service):
            response = self.client.post(f"/compra-rapida/{self.libro.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "178.50")
        self.assertEqual(Orden.objects.count(), 1)

    def test_post_sin_stock(self):
        self.inv.cantidad = 0
        self.inv.save()
        response = self.client.post(f"/compra-rapida/{self.libro.pk}/")
        self.assertEqual(response.status_code, 400)

    def test_libro_inexistente(self):
        for metodo in (self.client.get, self.client.post):
            self.assertEqual(metodo("/compra-rapida/99999/").status_code, 404)

    def test_metodo_no_permitido(self):
        self.assertEqual(self.client.put(f"/compra-rapida/{self.libro.pk}/").status_code, 405)

    def test_auditoria_tres_libros(self):
        with TemporaryDirectory() as carpeta:
            with override_settings(BASE_DIR=Path(carpeta)):
                with patch.dict("os.environ", {"ESTUDIANTE_NOMBRE": "PRUEBA UNITARIA"}):
                    service = CompraRapidaService(BancoNacionalProcesador())
                    for precio in ("150.00", "200.00", "120.00"):
                        libro = Libro.objects.create(titulo=precio, precio=precio)
                        Inventario.objects.create(libro=libro, cantidad=10)
                        service.procesar(libro.pk)
            lineas = (Path(carpeta) / "pagos_locales_PRUEBA_UNITARIA.log").read_text().splitlines()
            self.assertEqual(len(lineas), 3)
            self.assertEqual([x.rsplit("$", 1)[1] for x in lineas], ["178.50", "238.00", "142.80"])
