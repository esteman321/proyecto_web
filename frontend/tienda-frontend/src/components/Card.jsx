import { Link } from "react-router-dom";
import Jersey from "./Jersey.jsx";
import { money } from "../format.js";

/* Tarjeta de producto (misma estructura que templates/tienda/_card.html).
   Recibe el objeto "producto_json" de la API. */
export default function Card({ p }) {
  return (
    <li className="card">
      <Link to={`/camisetas/${p.id}`} className="card__link">
        {p.imagen
          ? <div className="card__art card__art--foto"><img src={p.imagen} alt={`Camiseta ${p.nombre}`} loading="lazy" decoding="async" /></div>
          : <div className="card__art"><Jersey c1={p.c1} c2={p.c2} /></div>}
        <h3>{p.nombre}</h3>
        <p className="card__meta">
          {(p.tiene_fan || p.tiene_player)
            ? (
              <>
                {p.tiene_fan && <span className="tag tag--fan">Fan</span>}
                {p.tiene_player && <span className="tag tag--player">Player</span>}
              </>
            )
            : <span className={`tag tag--${p.version}`}>{p.version_label}</span>}
          {p.meta && <>· {p.meta}</>}
        </p>
        <p className="card__price">
          {p.tiene_fan && p.tiene_player && <span className="card__from">Desde</span>}
          {money(p.precio_desde)}
        </p>
      </Link>
    </li>
  );
}
