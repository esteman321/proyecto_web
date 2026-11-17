import { Link } from "react-router-dom";

/* Anterior / "Página X de Y" / Siguiente.  `base` es la ruta actual
   y `params` los search params que se deben conservar (filtros, eq). */
export default function Pager({ numero, paginas, base, params = "" }) {
  if (paginas <= 1) return null;
  const con = (p) => `${base}${params ? `?${params}&page=${p}` : `?page=${p}`}`;
  return (
    <nav className="pager" aria-label="Paginación">
      {numero > 1 && <Link className="btn btn--soft" to={con(numero - 1)}>Anterior</Link>}
      <span className="pager__info">Página {numero} de {paginas}</span>
      {numero < paginas && <Link className="btn btn--soft" to={con(numero + 1)}>Siguiente</Link>}
    </nav>
  );
}
