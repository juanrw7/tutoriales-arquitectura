from decimal import Decimal, ROUND_HALF_UP


class CalculadorImpuestos:
    FACTOR_IVA = Decimal("1.19")

    @classmethod
    def obtener_total_con_iva(cls, precio_base):
        return (Decimal(str(precio_base)) * cls.FACTOR_IVA).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
