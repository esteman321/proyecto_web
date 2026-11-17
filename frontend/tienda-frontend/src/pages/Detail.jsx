import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { agregarAlCarrito, get } from "../api.js";
import Card from "../components/Card.jsx";
import Crumbs from "../components/Crumbs.jsx";
import Jersey from "../components/Jersey.jsx";
import { Cargando, Empty, Error } from "../components/State.jsx";
import useTitle from "../hooks/useTitle.js";
import { money } from "../format.js";

/* Detalle de la camiseta: foto o jersey SVG, versión Fan/Player,
   tallas, specs, agregar al carrito y relacionados. */
export default function Detail() {
  const { id } = useParams();
  const [datos, setDatos] = useState(null); // {producto, equipo, hermano, ...}
  const [error, setError] = useState(null);
  const [talla, setTalla] = useState("M");
  const [estado, setEstado] = useState("normal"); // normal | cargando | listo

  useTitle(datos ? `${datos.producto.nombre} · Tribuna` : "Tribuna");

  useEffect(() => {
    let activo = true;
    setDatos(null);
    setError(null);
    setEstado("normal");
    get(`/api/camisetas/${id}/`)
      .then(d => { if (activo) setDatos(d); })
      .catch(e => { if (activo) setError(e); });
    return () => { activo = false; };
  }, [id]);

  if (error) {
    return error.message === "HTTP 404"
      ? <Empty titulo="No encontramos esa camiseta"><Link className="btn btn--primary" to="/camisetas">Ver el catálogo</Link></Empty>
      : <div className="wrap"><Error /></div>;
  }
  if (!datos) return <div className="wrap"><Cargando /></div>;

  const { producto: p, hermano, relacionados } = datos;

  async function agregar() {
    setEstado("cargando");
    try {
      await agregarAlCarrito(p.id, talla);
      setEstado("listo");
      setTimeout(() => setEstado("normal"), 1600);
    } catch {
      setEstado("normal");
    }
  }

  return (
    <>
      <Crumbs items={[...datos.migas, [p.nombre, null]]} />

      <section className="wrap detail">
        {p.imagen
          ? <div className="detail__art detail__art--foto"><img src={p.imagen} alt={`Camiseta ${p.nombre}`} /></div>
          : <div className="detail__art"><Jersey c1={p.c1} c2={p.c2} /></div>}

        <div className="detail__info">
          <p className="eyebrow">
            {datos.equipo.tipo}{datos.equipo.liga ? ` · ${datos.equipo.liga}` : datos.equipo.pais ? ` · ${datos.equipo.pais}` : ""}
          </p>
          <h1 className="detail__title">{p.nombre}</h1>
          {p.meta && <p className="detail__meta">{p.meta}</p>}
          <p className="detail__price">{money(p.precio)}</p>

          {hermano && (
            <div className="seg" role="group" aria-label="Versión">
              {p.version === "fan"
                ? (
                  <>
                    <span className="seg__item is-active" aria-current="true">Fan <small>{money(p.precio)}</small></span>
                    <Link className="seg__item" to={`/camisetas/${hermano.id}`}>Player <small>{money(hermano.precio)}</small></Link>
                  </>
                )
                : (
                  <>
                    <Link className="seg__item" to={`/camisetas/${hermano.id}`}>Fan <small>{money(hermano.precio)}</small></Link>
                    <span className="seg__item is-active" aria-current="true">Player <small>{money(p.precio)}</small></span>
                  </>
                )}
            </div>
          )}
          {datos.info_version && <p className="detail__note">{datos.info_version}</p>}

          <fieldset className="sizes">
            <legend>Talla</legend>
            {datos.tallas.map(t => (
              <label className="size" key={t}>
                <input type="radio" name="talla" value={t} checked={talla === t} onChange={() => setTalla(t)} />
                <span>{t}</span>
              </label>
            ))}
          </fieldset>

          <div className="detail__cta">
            <button className="btn btn--blue" type="button" onClick={agregar} disabled={estado === "cargando"}>
              {estado === "cargando" ? "Agregando…" : estado === "listo" ? "✓ Agregado" : "Agregar al carrito"}
            </button>
            <a className="btn btn--soft" href="/carrito/">Ver carrito</a>
          </div>

          <dl className="specs">
            <div><dt>Equipo</dt><dd>{datos.equipo.nombre}</dd></div>
            <div><dt>Versión</dt><dd>{p.version_label}</dd></div>
            {p.equipacion_definida && <div><dt>Equipación</dt><dd>{p.equipacion_label}</dd></div>}
            {p.temporada && <div><dt>Temporada</dt><dd>{p.temporada}</dd></div>}
          </dl>
        </div>
      </section>

      {relacionados.length > 0 && (
        <section className="wrap section related">
          <div className="section__head">
            <h2>También te puede interesar</h2>
            <Link className="link" to={datos.url_equipo}>Ver más de {datos.equipo.nombre}</Link>
          </div>
          <ul className="grid">
            {relacionados.map(r => <Card key={r.id} p={r} />)}
          </ul>
        </section>
      )}
    </>
  );
}
