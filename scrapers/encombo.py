#!/usr/bin/env python3
"""scrapers/encombo.py — Scraper de Encombo (agregador de precios)."""

import logging
from scrapers.base import BaseScraper

log = logging.getLogger(__name__)

CATEGORIAS_URL = [
    "almacen.html",
    "almacen/lacteos.html",
    "bebidas.html",
    "limpieza.html",
    "perfumeria.html",
    "cuidado-de-la-ropa.html",
]

SELECTORES = {
    "listado":   "li.product-item",
    "nombre":    "strong.product-item-name a",
    "precio":    "span.price",
    "link":      "strong.product-item-name a",
    "siguiente": "a.action.next",
}


class EncomboScraper(BaseScraper):
    url_base = "https://encombo.com.ar"

    def fetch_all(self, limit=None) -> list[dict]:
        productos = []
        for categoria in CATEGORIAS_URL:
            page = 1
            while True:
                url = f"{self.url_base}/{categoria}?p={page}"
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

                            nombre = nombre_el.get_text(strip=True)

                            productos.append({
                                "nombre": nombre,
                                "precio": self.limpiar_precio(precio_el.get_text(strip=True)),
                                "url":    link_el["href"] if link_el else "",
                            })
                        except Exception as e:
                            log.debug(f"Error en item: {e}")

                        if limit and len(productos) >= limit:
                            return productos

                    siguiente = soup.select_one(SELECTORES["siguiente"])
                    if not siguiente:
                        break
                    page += 1

                except Exception as e:
                    log.warning(f"Error en {url}: {e}")
                    break

        return productos
