#!/usr/bin/env python3
"""scrapers/dia.py — Scraper for Supermercados Día (VTEX Catalog API)."""

import logging
import requests

from .vtex_base import VTEXScraper, HEADERS

log = logging.getLogger(__name__)

# Category slugs to scrape — resolved to IDs from the VTEX category tree.
# Use parent categories whenever possible to capture all subcategories.
# "frescos" includes: leches, lácteos, carnicería, frutas-y-verduras, fiambrería, pastas.
CATEGORIAS_SLUG = [
    "almacen",       # dry goods, oils, pasta, rice, etc.
    "desayuno",      # biscuits, infusions, spreads
    "bebidas",       # water, juices, sodas, wines
    "frescos",       # milk + dairy + meats + fruits + vegetables
    "congelados",    # ice cream, frozen patties, etc.
    "limpieza",      # detergents, bleach, etc.
    "perfumeria",    # personal hygiene, pharmacy, hair care
    "mascotas",      # pet food and accessories
]


class DiaScraper(VTEXScraper):
    url_base = "https://diaonline.supermercadosdia.com.ar"
    name = "Día"
    page_delay = (0.8, 1.8)

    def _get_categories(self) -> dict[int, str]:
        url = f"{self.url_base}/api/catalog_system/pub/category/tree/3"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            slug_to_id: dict[str, int] = {}

            def flatten(nodes):
                for node in nodes:
                    slug = node.get("url", "").rstrip("/").split("/")[-1].lower()
                    if slug:
                        slug_to_id[slug] = node["id"]
                    if node.get("hasChildren"):
                        flatten(node.get("children", []))

            flatten(resp.json())
            log.info(f"Día: {len(slug_to_id)} categories available in VTEX")

            return {
                slug_to_id[s]: s
                for s in CATEGORIAS_SLUG
                if s in slug_to_id
            }
        except Exception as e:
            log.warning(f"Día: could not fetch category tree: {e}")
            return {}
