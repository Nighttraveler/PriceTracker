import type { CartData } from "~/shared/types/cart"
import { formatPrice } from "~/shared/lib/formatPrice"

const escapeHtml = (s: string) =>
  s.replace(/[&<>"']/g, (c) => {
    switch (c) {
      case "&":
        return "&amp;"
      case "<":
        return "&lt;"
      case ">":
        return "&gt;"
      case '"':
        return "&quot;"
      default:
        return "&#39;"
    }
  })

const fmtPrice = formatPrice

const dateKey = (date: Date): string => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, "0")
  const d = String(date.getDate()).padStart(2, "0")
  return `${y}-${m}-${d}`
}

export function exportFileName(date: Date): string {
  return `lista-${dateKey(date)}.html`
}

export function buildChecklistHtml(cartData: CartData, exportDate: Date): string {
  const storageKey = `lista-${dateKey(exportDate)}`
  const fechaTexto = exportDate.toLocaleDateString("es-AR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  })

  const grandTotal = cartData.carrito.reduce((sum, g) => sum + g.total, 0)
  const grandAhorro = cartData.carrito.reduce((sum, g) => sum + g.ahorro_total, 0)

  const sections = cartData.carrito
    .map((grupo) => {
      const rows = grupo.productos
        .map(
          (item) => `
        <li class="item" data-id="${item.id}" data-precio="${item.precio}">
          <label>
            <input type="checkbox" />
            <span class="nombre">${escapeHtml(item.nombre)}</span>
            <span class="precio">${fmtPrice(item.precio)}</span>
          </label>
        </li>`
        )
        .join("")

      return `
    <section class="store" data-total="${grupo.total}">
      <h2>${escapeHtml(grupo.fuente)}</h2>
      <ul class="items">${rows}
      </ul>
      <div class="store-footer">
        <span>Restante: <strong class="remaining">${fmtPrice(grupo.total)}</strong></span>
        <span class="fixed">Total: ${fmtPrice(grupo.total)}${grupo.ahorro_total > 0 ? ` · Ahorro: ${fmtPrice(grupo.ahorro_total)}` : ""}</span>
      </div>
    </section>`
    })
    .join("")

  const noEncontrados = cartData.no_encontrados?.length
    ? `<p class="no-encontrados">Productos no encontrados: ${cartData.no_encontrados
        .map((id) => `#${id}`)
        .join(", ")}</p>`
    : ""

  return `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Lista de compras — ${fechaTexto}</title>
<style>
  :root {
    color-scheme: light;
    --bg: #fafafa;
    --fg: #1a1a1a;
    --muted: #888;
    --surface: #fff;
    --surface-header: rgba(0,0,0,0.04);
    --border: #ddd;
    --border-soft: #eee;
    --control-bg: #fff;
    --control-border: #ccc;
  }
  body[data-theme="dark"] {
    color-scheme: dark;
    --bg: #121212;
    --fg: #eee;
    --muted: #999;
    --surface: #1e1e1e;
    --surface-header: rgba(255,255,255,0.06);
    --border: #333;
    --border-soft: #2a2a2a;
    --control-bg: #1e1e1e;
    --control-border: #444;
  }
  body {
    font-family: -apple-system, system-ui, sans-serif;
    max-width: 480px;
    margin: 0 auto;
    padding: 1rem;
    background: var(--bg);
    color: var(--fg);
  }
  header { display: flex; align-items: flex-start; justify-content: space-between; gap: 0.75rem; margin-bottom: 1.25rem; }
  h1 { font-size: 1.25rem; margin: 0 0 0.25rem; }
  .fecha { font-size: 0.85rem; color: var(--muted); margin: 0; }
  .theme-toggle {
    flex-shrink: 0;
    border: 1px solid var(--control-border);
    background: var(--control-bg);
    color: var(--fg);
    border-radius: 6px;
    padding: 0.4rem 0.6rem;
    font-size: 0.8rem;
    cursor: pointer;
  }
  .store {
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 1rem;
    overflow: hidden;
    background: var(--surface);
  }
  .store h2 { font-size: 1rem; margin: 0; padding: 0.75rem 1rem; background: var(--surface-header); }
  .items { list-style: none; margin: 0; padding: 0; }
  .item { border-top: 1px solid var(--border-soft); }
  .item label {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.85rem 1rem;
    cursor: pointer;
  }
  .item input[type="checkbox"] { width: 1.25rem; height: 1.25rem; flex-shrink: 0; }
  .item .nombre { flex: 1; font-size: 0.95rem; }
  .item .precio { font-weight: 600; font-size: 0.95rem; white-space: nowrap; }
  .item.checked .nombre, .item.checked .precio {
    text-decoration: line-through;
    opacity: 0.5;
  }
  .store-footer {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 0.6rem 1rem;
    border-top: 1px solid var(--border-soft);
    font-size: 0.85rem;
  }
  .store-footer .remaining { font-size: 1rem; }
  .grand-total {
    display: flex;
    justify-content: space-between;
    font-weight: 700;
    font-size: 1.1rem;
    padding: 1rem;
    border-top: 2px solid var(--border);
    margin-top: 0.5rem;
  }
  .no-encontrados { font-size: 0.8rem; color: #b45309; margin-top: 1rem; }
</style>
</head>
<body>
<header>
  <div>
    <h1>🛒 Lista de compras</h1>
    <p class="fecha">${escapeHtml(fechaTexto)}</p>
  </div>
  <button type="button" class="theme-toggle" id="theme-toggle">🌙 Oscuro</button>
</header>
${sections}
<div class="grand-total">
  <span>Total restante</span>
  <span class="grand-remaining">${fmtPrice(grandTotal)}</span>
</div>
${grandAhorro > 0 ? `<p class="fecha">Ahorro total: ${fmtPrice(grandAhorro)}</p>` : ""}
${noEncontrados}
<script>
(function () {
  var STORAGE_KEY = ${JSON.stringify(storageKey)};
  var checked = {};
  try {
    var saved = localStorage.getItem(STORAGE_KEY);
    if (saved) checked = JSON.parse(saved);
  } catch (e) {}

  function persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(checked));
    } catch (e) {}
  }

  function storeRemaining(store) {
    var fixedTotal = parseFloat(store.dataset.total);
    var remaining = fixedTotal;
    store.querySelectorAll(".item").forEach(function (item) {
      if (item.classList.contains("checked")) {
        remaining -= parseFloat(item.dataset.precio);
      }
    });
    return remaining;
  }

  function updateStoreTotals(store) {
    store.querySelector(".remaining").textContent = fmt(storeRemaining(store));
  }

  function updateGrandTotal() {
    var total = 0;
    document.querySelectorAll(".store").forEach(function (store) {
      total += storeRemaining(store);
    });
    document.querySelector(".grand-remaining").textContent = fmt(total);
  }

  function fmt(n) {
    return "$" + Math.round(n).toLocaleString("es-AR");
  }

  document.querySelectorAll(".item").forEach(function (item) {
    var id = item.dataset.id;
    var checkbox = item.querySelector("input[type=checkbox]");
    if (checked[id]) {
      checkbox.checked = true;
      item.classList.add("checked");
    }
    checkbox.addEventListener("change", function () {
      item.classList.toggle("checked", checkbox.checked);
      checked[id] = checkbox.checked;
      persist();
      updateStoreTotals(item.closest(".store"));
      updateGrandTotal();
    });
  });

  document.querySelectorAll(".store").forEach(updateStoreTotals);
  updateGrandTotal();

  var THEME_KEY = "lista-theme";
  var toggle = document.getElementById("theme-toggle");
  function applyTheme(theme) {
    document.body.dataset.theme = theme;
    toggle.textContent = theme === "dark" ? "☀️ Claro" : "🌙 Oscuro";
  }
  var savedTheme = "light";
  try {
    savedTheme = localStorage.getItem(THEME_KEY) || "light";
  } catch (e) {}
  applyTheme(savedTheme);
  toggle.addEventListener("click", function () {
    var next = document.body.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(next);
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch (e) {}
  });
})();
</script>
</body>
</html>`
}

export function downloadChecklist(cartData: CartData, exportDate: Date = new Date()): boolean {
  try {
    const html = buildChecklistHtml(cartData, exportDate)
    const blob = new Blob([html], { type: "text/html" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = exportFileName(exportDate)
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    // Revoking immediately can drop the download in some mobile browsers
    // (notably iOS Safari) that read the blob asynchronously after click().
    setTimeout(() => URL.revokeObjectURL(url), 1000)
    return true
  } catch {
    return false
  }
}
