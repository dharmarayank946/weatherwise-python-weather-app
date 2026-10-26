"""WeatherWise — Comprehensive Python Weather Intelligence Application.

Week 3 Python Development Internship:
- REST API Integration via `requests`
- File Handling: Plain Text (`.txt`) and CSV (`.csv`)
- JSON Data Processing (`.json`)
- Python Standard Libraries: `os`, `random`, `datetime`, `math`
- Polished Terminal Application & Optional Native Tkinter Desktop GUI
"""

import os
import sys

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from weather_service import WeatherService
from storage import StorageEngine
from utils import (
    celsius_to_fahrenheit,
    celsius_to_kelvin,
    calculate_wind_chill,
    get_current_timestamp,
    get_weather_tip,
    get_random_sample_cities
)

# ANSI Color and Styling Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

CYAN = "\033[36m"
BLUE = "\033[34m"
PURPLE = "\033[35m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"
WHITE = "\033[37m"
GRAY = "\033[90m"


def get_weather_art(icon_type: str) -> list[str]:
    """Return stylized ASCII weather art for the given condition."""
    art_map = {
        "sunny": [
            f"{YELLOW}    \\   /    {RESET}",
            f"{YELLOW}     .-.     {RESET}",
            f"{YELLOW}  -- (   ) --{RESET}",
            f"{YELLOW}     `-´     {RESET}",
            f"{YELLOW}    /   \\    {RESET}"
        ],
        "cloudy": [
            f"{GRAY}     .--.    {RESET}",
            f"{GRAY}  .-(    ).  {RESET}",
            f"{WHITE} (___.__)__) {RESET}",
            f"{WHITE}             {RESET}",
            f"{WHITE}             {RESET}"
        ],
        "rainy": [
            f"{GRAY}     .--.    {RESET}",
            f"{GRAY}  .-(    ).  {RESET}",
            f"{WHITE} (___.__)__) {RESET}",
            f"{CYAN}  '   '   '  {RESET}",
            f"{CYAN}    '   '    {RESET}"
        ],
        "stormy": [
            f"{GRAY}     .--.    {RESET}",
            f"{GRAY}  .-(    ).  {RESET}",
            f"{WHITE} (___.__)__) {RESET}",
            f"{YELLOW}   / /  / /  {RESET}",
            f"{CYAN}   '   '  '  {RESET}"
        ],
        "snowy": [
            f"{GRAY}     .--.    {RESET}",
            f"{GRAY}  .-(    ).  {RESET}",
            f"{WHITE} (___.__)__) {RESET}",
            f"{CYAN}   *   *   * {RESET}",
            f"{CYAN}     *   *   {RESET}"
        ],
        "foggy": [
            f"{GRAY} _ - _ - _ - {RESET}",
            f"{GRAY}  _ - _ - _  {RESET}",
            f"{GRAY} _ - _ - _ - {RESET}",
            f"{GRAY}             {RESET}",
            f"{GRAY}             {RESET}"
        ]
    }
    return art_map.get(icon_type, art_map["cloudy"])


def display_header():
    """Display the application brand banner."""
    print()
    print(f"{CYAN}+==================================================================+{RESET}")
    print(f"{CYAN}|{RESET}  {BOLD}{WHITE}WeatherWise{RESET} - {CYAN}Your weather, intelligently presented.{RESET}          {CYAN}|{RESET}")
    print(f"{CYAN}|{RESET}  {DIM}Python Internship Week 3 | APIs, JSON, CSV, TXT & Libraries{RESET}     {CYAN}|{RESET}")
    print(f"{CYAN}+==================================================================+{RESET}")


