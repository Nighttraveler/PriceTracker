"""
Tests de integración para los scrapers — hacen requests HTTP reales.
Saltear en CI/offline: pytest -m "not integration"
"""
import pytest
from scrapers.anonima import AnonimaScraper
from scrapers.dia import DiaScraper
from scrapers.encombo import EncomboScraper
from scrapers.carrefour import CarrefourScraper


def _validar_productos(productos, fuente):
    assert len(productos) > 0, f"{fuente}: debe devolver al menos un producto"
    for p in productos:
        assert isinstance(p["nombre"], str) and p["nombre"].strip(), \
            f"{fuente}: nombre vacío en {p}"
        assert isinstance(p["precio"], float) and p["precio"] > 0, \
            f"{fuente}: precio inválido en {p}"
        assert isinstance(p["url"], str) and p["url"].startswith("http"), \
            f"{fuente}: URL inválida en {p}"


@pytest.mark.integration
class TestScrapersIntegration:

    def test_anonima(self):
        productos = AnonimaScraper().fetch_all(limit=5)
        _validar_productos(productos, "La Anónima")

    def test_dia(self):
        productos = DiaScraper().fetch_all(limit=5)
        _validar_productos(productos, "Día")

    def test_encombo(self):
        productos = EncomboScraper().fetch_all(limit=5)
        _validar_productos(productos, "Encombo")

    def test_carrefour(self):
        productos = CarrefourScraper().fetch_all(limit=5)
        _validar_productos(productos, "Carrefour")
