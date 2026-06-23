export function PriceVar({ pct }: { pct: number | string | null | undefined }) {
  if (pct === null || pct === undefined) return null
  const n = Number(pct)
  if (isNaN(n) || n === 0) return null
  return n > 0 ? (
    <span className="text-red-600 text-xs font-semibold">▲{Math.abs(n)}%</span>
  ) : (
    <span className="text-green-700 text-xs font-semibold">▼{Math.abs(n)}%</span>
  )
}
