import { useState, useEffect } from "react"
import { useSearchParams, Link } from "react-router"
import { useQuery } from "@tanstack/react-query"
import type { Route } from "./+types/buscar"
import { api } from "~/shared/lib/api"
import { FuenteChip } from "~/shared/ui/FuenteChip"
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
  return [{ title: "Buscar — Price Tracker" }]
}

export async function loader({ request }: Route.LoaderArgs) {
  const url = new URL(request.url)
  const params = url.searchParams
  if (!params.get("q") && !params.get("fuente") && !params.get("cat")) {
    const { data: meta } = await api.get("/api/v1/buscar")
    return { ...meta, resultados: [], buscado: false }
  }
  const { data } = await api.get(`/api/v1/buscar?${params}`)
  return data as BuscarData
}

const fmt = (n: number) =>
  n?.toLocaleString("es-AR", { maximumFractionDigits: 0 })

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}

export default function Buscar({ loaderData }: Route.ComponentProps) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [inputVal, setInputVal] = useState(searchParams.get("q") ?? "")
  const page = Number(searchParams.get("page") ?? 1)
  const fuentesSel = searchParams.getAll("fuente")
  const catsSel = searchParams.getAll("cat")

  const debouncedQ = useDebounce(inputVal, 300)

  function buildParams(
    q: string,
    fuentes: string[],
    cats: string[],
    pg: number
  ) {
    const p = new URLSearchParams()
    if (q) p.set("q", q)
    fuentes.forEach((f) => p.append("fuente", f))
    cats.forEach((c) => p.append("cat", c))
    if (pg > 1) p.set("page", String(pg))
    return p
  }

  const queryParams = buildParams(debouncedQ, fuentesSel, catsSel, page)

  const { data, isFetching } = useQuery({
    queryKey: ["buscar", debouncedQ, fuentesSel, catsSel, page],
    queryFn: () =>
      api.get(`/api/v1/buscar?${queryParams}`).then((r) => r.data),
    initialData: loaderData,
    staleTime: 2 * 60 * 1000,
  })

  const { all_fuentes, all_cats, resultados, fuentes_cols, buscado, total, total_pages } =
    data as BuscarData

  function toggleFuente(f: string) {
    const next = fuentesSel.includes(f)
      ? fuentesSel.filter((x) => x !== f)
      : [...fuentesSel, f]
    setSearchParams(buildParams(debouncedQ, next, catsSel, 1))
  }
  function toggleCat(c: string) {
    const next = catsSel.includes(c)
      ? catsSel.filter((x) => x !== c)
      : [...catsSel, c]
    setSearchParams(buildParams(debouncedQ, fuentesSel, next, 1))
  }

  useEffect(() => {
    if (debouncedQ !== searchParams.get("q")) {
      setSearchParams(buildParams(debouncedQ, fuentesSel, catsSel, 1))
    }
  }, [debouncedQ])

  const pageNums: number[] = []
  for (
    let p = Math.max(1, page - 2);
    p <= Math.min(total_pages ?? 1, page + 2);
    p++
  ) pageNums.push(p)

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-xl font-bold">Buscar productos</h1>
        {buscado && total > 0 && (
          <span className="text-muted-foreground text-sm">{total} resultado{total !== 1 ? "s" : ""}</span>
        )}
      </div>

      {/* Search bar */}
      <div className="flex gap-2 mb-4 max-w-xl">
        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          placeholder="Buscar producto…"
          autoFocus
          className="flex-1 border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-neutral-500"
        />
        {buscado && (
          <button
            onClick={() => {
              setInputVal("")
              setSearchParams(new URLSearchParams())
            }}
            className="px-3 text-muted-foreground hover:text-foreground border border-neutral-300 rounded text-sm"
          >
            ✕
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="border rounded p-3 mb-4 shadow-sm">
        <div className="flex flex-wrap gap-4">
          <div>
            <div className="text-[0.65rem] uppercase font-semibold text-muted-foreground mb-2 tracking-wide">
              Fuente
            </div>
            <div className="flex flex-wrap gap-2">
              {all_fuentes?.map((f: string) => (
                <button
                  key={f}
                  onClick={() => toggleFuente(f)}
                  className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                    fuentesSel.includes(f)
                      ? "border-blue-500 bg-blue-50 text-blue-600 font-semibold"
                      : "border-neutral-300 hover:border-neutral-500"
                  }`}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 min-w-40">
            <div className="text-[0.65rem] uppercase font-semibold text-muted-foreground mb-2 tracking-wide">
              Categoría
              {catsSel.length > 0 && (
                <span className="ml-1 bg-blue-500 text-white text-[0.6rem] px-1.5 py-0.5 rounded-full">
                  {catsSel.length}
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-1.5 max-h-[110px] overflow-y-auto">
              {all_cats?.map((c: string) => (
                <button
                  key={c}
                  onClick={() => toggleCat(c)}
                  className={`text-xs px-2.5 py-0.5 rounded-full border transition-colors ${
                    catsSel.includes(c)
                      ? "border-blue-500 bg-blue-50 text-blue-600 font-semibold"
                      : "border-neutral-300 hover:border-neutral-500"
                  }`}
                >
                  {c.charAt(0).toUpperCase() + c.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      {isFetching && (
        <p className="text-xs text-muted-foreground mb-2">Buscando…</p>
      )}

      {!buscado ? (
        <div className="text-center py-12 text-muted-foreground">
          <div className="text-4xl mb-3">🔍</div>
          <p className="font-medium">Buscá por nombre, fuente o categoría</p>
          <p className="text-sm mt-1">Los filtros se combinan — podés elegir varias fuentes y categorías a la vez</p>
        </div>
      ) : !resultados?.length ? (
        <div className="text-center py-12 text-muted-foreground">
          <div className="text-4xl mb-3">😶</div>
          <p className="font-medium">Sin resultados</p>
          <p className="text-sm mt-1">Probá con otros términos o menos filtros</p>
        </div>
      ) : (
        <div className="rounded border overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-neutral-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground uppercase tracking-wide w-[1%]">Cat.</th>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground uppercase tracking-wide">Producto</th>
                  {fuentes_cols?.map((f: string) => (
                    <th key={f} className="px-3 py-2 text-right font-medium text-muted-foreground uppercase tracking-wide">
                      <FuenteChip fuente={f} />
                    </th>
                  ))}
                  <th />
                </tr>
              </thead>
              <tbody>
                {resultados.map((prod: SearchResult) => (
                  <tr key={prod.id} className="border-t border-neutral-100 hover:bg-neutral-50">
                    <td className="px-3 py-1.5 text-muted-foreground whitespace-nowrap">{prod.categoria}</td>
                    <td className="px-3 py-1.5">
                      <Link to={`/producto/${prod.id}`} className="hover:underline font-medium">
                        {prod.nombre}
                      </Link>
                      {Object.keys(prod.fuentes).length > 1 && (
                        <span className="ml-1 bg-blue-500 text-white text-[0.62rem] px-1 rounded">
                          {Object.keys(prod.fuentes).length} fuentes
                        </span>
                      )}
                    </td>
                    {fuentes_cols?.map((f: string) => {
                      const d = prod.fuentes[f]
                      const isCheapest = prod.fuente_mas_barata === f
                      if (!d)
                        return (
                          <td key={f} className="px-3 py-1.5 text-center text-muted-foreground">—</td>
                        )
                      return (
                        <td
                          key={f}
                          className={`px-3 py-1.5 text-right whitespace-nowrap ${isCheapest ? "bg-green-50 font-semibold" : ""}`}
                        >
                          {d.url ? (
                            <a href={d.url} target="_blank" rel="noopener noreferrer"
                              className={`hover:underline ${isCheapest ? "text-green-800" : ""}`}>
                              ${fmt(d.precio)}
                            </a>
                          ) : (
                            <span className={isCheapest ? "text-green-800" : ""}>${fmt(d.precio)}</span>
                          )}
                          {isCheapest && Object.keys(prod.fuentes).length > 1 && (
                            <span className="ml-1 text-yellow-500" title="más barato">★</span>
                          )}
                        </td>
                      )
                    })}
                    <td className="pr-2">
                      <CartButton id={prod.id} nombre={prod.nombre} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {(total_pages ?? 1) > 1 && (
            <div className="py-2 border-t">
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      onClick={() => setSearchParams(buildParams(debouncedQ, fuentesSel, catsSel, page - 1))}
                      aria-disabled={page === 1}
                      className={page === 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                    />
                  </PaginationItem>
                  {pageNums.map((p) => (
                    <PaginationItem key={p}>
                      <PaginationLink
                        isActive={p === page}
                        onClick={() => setSearchParams(buildParams(debouncedQ, fuentesSel, catsSel, p))}
                        className="cursor-pointer"
                      >
                        {p}
                      </PaginationLink>
                    </PaginationItem>
                  ))}
                  <PaginationItem>
                    <PaginationNext
                      onClick={() => setSearchParams(buildParams(debouncedQ, fuentesSel, catsSel, page + 1))}
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

interface FuentePrice {
  precio: number
  url: string | null
}
interface SearchResult {
  id: number
  nombre: string
  categoria: string
  fuentes: Record<string, FuentePrice>
  fuente_mas_barata: string | null
}
interface BuscarData {
  all_fuentes: string[]
  all_cats: string[]
  resultados: SearchResult[]
  fuentes_cols: string[]
  buscado: boolean
  total: number
  total_pages: number
  page: number
  per_page: number
}
