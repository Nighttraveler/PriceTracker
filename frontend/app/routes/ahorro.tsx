import { Link } from "react-router"
import { useQuery } from "@tanstack/react-query"
import type { Route } from "./+types/ahorro"
import { api } from "~/shared/lib/api"
import { FuenteChip } from "~/shared/ui/FuenteChip"
import { Card, CardContent, CardHeader } from "~/shared/ui/shadcn/card"

export function meta(_: Route.MetaArgs) {
  return [{ title: "Ahorro — Price Tracker" }]
}

export async function loader(_: Route.LoaderArgs) {
  const { data } = await api.get("/api/v1/ahorro")
  return data as AhorroData
}

const fmt = (n: number) =>
  n?.toLocaleString("es-AR", { maximumFractionDigits: 0 })

export default function Ahorro({ loaderData }: Route.ComponentProps) {
  const { data } = useQuery({
    queryKey: ["ahorro"],
    queryFn: () => api.get("/api/v1/ahorro").then((r) => r.data),
    initialData: loaderData,
    staleTime: 10 * 60 * 1000,
  })

  const { tabla_cat, fuentes, carrito, n_productos_multi } = data

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Dashboard de Ahorro</h1>

      {/* Avg price by category × source */}
      <Card className="mb-6">
        <CardHeader className="py-3 px-4 border-b">
          <div>
            <span className="font-semibold text-sm">Precio promedio por categoría y fuente</span>
            <span className="text-muted-foreground text-xs ml-2">
              Solo productos individuales · Última fecha disponible
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Categoría
                  </th>
                  {fuentes.map((f: string) => (
                    <th
                      key={f}
                      className="px-4 py-2 text-center text-xs font-medium text-muted-foreground uppercase tracking-wide"
                    >
                      <FuenteChip fuente={f} />
                    </th>
                  ))}
                  <th className="px-4 py-2 text-center text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Más barato
                  </th>
                </tr>
              </thead>
              <tbody>
                {tabla_cat.map((row: CatRow) => (
                  <tr key={row.categoria} className="border-t border-neutral-100">
                    <td className="px-4 py-2 font-semibold capitalize">
                      {row.categoria}
                    </td>
                    {fuentes.map((f: string) => {
                      const d = row.fuentes[f]
                      const isCheapest = row.mas_barata === f
                      if (!d)
                        return (
                          <td
                            key={f}
                            className="px-4 py-2 text-center text-muted-foreground"
                          >
                            —
                          </td>
                        )
                      return (
                        <td
                          key={f}
                          className={`px-4 py-2 text-center ${
                            isCheapest ? "bg-green-50 font-semibold" : ""
                          }`}
                        >
                          <div>${fmt(d.avg)}</div>
                          <div className="text-xs text-muted-foreground">
                            {d.n} productos
                          </div>
                        </td>
                      )
                    })}
                    <td className="px-4 py-2 text-center">
                      <span className="bg-green-600 text-white text-xs px-2 py-0.5 rounded-full capitalize">
                        {row.mas_barata}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Optimal cart */}
      <Card>
        <CardHeader className="py-3 px-4 border-b flex flex-row items-center justify-between">
          <span className="font-semibold text-sm">
            Carrito óptimo — dónde comprar cada producto
          </span>
          <span className="text-muted-foreground text-xs">
            {n_productos_multi} productos en 2+ fuentes · top 20 mayor diferencia
          </span>
        </CardHeader>
        <CardContent className="pt-4">
          {carrito.length ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 mb-3">
                {carrito.map((bloque: CartGroup) => (
                  <div
                    key={bloque.fuente}
                    className="rounded border shadow-sm overflow-hidden"
                  >
                    <div className="flex items-center gap-2 px-3 py-2 border-b bg-white">
                      <FuenteChip fuente={bloque.fuente} />
                      <span className="text-xs text-muted-foreground">
                        {bloque.productos.length} producto
                        {bloque.productos.length !== 1 ? "s" : ""}
                      </span>
                    </div>
                    <table className="w-full text-xs">
                      <tbody>
                        {bloque.productos.map((item: CartItem) => (
                          <tr key={item.id} className="border-t border-neutral-100">
                            <td className="px-3 py-1.5">
                              <Link
                                to={`/producto/${item.id}`}
                                className="hover:underline text-neutral-800"
                              >
                                {item.nombre}
                              </Link>
                              {item.ahorro > 0 && (
                                <div className="text-green-700 font-semibold">
                                  ahorrás ${fmt(item.ahorro)}
                                </div>
                              )}
                            </td>
                            <td className="px-3 py-1.5 text-right whitespace-nowrap">
                              <div className="font-semibold text-green-700">
                                ${fmt(item.precio)}
                              </div>
                              {item.precio_max > item.precio && (
                                <div className="text-muted-foreground line-through">
                                  ${fmt(item.precio_max)}
                                </div>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot>
                        <tr className="border-t border-neutral-200 bg-neutral-50">
                          <td className="px-3 py-1.5 font-bold">Total</td>
                          <td className="px-3 py-1.5 text-right font-bold text-green-700">
                            ${fmt(bloque.total)}
                          </td>
                        </tr>
                        {bloque.ahorro_total > 0 && (
                          <tr>
                            <td
                              colSpan={2}
                              className="px-3 py-1 text-center text-[0.7rem] text-green-700"
                            >
                              Ahorro vs precio más caro: ${fmt(bloque.ahorro_total)}
                            </td>
                          </tr>
                        )}
                      </tfoot>
                    </table>
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">
                Cada producto asignado a la fuente con el precio más bajo del último
                relevamiento. El precio tachado es el más caro encontrado en otra fuente.
              </p>
            </>
          ) : (
            <p className="text-muted-foreground text-sm">
              Sin productos en múltiples fuentes para armar el carrito.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ── Types ──────────────────────────────────────────────────────────────────

interface CatRow {
  categoria: string
  fuentes: Record<string, { avg: number; min: number; max: number; n: number }>
  mas_barata: string
}
interface CartItem {
  id: number
  nombre: string
  precio: number
  precio_max: number
  ahorro: number
}
interface CartGroup {
  fuente: string
  productos: CartItem[]
  total: number
  ahorro_total: number
}
interface AhorroData {
  tabla_cat: CatRow[]
  fuentes: string[]
  carrito: CartGroup[]
  n_productos_multi: number
}
