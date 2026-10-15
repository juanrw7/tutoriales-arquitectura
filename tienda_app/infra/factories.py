import os
from .gateways import BancoNacionalProcesador
from ..domain.interfaces import ProcesadorPago


class MockPaymentProcessor(ProcesadorPago):
    def pagar(self, monto) -> bool:
        print(
            f"[DEBUG] Mock Payment: Procesando pago de ${monto:.2f} "
            "sin cargo real.", flush=True
        )
        return True


class PaymentFactory:
    @staticmethod
    def get_processor() -> ProcesadorPago:
        provider = os.getenv("PAYMENT_PROVIDER", "BANCO").strip().upper()
        if provider == "MOCK":
            return MockPaymentProcessor()
        # Mismo comportamiento por defecto que el tutorial.
        return BancoNacionalProcesador()
