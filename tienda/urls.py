from django.urls import path, re_path
from . import views

urlpatterns = [
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