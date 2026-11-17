import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import useTitle from "../hooks/useTitle.js";

export default function Register() {
  useTitle("Crear Cuenta · Tribuna");
  const { registro, autenticado } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [formulario, setFormulario] = useState({
    first_name: "",
    last_name: "",
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [verPassword, setVerPassword] = useState(false);
  const [error, setError] = useState(null);
  const [enviando, setEnviando] = useState(false);

  const destino = location.state?.from || "/";
  if (autenticado) {
    navigate(destino, { replace: true });
    return null;
  }

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormulario((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const { first_name, last_name, username, email, password, confirmPassword } = formulario;

    if (!username.trim() || !email.trim() || !password) {
      setError("Por favor completa los campos obligatorios.");
      return;
    }

    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    try {
      setEnviando(true);
      await registro({
        first_name: first_name.trim(),
        last_name: last_name.trim(),
        username: username.trim(),
        email: email.trim(),
        password,
      });
      navigate(destino, { replace: true });
    } catch (err) {
      setError(err.message || "Error al crear la cuenta. Inténtalo de nuevo.");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="wrap auth-wrapper">
      <div className="auth-card">
        <div className="auth-card__header">
          <span className="auth-card__badge">Únete a Tribuna</span>
          <h1>Crear Cuenta</h1>
          <p>Regístrate para comprar más rápido y seguir el estado de tus pedidos.</p>
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
          <div className="auth-field-row">
            <label className="field">
              <span>Nombre</span>
              <input
                type="text"
                name="first_name"
                value={formulario.first_name}
                onChange={handleChange}
                placeholder="Juan"
                autoComplete="given-name"
              />
            </label>

            <label className="field">
              <span>Apellido</span>
              <input
                type="text"
                name="last_name"
                value={formulario.last_name}
                onChange={handleChange}
                placeholder="Pérez"
                autoComplete="family-name"
              />
            </label>
          </div>

          <label className="field">
            <span>Nombre de Usuario *</span>
            <input
              type="text"
              name="username"
              value={formulario.username}
              onChange={handleChange}
              placeholder="ej. juan_perez"
              autoComplete="username"
              required
            />
          </label>

          <label className="field">
            <span>Correo Electrónico *</span>
            <input
              type="email"
              name="email"
              value={formulario.email}
              onChange={handleChange}
              placeholder="juan@ejemplo.com"
              autoComplete="email"
              required
            />
          </label>

          <label className="field">
            <span>Contraseña * (mínimo 6 caracteres)</span>
            <div className="auth-password-toggle">
              <input
                type={verPassword ? "text" : "password"}
                name="password"
                value={formulario.password}
                onChange={handleChange}
                placeholder="••••••••"
                autoComplete="new-password"
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

          <label className="field">
            <span>Confirmar Contraseña *</span>
            <div className="auth-password-toggle">
              <input
                type={verPassword ? "text" : "password"}
                name="confirmPassword"
                value={formulario.confirmPassword}
                onChange={handleChange}
                placeholder="••••••••"
                autoComplete="new-password"
                required
              />
            </div>
          </label>

          <button
            type="submit"
            className="btn btn--primary auth-submit-btn"
            disabled={enviando}
          >
            {enviando ? "Creando cuenta..." : "Crear Cuenta"}
          </button>
        </form>

        <div className="auth-footer">
          ¿Ya tienes una cuenta?{" "}
          <Link to="/login" state={{ from: destino }}>
            Inicia sesión aquí
          </Link>
        </div>
      </div>
    </div>
  );
}
