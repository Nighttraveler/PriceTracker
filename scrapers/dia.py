#!/usr/bin/env python3
"""scrapers/dia.py — Scraper de Supermercados Día (VTEX catalog API)."""

import logging
import time
import random
import requests

log = logging.getLogger(__name__)

URL_BASE = "https://diaonline.supermercadosdia.com.ar"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "es-AR,es;q=0.9",
}

PAGE_SIZE = 50
VTEX_MAX_OFFSET = 2500
MAX_RETRIES = 3

# Slugs de categorías a scrapear — se resuelven a IDs desde el árbol VTEX.
# Usar categorías padre siempre que sea posible para capturar todas las subcategorías.
# "frescos" incluye: leches, lácteos, carnicería, frutas-y-verduras, fiambrería, pastas.
CATEGORIAS_SLUG = [
    "almacen",       # secos, aceites, pastas, arroz, etc.
    "desayuno",      # galletitas, infusiones, para untar
    "bebidas",       # agua, jugos, gaseosas, vinos
    "frescos",       # leches + lácteos + carnes + frutas + verduras
    "congelados",    # helados, medallones, etc.
    "limpieza",      # detergentes, lavandina, etc.
    "perfumeria",    # higiene personal, farmacia, cuidado del pelo
    "mascotas",      # alimentos y accesorios para mascotas
]


class DiaScraper:
    url_base = URL_BASE

    def _get_category_tree(self) -> dict:
        """Obtiene el árbol de categorías VTEX y devuelve {slug: id}."""
        url = f"{self.url_base}/api/catalog_system/pub/category/tree/3"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            mapping = {}

            def flatten(nodes):
                for node in nodes:
                    slug = node.get("url", "").rstrip("/").split("/")[-1].lower()
                    if slug:
                        mapping[slug] = node["id"]
                    if node.get("hasChildren"):
                        flatten(node.get("children", []))

            flatten(resp.json())
            return mapping
        except Exception as e:
            log.warning(f"Día: no se pudo obtener árbol de categorías: {e}")
            return {}

    def _get_page(self, cat_id: int, from_: int) -> tuple[list, int]:
        url = (
            f"{self.url_base}/api/catalog_system/pub/products/search"
            f"?fq=C:{cat_id}&_from={from_}&_to={from_ + PAGE_SIZE - 1}"
        )
        for attempt in range(MAX_RETRIES):
            time.sleep(random.uniform(0.8, 1.8))
            resp = requests.get(url, headers=HEADERS, timeout=15)

            if resp.status_code == 429:
                wait = 5 * (2 ** attempt)
                log.warning(f"Día: 429 en offset {from_}, reintentando en {wait}s (intento {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait)
                continue

            resp.raise_for_status()

            total = 0
            resources = resp.headers.get("resources", "")
            if "/" in resources:
                try:
                    total = int(resources.split("/")[1])
                except ValueError:
                    pass

            return resp.json(), total

        raise requests.exceptions.RetryError(f"Día: 429 persistente después de {MAX_RETRIES} intentos en offset {from_}")

    def fetch_all(self, limit: int = None) -> list[dict]:
        cat_tree = self._get_category_tree()
        if not cat_tree:
            log.error("Día: árbol de categorías vacío, abortando")
            return []

        log.info(f"Día: {len(cat_tree)} categorías disponibles en VTEX")

        productos = []
        for slug in CATEGORIAS_SLUG:
            cat_id = cat_tree.get(slug)
            if not cat_id:
                log.warning(f"Día: categoría '{slug}' no encontrada en el árbol, omitiendo")
                continue

            log.info(f"Día: categoría {slug} (id={cat_id})")
            from_ = 0
            total = None

            while from_ < VTEX_MAX_OFFSET:
                try:
                    items, total_cat = self._get_page(cat_id, from_)
                    if total is None:
                        total = total_cat
                        log.info(f"  {slug}: {total} productos totales")

                    if not items:
                        break

                    for item in items:
                        try:
                            nombre = item.get("productName", "").strip()
                            vtex_items = item.get("items", [])
                            sellers = vtex_items[0].get("sellers", []) if vtex_items else []
                            offer = sellers[0].get("commertialOffer", {}) if sellers else {}
                            precio = offer.get("Price", 0)
                            link = item.get("link", "")

                            if not nombre or not precio:
                                continue

                            productos.append({
                                "nombre": nombre,
                                "precio": float(precio),
                                "url": link if link.startswith("http") else f"{self.url_base}{link}",
                            })
                        except Exception as e:
                            log.debug(f"Día: error en item: {e}")

                        if limit and len(productos) >= limit:
                            return productos

                    from_ += PAGE_SIZE
                    if total and from_ >= total:
                        break

                except Exception as e:
                    log.warning(f"Día: error en {slug} offset {from_}: {e}")
                    break

        return productos
