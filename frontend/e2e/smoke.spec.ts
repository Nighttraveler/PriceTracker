import { test, expect } from "@playwright/test"

test("home page loads with nav", async ({ page }) => {
  await page.goto("/")
  await expect(page.getByText("Dashboard")).toBeVisible()
  await expect(page.getByText("Precios")).toBeVisible()
  await expect(page.getByText("Ahorro")).toBeVisible()
  await expect(page.getByText("Buscar")).toBeVisible()
  await expect(page.getByLabel("Mi carrito")).toBeVisible()
})
