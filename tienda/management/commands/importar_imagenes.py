"""
Importa camisetas desde una carpeta organizada como:

    Fan - Player/
      Bundesliga/
        Bayern Munich/
          producto_018.jpeg
          producto_019.jpeg
      La Liga/
        Real Madrid/
          ...

Cada foto crea un producto por cada versión indicada (por defecto Fan y Player),
todos compartiendo el mismo archivo de imagen. Si el nombre del archivo trae
home/away/third/retro o una temporada (2024-25), también las detecta.

Uso:
    python manage.py importar_imagenes "C:\\ruta\\Fan - Player" --dry-run
    python manage.py importar_imagenes "C:\\ruta\\Fan - Player" --temporada 26/27
    python manage.py importar_imagenes "C:\\ruta\\Retro" --retro --versiones fan   # camisetas retro
"""
import re
import unicodedata
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from tienda.models import Equipo, Producto

EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp"}
VERSIONES = {"fan", "player"}
RETRO = {"retro", "vintage", "classic"}
CLAVES = [  # el orden importa: lo más específico primero
    ("tercera", {"third", "tercera", "3rd", "alternativa"}),
    ("visitante", {"away", "visitante", "visita"}),
    ("local", {"home", "local"}),
]
ESPALDA = {"back", "atras", "detras", "trasera", "espalda", "reverso", "rear"}


def normalizar(texto):
    """Minúsculas, sin tildes ni símbolos: 'Bayern_München' -> 'bayern munchen'."""
    ascii_ = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", ascii_.lower()).strip()


def es_espalda(ruta):
    return bool(set(normalizar(ruta.stem).split()) & ESPALDA)


def detectar_equipacion(stem):
    """Devuelve local/visitante/tercera si el nombre lo dice; si no, None."""
    palabras = set(normalizar(stem).split())
    for equipacion, claves in CLAVES:
        if palabras & claves:
            return equipacion
    return None


def detectar_temporada(stem, por_defecto):
    m = re.search(r"((?:19|20)\d{2})\s*[-_/]\s*((?:19|20)?\d{2})(?!\d)", stem)
    if m:
        return f"{m.group(1)[2:]}/{m.group(2)[-2:]}"
    m = re.search(r"(?<!\d)((?:19|20)\d{2})(?!\d)", stem)
    return m.group(1) if m else por_defecto


def numero_modelo(stem):
    m = re.search(r"(\d+)\D*$", stem)
    return m.group(1) if m else stem


class Command(BaseCommand):
    help = "Importa imágenes de camisetas desde carpetas liga/equipo/archivo."

    def add_arguments(self, parser):
        parser.add_argument("carpeta")
        parser.add_argument("--dry-run", action="store_true", help="Muestra qué haría sin guardar nada.")
        parser.add_argument("--reemplazar", action="store_true", help="Reemplaza imágenes ya asignadas.")
        parser.add_argument("--temporada", default="26/27", help="Temporada si el archivo no la indica.")
        parser.add_argument("--retro", action="store_true", help="Marca todo lo importado como retro.")
        parser.add_argument("--versiones", default="fan,player", help="Versiones a crear por foto.")
        parser.add_argument("--precio-fan", type=int, default=199000)
        parser.add_argument("--precio-player", type=int, default=279000)

    def handle(self, *args, **o):
        raiz = Path(o["carpeta"])
        if not raiz.is_dir():
            raise CommandError(f"No existe la carpeta: {raiz}")
        versiones = [v.strip().lower() for v in o["versiones"].split(",") if v.strip()]
        if not versiones or set(versiones) - VERSIONES:
            raise CommandError("--versiones solo acepta: fan, player (separadas por coma).")
        precios = {"fan": o["precio_fan"], "player": o["precio_player"]}
        dry = o["dry_run"]

        archivos = [p for p in raiz.rglob("*") if p.suffix.lower() in EXTENSIONES]
        if not archivos:
            raise CommandError("No encontré imágenes (.jpg, .jpeg, .png, .webp) en esa carpeta.")
        archivos.sort(key=lambda p: str(p))

        existentes = {normalizar(e.nombre): e for e in Equipo.objects.all()}
        stats = dict(equipos=0, productos=0, imagenes=0, omitidas=0, extras=0)

        with transaction.atomic():
            for ruta in archivos:
                if es_espalda(ruta):  # fotos de espalda: por ahora se ignoran
                    stats["extras"] += 1
                    continue

                partes = ruta.relative_to(raiz).parts
                if len(partes) == 3:
                    liga, nombre_equipo = partes[0].replace("_", " ").strip(), partes[1].replace("_", " ").strip()
                elif len(partes) == 2:
                    liga, nombre_equipo = "", partes[0].replace("_", " ").strip()
                else:
                    self.stdout.write(self.style.WARNING(f"  omitida (ruta inesperada): {ruta}"))
                    stats["omitidas"] += 1
                    continue

                clave_equipo = normalizar(nombre_equipo)
                equipo = existentes.get(clave_equipo)
                if equipo is None:
                    equipo = Equipo.objects.create(nombre=nombre_equipo, tipo="club", liga=liga)
                    existentes[clave_equipo] = equipo
                    stats["equipos"] += 1
                elif liga and not equipo.liga:
                    equipo.liga = liga
                    equipo.save(update_fields=["liga"])

                es_retro = o["retro"] or bool(set(normalizar(ruta.stem).split()) & RETRO)
                codigo = slugify(ruta.stem)
                if es_retro and not codigo.startswith("retro"):
                    codigo = f"retro-{codigo}"   # evita chocar con producto_001 de otra carpeta
                equipacion = detectar_equipacion(ruta.stem)
                temporada = detectar_temporada(ruta.stem, o["temporada"])
                base = f"{equipo.nombre} {equipacion}" if equipacion else \
                    f"{equipo.nombre} · {'Retro' if es_retro else 'Modelo'} {numero_modelo(ruta.stem)}"
                nombre = base

                self.stdout.write(f"  {liga or '-'} / {equipo.nombre} / {codigo}  ->  {' + '.join(versiones)}")

                ruta_imagen = None  # el primer producto guarda el archivo; los demás lo comparten
                for version in versiones:
                    producto, creado = Producto.objects.get_or_create(
                        equipo=equipo, codigo=codigo, version=version,
                        defaults={"nombre": nombre, "equipacion": equipacion or "sin_definir",
                                  "retro": es_retro, "temporada": temporada, "precio": precios[version]},
                    )
                    stats["productos"] += creado

                    if producto.imagen and not o["reemplazar"]:
                        ruta_imagen = ruta_imagen or producto.imagen.name
                        continue
                    if not dry:
                        if ruta_imagen is None:
                            archivo = f"{slugify(equipo.nombre)}-{codigo}{ruta.suffix.lower()}"
                            with ruta.open("rb") as f:
                                producto.imagen.save(archivo, File(f), save=True)
                            ruta_imagen = producto.imagen.name
                        else:
                            producto.imagen.name = ruta_imagen
                            producto.save(update_fields=["imagen"])
                    stats["imagenes"] += 1

            if dry:
                transaction.set_rollback(True)

        etiqueta = "SIMULACIÓN (no se guardó nada)" if dry else "Listo"
        self.stdout.write(self.style.SUCCESS(
            f"{etiqueta}: {stats['productos']} productos nuevos, {stats['imagenes']} imágenes asignadas, "
            f"{stats['equipos']} equipos nuevos, {stats['extras']} fotos de espalda ignoradas, "
            f"{stats['omitidas']} omitidas."))