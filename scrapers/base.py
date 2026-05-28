#!/usr/bin/env python3
"""scrapers/base.py — Clase base para todos los scrapers."""

import time
import random
import requests
import re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Language": "es-AR,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xhtml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com.ar/",
}


class BaseScraper:
    url_base = ""
    delay_min = 1.5
    delay_max = 3.5

    def get(self, url: str) -> BeautifulSoup:
        time.sleep(random.uniform(self.delay_min, self.delay_max))
        with requests.Session() as s:
            s.headers.update(HEADERS)
            resp = s.get(url, timeout=15)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "lxml")

    def limpiar_precio(self, texto: str) -> float:
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
                    # Special Magento 5-digit decimal bug, e.g. 4.92401 -> 4924.01
                    texto = parts[0] + parts[1][:3] + '.' + parts[1][3:]
                
        return float(texto)

    def fetch_all(self, limit=None) -> list[dict]:
        raise NotImplementedError
