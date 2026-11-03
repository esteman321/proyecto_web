/* Inclinación de la camiseta del hero.
   Usa un spring críticamente amortiguado (damping 1.0): sigue al puntero sin rebotar,
   conserva la velocidad si el puntero cambia de dirección y siempre anima desde el valor actual. */
(() => {
  const stage = document.querySelector('[data-tilt]');
  if (!stage || matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const jersey = stage.querySelector('.jersey');
  const MAX = 14;                        // grados máximos de inclinación
  const response = 0.35;                 // qué tan rápido llega al objetivo (segundos)
  const k = Math.pow((2 * Math.PI) / response, 2); // rigidez
  const c = 2 * Math.sqrt(k);            // amortiguación crítica

  const s = { x: 0, y: 0, vx: 0, vy: 0, tx: 0, ty: 0 };
  let last = performance.now(), running = false;

  const step = (now) => {
    const dt = Math.min((now - last) / 1000, 1 / 30);
    last = now;
    // X e Y se resuelven como springs independientes
    s.vx += (-k * (s.x - s.tx) - c * s.vx) * dt;
    s.vy += (-k * (s.y - s.ty) - c * s.vy) * dt;
    s.x += s.vx * dt;
    s.y += s.vy * dt;
    jersey.style.setProperty('--rx', `${s.x.toFixed(2)}deg`);
    jersey.style.setProperty('--ry', `${s.y.toFixed(2)}deg`);

    const settled = Math.abs(s.x - s.tx) + Math.abs(s.y - s.ty) + Math.abs(s.vx) + Math.abs(s.vy) < 0.01;
    if (settled) { running = false; return; }
    requestAnimationFrame(step);
  };
  const kick = () => { if (!running) { running = true; last = performance.now(); requestAnimationFrame(step); } };

  stage.addEventListener('pointermove', (e) => {
    const r = stage.getBoundingClientRect();
    const nx = (e.clientX - r.left) / r.width - 0.5;
    const ny = (e.clientY - r.top) / r.height - 0.5;
    s.ty = nx * MAX * 2;
    s.tx = -ny * MAX * 2;
    kick();
  });
  stage.addEventListener('pointerleave', () => { s.tx = 0; s.ty = 0; kick(); });
})();