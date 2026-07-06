import { useState } from "react"
import { Link } from "react-router"
import { useQuery, keepPreviousData } from "@tanstack/react-query"
import { toast } from "sonner"
import { X, Search } from "lucide-react"
import type { Route } from "./+types/carrito"
import { api } from "~/shared/lib/api"
import { useDebounce } from "~/shared/lib/useDebounce"
import { useCartStore } from "~/shared/stores/cart"
import { FuenteChip } from "~/shared/ui/FuenteChip"
import { Card, CardContent } from "~/shared/ui/shadcn/card"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "~/shared/ui/shadcn/dialog"

export function meta(_: Route.MetaArgs) {
  return [{ title: "Mi Carrito — Price Tracker" }]
}

const fmt = (n: number) =>
  n?.toLocaleString("es-AR", { maximumFractionDigits: 0 })

// ── Cart-search modal ─────────────────────────────────────────────────────

const minPrice = (prod: ModalResult) =>
  Math.min(
    ...Object.values(prod.fuentes).map((f) => (f as { precio: number }).precio)
  )

function AddControl({
  prod,
  inCart,
  onAdd,
}: {
  prod: ModalResult
  inCart: boolean
  onAdd: (prod: ModalResult) => void
}) {
  if (inCart) {
    return <span className="text-green-600 font-semibold text-xs">✓ Agregado</span>
  }
  return (
    <button
      onClick={() => onAdd(prod)}
      className="bg-blue-600 text-white text-xs px-2.5 py-1 rounded hover:bg-blue-700 transition-colors"
    >
      Agregar
    </button>
  )
}

