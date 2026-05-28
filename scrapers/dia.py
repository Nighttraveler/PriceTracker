#!/usr/bin/env python3
"""scrapers/dia.py — Scraper de Supermercados Día."""

import logging
from scrapers.base import BaseScraper

log = logging.getLogger(__name__)

CATEGORIAS_URL = [
    "almacen", "lacteos", "bebidas", "carnes-y-pescados",
    "limpieza", "higiene-personal", "congelados",
]

SELECTORES = {
    "listado":   'section[class*="vtex-product-summary-"]',
    "nombre":    '[class*="productBrand"], [class*="brand"], [class*="productName"]',
    "precio":    '[class*="sellingPriceValue"], [class*="sellingPrice"]',
    "link":      'a[href*="/p"]',
}


class DiaScraper(BaseScraper):
    url_base = "https://diaonline.supermercadosdia.com.ar"

    def fetch_all(self, limit=None) -> list[dict]:
        productos = []
        for categoria in CATEGORIAS_URL:
            page = 1
            while True:
                url = f"{self.url_base}/{categoria}?page={page}"
                try:
                    soup = self.get(url)
                    items = soup.select(SELECTORES["listado"])
                    if not items:
                        break

                    for item in items:
                        try:
                            nombre_el = item.select_one(SELECTORES["nombre"])
                            precio_el = item.select_one(SELECTORES["precio"])
                            link_el   = item.select_one(SELECTORES["link"])

                            if not nombre_el or not precio_el:
                                continue

                            productos.append({
                                "nombre": nombre_el.get_text(strip=True),
                                "precio": self.limpiar_precio(precio_el.get_text(strip=True)),
                                "url":    self.url_base + link_el["href"] if link_el else "",
                            })
                        except Exception as e:
                            log.debug(f"Error en item: {e}")

                        if limit and len(productos) >= limit:
                            return productos

                    page += 1

                except Exception as e:
                    log.warning(f"Error en {url}: {e}")
                    break

        return productos
