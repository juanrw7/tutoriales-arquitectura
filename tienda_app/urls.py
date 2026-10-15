from django.urls import path
from .api.views import CompraAPIView, ProductosAPIView
from .views import (SaludView, InventarioView, CompraPatronesView, CompraView, CompraRapidaView,
                    CompraRapidaIntermediaView, compra_rapida_fbv)

urlpatterns = [
    path("api/v1/productos/", ProductosAPIView.as_view(), name="api_productos"),
    path("health/", SaludView.as_view(), name="salud"),
    path("inventario/", InventarioView.as_view(), name="inventario"),
    path("compra-patrones/", CompraPatronesView.as_view(), name="compra_patrones"),
    path("compra/<int:libro_id>/", CompraView.as_view(), name="finalizar_compra"),
    path("api/v1/comprar/", CompraAPIView.as_view(), name="api_comprar"),
    path("compra-rapida/fbv/<int:libro_id>/", compra_rapida_fbv, name="compra_fbv"),
    path("compra-rapida/cbv/<int:libro_id>/", CompraRapidaIntermediaView.as_view(), name="compra_cbv"),
    path("compra-rapida/<int:libro_id>/", CompraRapidaView.as_view(), name="compra_rapida"),
]
