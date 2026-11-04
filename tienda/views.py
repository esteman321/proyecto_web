import re
from collections import Counter

from django.contrib.staticfiles import finders
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils.text import slugify

from .models import Equipo, Producto

ORDENES = {
    "nuevo": "-creado",
    "precio_asc": "precio",
    "precio_desc": "-precio",
    "nombre": "nombre",
}
TALLAS = ["S", "M", "L", "XL", "XXL"]
INFO_VERSION = {
    "fan": "Versión Fan: corte cómodo y tela pensada para el uso diario.",
    "player": "Versión Player: corte más ajustado, como la que usan los jugadores en cancha.",
}
SECCIONES = {"clubes": "Clubes", "retro": "Retro", "selecciones": "Selecciones"}
LIGAS_ORDEN = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
BUCKETS = [("local", "Local"), ("visitante", "Visitante"), ("otras", "Otras")]


# ------------------------------------------------------------------ utilidades
def _escudo(carpeta, nombre):
    """URL del escudo si existe static/escudos/<carpeta>/<slug>.<ext>; si no, None."""
    base = slugify(nombre)
    for ext in ("svg", "png", "webp", "jpg", "jpeg"):
        ruta = f"escudos/{carpeta}/{base}.{ext}"
        if finders.find(ruta):
            return static(ruta)
    return None


def _iniciales(nombre):
    partes = [p for p in re.split(r"[\s\-\.]+", nombre) if p]
    if not partes:
        return "?"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[1][0]).upper()


def _item(nombre, url, escudo, activo=False, iniciales=None):
    return {"nombre": nombre, "url": url, "escudo": escudo, "activo": activo,
            "iniciales": iniciales or _iniciales(nombre)}


def _productos_seccion(seccion):
    qs = Producto.objects.filter(activo=True).select_related("equipo")
    if seccion == "retro":
        return qs.filter(retro=True)
    tipo = "seleccion" if seccion == "selecciones" else "club"
    return qs.filter(retro=False, equipo__tipo=tipo)


def _orden_liga(nombre):
    if nombre in LIGAS_ORDEN:
        return (0, LIGAS_ORDEN.index(nombre), "")
    if nombre in ("Selecciones", "Otras ligas"):
        return (2, 0, nombre)
    return (1, 0, nombre.lower())


def _agrupar_por_liga(equipos):
    grupos = {}
    for e in equipos:
        grupos.setdefault(e.grupo, []).append(e)
    return dict(sorted(grupos.items(), key=lambda kv: _orden_liga(kv[0])))


def _buscar_equipo(equipos, slug):
    return next((e for e in equipos if e.slug == slug), None)


def _clave_bucket(equipacion):
    return equipacion if equipacion in ("local", "visitante") else "otras"


def _filtrar_bucket(qs, clave):
    if clave in ("local", "visitante"):
        return qs.filter(equipacion=clave)
    return qs.exclude(equipacion__in=["local", "visitante"])


def _url_seccion(seccion):
    if seccion == "selecciones":
        return reverse("selecciones")
    return reverse("ligas", kwargs={"seccion": seccion})


def _seccion_de(p):
    if p.retro:
        return "retro"
    return "selecciones" if p.equipo.tipo == "seleccion" else "clubes"


def _migas_producto(p):
    sec = _seccion_de(p)
    migas = [("Inicio", reverse("home")), (SECCIONES[sec], _url_seccion(sec))]
    if sec == "selecciones":
        migas.append((p.equipo.nombre, reverse("seleccion", kwargs={"equipo": p.equipo.slug})))
    else:
        migas.append((p.equipo.grupo, reverse("liga", kwargs={"seccion": sec, "liga": slugify(p.equipo.grupo)})))
        migas.append((p.equipo.nombre, reverse("equipo", kwargs={
            "seccion": sec, "liga": slugify(p.equipo.grupo), "equipo": p.equipo.slug})))
    return migas


# ---------------------------------------------------------------------- vistas
def home(request):
    productos = (Producto.objects.filter(activo=True)
                 .select_related("equipo").order_by("-creado", "-id")[:12])
    return render(request, "tienda/home.html", {"productos": productos})


