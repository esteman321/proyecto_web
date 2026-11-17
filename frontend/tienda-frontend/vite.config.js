import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// ── Desarrollo ──────────────────────────────────────────────
// `npm run dev` sirve la SPA en 5173 y pasa al backend de Django
// (8000) todo lo que React no maneja: la API, el carrito, los
// archivos estáticos y los medios.

// ── Producción ──────────────────────────────────────────────
// `npm run build` compila a static/spa/ con rutas absolutas
// /static/spa/..., para que Django lo sirva con SPA_ACTIVA = True.

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  base: mode === "production" ? "/static/spa/" : "/",
  build: {
    outDir: "../static/spa",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/carrito": "http://localhost:8000",
      "/checkout": "http://localhost:8000",
      "/pedido": "http://localhost:8000",
      "/static": "http://localhost:8000",
      "/media": "http://localhost:8000",
      "/admin": "http://localhost:8000",
    },
  },
}));
