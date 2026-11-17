/* Estados vacíos y de carga, con la clase .empty de home.css. */
export function Empty({ titulo, children }) {
  return (
    <div className="empty">
      <h2>{titulo}</h2>
      {children}
    </div>
  );
}

export function Cargando({ texto = "Cargando…" }) {
  return <div className="empty"><p className="lead">{texto}</p></div>;
}

export function Error({ texto = "No se pudo conectar con el servidor." }) {
  return <div className="empty"><h2>Ups</h2><p>{texto}</p></div>;
}
