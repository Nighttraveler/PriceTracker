# Plan: Carrito de compras con localStorage

## Context

El usuario quiere un carrito persistente por browser (sin DB) que:
1. Se arma buscando productos (desde `/buscar`)
2. Muestra un **carrito óptimo** (cada producto asignado a la fuente más barata)
3. Muestra una **tabla comparativa** de precios por fuente (solo productos en 2+ fuentes)

El carrito vive en `localStorage` del browser. Los precios se consultan al servidor via `fetch` cuando se abre la página del carrito.

---

## Archivos a crear/modificar

| Archivo | Cambio |
|---|---|
| `db.py` | Nuevo método `get_precios_carrito(ids)` |
| `app.py` | Nueva ruta `/carrito` + endpoint `/api/carrito` (POST) + helper `_compute_carrito_optimo` |
| `templates/carrito.html` | Nueva página: lista del carrito, carrito óptimo, tabla comparativa |
| `templates/buscar.html` | Botón "Agregar al carrito" por producto; estado "En carrito" si ya está |
| `templates/base.html` | Badge con count del carrito en la navbar |
| `docs/plans/carrito.md` | Copia del plan en el repo (crear carpeta) |

---

## Implementación paso a paso

### 1. `db.py` — `get_precios_carrito(producto_ids)`

Reutiliza el patrón `max_por_fuente + latest` ya existente en `buscar_productos` y `get_carrito_optimo`, filtrando por IDs en lugar de nombre.

```python
def get_precios_carrito(self, producto_ids: list[int]):
    if not producto_ids:
        return []
    placeholders = ",".join("?" * len(producto_ids))
    return self.conn.execute(f"""
        WITH max_por_fuente AS (
            SELECT v.fuente_id, MAX(date(pr.fecha)) AS max_fecha
            FROM precios pr JOIN variantes v ON pr.variante_id = v.id
            GROUP BY v.fuente_id
        ),
        latest AS (
            SELECT v.producto_id, f.nombre AS fuente, pr.precio, v.url_producto
            FROM precios pr
            JOIN variantes v ON pr.variante_id = v.id
            JOIN fuentes f ON v.fuente_id = f.id
            JOIN max_por_fuente m ON v.fuente_id = m.fuente_id
                AND date(pr.fecha) = m.max_fecha
        )
        SELECT p.id, p.nombre_normalizado, p.categoria,
               l.fuente, l.precio, l.url_producto
        FROM productos p
        JOIN latest l ON p.id = l.producto_id
        WHERE p.id IN ({placeholders})
        ORDER BY p.nombre_normalizado, l.fuente
    """, producto_ids).fetchall()
```

### 2. `app.py` — helper + rutas

**Helper `_compute_carrito_optimo(rows)`** (función module-level, no método):
- Agrupa las filas por producto → `{id, nombre, categoria, fuentes: {fuente: {precio, url}}}`
- Para cada producto, asigna a la fuente con `MIN(precio)`
- Agrupa asignaciones por fuente → lista de bloques con `total` y `ahorro_total`
- Retorna `(productos, carrito)` — misma forma que `get_carrito_optimo` de db.py

**Ruta `/carrito` (GET)**:
```python
@app.route("/carrito")
def carrito():
    return render_template("carrito.html")
```
Solo renderiza el shell; el JS hace el fetch.

**Ruta `/api/carrito` (POST)**:
```python
@app.route("/api/carrito", methods=["POST"])
def api_carrito():
    ids = [int(i) for i in (request.get_json() or {}).get("ids", [])]
    rows = get_db().get_precios_carrito(ids)
    productos, carrito = _compute_carrito_optimo(rows)
    fuentes = sorted({f for p in productos for f in p["fuentes"]})
    return jsonify({"productos": productos, "carrito": carrito, "fuentes": fuentes})
```

### 3. `templates/carrito.html`

