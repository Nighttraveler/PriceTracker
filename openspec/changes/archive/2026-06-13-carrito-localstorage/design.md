## Context

El proyecto ya tiene un sistema de carrito completo del lado del cliente:

- `templates/base.html` define helpers globales sobre `localStorage` (clave `pt_carrito`, array de IDs numéricos de producto): `getCart()`, `saveCart()`, `addToCart(id)`, `removeFromCart(id)`, `isInCart(id)`, `updateBadge()`. El badge del carrito en la navbar ya se actualiza vía `updateBadge()`.
- `/carrito` (`templates/carrito.html`) consume esos helpers para construir y mostrar el carrito óptimo; resuelve los nombres de producto desde el backend (`POST /api/carrito`) a partir de los IDs guardados.

El dashboard (`templates/index.html`) ya tiene a la vista los productos relevantes con su `id` de producto:
- `top_baratos[].items[]` → cada `it` tiene `it.id`, `it.nombre`, `it.fuente`, `it.precio` (ya linkea a `/producto/{{ it.id }}`).
- `highlights_por_fuente[].subas|bajas[]` → cada `h` tiene `h['id']`, `h['nombre_normalizado']`, etc. (ya linkea a `/producto/{{ h['id'] }}`).

Como los IDs ya están en el template y los helpers ya persisten en localStorage, este cambio es puramente de presentación + un pequeño handler JS. No requiere tocar Flask, queries ni la API.

## Goals / Non-Goals

**Goals:**
- Agregar un botón de carrito por fila en la canasta básica y en las listas de highlights del dashboard.
- Persistir el agregado en localStorage reutilizando los helpers existentes (sin duplicar lógica de storage).
- Reflejar el estado (agregado / no agregado) al cargar y tras cada click, y actualizar el badge de la navbar al instante.

**Non-Goals:**
- No se agrega capacidad de **quitar** del carrito desde el dashboard (eso ya existe en `/carrito`). El botón solo agrega; en estado "agregado" queda inerte/deshabilitado.
- No se persiste el nombre del producto: `/carrito` ya resuelve nombres por ID desde el backend.
- No se modifican rutas, queries, esquema de DB ni endpoints de API.
- No se añade el botón a otras páginas (`/precios`, `/buscar`, etc.) en este cambio.

## Decisions

**Reutilizar los helpers globales de `base.html` en vez de reimplementar storage.**
`addToCart`, `isInCart` y `updateBadge` ya están en scope global (definidos en el `<script>` de `base.html`, antes del bloque `extra_scripts`). El JS del index los llama directamente. Alternativa descartada: duplicar la lógica de localStorage en index.html → divergencia de la clave/formato `pt_carrito` y bugs de sincronización con el badge.

**Marcar cada botón con `data-id` y una clase común (`.cart-add-btn`), y delegar por selección en `extra_scripts`.**
El bloque `extra_scripts` de index.html ya hace `querySelectorAll('.hl-toggle')`; se agrega un patrón análogo: `querySelectorAll('.cart-add-btn')`, attach de listener, y una función `reflectState(btn)` que decide el render según `isInCart(id)`. Alternativa descartada: `onclick` inline → mezcla comportamiento en el markup y complica el reflejo de estado al cargar.

**El botón vive en una celda nueva al final de cada fila (`<td>` extra), tanto en canasta como en highlights.**
Mantiene el layout de tablas existente y queda "debajo/al costado" de cada item como pidió el usuario, sin romper el `<thead>` (en highlights se agrega un `<th>` vacío; en canasta no hay thead). Alternativa descartada: superponer el botón sobre el nombre → conflicto con el `<a>` a `/producto/<id>`.

**Reflejo de estado idempotente al cargar.**
En `DOMContentLoaded`, iterar todos los `.cart-add-btn` y aplicar `reflectState`. Como `isInCart` lee de localStorage, recargas y navegación entre páginas muestran el estado correcto sin estado server-side.

## Risks / Trade-offs

- **Los IDs de la canasta/highlights son IDs de producto, igual que los que espera el carrito.** → Verificado: ambas secciones linkean a `/producto/<id>` y `/carrito` opera sobre IDs de producto vía `POST /api/carrito`. Mismo espacio de IDs, sin conversión.
- **El botón duplicado en muchas filas podría sumar listeners.** → Volumen acotado (canasta ~pocas decenas; highlights cap visible 20 por sección, resto oculto con `d-none` pero presente en el DOM). `querySelectorAll` + un listener por botón es trivial a esta escala.
- **Filas ocultas de highlights (`hl-extra d-none`).** → Sus botones también reciben listener y reflejan estado; al expandir con "Ver más" ya están funcionales, sin re-inicialización.
- **Sin opción de quitar desde el dashboard.** → Aceptado como Non-Goal; el usuario quita desde `/carrito`. El estado "agregado" es visualmente claro para evitar confusión.

## Migration Plan

Cambio aditivo y solo de frontend (un template). Deploy = desplegar el template actualizado. Rollback = revertir `templates/index.html`. No hay migración de datos ni de esquema; `localStorage` existente (`pt_carrito`) es compatible sin cambios.

## Open Questions

Ninguna pendiente. El alcance, el espacio de IDs y los helpers reutilizables están confirmados contra el código existente.
