#!/usr/bin/env python3
"""scrapers/carrefour.py — Scraper de Carrefour Argentina (VTEX catalog API)."""

from .vtex_base import VTEXScraper, VTEX_MAX_OFFSET, PAGE_SIZE, MAX_RETRIES  # re-exported for tests

CATEGORIAS = {
    161: "almacen",
    222: "desayuno-y-merienda",
    255: "bebidas",
    292: "lacteos-y-productos-frescos",
    321: "carnes-y-pescados",
    330: "frutas-y-verduras",
    336: "panaderia",
    347: "congelados",
    359: "limpieza",
    402: "perfumeria-y-farmacia",
    471: "mascotas",
}


class CarrefourScraper(VTEXScraper):
    url_base = "https://www.carrefour.com.ar"
    name = "Carrefour"
    page_delay = (0.5, 1.2)

    def _get_categories(self) -> dict[int, str]:
        return CATEGORIAS
