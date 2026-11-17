"""
Genera los escudos que faltan como SVG con los colores del equipo.

    python manage.py generar_escudos
    python manage.py generar_escudos --carpeta equipos    (solo equipos o solo ligas)

Cada escudo es un blason simple: forma de escudo con el color principal del
equipo, borde con el secundario y sus iniciales en el centro.

    static/escudos/equipos/valencia.svg
    static/escudos/ligas/otras-ligas.svg

NUNCA reemplaza un archivo existente: los escudos reales (png/jpg) manda sobre
estos generados, y correr el comando dos veces no cambia nada.
"""
import colorsys
from collections import Counter
from pathlib import Path
import re

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from tienda.models import Equipo, Producto

EXT = ("svg", "png", "webp", "jpg", "jpeg")


def _iniciales(nombre):
    partes = [p for p in re.split(r"[\s\-\.]+", nombre) if p]
    if not partes:
        return "?"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[1][0]).upper()


def _luminancia(hex_color):
    """0 (negro) a 1 (blanco), para elegir el color del texto."""
    h = (hex_color or "").strip()
    if not h.startswith("#") or len(h) < 7:
        return 0.5
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    # percepción humana: el verde pesa más
    return 0.299 * r + 0.587 * g + 0.114 * b


def _tinte(hex_color, agua=0.35):
    """Devuelve un tono más suave del color, para el fondo del blasón."""
    h = (hex_color or "").strip()
    if not h.startswith("#") or len(h) < 7:
        return "#9CA3AF"
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    ll = ll + (1 - ll) * agua          # aclara
    ss = min(1, ss * 1.05)             # conserva un poco de saturación
    r2, g2, b2 = colorsys.hls_to_rgb(hh, ll, ss)
    return "#%02X%02X%02X" % (round(r2 * 255), round(g2 * 255), round(b2 * 255))


def _svg(nombre, c1, c2):
    """Blason con las iniciales: fondo tintado, borde y letras con el secundario."""
    ini = _iniciales(nombre)
    fondo = _tinte(c1)
    texto = "#1A1A1A" if _luminancia(fondo) > 0.55 else "#FFFFFF"
    borde = c2 if c2 else c1
    letra = borde if _luminancia(borde) != _luminancia(fondo) else texto
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<path d="M50 4 92 17V52Q92 84 50 96 8 84 8 52V17Z" '
        f'fill="{fondo}" stroke="{borde}" stroke-width="5"/>'
        '<path d="M50 12 85 22V51Q85 76 50 88Z" fill="#FFFFFF" opacity="0.14"/>'
        f'<text x="50" y="63" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" '
        f'font-weight="bold" font-size="30">{ini}</text>'
        f'<style>text{{fill:{letra}}}</style>'
        "</svg>"
    )


class Command(BaseCommand):
    help = "Genera escudos SVG (iniciales + colores del equipo) solo para los que faltan."

    def add_arguments(self, parser):
        parser.add_argument("--carpeta", choices=["ligas", "equipos"], default=None)

    def handle(self, *args, **opts):
        base = Path(settings.BASE_DIR) / "static" / "escudos"
        for sub in ("ligas", "equipos"):
            (base / sub).mkdir(parents=True, exist_ok=True)
        carpeta = opts["carpeta"]

        # Colores por equipo: el par (c1, c2) más repetido entre sus productos.
        colores_equipos = {}
        for eq in Equipo.objects.filter(productos__activo=True).distinct():
            pares = Counter(
                (p.color_principal.upper(), p.color_secundario.upper())
                for p in eq.productos.filter(activo=True)
            )
            if pares:
                colores_equipos[eq.nombre] = pares.most_common(1)[0][0]

        # Colores por liga: el c1 más repetido entre los productos de sus equipos.
        colores_ligas = {}
        por_liga = {}
        for p in Producto.objects.filter(activo=True).select_related("equipo"):
            por_liga.setdefault(p.equipo.grupo, []).append(p.color_principal.upper())
        for liga, cs in por_liga.items():
            if cs:
                # c1 de la liga + c2 gris azulado neutro para el borde
                colores_ligas[liga] = (Counter(cs).most_common(1)[0][0], "#334155")

        conjuntos = []
        if carpeta in (None, "ligas"):
            conjuntos.append(("LIGAS", "ligas", colores_ligas))
        if carpeta in (None, "equipos"):
            conjuntos.append(("EQUIPOS", "equipos", colores_equipos))

        total = 0
        for titulo, sub, colores in conjuntos:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{titulo}  ->  {base / sub}"))
            for nombre, (c1, c2) in sorted(colores.items()):
                slug = slugify(nombre)
                if next((f"{slug}.{x}" for x in EXT if (base / sub / f"{slug}.{x}").exists()), None):
                    self.stdout.write(f"  [ok]    {slug}  (ya tiene escudo)")
                    continue
                (base / sub / f"{slug}.svg").write_text(_svg(nombre, c1, c2), encoding="utf-8")
                total += 1
                self.stdout.write(self.style.SUCCESS(f"  [nuevo] {slug}.svg  <- {nombre}"))

        self.stdout.write(self.style.SUCCESS(f"\nGenerados {total} escudos SVG."))
