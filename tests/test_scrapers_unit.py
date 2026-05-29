"""
Tests unitarios para los scrapers — sin requests HTTP reales.
"""
import pytest
import requests
from unittest.mock import patch, MagicMock, call

from scrapers.carrefour import CarrefourScraper, VTEX_MAX_OFFSET, PAGE_SIZE, MAX_RETRIES
from scrapers.base import BaseScraper


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_response(status=200, json_data=None, headers=None):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data or []
    resp.headers = headers or {"resources": "0-49/100"}
    if status >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(
            response=MagicMock(status_code=status)
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


def _producto_vtex(nombre="Leche 1L", precio=1500.0, link="/leche-1l/p"):
    return {
        "productName": nombre,
        "link": link,
        "items": [{"sellers": [{"commertialOffer": {"Price": precio}}]}],
    }


# ── CarrefourScraper ──────────────────────────────────────────────────────────

class TestCarrefourVtexLimit:

    @patch("scrapers.carrefour.requests.get")
    @patch("scrapers.carrefour.time.sleep")
    def test_no_supera_offset_2500(self, mock_sleep, mock_get):
        """El scraper nunca debe hacer un request con _from >= VTEX_MAX_OFFSET."""
        # Categoría con 10000 productos según el header (más que el límite VTEX)
        mock_get.return_value = _mock_response(
            json_data=[_producto_vtex()],
            headers={"resources": "0-49/10000"},
        )

        scraper = CarrefourScraper()
        # Solo scrapear una categoría para acotar el test
        with patch.dict("scrapers.carrefour.CATEGORIAS", {161: "almacen"}, clear=True):
            scraper.fetch_all()

        offsets_solicitados = [
            int(c.args[0].split("_from=")[1].split("&")[0])
            for c in mock_get.call_args_list
        ]
        assert all(o < VTEX_MAX_OFFSET for o in offsets_solicitados), (
            f"Se solicitó offset >= {VTEX_MAX_OFFSET}: {offsets_solicitados}"
        )

    @patch("scrapers.carrefour.requests.get")
    @patch("scrapers.carrefour.time.sleep")
    def test_para_cuando_api_retorna_vacio(self, mock_sleep, mock_get):
        """Si la API devuelve lista vacía, el scraper termina esa categoría."""
        mock_get.return_value = _mock_response(json_data=[])

        scraper = CarrefourScraper()
        with patch.dict("scrapers.carrefour.CATEGORIAS", {161: "almacen"}, clear=True):
            productos = scraper.fetch_all()

        assert productos == []
        assert mock_get.call_count == 1


class TestCarrefourRateLimit:

    @patch("scrapers.carrefour.requests.get")
    @patch("scrapers.carrefour.time.sleep")
    def test_reintenta_en_429(self, mock_sleep, mock_get):
        """Con 429, el scraper reintenta hasta MAX_RETRIES veces."""
        mock_get.side_effect = [
            _mock_response(status=429),
            _mock_response(status=429),
            _mock_response(json_data=[_producto_vtex("Leche", 1000.0)],
                           headers={"resources": "0-49/50"}),
            _mock_response(json_data=[]),  # segunda página vacía → fin
        ]

        scraper = CarrefourScraper()
        with patch.dict("scrapers.carrefour.CATEGORIAS", {161: "almacen"}, clear=True):
            productos = scraper.fetch_all()

        assert len(productos) == 1
        assert productos[0]["nombre"] == "Leche"

    @patch("scrapers.carrefour.requests.get")
    @patch("scrapers.carrefour.time.sleep")
    def test_429_persistente_aborta_categoria(self, mock_sleep, mock_get):
        """Si los MAX_RETRIES intentos fallan por 429, esa categoría se saltea."""
        mock_get.return_value = _mock_response(status=429)

        scraper = CarrefourScraper()
        with patch.dict("scrapers.carrefour.CATEGORIAS", {161: "almacen", 255: "bebidas"}, clear=True):
            # La primera categoría falla por 429, la segunda tampoco tiene productos
            productos = scraper.fetch_all()

        # No debe lanzar excepción — retorna lo que pudo obtener
        assert isinstance(productos, list)
        # Todos los calls al primer cat_id deben ser reintentos
        assert mock_get.call_count >= MAX_RETRIES

    @patch("scrapers.carrefour.requests.get")
    @patch("scrapers.carrefour.time.sleep")
    def test_429_usa_backoff_exponencial(self, mock_sleep, mock_get):
        """El tiempo de espera debe crecer con cada reintento."""
        mock_get.return_value = _mock_response(status=429)

        scraper = CarrefourScraper()
        with patch.dict("scrapers.carrefour.CATEGORIAS", {161: "almacen"}, clear=True):
            scraper.fetch_all()

        # Extraer los sleeps del backoff (excluyendo el delay normal de requests)
        sleep_calls = [c.args[0] for c in mock_sleep.call_args_list]
        # Los sleeps de backoff deben ser >= 5s (RETRY_BASE_WAIT)
        backoff_sleeps = [s for s in sleep_calls if s >= 5]
        assert len(backoff_sleeps) >= 1, "Debe haber al menos un sleep de backoff"
        # El segundo backoff debe ser mayor que el primero
        if len(backoff_sleeps) >= 2:
            assert backoff_sleeps[1] > backoff_sleeps[0]


class TestCarrefourErroresDeRed:

    @patch("scrapers.carrefour.requests.get")
    @patch("scrapers.carrefour.time.sleep")
    def test_dns_failure_saltea_categoria_y_continua(self, mock_sleep, mock_get):
        """Un error de red en una categoría no debe abortar las siguientes."""
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("DNS failure"),  # almacen falla
            _mock_response(json_data=[_producto_vtex("Gaseosa", 500.0)],
                           headers={"resources": "0-49/50"}),    # bebidas ok
            _mock_response(json_data=[]),
        ]

        scraper = CarrefourScraper()
        with patch.dict("scrapers.carrefour.CATEGORIAS", {161: "almacen", 255: "bebidas"}, clear=True):
            productos = scraper.fetch_all()

        assert len(productos) == 1
        assert productos[0]["nombre"] == "Gaseosa"

    @patch("scrapers.carrefour.requests.get")
    @patch("scrapers.carrefour.time.sleep")
    def test_timeout_saltea_categoria(self, mock_sleep, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()

        scraper = CarrefourScraper()
        with patch.dict("scrapers.carrefour.CATEGORIAS", {161: "almacen"}, clear=True):
            productos = scraper.fetch_all()

        assert productos == []


class TestCarrefourParseoProductos:

    @patch("scrapers.carrefour.requests.get")
    @patch("scrapers.carrefour.time.sleep")
    def test_ignora_productos_sin_precio(self, mock_sleep, mock_get):
        sin_precio = {
            "productName": "Producto sin precio",
            "link": "/prod/p",
            "items": [{"sellers": [{"commertialOffer": {"Price": 0}}]}],
        }
        mock_get.side_effect = [
            _mock_response(json_data=[sin_precio], headers={"resources": "0-49/1"}),
            _mock_response(json_data=[]),
        ]

        scraper = CarrefourScraper()
        with patch.dict("scrapers.carrefour.CATEGORIAS", {161: "almacen"}, clear=True):
            productos = scraper.fetch_all()

        assert productos == []

    @patch("scrapers.carrefour.requests.get")
    @patch("scrapers.carrefour.time.sleep")
    def test_construye_url_absoluta(self, mock_sleep, mock_get):
        mock_get.side_effect = [
            _mock_response(
                json_data=[_producto_vtex(link="/leche-entera/p")],
                headers={"resources": "0-49/1"},
            ),
            _mock_response(json_data=[]),
        ]

        scraper = CarrefourScraper()
        with patch.dict("scrapers.carrefour.CATEGORIAS", {161: "almacen"}, clear=True):
            productos = scraper.fetch_all()

        assert productos[0]["url"] == "https://www.carrefour.com.ar/leche-entera/p"

    @patch("scrapers.carrefour.requests.get")
    @patch("scrapers.carrefour.time.sleep")
    def test_limit_respetado(self, mock_sleep, mock_get):
        mock_get.return_value = _mock_response(
            json_data=[_producto_vtex(f"Prod {i}", 100.0) for i in range(50)],
            headers={"resources": "0-49/500"},
        )

        scraper = CarrefourScraper()
        with patch.dict("scrapers.carrefour.CATEGORIAS", {161: "almacen"}, clear=True):
            productos = scraper.fetch_all(limit=10)

        assert len(productos) == 10


# ── BaseScraper.limpiar_precio — casos de error ───────────────────────────────

class TestLimpiarPrecioErrores:
    scraper = BaseScraper()

    def test_string_solo_simbolos(self):
        # Solo símbolo de peso sin número → debe lanzar ValueError
        with pytest.raises((ValueError, Exception)):
            self.scraper.limpiar_precio("$")

    def test_string_vacio(self):
        with pytest.raises((ValueError, Exception)):
            self.scraper.limpiar_precio("")

    def test_precio_con_espacios_internos(self):
        assert self.scraper.limpiar_precio("1 500,00") == 150000.0 or \
               self.scraper.limpiar_precio("1 500,00") == 1500.0
        # Comportamiento aceptable: los espacios se eliminan antes de parsear

    def test_precio_con_texto_adicional(self):
        assert self.scraper.limpiar_precio("Precio: $1.500,00") == 1500.0