function CartSearchModal({
  open,
  onClose,
}: {
  open: boolean
  onClose: () => void
}) {
  const [q, setQ] = useState("")
  const [page, setPage] = useState(1)
  const debouncedQ = useDebounce(q, 300)
  const { add, has } = useCartStore()

  const { data, isFetching } = useQuery({
    queryKey: ["buscar_carrito", debouncedQ, page],
    queryFn: () =>
      api
        .get(`/api/v1/buscar_carrito?q=${encodeURIComponent(debouncedQ)}&page=${page}&per_page=10`)
        .then((r) => r.data),
    placeholderData: keepPreviousData,
    staleTime: 60 * 1000,
  })

  const resultados = data?.resultados ?? []
  const totalPages = data?.total_pages ?? 1
  const total = data?.total ?? 0

  const handleAdd = (prod: ModalResult) => {
    add(prod.id)
    toast.success(`${prod.nombre} agregado al carrito`)
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-2xl p-0 flex flex-col max-h-[85dvh]">
        <DialogHeader className="px-4 pt-4 pb-0">
          <DialogTitle>Seleccioná un producto</DialogTitle>
          <input
            type="text"
            value={q}
            onChange={(e) => {
              setQ(e.target.value)
              setPage(1)
            }}
            placeholder="Buscar producto…"
            autoFocus
            className="mt-3 mb-2 w-full border border-neutral-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-neutral-500"
          />
        </DialogHeader>

        <div className="flex-1 min-h-0 overflow-y-auto">
          {isFetching && (
            <p className="text-xs text-muted-foreground px-4 pb-2">Buscando…</p>
          )}

          {!isFetching && !resultados.length && debouncedQ && (
            <p className="text-sm text-muted-foreground px-4 py-6 text-center">
              Sin resultados para esta búsqueda.
            </p>
          )}

          {resultados.length > 0 && (
            <>
              {/* Desktop: table */}
              <div className="hidden sm:block overflow-x-auto border-t">
                <table className="w-full text-xs">
                  <thead className="bg-neutral-50">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium text-muted-foreground">Producto</th>
                      <th className="px-4 py-2 text-left font-medium text-muted-foreground">Categoría</th>
                      <th className="px-4 py-2 text-left font-medium text-muted-foreground">Fuentes</th>
                      <th className="px-4 py-2 text-right font-medium text-muted-foreground">Precio desde</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {resultados.map((prod: ModalResult) => (
                      <tr key={prod.id} className="border-t border-neutral-100 hover:bg-neutral-50">
                        <td className="px-4 py-2 font-medium">{prod.nombre}</td>
                        <td className="px-4 py-2 text-muted-foreground whitespace-nowrap">
                          {prod.categoria || "—"}
                        </td>
                        <td className="px-4 py-2">
                          <div className="flex gap-1 flex-wrap">
                            {Object.keys(prod.fuentes).map((f) => (
                              <FuenteChip key={f} fuente={f} />
                            ))}
                          </div>
                        </td>
                        <td className="px-4 py-2 text-right whitespace-nowrap font-semibold">
                          ${fmt(minPrice(prod))}
                        </td>
                        <td className="px-4 py-2 text-right">
                          <AddControl prod={prod} inCart={has(prod.id)} onAdd={handleAdd} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile: stacked cards */}
              <div className="sm:hidden border-t">
                {resultados.map((prod: ModalResult) => (
                  <div key={prod.id} className="border-b border-neutral-100 px-4 py-3">
                    <div className="font-medium text-sm">{prod.nombre}</div>
                    {prod.categoria && (
                      <div className="text-xs text-muted-foreground mt-0.5">{prod.categoria}</div>
                    )}
                    <div className="flex gap-1 flex-wrap mt-1.5">
                      {Object.keys(prod.fuentes).map((f) => (
                        <FuenteChip key={f} fuente={f} />
                      ))}
                    </div>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-sm font-semibold">
                        desde ${fmt(minPrice(prod))}
                      </span>
                      <AddControl prod={prod} inCart={has(prod.id)} onAdd={handleAdd} />
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Modal pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t">
            <span className="text-xs text-muted-foreground">
              {total} resultado{total !== 1 ? "s" : ""}
            </span>
            {totalPages > 1 && (
              <div className="flex gap-1 items-center text-xs">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-2 py-1 border rounded disabled:opacity-40"
                >
                  ← Ant.
                </button>
                <span>Pág. {page} / {totalPages}</span>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-2 py-1 border rounded disabled:opacity-40"
                >
                  Sig. →
                </button>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function Carrito(_: Route.ComponentProps) {
  const [modalOpen, setModalOpen] = useState(false)
  const { ids, remove, clear } = useCartStore()

  const { data: cartData, isLoading: cartLoading } = useQuery({
    queryKey: ["carrito", ids],
    queryFn: () => api.post("/api/v1/carrito", { ids }).then((r) => r.data),
    enabled: ids.length > 0,
    staleTime: 2 * 60 * 1000,
  })

  // Build name lookup from cart API response
  const productNames: Record<number, string> = {}
  cartData?.productos?.forEach((p: { id: number; nombre: string }) => {
    productNames[p.id] = p.nombre
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Mi carrito</h1>
        {ids.length > 0 && (
          <button
            onClick={() => {
              clear()
              toast("Carrito vaciado")
            }}
            className="text-sm text-red-500 hover:text-red-700 border border-red-300 rounded px-3 py-1 transition-colors"
          >
            Limpiar todo
          </button>
        )}
      </div>

      {/* Search input */}
      <Card className="mb-3">
        <CardContent className="py-3">
          <div className="flex gap-2">
            <input
              type="text"
              readOnly
              onClick={() => setModalOpen(true)}
              placeholder="Escribí un producto (ej: leche, pan lactal, galletitas…)"
              className="flex-1 border border-neutral-300 rounded px-3 py-2 text-sm cursor-pointer focus:outline-none"
            />
            <button
              onClick={() => setModalOpen(true)}
              className="bg-blue-600 text-white px-4 rounded text-sm hover:bg-blue-700 transition-colors flex items-center gap-1"
            >
              <Search size={14} /> Buscar
            </button>
          </div>
          <p className="text-xs text-muted-foreground mt-1.5">
            Hacé click en Buscar para seleccionar el producto exacto.
          </p>
        </CardContent>
      </Card>

      {/* Cart item list */}
      <Card className="mb-4">
        {ids.length === 0 ? (
          <CardContent className="py-8 text-center text-muted-foreground">
            <div className="text-4xl mb-2">🛒</div>
            <p className="text-sm">El carrito está vacío — buscá productos arriba</p>
          </CardContent>
        ) : (
          <CardContent className="p-0">
            {ids.map((id) => (
              <div
                key={id}
                className="flex items-center justify-between px-4 py-2.5 border-b last:border-b-0"
              >
                <Link
                  to={`/producto/${id}`}
                  className="text-sm font-medium hover:underline"
                >
                  {productNames[id] || `Producto #${id}`}
                </Link>
                <button
                  onClick={() => {
                    remove(id)
                    toast(`Producto quitado del carrito`)
                  }}
                  className="text-neutral-400 hover:text-red-500 transition-colors"
                  title="Quitar"
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </CardContent>
        )}
      </Card>

      {/* Loading / error / not found */}
      {ids.length > 0 && cartLoading && (
        <p className="text-xs text-muted-foreground mb-3">Buscando precios…</p>
      )}

      {cartData?.no_encontrados?.length > 0 && (
        <div className="border border-yellow-300 bg-yellow-50 rounded p-3 text-sm text-yellow-800 mb-4">
          <strong>Productos no encontrados:</strong>{" "}
          {cartData.no_encontrados.map((i: number) => `#${i}`).join(", ")}
        </div>
      )}

      {/* Optimal cart */}
      {cartData?.carrito?.length > 0 && (
        <div>
          <h2 className="text-base font-semibold mb-3">
            Carrito óptimo{" "}
            <span className="text-muted-foreground font-normal text-sm">
              — dónde comprar cada cosa más barato
            </span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
            {cartData.carrito.map((bloque: CartGroup) => (
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
                          <div className="font-medium">{item.nombre}</div>
                          {item.ahorro > 0 && (
                            <div className="text-green-700 font-semibold">
                              ahorrás ${fmt(item.ahorro)}
                            </div>
                          )}
                        </td>
                        <td className="px-3 py-1.5 text-right whitespace-nowrap">
                          <div className="font-semibold text-green-700">${fmt(item.precio)}</div>
                          {item.precio_max > item.precio && (
                            <div className="text-muted-foreground line-through">${fmt(item.precio_max)}</div>
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
                        <td colSpan={2} className="px-3 py-1 text-center text-[0.7rem] text-green-700">
                          Ahorro vs precio más caro: ${fmt(bloque.ahorro_total)}
                        </td>
                      </tr>
                    )}
                  </tfoot>
                </table>
              </div>
            ))}
          </div>
        </div>
      )}

      <CartSearchModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  )
}

// ── Types ──────────────────────────────────────────────────────────────────

interface CartItem {
  id: number
  nombre: string
  precio: number
  precio_max: number
  ahorro: number
  url: string
}
interface CartGroup {
  fuente: string
  productos: CartItem[]
  total: number
  ahorro_total: number
}
interface ModalResult {
  id: number
  nombre: string
  categoria: string
  fuentes: Record<string, unknown>
}
