import pytest
from scrapers.base import BaseScraper

# Reusable instance (no HTTP requests — only tests the price parsing method)
scraper = BaseScraper()
parse_price = scraper.parse_price


class TestParsePrice:

    # Thousands separator as dot, no decimal
    def test_punto_miles_sin_decimal(self):
        assert parse_price("$ 1.432") == 1432.0

    # Dot as thousands separator + comma as decimal
    def test_punto_miles_coma_decimal(self):
        assert parse_price("$ 1.432,00") == 1432.0
        assert parse_price("$1.234,56") == 1234.56
        assert parse_price("$ 1.190,00") == 1190.0

    # Plain integer
    def test_entero_simple(self):
        assert parse_price("$ 840") == 840.0

    # Magento bug: 5 digits after the dot (thousands + decimal fused)
    def test_magento_5_digitos(self):
        assert parse_price("$\xa04.92401") == 4924.01
        assert parse_price("$\xa03.96039") == 3960.39
        assert parse_price("$\xa05.21956") == 5219.56

    # Comma as thousands separator (3 digits after comma)
    def test_coma_miles(self):
        assert parse_price("1,432") == 1432.0

    # Comma as decimal
    def test_coma_decimal(self):
        assert parse_price("150,50") == 150.5

    # Standard decimal dot
    def test_punto_decimal(self):
        assert parse_price("4280.00") == 4280.0

    # Currency symbols and spaces do not break parsing
    def test_ignora_simbolos_y_espacios(self):
        assert parse_price("$  1500") == 1500.0
        assert parse_price("ARS 999,99") == 999.99
