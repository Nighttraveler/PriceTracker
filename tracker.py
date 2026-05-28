#!/usr/bin/env python3
"""
Hermes Price Tracker — Script principal
Scrapea precios de La Anónima, Día y Encombo y los guarda en SQLite.
"""

import argparse
import logging
from datetime import date
from db import Database
from normalizer import Normalizer
from scrapers.anonima import AnonimaScraper
from scrapers.dia import DiaScraper
from scrapers.encombo import EncomboScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/tracker.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

SCRAPERS = {
    "anonima": AnonimaScraper,
    "dia":     DiaScraper,
    "encombo": EncomboScraper,
}


def run(source: str, dry_run: bool = False, limit: int = None):
    db = Database("data/precios.db")
    db.init_schema()
    normalizer = Normalizer(db)

    fuentes = list(SCRAPERS.keys()) if source == "all" else [source]

    for fuente_nombre in fuentes:
        log.info(f"=== Scraping: {fuente_nombre} ===")
        scraper_cls = SCRAPERS[fuente_nombre]
        scraper = scraper_cls()

        try:
            productos = scraper.fetch_all(limit=limit)
            log.info(f"{fuente_nombre}: {len(productos)} productos obtenidos")

            if dry_run:
                log.info("[DRY-RUN] Primeros resultados:")
                for p in productos[:5]:
                    log.info(f"  {p}")
                continue

            fuente_id = db.get_or_create_fuente(fuente_nombre, scraper.url_base)
            hoy = date.today().isoformat()
            insertados = 0

            for producto in productos:
                try:
                    prod_id = normalizer.obtener_o_crear_producto(
                        producto["nombre"], fuente_id
                    )
                    variante_id = db.get_or_create_variante(
                        prod_id, fuente_id,
                        producto["nombre"],
                        producto.get("url", "")
                    )
                    db.insertar_precio(variante_id, producto["precio"], hoy)
                    insertados += 1
                except Exception as e:
                    log.warning(f"Error procesando '{producto.get('nombre')}': {e}")

            log.info(f"{fuente_nombre}: {insertados} precios guardados para {hoy}")

        except Exception as e:
            log.error(f"Error scraping {fuente_nombre}: {e}", exc_info=True)

    log.info("Scraping finalizado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hermes Price Tracker")
    parser.add_argument("--source", default="all",
                        choices=["all", "anonima", "dia", "encombo"])
    parser.add_argument("--dry-run", action="store_true",
                        help="Scrapear sin guardar en DB")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limitar cantidad de productos por fuente")
    args = parser.parse_args()

    run(args.source, dry_run=args.dry_run, limit=args.limit)
