import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import useTitle from "../hooks/useTitle.js";

export default function Login() {
  useTitle("Iniciar Sesión · Tribuna");
  const { login, autenticado } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [identificador, setIdentificador] = useState("");
  const [password, setPassword] = useState("");
  const [verPassword, setVerPassword] = useState(false);
  const [error, setError] = useState(null);
  const [enviando, setEnviando] = useState(false);

  // Si ya está autenticado, redirigir a donde venía o a la portada
  const destino = location.state?.from || "/";
  if (autenticado) {
    navigate(destino, { replace: true });
    return null;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!identificador.trim() || !password) {
      setError("Por favor completa todos los campos.");
      return;
    }

    try {
      setEnviando(true);
      await login(identificador.trim(), password);
      navigate(destino, { replace: true });
    } catch (err) {
      setError(err.message || "Error al iniciar sesión. Inténtalo de nuevo.");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="wrap auth-wrapper">
      <div className="auth-card">
        <div className="auth-card__header">
          <span className="auth-card__badge">Cuenta Tribuna</span>
          <h1>Iniciar Sesión</h1>
          <p>Ingresa a tu cuenta para gestionar tus compras y favoritos.</p>
        </div>

        {error && (
          <div className="auth-error" role="alert">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form" style={{ marginTop: error ? "1.25rem" : "0" }}>
          <label className="field">
            <span>Usuario o Correo Electrónico</span>
            <input
              type="text"
              name="identificador"
              value={identificador}
              onChange={(e) => setIdentificador(e.target.value)}
              placeholder="ej. juan_perez o usuario@correo.com"
              autoComplete="username"
              required
              autoFocus
            />
          </label>

          <label className="field">
            <span>Contraseña</span>
            <div className="auth-password-toggle">
              <input
                type={verPassword ? "text" : "password"}
                name="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                className="auth-password-btn"
                onClick={() => setVerPassword(!verPassword)}
                aria-label={verPassword ? "Ocultar contraseña" : "Ver contraseña"}
                tabIndex="-1"
              >
                {verPassword ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </label>

          <button
            type="submit"
            className="btn btn--primary auth-submit-btn"
            disabled={enviando}
          >
            {enviando ? "Iniciando sesión..." : "Iniciar Sesión"}
          </button>
        </form>

        <div className="auth-footer">
          ¿No tienes una cuenta aún?{" "}
          <Link to="/registro" state={{ from: destino }}>
            Regístrate aquí
          </Link>
        </div>
      </div>
    </div>
  );
}
