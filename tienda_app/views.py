from django.shortcuts import render
from django.views import View

from .infra.factories import PaymentFactory
from .services import CompraService


class CompraView(View):
    """
    CBV: Vista Basada en Clases.
    Actúa como un "Portero": recibe la petición y delega al servicio.
    """

    template_name = 'tienda_app/compra.html'

    def setup_service(self):
        gateway = PaymentFactory.get_processor()
        return CompraService(procesador_pago=gateway)

    def get(self, request, libro_id):
        servicio = self.setup_service()
        contexto = servicio.obtener_detalle_producto(libro_id)
        return render(request, self.template_name, contexto)

    def post(self, request, libro_id):
        servicio = self.setup_service()
        try:
            total = servicio.ejecutar_compra(libro_id, cantidad=1)
            return render(
                request,
                self.template_name,
                {
                    'mensaje_exito': f"¡Gracias por su compra! Total: ${total}",
                    'total': total,
                },
            )
        except (ValueError, Exception) as e:
            return render(request, self.template_name, {'error': str(e)}, status=400)


import datetime
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Inventario, Libro, Orden
from .services import CompraRapidaService


def compra_rapida_fbv(request, libro_id):
    """Paso 1: ejemplo deliberado de responsabilidades mezcladas."""
    libro = get_object_or_404(Libro, pk=libro_id)
    if request.method == "POST":
        inventario = Inventario.objects.get(libro=libro)
        if inventario.cantidad <= 0:
            return HttpResponse("Sin stock", status=400)
        total = float(libro.precio) * 1.19
        with open("pagos_manuales.log", "a", encoding="utf-8") as archivo:
            archivo.write(f"[{datetime.datetime.now()}] Pago FBV: ${total}\n")
        inventario.cantidad -= 1
        inventario.save()
        Orden.objects.create(libro=libro, total=total)
        return HttpResponse(f"Compra exitosa: {libro.titulo}")
    return render(request, "tienda_app/compra_rapida.html", {
        "libro": libro, "total": float(libro.precio) * 1.19,
        "etapa": "FBV Spaghetti",
    })


class CompraRapidaIntermediaView(View):
    """Paso 2: separa GET/POST, pero mantiene negocio en la vista."""
    def get(self, request, libro_id):
        libro = get_object_or_404(Libro, pk=libro_id)
        return render(request, "tienda_app/compra_rapida.html", {
            "libro": libro, "total": float(libro.precio) * 1.19,
            "etapa": "CBV intermedia",
        })

    def post(self, request, libro_id):
        libro = get_object_or_404(Libro, pk=libro_id)
        inv = get_object_or_404(Inventario, libro=libro)
        if inv.cantidad <= 0:
            return HttpResponse("Sin stock", status=400)
        total = float(libro.precio) * 1.19
        with open("pagos_intermedios.log", "a", encoding="utf-8") as archivo:
            archivo.write(f"[{datetime.datetime.now()}] Pago CBV: ${total}\n")
        inv.cantidad -= 1
        inv.save()
        Orden.objects.create(libro=libro, total=total)
        return HttpResponse("Comprado via CBV intermedia")


# Punto de composicion: la implementacion concreta se conecta al servicio.
servicio_compra = CompraRapidaService(PaymentFactory.get_processor())


class CompraRapidaView(View):
    def get(self, request, libro_id):
        return render(request, "tienda_app/compra_rapida.html", servicio_compra.obtener_detalle_producto(libro_id))
    def post(self, request, libro_id):
        try:
            total = servicio_compra.procesar(libro_id)
            return HttpResponse(f"Compra exitosa. Total: ${total}")
        except ValueError as error:
            return HttpResponse(str(error), status=400)


class CompraPatronesView(View):
    template_name = "tienda_app/compra_patrones.html"

    def setup_service(self):
        return CompraService(PaymentFactory.get_processor())

    def get(self, request):
        return render(request, self.template_name,
                      self.setup_service().obtener_contexto_patrones())

    def post(self, request):
        try:
            mensaje = self.setup_service().comprar_desde_ids(
                request.POST.get("usuario_id"), request.POST.getlist("libros"),
                request.POST.get("direccion", ""),
            )
            return HttpResponse(mensaje)
        except ValueError as error:
            return HttpResponse(str(error), status=400)


class InventarioView(View):
    def get(self, request):
        libros = Libro.objects.select_related("inventario").order_by("id")
        return render(request, "tienda_app/inventario.html", {"libros": libros})
