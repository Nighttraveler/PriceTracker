## Purpose

Búsqueda de productos desde el modal del carrito (`/carrito`): modal dimensionado según el viewport, resultados como tabla en desktop y cards en mobile, búsqueda con debounce sin flicker, y alta de productos al carrito persistido.

## Requirements

### Requirement: Cart search modal is sized for the viewport

The cart-search modal on `/carrito` SHALL render at a width appropriate to the viewport: on desktop (`sm` breakpoint, ≥640px) it MUST expand up to `max-w-2xl` (~672px); on mobile it MUST fit within the screen width with comfortable margins and no horizontal page scroll.

#### Scenario: Desktop width

- **WHEN** the modal opens on a viewport ≥640px wide
- **THEN** the modal renders up to ~672px wide (`sm:max-w-2xl`), not capped at the Dialog default of 384px

#### Scenario: Mobile width

- **WHEN** the modal opens on a viewport <640px wide
- **THEN** the modal fits within the screen with margins and the page does not scroll horizontally

### Requirement: Search results adapt their layout to the viewport

Search results in the modal SHALL render as a table (Product, Category, Sources, Price from, action) on viewports ≥640px, and as stacked cards on viewports <640px. Each mobile card MUST show the product name, category, source chips, minimum price, and the add/added control.

#### Scenario: Table on desktop

- **WHEN** results are shown on a viewport ≥640px
- **THEN** they render as a table with columns Product, Category, Sources, Price from, and the add action

#### Scenario: Cards on mobile

- **WHEN** results are shown on a viewport <640px
- **THEN** each result renders as a stacked card containing product name, category, source chips, minimum price, and the add/added control
- **AND** no horizontal scrolling is required to see any of that content

### Requirement: Search requests are debounced

The modal SHALL debounce the search input so that a request to `/api/v1/buscar_carrito` is sent only after the user has stopped typing for 300ms, not on every keystroke. Typing MUST also reset pagination to page 1.

#### Scenario: No request per keystroke

- **WHEN** the user types "leche" quickly (5 keystrokes within 300ms of each other)
- **THEN** only one search request is sent, with the final value "leche", 300ms after the last keystroke

#### Scenario: Typing resets pagination

- **WHEN** the user is on page 2 of results and edits the search text
- **THEN** the next request is for page 1 of the new query

### Requirement: Previous results remain visible while searching

While a new search request is in flight, the modal SHALL keep displaying the previous results (with a loading indicator) instead of clearing the list, avoiding flicker.

#### Scenario: No flicker between queries

- **WHEN** results for "leche" are displayed and the user types more characters triggering a new request
- **THEN** the "leche" results remain visible with a loading indicator until the new results arrive

### Requirement: Adding a product from search results

Selecting a result SHALL add the product's `id` to the persisted cart (Zustand store backed by localStorage), show a confirmation toast, and close the modal. Products already in the cart MUST show an "added" state instead of the add button.

#### Scenario: Add a product

- **WHEN** the user taps/clicks the add control on a result not in the cart
- **THEN** the product id is added to the cart store, a confirmation toast appears, and the modal closes

#### Scenario: Already in cart

- **WHEN** a result's product is already in the cart
- **THEN** the result shows an "added" indicator and no add button
