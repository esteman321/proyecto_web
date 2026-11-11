"""
Importa TODO el catálogo desde la carpeta media (o desde una colección suelta).

    media/
      Fan - Player/                      camisetas actuales de clubes (Fan y Player)
        Premier League/Liverpool/liverpool.jpeg        liga / equipo (carpeta) / foto
        Liga Portuguesa/Sporting.jpeg                  liga / foto (el equipo es el nombre del archivo)
      Retro/                             camisetas retro
        Premier League/Liverpool/...                   igual que Fan - Player, marcadas como retro
        Selecciones/Brasil 1970.jpeg                   retro de selecciones -> botón "Selecciones" en Retro
      Selecciones/                       selecciones actuales: Alemania local.jpeg, Argentina despedida Messi (2).jpeg
      camisetas/                         donde Django guarda las fotos ya importadas (se ignora)

SELECCIONES: el PAÍS se busca dentro del nombre del archivo y el resto es la variante, así
todo queda unificado en un solo equipo por país:
    Argentina.jpg, Argentina(2).jpg           -> Argentina · Modelo 1, 2
    Argentina Despedida Messi (1).jpg         -> Argentina · Despedida Messi
    Beisbolera Argentina.jpg                  -> Argentina · Beisbolera

También funciona indicando una sola colección (por ejemplo "...\\media\\Fan - Player").
Si el nombre trae home/away/third o un año, lo detecta; si no, la equipación queda "Por definir"
y se clasifica después en /admin/.

Uso:
    python manage.py importar_imagenes "C:\\ruta\\media" --dry-run
    python manage.py importar_imagenes "C:\\ruta\\media"
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
EQUIPACIONES = [  # lo más específico primero
    ("tercera", {"third", "tercera", "3rd", "alternativa"}),
    ("visitante", {"away", "visitante", "visita"}),
    ("local", {"home", "local"}),
]
TEMPORADA_ACTUAL = "26/27"

# Carpetas de primer nivel de media y qué significan
COLECCIONES = {"fan player": "actual", "retro": "retro", "selecciones": "selecciones", "seleccion": "selecciones"}
IGNORAR = {"camisetas"}          # donde Django guarda las fotos importadas
CARPETAS_SELECCIONES = {"selecciones", "seleccion"}
CONTENEDORES = CARPETAS_SELECCIONES | {"retro", "varios", "fan player", "fan", "player", "camisetas"}
# Ligas que se llaman distinto en Fan - Player y en Retro (nombre normalizado -> nombre único)
ALIAS_LIGAS = {"liga brasilena": "Brasileirao", "liga holandesa eredivisie": "Liga Holandesa"}
# Palabras del archivo que no forman parte del nombre
RUIDO = (RETRO | {"producto", "product", "img", "image", "imagen", "foto", "photo", "camiseta",
                  "jersey", "shirt", "copia", "copy", "fan", "player"}
         | {palabra for _, claves in EQUIPACIONES for palabra in claves})

SELECCIONES = [
    "Albania", "Alemania", "Arabia Saudita", "Argelia", "Argentina", "Australia", "Austria", "Bélgica",
    "Bolivia", "Bosnia", "Brasil", "Cabo Verde", "Camerún", "Canadá", "Chile", "China", "Colombia",
    "Corea del Sur", "Costa de Marfil", "Costa Rica", "Croacia", "Curazao", "Dinamarca", "Ecuador",
    "Egipto", "Escocia", "Eslovaquia", "Eslovenia", "España", "Estados Unidos", "Finlandia", "Francia",
    "Gales", "Georgia", "Ghana", "Grecia", "Haití", "Honduras", "Hungría", "Inglaterra", "Irak", "Irán",
    "Irlanda", "Islandia", "Israel", "Italia", "Jamaica", "Japón", "Jordania", "Marruecos", "México",
    "Nigeria", "Noruega", "Nueva Zelanda", "Países Bajos", "Panamá", "Paraguay", "Perú", "Polonia",
    "Portugal", "Catar", "República Checa", "Rumania", "Rusia", "Senegal", "Serbia", "Sudáfrica",
    "Suecia", "Suiza", "Túnez", "Turquía", "Ucrania", "Uruguay", "Uzbekistán", "Venezuela",
]
ALIAS = {"Holanda": "Países Bajos", "Qatar": "Catar", "USA": "Estados Unidos", "EEUU": "Estados Unidos",
         "Brazil": "Brasil", "Corea": "Corea del Sur"}


# ---------------------------------------------------------------- utilidades
def normalizar(texto):
    """Minúsculas, sin tildes ni símbolos: 'Bayern_München' -> 'bayern munchen'."""
    ascii_ = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", ascii_.lower()).strip()


def detectar_equipacion(stem):
    """local / visitante / tercera si el nombre lo dice; si no, None."""
    palabras = set(normalizar(stem).split())
    for equipacion, claves in EQUIPACIONES:
        if palabras & claves:
            return equipacion
    return None


def detectar_temporada(stem):
    """'2024-25' -> '24/25', '1998' -> '1998'; None si el nombre no trae año."""
    m = re.search(r"((?:19|20)\d{2})\s*[-_/]\s*((?:19|20)?\d{2})(?!\d)", stem)
    if m:
        return f"{m.group(1)[2:]}/{m.group(2)[-2:]}"
    m = re.search(r"(?<!\d)((?:19|20)\d{2})(?!\d)", stem)
    return m.group(1) if m else None


def numero_modelo(stem):
    """Para nombres tipo 'producto_018' -> '018'."""
    m = re.search(r"(\d+)\D*$", stem)
    return m.group(1) if m else stem


def separar_numero(stem):
    """'Brasil(3)' -> ('Brasil', 3);  'Brasil 2' -> ('Brasil', 2);  'Brasil' -> ('Brasil', 1).
    Solo toma números de 1-2 dígitos, para no confundirlos con un año (1994)."""
    m = (re.search(r"\s*[\(\[]\s*(\d+)\s*[\)\]]\s*$", stem)
         or re.search(r"[\s_\-]+(\d{1,2})\s*$", stem))
    if m:
        return stem[:m.start()].strip(), int(m.group(1))
    return stem.strip(), 1


def limpiar_nombre(texto):
    texto = texto.replace("_", " ").strip()
    return texto.title() if texto.islower() else texto


def _palabras_utiles(texto, excluir=()):
    """Palabras del texto sin número de copia, años, ruido ni las de `excluir`."""
    base, _ = separar_numero(texto)
    return [w for w in re.split(r"[\s_\-]+", base)
            if w and re.search(r"[^\W\d_]", w)                       # con letras (fuera años)
            and normalizar(w) not in RUIDO and normalizar(w) not in excluir]


def nombre_desde_archivo(stem):
    """'Sporting (2)' -> 'Sporting'.  None si el archivo es genérico ('producto_018')."""
    palabras = _palabras_utiles(stem)
    return limpiar_nombre(" ".join(palabras)) if palabras else None


def variante_y_numero(stem, equipo):
    """Para fotos dentro de la carpeta de un equipo.
    'producto_018' -> ('', '018');  'liverpool (2)' -> ('', 2);  'liverpool entrenamiento' -> ('Entrenamiento', 1)"""
    if nombre_desde_archivo(stem) is None:
        return "", numero_modelo(stem)
    palabras = _palabras_utiles(stem, excluir=set(normalizar(equipo).split()))
    return " ".join(w.title() if w.islower() else w for w in palabras), separar_numero(stem)[1]


def canonica_liga(nombre):
    return ALIAS_LIGAS.get(normalizar(nombre), nombre)


def _indice_selecciones():
    indice = {tuple(normalizar(n).split()): n for n in SELECCIONES}
    for alias, nombre in ALIAS.items():
        indice[tuple(normalizar(alias).split())] = nombre
    return indice


INDICE_SELECCIONES = _indice_selecciones()


def detectar_seleccion(texto):
    """Busca un país DENTRO del texto y devuelve (país, variante), o None si no hay ninguno.
    'Beisbolera Argentina' -> ('Argentina', 'Beisbolera');  'Argentina Despedida Messi (1)' ->
    ('Argentina', 'Despedida Messi')."""
    base, _ = separar_numero(texto)
    palabras = [w for w in re.split(r"[\s_\-]+", base) if w]
    norm = [normalizar(w) for w in palabras]
    mejor = None  # (nº de palabras del país, posición, país): gana el nombre más largo
    for clave, pais in INDICE_SELECCIONES.items():
        n = len(clave)
        for i in range(len(norm) - n + 1):
            if tuple(norm[i:i + n]) == clave:
                if mejor is None or n > mejor[0]:
                    mejor = (n, i, pais)
                break
    if mejor is None:
        return None
    n, i, pais = mejor
    resto = [w for w in palabras[:i] + palabras[i + n:]
             if re.search(r"[^\W\d_]", w) and normalizar(w) not in RUIDO]
    return pais, " ".join(w.title() if w.islower() else w for w in resto)


# ------------------------------------------------------------------- comando
class Command(BaseCommand):
    help = "Importa el catálogo desde la carpeta media (Fan - Player, Retro, Selecciones)."

    def add_arguments(self, parser):
        parser.add_argument("carpeta", help="La carpeta media (o una colección suelta).")
        parser.add_argument("--dry-run", action="store_true", help="Muestra qué haría sin guardar nada.")
        parser.add_argument("--reemplazar", action="store_true", help="Reemplaza imágenes ya asignadas.")
        parser.add_argument("--temporada", default=None,
                            help=f"Temporada si el archivo no la indica (por defecto {TEMPORADA_ACTUAL}; "
                                 "en retro queda vacía).")
        parser.add_argument("--versiones", default="fan,player",
                            help="Versiones a crear por foto en Fan - Player y Selecciones.")
        parser.add_argument("--versiones-retro", default="fan", help="Versiones a crear por foto en Retro.")
        parser.add_argument("--precio-fan", type=int, default=75000)
        parser.add_argument("--precio-player", type=int, default=90000)

    def handle(self, *args, **o):
        raiz = Path(o["carpeta"])
        if not raiz.is_dir():
            raise CommandError(f"No existe la carpeta: {raiz}")

        self.versiones = self._leer_versiones(o["versiones"])
        self.versiones_retro = self._leer_versiones(o["versiones_retro"])
        self.precios = {"fan": o["precio_fan"], "player": o["precio_player"]}
        self.dry, self.reemplazar, self.temporada = o["dry_run"], o["reemplazar"], o["temporada"]
        self.stats = dict(equipos=0, productos=0, imagenes=0, omitidas=0)
        self.no_reconocidas = set()
        self.equipos = {normalizar(e.nombre): e for e in Equipo.objects.all()}

        archivos = [p for p in raiz.rglob("*") if p.suffix.lower() in EXTENSIONES
                    and not (len(p.relative_to(raiz).parts) > 1
                             and normalizar(p.relative_to(raiz).parts[0]) in IGNORAR)]
        archivos.sort(key=str)
        if not archivos:
            raise CommandError("No encontré imágenes (.jpg, .jpeg, .png, .webp) en esa carpeta.")
        # ¿me dieron la carpeta "padre" (media) o una colección suelta?
        self.modo_media = any(len(p.relative_to(raiz).parts) > 1
                              and normalizar(p.relative_to(raiz).parts[0]) in COLECCIONES for p in archivos)

        with transaction.atomic():
            for ruta in archivos:
                self._importar(ruta, raiz)
            if self.dry:
                transaction.set_rollback(True)

        s = self.stats
        titulo = "SIMULACIÓN (no se guardó nada)" if self.dry else "Listo"
        self.stdout.write(self.style.SUCCESS(
            f"{titulo}: {s['productos']} productos nuevos, {s['imagenes']} imágenes asignadas, "
            f"{s['equipos']} equipos nuevos, {s['omitidas']} omitidas."))
        if self.no_reconocidas:
            self.stdout.write(self.style.WARNING(
                "Selecciones que no reconocí (se crearon con el nombre del archivo; si son un país con "
                "variante, agrégalo a SELECCIONES en este archivo): " + ", ".join(sorted(self.no_reconocidas))))

    def _leer_versiones(self, texto):
        versiones = [v.strip().lower() for v in texto.split(",") if v.strip()]
        if not versiones or set(versiones) - VERSIONES:
            raise CommandError("Las versiones solo pueden ser: fan, player (separadas por coma).")
        return versiones

    # -- un archivo -> equipo + productos
    def _importar(self, ruta, raiz):
        carpetas = [c.replace("_", " ").strip() for c in ruta.relative_to(raiz).parts[:-1]]

        # 1) ¿A qué colección pertenece?
        if normalizar(raiz.name) in COLECCIONES:                 # me dieron la colección directamente
            coleccion, resto = COLECCIONES[normalizar(raiz.name)], carpetas
        elif carpetas and normalizar(carpetas[0]) in COLECCIONES:  # me dieron media
            coleccion, resto = COLECCIONES[normalizar(carpetas[0])], carpetas[1:]
        elif self.modo_media:
            self.stdout.write(self.style.WARNING(f"  carpeta ignorada: {ruta.relative_to(raiz)}"))
            self.stats["omitidas"] += 1
            return
        else:                                                    # estructura clásica: ya son las ligas
            coleccion, resto = "actual", carpetas

        es_retro = coleccion == "retro"
        es_seleccion = coleccion == "selecciones" or any(normalizar(c) in CARPETAS_SELECCIONES for c in resto)

        # 2) ¿Qué equipo es?
        liga, variante = "", ""
        if es_seleccion:                                          # el país sale del nombre del archivo
            resuelto = self._resolver_seleccion(ruta, resto)
            nombre_equipo, variante, numero = resuelto if resuelto else (None, "", None)
        else:
            liga = canonica_liga(resto[0]) if resto else ""
            if len(resto) >= 2:                                   # liga / equipo (carpeta) / foto
                nombre_equipo = resto[1]
                variante, numero = variante_y_numero(ruta.stem, nombre_equipo)
            else:                                                 # liga / foto: el equipo es el archivo
                nombre_equipo, numero = nombre_desde_archivo(ruta.stem), separar_numero(ruta.stem)[1]

        if not nombre_equipo:
            self.stdout.write(self.style.WARNING(
                f"  omitida (no pude deducir el equipo): {ruta.relative_to(raiz)}"))
            self.stats["omitidas"] += 1
            return

        equipo = self._equipo(nombre_equipo, liga, es_seleccion)
        datos = self._datos(ruta, equipo, numero, variante, es_retro)
        etiqueta = " · ".join(filter(None, [
            "selección" if es_seleccion else "",
            datos["equipacion"] if datos["equipacion"] != "sin_definir" else "equipación ?",
            datos["temporada"] or "sin temporada",
            "retro" if datos["retro"] else ""]))
        self.stdout.write(f"  {liga or '-'} / {equipo.nombre} / {datos['codigo']}  [{etiqueta}]")
        self._guardar(ruta, equipo, datos, self.versiones_retro if es_retro else self.versiones)

    def _resolver_seleccion(self, ruta, carpetas):
        """-> (país, variante, número) o None.  El país se busca en el nombre del archivo."""
        stem = ruta.stem
        utiles = [c for c in carpetas if normalizar(c) not in CONTENEDORES]
        hallado = detectar_seleccion(stem)
        if hallado:
            return hallado[0], hallado[1], separar_numero(stem)[1]

        nombre = nombre_desde_archivo(stem)
        if nombre is None and utiles:          # archivo genérico (producto_001): vale la carpeta
            hallado = detectar_seleccion(utiles[-1])
            pais, variante = hallado if hallado else (limpiar_nombre(utiles[-1]), "")
            return pais, variante, numero_modelo(stem)
        if nombre:                             # país que no está en la lista
            self.no_reconocidas.add(nombre)
            return nombre, "", separar_numero(stem)[1]
        return None

    def _equipo(self, nombre, liga, es_seleccion):
        tipo = "seleccion" if es_seleccion else "club"
        clave = normalizar(nombre)           # 'Bayern Munich' coincide con 'Bayern Múnich'
        equipo = self.equipos.get(clave)
        if equipo is None:
            equipo = Equipo.objects.create(nombre=nombre, tipo=tipo, liga=liga)
            self.equipos[clave] = equipo
            self.stats["equipos"] += 1
        elif es_seleccion and equipo.tipo != "seleccion":
            equipo.tipo, equipo.liga = "seleccion", ""
            equipo.save(update_fields=["tipo", "liga"])
        elif liga and (not equipo.liga or normalizar(equipo.liga) in CONTENEDORES):
            equipo.liga = liga               # también corrige ligas falsas como "Fan - Player"
            equipo.save(update_fields=["liga"])
        return equipo

    def _datos(self, ruta, equipo, numero, variante, es_retro):
        stem = ruta.stem
        retro = es_retro or bool(set(normalizar(stem).split()) & RETRO)
        codigo = slugify(stem)
        if retro and not codigo.startswith("retro"):
            codigo = f"retro-{codigo}"       # evita chocar con producto_001 de Fan - Player

        temporada = detectar_temporada(stem)
        if temporada is None:
            if self.temporada is not None:
                temporada = self.temporada
            else:
                temporada = "" if retro else TEMPORADA_ACTUAL   # retro: se completa en /admin/

        equipacion = detectar_equipacion(stem)
        nombre = equipo.nombre + (f" {equipacion}" if equipacion else "")
        if variante:
            nombre += f" · {variante}"
        if retro and (equipacion or variante):
            nombre += " retro"
        if not equipacion and not variante:
            nombre += f" · {'Retro' if retro else 'Modelo'} {numero}"
        elif str(numero).isdigit() and int(numero) > 1:
            nombre += f" {int(numero)}"
        return {"codigo": codigo, "equipacion": equipacion or "sin_definir",
                "temporada": temporada, "retro": retro, "nombre": nombre}

    def _guardar(self, ruta, equipo, d, versiones):
        ruta_imagen = None  # el primer producto guarda el archivo; los demás lo comparten
        for version in versiones:
            producto, creado = Producto.objects.get_or_create(
                equipo=equipo, codigo=d["codigo"], version=version,
                defaults={"nombre": d["nombre"], "equipacion": d["equipacion"], "retro": d["retro"],
                          "temporada": d["temporada"], "precio": self.precios[version]},
            )
            self.stats["productos"] += creado

            if producto.imagen and not self.reemplazar:
                ruta_imagen = ruta_imagen or producto.imagen.name
                continue
            if not self.dry:
                if ruta_imagen is None:
                    archivo = f"{slugify(equipo.nombre)}-{d['codigo']}{ruta.suffix.lower()}"
                    with ruta.open("rb") as f:
                        producto.imagen.save(archivo, File(f), save=True)
                    ruta_imagen = producto.imagen.name
                else:
                    producto.imagen.name = ruta_imagen
                    producto.save(update_fields=["imagen"])
            self.stats["imagenes"] += 1