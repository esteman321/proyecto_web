"""URLs principales de Tribuna."""
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("tienda.urls")),
]

from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# ── SPA de React (se activa con SPA_ACTIVA = True en settings) ──
# Cuando las plantillas se retiren, Django sirve el build de Vite:
# las rutas que no coinciden con la API/carrito caen aquí y React
# maneja el enrutamiento (Home, Section, Catalog, Detail, NotFound).
if settings.SPA_ACTIVA:
    def spa(request, *args, **kwargs):
        html = (settings.SPA_DIST / "index.html").read_text(encoding="utf-8")
        return HttpResponse(html, content_type="text/html")

    urlpatterns.append(re_path(r"^", spa))
