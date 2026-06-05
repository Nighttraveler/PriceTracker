import sys
import pytest
from unittest.mock import patch, MagicMock
from requests import RequestException

sys.path.insert(0, ".")
from scripts.chequear_urls import chequear_url, ESTADOS_DESCATALOGADO


def _mock_resp(status):
    r = MagicMock()
    r.status_code = status
    return r


class TestChequeURL:
    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_200_ok(self, mock_head, mock_get):
        mock_head.return_value = _mock_resp(200)
        assert chequear_url("http://example.com/prod") == 200
        mock_get.assert_not_called()

    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_301_descatalogado(self, mock_head, mock_get):
        """301 se retorna directo desde HEAD (< 400, no hay fallback GET)."""
        mock_head.return_value = _mock_resp(301)
        assert chequear_url("http://example.com/prod") == 301
        mock_get.assert_not_called()

    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_404_fallback_get(self, mock_head, mock_get):
        """HEAD con 404 (>=400) dispara GET; GET confirma 404."""
        mock_head.return_value = _mock_resp(404)
        mock_get.return_value = _mock_resp(404)
        assert chequear_url("http://example.com/prod") == 404

    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_410_fallback_get(self, mock_head, mock_get):
        """HEAD con 410 (>=400) dispara GET; GET confirma 410."""
        mock_head.return_value = _mock_resp(410)
        mock_get.return_value = _mock_resp(410)
        assert chequear_url("http://example.com/prod") == 410

    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_head_403_fallback_get_200(self, mock_head, mock_get):
        """WAF bloquea HEAD con 403; fallback GET devuelve 200 → producto activo."""
        mock_head.return_value = _mock_resp(403)
        mock_get.return_value = _mock_resp(200)
        assert chequear_url("http://example.com/prod") == 200

    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_head_405_fallback_get_404(self, mock_head, mock_get):
        """WAF bloquea HEAD con 405; fallback GET confirma 404 → descatalogado."""
        mock_head.return_value = _mock_resp(405)
        mock_get.return_value = _mock_resp(404)
        assert chequear_url("http://example.com/prod") == 404

    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_error_de_red(self, mock_head, mock_get):
        """Error de conexión → retorna 0 (no se marca como descatalogado)."""
        mock_head.side_effect = RequestException("timeout")
        assert chequear_url("http://example.com/prod") == 0


class TestEstadosDescatalogado:
    def test_301_en_set(self):
        assert 301 in ESTADOS_DESCATALOGADO

    def test_404_y_410_en_set(self):
        assert {404, 410}.issubset(ESTADOS_DESCATALOGADO)


@pytest.mark.integration
class TestChequeURLIntegration:
    def test_url_anonima_real(self):
        """HEAD devuelve 403 (WAF) → fallback GET → verifica que retorna status válido.

        La URL responde 200 (producto activo según ld+json InStock).
        El redirect al home que Firefox muestra es JS del lado cliente, no HTTP.
        """
        url = "https://www.laanonima.com.ar/agua-eco-de-los-andes-sin-gas-botella-1-5lt-x1/art_0220346/"
        status = chequear_url(url)
        assert status != 0, "Error de red: no se pudo conectar a laanonima.com.ar"
        assert status in {200, 301, 404, 410}, f"Status inesperado: {status}"