def seccion(request, seccion, liga=None, equipo=None):
    """Clubes / Retro: liga -> club -> equipación.  Selecciones: selección -> equipación."""
    base = _productos_seccion(seccion)
    equipos = list(Equipo.objects.filter(pk__in=base.values_list("equipo_id", flat=True)).order_by("nombre"))
    nombre_seccion = SECCIONES[seccion]
    migas = [("Inicio", reverse("home")), (nombre_seccion, _url_seccion(seccion))]
    ctx = {"seccion": seccion, "titulo": nombre_seccion, "eyebrow": nombre_seccion,
           "ligas": None, "equipos": None, "liga_sel": False, "equipo_sel": False,
           "selector": None, "pagina": None, "querystring": ""}
    sel = None
    nombre_liga = None

    if seccion == "selecciones":
        sel = _buscar_equipo(equipos, equipo) if equipo else None
        if equipo and sel is None:
            raise Http404
        ctx["subtitulo"] = "Elige tu selección."
        ctx["equipos"] = [_item("Todas", reverse("selecciones"), None, sel is None, iniciales="★")] + [
            _item(e.nombre, reverse("seleccion", kwargs={"equipo": e.slug}),
                  _escudo("equipos", e.nombre), sel == e) for e in equipos]
        productos = base
    else:
        grupos = _agrupar_por_liga(equipos)
        if liga:
            nombre_liga = next((g for g in grupos if slugify(g) == liga), None)
            if nombre_liga is None:
                raise Http404
        ctx["ligas"] = [
            _item(g, reverse("liga", kwargs={"seccion": seccion, "liga": slugify(g)}),
                  _escudo("ligas", g), g == nombre_liga) for g in grupos]
        ctx["liga_sel"] = nombre_liga is not None

        if nombre_liga is None:  # paso 1: solo se elige la liga
            ctx["eyebrow"] = f"{nombre_seccion} · Elige tu liga"
            ctx["subtitulo"] = "Toca el escudo de tu liga y luego el de tu equipo."
            ctx["migas"] = migas
            return render(request, "tienda/seccion.html", ctx)

        equipos_liga = grupos[nombre_liga]
        sel = _buscar_equipo(equipos_liga, equipo) if equipo else None
        if equipo and sel is None:
            raise Http404
        url_liga = reverse("liga", kwargs={"seccion": seccion, "liga": liga})
        migas.append((nombre_liga, url_liga))
        ctx["titulo"] = nombre_liga
        ctx["eyebrow"] = f"{nombre_seccion} · Elige tu club"
        ctx["subtitulo"] = "Ahora toca el escudo de tu club."
        ctx["equipos"] = [_item("Todos", url_liga, _escudo("ligas", nombre_liga), sel is None,
                                iniciales=_iniciales(nombre_liga))] + [
            _item(e.nombre, reverse("equipo", kwargs={"seccion": seccion, "liga": liga, "equipo": e.slug}),
                  _escudo("equipos", e.nombre), sel == e) for e in equipos_liga]
        productos = base.filter(equipo__in=equipos_liga)

    if sel:
        ctx["equipo_sel"] = True
        ctx["titulo"] = sel.nombre
        ctx["eyebrow"] = sel.grupo
        ctx["subtitulo"] = "Elige la equipación."
        migas.append((sel.nombre, None))
        productos = productos.filter(equipo=sel)
        conteo = Counter(_clave_bucket(e) for e in productos.values_list("equipacion", flat=True))
        elegido = request.GET.get("eq")
        if elegido not in conteo:
            elegido = next((k for k, _ in BUCKETS if conteo[k]), None)
        ctx["selector"] = [{"nombre": n, "count": conteo[k], "activo": k == elegido,
                            "url": f"{request.path}?eq={k}"} for k, n in BUCKETS]
        if elegido:
            productos = _filtrar_bucket(productos, elegido)
            ctx["querystring"] = f"eq={elegido}"

    ctx["migas"] = migas
    productos = productos.order_by("-temporada", "codigo", "version", "id")
    ctx["pagina"] = Paginator(productos, 12).get_page(request.GET.get("page"))
    return render(request, "tienda/seccion.html", ctx)


def catalogo(request):
    qs = Producto.objects.filter(activo=True).select_related("equipo")

    q = request.GET.get("q", "").strip()
    tipo = request.GET.get("tipo", "")
    liga = request.GET.get("liga", "")
    version = request.GET.get("version", "")
    equipacion = request.GET.get("equipacion", "")
    temporada = request.GET.get("temporada", "")
    orden = request.GET.get("orden", "nuevo")

    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(equipo__nombre__icontains=q))
    if tipo:
        qs = qs.filter(equipo__tipo=tipo)
    if liga:
        qs = qs.filter(equipo__liga=liga)
    if version:
        qs = qs.filter(version=version)
    if equipacion:
        qs = qs.filter(equipacion=equipacion)
    if temporada:
        qs = qs.filter(temporada=temporada)
    qs = qs.order_by(ORDENES.get(orden, "-creado"), "id")

    pagina = Paginator(qs, 12).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)

    return render(request, "tienda/catalogo.html", {
        "pagina": pagina, "querystring": params.urlencode(),
        "q": q, "tipo": tipo, "liga": liga, "version": version,
        "equipacion": equipacion, "temporada": temporada, "orden": orden,
        "tipos": Equipo.TIPOS, "versiones": Producto.VERSIONES,
        "ligas": (Equipo.objects.exclude(liga="").values_list("liga", flat=True)
                  .distinct().order_by("liga")),
        "equipaciones": [e for e in Producto.EQUIPACION if e[0] != "sin_definir"],
        "temporadas": (Producto.objects.filter(activo=True)
                       .values_list("temporada", flat=True).distinct().order_by("-temporada")),
    })


def detalle(request, pk):
    producto = get_object_or_404(
        Producto.objects.select_related("equipo"), pk=pk, activo=True)

    hermano = None  # la misma camiseta en la otra versión (Fan <-> Player)
    if producto.codigo:
        hermano = (Producto.objects.filter(equipo=producto.equipo, codigo=producto.codigo, activo=True)
                   .exclude(pk=pk).first())

    relacionados = (Producto.objects.filter(activo=True, equipo=producto.equipo, version=producto.version)
                    .exclude(pk=pk).select_related("equipo")[:6])
    if relacionados.count() < 4:
        relacionados = (Producto.objects.filter(activo=True, equipo__tipo=producto.equipo.tipo,
                                                version=producto.version)
                        .exclude(pk=pk).select_related("equipo").order_by("-creado")[:6])
    return render(request, "tienda/detalle.html", {
        "p": producto, "hermano": hermano, "tallas": TALLAS,
        "info_version": INFO_VERSION.get(producto.version, ""),
        "migas": _migas_producto(producto), "relacionados": relacionados})