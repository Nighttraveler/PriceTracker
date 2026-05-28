#!/usr/bin/env python3
"""scrapers/carrefour.py — Scraper de Carrefour Argentina (VTEX catalog API)."""

import logging
import time
import random
import requests

log = logging.getLogger(__name__)

# category_id → slug (solo supermercado, sin electro/ropa/etc)
CATEGORIAS = {
    161:  "almacen",
    222:  "desayuno-y-merienda",
    255:  "bebidas",
    292:  "lacteos-y-productos-frescos",
    321:  "carnes-y-pescados",
    330:  "frutas-y-verduras",
    336:  "panaderia",
    347:  "congelados",
    359:  "limpieza",
    402:  "perfumeria-y-farmacia",
    471:  "mascotas",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "es-AR,es;q=0.9",
}

PAGE_SIZE = 50


class CarrefourScraper:
    url_base = "https://www.carrefour.com.ar"

    def _get_page(self, cat_id: int, from_: int) -> tuple[list, int]:
        url = (
            f"{self.url_base}/api/catalog_system/pub/products/search"
            f"?fq=C:{cat_id}&_from={from_}&_to={from_ + PAGE_SIZE - 1}"
        )
        time.sleep(random.uniform(0.5, 1.2))
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        # resources header: "0-49/6016"
        total = 0
        resources = resp.headers.get("resources", "")
        if "/" in resources:
            try:
                total = int(resources.split("/")[1])
            except ValueError:
                pass

        return resp.json(), total

    def fetch_all(self, limit: int = None) -> list[dict]:
        productos = []

        for cat_id, cat_slug in CATEGORIAS.items():
            log.info(f"Carrefour: categoría {cat_slug} (id={cat_id})")
            from_ = 0
            total = None

            while True:
                try:
                    items, total_cat = self._get_page(cat_id, from_)
                    if total is None:
                        total = total_cat
                        log.info(f"  {cat_slug}: {total} productos totales")

                    if not items:
                        break

                    for item in items:
                        try:
                            nombre = item.get("productName", "").strip()
                            sellers = item.get("items", [{}])[0].get("sellers", [{}])
                            offer = sellers[0].get("commertialOffer", {}) if sellers else {}
                            precio = offer.get("Price", 0)
                            link = item.get("link", "")

                            if not nombre or not precio:
                                continue

                            productos.append({
                                "nombre": nombre,
                                "precio": float(precio),
                                "url": f"{self.url_base}{link}" if link.startswith("/") else link,
                            })
                        except Exception as e:
                            log.debug(f"Error en item: {e}")

                        if limit and len(productos) >= limit:
                            return productos

                    from_ += PAGE_SIZE
                    if total and from_ >= total:
                        break

                except Exception as e:
                    log.warning(f"Error en {cat_slug} offset {from_}: {e}")
                    break

        return productos
