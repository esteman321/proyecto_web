"""
Crea las carpetas de escudos y lista qué archivos faltan.

    python manage.py escudos

Cada escudo es un archivo con el nombre del equipo/liga "en minúsculas y con guiones":
    static/escudos/ligas/premier-league.png
    static/escudos/equipos/bayern-munich.svg
Formatos aceptados: svg, png, webp, jpg.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from tienda.models import Equipo

EXT = ("svg", "png", "webp", "jpg", "jpeg")


class Command(BaseCommand):
    help = "Crea static/escudos/ y lista los escudos que faltan."

    def handle(self, *args, **opts):
        base = Path(settings.BASE_DIR) / "static" / "escudos"
        for sub in ("ligas", "equipos"):
            (base / sub).mkdir(parents=True, exist_ok=True)

        equipos = Equipo.objects.filter(productos__activo=True).distinct().order_by("nombre")
        ligas = sorted({e.grupo for e in equipos})

        faltan = 0
        for titulo, carpeta, nombres in (("LIGAS", "ligas", ligas),
                                         ("EQUIPOS", "equipos", [e.nombre for e in equipos])):
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{titulo}  ->  {base / carpeta}"))
            for nombre in nombres:
                slug = slugify(nombre)
                existe = next((f"{slug}.{x}" for x in EXT if (base / carpeta / f"{slug}.{x}").exists()), None)
                if existe:
                    self.stdout.write(f"  [ok]    {existe}")
                else:
                    faltan += 1
                    self.stdout.write(self.style.WARNING(f"  [falta] {slug}.png      <- {nombre}"))
        self.stdout.write(self.style.SUCCESS(
            f"\nFaltan {faltan} escudos. Mientras tanto se muestran las iniciales del equipo."
            if faltan else "\nTodos los escudos están."))