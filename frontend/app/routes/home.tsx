import { useSearchParams, Link } from "react-router"
import { useQuery } from "@tanstack/react-query"
import type { Route } from "./+types/home"
import { api } from "~/shared/lib/api"
import { FuenteChip } from "~/shared/ui/FuenteChip"
import { PriceVar } from "~/shared/ui/PriceVar"
import { CartButton } from "~/shared/ui/CartButton"
import { Card, CardContent, CardHeader } from "~/shared/ui/shadcn/card"

export function meta(_: Route.MetaArgs) {
  return [{ title: "Dashboard — Price Tracker" }]
}

export async function loader({ request }: Route.LoaderArgs) {
  const url = new URL(request.url)
  const dias = url.searchParams.get("dias") ?? "7"
  const { data } = await api.get(`/api/v1/dashboard?dias=${dias}`)
  return data
}

const fmt = (n: number) =>
  n?.toLocaleString("es-AR", { maximumFractionDigits: 0 })

export default function Dashboard({ loaderData }: Route.ComponentProps) {
  const [searchParams, setSearchParams] = useSearchParams()
  const dias = Number(searchParams.get("dias") ?? 7)

  const { data } = useQuery({
    queryKey: ["dashboard", dias],
    queryFn: () => api.get(`/api/v1/dashboard?dias=${dias}`).then((r) => r.data),
    initialData: loaderData,
    staleTime: 5 * 60 * 1000,
  })

  const { stats, top_baratos, highlights } = data

  return (
    <div>
      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {[
          { num: fmt(stats.productos), label: "Productos" },
          { num: fmt(stats.variantes), label: "Variantes" },
          { num: fmt(stats.precios), label: "Registros de precio" },
          {
            num: <span className="text-base">{stats.ultima_fecha ?? "—"}</span>,
            label: (
              <div>
                <div className="mb-1">Última actualización</div>
                <div className="flex flex-wrap gap-1">
                  {stats.fuentes?.map((f: { nombre: string }) => (
                    <FuenteChip key={f.nombre} fuente={f.nombre} />
                  ))}
                </div>
              </div>
            ),
          },
        ].map((s, i) => (
          <Card key={i}>
            <CardContent className="pt-4">
              <div className="text-3xl font-bold">{s.num}</div>
              <div className="text-xs text-muted-foreground mt-1">{s.label}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Top canasta */}
      {top_baratos?.length > 0 && (
        <div className="mb-6">
          <h2 className="text-base font-semibold mb-1">TOP canasta básica</h2>
          <p className="text-muted-foreground text-xs mb-3">
            Los más baratos de cada item, unificando todas las fuentes.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {top_baratos.map((blk: TopBlock) => (
              <Card key={blk.label}>
                <CardHeader className="py-2 px-4 font-semibold text-sm border-b">
                  {blk.label}
                </CardHeader>
                <CardContent className="p-0">
                  {blk.items.length ? (
                    <table className="w-full text-sm">
                      <tbody>
                        {blk.items.map((it, idx) => (
                          <tr
                            key={it.id}
                            className={idx === 0 ? "bg-green-50" : ""}
                          >
                            <td className="px-3 py-1.5 text-muted-foreground text-xs w-4">
                              {idx + 1}
                            </td>
                            <td className="px-2 py-1.5">
                              <Link
                                to={`/producto/${it.id}`}
                                className="hover:underline text-xs"
                              >
                                {it.nombre}
                              </Link>
                            </td>
                            <td className="px-1 py-1.5">
                              <FuenteChip fuente={it.fuente} />
                            </td>
                            <td className="px-3 py-1.5 text-right font-semibold text-xs whitespace-nowrap">
                              ${fmt(it.precio)}
                            </td>
                            <td className="pr-2">
                              <CartButton id={it.id} nombre={it.nombre} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p className="px-4 py-2 text-muted-foreground text-xs">
                      Sin datos.
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Highlights header + day selector */}
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <h2 className="text-base font-semibold">Highlights por fuente</h2>
        <div className="flex gap-1">
          {[7, 14, 30].map((d) => (
            <button
              key={d}
              onClick={() => setSearchParams({ dias: String(d) })}
              className={`px-3 py-1 text-xs rounded border transition-colors ${
                dias === d
                  ? "bg-neutral-900 text-white border-neutral-900"
                  : "border-neutral-300 hover:border-neutral-500"
              }`}
            >
              {d} días
            </button>
          ))}
        </div>
      </div>

      {/* Per-source highlights */}
      {highlights?.map((bloque: HighlightBlock) => {
        if (!bloque.subas.length && !bloque.bajas.length) return null
        return (
          <div key={bloque.fuente} className="mb-4">
            <div className="mb-2">
              <FuenteChip fuente={bloque.fuente} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {(["subas", "bajas"] as const).map((tipo) => {
                const items = bloque[tipo]
                const isUp = tipo === "subas"
                return (
                  <Card key={tipo}>
                    <CardHeader className="py-2 px-4 border-b flex flex-row items-center justify-between">
                      <span className={`font-semibold text-sm ${isUp ? "text-red-600" : "text-green-700"}`}>
                        {isUp ? "▲ Subas" : "▼ Bajas"}
                      </span>
                      <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${isUp ? "bg-red-100 text-red-600" : "bg-green-100 text-green-700"}`}>
                        {items.length}
                      </span>
                    </CardHeader>
                    <CardContent className="p-0">
                      {items.length ? (
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="text-muted-foreground">
                              <th className="px-3 py-1.5 text-left font-medium">Producto</th>
                              <th className="px-2 py-1.5 text-right font-medium whitespace-nowrap">Precio</th>
                              <th className="px-3 py-1.5 text-right font-medium">Var.</th>
                              <th />
                            </tr>
                          </thead>
                          <tbody>
                            {items.slice(0, 20).map((h: Highlight) => (
                              <tr key={h.id} className="border-t border-neutral-100">
                                <td className="px-3 py-1.5">
                                  <Link to={`/producto/${h.id}`} className="hover:underline">
                                    {h.nombre_normalizado}
                                  </Link>
                                </td>
                                <td className="px-2 py-1.5 text-right whitespace-nowrap">
                                  ${fmt(h.precio_actual)}
                                </td>
                                <td className="px-3 py-1.5 text-right">
                                  <PriceVar pct={h.variacion_pct} />
                                </td>
                                <td className="pr-2">
                                  <CartButton id={h.id} nombre={h.nombre_normalizado} />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      ) : (
                        <p className="px-4 py-2 text-muted-foreground text-xs">
                          Sin {tipo} mayores al 5%.
                        </p>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>
        )
      })}

      {/* Quick links */}
      <Card className="mt-4">
        <CardContent className="pt-4">
          <h3 className="font-semibold text-sm mb-2">Accesos rápidos</h3>
          <div className="flex flex-wrap gap-2">
            {[
              { label: "Ver todos los precios", to: "/precios" },
              { label: "Precios — 14 días", to: "/precios?dias=14" },
              { label: "Precios — 30 días", to: "/precios?dias=30" },
            ].map((l) => (
              <Link
                key={l.to}
                to={l.to}
                className="text-xs border border-neutral-300 rounded px-3 py-1 hover:border-neutral-500 transition-colors"
              >
                {l.label}
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// ── Types ──────────────────────────────────────────────────────────────────

interface TopItem {
  id: number
  nombre: string
  fuente: string
  precio: number
}
interface TopBlock {
  label: string
  items: TopItem[]
}
interface Highlight {
  id: number
  nombre_normalizado: string
  precio_actual: number
  variacion_pct: number | string
}
interface HighlightBlock {
  fuente: string
  subas: Highlight[]
  bajas: Highlight[]
}
