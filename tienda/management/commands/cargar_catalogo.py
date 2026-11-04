import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from tienda.models import Equipo, Producto

RUTA_POR_DEFECTO = Path(__file__).resolve().parents[2] / "data" / "catalogo.csv"


class Command(BaseCommand):
    help = "Carga equipos y camisetas desde un CSV (por defecto tienda/data/catalogo.csv)."

    def add_arguments(self, parser):
        parser.add_argument("archivo", nargs="?", default=str(RUTA_POR_DEFECTO))

    def handle(self, *args, **opts):
        ruta = Path(opts["archivo"])
        if not ruta.exists():
            raise CommandError(f"No existe el archivo: {ruta}")

        nuevos = actualizados = 0
        with ruta.open(newline="", encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                equipo, _ = Equipo.objects.get_or_create(
                    nombre=fila["equipo"],
                    defaults={"tipo": fila["tipo_equipo"], "pais": fila["pais"]},
                )
                _, creado = Producto.objects.update_or_create(
                    equipo=equipo,
                    nombre=fila["nombre"],
                    temporada=fila["temporada"],
                    defaults={
                        "equipacion": fila["equipacion"],
                        "precio": fila["precio"],
                        "color_principal": fila["color_principal"],
                        "color_secundario": fila["color_secundario"],
                    },
                )
                nuevos += creado
                actualizados += not creado

        self.stdout.write(self.style.SUCCESS(
            f"Listo: {nuevos} camisetas nuevas, {actualizados} actualizadas."))