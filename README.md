# WeatherWise V3 — Weather Intelligence Application

> **Tagline:** *Your weather, intelligently presented.*  
> **Internship:** Python Development Internship — Week 3 Project  
> **Core Focus:** File Handling (.txt & .csv), JSON Processing, REST APIs (`requests`), Standard Libraries (`os`, `datetime`, `math`, `random`), and V3 Professional Desktop GUI.

---

## 1. Project Overview

**WeatherWise** is a full-featured Python weather intelligence application built for **Week 3 of the Python Development Internship** and upgraded to **V3 Professional Edition**. It connects to live REST APIs to retrieve real-time atmospheric data, persists search history and favorites using Python's file storage engine, and provides a polished multi-page desktop dashboard inspired by QuizUp Python Edition alongside an interactive terminal menu.

---

## 2. Features

### V3 Professional Multi-Page Desktop GUI
The graphical desktop interface is built with standard library `tkinter` and offers 6 dedicated pages:

1. **📊 Dashboard:**
   - Hero Weather Card with large temperature typography, weather condition icons, feels-like temperature, and high/low ranges.
   - 4 Key Atmospheric Metric Cards: Relative Humidity (comfort index), Wind Velocity (breeze scale), Barometric Pressure, and Calculated Wind Chill (`math.pow`).
   - Celestial Times Card: Local sunrise and sunset times.
   - Dynamic Weather Insight Card: Context-aware guidance generated dynamically via Python `random`.
   - Quick City Explorer: Interactive pills for instant access to major world cities.

2. **📅 7-Day & Hourly Forecast:**
   - 24-Hour Temperature Curve Trend Chart: Custom-drawn on native `tk.Canvas` with smooth interpolation, temperature indicators, and weather condition badges (no heavy external chart libraries needed).
   - 7-Day Extended Weather Outlook: Daily breakdown with precipitation sum (mm), maximum wind velocity, and temperature ranges.

3. **🔍 Explore & Compare:**
   - Live global city search with geocoding coordinates.
   - Side-by-Side Two-City Weather Comparison: Compare any two global cities (e.g. Aland vs. Bengaluru) with calculated metric deltas and visual highlight banners.

4. **⭐ Saved Favourites:**
   - City bookmarks persisted to `data/favorites.json`.
   - One-click live loading into the dashboard and removal controls.

5. **📋 History & Reports:**
   - Tabular search history viewer populated from `data/search_history.csv`.
   - Plain text intelligence report generator and in-app monospace previewer for `data/weather_report.txt`.

6. **⚙️ Preferences & Settings:**
   - Unit toggle between Celsius (°C) and Fahrenheit (°F).
   - Default startup city configuration.
   - Configurable automatic refresh interval (Manual, 5m, 15m, 30m).
   - Theme presets: *Sky Blue*, *Soft Lavender* (candy-styled), and *Slate Dark*.
   - Storage statistics and diagnostic overview.

### Internship Week 3 Requirements Preserved
1. **REST API Integration:**
   - Powered by **Open-Meteo REST API** (verified live, open geocoding and forecast, **requires zero API keys**).
   - Non-blocking asynchronous network requests via Python `threading`.
   - Optional fallback support for **OpenWeatherMap** if an API key is provided.
2. **File Handling:**
   - **Search History (`.csv`):** Standardized CSV logging with headers.
   - **Weather Intelligence Reports (`.txt`):** Structured human-readable summary reports.
   - **Favourites & Cache (`.json`):** JSON storage with duplicate guards and response caching.
3. **Standard Library Demonstrations:**
   - **`math`:** Conversions (Celsius, Fahrenheit, Kelvin) and wind chill formulas.
   - **`datetime`:** Standardized timestamp formatting and ISO sun time parsing.
   - **`random`:** Rotating discovery prompts and weather tips.
   - **`os`:** Safe path resolution and directory management.

---

## 3. Mapping of Official Week 3 Requirements

