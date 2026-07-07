# cart-export

## Purpose

Lets a user on the cart page export the current optimal split as a single self-contained,
offline-capable HTML checklist they can download to their phone and check off items against
while shopping in-store.

## Requirements

### Requirement: Download button on the cart page
The cart page SHALL show a "Download list" action that is enabled only when the cart contains at least one resolved product (a non-empty optimal split). Activating it SHALL trigger a browser download of a single HTML file named `lista-YYYY-MM-DD.html` (export date), generated entirely client-side from the optimal-cart data already loaded on the page, with no additional API calls.

#### Scenario: Cart with products
- **WHEN** the cart page has loaded an optimal split with at least one product and the user taps "Download list"
- **THEN** the browser downloads `lista-<today>.html` without any network request beyond those already made by the page

#### Scenario: Empty cart
- **WHEN** the cart has no resolved products
- **THEN** the download action is disabled or hidden

### Requirement: Exported file is self-contained and offline-capable
The exported HTML file SHALL contain all markup, styles, and script inline, SHALL reference no external resources (no network requests of any kind), and SHALL render and function when opened from the phone's local storage (`file://` or `content://`) in any modern mobile browser.

#### Scenario: Opened offline
- **WHEN** the file is opened on a phone with no network connectivity
- **THEN** the full checklist renders and all interactions work

### Requirement: Checklist content mirrors the optimal split
The exported file SHALL show a date-stamped header and one section per supermarket from the optimal split, each listing its items with name and price in ARS formatting, plus the store total and total savings. A grand total across all stores SHALL be shown. Product IDs that could not be resolved SHALL be noted. All interpolated text SHALL be HTML-escaped.

#### Scenario: Multi-store split
- **WHEN** the optimal cart assigns items to two supermarkets
- **THEN** the file shows two sections, each with its items, store total and savings, and a grand total across both

#### Scenario: Product name contains HTML-special characters
- **WHEN** a product name contains characters such as `&`, `<`, or `"`
- **THEN** the name renders literally and the document markup is not broken

### Requirement: Items can be checked off with live remaining totals
Each item row SHALL toggle between unchecked and checked when tapped anywhere on the row. Checked items SHALL be visibly struck through and excluded from their store's "remaining" subtotal and the grand remaining total, both of which SHALL update immediately on each toggle.

#### Scenario: Checking an item
- **WHEN** the user taps an unchecked item row priced $1.200 in a store with $5.000 remaining
- **THEN** the row shows strikethrough and the store's remaining subtotal drops to $3.800

#### Scenario: Unchecking an item
- **WHEN** the user taps a checked item row
- **THEN** the strikethrough is removed and its price is added back to the remaining subtotals

### Requirement: Best-effort checkbox persistence
The exported file SHALL attempt to persist checked-item state to `localStorage` keyed by the export date (`lista-YYYY-MM-DD`), and SHALL degrade silently to in-memory state when storage is unavailable, without errors or visible warnings.

#### Scenario: Storage unavailable
- **WHEN** the browser denies localStorage access (e.g., file opened via a `content://` URI)
- **THEN** checking items still works for the open tab and no error is shown

#### Scenario: Storage available and file reopened
- **WHEN** localStorage is available, items were checked, and the same file is reopened in the same browser context
- **THEN** previously checked items are restored as checked, subject to the browser's storage partitioning behavior for `file://` URLs — this persistence is best-effort, not guaranteed

#### Scenario: Multiple downloads on the same day share checked state
- **WHEN** the user downloads the list more than once on the same calendar day (e.g., after refreshing the cart) and localStorage is available in the browser context
- **THEN** the checked-item state persisted by an earlier download of that day is restored in the later download, since both share the same `lista-YYYY-MM-DD` storage key

### Requirement: Light/dark theme toggle
The exported file SHALL render in a light theme by default regardless of the OS or browser's `prefers-color-scheme` setting, and SHALL NOT automatically follow the OS dark-mode preference. A toggle button in the header (labeled "🌙 Oscuro" in light mode, "☀️ Claro" in dark mode) SHALL let the user manually switch between light and dark themes. The chosen theme SHALL be persisted in `localStorage` under a key shared across all exported files (not scoped per file or export date). The CSS `color-scheme` property SHALL be kept in sync with the chosen theme (`light` by default, `dark` when toggled) so native form controls such as checkboxes render consistently with the chosen theme rather than following the OS preference independently.

#### Scenario: Default theme ignores OS dark mode
- **WHEN** the file is opened on a device or browser with a system-wide dark-mode preference enabled
- **THEN** the file renders in the light theme until the user manually toggles it

#### Scenario: Toggling to dark theme
- **WHEN** the user taps the "🌙 Oscuro" toggle button
- **THEN** the file switches to the dark theme, the button label changes to "☀️ Claro", the CSS `color-scheme` property is set to `dark`, and the choice is saved to the shared `localStorage` key

#### Scenario: Theme choice persists across exports
- **WHEN** the user previously toggled to the dark theme in one exported file and later opens a different exported list file in the same browser context
- **THEN** the newly opened file also renders in the dark theme, since the theme preference is read from the shared storage key rather than a per-file or per-date key
