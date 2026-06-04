#!/usr/bin/env python3
"""scrapers/vtex_base.py — Base abstracta para scrapers VTEX Catalog API."""

import logging
import time
import random
import requests

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "es-AR,es;q=0.9",
}

PAGE_SIZE = 50
VTEX_MAX_OFFSET = 2500
MAX_RETRIES = 3
RETRY_BASE_WAIT = 5


class VTEXScraper:
    """Base para scrapers que usan la VTEX Catalog API.

    Subclases deben definir: url_base, name, page_delay, y _get_categories().
    """

    url_base: str
    name: str
    page_delay: tuple = (0.5, 1.5)

    def _get_categories(self) -> dict[int, str]:
        """Devuelve {cat_id: cat_slug} a scrapear."""
        raise NotImplementedError

    def _get_page(self, cat_id: int, from_: int) -> tuple[list, int]:
        url = (
            f"{self.url_base}/api/catalog_system/pub/products/search"
            f"?fq=C:{cat_id}&_from={from_}&_to={from_ + PAGE_SIZE - 1}"
        )
        for attempt in range(MAX_RETRIES):
            time.sleep(random.uniform(*self.page_delay))
            resp = requests.get(url, headers=HEADERS, timeout=15)

            if resp.status_code == 429:
                wait = RETRY_BASE_WAIT * (2 ** attempt)
                log.warning(
                    f"{self.name}: 429 en offset {from_}, reintentando en {wait}s"
                    f" (intento {attempt + 1}/{MAX_RETRIES})"
                )
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

        raise requests.exceptions.RetryError(
            f"{self.name}: 429 persistente después de {MAX_RETRIES} intentos en offset {from_}"
        )

    def fetch_all(self, limit: int = None) -> list[dict]:
        categories = self._get_categories()
        if not categories:
            log.error(f"{self.name}: sin categorías, abortando")
            return []

        productos = []
        for cat_id, cat_slug in categories.items():
            log.info(f"{self.name}: categoría {cat_slug} (id={cat_id})")
            from_ = 0
            total = None

            while from_ < VTEX_MAX_OFFSET:
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
                            vtex_items = item.get("items", [])
                            if not vtex_items:
                                continue

                            sellers = vtex_items[0].get("sellers", [])
                            if not sellers:
                                continue

                            offer = sellers[0].get("commertialOffer", {})
                            precio = offer.get("Price", 0)
                            # AvailableQuantity puede ser 0 para productos por peso;
                            # IsAvailable cubre esos casos correctamente.
                            available = (
                                offer.get("AvailableQuantity", 0) > 0
                                or offer.get("IsAvailable", False)
                            )
                            link = item.get("link", "")

                            if not nombre or not precio or not available:
                                continue

                            productos.append({
                                "nombre": nombre,
                                "precio": float(precio),
                                "url": link if link.startswith("http") else f"{self.url_base}{link}",
                            })
                        except Exception as e:
                            log.debug(f"{self.name}: error en item: {e}")

                        if limit and len(productos) >= limit:
                            return productos

                    from_ += PAGE_SIZE
                    if total and from_ >= total:
                        break

                except Exception as e:
                    log.warning(f"{self.name}: error en {cat_slug} offset {from_}: {e}")
                    break

        return productos
