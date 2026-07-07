export interface CartItem {
  id: number
  nombre: string
  precio: number
  precio_max: number
  ahorro: number
}

export interface CartGroup {
  fuente: string
  productos: CartItem[]
  total: number
  ahorro_total: number
}

export interface CartData {
  carrito: CartGroup[]
  no_encontrados?: number[]
}
