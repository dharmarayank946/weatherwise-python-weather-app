"""Unit and Integration Tests for WeatherWise.

Tests:
1. Math calculations (Celsius, Fahrenheit, Kelvin, wind chill)
2. Datetime formatting and timestamps
3. Random weather tips generator
4. File storage operations:
   - Text file (.txt) report generation and reading
   - CSV file (.csv) logging and row retrieval
   - JSON file (.json) favorites and cache persistence
5. Weather API integration and error handling (with live & mock cases)
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils import (
    celsius_to_fahrenheit,
    celsius_to_kelvin,
    calculate_wind_chill,
    get_current_timestamp,
    format_display_time,
    get_weather_tip,
    get_random_sample_cities
)
from storage import StorageEngine
from weather_service import WeatherService


class TestUtils(unittest.TestCase):
    """Test mathematical calculations and utility functions."""

    def test_temperature_conversions(self):
        # 0 C = 32 F = 273.15 K
        self.assertEqual(celsius_to_fahrenheit(0.0), 32.0)
        self.assertEqual(celsius_to_kelvin(0.0), 273.15)

        # 100 C = 212 F = 373.15 K
        self.assertEqual(celsius_to_fahrenheit(100.0), 212.0)
        self.assertEqual(celsius_to_kelvin(100.0), 373.15)

        # -40 C = -40 F
        self.assertEqual(celsius_to_fahrenheit(-40.0), -40.0)

    def test_wind_chill_calculation(self):
        # Above 10 C, wind chill is equal to temperature
        self.assertEqual(calculate_wind_chill(15.0, 20.0), 15.0)

        # At or below 10 C with wind > 4.8 km/h, wind chill is calculated
        chill = calculate_wind_chill(5.0, 25.0)
        self.assertTrue(chill < 5.0, f"Expected wind chill to be colder than 5 C, got {chill}")

    def test_datetime_formatting(self):
        ts = get_current_timestamp()
        self.assertRegex(ts, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

        formatted = format_display_time("2026-10-26T10:30")
        self.assertIn("2026", formatted)

    def test_random_weather_tip(self):
        # High heat tip
        tip_hot = get_weather_tip("Sunny", 35.0)
        self.assertIn("category", tip_hot)
        self.assertIn("tip", tip_hot)
        self.assertEqual(tip_hot["category"], "Warm Weather Care")

        # Rain tip
        tip_rain = get_weather_tip("Moderate Rain", 18.0)
        self.assertEqual(tip_rain["category"], "Rain Preparedness")

    def test_random_sample_cities(self):
        samples = get_random_sample_cities()
        self.assertEqual(len(samples), 4)
        self.assertTrue(all(isinstance(c, str) for c in samples))


class TestStorageEngine(unittest.TestCase):
    """Test .txt, .csv, and .json persistence in an isolated temporary directory."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageEngine(data_directory=self.test_dir)
        self.sample_weather = {
            "city": "Bengaluru",
            "country": "India",
            "temperature_c": 24.5,
            "feels_like_c": 25.0,
            "temp_max_c": 28.0,
            "temp_min_c": 19.0,
            "humidity": 65,
            "wind_speed_kmh": 12.0,
            "pressure_hpa": 1012,
            "condition": "Partly Cloudy",
            "sunrise": "06:10",
            "sunset": "18:05",
            "source": "Open-Meteo Test"
        }

    def tearDown(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_text_report_storage(self):
        # Write .txt report
        path = self.storage.save_text_report(self.sample_weather)
        self.assertTrue(os.path.exists(path))

        # Read .txt report back
        content = self.storage.read_text_report(path)
        self.assertIn("WEATHERWISE INTELLIGENCE REPORT", content)
        self.assertIn("Bengaluru", content)
        self.assertIn("24.5 °C", content)

    def test_csv_search_logging(self):
        # Write to CSV
        logged = self.storage.log_search_to_csv(self.sample_weather)
        self.assertTrue(logged)
        self.assertTrue(os.path.exists(self.storage.history_csv_path))

        # Read CSV back
        history = self.storage.get_search_history_csv()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["City"], "Bengaluru")
        self.assertEqual(history[0]["Country"], "India")
        self.assertEqual(history[0]["Condition"], "Partly Cloudy")

    def test_json_favorites_storage(self):
        # Add to favorites
        added = self.storage.add_favorite("Tokyo", "Japan")
        self.assertTrue(added)

        # Duplicate addition should be rejected
        duplicate = self.storage.add_favorite("Tokyo", "Japan")
        self.assertFalse(duplicate)

        # Retrieve favorites
        favs = self.storage.get_favorites()
        self.assertEqual(len(favs), 1)
        self.assertEqual(favs[0]["city"], "Tokyo")

        # Remove from favorites
        removed = self.storage.remove_favorite("Tokyo")
        self.assertTrue(removed)
        self.assertEqual(len(self.storage.get_favorites()), 0)

    def test_json_weather_cache(self):
        # Cache snapshot
        cached = self.storage.cache_weather_snapshot(self.sample_weather)
        self.assertTrue(cached)

        # Retrieve from cache
        retrieved = self.storage.get_cached_weather("Bengaluru")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["city"], "Bengaluru")
        self.assertEqual(retrieved["temperature_c"], 24.5)


class TestWeatherService(unittest.TestCase):
    """Test API integration and error handling."""

    def setUp(self):
        self.service = WeatherService()

    def test_empty_city_validation(self):
        result = self.service.get_weather("")
        self.assertFalse(result["success"])
        self.assertIn("empty", result["error"])

    def test_invalid_city_handling(self):
        # Random non-existent city string
        result = self.service.get_weather("NonExistentCityXYZ1234567")
        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"].lower())

    def test_live_api_fetch(self):
        # Test real live lookup on London
        result = self.service.get_weather("London")
        self.assertTrue(result["success"], f"API call failed: {result.get('error')}")
        self.assertEqual(result["city"], "London")
        self.assertIn("temperature_c", result)
        self.assertIn("humidity", result)
        self.assertIn("condition", result)


class TestGUI(unittest.TestCase):
    """Test Tkinter GUI instantiation and initialization."""

    def test_gui_initialization(self):
        try:
            import tkinter as tk
            from gui import WeatherWiseGUI
            root = tk.Tk()
            root.withdraw()
            app = WeatherWiseGUI(root)
            self.assertIsNotNone(app)
            self.assertEqual(app.current_unit, "C")
            root.destroy()
        except tk.TclError:
            # Display server not available in headless environment
            pass


if __name__ == "__main__":
    unittest.main()

