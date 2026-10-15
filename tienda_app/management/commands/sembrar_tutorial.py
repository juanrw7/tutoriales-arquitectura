from decimal import Decimal
from django.core.management.base import BaseCommand
from tienda_app.models import Libro, Inventario


class Command(BaseCommand):
    help = "Crea tres libros con stock; no restablece compras existentes."

    def handle(self, *args, **options):
        datos = [("Clean Code en Python", "150.00"),
                 ("Arquitectura Limpia", "200.00"),
                 ("Patrones de Diseno", "120.00")]
        for titulo, precio in datos:
            libro, _ = Libro.objects.get_or_create(
                titulo=titulo, defaults={"precio": Decimal(precio)}
            )
            Inventario.objects.get_or_create(libro=libro, defaults={"cantidad": 10})
            self.stdout.write(f"ID {libro.pk}: {titulo}")