| Official Requirement | Implementation File | Function / Component | Description |
| :--- | :--- | :--- | :--- |
| **Consume APIs (`requests`)** | [`weather_service.py`](file:///d:/Projects/Python%20Internship/Weather%20App/weather_service.py) | `WeatherService._fetch_open_meteo()` | Queries Open-Meteo REST API, checks HTTP status codes, and processes JSON payloads for current, daily, and hourly forecasts. |
| **File Handling (`.txt`)** | [`storage.py`](file:///d:/Projects/Python%20Internship/Weather%20App/storage.py) | `save_text_report()` & `read_text_report()` | Writes and reads formatted text reports in `data/weather_report.txt`. |
| **File Handling (`.csv`)** | [`storage.py`](file:///d:/Projects/Python%20Internship/Weather%20App/storage.py) | `log_search_to_csv()`, `get_search_history_csv()`, `clear_search_history()` | Uses Python's `csv` module to log searches with headers and retrieve historical records. |
| **JSON Data Processing** | [`storage.py`](file:///d:/Projects/Python%20Internship/Weather%20App/storage.py) | `add_favorite()`, `get_favorites()`, `get_settings()`, `save_settings()` | Serializes and parses JSON records in `favorites.json`, `weather_cache.json`, and `settings.json`. |
| **`os` Module** | [`utils.py`](file:///d:/Projects/Python%20Internship/Weather%20App/utils.py) | `get_base_dir()`, `get_data_dir()` | Handles cross-platform paths, ensures `data/` exists, and reads environment variables. |
| **`datetime` Module** | [`utils.py`](file:///d:/Projects/Python%20Internship/Weather%20App/utils.py) | `get_current_timestamp()`, `format_display_time()` | Generates standardized timestamps and parses ISO sun times. |
| **`math` Module** | [`utils.py`](file:///d:/Projects/Python%20Internship/Weather%20App/utils.py) | `celsius_to_fahrenheit()`, `calculate_wind_chill()` | Calculates unit conversions and wind chill indices using `math.pow()`. |
| **`random` Module** | [`utils.py`](file:///d:/Projects/Python%20Internship/Weather%20App/utils.py) | `get_weather_tip()`, `get_random_sample_cities()` | Selects dynamic contextual advice and random city discovery prompts. |
| **Error Handling** | [`weather_service.py`](file:///d:/Projects/Python%20Internship/Weather%20App/weather_service.py) | `try...except` in API & file calls | Catches `requests.exceptions.Timeout`, `ConnectionError`, `RequestException`, `KeyError`, and `OSError`. |

---

## 4. Project Structure

```text
Weather App/
├── main.py               # Unified application entry point (Default: Launches GUI)
├── gui.py                # WeatherWise V3 professional 6-page Tkinter desktop GUI
├── weather_app.py        # Terminal application with interactive 7-option menu
├── weather_service.py    # REST API client (Open-Meteo & optional OpenWeatherMap)
├── storage.py            # File persistence engine (TXT, CSV, JSON, Settings)
├── utils.py              # Math conversions, datetime formatting, random tips, os paths
├── requirements.txt      # Project dependencies (requests>=2.31.0)
├── .env.example          # Template for optional API credentials
├── config.example.json   # Template for optional JSON configuration
├── .gitignore            # Ignores sensitive keys, data/, logs, and cache
├── README.md             # Project documentation and requirements mapping
├── data/                 # Auto-generated persistent runtime storage
│   ├── favorites.json    # JSON storage for saved favorite cities
│   ├── settings.json     # JSON storage for user preferences and theme
│   ├── weather_cache.json# JSON storage for cached weather snapshots
│   ├── search_history.csv# CSV storage for search history metrics
│   └── weather_report.txt# TXT export of formatted weather reports
└── tests/
    └── test_weather.py   # Automated unit & integration tests (17 tests)
```

---

## 5. Prerequisites & Installation

### Prerequisites
- Python 3.10 or newer (tested on Python 3.14)
- Windows, macOS, or Linux

### Installation
1. Open a terminal in the project directory:
   ```powershell
   cd "d:\Projects\Python Internship\Weather App"
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 6. How to Run

### Method 1: Desktop Graphical Application (Default)
Directly launches the modern V3 multi-page dashboard:
```powershell
python main.py
```
*(Or run `python gui.py` directly).*

### Method 2: Terminal Application
To launch the interactive command-line interface:
```powershell
python main.py --cli
```
*(Or run `python weather_app.py`).*

Interactive Terminal Menu:
```text
Main Menu:
  1. Search Weather by City Name (Live REST API)
  2. View Search History (.csv)
  3. Generate & View Weather Report (.txt)
  4. Manage Saved Favourites (.json)
  5. Compare Weather of Two Cities
  6. Launch Desktop GUI Window (Tkinter)
  7. Exit
```

---

## 7. Automated Testing

Run the test suite verifying all modules and requirements:

```powershell
python main.py --test
```
*(Or run `python -m unittest discover tests`).*

### Test Results
```text
test_gui_initialization (test_weather.TestGUI) ... ok
test_gui_multi_page_navigation (test_weather.TestGUI) ... ok
test_csv_search_logging (test_weather.TestStorageEngine) ... ok
test_json_favorites_storage (test_weather.TestStorageEngine) ... ok
test_json_weather_cache (test_weather.TestStorageEngine) ... ok
test_text_report_storage (test_weather.TestStorageEngine) ... ok
test_clear_search_history (test_weather.TestStorageEngineExtended) ... ok
test_settings_persistence (test_weather.TestStorageEngineExtended) ... ok
test_storage_stats (test_weather.TestStorageEngineExtended) ... ok
test_datetime_formatting (test_weather.TestUtils) ... ok
test_random_sample_cities (test_weather.TestUtils) ... ok
test_random_weather_tip (test_weather.TestUtils) ... ok
test_temperature_conversions (test_weather.TestUtils) ... ok
test_wind_chill_calculation (test_weather.TestUtils) ... ok
test_empty_city_validation (test_weather.TestWeatherService) ... ok
test_invalid_city_handling (test_weather.TestWeatherService) ... ok
test_live_api_fetch (test_weather.TestWeatherService) ... ok

----------------------------------------------------------------------
Ran 17 tests in 5.434s

OK
```

All 17 tests passed:
- Mathematical calculations (`math.pow`, Celsius, Fahrenheit, Kelvin, wind chill formulas).
- Datetime timestamp formatting and ISO 8601 parsing.
- Dynamic contextual weather tips (`random`).
- Text file (`.txt`) report generation and reading.
- CSV file (`.csv`) search logging with column headers and clearing.
- JSON file (`.json`) favorite addition, duplicate guard, and deletion.
- User settings persistence in `settings.json`.
- Live Open-Meteo REST API queries, hourly and 7-day forecast parsing.
- Tkinter GUI initialization and multi-page navigation.

---

## 8. Security & GitHub Readiness

- [x] **Zero Mandatory Keys:** Open-Meteo operates key-free out of the box.
- [x] **Git Ignored:** `.gitignore` excludes `.env`, `config.json`, `data/`, and `__pycache__/`.
- [x] **Project Isolation:** Week 1 ([`Basic Calculator/`](file:///d:/Projects/Python%20Internship/Basic%20Calculator)), Week 2 ([`Student Management System/`](file:///d:/Projects/Python%20Internship/Student%20Management%20System)), and Week 4 ([`QuizUp Python Edition/`](file:///d:/Projects/Python%20Internship/QuizUp%20Python%20Edition)) are completely untouched.
