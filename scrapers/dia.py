#!/usr/bin/env python3
"""scrapers/dia.py — Scraper de Supermercados Día (VTEX catalog API)."""

import logging
import requests

from .vtex_base import VTEXScraper, HEADERS

log = logging.getLogger(__name__)

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
            log.info(f"Día: {len(slug_to_id)} categorías disponibles en VTEX")

            return {
                slug_to_id[s]: s
                for s in CATEGORIAS_SLUG
                if s in slug_to_id
            }
        except Exception as e:
            log.warning(f"Día: no se pudo obtener árbol de categorías: {e}")
            return {}