def display_weather_card(data: dict):
    """Render a clean, polished terminal card with atmospheric readings."""
    city = data.get("city", "Unknown")
    country = data.get("country", "")
    region = data.get("region", "")
    location_str = f"{city}, {region}, {country}" if region else f"{city}, {country}"

    temp_c = data.get("temperature_c", 0.0)
    temp_f = celsius_to_fahrenheit(temp_c)
    temp_k = celsius_to_kelvin(temp_c)

    feels_c = data.get("feels_like_c", temp_c)
    feels_f = celsius_to_fahrenheit(feels_c)
    chill_c = calculate_wind_chill(temp_c, data.get("wind_speed_kmh", 0.0))

    temp_max_c = data.get("temp_max_c", temp_c)
    temp_min_c = data.get("temp_min_c", temp_c)

    condition = data.get("condition", "N/A")
    humidity = data.get("humidity", 0)
    wind_kmh = data.get("wind_speed_kmh", 0.0)
    pressure = data.get("pressure_hpa", 1013)
    sunrise = data.get("sunrise", "N/A")
    sunset = data.get("sunset", "N/A")
    source = data.get("source", "Live API")
    coords = f"Lat {data.get('latitude', 0.0)}, Lon {data.get('longitude', 0.0)}"

    art_lines = get_weather_art(data.get("icon_type", "cloudy"))

    print()
    print(f"{BLUE}+------------------------------------------------------------------+{RESET}")
    print(f"{BLUE}|{RESET} {BOLD}{WHITE}{location_str[:40]:<40}{RESET} {GREEN}[{source}]{RESET} {coords:>10} {BLUE}|{RESET}")
    print(f"{BLUE}+------------------------------------------------------------------+{RESET}")

    # Top Block: ASCII Art with temperature and condition
    print(f"{BLUE}|{RESET}  {art_lines[0]}   {BOLD}{YELLOW}{temp_c} C{RESET}  {DIM}/ {temp_f} F  / {temp_k} K{RESET}                {BLUE}|{RESET}")
    print(f"{BLUE}|{RESET}  {art_lines[1]}   {BOLD}{WHITE}{condition[:38]:<38}{RESET}        {BLUE}|{RESET}")
    print(f"{BLUE}|{RESET}  {art_lines[2]}   {GRAY}Feels like {feels_c} C ({feels_f} F) | Chill: {chill_c} C{RESET}      {BLUE}|{RESET}")
    print(f"{BLUE}|{RESET}  {art_lines[3]}   {GRAY}Day High: {temp_max_c} C  |  Low: {temp_min_c} C{RESET}          {BLUE}|{RESET}")
    print(f"{BLUE}|{RESET}  {art_lines[4]}                                                 {BLUE}|{RESET}")
    print(f"{BLUE}+------------------------------------------------------------------+{RESET}")

    # Atmospheric Metrics
    rise_time = sunrise[-5:] if len(sunrise) >= 5 else sunrise
    set_time = sunset[-5:] if len(sunset) >= 5 else sunset
    print(f"{BLUE}|{RESET}  {CYAN}Humidity{RESET}     : {WHITE}{humidity}%{RESET}          {CYAN}Wind Velocity{RESET} : {WHITE}{wind_kmh} km/h{RESET}       {BLUE}|{RESET}")
    print(f"{BLUE}|{RESET}  {CYAN}Pressure{RESET}     : {WHITE}{pressure} hPa{RESET}     {CYAN}Sun Times{RESET}     : {WHITE}Rise {rise_time} / Set {set_time}{RESET}   {BLUE}|{RESET}")
    print(f"{BLUE}+------------------------------------------------------------------+{RESET}")

    # Dynamic Insight using random & math
    tip = get_weather_tip(condition, temp_c)
    print(f"{BLUE}|{RESET}  {PURPLE}Insight [{tip['category']}]{RESET}: {WHITE}{tip['tip'][:46]:<46}{RESET} {BLUE}|{RESET}")
    print(f"{BLUE}+------------------------------------------------------------------+{RESET}")


