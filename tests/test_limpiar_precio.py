import pytest
from scrapers.base import BaseScraper

# Instancia reutilizable (no hace requests, solo usa el método de parsing)
scraper = BaseScraper()
limpiar = scraper.limpiar_precio


class TestLimpiarPrecio:

    # Separador de miles con punto, sin decimales
    def test_punto_miles_sin_decimal(self):
        assert limpiar("$ 1.432") == 1432.0

    # Punto como miles + coma como decimal
    def test_punto_miles_coma_decimal(self):
        assert limpiar("$ 1.432,00") == 1432.0
        assert limpiar("$1.234,56") == 1234.56
        assert limpiar("$ 1.190,00") == 1190.0

    # Número entero simple
    def test_entero_simple(self):
        assert limpiar("$ 840") == 840.0

    # Bug Magento: 5 dígitos después del punto (miles + decimal fusionados)
    def test_magento_5_digitos(self):
        assert limpiar("$\xa04.92401") == 4924.01
        assert limpiar("$\xa03.96039") == 3960.39
        assert limpiar("$\xa05.21956") == 5219.56

    # Coma como separador de miles (3 dígitos después de la coma)
    def test_coma_miles(self):
        assert limpiar("1,432") == 1432.0

    # Coma como decimal
    def test_coma_decimal(self):
        assert limpiar("150,50") == 150.5

    # Punto como decimal estándar
    def test_punto_decimal(self):
        assert limpiar("4280.00") == 4280.0

    # Símbolo de peso y espacios no rompen el parsing
    def test_ignora_simbolos_y_espacios(self):
        assert limpiar("$  1500") == 1500.0
        assert limpiar("ARS 999,99") == 999.99
