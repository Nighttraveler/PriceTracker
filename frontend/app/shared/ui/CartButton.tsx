import { ShoppingCart, X } from "lucide-react"
import { toast } from "sonner"
import { useCartStore } from "~/shared/stores/cart"

export function CartButton({ id, nombre }: { id: number; nombre: string }) {
  const { has, add, remove } = useCartStore()
  const inCart = has(id)

  function toggle() {
    if (inCart) {
      remove(id)
      toast(`${nombre} quitado del carrito`)
    } else {
      add(id)
      toast.success(`${nombre} agregado al carrito`)
    }
  }

  return (
    <button
      onClick={toggle}
      title={inCart ? "Quitar del carrito" : "Agregar al carrito"}
      className={`p-1 rounded transition-colors ${
        inCart
          ? "text-red-500 hover:text-red-700"
          : "text-neutral-400 hover:text-neutral-700"
      }`}
    >
      {inCart ? <X size={14} /> : <ShoppingCart size={14} />}
    </button>
  )
}
