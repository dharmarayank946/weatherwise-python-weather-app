# WeatherWise — Weather Intelligence Application

> **Tagline:** *Your weather, intelligently presented.*  
> **Internship:** Python Development Internship — Week 3 Project  
> **Core Focus:** File Handling (.txt & .csv), JSON Processing, REST APIs (`requests`), and Python Standard Libraries (`os`, `datetime`, `math`, `random`).

---

## 1. Project Overview

**WeatherWise** is a Python application built for **Week 3 of the Python Development Internship**. It connects to live REST APIs to retrieve real-time atmospheric data, persists search history and favorites using Python's file storage engine, and provides a polished, menu-driven terminal experience alongside an optional native desktop GUI companion built with standard `tkinter`.

---

## 2. Features

1. **Live City Weather Search:** Query any worldwide city to retrieve real-time atmospheric metrics:
   - Temperature, Apparent "Feels-Like" Temperature, and Perceived Wind Chill.
   - Atmospheric Pressure, Relative Humidity, and Wind Velocity.
   - Daylight intervals: Local Sunrise and Sunset times.
   - WMO Weather interpretation condition codes and ASCII weather visuals.
2. **REST API Integration:**
   - Powered by **Open-Meteo REST API** (verified live, open geocoding and forecast, **requires no API key**).
   - Optional support for **OpenWeatherMap** if an API key is provided via environment variables.
3. **File Handling Demonstrations:**
   - **Search History (`.csv`):** Automatically appends every search query and atmospheric reading to `data/search_history.csv` with standardized headers (`Timestamp, City, Country, Temperature_C, Temperature_F, Humidity, Wind_Speed_KMH, Condition`).
   - **Weather Intelligence Reports (`.txt`):** Generates and reads formatted, human-readable summary reports in `data/weather_report.txt`.
   - **Favourites & Cache (`.json`):** Persists favorite cities in `data/favorites.json` (with duplicate guards) and caches response snapshots in `data/weather_cache.json`.
4. **Standard Library Demonstrations:**
   - **`math`:** Metric/Imperial conversions (Celsius, Fahrenheit, Kelvin) and thermodynamic wind chill calculations using `math.pow()`.
   - **`datetime`:** Timestamp formatting (`YYYY-MM-DD HH:MM:SS`), ISO 8601 parsing, and update interval formatting.
   - **`random`:** Rotating discovery prompts and dynamic, context-aware weather preparedness tips.
   - **`os`:** Safe cross-platform path resolution, directory validation, and environment credential checks.
5. **City Comparison Tool:** Compare atmospheric conditions between two global destinations side-by-side.
6. **Native Desktop GUI Companion:** Built entirely with Python's standard `tkinter` library (no external GUI packages or web servers required).

---

## 3. Mapping of Official Week 3 Requirements

