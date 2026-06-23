import { useSearchParams, Link } from "react-router"
import { useQuery } from "@tanstack/react-query"
import type { Route } from "./+types/precios"
import { api } from "~/shared/lib/api"
import { FuenteChip } from "~/shared/ui/FuenteChip"
import { PriceVar } from "~/shared/ui/PriceVar"
import { CartButton } from "~/shared/ui/CartButton"
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "~/shared/ui/shadcn/pagination"

export function meta(_: Route.MetaArgs) {
  return [{ title: "Precios — Price Tracker" }]
}

export async function loader({ request }: Route.LoaderArgs) {
  const url = new URL(request.url)
  const params = new URLSearchParams({
    dias: url.searchParams.get("dias") ?? "7",
    page: url.searchParams.get("page") ?? "1",
    cat: url.searchParams.get("cat") ?? "",
  })
  const { data } = await api.get(`/api/v1/precios?${params}`)
  return data
}

const fmt = (n: number) =>
  n?.toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function Precios({ loaderData }: Route.ComponentProps) {
  const [searchParams, setSearchParams] = useSearchParams()
  const dias = Number(searchParams.get("dias") ?? 7)
  const page = Number(searchParams.get("page") ?? 1)
  const cat = searchParams.get("cat") ?? ""

  function nav(patch: Record<string, string>) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      Object.entries(patch).forEach(([k, v]) => {
        if (v) next.set(k, v)
        else next.delete(k)
      })
      return next
    })
  }

  const { data } = useQuery({
    queryKey: ["precios", dias, page, cat],
    queryFn: () =>
      api
        .get(`/api/v1/precios?dias=${dias}&page=${page}&cat=${encodeURIComponent(cat)}`)
        .then((r) => r.data),
    initialData: loaderData,
    staleTime: 5 * 60 * 1000,
  })

  const { filas, fuentes, categorias_list, total, total_pages } = data

  const pageNums: number[] = []
  for (
    let p = Math.max(1, page - 2);
    p <= Math.min(total_pages, page + 2);
    p++
  ) pageNums.push(p)

  return (
    <div>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <h1 className="text-xl font-bold">Comparativa de precios</h1>
        <span className="text-muted-foreground text-sm">{total} productos</span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4 items-center">
        <div className="flex gap-1">
          {[7, 14, 30, 60].map((d) => (
            <button
              key={d}
              onClick={() => nav({ dias: String(d), page: "1" })}
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
        <select
          value={cat}
          onChange={(e) => nav({ cat: e.target.value, page: "1" })}
          className="text-xs border border-neutral-300 rounded px-2 py-1 bg-background"
        >
          <option value="">Todas las categorías</option>
          {categorias_list?.map((c: string) => (
            <option key={c} value={c}>
              {c.charAt(0).toUpperCase() + c.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {!filas?.length ? (
        <div className="text-muted-foreground text-sm p-4 border rounded">
          Sin datos para este período.
        </div>
      ) : (
        <div className="rounded border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-neutral-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground uppercase tracking-wide whitespace-nowrap">
                    Categoría
                  </th>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground uppercase tracking-wide">
                    Producto
                  </th>
                  {fuentes?.map((f: string) => (
                    <th
                      key={f}
                      className="px-3 py-2 text-left font-medium text-muted-foreground uppercase tracking-wide whitespace-nowrap"
                    >
                      <FuenteChip fuente={f} />
                    </th>
                  ))}
                  <th />
                </tr>
              </thead>
              <tbody>
                {filas.map((row: PrecioRow) => (
                  <tr
                    key={`${row.cat}-${row.producto}`}
                    className={`border-t border-neutral-100 hover:bg-neutral-50 ${
                      row.num_fuentes > 1 ? "border-l-2 border-l-blue-400" : ""
                    }`}
                  >
                    <td className="px-3 py-1.5 text-muted-foreground whitespace-nowrap">
                      {row.cat}
                    </td>
                    <td className="px-3 py-1.5">
                      {row.producto_id ? (
                        <Link
                          to={`/producto/${row.producto_id}`}
                          className="hover:underline font-medium"
                        >
                          {row.producto}
                        </Link>
                      ) : (
                        row.producto
                      )}
                    </td>
                    {fuentes?.map((f: string) => {
                      const d = row.fuentes[f]
                      const isCheapest = row.fuente_mas_barata === f
                      if (!d)
                        return (
                          <td
                            key={f}
                            className="px-3 py-1.5 text-muted-foreground text-center"
                          >
                            —
                          </td>
                        )
                      return (
                        <td
                          key={f}
                          className={`px-3 py-1.5 whitespace-nowrap ${
                            isCheapest
                              ? "bg-green-50 font-semibold"
                              : ""
                          }`}
                        >
                          {d.url ? (
                            <a
                              href={d.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={`hover:underline ${isCheapest ? "text-green-800" : ""}`}
                            >
                              ${fmt(d.precio_actual)}
                            </a>
                          ) : (
                            <span>${fmt(d.precio_actual)}</span>
                          )}{" "}
                          <PriceVar pct={d.variacion_pct} />
                          {isCheapest && (
                            <span className="ml-1 text-yellow-500" title="más barato">
                              ★
                            </span>
                          )}
                        </td>
                      )
                    })}
                    <td className="pr-2">
                      {row.producto_id && (
                        <CartButton id={row.producto_id} nombre={row.producto} />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {total_pages > 1 && (
            <div className="py-3 border-t">
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      onClick={() => nav({ page: String(page - 1) })}
                      aria-disabled={page === 1}
                      className={page === 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                    />
                  </PaginationItem>
                  {page > 3 && (
                    <PaginationItem>
                      <PaginationLink onClick={() => nav({ page: "1" })} className="cursor-pointer">
                        1
                      </PaginationLink>
                    </PaginationItem>
                  )}
                  {pageNums.map((p) => (
                    <PaginationItem key={p}>
                      <PaginationLink
                        isActive={p === page}
                        onClick={() => nav({ page: String(p) })}
                        className="cursor-pointer"
                      >
                        {p}
                      </PaginationLink>
                    </PaginationItem>
                  ))}
                  {page < total_pages - 2 && (
                    <PaginationItem>
                      <PaginationLink
                        onClick={() => nav({ page: String(total_pages) })}
                        className="cursor-pointer"
                      >
                        {total_pages}
                      </PaginationLink>
                    </PaginationItem>
                  )}
                  <PaginationItem>
                    <PaginationNext
                      onClick={() => nav({ page: String(page + 1) })}
                      aria-disabled={page === total_pages}
                      className={page === total_pages ? "pointer-events-none opacity-50" : "cursor-pointer"}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Types ──────────────────────────────────────────────────────────────────

interface FuenteData {
  precio_actual: number
  variacion_pct: number | null
  url: string
}
interface PrecioRow {
  producto: string
  cat: string
  fuentes: Record<string, FuenteData>
  num_fuentes: number
  producto_id: number | null
  fuente_mas_barata: string | null
}
