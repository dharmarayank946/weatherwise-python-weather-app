"""Tests for WeatherWise Global Search, Geocoding, and Multi-Location Match Engine."""

import os
import sys
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from weather_service import WeatherService


class TestGlobalWeatherSearch(unittest.TestCase):

    def setUp(self):
        self.service = WeatherService()

    def test_search_kolkata(self):
        """Verify Kolkata resolves correctly to West Bengal, India."""
        data = self.service.get_weather("Kolkata")
        self.assertTrue(data.get("success"), f"Failed for Kolkata: {data.get('error')}")
        self.assertEqual(data.get("city"), "Kolkata")
        self.assertEqual(data.get("country"), "India")
        self.assertIn("West Bengal", data.get("region", ""))
        self.assertIn("temperature_c", data)
        self.assertIn("daily_forecast", data)
        self.assertGreater(len(data["daily_forecast"]), 0)

    def test_search_aland(self):
        """Verify Aland prioritizes Aland, Karnataka over Alandur prefix."""
        data = self.service.get_weather("Aland")
        self.assertTrue(data.get("success"), f"Failed for Aland: {data.get('error')}")
        self.assertEqual(data.get("city"), "Aland")
        self.assertEqual(data.get("region"), "Karnataka")
        self.assertEqual(data.get("country"), "India")

    def test_search_calcutta_alias(self):
        """Verify historic alias Calcutta resolves to Kolkata."""
        data = self.service.get_weather("Calcutta")
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("city"), "Kolkata")
        self.assertEqual(data.get("country"), "India")

    def test_search_comma_qualified(self):
        """Verify comma-separated city and state queries parse properly."""
        data = self.service.get_weather("Aland, Karnataka")
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("city"), "Aland")
        self.assertEqual(data.get("region"), "Karnataka")

    def test_search_locations_multi_match(self):
        """Verify search_locations returns multiple ranked candidates."""
        candidates = self.service.search_locations("London", count=5)
        self.assertGreaterEqual(len(candidates), 2)
        top = candidates[0]
        self.assertEqual(top["name"], "London")
        # Ensure display_name contains country
        self.assertIn("United Kingdom", top["display_name"])

    def test_all_16_target_locations(self):
        """Verify all 16 required global cities return successful forecasts."""
        required_cities = [
            "Kolkata", "Bengaluru", "Mumbai", "Delhi", "Chennai",
            "Hyderabad", "Pune", "Patna", "Aland", "London",
            "New York", "Tokyo", "Singapore", "Dubai", "Paris", "Sydney"
        ]
        for city in required_cities:
            with self.subTest(city=city):
                res = self.service.get_weather(city)
                self.assertTrue(res.get("success"), f"Failed on required city '{city}': {res.get('error')}")
                self.assertIsNotNone(res.get("temperature_c"))
                self.assertIsNotNone(res.get("humidity"))
                self.assertGreater(len(res.get("daily_forecast", [])), 0)


if __name__ == "__main__":
    unittest.main()
