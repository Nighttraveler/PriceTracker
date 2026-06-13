## Why

El dashboard (`/`) ya muestra los productos más relevantes en dos lugares: la sección "TOP canasta básica" y los "Highlights por fuente" (subas/bajas). Hoy, para sumar uno de esos productos al carrito, el usuario tiene que ir a `/carrito`, escribir el nombre y buscarlo de nuevo en un modal. Es fricción innecesaria sobre productos que ya están a la vista. Un botón de "agregar al carrito" en cada fila cierra ese loop directamente desde el dashboard.

## What Changes

- Agregar un botón compacto de carrito (🛒) en cada item de la sección "TOP canasta básica" del index.
- Agregar el mismo botón en cada fila de las listas de Highlights por fuente (subas y bajas).
- Al hacer click, el producto se agrega al carrito persistido en `localStorage` (clave `pt_carrito`), reutilizando los helpers globales ya existentes en `base.html` (`addToCart`, `isInCart`, `updateBadge`).
- El botón refleja su estado: muestra "agregado" (✓) si el producto ya está en el carrito, tanto al cargar la página como tras el click. El badge del carrito en la navbar se actualiza al instante.
- Cambio puramente client-side: no se tocan rutas de Flask, queries de DB ni la API. Los datos de cada fila (`id` de producto) ya están disponibles en los templates.

## Capabilities

### New Capabilities
- `cart-quick-add`: Botón de agregado rápido al carrito desde las listas del dashboard, con persistencia en localStorage y reflejo de estado (agregado / no agregado).

### Modified Capabilities
<!-- Ninguna: el sistema de carrito en localStorage no tiene spec previa en openspec/specs/. -->

## Impact

- **Templates**: `templates/index.html` (filas de `top_baratos` y de `highlights_por_fuente`; bloque `extra_scripts`).
- **Reutiliza** (sin modificar): helpers globales de carrito en `templates/base.html` (`getCart`, `addToCart`, `isInCart`, `updateBadge`, clave `pt_carrito`).
- **Sin cambios** en `app.py`, `db.py`, esquema de DB ni endpoints de API.