# -------------------------------------------------------------
# Operations Handlers
# -------------------------------------------------------------
def search_flow(service: WeatherService, storage: StorageEngine) -> dict:
    """Search weather for a city, persist to CSV and JSON, and return data."""
    city_input = input(f"\n{BOLD}Enter city name to search{RESET} (or press Enter to return): ").strip()
    if not city_input:
        return None

    print(f"{CYAN}Connecting to API and fetching weather for '{city_input}'...{RESET}")
    result = service.get_weather(city_input)

    if not result.get("success"):
        error_msg = result.get("error", "Unknown error occurred.")
        print(f"\n{RED}{BOLD}[Error]{RESET} {error_msg}")
        return None

    # Persist search to CSV log and cache to JSON
    storage.log_search_to_csv(result)
    storage.cache_weather_snapshot(result)

    display_weather_card(result)
    return result


def view_search_history(storage: StorageEngine):
    """Read and display recent search records from CSV file."""
    print(f"\n{BOLD}--- Recent Search History (.csv) ---{RESET}")
    history = storage.get_search_history_csv(limit=15)

    if not history:
        print(f"{YELLOW}No search history recorded in CSV yet.{RESET}")
        return

    print(f"{DIM}Source file: {storage.history_csv_path}{RESET}\n")
    print(f"{CYAN}{'Timestamp':<20} {'City':<16} {'Country':<10} {'Temp (C)':<10} {'Condition':<20}{RESET}")
    print("-" * 78)

    for item in history:
        ts = item.get("Timestamp", "")
        city = item.get("City", "")
        country = item.get("Country", "")
        temp = f"{item.get('Temperature_C', '')} C"
        cond = item.get("Condition", "")
        print(f"{ts:<20} {city:<16} {country:<10} {temp:<10} {cond:<20}")


def generate_and_view_report(storage: StorageEngine, last_weather: dict, service: WeatherService):
    """Generate a readable weather report in a .txt file and read it back."""
    print(f"\n{BOLD}--- Generate & View Weather Report (.txt) ---{RESET}")

    target_weather = last_weather
    if not target_weather:
        city = input("Enter city name for report: ").strip()
        if not city:
            return
        target_weather = service.get_weather(city)
        if not target_weather.get("success"):
            print(f"{RED}Error: {target_weather.get('error')}{RESET}")
            return

    path = storage.save_text_report(target_weather)
    print(f"{GREEN}Success: Report written to:{RESET} {path}\n")

    content = storage.read_text_report(path)
    print(content)


