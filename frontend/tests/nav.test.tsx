import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { QueryClientProvider } from "@tanstack/react-query"
import { describe, it, expect } from "vitest"
import { Nav } from "~/shared/ui/Nav"
import { createQueryClient } from "~/shared/lib/queryClient"

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={createQueryClient()}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe("Nav", () => {
  it("renders all navigation links", () => {
    render(<Nav />, { wrapper: Wrapper })
    expect(screen.getByText("Dashboard")).toBeInTheDocument()
    expect(screen.getByText("Precios")).toBeInTheDocument()
    expect(screen.getByText("Ahorro")).toBeInTheDocument()
    expect(screen.getByText("Buscar")).toBeInTheDocument()
    expect(screen.getByLabelText("Mi carrito")).toBeInTheDocument()
  })
})
