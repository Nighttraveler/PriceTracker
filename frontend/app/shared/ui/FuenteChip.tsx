const COLORS: Record<string, string> = {
  dia: "bg-orange-500",
  anonima: "bg-red-600",
  encombo: "bg-blue-500",
  carrefour: "bg-blue-900",
}

export function FuenteChip({ fuente }: { fuente: string }) {
  const color = COLORS[fuente] ?? "bg-neutral-500"
  return (
    <span className={`${color} text-white text-[0.7rem] font-semibold px-2 py-0.5 rounded-full`}>
      {fuente.charAt(0).toUpperCase() + fuente.slice(1)}
    </span>
  )
}
