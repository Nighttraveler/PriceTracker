import { useSearchParams, Link, isRouteErrorResponse, useRouteError } from "react-router"
import { useQuery } from "@tanstack/react-query"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import type { Route } from "./+types/producto.$id"
import { api } from "~/shared/lib/api"
import { FuenteChip } from "~/shared/ui/FuenteChip"
import { PriceVar } from "~/shared/ui/PriceVar"
import { CartButton } from "~/shared/ui/CartButton"
import { Card, CardContent, CardHeader } from "~/shared/ui/shadcn/card"

export function meta({ data }: Route.MetaArgs) {
  const name = (data as ProductoData | undefined)?.prod?.nombre_normalizado ?? "Producto"
  const title = name.charAt(0).toUpperCase() + name.slice(1)
  return [{ title: `${title} — Price Tracker` }]
}

export async function loader({ params, request }: Route.LoaderArgs) {
  const url = new URL(request.url)
  const dias = url.searchParams.get("dias") ?? "30"
  const { data } = await api.get(`/api/v1/producto/${params.id}?dias=${dias}`)
  return data as ProductoData
}

export function ErrorBoundary() {
  const error = useRouteError()
  if (isRouteErrorResponse(error) && error.status === 404) {
    return (
      <div className="py-10 text-center text-muted-foreground">
        <p className="text-lg font-semibold">Producto no encontrado</p>
        <Link to="/precios" className="text-sm hover:underline mt-2 inline-block">
          ← Volver a Precios
        </Link>
      </div>
    )
  }
  return <div className="py-10 text-center text-red-500">Error al cargar el producto.</div>
}

const fmt = (n: number) =>
  n?.toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function Producto({ loaderData, params }: Route.ComponentProps) {
  const [searchParams, setSearchParams] = useSearchParams()
  const dias = Number(searchParams.get("dias") ?? 30)

  const { data } = useQuery({
    queryKey: ["producto", params.id, dias],
    queryFn: () =>
      api.get(`/api/v1/producto/${params.id}?dias=${dias}`).then((r) => r.data),
    initialData: loaderData,
    staleTime: 5 * 60 * 1000,
  })

  const { prod, fechas, datasets, variantes } = data

  // Build recharts data: [{fecha, Dia: n, Anonima: n, ...}]
  const chartData = fechas.map((f: string, i: number) => {
    const point: Record<string, string | number | null> = { fecha: f }
    datasets.forEach((ds: Dataset) => {
      point[ds.label] = ds.data[i] ?? null
    })
    return point
  })

  // URL map from variants
  const urlByFuente: Record<string, string> = {}
  variantes?.forEach((v: Variante) => {
    if (v.url_producto && !urlByFuente[v.fuente]) {
      urlByFuente[v.fuente] = v.url_producto
    }
  })

  return (
    <div>
      {/* Breadcrumb */}
      <nav className="text-sm text-muted-foreground mb-4">
        <Link to="/precios" className="hover:underline">
          Precios
        </Link>
        {" › "}
        <span className="text-foreground">
          {prod.nombre_normalizado.charAt(0).toUpperCase() +
            prod.nombre_normalizado.slice(1)}
        </span>
      </nav>

      <Card className="mb-4">
        <CardContent className="pt-4">
          {/* Header */}
          <div className="flex items-start justify-between flex-wrap gap-3 mb-4">
            <div>
              <h1 className="text-xl font-bold capitalize mb-1">
                {prod.nombre_normalizado}
              </h1>
              <div className="flex flex-wrap items-center gap-2">
                {prod.categoria && (
                  <span className="bg-neutral-200 text-neutral-700 text-xs px-2 py-0.5 rounded">
                    {prod.categoria}
                  </span>
                )}
                {Object.entries(urlByFuente).map(([fuente, url]) => (
                  <a
                    key={fuente}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs no-underline"
                  >
                    <FuenteChip fuente={fuente} />
                    <span className="ml-0.5">↗</span>
                  </a>
                ))}
                <CartButton id={prod.id} nombre={prod.nombre_normalizado} />
              </div>
            </div>

            {/* Day selector */}
            <div className="flex gap-1">
              {[7, 14, 30, 90].map((d) => (
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

          {/* Chart */}
          {datasets.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="fecha"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => v.slice(5)}
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) =>
                    "$" + v.toLocaleString("es-AR", { maximumFractionDigits: 0 })
                  }
                  width={70}
                />
                <Tooltip
                  formatter={(value) => [
                    typeof value === "number"
                      ? `$${value.toLocaleString("es-AR", { minimumFractionDigits: 2 })}`
                      : "—",
                  ]}
                />
                <Legend />
                {datasets.map((ds: Dataset) => (
                  <Line
                    key={ds.label}
                    type="monotone"
                    dataKey={ds.label}
                    stroke={ds.color}
                    dot={{ r: 3 }}
                    connectNulls
                    strokeWidth={2}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-muted-foreground text-sm">
              Sin datos de precio en los últimos {dias} días.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Period summary table */}
      {datasets.length > 0 && (
        <Card>
          <CardHeader className="py-3 px-4 border-b font-semibold text-sm">
            Resumen del período
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-neutral-50">
                  <tr>
                    {["Fuente", "Primer precio", "Último precio", "Variación", ""].map(
                      (h) => (
                        <th
                          key={h}
                          className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide"
                        >
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody>
                  {datasets.map((ds: Dataset) => {
                    const valid = ds.data.filter((v) => v !== null) as number[]
                    if (!valid.length) return null
                    const first = valid[0]
                    const last = valid[valid.length - 1]
                    const pct =
                      first > 0 ? Math.round(((last - first) / first) * 1000) / 10 : 0
                    const fuente = ds.label.toLowerCase()
                    const url = urlByFuente[fuente]
                    const isOdd = Math.abs(pct) > 1000
                    return (
                      <tr key={ds.label} className="border-t border-neutral-100">
                        <td className="px-4 py-2">
                          <FuenteChip fuente={fuente} />
                        </td>
                        <td className="px-4 py-2">${fmt(first)}</td>
                        <td className="px-4 py-2">${fmt(last)}</td>
                        <td className="px-4 py-2">
                          {isOdd ? (
                            <span className="text-xs bg-yellow-100 text-yellow-800 px-1 rounded">
                              ⚠ datos inconsistentes
                            </span>
                          ) : (
                            <PriceVar pct={pct} />
                          )}
                        </td>
                        <td className="px-4 py-2">
                          {url && (
                            <a
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs border border-neutral-300 rounded px-2 py-1 hover:border-neutral-500 transition-colors whitespace-nowrap"
                            >
                              Ver en {ds.label} ↗
                            </a>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// ── Types ──────────────────────────────────────────────────────────────────

interface Dataset {
  label: string
  color: string
  data: (number | null)[]
}
interface Variante {
  fuente: string
  url_producto: string | null
}
interface ProductoData {
  prod: { id: number; nombre_normalizado: string; categoria: string }
  fechas: string[]
  datasets: Dataset[]
  variantes: Variante[]
  dias: number
}
