from django.urls import path, re_path
from . import api, views

urlpatterns = [
    # API JSON para React (mismas rutas del sitio con el prefijo /api)
    path("api/home/", api.home),
    re_path(r"^api/(?P<seccion>clubes|retro)/$", api.seccion),
    re_path(r"^api/(?P<seccion>clubes|retro)/(?P<liga>[-\w]+)/$", api.seccion),
    re_path(r"^api/(?P<seccion>clubes|retro)/(?P<liga>[-\w]+)/(?P<equipo>[-\w]+)/$", api.seccion),
    path("api/selecciones/", api.seccion, {"seccion": "selecciones"}),
    path("api/selecciones/<slug:equipo>/", api.seccion, {"seccion": "selecciones"}),
    path("api/camisetas/", api.catalogo),
    path("api/camisetas/<int:pk>/", api.detalle),

    # Sitio con plantillas de Django (se retira cuando React lo reemplace por completo)
    path("", views.home, name="home"),

    # Clubes y Retro: liga -> club -> equipación
    re_path(r"^(?P<seccion>clubes|retro)/$", views.seccion, name="ligas"),
    re_path(r"^(?P<seccion>clubes|retro)/(?P<liga>[-\w]+)/$", views.seccion, name="liga"),
    re_path(r"^(?P<seccion>clubes|retro)/(?P<liga>[-\w]+)/(?P<equipo>[-\w]+)/$", views.seccion, name="equipo"),

    # Selecciones: selección -> equipación
    path("selecciones/", views.seccion, {"seccion": "selecciones"}, name="selecciones"),
    path("selecciones/<slug:equipo>/", views.seccion, {"seccion": "selecciones"}, name="seleccion"),

    # Catálogo completo y detalle
    path("camisetas/", views.catalogo, name="catalogo"),
    path("camisetas/<int:pk>/", views.detalle, name="detalle"),
]