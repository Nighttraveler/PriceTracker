export const formatPrice = (n: number) =>
  `$${n?.toLocaleString("es-AR", { maximumFractionDigits: 0 })}`
