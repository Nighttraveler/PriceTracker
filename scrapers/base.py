#!/usr/bin/env python3
"""scrapers/base.py — Base class for all scrapers."""

import time
import random
import re
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests

MAX_RETRIES = 3
RETRY_BASE_WAIT = 15

# Only Accept-Language is set manually: curl_cffi's impersonation supplies a
# User-Agent and sec-ch-ua headers consistent with the TLS fingerprint, and a
# manual UA that mismatches the fingerprint is itself a bot signal.
HEADERS = {
    "Accept-Language": "es-AR,es;q=0.9",
}


class ScraperBlockedError(Exception):
    """Raised on 403, or on persistent 429/5xx — the IP or session is blocked."""


class BaseScraper:
    url_base = ""
    delay_min = 1.5
    delay_max = 3.5

    def __init__(self):
        self.session = curl_requests.Session(impersonate="chrome")
        self.session.headers.update(HEADERS)

    def get(self, url: str) -> BeautifulSoup:
        time.sleep(random.uniform(self.delay_min, self.delay_max))
        for attempt in range(MAX_RETRIES):
            resp = self.session.get(url, timeout=15)

            if resp.status_code == 403:
                raise ScraperBlockedError(f"Blocked (403): {url}")

            if resp.status_code == 429 or resp.status_code >= 500:
                wait = RETRY_BASE_WAIT * (2 ** attempt)
                time.sleep(wait)
                continue

            resp.raise_for_status()
            return BeautifulSoup(resp.text, "lxml")

        # Sustained 429/5xx from a WAF-fronted site is a block, not noise.
        raise ScraperBlockedError(
            f"Blocked (persistent 429/5xx after {MAX_RETRIES} attempts): {url}"
        )

    def parse_price(self, texto: str) -> float:
        # Remove everything except digits, commas, and dots
        texto = re.sub(r'[^\d,.]', '', texto)

        # If both dot and comma are present, e.g. 1.234,56
        if ',' in texto and '.' in texto:
            if texto.rfind(',') > texto.rfind('.'):
                texto = texto.replace('.', '').replace(',', '.')
            else:
                texto = texto.replace(',', '')
        elif ',' in texto:
            parts = texto.split(',')
            if len(parts) == 2 and len(parts[1]) == 3:
                # Thousands separator, e.g. 1,432 -> 1432
                texto = texto.replace(',', '')
            else:
                # Decimal, e.g. 150,50 -> 150.50
                texto = texto.replace(',', '.')
        elif '.' in texto:
            parts = texto.split('.')
            if len(parts) == 2:
                if len(parts[1]) == 3:
                    # Thousands separator, e.g. 1.432 -> 1432
                    texto = texto.replace('.', '')
                elif len(parts[1]) > 3:
                    # Magento 5-digit decimal bug, e.g. 4.92401 -> 4924.01
                    texto = parts[0] + parts[1][:3] + '.' + parts[1][3:]

        return float(texto)

    def fetch_all(self, limit=None) -> list[dict]:
        raise NotImplementedError
