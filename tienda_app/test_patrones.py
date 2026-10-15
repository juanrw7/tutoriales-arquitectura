from decimal import Decimal
from unittest.mock import Mock, patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from .domain.builders import OrdenBuilder
from .infra.factories import MockPaymentProcessor, PaymentFactory
from .infra.gateways import BancoNacionalProcesador
from .models import DetalleOrden, Inventario, Libro, Orden
from .services import CompraService


class PatronesTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(username="juan_prueba")
        self.libros = [Libro.objects.create(titulo=titulo, precio=precio) for titulo, precio in [("A", "150.00"), ("B", "200.00")]]
        for libro in self.libros:
            Inventario.objects.create(libro=libro, cantidad=10)
        self.gateway = Mock()
        self.gateway.pagar.return_value = True
        self.service = CompraService(self.gateway)

    def builder(self):
        return OrdenBuilder().con_usuario(self.usuario).con_productos(self.libros).para_envio("Medellin")

    def test_factory_mock(self):
        with patch.dict("os.environ", {"PAYMENT_PROVIDER": "MOCK"}):
            self.assertIsInstance(PaymentFactory.get_processor(), MockPaymentProcessor)

    def test_factory_default_y_fallback(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertIsInstance(PaymentFactory.get_processor(), BancoNacionalProcesador)
        with patch.dict("os.environ", {"PAYMENT_PROVIDER": "OTRO"}):
            self.assertIsInstance(PaymentFactory.get_processor(), BancoNacionalProcesador)

    def test_mock_no_escribe_archivo(self):
        with patch("pathlib.Path.open") as archivo, patch("builtins.print") as salida:
            self.assertTrue(MockPaymentProcessor().pagar(Decimal("416.50")))
        archivo.assert_not_called()
        self.assertIn("[DEBUG] Mock Payment", salida.call_args.args[0])

    def test_builder_productos_direccion_total(self):
        orden = self.builder().build()
        self.assertEqual(orden.usuario, self.usuario)
        self.assertEqual(orden.direccion_envio, "Medellin")
        self.assertEqual(orden.total, Decimal("416.50"))
        self.assertIsNone(orden.libro)
        self.assertEqual(orden.detalles.count(), 2)

    def test_builder_sin_usuario(self):
        with self.assertRaises(ValueError):
            OrdenBuilder().con_productos(self.libros).build()
        self.assertFalse(Orden.objects.exists())

    def test_builder_sin_productos(self):
        with self.assertRaises(ValueError):
            OrdenBuilder().con_usuario(self.usuario).build()
        self.assertFalse(Orden.objects.exists())

    def test_builder_reset_exito_y_error(self):
        builder = self.builder()
        builder.build()
        with self.assertRaises(ValueError):
            builder.build()
        with self.assertRaises(ValueError):
            builder.con_productos(self.libros).build()
        self.assertIsNone(builder._usuario)
        self.assertEqual(builder._items, [])

    def test_builder_cantidades_invalidas(self):
        for cantidad in [0, -1, True, 1.5]:
            with self.assertRaises(ValueError):
                self.builder().con_cantidad(cantidad).build()
        self.assertFalse(Orden.objects.exists())

    def test_builder_producto_repetido(self):
        orden = OrdenBuilder().con_usuario(self.usuario).con_productos([self.libros[0]]*2).build()
        self.assertEqual(orden.total, Decimal("357.00"))
        self.assertEqual(orden.detalles.get().cantidad, 2)

    def test_iva_sobre_subtotal(self):
        libro = Libro.objects.create(titulo="Centavos", precio="0.03")
        orden = OrdenBuilder().con_usuario(self.usuario).con_productos([libro]*3).build()
        self.assertEqual(orden.total, Decimal("0.11"))

    def test_service_compra_multiple(self):
        mensaje = self.service.ejecutar_proceso_compra(self.usuario, self.libros, "Medellin")
        self.assertIn("procesada exitosamente", mensaje)
        self.gateway.pagar.assert_called_once_with(Decimal("416.50"))
        self.assertEqual(list(Inventario.objects.values_list("cantidad", flat=True)), [9, 9])

    def test_service_rechazo_revierte(self):
        self.gateway.pagar.return_value = False
        with self.assertRaises(ValueError):
            self.service.ejecutar_proceso_compra(self.usuario, self.libros, "Medellin")
        self.assertFalse(Orden.objects.exists())
        self.assertFalse(DetalleOrden.objects.exists())
        self.assertEqual(list(Inventario.objects.values_list("cantidad", flat=True)), [10, 10])

    def test_service_sin_stock_no_paga(self):
        Inventario.objects.filter(libro=self.libros[1]).update(cantidad=0)
        with self.assertRaises(ValueError):
            self.service.ejecutar_proceso_compra(self.usuario, self.libros, "Medellin")
        self.assertFalse(Orden.objects.exists())
        self.gateway.pagar.assert_not_called()
        self.assertEqual(Inventario.objects.get(libro=self.libros[0]).cantidad, 10)

    def test_service_error_gateway_revierte(self):
        self.gateway.pagar.side_effect = OSError("Error de infraestructura")
        with self.assertRaises(OSError):
            self.service.ejecutar_proceso_compra(self.usuario, self.libros, "Medellin")
        self.assertFalse(Orden.objects.exists())
        self.assertEqual(list(Inventario.objects.values_list("cantidad", flat=True)), [10, 10])

    def test_vista_factory_mock(self):
        with patch.dict("os.environ", {"PAYMENT_PROVIDER": "MOCK"}), patch("builtins.print") as salida:
            response = self.client.post("/compra-patrones/", {"usuario_id": self.usuario.pk, "libros": [x.pk for x in self.libros], "direccion": "Medellin"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("[DEBUG] Mock Payment", salida.call_args.args[0])
        self.assertEqual(Orden.objects.get().detalles.count(), 2)
