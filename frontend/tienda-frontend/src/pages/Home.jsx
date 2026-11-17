import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../api.js";
import Card from "../components/Card.jsx";
import Jersey from "../components/Jersey.jsx";
import { Cargando, Error } from "../components/State.jsx";
import useTilt from "../hooks/useTilt.js";
import useTitle from "../hooks/useTitle.js";

/* Portada: hero con camiseta que se inclina, categorías, novedades y promo. */
export default function Home() {
  useTitle("Tribuna · Camisetas de fútbol");
  const inclinar = useTilt();
  const [novedades, setNovedades] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    get("/api/home/").then(d => setNovedades(d.novedades)).catch(e => setError(e));
  }, []);

  return (
    <>
      <section className="hero">
        <div className="wrap hero__inner">
          <div className="hero__text">
            <h1>La camiseta de tu equipo, a tu talla.</h1>
            <p className="lead">Selecciones y clubes de todo el mundo. Elige, compara y recibe en casa.</p>
            <div className="hero__cta">
              <a href="#novedades" className="btn btn--primary">Ver novedades</a>
              <Link to="/selecciones" className="btn btn--ghost">Explorar selecciones</Link>
            </div>
          </div>
          <div className="hero__stage" ref={inclinar} data-tilt>
            <Jersey c1="#FCD116" c2="#003893" />
          </div>
        </div>
      </section>

      <section className="section wrap" id="categorias">
        <h2>Compra por categoría</h2>
        <div className="tiles">
          <Link to="/selecciones" className="tile tile--wide">
            <h3>Selecciones</h3>
            <p>Eliminatorias, Copa América y Mundial.</p>
            <div className="tile__art"><Jersey c1="#FCD116" c2="#CE1126" /></div>
          </Link>
          <Link to="/clubes" className="tile">
            <h3>Clubes</h3>
            <p>Local, visitante y tercera.</p>
            <div className="tile__art"><Jersey c1="#0B6E3A" c2="#FFFFFF" /></div>
          </Link>
          <Link to="/retro" className="tile">
            <h3>Retro</h3>
            <p>Diseños que hicieron historia.</p>
            <div className="tile__art"><Jersey c1="#1B2A4A" c2="#E8C547" /></div>
          </Link>
        </div>
      </section>

      <section className="section" id="novedades">
        <div className="wrap section__head">
          <h2>Recién llegadas</h2>
          <Link to="/camisetas" className="link">Ver todo</Link>
        </div>
        {error && <div className="wrap"><Error /></div>}
        {!error && !novedades && <div className="wrap"><Cargando /></div>}
        {novedades && (
          <ul className="rail" tabIndex="0" aria-label="Camisetas recién llegadas">
            {novedades.map(p => <Card key={p.id} p={p} />)}
          </ul>
        )}
      </section>

      <section className="section wrap">
        <div className="promo">
          <h2>Elige tu talla sin dudas</h2>
          <p>Guía de tallas en cada camiseta y cambios sin costo en los primeros 15 días.</p>
          <Link to="/camisetas" className="btn btn--light">Ver catálogo</Link>
        </div>
      </section>
    </>
  );
}