| Official Requirement | Implementation File | Function / Component | Description |
| :--- | :--- | :--- | :--- |
| **Consume APIs (`requests`)** | [`weather_service.py`](file:///d:/Projects/Python%20Internship/Weather%20App/weather_service.py) | `WeatherService._fetch_open_meteo()` | Queries Open-Meteo REST API, checks HTTP status codes, and processes JSON payloads. |
| **File Handling (`.txt`)** | [`storage.py`](file:///d:/Projects/Python%20Internship/Weather%20App/storage.py) | `save_text_report()` & `read_text_report()` | Writes and reads formatted text reports in `data/weather_report.txt`. |
| **File Handling (`.csv`)** | [`storage.py`](file:///d:/Projects/Python%20Internship/Weather%20App/storage.py) | `log_search_to_csv()` & `get_search_history_csv()` | Uses Python's `csv` module to log searches with headers and retrieve historical records. |
| **JSON Data Processing** | [`storage.py`](file:///d:/Projects/Python%20Internship/Weather%20App/storage.py) | `add_favorite()`, `get_favorites()`, `cache_weather_snapshot()` | Serializes and parses JSON records in `favorites.json` and `weather_cache.json`. |
| **`os` Module** | [`utils.py`](file:///d:/Projects/Python%20Internship/Weather%20App/utils.py) | `get_base_dir()`, `get_data_dir()` | Handles cross-platform paths, ensures `data/` exists, and reads environment variables. |
| **`datetime` Module** | [`utils.py`](file:///d:/Projects/Python%20Internship/Weather%20App/utils.py) | `get_current_timestamp()`, `format_display_time()` | Generates standardized timestamps and parses ISO sun times. |
| **`math` Module** | [`utils.py`](file:///d:/Projects/Python%20Internship/Weather%20App/utils.py) | `celsius_to_fahrenheit()`, `calculate_wind_chill()` | Calculates unit conversions and wind chill indices using `math.pow()`. |
| **`random` Module** | [`utils.py`](file:///d:/Projects/Python%20Internship/Weather%20App/utils.py) | `get_weather_tip()`, `get_random_sample_cities()` | Selects dynamic contextual advice and random city discovery prompts. |
| **Error Handling** | [`weather_service.py`](file:///d:/Projects/Python%20Internship/Weather%20App/weather_service.py) | `try...except` in API & file calls | Catches `requests.exceptions.Timeout`, `ConnectionError`, `RequestException`, `KeyError`, and `OSError`. |

---

## 4. Project Structure

```text
Weather App/
├── weather_app.py        # Main terminal application with interactive 7-option menu
├── weather_service.py    # REST API client (Open-Meteo & optional OpenWeatherMap)
├── storage.py            # File persistence engine (TXT, CSV, JSON)
├── utils.py              # Math conversions, datetime formatting, random tips, os paths
├── gui.py                # Optional native Tkinter desktop graphical interface
├── requirements.txt      # Project dependencies (requests>=2.31.0)
├── .env.example          # Template for optional API credentials
├── config.example.json   # Template for optional JSON configuration
├── .gitignore            # Ignores sensitive keys, data/, logs, and cache
├── README.md             # Project documentation and requirements mapping
├── data/                 # Auto-generated persistent runtime storage
│   ├── favorites.json    # JSON storage for saved favorite cities
│   ├── weather_cache.json# JSON storage for cached weather snapshots
│   ├── search_history.csv# CSV storage for search history metrics
│   └── weather_report.txt# TXT export of formatted weather reports
└── tests/
    └── test_weather.py   # Automated unit & integration tests
```

---

## 5. Prerequisites & Installation

### Prerequisites
- Python 3.10 or newer (tested on Python 3.13)
- Windows, macOS, or Linux

### Installation
1. Open a terminal in the project directory:
   ```powershell
   cd "d:\Projects\Python Internship\Weather App"
   ```

2. Install the `requests` library:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 6. How to Run

### Method 1: Terminal Application (Main Interface)
```powershell
python weather_app.py
```
This presents an interactive menu:
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

### Method 2: Native Desktop GUI Companion
To launch the graphical window directly:
```powershell
python weather_app.py --gui
```
*(Or run `python gui.py` directly).*

---

## 7. Automated Testing

Run the test suite verifying all required concepts:

```powershell
python tests/test_weather.py
```

### Test Results
```text
............
----------------------------------------------------------------------
Ran 12 tests in 2.746s

OK
```

All 12 tests passed:
- Math unit conversions ($^\circ\text{C} \rightarrow ^\circ\text{F} \rightarrow \text{K}$) and wind chill formulas.
- Datetime timestamp formatting and ISO parsing.
- Random contextual weather tips and sample city selection.
- Text file (`.txt`) report generation and reading.
- CSV file (`.csv`) search logging with column headers and dictionary retrieval.
- JSON file (`.json`) favorite addition, duplicate guard, and deletion.
- JSON response caching and lookup.
- API validation: empty string rejection, unknown city (404) handling, and real live API retrieval.

---

## 8. Security & GitHub Readiness

- [x] **No Hardcoded Keys:** Open-Meteo requires no key; OpenWeatherMap uses `os.environ.get("OPENWEATHER_API_KEY")`.
- [x] **Git Ignored:** `.gitignore` excludes `.env`, `config.json`, `data/`, and `__pycache__/`.
- [x] **Project Isolation:** Week 1 ([`Basic Calculator/`](file:///d:/Projects/Python%20Internship/Basic%20Calculator)) and Week 2 ([`Student Management System/`](file:///d:/Projects/Python%20Internship/Student%20Management%20System)) are completely untouched.