Estructura de la página:
```
Navbar (con badge)
│
├─ Sección: "Mi carrito" (lista de items + botón limpiar)
│   └─ <ul> generada por JS desde localStorage
│       └─ cada item: nombre | [×] quitar
│
├─ Sección: "Carrito óptimo" (igual al bloque de ahorro.html)
│   └─ columnas por fuente, cada una con sus productos + total + ahorro
│
└─ Sección: "Comparativa por fuente" (tabla como precios.html)
    └─ solo productos presentes en 2+ fuentes
    └─ columna por fuente, celda verde = más barata, ★
```

El JS en esta página:
1. Al cargar: lee `localStorage`, si está vacío muestra "carrito vacío"
2. Si hay items: hace `fetch('/api/carrito', {method:'POST', body: JSON.stringify({ids})})` 
3. Renderiza las dos secciones con los datos recibidos

### 4. `templates/buscar.html`

En cada fila de resultados, agregar botón:
```html
<button class="btn btn-sm btn-outline-success add-cart-btn"
        data-id="{{ p.id }}"
        data-nombre="{{ p.nombre }}"
        data-categoria="{{ p.categoria or '' }}">
  + Carrito
</button>
```

JS en la página:
- Al cargar: para cada botón, si `isInCart(id)` → cambiar texto a "✓ En carrito" y deshabilitar
- Click: `addToCart(id, nombre, cat)` → actualizar badge navbar + estado del botón

### 5. `templates/base.html`

En la navbar, agregar link al carrito con badge:
```html
<a href="/carrito" class="nav-link text-white position-relative">
  🛒 <span id="cart-badge" class="badge bg-danger position-absolute" style="font-size:0.6rem; top:0; right:-8px"></span>
</a>
```

JS compartido (en base.html, antes de `</body>`):
```javascript
const CART_KEY = 'pt_carrito';
function getCart()       { return JSON.parse(localStorage.getItem(CART_KEY) || '[]'); }
function saveCart(c)     { localStorage.setItem(CART_KEY, JSON.stringify(c)); updateBadge(); }
function addToCart(id, nombre, cat) {
    const c = getCart();
    if (!c.find(i => i.id === id)) { c.push({id, nombre, cat}); saveCart(c); }
}
function removeFromCart(id) { saveCart(getCart().filter(i => i.id !== id)); }
function isInCart(id)    { return getCart().some(i => i.id === id); }
function updateBadge()   {
    const n = getCart().length;
    const b = document.getElementById('cart-badge');
    if (b) { b.textContent = n || ''; b.style.display = n ? '' : 'none'; }
}
document.addEventListener('DOMContentLoaded', updateBadge);
```

---

## Notas de diseño

- El JS del carrito (funciones base) vive en `base.html` para que esté disponible en todas las páginas sin duplicación.
- `carrito.html` renderiza solo un shell; todo el contenido de precios se inyecta vía JS tras el fetch para evitar pasar IDs al servidor en la URL (puede ser larga con muchos productos).
- La comparativa multi-fuente reutiliza exactamente los mismos estilos CSS que `buscar.html` (`.fuente-chip`, `.cheapest`, `badge-up/down`).
- No se guarda nada en la DB. Si el usuario limpia localStorage, el carrito se pierde.

---

## Verificación

```bash
# 1. Levantar el servidor
source .venv/bin/activate && python app.py

# 2. En el browser:
#    - Ir a /buscar, buscar "leche", agregar 3 productos → badge muestra 3
#    - Ir a /carrito → lista aparece, secciones se cargan
#    - Quitar un producto → lista se actualiza, badge baja a 2
#    - Limpiar carrito → página muestra "carrito vacío"
#    - Recargar → carrito persiste desde localStorage

# 3. Verificar API directamente:
curl -s -X POST http://localhost:5000/api/carrito \
  -H 'Content-Type: application/json' \
  -d '{"ids":[1,2,3]}' | python -m json.tool
```
