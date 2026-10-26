"""WeatherWise — Desktop Graphical User Interface.

Built with Python's standard `tkinter` library (no external GUI packages required).
Features:
- Responsive desktop window with automatic foreground elevation
- Asynchronous API requests (non-blocking UI)
- Real-time weather search via `WeatherService`
- File operations: Save favourites (JSON) and export reports (TXT)
- Dynamic weather tips using `random` & unit conversions using `math`
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from weather_service import WeatherService
from storage import StorageEngine
from utils import celsius_to_fahrenheit, celsius_to_kelvin, calculate_wind_chill, get_weather_tip


class WeatherWiseGUI:
    """Tkinter Desktop Application for WeatherWise."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WeatherWise — Desktop Weather Intelligence")
        self.root.geometry("720x680")
        self.root.minsize(620, 560)

        # Force window to foreground so it appears above VS Code / terminal
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(400, lambda: self.root.attributes("-topmost", False))
        self.root.focus_force()

        # Theme Colors (Modern Slate & Cyan Dark Theme)
        self.bg_color = "#0f172a"
        self.card_bg = "#1e293b"
        self.card_sub_bg = "#334155"
        self.text_color = "#f8fafc"
        self.accent_color = "#38bdf8"
        self.accent_blue = "#3b82f6"
        self.muted_color = "#94a3b8"
        self.border_color = "#334155"
        self.success_color = "#10b981"
        self.amber_color = "#f59e0b"

        self.root.configure(bg=self.bg_color)

        self.service = WeatherService()
        self.storage = StorageEngine()
        self.current_weather = None
        self.current_unit = "C"

        self._build_ui()

        # Schedule initial city load after window is fully rendered (prevents startup freezing)
        self.root.after(200, self._load_initial_city)

    def _build_ui(self):
        """Construct all UI widgets."""
        # Top Header Frame
        header = tk.Frame(self.root, bg=self.bg_color, pady=10)
        header.pack(fill=tk.X, padx=22)

        title_row = tk.Frame(header, bg=self.bg_color)
        title_row.pack(fill=tk.X)

        title = tk.Label(
            title_row,
            text="WeatherWise",
            font=("Segoe UI", 22, "bold"),
            fg=self.accent_color,
            bg=self.bg_color
        )
        title.pack(side=tk.LEFT)

        self.unit_btn = tk.Button(
            title_row,
            text="Switch to °F",
            font=("Segoe UI", 9, "bold"),
            bg=self.card_bg,
            fg=self.accent_color,
            activebackground=self.accent_blue,
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.toggle_unit
        )
        self.unit_btn.pack(side=tk.RIGHT)

        subtitle = tk.Label(
            header,
            text="Your weather, intelligently presented • Python Internship Week 3",
            font=("Segoe UI", 9),
            fg=self.muted_color,
            bg=self.bg_color
        )
        subtitle.pack(anchor="w")

        # Search Bar Frame
        search_frame = tk.Frame(self.root, bg=self.bg_color)
        search_frame.pack(fill=tk.X, padx=22, pady=(4, 8))

        self.city_entry = tk.Entry(
            search_frame,
            font=("Segoe UI", 12),
            bg=self.card_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor=self.accent_color,
            highlightbackground=self.border_color
        )
        self.city_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 10))
        self.city_entry.bind("<Return>", lambda e: self.search_city())

        self.search_btn = tk.Button(
            search_frame,
            text="Search",
            font=("Segoe UI", 10, "bold"),
            bg=self.accent_color,
            fg="#0f172a",
            activebackground="#0284c7",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.search_city
        )
        self.search_btn.pack(side=tk.RIGHT)

        # Quick Pick Cities Frame
        quick_frame = tk.Frame(self.root, bg=self.bg_color)
        quick_frame.pack(fill=tk.X, padx=22, pady=(0, 8))

        quick_label = tk.Label(
            quick_frame,
            text="Quick Cities:",
            font=("Segoe UI", 8, "bold"),
            fg=self.muted_color,
            bg=self.bg_color
        )
        quick_label.pack(side=tk.LEFT, padx=(0, 6))

        for city_name in ["London", "Tokyo", "Bengaluru", "New York", "Paris"]:
            btn = tk.Button(
                quick_frame,
                text=city_name,
                font=("Segoe UI", 8),
                bg=self.card_bg,
                fg=self.text_color,
                activebackground=self.accent_blue,
                activeforeground="#fff",
                relief=tk.FLAT,
                padx=8,
                pady=2,
                cursor="hand2",
                command=lambda c=city_name: self.quick_search(c)
            )
            btn.pack(side=tk.LEFT, padx=3)

        # Main Weather Display Card
        self.card = tk.Frame(
            self.root,
            bg=self.card_bg,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.border_color
        )
        self.card.pack(fill=tk.BOTH, expand=True, padx=22, pady=6)

        # City & Location Title
        self.city_label = tk.Label(
            self.card,
            text="Ready to search",
            font=("Segoe UI", 18, "bold"),
            fg=self.text_color,
            bg=self.card_bg
        )
        self.city_label.pack(anchor="w", padx=20, pady=(16, 2))

        self.coords_label = tk.Label(
            self.card,
            text="Enter a city above to fetch live atmospheric data",
            font=("Segoe UI", 9),
            fg=self.muted_color,
            bg=self.card_bg
        )
        self.coords_label.pack(anchor="w", padx=20, pady=(0, 12))

        # Main Temperature & Condition Row
        temp_row = tk.Frame(self.card, bg=self.card_bg)
        temp_row.pack(fill=tk.X, padx=20, pady=(0, 8))

        self.temp_label = tk.Label(
            temp_row,
            text="-- °C",
            font=("Segoe UI", 36, "bold"),
            fg=self.accent_color,
            bg=self.card_bg
        )
        self.temp_label.pack(side=tk.LEFT)

        self.feels_label = tk.Label(
            temp_row,
            text="Feels like: --°\nDay High: --° | Low: --°",
            font=("Segoe UI", 10),
            fg=self.muted_color,
            bg=self.card_bg,
            justify=tk.LEFT
        )
        self.feels_label.pack(side=tk.LEFT, padx=24)

        self.cond_label = tk.Label(
            self.card,
            text="Condition: --",
            font=("Segoe UI", 13, "bold"),
            fg=self.text_color,
            bg=self.card_bg
        )
        self.cond_label.pack(anchor="w", padx=20, pady=(0, 10))

        # Metrics Grid (Humidity, Wind, Pressure, Sun Times)
        metrics_frame = tk.Frame(self.card, bg=self.card_bg)
        metrics_frame.pack(fill=tk.X, padx=20, pady=8)

        self.humidity_label = tk.Label(
            metrics_frame,
            text="💧 Humidity: --%",
            font=("Segoe UI", 10),
            fg=self.text_color,
            bg=self.card_sub_bg,
            padx=12,
            pady=8,
            relief=tk.FLAT
        )
        self.humidity_label.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=4)

        self.wind_label = tk.Label(
            metrics_frame,
            text="💨 Wind: -- km/h",
            font=("Segoe UI", 10),
            fg=self.text_color,
            bg=self.card_sub_bg,
            padx=12,
            pady=8,
            relief=tk.FLAT
        )
        self.wind_label.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=4)

        self.pressure_label = tk.Label(
            metrics_frame,
            text="🧭 Pressure: -- hPa",
            font=("Segoe UI", 10),
            fg=self.text_color,
            bg=self.card_sub_bg,
            padx=12,
            pady=8,
            relief=tk.FLAT
        )
        self.pressure_label.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=4)

        self.sun_label = tk.Label(
            metrics_frame,
            text="🌅 Sun Times: Rise -- | Set --",
            font=("Segoe UI", 10),
            fg=self.text_color,
            bg=self.card_sub_bg,
            padx=12,
            pady=8,
            relief=tk.FLAT
        )
        self.sun_label.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=4)

        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.columnconfigure(1, weight=1)

        # Dynamic Tip Banner (Random & Math logic)
        self.tip_label = tk.Label(
            self.card,
            text="Weather Tip: Check atmospheric conditions before heading outdoors.",
            font=("Segoe UI", 9, "italic"),
            fg="#e2e8f0",
            bg="#334155",
            padx=14,
            pady=8,
            wraplength=560,
            justify=tk.LEFT
        )
        self.tip_label.pack(fill=tk.X, padx=20, pady=(10, 16))

        # Bottom Action Buttons Bar
        btn_bar = tk.Frame(self.root, bg=self.bg_color)
        btn_bar.pack(fill=tk.X, padx=22, pady=(4, 6))

        self.fav_btn = tk.Button(
            btn_bar,
            text="★ Save to Favourites (.json)",
            font=("Segoe UI", 9, "bold"),
            bg=self.card_bg,
            fg=self.amber_color,
            activebackground=self.card_sub_bg,
            activeforeground="#fff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.save_favorite
        )
        self.fav_btn.pack(side=tk.LEFT, padx=(0, 8))

        export_txt_btn = tk.Button(
            btn_bar,
            text="📄 Export Report (.txt)",
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.text_color,
            activebackground=self.card_sub_bg,
            activeforeground="#fff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.export_report
        )
        export_txt_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Segoe UI", 8),
            fg=self.muted_color,
            bg=self.bg_color,
            anchor="w"
        )
        status_bar.pack(fill=tk.X, padx=22, pady=(0, 8))

    def _load_initial_city(self):
        """Load default city weather without freezing window creation."""
        self.city_entry.insert(0, "London")
        self.search_city()

    def quick_search(self, city_name: str):
        """Perform search for a quick-pick city."""
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, city_name)
        self.search_city()

    def toggle_unit(self):
        """Toggle between Celsius and Fahrenheit."""
        self.current_unit = "F" if self.current_unit == "C" else "C"
        self.unit_btn.config(text="Switch to °C" if self.current_unit == "F" else "Switch to °F")
        if self.current_weather:
            self._update_display(self.current_weather)

    def search_city(self):
        """Perform search asynchronously so UI remains 100% responsive."""
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning("Input Required", "Please enter a city name to search.")
            return

        # Show loading status and disable search button temporarily
        self.status_var.set(f"Connecting to API and fetching weather for '{city}'...")
        self.search_btn.config(state=tk.DISABLED, text="Loading...")

        # Run fetch in background thread so GUI never blocks
        threading.Thread(target=self._fetch_thread, args=(city,), daemon=True).start()

    def _fetch_thread(self, city: str):
        """Background thread target for API request."""
        try:
            result = self.service.get_weather(city)
            # Send result back to Tkinter main thread
            self.root.after(0, self._handle_result, result)
        except Exception as exc:
            self.root.after(0, self._handle_error, str(exc))

    def _handle_result(self, result: dict):
        """Process API result on the Tkinter main thread."""
        self.search_btn.config(state=tk.NORMAL, text="Search")

        if not result.get("success"):
            error_msg = result.get("error", "Unable to fetch weather data.")
            self.status_var.set(f"Error: {error_msg}")
            messagebox.showerror("Weather Lookup Error", error_msg)
            return

        self.current_weather = result
        self.status_var.set(f"Successfully retrieved weather for {result['city']} (Logged to search_history.csv)")

        # Persist to CSV search history and JSON cache
        self.storage.log_search_to_csv(result)
        self.storage.cache_weather_snapshot(result)

        self._update_display(result)

    def _handle_error(self, err_text: str):
        """Handle unexpected background thread exceptions."""
        self.search_btn.config(state=tk.NORMAL, text="Search")
        self.status_var.set(f"Network error: {err_text}")
        messagebox.showerror("Connection Error", f"Failed to connect to weather API:\n{err_text}")

    def _update_display(self, data: dict):
        """Update all card labels with the weather data."""
        region = data.get("region", "")
        country = data.get("country", "")
        loc_str = f"{data['city']}, {region}, {country}" if region else f"{data['city']}, {country}"

        self.city_label.config(text=loc_str)
        self.coords_label.config(
            text=f"Lat {data['latitude']}, Lon {data['longitude']} • Source: {data['source']} • Reported: {data['timestamp']}"
        )

        c = data["temperature_c"]
        f = celsius_to_fahrenheit(c)
        feels_c = data["feels_like_c"]
        feels_f = celsius_to_fahrenheit(feels_c)
        max_c = data["temp_max_c"]
        min_c = data["temp_min_c"]
        chill_c = calculate_wind_chill(c, data["wind_speed_kmh"])

        if self.current_unit == "F":
            self.temp_label.config(text=f"{f} °F")
            self.feels_label.config(
                text=f"Feels like: {feels_f} °F | Wind Chill: {celsius_to_fahrenheit(chill_c)} °F\nDay High: {celsius_to_fahrenheit(max_c)} °F | Low: {celsius_to_fahrenheit(min_c)} °F"
            )
        else:
            self.temp_label.config(text=f"{c} °C")
            self.feels_label.config(
                text=f"Feels like: {feels_c} °C | Wind Chill: {chill_c} °C\nDay High: {max_c} °C | Low: {min_c} °C"
            )

        self.cond_label.config(text=f"Condition: {data['condition']}")
        self.humidity_label.config(text=f"💧 Humidity: {data['humidity']}%")
        self.wind_label.config(text=f"💨 Wind: {data['wind_speed_kmh']} km/h")
        self.pressure_label.config(text=f"🧭 Pressure: {data['pressure_hpa']} hPa")

        sunrise = data["sunrise"][-5:] if len(data["sunrise"]) >= 5 else data["sunrise"]
        sunset = data["sunset"][-5:] if len(data["sunset"]) >= 5 else data["sunset"]
        self.sun_label.config(text=f"🌅 Sun Times: Rise {sunrise} | Set {sunset}")

        tip = get_weather_tip(data["condition"], c)
        self.tip_label.config(text=f"Weather Insight [{tip['category']}]: {tip['tip']}")

    def save_favorite(self):
        """Save the currently loaded city to favorites.json."""
        if not self.current_weather:
            messagebox.showinfo("Notice", "Please search for a city first.")
            return

        city = self.current_weather["city"]
        country = self.current_weather.get("country", "")
        added = self.storage.add_favorite(city, country)
        if added:
            messagebox.showinfo("Success", f"'{city}' saved to favourites (.json)!")
            self.status_var.set(f"'{city}' saved to data/favorites.json")
        else:
            messagebox.showinfo("Notice", f"'{city}' is already in your favourites.")

    def export_report(self):
        """Export the current weather to a .txt report."""
        if not self.current_weather:
            messagebox.showinfo("Notice", "Please search for a city first.")
            return

        path = self.storage.save_text_report(self.current_weather)
        if path:
            messagebox.showinfo("Report Exported", f"Weather report written to:\n{path}")
            self.status_var.set(f"Report exported to {path}")
        else:
            messagebox.showerror("Export Error", "Could not export text report.")


def launch_gui():
    """Start the Tkinter GUI event loop."""
    root = tk.Tk()
    app = WeatherWiseGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
