## Purpose

Botón de agregado rápido al carrito desde las listas del dashboard (`/`), con persistencia en `localStorage` y reflejo visual del estado (agregado / no agregado).

## Requirements

### Requirement: Botón de agregado rápido en las listas del dashboard

El dashboard (`/`) SHALL mostrar un botón de carrito en cada fila de la sección "TOP canasta básica" y en cada fila de las listas de Highlights por fuente (subas y bajas). Cada botón MUST asociarse al `id` de producto de su fila.

#### Scenario: El botón aparece en cada item de la canasta básica

- **WHEN** el dashboard renderiza la sección "TOP canasta básica" con al menos un item
- **THEN** cada fila muestra un botón de carrito asociado al `id` de producto de esa fila

#### Scenario: El botón aparece en cada fila de highlights

- **WHEN** el dashboard renderiza un bloque de Highlights por fuente con subas o bajas
- **THEN** cada fila de subas y de bajas muestra un botón de carrito asociado al `id` de producto de esa fila

### Requirement: Agregar al carrito persiste en localStorage

Al hacer click en el botón de un producto que no está en el carrito, el sistema SHALL agregar el `id` de ese producto al carrito persistido en `localStorage` bajo la clave `pt_carrito`, reutilizando los helpers globales existentes (`addToCart`). El estado MUST sobrevivir a recargas de página.

#### Scenario: Agregar un producto nuevo

- **WHEN** el usuario hace click en el botón de carrito de un producto que no está en el carrito
- **THEN** el `id` del producto queda guardado en `localStorage` bajo la clave `pt_carrito`
- **AND** el botón pasa a su estado "agregado" (✓)

#### Scenario: El carrito persiste tras recargar

- **WHEN** el usuario agregó un producto y luego recarga el dashboard
- **THEN** el botón de ese producto se muestra en estado "agregado" al cargar la página

#### Scenario: No se duplican productos

- **WHEN** el usuario hace click en el botón de un producto que ya está en el carrito
- **THEN** el carrito no agrega una entrada duplicada para ese `id`

### Requirement: El botón refleja el estado del carrito

Cada botón SHALL reflejar visualmente si su producto ya está en el carrito, tanto al cargar la página como inmediatamente después de un click. El badge del carrito en la navbar MUST actualizarse al instante tras agregar un producto.

#### Scenario: Estado inicial al cargar

- **WHEN** el dashboard carga y un producto de la lista ya está en el carrito
- **THEN** su botón se muestra en estado "agregado" (✓), distinto de los productos no agregados

#### Scenario: El badge de la navbar se actualiza

- **WHEN** el usuario agrega un producto desde el dashboard
- **THEN** el contador del badge del carrito en la navbar incrementa sin recargar la página
