// ── API JSON de Django y Autenticación JWT ─────────────────────────

export function getTokens() {
  const access = localStorage.getItem("tribuna_access_token");
  const refresh = localStorage.getItem("tribuna_refresh_token");
  return { access, refresh };
}

export function setTokens(access, refresh) {
  if (access) localStorage.setItem("tribuna_access_token", access);
  else localStorage.removeItem("tribuna_access_token");

  if (refresh) localStorage.setItem("tribuna_refresh_token", refresh);
  else localStorage.removeItem("tribuna_refresh_token");
}

export function clearTokens() {
  localStorage.removeItem("tribuna_access_token");
  localStorage.removeItem("tribuna_refresh_token");
  localStorage.removeItem("tribuna_user");
}

/** Token CSRF que Django deja en la cookie (CSRF_COOKIE_HTTPONLY = False). */
function csrf() {
  const cookie = document.cookie.split(";").find(c => c.trim().startsWith("csrftoken="));
  return cookie ? decodeURIComponent(cookie.split("=")[1]) : "";
}

/** Intenta refrescar el token de acceso expirado usando el refresh token. */
export async function refrescarToken() {
  const { refresh } = getTokens();
  if (!refresh) return null;

  try {
    const r = await fetch("/api/auth/token/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!r.ok) {
      clearTokens();
      return null;
    }
    const data = await r.json();
    if (data.access) {
      localStorage.setItem("tribuna_access_token", data.access);
      return data.access;
    }
  } catch {
    clearTokens();
  }
  return null;
}

/** GET que lanza si el servidor responde 4xx/5xx y adjunta token si existe. */
export async function get(url, headers = {}) {
  const { access } = getTokens();
  const reqHeaders = { ...headers };
  if (access) {
    reqHeaders["Authorization"] = `Bearer ${access}`;
  }

  let r = await fetch(url, { headers: reqHeaders });

  // Si da 401 por token expirado, intentar refrescar una vez
  if (r.status === 401 && access) {
    const nuevoAccess = await refrescarToken();
    if (nuevoAccess) {
      reqHeaders["Authorization"] = `Bearer ${nuevoAccess}`;
      r = await fetch(url, { headers: reqHeaders });
    }
  }

  if (!r.ok) {
    const errorData = await r.json().catch(() => ({}));
    const err = new Error(errorData.error || errorData.detail || `HTTP ${r.status}`);
    err.status = r.status;
    err.data = errorData;
    throw err;
  }
  return r.json();
}

/** POST JSON con CSRF y JWT si está disponible. */
export async function post(url, body, headers = {}) {
  const { access } = getTokens();
  const reqHeaders = {
    "Content-Type": "application/json",
    "X-CSRFToken": csrf(),
    ...headers,
  };
  if (access) {
    reqHeaders["Authorization"] = `Bearer ${access}`;
  }

  let r = await fetch(url, {
    method: "POST",
    headers: reqHeaders,
    body: JSON.stringify(body),
  });

  // Si da 401 por token expirado, intentar refrescar una vez
  if (r.status === 401 && access && !url.includes("/auth/")) {
    const nuevoAccess = await refrescarToken();
    if (nuevoAccess) {
      reqHeaders["Authorization"] = `Bearer ${nuevoAccess}`;
      r = await fetch(url, {
        method: "POST",
        headers: reqHeaders,
        body: JSON.stringify(body),
      });
    }
  }

  if (!r.ok) {
    const errorData = await r.json().catch(() => ({}));
    const err = new Error(errorData.error || errorData.detail || `HTTP ${r.status}`);
    err.status = r.status;
    err.data = errorData;
    throw err;
  }
  return r.json();
}

// ── Servicios de autenticación ─────────────────────────────────

export async function loginApi(identificador, password) {
  return post("/api/auth/login/", { username: identificador, password });
}

export async function registroApi(datos) {
  return post("/api/auth/registro/", datos);
}

export async function perfilApi() {
  return get("/api/auth/perfil/");
}

export async function logoutApi() {
  return post("/api/auth/logout/", {});
}

// ── Carrito ───────────────────────────────────────────────────

/** Agrega un producto al carrito y avisa al header (badge) + toast. */
export async function agregarAlCarrito(productoId, talla, cantidad = 1) {
  const data = await post("/carrito/agregar/", { producto_id: productoId, talla, cantidad });
  setBadge(data.badge);
  toast(data.mensaje);
  return data;
}

// ── Eventos de página (los escucha Layout.jsx) ─────────────────

/** Actualiza el número del badge del carrito en el header. */
export function setBadge(n) {
  window.dispatchEvent(new CustomEvent("tribuna:badge", { detail: n }));
}

/** Muestra un toast (mensaje corto abajo). */
export function toast(mensaje, tipo = "success") {
  window.dispatchEvent(new CustomEvent("tribuna:toast", { detail: { mensaje, tipo } }));
}
