"""
Comando de conveniencia: carga el catálogo completo desde la carpeta media
del proyecto (Fan - Player, Retro y Selecciones).

    python manage.py cargar_catalogo
    python manage.py cargar_catalogo --dry-run
    python manage.py cargar_catalogo --reemplazar   (reasigna imágenes)
"""
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Importa el catálogo desde la carpeta media del proyecto (equivale a importar_imagenes media)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--reemplazar", action="store_true")

    def handle(self, *args, **opts):
        media = settings.BASE_DIR / "media"
        self.stdout.write(f"Importando desde: {media}")
        call_command(
            "importar_imagenes", str(media),
            dry_run=opts["dry_run"], reemplazar=opts["reemplazar"],
        )
