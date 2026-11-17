import { Link } from "react-router-dom";

/* Migas de pan: recibe la lista "migas" de la API [(nombre, url), ...]. */
export default function Crumbs({ items = [] }) {
  return (
    <nav className="wrap crumbs" aria-label="Ruta">
      {items.map(([nombre, url], i) => {
        const ultimo = i === items.length - 1 || url === null;
        return ultimo
          ? <span key={i} aria-current="page">{nombre}</span>
          : (
            <span key={i}>
              <Link to={url}>{nombre}</Link> <span>/</span>
            </span>
          );
      })}
    </nav>
  );
}
