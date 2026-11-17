import { Link } from "react-router-dom";

/* Selector de ligas / equipos con escudos (templates/tienda/_escudo.html).
   item = {nombre, url, escudo, activo, iniciales}; size = "lg" | "sm";
   dim = atenuar todos si hay uno seleccionado. */
export default function Picker({ items = [], size = "sm", dim = false, ariaLabel }) {
  return (
    <ul className={`picker picker--${size === "lg" ? "ligas" : "equipos"}`} aria-label={ariaLabel}>
      {items.map((item, i) => (
        <li key={i}>
          <Link
            className={`badge badge--${size}${item.activo ? " is-active" : dim ? " is-dim" : ""}`}
            to={item.url}
            aria-current={item.activo ? "page" : undefined}
          >
            {item.escudo
              ? <span className="badge__disc"><img src={item.escudo} alt="" loading="lazy" /></span>
              : <span className="badge__disc badge__disc--mono"><span className="badge__ini">{item.iniciales}</span></span>}
            <span className="badge__name">{item.nombre}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
