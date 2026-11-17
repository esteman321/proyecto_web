# Frontend de React (SPA)

La SPA consume la API JSON de Django (`tienda/api.py`), que usa las mismas
rutas del sitio con el prefijo `/api`:

| Página | Ruta React | API |
|---|---|---|
| Home | `/` | `/api/home/` |
| Selecciones | `/selecciones(/:equipo)` | `/api/selecciones/...` |
| Clubes | `/clubes(/:liga)(/:equipo)` | `/api/clubes/...` |
| Retro | `/retro(/:liga)(/:equipo)` | `/api/retro/...` |
| Todo | `/camisetas` | `/api/camisetas/` |
| Detalle | `/camisetas/:id` | `/api/camisetas/:id/` |
| Cualquier otra | `*` → NotFound | — |

El carrito y el checkout siguen siendo páginas de Django (`/carrito/`,
`/checkout/`) con `static/js/carrito.js`; React solo agrega productos y
mantiene el badge del header.

## Desarrollo

```bash
npm install
npm run dev        # http://localhost:5173 (Django debe correr en 8000)
```

El servidor de Vite hace proxy de `/api`, `/carrito`, `/checkout`,
`/static`, `/media` y `/admin` hacia Django, así que la SPA se comporta
igual que en producción. Usa `/static/css/home.css` (la misma hoja que
las plantillas) + `src/extra.css` para los detalles propios de React.

## Producción

```bash
npm run build      # compila a ../static/spa/ con base /static/spa/
```

Luego, en `config/settings.py`, pon `SPA_ACTIVA = True`: Django servirá
`static/spa/index.html` para cualquier ruta que no sea API/carrito, y las
plantillas del MPA quedan retiradas.
