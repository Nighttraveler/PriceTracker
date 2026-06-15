## Context

The home page (`templates/index.html`) has three tables with `.cart-add-btn` buttons. The current `reflectState()` function shows a disabled ✓ when the item is in cart — no action possible. The global `removeFromCart(id)` helper already exists in `base.html` but is not used from the home page.

## Goals / Non-Goals

**Goals:**
- When a `.cart-add-btn` item is in the cart, show an active ✗ button (red outline, `btn-outline-danger`) that removes the item on click.
- Revert to 🛒 state after removal.
- Reuse existing `removeFromCart()` and `isInCart()` from `base.html` — no new localStorage logic.

**Non-Goals:**
- Changes to `base.html`, `app.py`, or any backend file.
- Changing the cart page (`carrito.html`) behavior.
- Animating transitions between states.

## Decisions

**Toggle in place vs. separate button**: Reuse the same button element and toggle its label/class. Avoids adding DOM nodes and keeps the HTML unchanged.

**Label choice — ✗ vs ×**: Use `✗` (U+2717 BALLOT X) consistent with a "cancel/remove" action. Lighter visual weight than ❌.

**Color**: `btn-outline-danger` (Bootstrap red) for the remove state — visually distinct from the add state (`btn-outline-secondary`) and the old success state (`btn-success`).

**State on page load**: `reflectState()` is called once per button on `DOMContentLoaded`, same as before. If the user adds/removes from another tab, state won't sync — acceptable given the localStorage scope.

## Risks / Trade-offs

- [Button shows stale state if localStorage changes in another tab] → Acceptable; no cross-tab sync is required.
- [✗ character may not render on very old browsers] → Acceptable; target is modern browsers.
