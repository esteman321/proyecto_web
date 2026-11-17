import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { get } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";

/* Toast: escucha eventos "tribuna:toast" de cualquier página. */
function Toast() {
  const [aviso, setAviso] = useState(null); // {mensaje, tipo}

  useEffect(() => {
    const mostrar = (e) => {
      setAviso(e.detail);
      clearTimeout(mostrar._timer);
      mostrar._timer = setTimeout(() => setAviso(null), 2800);
    };
    window.addEventListener("tribuna:toast", mostrar);
    return () => window.removeEventListener("tribuna:toast", mostrar);
  }, []);

  if (!aviso) return null;
  return <div className={`toast toast--${aviso.tipo} toast--show`}>{aviso.mensaje}</div>;
}

/* Badge del carrito: se carga al abrir y se actualiza con eventos. */
function CartBadge() {
  const [n, setN] = useState(0);

  useEffect(() => {
    get("/carrito/badge/").then(d => setN(d.badge)).catch(() => {});
    const alCambiar = (e) => setN(e.detail);
    window.addEventListener("tribuna:badge", alCambiar);
    return () => window.removeEventListener("tribuna:badge", alCambiar);
  }, []);

  return (
    <span className={`cart-badge${n > 0 ? " cart-badge--bounce" : ""}`} style={n > 0 ? null : { display: "none" }}>
      {n}
    </span>
  );
}

/* Menú de usuario en la barra de navegación. */
function UserNav() {
  const { user, autenticado, logout } = useAuth();
  const [menuAbierto, setMenuAbierto] = useState(false);

  // Cerrar menú al hacer clic fuera
  useEffect(() => {
    if (!menuAbierto) return;
    const cerrar = (e) => {
      if (!e.target.closest(".nav__user-wrapper")) {
        setMenuAbierto(false);
      }
    };
    window.addEventListener("click", cerrar);
    return () => window.removeEventListener("click", cerrar);
  }, [menuAbierto]);

  if (!autenticado) {
    return (
      <Link to="/login" className="nav__auth-btn" aria-label="Iniciar Sesión">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
        <span>Ingresar</span>
      </Link>
    );
  }

  const inicial = (user?.first_name || user?.username || "U")[0].toUpperCase();
  const nombreMostrar = user?.first_name || user?.username;

  return (
    <div className="nav__user-wrapper">
      <button
        type="button"
        className="nav__user-trigger"
        onClick={() => setMenuAbierto(!menuAbierto)}
        aria-expanded={menuAbierto}
        aria-label="Menú de usuario"
      >
        <span className="nav__user-avatar">{inicial}</span>
        <span className="nav__user-name">{nombreMostrar}</span>
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            transform: menuAbierto ? "rotate(180deg)" : "none",
            transition: "transform 150ms",
          }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {menuAbierto && (
        <div className="nav__dropdown">
          <div className="nav__dropdown-header">
            <strong>{user.first_name ? `${user.first_name} ${user.last_name || ""}`.trim() : user.username}</strong>
            <span>{user.email}</span>
          </div>

          <button
            type="button"
            className="nav__dropdown-item nav__dropdown-item--danger"
            onClick={() => {
              setMenuAbierto(false);
              logout();
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            <span>Cerrar Sesión</span>
          </button>
        </div>
      )}
    </div>
  );
}

/* Header + contenido + footer. El carrito/checkout siguen siendo páginas de Django. */
export default function Layout({ children }) {
  const { pathname } = useLocation();

  // Al cambiar de ruta, vuelve arriba (como una página nueva)
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);

  return (
    <>
      <header className="nav">
        <nav className="nav__inner" aria-label="Principal">
          <Link className="nav__brand" to="/">Tribuna</Link>
          <ul className="nav__links">
            <li><NavLink to="/selecciones">Selecciones</NavLink></li>
            <li><NavLink to="/clubes">Clubes</NavLink></li>
            <li><NavLink to="/retro">Retro</NavLink></li>
            <li><NavLink to="/camisetas">Todo</NavLink></li>
          </ul>
          <div className="nav__actions">
            <Link to="/camisetas" aria-label="Buscar" className="icon-btn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
            </Link>
            {/* El carrito y el checkout son páginas de Django: enlace normal,
                no <Link>, para que el navegador salga de la SPA al proxy/Django. */}
            <a href="/carrito/" aria-label="Carrito" className="icon-btn icon-btn--cart">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 8h14l-1 12H6L5 8Z"/><path d="M9 8a3 3 0 0 1 6 0"/></svg>
              <CartBadge />
            </a>
            <UserNav />
          </div>
        </nav>
      </header>

      <main>{children}</main>

      <footer className="footer">
        <div className="wrap footer__inner">
          <p className="footer__brand">Tribuna</p>
        </div>
      </footer>

      <Toast />
    </>
  );
}
