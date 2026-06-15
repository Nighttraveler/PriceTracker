## 1. Update reflectState in index.html

- [x] 1.1 Change the `isInCart` branch in `reflectState()`: set `btn.textContent = '✗'`, keep `btn.disabled = false`, swap classes to `btn-outline-danger` instead of `btn-success`
- [x] 1.2 Update the else branch to restore `btn-outline-secondary` and `🛒` (remove any leftover `btn-success` and `btn-outline-danger` cleanup)

## 2. Update click handler in index.html

- [x] 2.1 In the `.cart-add-btn` click listener, replace the unconditional `addToCart()` call with a toggle: if `isInCart(id)` call `removeFromCart(id)`, else call `addToCart(id)`, then call `reflectState(this)` in both cases

## 3. Verify

- [ ] 3.1 Open the home page in a browser, confirm 🛒 button adds item and flips to ✗ (red outline)
- [ ] 3.2 Confirm clicking ✗ removes item and reverts to 🛒
- [ ] 3.3 Confirm page reload preserves state (localStorage persistence)
- [ ] 3.4 Confirm cart badge count updates correctly on add and remove
