import { createContext, useContext, useEffect, useState } from "react";
import {
  clearTokens,
  get,
  getTokens,
  loginApi,
  logoutApi,
  perfilApi,
  registroApi,
  setBadge,
  setTokens,
  toast,
} from "../api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const guardado = localStorage.getItem("tribuna_user");
      return guardado ? JSON.parse(guardado) : null;
    } catch {
      return null;
    }
  });
  const [cargando, setCargando] = useState(true);

  // Al montar, verificamos la validez del token con /api/auth/perfil/
  useEffect(() => {
    let montado = true;
    async function verificarSesion() {
      const { access, refresh } = getTokens();
      if (!access && !refresh) {
        if (montado) {
          setUser(null);
          setCargando(false);
        }
        return;
      }

      try {
        const resp = await perfilApi();
        if (montado && resp?.user) {
          setUser(resp.user);
          localStorage.setItem("tribuna_user", JSON.stringify(resp.user));
          // Sincronizar badge del carrito con los items guardados del usuario
          get("/carrito/badge/").then((b) => setBadge(b.badge)).catch(() => {});
        }
      } catch {
        if (montado) {
          clearTokens();
          setUser(null);
        }
      } finally {
        if (montado) {
          setCargando(false);
        }
      }
    }

    verificarSesion();
    return () => { montado = false; };
  }, []);

  const login = async (identificador, password) => {
    const data = await loginApi(identificador, password);
    setTokens(data.tokens.access, data.tokens.refresh);
    setUser(data.user);
    localStorage.setItem("tribuna_user", JSON.stringify(data.user));

    // Sincronizar el badge del carrito recuperado/fusionado
    if (typeof data.badge === "number") {
      setBadge(data.badge);
    } else {
      get("/carrito/badge/").then((b) => setBadge(b.badge)).catch(() => {});
    }

    toast(data.mensaje || `¡Bienvenido de nuevo, ${data.user.first_name || data.user.username}!`);
    return data.user;
  };

  const registro = async (datos) => {
    const data = await registroApi(datos);
    setTokens(data.tokens.access, data.tokens.refresh);
    setUser(data.user);
    localStorage.setItem("tribuna_user", JSON.stringify(data.user));

    if (typeof data.badge === "number") {
      setBadge(data.badge);
    } else {
      get("/carrito/badge/").then((b) => setBadge(b.badge)).catch(() => {});
    }

    toast(data.mensaje || "¡Tu cuenta ha sido creada exitosamente!");
    return data.user;
  };

  const logout = async () => {
    try {
      await logoutApi();
    } catch {
      // Ignorar error si el backend no responde
    }
    clearTokens();
    setUser(null);
    setBadge(0);
    toast("Has cerrado sesión.", "info");
  };

  const value = {
    user,
    autenticado: !!user,
    cargando,
    login,
    registro,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth debe usarse dentro de un AuthProvider");
  }
  return ctx;
}
