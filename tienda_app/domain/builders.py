from collections import Counter
from decimal import Decimal
from django.db import transaction
from .logic import CalculadorImpuestos
from ..models import DetalleOrden, Libro, Orden


class OrdenBuilder:
    """Construye ordenes con productos; conserva compra unitaria previa."""
    def __init__(self):
        self.reset()

    def reset(self):
        self._usuario = None
        self._items = []
        self._direccion = ""
        self._cantidad = 1
        self._unitaria = False

    def con_usuario(self, usuario):
        self._usuario = usuario
        return self

    def con_productos(self, productos):
        self._items = list(productos)
        self._unitaria = False
        return self

    def para_envio(self, direccion):
        self._direccion = direccion
        return self

    def con_libro(self, libro):
        self._items = [libro]
        self._unitaria = True
        return self

    def con_cantidad(self, cantidad):
        self._cantidad = cantidad
        return self

    @transaction.atomic
    def build(self) -> Orden:
        try:
            if not self._items:
                raise ValueError("Datos insuficientes: faltan productos.")
            if not self._unitaria and (
                self._usuario is None or self._usuario.pk is None
            ):
                raise ValueError("Datos insuficientes: falta un usuario guardado.")
            if (not isinstance(self._cantidad, int)
                    or isinstance(self._cantidad, bool) or self._cantidad < 1):
                raise ValueError("La cantidad debe ser un entero positivo.")
            if not isinstance(self._direccion, str) or len(self._direccion) > 200:
                raise ValueError("La direccion debe ser texto de hasta 200 caracteres.")
            if any(not isinstance(item, Libro) or item.pk is None
                   for item in self._items):
                raise ValueError("Todos los productos deben ser libros guardados.")
            cantidades = Counter(item.pk for item in self._items)
            cantidades = {pk: qty * self._cantidad for pk, qty in cantidades.items()}
            libros = Libro.objects.in_bulk(cantidades)
            if len(libros) != len(cantidades):
                raise ValueError("Uno de los productos ya no existe.")
            subtotal = sum(
                (libros[pk].precio * qty for pk, qty in cantidades.items()),
                Decimal("0.00"),
            )
            total = CalculadorImpuestos.obtener_total_con_iva(subtotal)
            orden = Orden.objects.create(
                usuario=self._usuario,
                libro=self._items[0] if self._unitaria else None,
                total=total,
                direccion_envio=self._direccion,
            )
            DetalleOrden.objects.bulk_create([
                DetalleOrden(orden=orden, libro=libros[pk], cantidad=qty,
                             precio_unitario=libros[pk].precio)
                for pk, qty in cantidades.items()
            ])
            return orden
        finally:
            # Evita arrastrar datos tanto al terminar como al fallar.
            self.reset()
