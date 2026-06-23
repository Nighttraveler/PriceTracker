import { NavLink } from "react-router"
import { ShoppingCart } from "lucide-react"
import { useCartStore } from "~/shared/stores/cart"

export function Nav() {
  const count = useCartStore((s) => s.count())

  return (
    <nav className="bg-neutral-900 text-white px-4 h-12 flex items-center justify-between">
      <NavLink to="/" className="font-semibold text-sm tracking-tight">
        Price Tracker
      </NavLink>
      <div className="flex items-center gap-4 text-sm">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            isActive ? "font-semibold" : "text-neutral-400 hover:text-white transition-colors"
          }
        >
          Dashboard
        </NavLink>
        <NavLink
          to="/precios"
          className={({ isActive }) =>
            isActive ? "font-semibold" : "text-neutral-400 hover:text-white transition-colors"
          }
        >
          Precios
        </NavLink>
        <NavLink
          to="/ahorro"
          className={({ isActive }) =>
            isActive ? "font-semibold" : "text-neutral-400 hover:text-white transition-colors"
          }
        >
          Ahorro
        </NavLink>
        <NavLink
          to="/buscar"
          className={({ isActive }) =>
            isActive ? "font-semibold" : "text-neutral-400 hover:text-white transition-colors"
          }
        >
          Buscar
        </NavLink>
        <NavLink
          to="/carrito"
          className="relative text-neutral-400 hover:text-white transition-colors"
          aria-label="Mi carrito"
        >
          <ShoppingCart size={18} />
          {count > 0 && (
            <span className="absolute -top-1.5 -right-2 bg-red-500 text-white text-[0.6rem] font-bold rounded-full min-w-[1.1em] h-[1.1em] flex items-center justify-center px-0.5 leading-none">
              {count}
            </span>
          )}
        </NavLink>
      </div>
    </nav>
  )
}
