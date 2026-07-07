import { describe, it, expect } from "vitest"
import { buildChecklistHtml, exportFileName } from "~/shared/lib/exportChecklist"

const exportDate = new Date(2026, 6, 7) // 2026-07-07

describe("exportFileName", () => {
  it("formats as lista-YYYY-MM-DD.html", () => {
    expect(exportFileName(exportDate)).toBe("lista-2026-07-07.html")
  })
})

describe("buildChecklistHtml", () => {
  it("renders one section per store with items and totals", () => {
    const html = buildChecklistHtml(
      {
        carrito: [
          {
            fuente: "dia",
            productos: [
              { id: 1, nombre: "Leche", precio: 1200, precio_max: 1500, ahorro: 300 },
            ],
            total: 1200,
            ahorro_total: 300,
          },
          {
            fuente: "carrefour",
            productos: [
              { id: 2, nombre: "Arroz", precio: 2100, precio_max: 2100, ahorro: 0 },
            ],
            total: 2100,
            ahorro_total: 0,
          },
        ],
      },
      exportDate
    )

    expect(html).toContain("dia")
    expect(html).toContain("carrefour")
    expect(html).toContain("Leche")
    expect(html).toContain("Arroz")
    expect(html).toContain("$1.200")
    expect(html).toContain("$2.100")
    expect(html).toContain("$3.300") // grand total
  })

  it("escapes HTML-special characters in product names", () => {
    const html = buildChecklistHtml(
      {
        carrito: [
          {
            fuente: "dia",
            productos: [
              { id: 1, nombre: `Pan & Manteca <"especial">`, precio: 500, precio_max: 500, ahorro: 0 },
            ],
            total: 500,
            ahorro_total: 0,
          },
        ],
      },
      exportDate
    )

    expect(html).toContain("Pan &amp; Manteca &lt;&quot;especial&quot;&gt;")
    expect(html).not.toContain(`Pan & Manteca <"especial">`)
  })

  it("omits the no-encontrados footer when there are none", () => {
    const html = buildChecklistHtml(
      {
        carrito: [
          {
            fuente: "dia",
            productos: [{ id: 1, nombre: "Leche", precio: 1200, precio_max: 1200, ahorro: 0 }],
            total: 1200,
            ahorro_total: 0,
          },
        ],
        no_encontrados: [],
      },
      exportDate
    )

    expect(html).not.toContain("Productos no encontrados")
  })

  it("includes unresolved product ids in the footer note", () => {
    const html = buildChecklistHtml(
      {
        carrito: [
          {
            fuente: "dia",
            productos: [{ id: 1, nombre: "Leche", precio: 1200, precio_max: 1200, ahorro: 0 }],
            total: 1200,
            ahorro_total: 0,
          },
        ],
        no_encontrados: [42, 99],
      },
      exportDate
    )

    expect(html).toContain("#42")
    expect(html).toContain("#99")
  })
})
