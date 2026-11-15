from django.urls import path, re_path
from . import api, views
from . import carrito_views

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

    # === Carrito y Checkout ===
    path("carrito/", carrito_views.ver_carrito, name="carrito"),
    path("carrito/agregar/", carrito_views.agregar_al_carrito, name="agregar_al_carrito"),
    path("carrito/actualizar/<int:item_id>/", carrito_views.actualizar_item, name="actualizar_item"),
    path("carrito/eliminar/<int:item_id>/", carrito_views.eliminar_item, name="eliminar_item"),
    path("carrito/badge/", carrito_views.badge_carrito, name="badge_carrito"),
    path("checkout/", carrito_views.checkout, name="checkout"),
    path("checkout/pagar/", carrito_views.procesar_pago, name="procesar_pago"),
    path("pedido/<uuid:numero>/", carrito_views.confirmacion, name="confirmacion"),

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