def manage_favorites(storage: StorageEngine, service: WeatherService, last_weather: dict = None):
    """Manage saved favorite cities using JSON storage."""
    while True:
        favs = storage.get_favorites()
        print(f"\n{BOLD}--- Manage Saved Favourites (.json) ---{RESET}")
        print(f"{DIM}Source file: {storage.favorites_json_path}{RESET}")

        if not favs:
            print(f"{YELLOW}No favourite cities saved yet.{RESET}")
        else:
            for idx, fav in enumerate(favs, start=1):
                city_name = fav.get("city", "Unknown")
                country = fav.get("country", "")
                loc = f"{city_name} ({country})" if country else city_name
                print(f"  {CYAN}{idx}.{RESET} {loc} — Added: {fav.get('added_at', '')}")

        print(f"\nOptions:")
        print(f"  {CYAN}1.{RESET} Add a City to Favourites")
        print(f"  {CYAN}2.{RESET} Quick Search a Favourite City")
        print(f"  {CYAN}3.{RESET} Remove a Favourite City")
        print(f"  {CYAN}4.{RESET} Return to Main Menu")

        choice = input("\nSelect choice (1-4): ").strip()

        if choice == "1":
            default_prompt = f" (press Enter for '{last_weather['city']}')" if last_weather else ""
            city = input(f"Enter city name to add{default_prompt}: ").strip()
            if not city and last_weather:
                city = last_weather.get("city", "")
                country = last_weather.get("country", "")
            elif city:
                country = ""
                # If city matches current weather, use its country
                if last_weather and last_weather.get("city", "").lower() == city.lower():
                    country = last_weather.get("country", "")
                else:
                    # Quick lookup to fetch country if available
                    lookup = service.get_weather(city)
                    if lookup.get("success"):
                        city = lookup.get("city", city)
                        country = lookup.get("country", "")

            if city:
                added = storage.add_favorite(city, country)
                if added:
                    print(f"{GREEN}Success: '{city}' added to favourites (.json)!{RESET}")
                else:
                    print(f"{YELLOW}Notice: '{city}' is already in your favourites.{RESET}")
        elif choice == "2":
            if not favs:
                print(f"{YELLOW}No favourites to select.{RESET}")
                continue
            num = input(f"Enter favourite number (1-{len(favs)}): ").strip()
            if num.isdigit() and 1 <= int(num) <= len(favs):
                chosen = favs[int(num) - 1]["city"]
                print(f"{CYAN}Fetching live weather for '{chosen}'...{RESET}")
                data = service.get_weather(chosen)
                if data.get("success"):
                    storage.log_search_to_csv(data)
                    display_weather_card(data)
                else:
                    print(f"{RED}Error: {data.get('error')}{RESET}")
            else:
                print(f"{YELLOW}Invalid selection.{RESET}")
        elif choice == "3":
            if not favs:
                print(f"{YELLOW}No favourites to remove.{RESET}")
                continue
            target = input("Enter favourite number (1-" + str(len(favs)) + ") or city name to remove: ").strip()
            if not target:
                continue
            if target.isdigit() and 1 <= int(target) <= len(favs):
                city_to_remove = favs[int(target) - 1]["city"]
            else:
                city_to_remove = target

            removed = storage.remove_favorite(city_to_remove)
            if removed:
                print(f"{GREEN}Success: '{city_to_remove}' removed from favourites.{RESET}")
            else:
                print(f"{YELLOW}Notice: '{city_to_remove}' was not found in favourites.{RESET}")
        elif choice == "4":
            break


