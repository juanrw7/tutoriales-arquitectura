import logging
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import OrdenInputSerializer
from tienda_app.services import CompraService
from tienda_app.infra.factories import PaymentFactory

logger = logging.getLogger(__name__)


class CompraAPIView(APIView):
    """POST /api/v1/comprar/: adapta JSON al servicio ya existente."""
    serializer_class = OrdenInputSerializer

    def get_serializer(self, *args, **kwargs):
        # Permite mostrar tambien el formulario de la interfaz web de DRF.
        return self.serializer_class(*args, **kwargs)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        datos = serializer.validated_data
        try:
            gateway = PaymentFactory.get_processor()
            servicio = CompraService(procesador_pago=gateway)
            usuario = request.user if request.user.is_authenticated else None
            resultado = servicio.ejecutar_compra(
                libro_id=datos["libro_id"],
                cantidad=datos["cantidad"],
                direccion=datos["direccion_envio"],
                usuario=usuario,
            )
            return Response({"estado": "exito", "mensaje":
                             f"Orden creada. Total: {resultado}"},
                            status=status.HTTP_201_CREATED)
        except Http404:
            # DRF transforma el error de recurso ausente en un 404 JSON.
            raise
        except ValueError as error:
            return Response({"error": str(error)},
                            status=status.HTTP_409_CONFLICT)
        except Exception:
            logger.exception("Error inesperado al comprar por API")
            return Response({"error": "Error interno"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductosAPIView(APIView):
    """Catalogo v1 del monolito para probar coexistencia con Flask."""
    def get(self, request):
        from tienda_app.models import Libro
        from .serializers import LibroSerializer
        libros = Libro.objects.select_related("inventario").order_by("id")
        return Response(LibroSerializer(libros, many=True).data,
                        headers={"X-Backend": "Django-v1"})
