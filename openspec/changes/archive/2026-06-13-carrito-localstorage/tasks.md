## 1. Botón en la canasta básica (`top_baratos`)

- [x] 1.1 En `templates/index.html`, agregar una celda `<td>` al final de cada fila del loop de `blk['items']` con un botón `<button class="cart-add-btn btn btn-sm btn-outline-secondary" data-id="{{ it.id }}" title="Agregar al carrito">🛒</button>`.
- [x] 1.2 Verificar que el botón no rompe el layout de la tabla sin `<thead>` y que convive con el link a `/producto/{{ it.id }}`.

## 2. Botón en las listas de Highlights por fuente

- [x] 2.1 En la tabla de subas, agregar un `<th></th>` al `<thead>` y un `<td>` con el botón `cart-add-btn data-id="{{ h['id'] }}"` al final de cada fila.
- [x] 2.2 Repetir lo mismo en la tabla de bajas.
- [x] 2.3 Confirmar que las filas ocultas (`hl-extra d-none`) también incluyen el botón para que funcionen al expandir con "Ver más".

## 3. Lógica JS (bloque `extra_scripts` de `index.html`)

- [x] 3.1 Agregar función `reflectState(btn)` que, según `isInCart(parseInt(btn.dataset.id, 10))`, marque el botón como "agregado" (texto ✓, `disabled`, clase de estado) o como agregable (🛒).
- [x] 3.2 En `DOMContentLoaded`, iterar `document.querySelectorAll('.cart-add-btn')`, aplicar `reflectState(btn)` y attach de listener `click` que llame `addToCart(id)`, `updateBadge()` (vía `addToCart`/`saveCart`) y luego `reflectState(btn)`.
- [x] 3.3 Reutilizar los helpers globales de `base.html` (`addToCart`, `isInCart`, `updateBadge`) sin redefinir lógica de localStorage ni la clave `pt_carrito`.

## 4. Verificación

- [x] 4.1 Levantar la app (`python app.py`) y abrir `/`: confirmar que el botón aparece en canasta básica y en subas/bajas.
- [x] 4.2 Click en un botón → el badge de la navbar incrementa y el botón pasa a estado "agregado".
- [x] 4.3 Recargar `/` → el botón del producto agregado sigue mostrándose como "agregado" (persistencia en localStorage).
- [x] 4.4 Ir a `/carrito` → confirmar que el producto agregado desde el dashboard aparece en el carrito.
- [x] 4.5 Click repetido / producto ya en carrito → no se duplica la entrada en `pt_carrito`.
