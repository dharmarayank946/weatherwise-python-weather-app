"""Utilities Module for WeatherWise.

Demonstrates official Week 3 standard library requirements:
- `math`: Temperature unit conversions (Celsius, Fahrenheit, Kelvin) and calculations.
- `datetime`: Timestamp parsing, time formatting, and readable update dates.
- `random`: Dynamic, rotating weather insights and sample city suggestions.
- `os`: Path resolution, directory validation, and environment helpers.
"""

from datetime import datetime
import math
import os
import random


# -------------------------------------------------------------
# OS Module Utilities
# -------------------------------------------------------------
def get_base_dir() -> str:
    """Return the absolute base directory of the Weather App."""
    return os.path.dirname(os.path.abspath(__file__))


def get_data_dir() -> str:
    """Ensure and return the path to the data storage directory."""
    data_dir = os.path.join(get_base_dir(), "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_env_variable(var_name: str, default: str = "") -> str:
    """Retrieve an environment variable safely using os.environ."""
    return os.environ.get(var_name, default).strip()


# -------------------------------------------------------------
# Math Module Utilities
# -------------------------------------------------------------
def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit using math calculation.
    
    Formula: (C * 9/5) + 32
    """
    f = (float(celsius) * 9.0 / 5.0) + 32.0
    return round(f, 1)


def celsius_to_kelvin(celsius: float) -> float:
    """Convert Celsius to Kelvin using exact thermodynamic constant."""
    return round(float(celsius) + 273.15, 2)


def calculate_wind_chill(celsius: float, wind_kmh: float) -> float:
    """Calculate perceived wind chill temperature using math.pow.
    
    Formula is valid for temperatures <= 10 C and wind speeds > 4.8 km/h.
    """
    if celsius <= 10.0 and wind_kmh > 4.8:
        # Standard wind chill index formula
        wind_factor = math.pow(wind_kmh, 0.16)
        chill = 13.12 + (0.6215 * celsius) - (11.37 * wind_factor) + (0.3965 * celsius * wind_factor)
        return round(chill, 1)
    return round(celsius, 1)


# -------------------------------------------------------------
# Datetime Module Utilities
# -------------------------------------------------------------
def get_current_timestamp() -> str:
    """Return current date and time formatted for logs and reports."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def format_display_time(raw_time: str = None) -> str:
    """Format an ISO timestamp or current time into a human-readable string."""
    if not raw_time:
        return datetime.now().strftime("%A, %B %d, %Y | %I:%M %p")
    
    try:
        # Open-Meteo returns ISO format: "2026-10-26T11:00"
        dt = datetime.fromisoformat(raw_time)
        return dt.strftime("%A, %B %d, %Y | %I:%M %p")
    except (ValueError, TypeError):
        # Fallback to current time
        return datetime.now().strftime("%A, %B %d, %Y | %I:%M %p")


def format_sun_time(raw_time: str) -> str:
    """Format an ISO timestamp into a readable 12-hour time (e.g. 06:14 AM)."""
    if not raw_time or raw_time == "N/A":
        return "N/A"
    try:
        dt = datetime.fromisoformat(raw_time)
        return dt.strftime("%I:%M %p")
    except (ValueError, TypeError):
        return str(raw_time)


# -------------------------------------------------------------
# Random Module Utilities
# -------------------------------------------------------------
def get_weather_tip(condition: str, temp_c: float) -> dict:
    """Generate a dynamic, rotating weather insight or tip using `random`.
    
    Provides relevant guidance without fabricating any actual weather data.
    """
    condition_lower = condition.lower()
    
    rain_tips = [
        "Carry a compact umbrella or rain jacket today.",
        "Roads may be slick; leave a few minutes early.",
        "High humidity expected—stay comfortable indoors.",
        "A warm cup of coffee or tea is perfect for rainy conditions."
    ]
    
    cold_tips = [
        "Layer your clothing to retain body heat efficiently.",
        "Keep your extremities covered with gloves and warm socks.",
        "Check tire pressure as cool air reduces pressure.",
        "A warm soup or warm beverage is recommended today."
    ]
    
    hot_tips = [
        "Stay hydrated! Drink plenty of water throughout the day.",
        "Wear UV-protective sunglasses and broad-spectrum sunscreen.",
        "Seek shade during peak afternoon sunlight hours.",
        "Wear lightweight, breathable cotton or linen clothing."
    ]
    
    clear_tips = [
        "Great weather for an outdoor walk or light exercise.",
        "Clear skies provide optimal solar energy and natural lighting.",
        "Ideal conditions for outdoor photography.",
        "Enjoy the pleasant visibility and crisp atmosphere."
    ]
    
    general_tips = [
        "Weather conditions can shift; check updates before travel.",
        "Dress in adaptable layers for varying indoor/outdoor climates.",
        "Keep your device charged when heading out for the day."
    ]
    
    if "rain" in condition_lower or "drizzle" in condition_lower or "storm" in condition_lower:
        selected_tip = random.choice(rain_tips)
        category = "Rain Preparedness"
    elif temp_c <= 12.0:
        selected_tip = random.choice(cold_tips)
        category = "Cold Weather Advice"
    elif temp_c >= 28.0:
        selected_tip = random.choice(hot_tips)
        category = "Warm Weather Care"
    elif "clear" in condition_lower or "sunny" in condition_lower:
        selected_tip = random.choice(clear_tips)
        category = "Clear Sky Tip"
    else:
        selected_tip = random.choice(general_tips)
        category = "Daily Weather Tip"
        
    return {
        "category": category,
        "tip": selected_tip
    }


def get_random_sample_cities() -> list[str]:
    """Return a randomly chosen sample of worldwide cities for discovery."""
    city_pool = [
        "Tokyo", "London", "Bengaluru", "New York", "Paris",
        "Sydney", "Dubai", "Singapore", "Toronto", "Berlin",
        "Mumbai", "San Francisco", "Rome", "Seoul", "Cape Town"
    ]
    return random.sample(city_pool, 4)
