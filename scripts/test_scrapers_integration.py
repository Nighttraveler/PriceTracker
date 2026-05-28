import unittest
from scrapers.anonima import AnonimaScraper
from scrapers.dia import DiaScraper
from scrapers.encombo import EncomboScraper

class TestScrapersIntegration(unittest.TestCase):

    def test_encombo_scraper(self):
        """Test Encombo scraper gets items and valid prices."""
        scraper = EncomboScraper()
        # Fetch with a limit of 5 items
        products = scraper.fetch_all(limit=5)
        
        self.assertGreater(len(products), 0, "Encombo scraper should return at least one product.")
        print(f"\n[Test Encombo] Retrieved {len(products)} products.")
        
        for p in products:
            self.assertIn("nombre", p)
            self.assertIn("precio", p)
            self.assertIn("url", p)
            
            self.assertIsInstance(p["nombre"], str)
            self.assertNotEmptyString(p["nombre"])
            
            self.assertIsInstance(p["precio"], float)
            self.assertGreater(p["precio"], 0.0)
            
            self.assertIsInstance(p["url"], str)
            self.assertTrue(p["url"].startswith("http"))
            print(f"  - {p['nombre']}: ${p['precio']} ({p['url']})")

    def test_anonima_scraper(self):
        """Test La Anónima scraper gets items and valid prices."""
        scraper = AnonimaScraper()
        # Fetch with a limit of 5 items
        products = scraper.fetch_all(limit=5)
        
        self.assertGreater(len(products), 0, "La Anónima scraper should return at least one product.")
        print(f"\n[Test La Anónima] Retrieved {len(products)} products.")
        
        for p in products:
            self.assertIn("nombre", p)
            self.assertIn("precio", p)
            self.assertIn("url", p)
            
            self.assertIsInstance(p["nombre"], str)
            self.assertNotEmptyString(p["nombre"])
            
            self.assertIsInstance(p["precio"], float)
            self.assertGreater(p["precio"], 0.0)
            
            self.assertIsInstance(p["url"], str)
            self.assertTrue(p["url"].startswith("http"))
            print(f"  - {p['nombre']}: ${p['precio']} ({p['url']})")

    def test_dia_scraper(self):
        """Test Día scraper gets items and valid prices."""
        scraper = DiaScraper()
        # Fetch with a limit of 5 items
        products = scraper.fetch_all(limit=5)
        
        self.assertGreater(len(products), 0, "Día scraper should return at least one product.")
        print(f"\n[Test Día] Retrieved {len(products)} products.")
        
        for p in products:
            self.assertIn("nombre", p)
            self.assertIn("precio", p)
            self.assertIn("url", p)
            
            self.assertIsInstance(p["nombre"], str)
            self.assertNotEmptyString(p["nombre"])
            
            self.assertIsInstance(p["precio"], float)
            self.assertGreater(p["precio"], 0.0)
            
            self.assertIsInstance(p["url"], str)
            self.assertTrue(p["url"].startswith("http"))
            print(f"  - {p['nombre']}: ${p['precio']} ({p['url']})")

    def assertNotEmptyString(self, val):
        self.assertTrue(len(val.strip()) > 0, "String should not be empty")

if __name__ == "__main__":
    unittest.main()
