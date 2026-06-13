import sys
import pytest
from unittest.mock import patch, MagicMock
from requests import RequestException

sys.path.insert(0, ".")
from scripts.chequear_urls import check_url, DISCONTINUED_STATUSES


def _mock_resp(status):
    r = MagicMock()
    r.status_code = status
    return r


class TestCheckURL:
    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_200_ok(self, mock_head, mock_get):
        mock_head.return_value = _mock_resp(200)
        assert check_url("http://example.com/prod") == 200
        mock_get.assert_not_called()

    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_301_descatalogado(self, mock_head, mock_get):
        """301 is returned directly from HEAD (< 400, no GET fallback)."""
        mock_head.return_value = _mock_resp(301)
        assert check_url("http://example.com/prod") == 301
        mock_get.assert_not_called()

    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_404_fallback_get(self, mock_head, mock_get):
        """HEAD with 404 (>=400) triggers GET fallback; GET confirms 404."""
        mock_head.return_value = _mock_resp(404)
        mock_get.return_value = _mock_resp(404)
        assert check_url("http://example.com/prod") == 404

    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_410_fallback_get(self, mock_head, mock_get):
        """HEAD with 410 (>=400) triggers GET fallback; GET confirms 410."""
        mock_head.return_value = _mock_resp(410)
        mock_get.return_value = _mock_resp(410)
        assert check_url("http://example.com/prod") == 410

    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_head_403_fallback_get_200(self, mock_head, mock_get):
        """WAF blocks HEAD with 403; GET fallback returns 200 → product active."""
        mock_head.return_value = _mock_resp(403)
        mock_get.return_value = _mock_resp(200)
        assert check_url("http://example.com/prod") == 200

    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_head_405_fallback_get_404(self, mock_head, mock_get):
        """WAF blocks HEAD with 405; GET fallback confirms 404 → discontinued."""
        mock_head.return_value = _mock_resp(405)
        mock_get.return_value = _mock_resp(404)
        assert check_url("http://example.com/prod") == 404

    @patch("scripts.chequear_urls.requests.get")
    @patch("scripts.chequear_urls.requests.head")
    def test_error_de_red(self, mock_head, mock_get):
        """Network error → returns 0 (not marked as discontinued)."""
        mock_head.side_effect = RequestException("timeout")
        assert check_url("http://example.com/prod") == 0


class TestDiscontinuedStatuses:
    def test_301_in_set(self):
        assert 301 in DISCONTINUED_STATUSES

    def test_404_y_410_in_set(self):
        assert {404, 410}.issubset(DISCONTINUED_STATUSES)


@pytest.mark.integration
class TestCheckURLIntegration:
    def test_url_anonima_real(self):
        """HEAD returns 403 (WAF) → GET fallback → verifies a valid status is returned.

        The URL responds 200 (active product per ld+json InStock).
        The redirect to home shown in Firefox is client-side JS, not HTTP.
        """
        url = "https://www.laanonima.com.ar/agua-eco-de-los-andes-sin-gas-botella-1-5lt-x1/art_0220346/"
        status = check_url(url)
        assert status != 0, "Network error: could not connect to laanonima.com.ar"
        assert status in {200, 301, 404, 410}, f"Unexpected status: {status}"
