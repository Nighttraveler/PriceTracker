import { create } from "zustand"
import { persist } from "zustand/middleware"

interface CartStore {
  ids: number[]
  add: (id: number) => void
  remove: (id: number) => void
  has: (id: number) => boolean
  clear: () => void
  count: () => number
}

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      ids: [],
      add: (id) =>
        set((s) => ({ ids: s.ids.includes(id) ? s.ids : [...s.ids, id] })),
      remove: (id) =>
        set((s) => ({ ids: s.ids.filter((i) => i !== id) })),
      has: (id) => get().ids.includes(id),
      clear: () => set({ ids: [] }),
      count: () => get().ids.length,
    }),
    { name: "pt_carrito" }
  )
)
