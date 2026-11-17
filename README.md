# Tribuna

> La camiseta de tu equipo, a tu talla.

E-commerce de camisetas de fútbol: **Django (MPA con templates)** que evoluciona
hacia **React (SPA)**. Las secciones de navegación ya viven en React y el
carrito/checkout siguen en Django; al final, la SPA reemplaza a los templates.

## Estructura

```
tribuna-web/
├── manage.py
├── db.sqlite3                     SQLite (dev); PostgreSQL listo en settings.py
├── venv/                          Django 6 + Pillow
│
├── config/                        proyecto Django
│   ├── settings.py                SQLite/PostgreSQL, SPA_ACTIVA, CSRF para Vite
│   ├── urls.py                    tienda + media + catch-all de la SPA
│   └── wsgi.py / asgi.py
│
├── tienda/                        app Django
│   ├── models.py                  Equipo, Producto, Carrito, ItemCarrito, Pedido…
│   ├── views.py                   contexto_*() que alimentan templates y API
│   ├── api.py                     API JSON para React (mismas rutas con /api)
│   ├── carrito_views.py           carrito + checkout con pasarela simulada
│   ├── urls.py                    mapa de rutas del sitio y de la API
│   ├── migrations/
│   └── management/
│       └── commands/
│           ├── importar_imagenes.py   importa el catálogo desde media/
│           ├── cargar_catalogo.py     atajo: importar_imagenes media
│           ├── escudos.py             crea static/escudos/ y lista faltantes
│           └── generar_escudos.py     escudos SVG (iniciales) para los faltantes
│
├── templates/                     sitio con plantillas (se retira al final)
│   ├── base.html
│   └── tienda/
│       ├── home.html, seccion.html, catalogo.html, detalle.html
│       ├── carrito.html, checkout.html, confirmacion.html
│       └── _card.html, _escudo.html, _camiseta.html
│
├── static/
│   ├── css/home.css               hoja única: la usan templates Y React
│   ├── js/home.js                 tilt del hero (solo templates)
│   ├── js/carrito.js              carrito/checkout con vanilla JS
│   ├── escudos/ligas/ y equipos/  escudos reales (el resto: iniciales)
│   └── spa/                       build de Vite (npm run build)
│
├── media/
│   ├── Fan - Player/  Retro/  Selecciones/    fotos fuente (no tocar)
│   └── camisetas/                 fotos que Django sirve (las copia el import)
│
└── frontend/                      React, al lado de manage.py y static/
    ├── package.json  vite.config.js  index.html  README.md
    └── src/
        ├── main.jsx  App.jsx  api.js  format.js  extra.css
        ├── components/  Card, Crumbs, Jersey, Layout, Pager, Picker, State
        ├── hooks/       useTilt.js, useTitle.js
        └── pages/       Home, Section, Catalog, Detail, NotFound
```

## Arquitectura

| Capa | Tecnología | Rutas |
|---|---|---|
| SPA React (hoy en dev) | Vite + React Router | `/`, `/selecciones(/:equipo)`, `/clubes(/:liga)(/:equipo)`, `/retro(…)`, `/camisetas(/:id)` |
| API JSON | Django `tienda/api.py` | mismas rutas con prefijo `/api` |
| MPA Django | templates | igual que la SPA + carrito/checkout |
| Carrito y checkout | Django templates + `carrito.js` | `/carrito/`, `/checkout/…`, `/pedido/…` |

La API reutiliza las mismas funciones `contexto_*()` de `views.py`, así que
templates y React muestran exactamente lo mismo.

### El paso a producción de la SPA

1. `npm run build` → compila a `static/spa/` con base `/static/spa/`.
2. En `config/settings.py`, `SPA_ACTIVA = True` → Django sirve
   `static/spa/index.html` en cualquier ruta que no sea API/carrito/media.
3. Los templates del MPA quedan retirados (por eso "se retira al final" ).

## Puesta en marcha

```bash
# 1. Backend
python -m venv venv
venv\Scripts\activate
pip install Django Pillow
python manage.py migrate
python manage.py cargar_catalogo      # importa 962 productos desde media/
python manage.py escudos              # crea static/escudos/ y lista faltantes
python manage.py generar_escudos      # escudos SVG para los que no tengan foto
python manage.py runserver            # http://localhost:8000

# 2. Frontend (en otra terminal)
cd frontend
npm install
npm run dev                           # http://localhost:5173
```

Con `SPA_ACTIVA = False` el sitio en 8000 lo sirven los templates de Django y
en 5173 corre la SPA (Vite hace proxy de `/api`, `/carrito`, `/checkout`,
`/static`, `/media` y `/admin` hacia 8000).

## Admin

- URL: `http://localhost:8000/admin/`
- Usuario: `admin` · `admin@gmail.com` · contraseña: `admin` (solo desarrollo)
