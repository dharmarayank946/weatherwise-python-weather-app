"""WeatherWise — FastAPI Production Weather Intelligence Microservice.
==================================================================
Directly leverages the existing WeatherService (Open-Meteo zero-key integration)
and StorageEngine to provide real-time atmospheric conditions, forecasts,
air quality indices, city comparisons, and favorites persistence.
"""

import os
import sys
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

# Ensure root Weather App modules are in python sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from weather_service import WeatherService
from storage import StorageEngine

app = FastAPI(
    title="WeatherWise API",
    description="Real-time atmospheric intelligence microservice powered by live Open-Meteo REST integration.",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = WeatherService()
storage = StorageEngine()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------
class FavoriteCityRequest(BaseModel):
    city: str = Field(..., min_length=1, max_length=100, example="Bangalore")


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------
@app.get("/health", tags=["Health"])
def health_check():
    """Liveness probe for Render deployment."""
    return {
        "status": "healthy",
        "service": "weatherwise-api",
        "version": "3.0.0",
        "provider": "Open-Meteo API",
        "favorites_count": len(storage.get_favorites())
    }


@app.get("/api/v1/weather/current", tags=["Weather"])
def get_current_weather(city: str = Query("London", description="Target city name")):
    """Fetch live atmospheric conditions for a target city."""
    clean_city = city.strip()
    if not clean_city:
        raise HTTPException(status_code=400, detail="City name cannot be empty.")

    data = service.get_weather(clean_city)
    if not data.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=data.get("error", f"Could not retrieve weather for '{clean_city}'.")
        )

    # Log to history in storage engine
    try:
        storage.log_search_to_csv(data)
    except Exception:
        pass

    return data


@app.get("/api/v1/weather/forecast", tags=["Weather"])
def get_forecast(city: str = Query("London", description="Target city name")):
    """Fetch 7-day daily and 24-hour hourly forecasts."""
    clean_city = city.strip()
    data = service.get_weather(clean_city)
    if not data.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=data.get("error", f"Could not retrieve forecast for '{clean_city}'.")
        )

    return {
        "city": data.get("city"),
        "country": data.get("country"),
        "current": {
            "temperature_c": data.get("temperature_c"),
            "condition": data.get("condition"),
            "humidity": data.get("humidity"),
            "wind_speed_kmh": data.get("wind_speed_kmh")
        },
        "daily_forecast": data.get("daily_forecast", []),
        "hourly_forecast": data.get("hourly_forecast", [])
    }


@app.get("/api/v1/weather/compare", tags=["Weather"])
def compare_cities(
    city1: str = Query(..., description="First city"),
    city2: str = Query(..., description="Second city")
):
    """Side-by-side meteorological comparison of two cities."""
    w1 = service.get_weather(city1.strip())
    w2 = service.get_weather(city2.strip())

    if not w1.get("success"):
        raise HTTPException(status_code=404, detail=f"City 1 ({city1}) error: {w1.get('error')}")
    if not w2.get("success"):
        raise HTTPException(status_code=404, detail=f"City 2 ({city2}) error: {w2.get('error')}")

    diff_temp = round(w1.get("temperature_c", 0) - w2.get("temperature_c", 0), 1)
    diff_humidity = round(w1.get("humidity", 0) - w2.get("humidity", 0), 1)

    return {
        "city1": w1,
        "city2": w2,
        "delta": {
            "temperature_diff_c": diff_temp,
            "humidity_diff": diff_humidity,
            "warmer_city": w1.get("city") if diff_temp > 0 else w2.get("city") if diff_temp < 0 else "Equal"
        }
    }


@app.get("/api/v1/weather/air-quality", tags=["Weather"])
def get_air_quality(city: str = Query("London")):
    """Retrieve European AQI and major pollutant levels."""
    data = service.get_weather(city.strip())
    if not data.get("success"):
        raise HTTPException(status_code=404, detail=data.get("error"))

    aqi = data.get("air_quality", {})
    return {
        "city": data.get("city"),
        "country": data.get("country"),
        "air_quality": aqi
    }


@app.get("/api/v1/weather/favorites", tags=["Favorites"])
def list_favorites():
    """Retrieve bookmarked favorite cities."""
    return {"favorites": storage.get_favorites()}


@app.post("/api/v1/weather/favorites", tags=["Favorites"])
def add_favorite(req: FavoriteCityRequest):
    """Bookmark a favorite city."""
    city_clean = req.city.strip().title()
    storage.add_favorite(city_clean)
    return {"favorites": storage.get_favorites(), "message": f"'{city_clean}' added to favorites."}


@app.delete("/api/v1/weather/favorites/{city}", tags=["Favorites"])
def remove_favorite(city: str):
    """Remove a city from bookmarks."""
    city_clean = city.strip().title()
    storage.remove_favorite(city_clean)
    return {"favorites": storage.get_favorites(), "message": f"'{city_clean}' removed."}


@app.get("/api/v1/weather/report/txt", tags=["Reports"])
def download_weather_report(city: str = Query("London")):
    """Generate and download formatted WeatherWise intelligence plain-text report."""
    data = service.get_weather(city.strip())
    if not data.get("success"):
        raise HTTPException(status_code=404, detail=data.get("error"))

    # Generate report text using storage engine logic
    report_text = f"""======================================================================
                     WEATHERWISE INTELLIGENCE REPORT
======================================================================
Target City   : {data.get('city')}, {data.get('country')}
Coordinates   : Lat {data.get('latitude')}, Lon {data.get('longitude')}
Data Source   : {data.get('source', 'Open-Meteo')}
----------------------------------------------------------------------
CURRENT CONDITIONS
----------------------------------------------------------------------
Condition     : {data.get('condition')}
Temperature   : {data.get('temperature_c')} °C  |  {data.get('temperature_f')} °F
Feels Like    : {data.get('feels_like_c')} °C
Day Range     : High {data.get('temp_max_c')} °C / Low {data.get('temp_min_c')} °C
Humidity      : {data.get('humidity')} %
Wind Speed    : {data.get('wind_speed_kmh')} km/h
Pressure      : {data.get('pressure_hpa')} hPa
======================================================================
               WeatherWise Real-time Microservice Report
"""
    return PlainTextResponse(
        content=report_text,
        headers={"Content-Disposition": f"attachment; filename=weatherwise_{city.lower()}_report.txt"}
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
