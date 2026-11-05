"""
Importa camisetas desde carpetas y las reparte en las secciones de la tienda:

    Clubes       -> carpeta "Fan - Player" (equipo con tipo="club")
    Selecciones  -> carpeta/equipo que sea una selección (equipo con tipo="seleccion")
    Retro        -> carpeta "Retro" (producto con retro=True)

Estructuras que entiende (las carpetas contenedoras como "Fan - Player", "Retro"
o "media" se ignoran, así que puedes apuntar a .\\media o a una subcarpeta):

    Fan - Player/Brasileirao/Atletico Mineiro/producto_008.jpg   -> club
    Fan - Player/Liga Holandesa/producto_032.jpeg                 -> club "Varios · Liga Holandesa"
    Selecciones/producto_010.jpg                                  -> selección "Varios · Selecciones"
    Selecciones/Argentina/producto_001.jpg                        -> selección Argentina
    Retro/Serie A/AC Milan/producto_003.jpg                       -> club, retro
    Retro/Selecciones/Brasil/producto_004.jpg                     -> selección, retro

Cada foto crea un producto por versión (Fan y Player por defecto; en Retro solo Fan),
todos compartiendo el mismo archivo de imagen.

Uso:
    python manage.py importar_imagenes ".\\media\\Fan - Player" --dry-run
    python manage.py importar_imagenes ".\\media\\Selecciones" --dry-run
    python manage.py importar_imagenes ".\\media\\Retro" --dry-run
    python manage.py importar_imagenes ".\\media\\Fan - Player" --temporada 26/27
    python manage.py importar_imagenes ".\\media\\Mundial" --selecciones   # fuerza selecciones
"""
import re
import unicodedata
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from tienda.models import Equipo, Producto

# --- Ajusta estos valores a tu proyecto -------------------------------------
CAMPO_IMAGEN = "imagen"        # nombre real del ImageField en tu modelo Producto
TIPO_CLUB = "club"             # valor de Equipo.tipo para clubes
TIPO_SELECCION = "seleccion"   # valor de Equipo.tipo para selecciones (revisa tus choices)
SIN_EQUIPO = "Varios"          # equipo genérico para fotos sueltas (en una liga o en Selecciones)
# -----------------------------------------------------------------------------

EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp"}
VERSIONES = {"fan", "player"}
RETRO = {"retro", "vintage", "classic"}
CLAVES = [  # el orden importa: lo más específico primero
    ("tercera", {"third", "tercera", "3rd", "alternativa"}),
    ("visitante", {"away", "visitante", "visita"}),
    ("local", {"home", "local"}),
]
ESPALDA = {"back", "atras", "detras", "trasera", "espalda", "reverso", "rear"}

# Carpetas que solo agrupan (no son liga ni equipo); se ignoran al leer la ruta
CONTENEDORES = {"fan player", "fan", "player", "retro", "media", "camisetas", "fan y player"}

# Si una carpeta suelta contiene alguna de estas palabras, se trata como LIGA
PALABRAS_LIGA = {
    "liga", "league", "serie", "bundesliga", "ligue", "premier", "eredivisie",
    "brasileirao", "primeira", "lig", "championship", "mls",
}

# Palabras en el nombre de una carpeta que indican "esto son selecciones"
PALABRAS_SELECCION = {
    "seleccion", "selecciones", "seleccionados", "national", "nacional", "nacionales",
    "nations", "internacional", "internacionales", "mundial", "eurocopa", "copa america",
}

# Respaldo: si el equipo se llama exactamente como un país, se considera selección
PAISES = {
    "argentina", "brasil", "brazil", "colombia", "uruguay", "chile", "peru", "ecuador",
    "paraguay", "bolivia", "venezuela", "mexico", "usa", "estados unidos", "canada",
    "costa rica", "espana", "spain", "francia", "france", "alemania", "germany",
    "italia", "italy", "portugal", "inglaterra", "england", "holanda", "paises bajos",
    "netherlands", "belgica", "belgium", "croacia", "croatia", "suiza", "dinamarca",
    "suecia", "noruega", "polonia", "serbia", "escocia", "gales", "turquia", "japon",
    "japan", "corea del sur", "south korea", "australia", "marruecos", "morocco",
    "senegal", "nigeria", "ghana", "camerun", "egipto", "tunez", "argelia",
    "arabia saudita", "iran", "catar", "qatar",
}


def normalizar(texto):
    """Minúsculas, sin tildes ni símbolos: 'Bayern_München' -> 'bayern munchen'."""
    ascii_ = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", ascii_.lower()).strip()


def palabras(texto):
    return set(normalizar(texto).split())


