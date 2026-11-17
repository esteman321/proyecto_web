/* Inclinación de la camiseta del hero siguiendo al puntero.
   Replica static/js/home.js: un spring críticamente amortiguado
   (damping 1.0) por eje — sigue al puntero sin rebotar, conserva la
   velocidad si el puntero cambia de dirección y anima desde el valor actual. */
import { useEffect, useRef } from "react";

export default function useTilt() {
  const ref = useRef(null);

  useEffect(() => {
    const stage = ref.current;
    if (!stage || matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const jersey = stage.querySelector(".jersey");
    if (!jersey) return;

    const MAX = 14;                                   // grados máximos
    const response = 0.35;                            // segundos hasta el objetivo
    const k = Math.pow((2 * Math.PI) / response, 2);  // rigidez
    const c = 2 * Math.sqrt(k);                       // amortiguación crítica

    const s = { x: 0, y: 0, vx: 0, vy: 0, tx: 0, ty: 0 };
    let last = performance.now(), running = false;

    const step = (now) => {
      const dt = Math.min((now - last) / 1000, 1 / 30);
      last = now;
      s.vx += (-k * (s.x - s.tx) - c * s.vx) * dt;
      s.vy += (-k * (s.y - s.ty) - c * s.vy) * dt;
      s.x += s.vx * dt;
      s.y += s.vy * dt;
      jersey.style.setProperty("--rx", `${s.x.toFixed(2)}deg`);
      jersey.style.setProperty("--ry", `${s.y.toFixed(2)}deg`);

      const quieto = Math.abs(s.x - s.tx) + Math.abs(s.y - s.ty) + Math.abs(s.vx) + Math.abs(s.vy) < 0.01;
      if (quieto) { running = false; return; }
      requestAnimationFrame(step);
    };
    const kick = () => { if (!running) { running = true; last = performance.now(); requestAnimationFrame(step); } };

    const mover = (e) => {
      const r = stage.getBoundingClientRect();
      const nx = (e.clientX - r.left) / r.width - 0.5;
      const ny = (e.clientY - r.top) / r.height - 0.5;
      s.ty = nx * MAX * 2;
      s.tx = -ny * MAX * 2;
      kick();
    };
    const salir = () => { s.tx = 0; s.ty = 0; kick(); };

    stage.addEventListener("pointermove", mover);
    stage.addEventListener("pointerleave", salir);
    return () => {
      stage.removeEventListener("pointermove", mover);
      stage.removeEventListener("pointerleave", salir);
    };
  }, []);

  return ref;
}