def compare_two_cities(service: WeatherService, storage: StorageEngine = None):
    """Compare weather of two cities side by side using live REST API data."""
    print(f"\n{BOLD}--- Compare Weather of Two Cities ---{RESET}")
    c1 = input("Enter First City : ").strip()
    c2 = input("Enter Second City: ").strip()

    if not c1 or not c2:
        print(f"{YELLOW}Both city names are required.{RESET}")
        return

    print(f"{CYAN}Connecting to API and fetching live data for '{c1}' and '{c2}'...{RESET}")
    res1 = service.get_weather(c1)
    res2 = service.get_weather(c2)

    if not res1.get("success"):
        print(f"{RED}Error fetching '{c1}': {res1.get('error')}{RESET}")
        return
    if not res2.get("success"):
        print(f"{RED}Error fetching '{c2}': {res2.get('error')}{RESET}")
        return

    # Persist both live queries to CSV history and JSON cache
    if storage:
        storage.log_search_to_csv(res1)
        storage.log_search_to_csv(res2)
        storage.cache_weather_snapshot(res1)
        storage.cache_weather_snapshot(res2)

    # Column formatting
    w_metric = 18
    w_col = 26
    sep_line = "+" + "-" * (w_metric + 2) + "+" + "-" * (w_col + 2) + "+" + "-" * (w_col + 2) + "+"

    loc1 = f"{res1['city']}, {res1['country']}" if res1.get("country") else res1["city"]
    loc2 = f"{res2['city']}, {res2['country']}" if res2.get("country") else res2["city"]

    t1_c = res1["temperature_c"]
    t2_c = res2["temperature_c"]
    t1_str = f"{t1_c} C ({celsius_to_fahrenheit(t1_c)} F)"
    t2_str = f"{t2_c} C ({celsius_to_fahrenheit(t2_c)} F)"

    f1_c = res1["feels_like_c"]
    f2_c = res2["feels_like_c"]
    f1_str = f"{f1_c} C ({celsius_to_fahrenheit(f1_c)} F)"
    f2_str = f"{f2_c} C ({celsius_to_fahrenheit(f2_c)} F)"

    h1_str = f"{res1.get('temp_max_c', t1_c)} C / {res1.get('temp_min_c', t1_c)} C"
    h2_str = f"{res2.get('temp_max_c', t2_c)} C / {res2.get('temp_min_c', t2_c)} C"

    hum1_str = f"{res1.get('humidity', 0)}%"
    hum2_str = f"{res2.get('humidity', 0)}%"

    wind1_str = f"{res1.get('wind_speed_kmh', 0.0)} km/h"
    wind2_str = f"{res2.get('wind_speed_kmh', 0.0)} km/h"

    press1_str = f"{res1.get('pressure_hpa', 1013)} hPa"
    press2_str = f"{res2.get('pressure_hpa', 1013)} hPa"

    sun1 = f"Rise {res1['sunrise'][-5:]} / Set {res1['sunset'][-5:]}"
    sun2 = f"Rise {res2['sunrise'][-5:]} / Set {res2['sunset'][-5:]}"

    print()
    print(f"{BLUE}{sep_line}{RESET}")
    print(f"{BLUE}|{RESET} {BOLD}{'METRIC':<{w_metric}}{RESET} {BLUE}|{RESET} {BOLD}{CYAN}{loc1[:w_col]:<{w_col}}{RESET} {BLUE}|{RESET} {BOLD}{CYAN}{loc2[:w_col]:<{w_col}}{RESET} {BLUE}|{RESET}")
    print(f"{BLUE}{sep_line}{RESET}")
    print(f"{BLUE}|{RESET} {'Condition':<{w_metric}} {BLUE}|{RESET} {res1['condition'][:w_col]:<{w_col}} {BLUE}|{RESET} {res2['condition'][:w_col]:<{w_col}} {BLUE}|{RESET}")
    print(f"{BLUE}|{RESET} {'Temperature':<{w_metric}} {BLUE}|{RESET} {t1_str:<{w_col}} {BLUE}|{RESET} {t2_str:<{w_col}} {BLUE}|{RESET}")
    print(f"{BLUE}|{RESET} {'Feels Like':<{w_metric}} {BLUE}|{RESET} {f1_str:<{w_col}} {BLUE}|{RESET} {f2_str:<{w_col}} {BLUE}|{RESET}")
    print(f"{BLUE}|{RESET} {'Day High / Low':<{w_metric}} {BLUE}|{RESET} {h1_str:<{w_col}} {BLUE}|{RESET} {h2_str:<{w_col}} {BLUE}|{RESET}")
    print(f"{BLUE}|{RESET} {'Humidity':<{w_metric}} {BLUE}|{RESET} {hum1_str:<{w_col}} {BLUE}|{RESET} {hum2_str:<{w_col}} {BLUE}|{RESET}")
    print(f"{BLUE}|{RESET} {'Wind Velocity':<{w_metric}} {BLUE}|{RESET} {wind1_str:<{w_col}} {BLUE}|{RESET} {wind2_str:<{w_col}} {BLUE}|{RESET}")
    print(f"{BLUE}|{RESET} {'Air Pressure':<{w_metric}} {BLUE}|{RESET} {press1_str:<{w_col}} {BLUE}|{RESET} {press2_str:<{w_col}} {BLUE}|{RESET}")
    print(f"{BLUE}|{RESET} {'Sun Times':<{w_metric}} {BLUE}|{RESET} {sun1:<{w_col}} {BLUE}|{RESET} {sun2:<{w_col}} {BLUE}|{RESET}")
    print(f"{BLUE}{sep_line}{RESET}")

    # Comparative Insights using math
    temp_diff = round(abs(t1_c - t2_c), 1)
    if t1_c > t2_c:
        temp_summary = f"{res1['city']} is {temp_diff} C warmer than {res2['city']}."
    elif t2_c > t1_c:
        temp_summary = f"{res2['city']} is {temp_diff} C warmer than {res1['city']}."
    else:
        temp_summary = f"Both cities have identical temperatures ({t1_c} C)."

    hum_diff = abs(res1["humidity"] - res2["humidity"])
    hum_higher = res1["city"] if res1["humidity"] > res2["humidity"] else res2["city"]

    print(f"{BLUE}|{RESET} {PURPLE}Summary:{RESET} {temp_summary:<62} {BLUE}|{RESET}")
    if hum_diff > 0:
        hum_summary = f"{hum_higher} has {hum_diff}% higher relative humidity."
        print(f"{BLUE}|{RESET}          {hum_summary:<63} {BLUE}|{RESET}")
    print(f"{BLUE}{sep_line}{RESET}")


