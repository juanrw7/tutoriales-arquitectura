import os
import re
import unicodedata
from django.conf import settings
from django.utils import timezone
from ..domain.interfaces import ProcesadorPago


class BancoNacionalProcesador(ProcesadorPago):
    def pagar(self, monto):
        nombre = os.getenv("ESTUDIANTE_NOMBRE", "Juan Manuel Ramirez")
        nombre = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
        nombre = re.sub(r"[^A-Z0-9]+", "_", nombre.upper()).strip("_")
        if not nombre:
            raise ValueError("Debe indicar su nombre y apellido reales.")
        carpeta = getattr(settings, "PAYMENTS_LOG_DIR", settings.BASE_DIR)
        carpeta.mkdir(parents=True, exist_ok=True)
        archivo = carpeta / f"pagos_locales_{nombre}.log"
        fecha = timezone.localtime().isoformat(timespec="microseconds")
        with archivo.open("a", encoding="utf-8") as log:
            log.write(f"[{fecha}] Transaccion exitosa por: ${monto:.2f}\n")
        return True
