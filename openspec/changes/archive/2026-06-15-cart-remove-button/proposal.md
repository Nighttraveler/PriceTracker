## Why

The "add to cart" button on the home page currently shows a disabled checkmark (✓) when an item is already in the cart, giving no way to remove it from that same page. Users must navigate to the cart page to deselect items, which is friction for a quick add/remove workflow.

## What Changes

- Replace the disabled ✓ state with an active ✗ (remove) button when an item is already in the cart.
- Clicking ✗ removes the item from the cart and reverts the button to the "add" (🛒) state.
- Applies to all three `cart-add-btn` locations on the home page: TOP canasta básica table, Subas highlights table, Bajas highlights table.

No backend changes. No new routes. No Alembic migration required.

## Capabilities

### New Capabilities

- `cart-toggle-home`: Toggle cart membership (add/remove) directly from the home page dashboard buttons.

### Modified Capabilities

_(none — no existing spec-level behavior changes)_

## Impact

- `templates/index.html`: `reflectState()` function and click handler in `{% block extra_scripts %}`.
- No changes to `base.html`, `app.py`, or any backend file.
- Does not affect cached routes (/, /precios, /ahorro, /buscar) in terms of cache behavior.
- Does not touch latest-price queries.