def launch_desktop_gui():
    """Launch the optional Tkinter desktop GUI as an independent, responsive desktop window."""
    try:
        import tkinter
    except ImportError:
        print(f"\n{RED}[Error] Tkinter is not installed in this Python environment.{RESET}")
        print("Please ensure Python was installed with tcl/tk support.")
        return

    gui_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui.py")
    if not os.path.exists(gui_script):
        print(f"\n{RED}[Error] GUI module file not found at: {gui_script}{RESET}")
        return

    print(f"\n{CYAN}Launching WeatherWise Desktop GUI window...{RESET}")
    try:
        import subprocess
        # Launch GUI as an independent detached desktop process
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        proc = subprocess.Popen(
            [sys.executable, gui_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            **kwargs
        )
        print(f"{GREEN}✔ Success: Desktop GUI window launched (Process ID: {proc.pid}).{RESET}")
        print(f"{DIM}The GUI is running in a separate window. You can continue using this terminal!{RESET}")
    except Exception as exc:
        print(f"{YELLOW}Process launch failed ({exc}). Attempting in-process launch...{RESET}")
        try:
            from gui import launch_gui
            launch_gui()
        except Exception as direct_exc:
            print(f"{RED}[Error] Could not initialize Tkinter desktop window: {direct_exc}{RESET}")



# -------------------------------------------------------------
# Main Application Loop
# -------------------------------------------------------------
def main():
    """Main menu loop."""
    display_header()
    service = WeatherService()
    storage = StorageEngine()
    last_weather = None

    while True:
        samples = ", ".join(get_random_sample_cities()[:3])
        print(f"\n{BOLD}Main Menu:{RESET} {DIM}(Try: {samples}){RESET}")
        print(f"  {CYAN}1.{RESET} Search Weather by City Name (Live REST API)")
        print(f"  {CYAN}2.{RESET} View Search History ({CYAN}.csv{RESET})")
        print(f"  {CYAN}3.{RESET} Generate & View Weather Report ({CYAN}.txt{RESET})")
        print(f"  {CYAN}4.{RESET} Manage Saved Favourites ({CYAN}.json{RESET})")
        print(f"  {CYAN}5.{RESET} Compare Weather of Two Cities")
        print(f"  {CYAN}6.{RESET} Launch Desktop GUI Window (Tkinter)")
        print(f"  {CYAN}7.{RESET} Exit")

        choice = input(f"\n{BOLD}Select an option (1-7):{RESET} ").strip()

        if choice == "1":
            weather = search_flow(service, storage)
            if weather:
                last_weather = weather
        elif choice == "2":
            view_search_history(storage)
        elif choice == "3":
            generate_and_view_report(storage, last_weather, service)
        elif choice == "4":
            manage_favorites(storage, service, last_weather)
        elif choice == "5":
            compare_two_cities(service, storage)
        elif choice == "6":
            launch_desktop_gui()
        elif choice == "7":
            print(f"\n{GREEN}Thank you for using WeatherWise! Have a wonderful day.{RESET}\n")
            sys.exit(0)
        else:
            print(f"{YELLOW}Invalid option. Please enter a number between 1 and 7.{RESET}")


if __name__ == "__main__":
    if "--gui" in sys.argv:
        launch_desktop_gui()
    else:
        main()
