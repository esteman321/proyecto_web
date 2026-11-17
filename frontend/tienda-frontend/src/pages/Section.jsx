import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { get } from "../api.js";
import Card from "../components/Card.jsx";
import Crumbs from "../components/Crumbs.jsx";
import Pager from "../components/Pager.jsx";
import Picker from "../components/Picker.jsx";
import { Cargando, Empty, Error } from "../components/State.jsx";
import useTitle from "../hooks/useTitle.js";

/* Secciones: Clubes y Retro (liga -> club -> equipación) y Selecciones
   (selección -> equipación).  Los datos salen de /api/... con la misma
   estructura que usa seccion.html. */
export default function Section({ seccion }) {
  const { liga, equipo } = useParams();
  const [params] = useSearchParams();
  const eq = params.get("eq") || "";
  const page = params.get("page") || "";

  const [datos, setDatos] = useState(null); // respuesta de la API
  const [error, setError] = useState(null);

  // Arma la URL de la API igual que tienda/urls.py
  let url = seccion === "selecciones"
    ? "/api/selecciones/"
    : `/api/${seccion}/`;
  if (liga) url += `${liga}/`;
  if (equipo) url += `${equipo}/`;
  const consulta = new URLSearchParams();
  if (eq) consulta.set("eq", eq);
  if (page) consulta.set("page", page);
  const qs = consulta.toString();

  useTitle(datos ? `${datos.titulo} · Tribuna` : "Tribuna");

  useEffect(() => {
    let activo = true;
    setDatos(null);
    setError(null);
    get(url + (qs ? `?${qs}` : ""))
      .then(d => { if (activo) setDatos(d); })
      .catch(e => { if (activo) setError(e); });
    return () => { activo = false; };
  }, [url, qs]);

  if (error) {
    return error.message === "HTTP 404"
      ? <Empty titulo="No encontramos esa página"><Link className="btn btn--primary" to="/">Volver al inicio</Link></Empty>
      : <div className="wrap"><Error /></div>;
  }
  if (!datos) return <div className="wrap"><Cargando /></div>;

  const haySelector = datos.selector && datos.selector.some(s => s.count > 0);
  const base = datos.migas.at(-1)?.[1] || `/${seccion}`;

  return (
    <>
      <Crumbs items={datos.migas} />

      <section className="wrap picker-head">
        <p className="eyebrow">{datos.eyebrow}</p>
        <h1 className="page-title">{datos.titulo}</h1>
        <p className="lead">{datos.subtitulo}</p>
      </section>

      <section className="wrap picker-panel">
        {datos.ligas && <Picker items={datos.ligas} size="lg" dim={datos.liga_sel} ariaLabel="Ligas" />}
        {datos.ligas && datos.equipos && <hr className="picker__sep" />}
        {datos.equipos && <Picker items={datos.equipos} size="sm" dim={datos.equipo_sel} ariaLabel="Equipos" />}
        {!datos.ligas && !datos.equipos && (
          <Empty titulo="Aún no hay camisetas aquí">
            <p>Cuando cargues productos de esta sección aparecerán sus ligas y equipos.</p>
          </Empty>
        )}
      </section>

      {haySelector && (
        <section className="wrap selector-bar">
          <p className="picker__label">Equipación</p>
          <div className="seg" role="group" aria-label="Equipación">
            {datos.selector.map(s => s.count > 0
              ? <Link key={s.nombre} className={`seg__item${s.activo ? " is-active" : ""}`} to={s.url} aria-current={s.activo ? "true" : undefined}>{s.nombre} <small>{s.count}</small></Link>
              : <span key={s.nombre} className="seg__item is-disabled">{s.nombre} <small>0</small></span>)}
          </div>
        </section>
      )}

      {datos.pagina && (
        <section className="wrap section section--tight">
          {datos.pagina.items.length > 0
            ? (
              <>
                <ul className="grid">
                  {datos.pagina.items.map(p => <Card key={p.id} p={p} />)}
                </ul>
                <Pager numero={datos.pagina.numero} paginas={datos.pagina.paginas} base={base} params={qs.replace(/&?page=\d+/, "")} />
              </>
            )
            : (
              <Empty titulo="No hay camisetas en esta selección">
                <Link className="btn btn--primary" to="/camisetas">Ver todo el catálogo</Link>
              </Empty>
            )}
        </section>
      )}

      {!datos.pagina && (
        <section className="wrap section section--tight picker-foot">
          <Link className="link" to="/camisetas">Prefiero ver todas las camisetas</Link>
        </section>
      )}
    </>
  );
}
