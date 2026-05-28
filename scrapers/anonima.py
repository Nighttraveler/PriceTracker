#!/usr/bin/env python3
"""scrapers/anonima.py — Scraper de La Anónima."""

import logging
from scrapers.base import BaseScraper

log = logging.getLogger(__name__)

CATEGORIAS_URL = [
    "almacen/n1_512/",
    "bebidas/n1_513/",
    "lacteos-y-frescos/n1_516/",
    "limpieza/n1_514/",
    "perfumeria/n1_820/",
    "congelados/n1_766/",
    "carniceria/n1_518/",
]


class AnonimaScraper(BaseScraper):
    url_base = "https://www.laanonima.com.ar"

    def fetch_all(self, limit=None) -> list[dict]:
        productos = []
        for categoria in CATEGORIAS_URL:
            url = f"{self.url_base}/{categoria}"
            try:
                soup = self.get(url)
                items = soup.select(".producto-item")
                if not items:
                    continue

                for item in items:
                    try:
                        a_el = item.find('a', href=True)
                        if not a_el:
                            continue

                        nombre = a_el.get('data-nombre')
                        precio_str = a_el.get('data-precio') or a_el.get('data-precio_oferta')

                        if not nombre or not precio_str:
                            continue

                        # data-precio contains a raw number like '1190' or similar
                        precio = float(precio_str)

                        productos.append({
                            "nombre": nombre,
                            "precio": precio,
                            "url":    self.url_base + a_el["href"] if a_el["href"] else "",
                        })
                    except Exception as e:
                        log.debug(f"Error en item: {e}")

                    if limit and len(productos) >= limit:
                        return productos

            except Exception as e:
                log.warning(f"Error en {url}: {e}")

        return productos
