import { Link } from "react-router-dom";
import { Empty } from "../components/State.jsx";
import useTitle from "../hooks/useTitle.js";

/* Ruta inexistente dentro de la SPA. */
export default function NotFound() {
  useTitle("Página no encontrada · Tribuna");
  return (
    <div className="wrap section">
      <Empty titulo="404 · La jugada no salió">
        <p>Esta página no existe o se movió de lugar.</p>
        <Link className="btn btn--primary" to="/">Volver al inicio</Link>
      </Empty>
    </div>
  );
}
