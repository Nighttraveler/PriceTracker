## ADDED Requirements

### Requirement: Home page cart buttons toggle membership
Each `.cart-add-btn` on the home page SHALL reflect and control cart membership: clicking adds the item when not in cart, and removes it when already in cart. The `removeFromCart()` global helper from `base.html` MUST be used for removal.

#### Scenario: Button shows add state when item is not in cart
- **WHEN** the page loads and the item is not in localStorage cart
- **THEN** the button shows 🛒, is enabled, and has class `btn-outline-secondary`

#### Scenario: Button shows remove state when item is in cart
- **WHEN** the page loads and the item is in localStorage cart
- **THEN** the button shows ✗, is enabled, and has class `btn-outline-danger`

#### Scenario: Clicking add button adds item and flips to remove state
- **WHEN** user clicks a 🛒 button
- **THEN** the item is added to localStorage cart and the button immediately shows ✗ with `btn-outline-danger`

#### Scenario: Clicking remove button removes item and flips to add state
- **WHEN** user clicks a ✗ button
- **THEN** the item is removed from localStorage cart and the button immediately shows 🛒 with `btn-outline-secondary`
