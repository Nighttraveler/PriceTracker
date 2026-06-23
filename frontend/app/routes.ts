import { type RouteConfig, index, route } from "@react-router/dev/routes"

export default [
  index("routes/home.tsx"),
  route("precios", "routes/precios.tsx"),
  route("producto/:id", "routes/producto.$id.tsx"),
  route("ahorro", "routes/ahorro.tsx"),
  route("buscar", "routes/buscar.tsx"),
  route("carrito", "routes/carrito.tsx"),
] satisfies RouteConfig
