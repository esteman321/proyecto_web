"""
API JSON para el frontend en React.

Las URLs son las mismas del sitio con el prefijo /api:
    /clubes/serie-a/atalanta/?eq=local   ->   /api/clubes/serie-a/atalanta/?eq=local
Así React usa la misma ruta para pedir datos y para mostrar la página.
Los datos salen de las mismas funciones contexto_*() que usan las plantillas (views.py).
"""
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET

from . import views

ORDENES = [("nuevo", "Más nuevas"), ("precio_asc", "Precio: menor a mayor"),
           ("precio_desc", "Precio: mayor a menor"), ("nombre", "Nombre A–Z")]


def producto_json(p):
    """Una camiseta, lista para la tarjeta o el detalle."""
    tiene_fan = getattr(p, "tiene_fan", None)
    tiene_player = getattr(p, "tiene_player", None)
    desde = getattr(p, "precio_desde", None)
    return {
        "id": p.pk,
        "nombre": p.nombre,
        "version": p.version,
        "version_label": p.get_version_display(),
        "tiene_fan": p.version == "fan" if tiene_fan is None else bool(tiene_fan),
        "tiene_player": p.version == "player" if tiene_player is None else bool(tiene_player),
        "precio": int(p.precio),
        "precio_desde": int(desde if desde is not None else p.precio),
        "meta": p.meta,
        "retro": p.retro,
        "imagen": p.imagen.url if p.imagen else None,
        "c1": p.color_principal,
        "c2": p.color_secundario,
    }


def pagina_json(pagina):
    return {"items": [producto_json(p) for p in pagina], "numero": pagina.number,
            "paginas": pagina.paginator.num_pages, "total": pagina.paginator.count}


def _no_encontrado():
    return JsonResponse({"detail": "No encontrado"}, status=404)


@require_GET
def home(request):
    return JsonResponse({"novedades": [producto_json(p) for p in views.contexto_home()["productos"]]})


@require_GET
def seccion(request, seccion, liga=None, equipo=None):
    try:
        ctx = views.contexto_seccion(request, seccion, liga, equipo)
    except Http404:
        return _no_encontrado()
    return JsonResponse({
        "seccion": ctx["seccion"], "titulo": ctx["titulo"], "eyebrow": ctx["eyebrow"],
        "subtitulo": ctx["subtitulo"], "migas": ctx["migas"],
        "ligas": ctx["ligas"], "equipos": ctx["equipos"], "selector": ctx["selector"],
        "liga_sel": ctx["liga_sel"], "equipo_sel": ctx["equipo_sel"],
        "pagina": pagina_json(ctx["pagina"]) if ctx["pagina"] else None,
    })


@require_GET
def catalogo(request):
    ctx = views.contexto_catalogo(request)
    return JsonResponse({
        "pagina": pagina_json(ctx["pagina"]),
        "filtros": {k: ctx[k] for k in ("q", "tipo", "liga", "version", "equipacion", "temporada", "orden")},
        "opciones": {
            "tipos": [list(t) for t in ctx["tipos"]],
            "versiones": [list(v) for v in ctx["versiones"]],
            "ligas": list(ctx["ligas"]),
            "equipaciones": [list(e) for e in ctx["equipaciones"]],
            "temporadas": list(ctx["temporadas"]),
            "ordenes": [list(o) for o in ORDENES],
        },
    })


@require_GET
def detalle(request, pk):
    try:
        ctx = views.contexto_detalle(pk)
    except Http404:
        return _no_encontrado()
    p, h = ctx["p"], ctx["hermano"]
    return JsonResponse({
        "producto": {**producto_json(p), "temporada": p.temporada, "equipacion": p.equipacion,
                     "equipacion_label": p.get_equipacion_display(), "equipacion_definida": p.equipacion_definida},
        "equipo": {"nombre": p.equipo.nombre, "tipo": p.equipo.get_tipo_display(),
                   "liga": p.equipo.liga, "pais": p.equipo.pais},
        "hermano": ({"id": h.pk, "version": h.version, "version_label": h.get_version_display(),
                     "precio": int(h.precio)} if h else None),
        "info_version": ctx["info_version"], "tallas": ctx["tallas"],
        "migas": ctx["migas"], "url_equipo": ctx["url_equipo"],
        "relacionados": [producto_json(r) for r in ctx["relacionados"]],
    })