/* Título de la pestaña por página: useTitle(`${p.nombre} · Tribuna`). */
import { useEffect } from "react";

export default function useTitle(texto) {
  useEffect(() => {
    document.title = texto || "Tribuna · Camisetas de fútbol";
    return () => { document.title = "Tribuna · Camisetas de fútbol"; };
  }, [texto]);
}
