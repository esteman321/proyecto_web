import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { get } from "../api.js";
import Card from "../components/Card.jsx";
import Pager from "../components/Pager.jsx";
import { Cargando, Empty, Error } from "../components/State.jsx";
import useTitle from "../hooks/useTitle.js";
import { plural } from "../format.js";

/* Catálogo completo ("Todo"): filtros GET con la misma semántica de
   catalogo.html.  Los filtros viven en la URL, así que cada vista es
   compartible con adelante/atrás del navegador. */
const FILTROS = [
  ["tipo", "Tipo", [["", "Todos"], ["club", "Club"], ["seleccion", "Selección"]]],
  ["version", "Versión", [["", "Todas"], ["fan", "Fan"], ["player", "Player"]]],
  ["equipacion", "Equipación", [["", "Todas"], ["local", "Local"], ["visitante", "Visitante"], ["tercera", "Tercera"]]],
];
const ORDENES = [["nuevo", "Más nuevas"], ["precio_asc", "Precio: menor a mayor"],
                 ["precio_desc", "Precio: mayor a menor"], ["nombre", "Nombre A–Z"]];

export default function Catalog() {
  useTitle("Camisetas · Tribuna");
  const [params, setParams] = useSearchParams();
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState(null);
  const [texto, setTexto] = useState(params.get("q") || "");

  // El formulario actualiza la URL; el efecto consulta la API
  const qs = params.toString();

  useEffect(() => {
    let activo = true;
    setDatos(null);
    setError(null);
    get(`/api/camisetas/${qs ? `?${qs}` : ""}`)
      .then(d => { if (activo) setDatos(d); })
      .catch(e => { if (activo) setError(e); });
    return () => { activo = false; };
  }, [qs]);

  useEffect(() => { setTexto(params.get("q") || ""); }, [qs]);

  function aplicar(e) {
    e.preventDefault();
    const nueva = new URLSearchParams(params);
    if (texto) nueva.set("q", texto); else nueva.delete("q");
    nueva.delete("page");
    setParams(nueva);
  }

  function cambiar(clave, valor) {
    const nueva = new URLSearchParams(params);
    if (valor) nueva.set(clave, valor); else nueva.delete(clave);
    nueva.delete("page"); // al cambiar un filtro, vuelve a la página 1
    setParams(nueva);
  }

  if (error) return <div className="wrap"><Error /></div>;

  const pagina = datos?.pagina;
  const opciones = datos?.opciones;
  const filtros = datos?.filtros;

  return (
    <>
      <section className="wrap page-head">
        <h1 className="page-title">Camisetas</h1>
        <p className="lead">{pagina ? `${pagina.total} ${plural(pagina.total, "resultado")}` : "Cargando…"}</p>
      </section>

      <form className="wrap filters" method="get" action="/camisetas">
        <label className="field field--grow">
          <span>Buscar</span>
          <input type="search" name="q" value={texto} placeholder="Equipo o camiseta" onChange={e => setTexto(e.target.value)} />
        </label>
        {FILTROS.map(([clave, etiqueta, opcionesDuras]) => (
          <label className="field" key={clave}>
            <span>{etiqueta}</span>
            <select name={clave} value={filtros?.[clave] ?? params.get(clave) ?? ""} onChange={e => cambiar(clave, e.target.value)}>
              {opcionesDuras.map(([valor, nombre]) => <option key={valor} value={valor}>{nombre}</option>)}
            </select>
          </label>
        ))}
        <label className="field">
          <span>Liga</span>
          <select name="liga" value={filtros?.liga ?? params.get("liga") ?? ""} onChange={e => cambiar("liga", e.target.value)}>
            <option value="">Todas</option>
            {opciones?.ligas.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </label>
        <label className="field">
          <span>Temporada</span>
          <select name="temporada" value={filtros?.temporada ?? params.get("temporada") ?? ""} onChange={e => cambiar("temporada", e.target.value)}>
            <option value="">Todas</option>
            {opciones?.temporadas.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </label>
        <label className="field">
          <span>Ordenar</span>
          <select name="orden" value={filtros?.orden ?? params.get("orden") ?? "nuevo"} onChange={e => cambiar("orden", e.target.value)}>
            {ORDENES.map(([valor, nombre]) => <option key={valor} value={valor}>{nombre}</option>)}
          </select>
        </label>
        <button className="btn btn--primary btn--sm" type="submit">Aplicar</button>
        <Link className="link filters__clear" to="/camisetas">Limpiar</Link>
      </form>

      <section className="wrap section section--tight">
        {!datos && <Cargando />}
        {datos && pagina.items.length > 0 && (
          <>
            <ul className="grid">
              {pagina.items.map(p => <Card key={p.id} p={p} />)}
            </ul>
            <Pager numero={pagina.numero} paginas={pagina.paginas} base="/camisetas" params={qs.replace(/&?page=\d+/, "")} />
          </>
        )}
        {datos && pagina.items.length === 0 && (
          <Empty titulo="No encontramos camisetas">
            <p>Prueba con otros filtros o una búsqueda distinta.</p>
            <Link className="btn btn--primary" to="/camisetas">Ver todo el catálogo</Link>
          </Empty>
        )}
      </section>
    </>
  );
}
