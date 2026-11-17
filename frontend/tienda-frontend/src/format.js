// ── Formato de valores ──────────────────────────────────────────

/** 189900 -> "$ 189.900" */
export function money(valor) {
  return "$ " + Number(valor).toLocaleString("es-CO");
}

/** "resultado"/"resultados" según el número. */
export function plural(n, uno, muchos) {
  return n === 1 ? uno : (muchos ?? `${uno}s`);
}
