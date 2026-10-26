"""Weather Service Module for WeatherWise.

Handles REST API integration using the `requests` library.
Supports:
1. Open-Meteo API (Free, zero-key, live geocoding + weather)
2. OpenWeatherMap API (Optional, requires API key via environment variable)
Includes robust error handling for timeouts, invalid cities, and network issues.
"""

import os
import requests

# Default timeout in seconds for API requests
REQUEST_TIMEOUT = 12


class WeatherService:
    """Service to fetch and process live weather data from open APIs."""

    def __init__(self, openweather_api_key: str = None):
        # Allow passing key directly or reading from environment
        self.openweather_api_key = openweather_api_key or os.environ.get("OPENWEATHER_API_KEY", "").strip()

    def get_weather(self, city_name: str) -> dict:
        """Fetch weather data for a given city name.
        
        Attempts OpenWeatherMap if an API key is configured; otherwise uses Open-Meteo.
        """
        clean_city = city_name.strip()
        if not clean_city:
            return {"success": False, "error": "City name cannot be empty."}

        # If OpenWeatherMap API key is provided and valid, try it first
        if self.openweather_api_key:
            result = self._fetch_openweather(clean_city)
            if result.get("success"):
                return result
            # If failed due to bad key or rate limit, fall back to Open-Meteo
            print(f"[Notice] OpenWeatherMap failed ({result.get('error')}). Falling back to Open-Meteo...")

        return self._fetch_open_meteo(clean_city)

    def _fetch_open_meteo(self, city_name: str) -> dict:
        """Fetch live weather data from Open-Meteo (No API key required)."""
        try:
            # Step 1: Geocoding lookup to resolve city name to latitude/longitude
            geo_url = "https://geocoding-api.open-meteo.com/v1/search"
            geo_params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
            
            geo_response = requests.get(geo_url, params=geo_params, timeout=REQUEST_TIMEOUT)
            
            if geo_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Geocoding service returned status code {geo_response.status_code}."
                }

            geo_data = geo_response.json()
            results = geo_data.get("results")
            if not results:
                return {
                    "success": False,
                    "error": f"City '{city_name}' not found. Please verify the spelling."
                }

            city_info = results[0]
            lat = city_info["latitude"]
            lon = city_info["longitude"]
            resolved_city = city_info.get("name", city_name)
            country = city_info.get("country", "")
            admin1 = city_info.get("admin1", "")

            # Step 2: Fetch current weather and daily forecast
            weather_url = "https://api.open-meteo.com/v1/forecast"
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure",
                "daily": "sunrise,sunset,temperature_2m_max,temperature_2m_min",
                "timezone": "auto",
            }

            weather_response = requests.get(weather_url, params=weather_params, timeout=REQUEST_TIMEOUT)
            
            if weather_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Weather API returned status code {weather_response.status_code}."
                }

            weather_data = weather_response.json()
            current = weather_data.get("current", {})
            daily = weather_data.get("daily", {})

            # Map WMO weather code to human description and visual category
            code = current.get("weather_code", 0)
            desc, icon_type = self._decode_wmo_code(code)

            temp_c = current.get("temperature_2m", 0.0)
            feels_like_c = current.get("apparent_temperature", temp_c)
            humidity = current.get("relative_humidity_2m", 0)
            wind_speed = current.get("wind_speed_10m", 0.0)
            pressure = current.get("surface_pressure", 1013)

            sunrises = daily.get("sunrise", [])
            sunsets = daily.get("sunset", [])
            sunrise = sunrises[0] if sunrises else "N/A"
            sunset = sunsets[0] if sunsets else "N/A"

            temp_max = daily.get("temperature_2m_max", [temp_c])[0]
            temp_min = daily.get("temperature_2m_min", [temp_c])[0]

            return {
                "success": True,
                "source": "Open-Meteo",
                "city": resolved_city,
                "country": country,
                "region": admin1,
                "latitude": lat,
                "longitude": lon,
                "temperature_c": round(temp_c, 1),
                "feels_like_c": round(feels_like_c, 1),
                "temp_max_c": round(temp_max, 1),
                "temp_min_c": round(temp_min, 1),
                "humidity": humidity,
                "wind_speed_kmh": round(wind_speed, 1),
                "pressure_hpa": round(pressure, 1),
                "condition": desc,
                "icon_type": icon_type,
                "weather_code": code,
                "sunrise": sunrise,
                "sunset": sunset,
                "timestamp": current.get("time", ""),
            }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out. Please check your internet connection."}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Unable to connect to the weather server. Network is unavailable."}
        except requests.exceptions.RequestException as exc:
            return {"success": False, "error": f"API request error: {str(exc)}"}
        except (KeyError, ValueError, IndexError) as parse_error:
            return {"success": False, "error": f"Failed to parse weather data: {str(parse_error)}"}

    def _fetch_openweather(self, city_name: str) -> dict:
        """Fetch weather data from OpenWeatherMap (requires API key)."""
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city_name, "appid": self.openweather_api_key, "units": "metric"}

        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 404:
                return {"success": False, "error": f"City '{city_name}' not found on OpenWeatherMap."}
            if response.status_code == 401:
                return {"success": False, "error": "Invalid OpenWeatherMap API key."}
            if response.status_code != 200:
                return {"success": False, "error": f"OpenWeatherMap returned code {response.status_code}."}

            data = response.json()
            main = data.get("main", {})
            weather_list = data.get("weather", [{}])
            weather_desc = weather_list[0].get("description", "Clear").title()
            weather_main = weather_list[0].get("main", "Clear").lower()
            wind = data.get("wind", {})
            sys = data.get("sys", {})

            # Map category to visual icon
            icon_map = {
                "clear": "sunny",
                "clouds": "cloudy",
                "rain": "rainy",
                "drizzle": "rainy",
                "thunderstorm": "stormy",
                "snow": "snowy",
                "mist": "foggy",
                "fog": "foggy",
                "haze": "foggy",
            }
            icon_type = icon_map.get(weather_main, "cloudy")

            temp_c = main.get("temp", 0.0)
            feels_like_c = main.get("feels_like", temp_c)

            return {
                "success": True,
                "source": "OpenWeatherMap",
                "city": data.get("name", city_name),
                "country": sys.get("country", ""),
                "region": "",
                "latitude": data.get("coord", {}).get("lat", 0.0),
                "longitude": data.get("coord", {}).get("lon", 0.0),
                "temperature_c": round(temp_c, 1),
                "feels_like_c": round(feels_like_c, 1),
                "temp_max_c": round(main.get("temp_max", temp_c), 1),
                "temp_min_c": round(main.get("temp_min", temp_c), 1),
                "humidity": main.get("humidity", 0),
                "wind_speed_kmh": round(wind.get("speed", 0.0) * 3.6, 1),
                "pressure_hpa": main.get("pressure", 1013),
                "condition": weather_desc,
                "icon_type": icon_type,
                "weather_code": data.get("id", 800),
                "sunrise": str(sys.get("sunrise", "N/A")),
                "sunset": str(sys.get("sunset", "N/A")),
                "timestamp": str(data.get("dt", "")),
            }

        except requests.exceptions.RequestException as exc:
            return {"success": False, "error": f"OpenWeatherMap request failed: {str(exc)}"}

    @staticmethod
    def _decode_wmo_code(code: int) -> tuple[str, str]:
        """Convert WMO Weather interpretation codes to readable description and icon category."""
        wmo_table = {
            0: ("Clear Sky", "sunny"),
            1: ("Mainly Clear", "sunny"),
            2: ("Partly Cloudy", "cloudy"),
            3: ("Overcast", "cloudy"),
            45: ("Foggy", "foggy"),
            48: ("Depositing Rime Fog", "foggy"),
            51: ("Light Drizzle", "rainy"),
            53: ("Moderate Drizzle", "rainy"),
            55: ("Dense Drizzle", "rainy"),
            61: ("Slight Rain", "rainy"),
            63: ("Moderate Rain", "rainy"),
            65: ("Heavy Rain", "rainy"),
            71: ("Slight Snow Fall", "snowy"),
            73: ("Moderate Snow Fall", "snowy"),
            75: ("Heavy Snow Fall", "snowy"),
            77: ("Snow Grains", "snowy"),
            80: ("Slight Rain Showers", "rainy"),
            81: ("Moderate Rain Showers", "rainy"),
            82: ("Violent Rain Showers", "stormy"),
            85: ("Slight Snow Showers", "snowy"),
            86: ("Heavy Snow Showers", "snowy"),
            95: ("Thunderstorm", "stormy"),
            96: ("Thunderstorm with Slight Hail", "stormy"),
            99: ("Thunderstorm with Heavy Hail", "stormy"),
        }
        return wmo_table.get(code, ("Variable Conditions", "cloudy"))
