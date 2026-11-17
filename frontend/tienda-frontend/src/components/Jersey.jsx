/* Camiseta dibujada con SVG usando los colores del producto
   (la misma figura de templates/tienda/_camiseta.html). */
export default function Jersey({ c1 = "#FCD116", c2 = "#003893", className = "jersey" }) {
  return (
    <svg className={className} viewBox="0 0 200 200" role="img" aria-hidden="true">
      <path style={{ fill: c2 }} d="M70 20 40 30 10 70l25 20 15-12V40Z" />
      <path style={{ fill: c2 }} d="M130 20l30 10 30 40-25 20-15-12V40Z" />
      <path style={{ fill: c1 }} d="M70 20Q100 48 130 20L150 40v140H50V40Z" />
      <path style={{ fill: c2, opacity: 0.9 }} d="M50 104h100v18H50Z" />
      <path style={{ fill: "none", stroke: c2, strokeWidth: 6, strokeLinecap: "round" }} d="M70 20Q100 48 130 20" />
    </svg>
  );
}
