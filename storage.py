"""Storage Engine for WeatherWise.

Demonstrates official Week 3 file handling requirements:
- `.txt` files: Formatted human-readable weather reports.
- `.csv` files: Tabular search history logging with headers.
- `.json` files: Persistent favorites list and cached weather responses.
Includes safe file reading, error recovery, and directory management via `os`.
"""

import csv
import json
import os
from utils import get_data_dir, get_current_timestamp, celsius_to_fahrenheit, celsius_to_kelvin


class StorageEngine:
    """Manages file storage and data persistence for WeatherWise."""

    def __init__(self, data_directory: str = None):
        self.data_dir = data_directory or get_data_dir()
        self.history_csv_path = os.path.join(self.data_dir, "search_history.csv")
        self.favorites_json_path = os.path.join(self.data_dir, "favorites.json")
        self.cache_json_path = os.path.join(self.data_dir, "weather_cache.json")
        self.latest_report_txt_path = os.path.join(self.data_dir, "weather_report.txt")
        self.settings_json_path = os.path.join(self.data_dir, "settings.json")

    # =========================================================
    # TXT File Handling
    # =========================================================
    def save_text_report(self, weather: dict, filepath: str = None) -> str:
        """Generate and save a structured, readable plain-text weather report.
        
        Demonstrates Week 3: Text file writing.
        """
        target_path = filepath or self.latest_report_txt_path
        celsius = weather.get("temperature_c", 0.0)
        fahrenheit = celsius_to_fahrenheit(celsius)
        kelvin = celsius_to_kelvin(celsius)

        report_content = f"""======================================================================
                     WEATHERWISE INTELLIGENCE REPORT
======================================================================
Generated On  : {get_current_timestamp()}
Target City   : {weather.get('city', 'Unknown')}, {weather.get('country', '')}
Coordinates   : Lat {weather.get('latitude', 'N/A')}, Lon {weather.get('longitude', 'N/A')}
Data Source   : {weather.get('source', 'API Provider')}
----------------------------------------------------------------------
CURRENT ATMOSPHERIC CONDITIONS
----------------------------------------------------------------------
Condition     : {weather.get('condition', 'N/A')}
Temperature   : {celsius} °C  |  {fahrenheit} °F  |  {kelvin} K
Feels Like    : {weather.get('feels_like_c', 'N/A')} °C
Day Range     : High {weather.get('temp_max_c', 'N/A')} °C / Low {weather.get('temp_min_c', 'N/A')} °C
Relative Hum. : {weather.get('humidity', 'N/A')} %
Wind Velocity : {weather.get('wind_speed_kmh', 'N/A')} km/h
Pressure      : {weather.get('pressure_hpa', 'N/A')} hPa
Sunrise Time  : {weather.get('sunrise', 'N/A')}
Sunset Time   : {weather.get('sunset', 'N/A')}
======================================================================
              Report stored by WeatherWise File Storage Engine
======================================================================
"""
        try:
            with open(target_path, "w", encoding="utf-8") as file:
                file.write(report_content)
            return target_path
        except OSError as error:
            print(f"Error saving text report: {error}")
            return ""

    def read_text_report(self, filepath: str = None) -> str:
        """Read and return content of the saved text report.
        
        Demonstrates Week 3: Text file reading.
        """
        target_path = filepath or self.latest_report_txt_path
        if not os.path.exists(target_path):
            return "No text report has been generated yet."

        try:
            with open(target_path, "r", encoding="utf-8") as file:
                return file.read()
        except OSError as error:
            return f"Error reading text report: {error}"

    # =========================================================
    # CSV File Handling
    # =========================================================
    def log_search_to_csv(self, weather: dict) -> bool:
        """Append a search entry to search_history.csv with standardized column headers.
        
        Demonstrates Week 3: CSV file writing.
        """
        file_exists = os.path.exists(self.history_csv_path)
        headers = [
            "Timestamp", "City", "Country", "Temperature_C",
            "Temperature_F", "Humidity", "Wind_Speed_KMH", "Condition"
        ]

        celsius = weather.get("temperature_c", 0.0)
        row = [
            get_current_timestamp(),
            weather.get("city", "Unknown"),
            weather.get("country", ""),
            celsius,
            celsius_to_fahrenheit(celsius),
            weather.get("humidity", 0),
            weather.get("wind_speed_kmh", 0.0),
            weather.get("condition", "Unknown")
        ]

        try:
            with open(self.history_csv_path, "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(headers)
                writer.writerow(row)
            return True
        except OSError as error:
            print(f"Error writing to search history CSV: {error}")
            return False

    def get_search_history_csv(self, limit: int = 15) -> list[dict]:
        """Read search history rows from search_history.csv.
        
        Demonstrates Week 3: CSV file reading.
        """
        if not os.path.exists(self.history_csv_path):
            return []

        records = []
        try:
            with open(self.history_csv_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    records.append(row)
            # Return most recent records first
            return list(reversed(records))[:limit]
        except (OSError, csv.Error) as error:
            print(f"Error reading search history CSV: {error}")
            return []

    # =========================================================
    # JSON File Handling (Favorites & Cache)
    # =========================================================
    def get_favorites(self) -> list[dict]:
        """Retrieve the list of saved favorite cities from favorites.json.
        
        Demonstrates Week 3: JSON file reading.
        """
        if not os.path.exists(self.favorites_json_path):
            return []

        # Guard against empty file (0 bytes)
        if os.path.getsize(self.favorites_json_path) == 0:
            return []

        try:
            with open(self.favorites_json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, list):
                    # Filter only valid dictionary records with a city field
                    return [item for item in data if isinstance(item, dict) and "city" in item]
                return []
        except (json.JSONDecodeError, OSError) as error:
            print(f"[Warning] Could not load favorites JSON ({error}). Starting with empty list.")
            return []

    def add_favorite(self, city_name: str, country: str = "") -> bool:
        """Add a city to favorites, avoiding duplicates.
        
        Demonstrates Week 3: JSON file writing.
        """
        clean_city = city_name.strip()
        if not clean_city:
            return False

        favorites = self.get_favorites()
        
        # Check if already in favorites (case-insensitive)
        for fav in favorites:
            if isinstance(fav, dict) and fav.get("city", "").lower() == clean_city.lower():
                return False  # Already present

        favorites.append({
            "city": clean_city,
            "country": country.strip(),
            "added_at": get_current_timestamp()
        })

        try:
            with open(self.favorites_json_path, "w", encoding="utf-8") as file:
                json.dump(favorites, file, indent=4)
            return True
        except OSError as error:
            print(f"Error saving favorites JSON: {error}")
            return False

    def remove_favorite(self, city_name: str) -> bool:
        """Remove a city from favorites.json."""
        clean_city = city_name.strip().lower()
        if not clean_city:
            return False

        favorites = self.get_favorites()
        new_favorites = [
            f for f in favorites 
            if isinstance(f, dict) and f.get("city", "").lower() != clean_city
        ]

        if len(new_favorites) == len(favorites):
            return False  # Not found

        try:
            with open(self.favorites_json_path, "w", encoding="utf-8") as file:
                json.dump(new_favorites, file, indent=4)
            return True
        except OSError as error:
            print(f"Error updating favorites JSON: {error}")
            return False

    def cache_weather_snapshot(self, weather: dict) -> bool:
        """Cache a weather response to weather_cache.json for offline fallback/history."""
        city = weather.get("city", "Unknown")
        cache = {}
        if os.path.exists(self.cache_json_path):
            try:
                with open(self.cache_json_path, "r", encoding="utf-8") as file:
                    cache = json.load(file)
                    if not isinstance(cache, dict):
                        cache = {}
            except (json.JSONDecodeError, OSError):
                cache = {}

        cache[city] = {
            "cached_at": get_current_timestamp(),
            "data": weather
        }

        try:
            with open(self.cache_json_path, "w", encoding="utf-8") as file:
                json.dump(cache, file, indent=4)
            return True
        except OSError as error:
            print(f"Error updating weather cache: {error}")
            return False

    def get_cached_weather(self, city_name: str) -> dict:
        """Retrieve cached weather response for a city if available."""
        if not os.path.exists(self.cache_json_path):
            return None

        try:
            with open(self.cache_json_path, "r", encoding="utf-8") as file:
                cache = json.load(file)
                for stored_city, entry in cache.items():
                    if stored_city.lower() == city_name.strip().lower():
                        return entry.get("data")
        except (json.JSONDecodeError, OSError):
            return None
        return None

    # =========================================================
    # Settings & Stats Persistence
    # =========================================================
    def get_settings(self) -> dict:
        """Retrieve user configuration preferences from settings.json."""
        default_settings = {
            "unit": "C",
            "default_city": "Bengaluru",
            "theme": "Deep Twilight",
            "refresh_interval_min": 15,
            "auto_refresh": True,
        }

        if not os.path.exists(self.settings_json_path):
            return default_settings

        try:
            with open(self.settings_json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, dict):
                    # Merge with defaults for any missing keys
                    default_settings.update(data)
                    return default_settings
        except (json.JSONDecodeError, OSError) as error:
            print(f"[Warning] Could not load settings JSON ({error}). Using defaults.")

        return default_settings

    def save_settings(self, settings: dict) -> bool:
        """Persist user configuration preferences to settings.json."""
        current = self.get_settings()
        current.update(settings)
        try:
            with open(self.settings_json_path, "w", encoding="utf-8") as file:
                json.dump(current, file, indent=4)
            return True
        except OSError as error:
            print(f"Error saving settings JSON: {error}")
            return False

    def clear_search_history(self) -> bool:
        """Clear all search history entries in search_history.csv."""
        headers = [
            "Timestamp", "City", "Country", "Temperature_C",
            "Temperature_F", "Humidity", "Wind_Speed_KMH", "Condition"
        ]
        try:
            with open(self.history_csv_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(headers)
            return True
        except OSError as error:
            print(f"Error clearing search history CSV: {error}")
            return False

    def get_stats(self) -> dict:
        """Compute quick summary statistics of stored data."""
        favs = self.get_favorites()
        history = self.get_search_history_csv(limit=1000)
        cache_count = 0
        if os.path.exists(self.cache_json_path):
            try:
                with open(self.cache_json_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    if isinstance(data, dict):
                        cache_count = len(data)
            except Exception:
                cache_count = 0

        return {
            "favorites_count": len(favs),
            "history_count": len(history),
            "cache_count": cache_count,
            "has_report": os.path.exists(self.latest_report_txt_path),
        }

