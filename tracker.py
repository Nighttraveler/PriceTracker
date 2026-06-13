#!/usr/bin/env python3
"""
Price Tracker — Main scraping script.
Scrapes prices from La Anónima, Día, Encombo, and Carrefour and stores them in the DB.
"""

import argparse
import logging
from datetime import date
from db import Database
from normalizer import Normalizer
from scrapers.anonima import AnonimaScraper
from scrapers.dia import DiaScraper
from scrapers.encombo import EncomboScraper
from scrapers.carrefour import CarrefourScraper

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
    "anonima":   AnonimaScraper,
    "dia":       DiaScraper,
    "encombo":   EncomboScraper,
    "carrefour": CarrefourScraper,
}


def run(source: str, dry_run: bool = False, limit: int = None):
    db = Database("data/precios.db")
    db.init_schema()
    normalizer = Normalizer(db)

    sources = list(SCRAPERS.keys()) if source == "all" else [source]

    for source_name in sources:
        log.info(f"=== Scraping: {source_name} ===")
        scraper_cls = SCRAPERS[source_name]
        scraper = scraper_cls()

        try:
            products = scraper.fetch_all(limit=limit)
            log.info(f"{source_name}: {len(products)} products fetched")

            if dry_run:
                log.info("[DRY-RUN] First results:")
                for p in products[:5]:
                    log.info(f"  {p}")
                continue

            fuente_id = db.get_or_create_fuente(source_name, scraper.url_base)
            hoy = date.today().isoformat()
            inserted = 0

            for producto in products:
                try:
                    prod_id = normalizer.get_or_create_product(
                        producto["nombre"], fuente_id
                    )
                    variante_id = db.get_or_create_variante(
                        prod_id, fuente_id,
                        producto["nombre"],
                        producto.get("url", "")
                    )
                    db.insertar_precio(variante_id, producto["precio"], hoy)
                    inserted += 1
                except Exception as e:
                    log.warning(f"Error processing '{producto.get('nombre')}': {e}")

            log.info(f"{source_name}: {inserted} prices saved for {hoy}")

        except Exception as e:
            log.error(f"Error scraping {source_name}: {e}", exc_info=True)

    log.info("Scraping complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hermes Price Tracker")
    parser.add_argument("--source", default="all",
                        choices=["all", "anonima", "dia", "encombo", "carrefour"])
    parser.add_argument("--dry-run", action="store_true",
                        help="Scrape without saving to DB")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of products per source")
    args = parser.parse_args()

    run(args.source, dry_run=args.dry_run, limit=args.limit)