def es_espalda(ruta):
    return bool(palabras(ruta.stem) & ESPALDA)


def es_liga(nombre):
    return bool(palabras(nombre) & PALABRAS_LIGA)


def es_carpeta_seleccion(nombre):
    return bool(palabras(nombre) & PALABRAS_SELECCION)


def carpetas_de(ruta, raiz):
    """Carpetas entre la raíz y el archivo, sin las 'contenedoras'."""
    carpetas = [c.replace("_", " ").strip() for c in ruta.relative_to(raiz).parts[:-1]]
    return [c for c in carpetas if normalizar(c) not in CONTENEDORES]


def nombres_de_ruta(ruta, raiz):
    """Todos los nombres de carpeta relevantes (incluida la raíz) para detectar retro/selecciones."""
    return [raiz.name] + list(ruta.relative_to(raiz).parts[:-1])


def detectar_equipacion(stem):
    """Devuelve local/visitante/tercera si el nombre lo dice; si no, None."""
    pals = palabras(stem)
    for equipacion, claves in CLAVES:
        if pals & claves:
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
    help = "Importa imágenes de camisetas y las reparte en Clubes, Selecciones y Retro."

    def add_arguments(self, parser):
        parser.add_argument("carpeta")
        parser.add_argument("--dry-run", action="store_true", help="Muestra qué haría sin guardar nada.")
        parser.add_argument("--reemplazar", action="store_true", help="Reemplaza imágenes ya asignadas.")
        parser.add_argument("--temporada", default="26/27", help="Temporada si el archivo no la indica.")
        parser.add_argument("--retro", action="store_true", help="Fuerza que todo lo importado sea retro.")
        parser.add_argument("--selecciones", action="store_true", help="Fuerza que todo sean selecciones.")
        parser.add_argument("--versiones", default=None,
                            help="Versiones por foto (fan,player). Por defecto: fan+player; en retro solo fan.")
        parser.add_argument("--precio-fan", type=int, default=199000)
        parser.add_argument("--precio-player", type=int, default=279000)

    def handle(self, *args, **o):
        raiz = Path(o["carpeta"]).resolve()
        if not raiz.is_dir():
            raise CommandError(f"No existe la carpeta: {raiz}")

        versiones_arg = None
        if o["versiones"]:
            versiones_arg = [v.strip().lower() for v in o["versiones"].split(",") if v.strip()]
            if not versiones_arg or set(versiones_arg) - VERSIONES:
                raise CommandError("--versiones solo acepta: fan, player (separadas por coma).")

        precios = {"fan": o["precio_fan"], "player": o["precio_player"]}
        dry = o["dry_run"]

        archivos = [p for p in raiz.rglob("*") if p.suffix.lower() in EXTENSIONES]
        if not archivos:
            raise CommandError("No encontré imágenes (.jpg, .jpeg, .png, .webp) en esa carpeta.")
        archivos.sort(key=lambda p: str(p))

        existentes = {normalizar(e.nombre): e for e in Equipo.objects.all()}
        stats = dict(equipos=0, productos=0, imagenes=0, omitidas=0, extras=0,
                     selecciones=0, retro=0, actualizados=0)

        with transaction.atomic():
            for ruta in archivos:
                if es_espalda(ruta):  # fotos de espalda: por ahora se ignoran
                    stats["extras"] += 1
                    continue

                # --- liga / equipo según las carpetas -------------------------------
                carpetas = carpetas_de(ruta, raiz)
                # Las carpetas tipo "Selecciones" son categoría, no liga ni equipo
                carpetas_utiles = [c for c in carpetas if not es_carpeta_seleccion(c)]
                en_carpeta_selecciones = len(carpetas_utiles) != len(carpetas)
                modo_selecciones = (
                    o["selecciones"]
                    or en_carpeta_selecciones
                    or any(es_carpeta_seleccion(n) for n in nombres_de_ruta(ruta, raiz))
                )

                if len(carpetas_utiles) >= 2:
                    liga, nombre_equipo = carpetas_utiles[-2], carpetas_utiles[-1]
                elif len(carpetas_utiles) == 1:
                    unica = carpetas_utiles[0]
                    if modo_selecciones or normalizar(unica) in PAISES:
                        liga, nombre_equipo = "", unica          # .../Selecciones/Argentina/foto
                    elif es_liga(unica):
                        liga, nombre_equipo = unica, f"{SIN_EQUIPO} · {unica}"   # foto suelta en una liga
                    else:
                        liga, nombre_equipo = "", unica          # .../Equipo/foto
                else:
                    if modo_selecciones:
                        # .../Selecciones/producto_010.jpg -> foto suelta de selecciones
                        liga, nombre_equipo = "", f"{SIN_EQUIPO} · Selecciones"
                    else:
                        self.stdout.write(self.style.WARNING(f"  omitida (sin carpeta de liga/equipo): {ruta}"))
                        stats["omitidas"] += 1
                        continue

                # --- ¿selección o club? ---------------------------------------------
                es_seleccion = modo_selecciones or normalizar(nombre_equipo) in PAISES
                tipo = TIPO_SELECCION if es_seleccion else TIPO_CLUB
                if es_seleccion:
                    liga = ""   # las selecciones no pertenecen a una liga de clubes

                # --- ¿retro? --------------------------------------------------------
                es_retro = (
                    o["retro"]
                    or any(palabras(n) & RETRO for n in nombres_de_ruta(ruta, raiz))
                    or bool(palabras(ruta.stem) & RETRO)
                )

                # --- equipo ----------------------------------------------------------
                clave_equipo = normalizar(nombre_equipo)
                equipo = existentes.get(clave_equipo)
                if equipo is None:
                    equipo = Equipo.objects.create(nombre=nombre_equipo, tipo=tipo, liga=liga)
                    existentes[clave_equipo] = equipo
                    stats["equipos"] += 1
                else:
                    cambios = []
                    if es_seleccion and equipo.tipo != TIPO_SELECCION:
                        equipo.tipo = TIPO_SELECCION   # lo saca de Clubes y lo pasa a Selecciones
                        cambios.append("tipo")
                    if liga and not equipo.liga:
                        equipo.liga = liga
                        cambios.append("liga")
                    if cambios:
                        equipo.save(update_fields=cambios)

                # --- producto(s) -----------------------------------------------------
                codigo = slugify(ruta.stem)
                if es_retro and not codigo.startswith("retro"):
                    codigo = f"retro-{codigo}"   # evita chocar con producto_001 de otra carpeta
                equipacion = detectar_equipacion(ruta.stem)
                temporada = detectar_temporada(ruta.stem, o["temporada"])
                nombre = (f"{equipo.nombre} {equipacion}" if equipacion else
                          f"{equipo.nombre} · {'Retro' if es_retro else 'Modelo'} {numero_modelo(ruta.stem)}")

                versiones = versiones_arg or (["fan"] if es_retro else ["fan", "player"])
                seccion = "Retro" if es_retro else ("Selecciones" if es_seleccion else "Clubes")
                if es_seleccion:
                    stats["selecciones"] += 1
                if es_retro:
                    stats["retro"] += 1

                self.stdout.write(
                    f"  [{seccion}] {liga or '-'} / {equipo.nombre} / {codigo}  ->  {' + '.join(versiones)}")

                ruta_imagen = None  # el primer producto guarda el archivo; los demás lo comparten
                for version in versiones:
                    producto, creado = Producto.objects.get_or_create(
                        equipo=equipo, codigo=codigo, version=version,
                        defaults={"nombre": nombre, "equipacion": equipacion or "sin_definir",
                                  "retro": es_retro, "temporada": temporada, "precio": precios[version]},
                    )
                    stats["productos"] += creado

                    # Si el producto ya existía, corrige su marca de retro
                    if not creado and producto.retro != es_retro:
                        producto.retro = es_retro
                        producto.save(update_fields=["retro"])
                        stats["actualizados"] += 1

                    campo = getattr(producto, CAMPO_IMAGEN)
                    if campo and not o["reemplazar"]:
                        ruta_imagen = ruta_imagen or campo.name
                        continue
                    if not dry:
                        if ruta_imagen is None:
                            archivo = f"{slugify(equipo.nombre)}-{codigo}{ruta.suffix.lower()}"
                            with ruta.open("rb") as f:
                                campo.save(archivo, File(f), save=True)
                            ruta_imagen = campo.name
                        else:
                            campo.name = ruta_imagen
                            producto.save(update_fields=[CAMPO_IMAGEN])
                    stats["imagenes"] += 1

            if dry:
                transaction.set_rollback(True)

        etiqueta = "SIMULACIÓN (no se guardó nada)" if dry else "Listo"
        self.stdout.write(self.style.SUCCESS(
            f"{etiqueta}: {stats['productos']} productos nuevos, {stats['imagenes']} imágenes asignadas, "
            f"{stats['equipos']} equipos nuevos, {stats['selecciones']} fotos de selecciones, "
            f"{stats['retro']} fotos retro, {stats['actualizados']} productos corregidos, "
            f"{stats['extras']} fotos de espalda ignoradas, {stats['omitidas']} omitidas."))