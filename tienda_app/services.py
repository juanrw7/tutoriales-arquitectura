from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from .domain.builders import OrdenBuilder
from .domain.interfaces import ProcesadorPago
from .domain.logic import CalculadorImpuestos
from .models import Inventario, Libro, Orden


class CompraService:
    def __init__(self, procesador_pago: ProcesadorPago):
        self.procesador = procesador_pago

    def obtener_detalle_producto(self, libro_id):
        libro = get_object_or_404(Libro, pk=libro_id)
        return {"libro": libro, "total":
                CalculadorImpuestos.obtener_total_con_iva(libro.precio)}

    def obtener_contexto_patrones(self):
        return {"libros": Libro.objects.order_by("id"),
                "usuarios": get_user_model().objects.order_by("id")}

    def comprar_desde_ids(self, usuario_id, libro_ids, direccion):
        try:
            usuario_id = int(usuario_id)
            ids = [int(pk) for pk in libro_ids]
        except (TypeError, ValueError):
            raise ValueError("Seleccione usuario y productos validos.")
        usuario = get_object_or_404(get_user_model(), pk=usuario_id)
        libros = Libro.objects.in_bulk(ids)
        if len(libros) != len(set(ids)):
            raise ValueError("Hay productos inexistentes.")
        return self.ejecutar_proceso_compra(
            usuario, [libros[pk] for pk in ids], direccion
        )

    @transaction.atomic
    def ejecutar_proceso_compra(self, usuario, lista_productos, direccion):
        orden = (OrdenBuilder().con_usuario(usuario)
                 .con_productos(lista_productos).para_envio(direccion).build())
        self._finalizar(orden)
        return f"Orden {orden.id} procesada exitosamente."

    @transaction.atomic
    def ejecutar_compra(self, libro_id, cantidad=1, direccion="", usuario=None):
        libro = get_object_or_404(Libro, pk=libro_id)
        orden = (OrdenBuilder().con_usuario(usuario).con_libro(libro)
                 .con_cantidad(cantidad).para_envio(direccion).build())
        self._finalizar(orden)
        return orden.total

    def _finalizar(self, orden):
        detalles = list(orden.detalles.order_by("libro_id"))
        inventarios = []
        for detalle in detalles:
            inv = get_object_or_404(
                Inventario.objects.select_for_update(), libro_id=detalle.libro_id
            )
            if inv.cantidad < detalle.cantidad:
                raise ValueError("No hay suficiente stock para completar la compra.")
            inventarios.append((inv, detalle.cantidad))
        for inv, cantidad in inventarios:
            inv.cantidad -= cantidad
            inv.save(update_fields=["cantidad"])
        if not self.procesador.pagar(orden.total):
            raise ValueError("Error en la pasarela de pagos.")


class CompraRapidaService:
    """Orquesta compras unitarias; el gateway se recibe por inyeccion."""

    def __init__(self, procesador_pago: ProcesadorPago):
        self.procesador_pago = procesador_pago

    def obtener_detalle_producto(self, libro_id):
        libro = get_object_or_404(Libro, pk=libro_id)
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        return {"libro": libro, "total": total}

    @transaction.atomic
    def procesar(self, libro_id):
        libro = get_object_or_404(Libro, pk=libro_id)
        inv = get_object_or_404(
            Inventario.objects.select_for_update(), libro=libro
        )
        if inv.cantidad <= 0:
            raise ValueError("No hay existencias.")
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        # Primero persistimos; un rechazo revierte orden e inventario.
        Orden.objects.create(libro=libro, total=total)
        inv.cantidad -= 1
        inv.save(update_fields=["cantidad"])
        if not self.procesador_pago.pagar(total):
            raise ValueError("El pago fue rechazado.")
        return total
