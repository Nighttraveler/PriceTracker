import pytest
from unittest.mock import MagicMock, patch
from scrapers.anonima import AnonimaScraper
from scrapers.encombo import EncomboScraper

class TestScraperFiltering:

    def test_anonima_filters_unavailable_and_zero_price(self):
        scraper = AnonimaScraper()
        with patch.object(scraper, 'get') as mock_get:
            mock_soup = MagicMock()
            item1 = MagicMock()
            item1.find.return_value = {'data-nombre': 'Produc A', 'data-precio': '100', 'data-stock': '1', 'href': '/a'}
            item2 = MagicMock()
            item2.find.return_value = {'data-nombre': 'Produc B', 'data-precio': '200', 'data-stock': '0', 'href': '/b'}
            item3 = MagicMock()
            item3.find.return_value = {'data-nombre': 'Produc C', 'data-precio': '0', 'data-stock': '1', 'href': '/c'}
            
            mock_soup.select.return_value = [item1, item2, item3]
            mock_get.return_value = mock_soup
            
            with patch('scrapers.anonima.CATEGORIAS_URL', ['test/']):
                productos = scraper.fetch_all()
        
        assert len(productos) == 1
        assert productos[0]['nombre'] == 'Produc A'

    def test_encombo_filters_zero_price(self):
        scraper = EncomboScraper()
        with patch.object(scraper, 'get') as mock_get:
            mock_soup = MagicMock()
            
            # Helper for item side effects
            def create_item(name, price):
                item = MagicMock()
                item.select_one.side_effect = [
                    MagicMock(get_text=lambda strip: name),
                    MagicMock(get_text=lambda strip: price),
                    {'href': '/a'}
                ]
                return item

            item1 = create_item('Produc A', '$100')
            item2 = create_item('Produc B', '$0')
            
            mock_soup.select.return_value = [item1, item2]
            mock_soup.select_one.return_value = None
            mock_get.return_value = mock_soup
            
            with patch('scrapers.encombo.CATEGORIAS_URL', ['test.html']):
                productos = scraper.fetch_all()
        
        assert len(productos) == 1
        assert productos[0]['nombre'] == 'Produc A'
