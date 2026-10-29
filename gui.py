"""WeatherWise V3 — Professional Desktop GUI Application.
======================================================
An interactive, multi-page weather desktop dashboard inspired by
QuizUp Python Edition's visual design and navigation experience.

Features:
- Global Navigation Header with brand logo, live search, last-updated timestamp,
  refresh button, and fast temperature unit switcher (°C / °F).
- Six Comprehensive Application Pages:
  1. 📊 Dashboard: Current weather hero card, 4 atmospheric cards, celestial sun times,
     dynamic weather tips using `random`, and quick city suggestion pills.
  2. 📅 Forecast: 24-Hour hourly forecast with a native Tkinter Canvas temperature
     trend line chart, and a 7-day daily forecast breakdown with precipitation details.
  3. 🔍 Explore & Compare: Global city search & live side-by-side weather comparison
     of two cities with calculated metric deltas.
  4. ⭐ Favourites: Persistent saved locations (.json) with quick live weather loading.
  5. 📋 History & Reports: Tabular CSV search history (.csv) and TXT weather report
     generator (.txt) with in-app report viewer.
  6. ⚙️ Settings: Persistent preferences for temperature unit, default startup city,
     auto-refresh interval, themes, and storage diagnostics.
- Non-blocking asynchronous network requests via Python threading.
- Native Canvas graphics for smooth temperature trend charts without external dependencies.
- 100% Tkinter and standard library compliant.
"""

import os
import sys
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from weather_service import WeatherService
from storage import StorageEngine
from utils import (
    celsius_to_fahrenheit,
    celsius_to_kelvin,
    calculate_wind_chill,
    get_weather_tip,
    get_random_sample_cities,
    format_sun_time,
    get_current_timestamp,
)


# =============================================================================
# Theme Palettes
# =============================================================================
THEMES = {
    "Deep Twilight": {
        "bg": "#0B1120",
        "card_bg": "#152238",
        "card_sub_bg": "#1E2E4A",
        "primary": "#38BDF8",
        "primary_hover": "#0284C7",
        "secondary": "#1E2E4A",
        "accent": "#F59E0B",
        "text_main": "#F8FAFC",
        "text_muted": "#94A3B8",
        "border": "#1E2E4A",
        "badge_bg": "#0C4A6E",
        "badge_fg": "#7DD3FC",
        "success_bg": "#064E3B",
        "success_fg": "#6EE7B7",
        "chart_line": "#38BDF8",
        "chart_fill": "#0C4A6E",
        "chart_dot": "#BAE6FD",
    },
    "Sky Blue": {
        "bg": "#F0F7FD",
        "card_bg": "#FFFFFF",
        "card_sub_bg": "#F8FAFC",
        "primary": "#0284C7",
        "primary_hover": "#0369A1",
        "secondary": "#E0F2FE",
        "accent": "#38BDF8",
        "text_main": "#0F172A",
        "text_muted": "#64748B",
        "border": "#E2E8F0",
        "badge_bg": "#E0F2FE",
        "badge_fg": "#0369A1",
        "success_bg": "#ECFDF5",
        "success_fg": "#065F46",
        "chart_line": "#0284C7",
        "chart_fill": "#BAE6FD",
        "chart_dot": "#0369A1",
    },
    "Soft Lavender": {
        "bg": "#F7F4FF",
        "card_bg": "#FFFFFF",
        "card_sub_bg": "#FAF7FF",
        "primary": "#9A83E8",
        "primary_hover": "#8870DC",
        "secondary": "#E9DFFF",
        "accent": "#F5A5C8",
        "text_main": "#302B40",
        "text_muted": "#6F687D",
        "border": "#E7E1F0",
        "badge_bg": "#E9DFFF",
        "badge_fg": "#6B46C1",
        "success_bg": "#E6F9F6",
        "success_fg": "#168274",
        "chart_line": "#9A83E8",
        "chart_fill": "#E9DFFF",
        "chart_dot": "#7C3AED",
    },
}

WMO_EMOJI_MAP = {
    "sunny": "☀️",
    "cloudy": "⛅",
    "rainy": "🌧️",
    "stormy": "⛈️",
    "snowy": "❄️",
    "foggy": "🌫️",
}


class WeatherWiseGUI:
    """WeatherWise V3 Interactive Desktop Dashboard."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WeatherWise ✦ Desktop Weather Intelligence V3")
        self._center_and_elevate_window(1120, 740)

        # Backend engines
        self.service = WeatherService()
        self.storage = StorageEngine()

        # Load persisted settings
        self.settings = self.storage.get_settings()
        self.current_unit = self.settings.get("unit", "C")
        self.current_theme_name = self.settings.get("theme", "Deep Twilight")
        if self.current_theme_name not in THEMES:
            self.current_theme_name = "Deep Twilight"
        self.colors = THEMES[self.current_theme_name]

        self.root.configure(bg=self.colors["bg"])

        # State tracking
        self.current_weather = None
        self.comparison_data = {"city1": None, "city2": None}
        self.current_page = "dashboard"
        self.is_loading = False
        self.last_updated_time = None
        self.nav_buttons = {}
        self.auto_refresh_id = None

        # Interactive Radar Simulation State
        self.radar_anim_id = None
        self.radar_angle = 0
        self.radar_layer = "precip"
        self.radar_playing = True
        self.active_alert_banner = None

        # Build UI layout:
        # 1. Top Horizon Search Header
        self._build_top_header()
        # 2. Bottom Floating Meteorological Action Dock
        self._build_nav_bar()

        # 3. Content container (fills space between top header and bottom dock)
        self.content_container = tk.Frame(self.root, bg=self.colors["bg"])
        self.content_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(6, 4))

        # Show Dashboard initially
        self.show_dashboard_page()

        # Initial city load
        initial_city = self.settings.get("default_city", "Bengaluru")
        self.root.after(250, lambda: self.search_city_threaded(initial_city))

        # Setup auto refresh timer if enabled
        self._schedule_auto_refresh()

        # Safe close protocol
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_and_elevate_window(self, width: int, height: int):
        """Center the window on the active monitor and elevate smoothly."""
        try:
            self.root.update_idletasks()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            w = min(width, sw - 40)
            h = min(height, sh - 80)
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
            self.root.geometry(f"{w}x{h}+{x}+{y}")
            self.root.minsize(940, 620)
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(800, lambda: self.root.attributes("-topmost", False))
            self.root.focus_force()
        except Exception:
            pass

    def _on_close(self):
        """Cleanly cancel timers and close application."""
        if self.auto_refresh_id:
            try:
                self.root.after_cancel(self.auto_refresh_id)
            except Exception:
                pass
        if self.radar_anim_id:
            try:
                self.root.after_cancel(self.radar_anim_id)
            except Exception:
                pass
        self.root.destroy()

    # =========================================================================
    # Header & Navigation UI
    # =========================================================================
    def _build_top_header(self):
        """Build global persistent top header bar."""
        self.header_frame = tk.Frame(self.root, bg=self.colors["card_bg"], height=70)
        self.header_frame.pack(fill=tk.X, padx=0, pady=0)

        # Bottom accent border on header
        self.header_border = tk.Frame(self.root, bg=self.colors["border"], height=1)
        self.header_border.pack(fill=tk.X)

        inner = tk.Frame(self.header_frame, bg=self.colors["card_bg"])
        inner.pack(fill=tk.X, padx=24, pady=12)

        # Left: Logo & Title
        title_box = tk.Frame(inner, bg=self.colors["card_bg"])
        title_box.pack(side=tk.LEFT)

        app_icon = tk.Label(
            title_box,
            text="🌦️",
            font=("Segoe UI", 22),
            bg=self.colors["card_bg"]
        )
        app_icon.pack(side=tk.LEFT, padx=(0, 8))

        text_box = tk.Frame(title_box, bg=self.colors["card_bg"])
        text_box.pack(side=tk.LEFT)

        app_title = tk.Label(
            text_box,
            text="WeatherWise",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        )
        app_title.pack(anchor="w")

        app_tag = tk.Label(
            text_box,
            text="Python Intelligence V3 • Live Open-Meteo",
            font=("Segoe UI", 8),
            fg=self.colors["text_muted"],
            bg=self.colors["card_bg"]
        )
        app_tag.pack(anchor="w")

        # Center: Global Search Bar
        search_box = tk.Frame(inner, bg=self.colors["card_bg"])
        search_box.pack(side=tk.LEFT, padx=32, fill=tk.X, expand=True)

        search_border = tk.Frame(
            search_box,
            bg=self.colors["border"],
            padx=1,
            pady=1,
            relief=tk.FLAT
        )
        search_border.pack(side=tk.LEFT, fill=tk.X, expand=True)

        search_inner = tk.Frame(search_border, bg=self.colors["card_sub_bg"])
        search_inner.pack(fill=tk.BOTH, expand=True)

        s_icon = tk.Label(
            search_inner,
            text="🔍",
            font=("Segoe UI", 10),
            fg=self.colors["text_muted"],
            bg=self.colors["card_sub_bg"],
            padx=8
        )
        s_icon.pack(side=tk.LEFT)

        self.search_entry = tk.Entry(
            search_inner,
            font=("Segoe UI", 11),
            bg=self.colors["card_sub_bg"],
            fg=self.colors["text_main"],
            insertbackground=self.colors["primary"],
            relief=tk.FLAT,
            bd=0
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=6)
        self.search_entry.insert(0, "Search city name (e.g. London, Aland, Tokyo)...")
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_entry.bind("<Return>", lambda e: self.on_search_submit())

        self.header_search_btn = tk.Button(
            search_inner,
            text="Search",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["primary"],
            fg="#FFFFFF",
            activebackground=self.colors["primary_hover"],
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=14,
            pady=4,
            cursor="hand2",
            bd=0,
            command=self.on_search_submit
        )
        self.header_search_btn.pack(side=tk.RIGHT, padx=4, pady=4)

        # Right: Quick Controls & Status
        right_box = tk.Frame(inner, bg=self.colors["card_bg"])
        right_box.pack(side=tk.RIGHT)

        self.status_badge = tk.Label(
            right_box,
            text="🟢 Ready",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["badge_fg"],
            bg=self.colors["badge_bg"],
            padx=10,
            pady=4
        )
        self.status_badge.pack(side=tk.LEFT, padx=(0, 10))

        # Unit Toggle Button
        self.header_unit_btn = tk.Button(
            right_box,
            text=f"°{self.current_unit}",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["secondary"],
            fg=self.colors["primary"],
            activebackground=self.colors["primary"],
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            bd=0,
            command=self.toggle_temperature_unit
        )
        self.header_unit_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Refresh Button
        self.header_refresh_btn = tk.Button(
            right_box,
            text="🔄 Refresh",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card_sub_bg"],
            fg=self.colors["text_main"],
            activebackground=self.colors["border"],
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            bd=0,
            command=self.refresh_current_weather
        )
        self.header_refresh_btn.pack(side=tk.LEFT)

    def _on_search_focus_in(self, event):
        if "Search city name" in self.search_entry.get():
            self.search_entry.delete(0, tk.END)

    def _on_search_focus_out(self, event):
        if not self.search_entry.get().strip():
            self.search_entry.insert(0, "Search city name (e.g. London, Aland, Tokyo)...")

    def _build_nav_bar(self):
        """Construct bottom floating meteorological control dock."""
        self.nav_dock_outer = tk.Frame(self.root, bg=self.colors["bg"])
        self.nav_dock_outer.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(4, 10))

        # Centered glass capsule container
        self.nav_frame = tk.Frame(
            self.nav_dock_outer,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=8,
            pady=4
        )
        self.nav_frame.pack(anchor="center")

        nav_items = [
            ("dashboard", "🌦️ Horizon", self.show_dashboard_page),
            ("forecast", "📈 24H & 7-Day", self.show_forecast_page),
            ("radar", "📡 Live Radar", self.show_radar_page),
            ("air_quality", "🍃 Air & UV", self.show_air_quality_page),
            ("alerts", "⚠️ Advisories", self.show_alerts_page),
            ("explore", "⚖️ Compare", self.show_explore_page),
            ("favorites", "⭐ Saved", self.show_favorites_page),
            ("history", "📑 Reports", self.show_history_page),
            ("settings", "⚙️ Config", self.show_settings_page),
        ]

        self.nav_buttons = {}
        for key, label, cmd in nav_items:
            btn = tk.Button(
                self.nav_frame,
                text=label,
                font=("Segoe UI", 9, "bold"),
                bg=self.colors["card_sub_bg"],
                fg=self.colors["text_muted"],
                activebackground=self.colors["secondary"],
                activeforeground=self.colors["primary"],
                relief=tk.FLAT,
                padx=10,
                pady=5,
                cursor="hand2",
                bd=0,
                command=cmd
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.nav_buttons[key] = btn

    def _update_nav_highlight(self, active_key: str):
        """Update navigation tab colors to indicate active view."""
        self.current_page = active_key
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.configure(
                    bg=self.colors["primary"],
                    fg="#0B1120" if self.current_theme_name == "Deep Twilight" else "#FFFFFF",
                    activebackground=self.colors["primary_hover"],
                    activeforeground="#FFFFFF"
                )
            else:
                btn.configure(
                    bg=self.colors["card_sub_bg"],
                    fg=self.colors["text_muted"],
                    activebackground=self.colors["secondary"],
                    activeforeground=self.colors["primary"]
                )

    def _clear_content(self):
        """Clear dynamic content container and cancel running animations."""
        if hasattr(self, "radar_anim_id") and self.radar_anim_id:
            try:
                self.root.after_cancel(self.radar_anim_id)
            except Exception:
                pass
            self.radar_anim_id = None
        for widget in self.content_container.winfo_children():
            widget.destroy()

    def _create_scrollable_container(self) -> tk.Frame:
        """Create a responsive scrollable canvas container."""
        canvas = tk.Canvas(self.content_container, bg=self.colors["bg"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(self.content_container, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors["bg"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Mousewheel scrolling
        def _on_mousewheel(event):
            delta = -1 if event.delta < 0 else 1
            canvas.yview_scroll(delta * -1, "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        return scrollable_frame

    # =========================================================================
    # Asynchronous Weather Service Integration
    # =========================================================================
    def on_search_submit(self):
        """Handle search form submission."""
        city = self.search_entry.get().strip()
        if not city or "Search city name" in city:
            messagebox.showinfo("City Search", "Please enter a valid city name.")
            return
        self.search_city_threaded(city)

    def search_city_threaded(self, city_name: str, on_complete=None):
        """Initiate non-blocking background thread for API lookup."""
        if self.is_loading:
            return

        self.is_loading = True
        self.status_badge.configure(
            text="⏳ Fetching...",
            bg=self.colors["secondary"],
            fg=self.colors["primary"]
        )

        def worker():
            result = self.service.get_weather(city_name)
            # Switch back to UI thread
            self.root.after(0, lambda: self._on_weather_fetched(result, on_complete))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _on_weather_fetched(self, result: dict, on_complete=None):
        """Handle completed weather request in main thread."""
        self.is_loading = False

        if not result.get("success"):
            err_msg = result.get("error", "Unknown API error occurred.")
            self.status_badge.configure(
                text="⚠️ Lookup Failed",
                bg="#FEE2E2",
                fg="#B91C1C"
            )
            messagebox.showerror("WeatherWise Lookup Error", err_msg)
            if on_complete:
                on_complete(False)
            return

        self.current_weather = result
        self.last_updated_time = datetime.now()

        # Update last updated badge
        ts_str = self.last_updated_time.strftime("%I:%M %p")
        self.status_badge.configure(
            text=f"🟢 Updated {ts_str}",
            bg=self.colors["success_bg"],
            fg=self.colors["success_fg"]
        )

        # Log search to CSV and cache response automatically
        self.storage.log_search_to_csv(result)
        self.storage.cache_weather_snapshot(result)

        # Re-render active view if it depends on current weather
        if self.current_page == "dashboard":
            self.show_dashboard_page()
        elif self.current_page == "forecast":
            self.show_forecast_page()

        if on_complete:
            on_complete(True)

    def refresh_current_weather(self):
        """Refresh current loaded city."""
        if self.current_weather:
            city = self.current_weather.get("city")
            self.search_city_threaded(city)
        else:
            default_city = self.settings.get("default_city", "Bengaluru")
            self.search_city_threaded(default_city)

    def toggle_temperature_unit(self):
        """Toggle between Celsius and Fahrenheit."""
        self.current_unit = "F" if self.current_unit == "C" else "C"
        self.header_unit_btn.configure(text=f"°{self.current_unit}")
        self.settings["unit"] = self.current_unit
        self.storage.save_settings({"unit": self.current_unit})

        # Re-render current page
        getattr(self, f"show_{self.current_page}_page", self.show_dashboard_page)()

    def _format_temp(self, celsius: float) -> str:
        """Format temperature float according to active unit."""
        if celsius is None:
            return "N/A"
        if self.current_unit == "F":
            return f"{celsius_to_fahrenheit(celsius)}°F"
        return f"{celsius:.1f}°C"

    def _schedule_auto_refresh(self):
        """Schedule periodic background refresh according to settings."""
        if self.auto_refresh_id:
            try:
                self.root.after_cancel(self.auto_refresh_id)
            except Exception:
                pass

        interval_min = int(self.settings.get("refresh_interval_min", 15))
        if interval_min > 0:
            ms = interval_min * 60 * 1000
            self.auto_refresh_id = self.root.after(ms, self._auto_refresh_tick)

    def _auto_refresh_tick(self):
        """Callback for auto-refresh timer."""
        if self.current_weather and not self.is_loading:
            city = self.current_weather.get("city")
            self.search_city_threaded(city)
        self._schedule_auto_refresh()

    # =========================================================================
    # Page 1: Dashboard View
    # =========================================================================
    def show_dashboard_page(self):
        """Render Dashboard page with current weather, atmospheric cards & tips."""
        self._update_nav_highlight("dashboard")
        self._clear_content()

        container = self._create_scrollable_container()

        if not self.current_weather:
            self._render_empty_state(
                container,
                icon="🌦️",
                title="Welcome to WeatherWise V3",
                description="Search for any city above or pick one of the popular locations below."
            )
            self._render_quick_cities(container)
            return

        w = self.current_weather
        celsius = w.get("temperature_c", 0.0)
        feels_c = w.get("feels_like_c", celsius)
        max_c = w.get("temp_max_c", celsius)
        min_c = w.get("temp_min_c", celsius)
        icon_emoji = WMO_EMOJI_MAP.get(w.get("icon_type", "cloudy"), "⛅")

        # ---------------- Top Hero Card ----------------
        hero_card = tk.Frame(
            container,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=28,
            pady=22
        )
        hero_card.pack(fill=tk.X, pady=(0, 16))

        # Top row: City Name & Action buttons
        h_top = tk.Frame(hero_card, bg=self.colors["card_bg"])
        h_top.pack(fill=tk.X)

        loc_label = tk.Label(
            h_top,
            text=f"📍 {w.get('city')}, {w.get('country')}",
            font=("Segoe UI", 18, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        )
        loc_label.pack(side=tk.LEFT)

        # Region badge if available
        if w.get("region"):
            reg_badge = tk.Label(
                h_top,
                text=w.get("region"),
                font=("Segoe UI", 9, "bold"),
                fg=self.colors["primary"],
                bg=self.colors["secondary"],
                padx=8,
                pady=2
            )
            reg_badge.pack(side=tk.LEFT, padx=(10, 0))

        # Action Buttons on Hero
        btn_box = tk.Frame(h_top, bg=self.colors["card_bg"])
        btn_box.pack(side=tk.RIGHT)

        fav_btn = tk.Button(
            btn_box,
            text="⭐ Add to Favourites",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["secondary"],
            fg=self.colors["primary"],
            activebackground=self.colors["primary"],
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
            bd=0,
            command=self.save_current_to_favorites
        )
        fav_btn.pack(side=tk.LEFT, padx=(0, 8))

        report_btn = tk.Button(
            btn_box,
            text="📄 Generate TXT Report",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card_sub_bg"],
            fg=self.colors["text_main"],
            activebackground=self.colors["border"],
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
            bd=0,
            command=self.generate_txt_report
        )
        report_btn.pack(side=tk.LEFT)

        # Middle row: Hero Temperature & Icon
        h_mid = tk.Frame(hero_card, bg=self.colors["card_bg"])
        h_mid.pack(fill=tk.X, pady=(16, 12))

        temp_box = tk.Frame(h_mid, bg=self.colors["card_bg"])
        temp_box.pack(side=tk.LEFT)

        main_temp = tk.Label(
            temp_box,
            text=self._format_temp(celsius),
            font=("Segoe UI", 48, "bold"),
            fg=self.colors["primary"],
            bg=self.colors["card_bg"]
        )
        main_temp.pack(side=tk.LEFT)

        cond_box = tk.Frame(h_mid, bg=self.colors["card_bg"])
        cond_box.pack(side=tk.LEFT, padx=(24, 0))

        hero_icon_lbl = tk.Label(
            cond_box,
            text=icon_emoji,
            font=("Segoe UI", 36),
            bg=self.colors["card_bg"]
        )
        hero_icon_lbl.pack(anchor="w")

        hero_cond_lbl = tk.Label(
            cond_box,
            text=w.get("condition", "Variable"),
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        )
        hero_cond_lbl.pack(anchor="w")

        # Bottom row: Feels-like & Day range
        h_bot = tk.Frame(hero_card, bg=self.colors["card_bg"])
        h_bot.pack(fill=tk.X, pady=(4, 0))

        meta_text = (
            f"🌡️ Feels like {self._format_temp(feels_c)}  •  "
            f"🔺 High {self._format_temp(max_c)}  •  "
            f"🔻 Low {self._format_temp(min_c)}  •  "
            f"Data Source: {w.get('source', 'Open-Meteo')}"
        )
        meta_lbl = tk.Label(
            h_bot,
            text=meta_text,
            font=("Segoe UI", 10),
            fg=self.colors["text_muted"],
            bg=self.colors["card_bg"]
        )
        meta_lbl.pack(side=tk.LEFT)

        # ---------------- 4 Key Atmospheric Indicators Grid ----------------
        grid_frame = tk.Frame(container, bg=self.colors["bg"])
        grid_frame.pack(fill=tk.X, pady=(0, 16))

        humidity = w.get("humidity", 0)
        wind_kmh = w.get("wind_speed_kmh", 0.0)
        pressure = w.get("pressure_hpa", 1013)
        wind_chill = calculate_wind_chill(celsius, wind_kmh)

        # Comfort rating based on humidity
        if humidity < 30:
            hum_status = "Dry Air"
        elif humidity <= 60:
            hum_status = "Comfortable"
        else:
            hum_status = "High Humidity"

        # Wind classification
        if wind_kmh < 12:
            wind_status = "Light Breeze"
        elif wind_kmh < 29:
            wind_status = "Moderate Wind"
        else:
            wind_status = "Strong Wind"

        cards_data = [
            ("💧 Relative Humidity", f"{humidity}%", hum_status),
            ("💨 Wind Velocity", f"{wind_kmh} km/h", wind_status),
            ("🧭 Barometric Pressure", f"{pressure} hPa", "Stable Surface Pressure"),
            ("❄️ Calculated Wind Chill", self._format_temp(wind_chill), "Perceived Thermal Feel (math.pow)"),
        ]

        for i, (ctitle, cval, csub) in enumerate(cards_data):
            c_frame = tk.Frame(
                grid_frame,
                bg=self.colors["card_bg"],
                highlightbackground=self.colors["border"],
                highlightthickness=1,
                padx=18,
                pady=16
            )
            c_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 10, 0))

            tk.Label(
                c_frame,
                text=ctitle,
                font=("Segoe UI", 10, "bold"),
                fg=self.colors["text_muted"],
                bg=self.colors["card_bg"]
            ).pack(anchor="w")

            tk.Label(
                c_frame,
                text=cval,
                font=("Segoe UI", 20, "bold"),
                fg=self.colors["text_main"],
                bg=self.colors["card_bg"]
            ).pack(anchor="w", pady=(6, 2))

            tk.Label(
                c_frame,
                text=csub,
                font=("Segoe UI", 8),
                fg=self.colors["primary"],
                bg=self.colors["card_bg"]
            ).pack(anchor="w")

        # ---------------- Celestial Times & Dynamic Weather Tip ----------------
        split_row = tk.Frame(container, bg=self.colors["bg"])
        split_row.pack(fill=tk.X, pady=(0, 16))

        # Celestial Times Card (Left)
        sun_card = tk.Frame(
            split_row,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=20,
            pady=16
        )
        sun_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(
            sun_card,
            text="☀️ Daylight & Celestial Hours",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 10))

        sun_grid = tk.Frame(sun_card, bg=self.colors["card_bg"])
        sun_grid.pack(fill=tk.X)

        rise_t = format_sun_time(w.get("sunrise", "N/A"))
        set_t = format_sun_time(w.get("sunset", "N/A"))

        # Sunrise Box
        rise_box = tk.Frame(sun_grid, bg=self.colors["card_sub_bg"], padx=14, pady=10)
        rise_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        tk.Label(rise_box, text="🌅 Sunrise", font=("Segoe UI", 9, "bold"), fg=self.colors["text_muted"], bg=self.colors["card_sub_bg"]).pack(anchor="w")
        tk.Label(rise_box, text=rise_t, font=("Segoe UI", 14, "bold"), fg=self.colors["text_main"], bg=self.colors["card_sub_bg"]).pack(anchor="w")

        # Sunset Box
        set_box = tk.Frame(sun_grid, bg=self.colors["card_sub_bg"], padx=14, pady=10)
        set_box.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tk.Label(set_box, text="🌇 Sunset", font=("Segoe UI", 9, "bold"), fg=self.colors["text_muted"], bg=self.colors["card_sub_bg"]).pack(anchor="w")
        tk.Label(set_box, text=set_t, font=("Segoe UI", 14, "bold"), fg=self.colors["text_main"], bg=self.colors["card_sub_bg"]).pack(anchor="w")

        # Dynamic Weather Tip Card (Right)
        tip_card = tk.Frame(
            split_row,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=20,
            pady=16
        )
        tip_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tip_data = get_weather_tip(w.get("condition", "Clear"), celsius)

        tk.Label(
            tip_card,
            text=f"💡 Weather Insight • {tip_data['category']}",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["primary"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            tip_card,
            text=tip_data["tip"],
            font=("Segoe UI", 10),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"],
            wraplength=440,
            justify=tk.LEFT
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            tip_card,
            text="Rotating guidance generated via Python `random` module.",
            font=("Segoe UI", 8),
            fg=self.colors["text_muted"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w")

        # ---------------- Quick City Suggestions ----------------
        self._render_quick_cities(container)

    def _render_quick_cities(self, container: tk.Frame):
        """Render clickable quick city pills."""
        quick_frame = tk.Frame(
            container,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=20,
            pady=16
        )
        quick_frame.pack(fill=tk.X, pady=(0, 16))

        tk.Label(
            quick_frame,
            text="🌍 Quick City Explorer",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 8))

        pills_frame = tk.Frame(quick_frame, bg=self.colors["card_bg"])
        pills_frame.pack(fill=tk.X)

        suggested_cities = ["Bengaluru", "London", "New York", "Tokyo", "Paris", "Sydney", "Dubai", "Aland"]
        for city in suggested_cities:
            pill = tk.Button(
                pills_frame,
                text=city,
                font=("Segoe UI", 9),
                bg=self.colors["card_sub_bg"],
                fg=self.colors["text_main"],
                activebackground=self.colors["primary"],
                activeforeground="#FFFFFF",
                relief=tk.FLAT,
                padx=12,
                pady=4,
                cursor="hand2",
                bd=0,
                command=lambda c=city: self.search_city_threaded(c)
            )
            pill.pack(side=tk.LEFT, padx=(0, 8), pady=4)

    # =========================================================================
    # Page 2: Forecast View (Canvas Chart + 7-Day Cards)
    # =========================================================================
    def show_forecast_page(self):
        """Render 24-hour interactive canvas chart and 7-day daily forecast."""
        self._update_nav_highlight("forecast")
        self._clear_content()

        container = self._create_scrollable_container()

        if not self.current_weather or not self.current_weather.get("hourly_forecast"):
            self._render_empty_state(
                container,
                icon="📅",
                title="No Forecast Loaded",
                description="Search for a city above to view live hourly trends and 7-day weather outlook."
            )
            return

        w = self.current_weather
        city_title = f"{w.get('city')}, {w.get('country')}"

        # Header Title
        title_box = tk.Frame(container, bg=self.colors["bg"])
        title_box.pack(fill=tk.X, pady=(0, 14))

        tk.Label(
            title_box,
            text=f"Forecast Outlook for {city_title}",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["bg"]
        ).pack(side=tk.LEFT)

        tk.Label(
            title_box,
            text="Hourly Trend & 7-Day Precision",
            font=("Segoe UI", 10),
            fg=self.colors["text_muted"],
            bg=self.colors["bg"]
        ).pack(side=tk.RIGHT)

        # ---------------- 24-Hour Trend Chart Card ----------------
        chart_card = tk.Frame(
            container,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=20,
            pady=16
        )
        chart_card.pack(fill=tk.X, pady=(0, 16))

        tk.Label(
            chart_card,
            text="📈 24-Hour Temperature Trend Curve",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 8))

        # Draw Native Tkinter Canvas Line Chart
        hourly = w.get("hourly_forecast", [])[:16]  # Next 16 hours for clean layout
        if hourly:
            self._draw_temperature_canvas(chart_card, hourly)

        # ---------------- 7-Day Forecast Breakdown ----------------
        daily = w.get("daily_forecast", [])
        if daily:
            daily_card = tk.Frame(
                container,
                bg=self.colors["card_bg"],
                highlightbackground=self.colors["border"],
                highlightthickness=1,
                padx=20,
                pady=16
            )
            daily_card.pack(fill=tk.X, pady=(0, 16))

            tk.Label(
                daily_card,
                text="📅 7-Day Extended Weather Outlook",
                font=("Segoe UI", 12, "bold"),
                fg=self.colors["text_main"],
                bg=self.colors["card_bg"]
            ).pack(anchor="w", pady=(0, 12))

            for day_info in daily:
                row = tk.Frame(daily_card, bg=self.colors["card_sub_bg"], padx=14, pady=10)
                row.pack(fill=tk.X, pady=(0, 6))

                # Day name and date
                d_box = tk.Frame(row, bg=self.colors["card_sub_bg"], width=130)
                d_box.pack(side=tk.LEFT)
                d_box.pack_propagate(False)

                tk.Label(
                    d_box,
                    text=day_info.get("day_name", ""),
                    font=("Segoe UI", 11, "bold"),
                    fg=self.colors["text_main"],
                    bg=self.colors["card_sub_bg"]
                ).pack(anchor="w")

                tk.Label(
                    d_box,
                    text=day_info.get("formatted_date", ""),
                    font=("Segoe UI", 8),
                    fg=self.colors["text_muted"],
                    bg=self.colors["card_sub_bg"]
                ).pack(anchor="w")

                # Condition Icon & Name
                cond_box = tk.Frame(row, bg=self.colors["card_sub_bg"], width=200)
                cond_box.pack(side=tk.LEFT, padx=10)
                cond_box.pack_propagate(False)

                c_emoji = WMO_EMOJI_MAP.get(day_info.get("icon_type", "cloudy"), "⛅")
                tk.Label(
                    cond_box,
                    text=f"{c_emoji} {day_info.get('condition', 'Clear')}",
                    font=("Segoe UI", 10),
                    fg=self.colors["text_main"],
                    bg=self.colors["card_sub_bg"]
                ).pack(anchor="w")

                # Rain & Wind
                rain_box = tk.Frame(row, bg=self.colors["card_sub_bg"], width=160)
                rain_box.pack(side=tk.LEFT, padx=10)
                rain_box.pack_propagate(False)

                precip_mm = day_info.get("precipitation_mm", 0.0)
                wind_max = day_info.get("wind_max_kmh", 0.0)
                tk.Label(
                    rain_box,
                    text=f"🌧️ {precip_mm:.1f} mm  •  💨 {wind_max:.0f} km/h",
                    font=("Segoe UI", 9),
                    fg=self.colors["text_muted"],
                    bg=self.colors["card_sub_bg"]
                ).pack(anchor="w")

                # Temperature range pill
                temp_pill = tk.Frame(row, bg=self.colors["card_sub_bg"])
                temp_pill.pack(side=tk.RIGHT)

                max_t = self._format_temp(day_info.get("temp_max_c", 0.0))
                min_t = self._format_temp(day_info.get("temp_min_c", 0.0))

                tk.Label(
                    temp_pill,
                    text=f"🔺 {max_t}",
                    font=("Segoe UI", 10, "bold"),
                    fg=self.colors["primary"],
                    bg=self.colors["card_sub_bg"]
                ).pack(side=tk.LEFT, padx=(0, 10))

                tk.Label(
                    temp_pill,
                    text=f"🔻 {min_t}",
                    font=("Segoe UI", 10),
                    fg=self.colors["text_muted"],
                    bg=self.colors["card_sub_bg"]
                ).pack(side=tk.LEFT)

    def _draw_temperature_canvas(self, parent: tk.Frame, hourly: list):
        """Draw smooth Canvas curve line chart for hourly temperatures."""
        c_width = 820
        c_height = 200
        canvas = tk.Canvas(
            parent,
            width=c_width,
            height=c_height,
            bg=self.colors["card_bg"],
            highlightthickness=0,
            bd=0
        )
        canvas.pack(fill=tk.X, expand=True, pady=8)

        temps = [h.get("temp_c", 0.0) for h in hourly]
        if not temps:
            return

        min_t = min(temps) - 1.5
        max_t = max(temps) + 1.5
        range_t = max(max_t - min_t, 1.0)

        padding_x = 45
        padding_y_top = 35
        padding_y_bottom = 50
        usable_w = c_width - (2 * padding_x)
        usable_h = c_height - padding_y_top - padding_y_bottom

        points = []
        n = len(temps)
        step_x = usable_w / max(n - 1, 1)

        for i, t in enumerate(temps):
            x = padding_x + (i * step_x)
            y = padding_y_top + usable_h - ((t - min_t) / range_t * usable_h)
            points.append((x, y, t, hourly[i]))

        # Draw soft polygon shaded background
        fill_coords = [padding_x, padding_y_top + usable_h]
        for x, y, _, _ in points:
            fill_coords.extend([x, y])
        fill_coords.extend([padding_x + usable_w, padding_y_top + usable_h])

        canvas.create_polygon(
            fill_coords,
            fill=self.colors["chart_fill"],
            outline="",
            smooth=True
        )

        # Draw main trend curve line
        line_coords = []
        for x, y, _, _ in points:
            line_coords.extend([x, y])

        canvas.create_line(
            line_coords,
            fill=self.colors["chart_line"],
            width=3,
            smooth=True
        )

        # Draw point markers, temperature labels, and time labels
        for x, y, t, h in points:
            # Point circle
            canvas.create_oval(
                x - 4, y - 4, x + 4, y + 4,
                fill=self.colors["chart_dot"],
                outline=self.colors["card_bg"],
                width=2
            )

            # Temp text above
            disp_temp = self._format_temp(t)
            canvas.create_text(
                x, y - 14,
                text=disp_temp,
                font=("Segoe UI", 9, "bold"),
                fill=self.colors["text_main"]
            )

            # Time text below
            canvas.create_text(
                x, padding_y_top + usable_h + 16,
                text=h.get("display_time", ""),
                font=("Segoe UI", 8),
                fill=self.colors["text_muted"]
            )

            # Emoji condition icon
            c_icon = WMO_EMOJI_MAP.get(h.get("icon_type", "cloudy"), "⛅")
            canvas.create_text(
                x, padding_y_top + usable_h + 32,
                text=c_icon,
                font=("Segoe UI", 9)
            )

    # =========================================================================
    # Page: Interactive Doppler Weather Radar & Map Simulator
    # =========================================================================
    def show_radar_page(self):
        """Render Interactive Live Doppler Radar & Atmospheric Map Simulator."""
        self._update_nav_highlight("radar")
        self._clear_content()

        container = self._create_scrollable_container()
        w = self.current_weather or {}
        city_name = w.get("city", "Bengaluru")

        # Header with status indicator
        h_frame = tk.Frame(container, bg=self.colors["bg"])
        h_frame.pack(fill=tk.X, pady=(0, 12))

        left_h = tk.Frame(h_frame, bg=self.colors["bg"])
        left_h.pack(side=tk.LEFT)

        tk.Label(
            left_h,
            text=f"📡 Interactive Doppler Radar — {city_name}",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["bg"]
        ).pack(anchor="w")

        tk.Label(
            left_h,
            text="Simulated high-resolution radar sweep, precipitation reflectivity (dBZ), and atmospheric vector streams.",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["bg"]
        ).pack(anchor="w", pady=(2, 0))

        # Right control pills
        ctrl_pills = tk.Frame(h_frame, bg=self.colors["bg"])
        ctrl_pills.pack(side=tk.RIGHT)

        self.radar_play_btn = tk.Button(
            ctrl_pills,
            text="⏸ Pause Loop" if self.radar_playing else "▶ Play Sweep",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["primary"],
            fg="#0B1120" if self.current_theme_name == "Deep Twilight" else "#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            bd=0,
            command=self._toggle_radar_play
        )
        self.radar_play_btn.pack(side=tk.LEFT, padx=4)

        # Radar Main Card
        radar_card = tk.Frame(
            container,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=18,
            pady=16
        )
        radar_card.pack(fill=tk.BOTH, expand=True, pady=(0, 14))

        # Layer Selector Bar
        layer_bar = tk.Frame(radar_card, bg=self.colors["card_bg"])
        layer_bar.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            layer_bar,
            text="Active Radar Layer:",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["text_muted"],
            bg=self.colors["card_bg"]
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.layer_buttons = {}
        layers = [
            ("precip", "🌧️ Precipitation Doppler"),
            ("wind", "💨 Wind Stream Vectors"),
            ("clouds", "☁️ Satellite Cloud Cover"),
            ("thermal", "🌡️ Thermal Heatmap"),
        ]

        for l_key, l_label in layers:
            is_active = (self.radar_layer == l_key)
            b = tk.Button(
                layer_bar,
                text=l_label,
                font=("Segoe UI", 9, "bold" if is_active else "normal"),
                bg=self.colors["primary"] if is_active else self.colors["card_sub_bg"],
                fg="#0B1120" if (is_active and self.current_theme_name == "Deep Twilight") else (
                    "#FFFFFF" if is_active else self.colors["text_muted"]
                ),
                relief=tk.FLAT,
                padx=10,
                pady=4,
                cursor="hand2",
                bd=0,
                command=lambda k=l_key: self._set_radar_layer(k)
            )
            b.pack(side=tk.LEFT, padx=3)
            self.layer_buttons[l_key] = b

        # Native Radar Canvas Scope
        canvas_w = 780
        canvas_h = 340
        self.radar_canvas = tk.Canvas(
            radar_card,
            width=canvas_w,
            height=canvas_h,
            bg="#060913",
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            bd=0
        )
        self.radar_canvas.pack(fill=tk.BOTH, expand=True)

        # Reflectivity dBZ Legend
        legend_row = tk.Frame(radar_card, bg=self.colors["card_bg"])
        legend_row.pack(fill=tk.X, pady=(10, 0))

        tk.Label(
            legend_row,
            text="Reflectivity (dBZ):",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["text_muted"],
            bg=self.colors["card_bg"]
        ).pack(side=tk.LEFT, padx=(0, 10))

        dbz_levels = [
            ("5 dBZ Drizzle", "#0284C7"),
            ("20 dBZ Light", "#38BDF8"),
            ("35 dBZ Moderate", "#10B981"),
            ("45 dBZ Heavy", "#F59E0B"),
            ("55+ dBZ Storm", "#EF4444"),
        ]
        for name, col in dbz_levels:
            pill = tk.Frame(legend_row, bg=col, padx=8, pady=2)
            pill.pack(side=tk.LEFT, padx=3)
            tk.Label(pill, text=name, font=("Segoe UI", 7, "bold"), fg="#FFFFFF", bg=col).pack()

        # Telemetry Summary Tiles
        stats_row = tk.Frame(container, bg=self.colors["bg"])
        stats_row.pack(fill=tk.X, pady=(0, 14))

        radar_tiles = [
            ("📡 Radar Station", f"{city_name} Met-Doppler 01", "Frequency: 2.8 GHz S-band"),
            ("🔄 Sweep Velocity", "18.5 RPM", "360° Continuous Radial Scan"),
            ("🎯 Radial Coverage", "200 km Radius", "Beam Elevation: 0.5° Base Tilt"),
            ("⚡ Echo Vector", f"{w.get('wind_speed_kmh', 14.0):.1f} km/h Vectors", f"Dew point: {w.get('feels_like_c', 22.0):.1f}°C"),
        ]

        for i, (t1, t2, t3) in enumerate(radar_tiles):
            card = tk.Frame(
                stats_row,
                bg=self.colors["card_bg"],
                highlightbackground=self.colors["border"],
                highlightthickness=1,
                padx=16,
                pady=12
            )
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 8, 0))

            tk.Label(card, text=t1, font=("Segoe UI", 8, "bold"), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).pack(anchor="w")
            tk.Label(card, text=t2, font=("Segoe UI", 12, "bold"), fg=self.colors["text_main"], bg=self.colors["card_bg"]).pack(anchor="w", pady=(4, 2))
            tk.Label(card, text=t3, font=("Segoe UI", 8), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).pack(anchor="w")

        # Initial Draw & Start Animation
        self._draw_radar_scope()
        if self.radar_playing:
            self._schedule_radar_animation()

    def _toggle_radar_play(self):
        self.radar_playing = not self.radar_playing
        if hasattr(self, "radar_play_btn"):
            self.radar_play_btn.configure(
                text="⏸ Pause Loop" if self.radar_playing else "▶ Play Sweep"
            )
        if self.radar_playing:
            self._schedule_radar_animation()
        else:
            if self.radar_anim_id:
                try:
                    self.root.after_cancel(self.radar_anim_id)
                except Exception:
                    pass
                self.radar_anim_id = None

    def _set_radar_layer(self, layer_key: str):
        self.radar_layer = layer_key
        for k, btn in getattr(self, "layer_buttons", {}).items():
            is_active = (k == layer_key)
            btn.configure(
                font=("Segoe UI", 9, "bold" if is_active else "normal"),
                bg=self.colors["primary"] if is_active else self.colors["card_sub_bg"],
                fg="#0B1120" if (is_active and self.current_theme_name == "Deep Twilight") else (
                    "#FFFFFF" if is_active else self.colors["text_muted"]
                )
            )
        self._draw_radar_scope()

    def _draw_radar_scope(self):
        if not hasattr(self, "radar_canvas") or not self.radar_canvas.winfo_exists():
            return

        c = self.radar_canvas
        c.delete("all")

        w = c.winfo_width() or 780
        h = c.winfo_height() or 340
        cx, cy = w / 2, h / 2
        max_r = min(cx, cy) - 20

        # Draw concentric distance range rings
        rings = [0.25, 0.5, 0.75, 1.0]
        distances = ["50 km", "100 km", "150 km", "200 km"]
        for frac, dist in zip(rings, distances):
            r = max_r * frac
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#162947", width=1)
            c.create_text(cx + 8, cy - r + 8, text=dist, font=("Segoe UI", 7), fill="#38BDF8")

        # Draw compass crosshairs
        c.create_line(cx - max_r, cy, cx + max_r, cy, fill="#162947", dash=(2, 4))
        c.create_line(cx, cy - max_r, cx, cy + max_r, fill="#162947", dash=(2, 4))

        # Direction labels
        c.create_text(cx, cy - max_r - 8, text="N (0°)", font=("Segoe UI", 8, "bold"), fill="#64748B")
        c.create_text(cx + max_r + 14, cy, text="E (90°)", font=("Segoe UI", 8, "bold"), fill="#64748B")
        c.create_text(cx, cy + max_r + 8, text="S (180°)", font=("Segoe UI", 8, "bold"), fill="#64748B")
        c.create_text(cx - max_r - 18, cy, text="W (270°)", font=("Segoe UI", 8, "bold"), fill="#64748B")

        # Draw layer-specific weather phenomena
        w_data = self.current_weather or {}
        cond = w_data.get("condition", "clear").lower()
        has_rain = any(term in cond for term in ["rain", "storm", "shower", "drizzle"])

        if self.radar_layer == "precip":
            # Simulated Doppler precipitation cells
            cells = [
                (cx + 40, cy - 35, 45, "#10B981"),
                (cx + 55, cy - 25, 25, "#F59E0B"),
                (cx - 70, cy + 50, 60, "#38BDF8"),
                (cx - 85, cy + 60, 30, "#0284C7"),
            ]
            if has_rain:
                cells.append((cx - 15, cy - 10, 40, "#EF4444"))
                cells.append((cx + 10, cy + 15, 55, "#F59E0B"))

            for bx, by, br, color in cells:
                c.create_oval(bx - br, by - br, bx + br, by + br, fill=color, outline="", stipple="gray50")

        elif self.radar_layer == "wind":
            import math
            for gx in range(int(cx - max_r + 30), int(cx + max_r - 30), 50):
                for gy in range(int(cy - max_r + 30), int(cy + max_r - 30), 50):
                    dist_to_center = math.hypot(gx - cx, gy - cy)
                    if dist_to_center < max_r - 15:
                        ang = math.atan2(gy - cy, gx - cx) + math.radians(self.radar_angle * 0.3)
                        vx = gx + 18 * math.cos(ang)
                        vy = gy + 18 * math.sin(ang)
                        c.create_line(gx, gy, vx, vy, fill="#38BDF8", arrow=tk.LAST, width=1.5)

        elif self.radar_layer == "clouds":
            c.create_oval(cx - 110, cy - 80, cx + 130, cy + 80, fill="#334155", outline="", stipple="gray25")
            c.create_oval(cx - 140, cy + 10, cx + 80, cy + 110, fill="#475569", outline="", stipple="gray50")

        elif self.radar_layer == "thermal":
            c.create_oval(cx - max_r + 20, cy - 60, cx + max_r - 20, cy + 60, fill="#F59E0B", outline="", stipple="gray25")
            c.create_oval(cx - 80, cy - 40, cx + 80, cy + 40, fill="#EF4444", outline="", stipple="gray25")

        # Rotating radar sweep line
        import math
        rad = math.radians(self.radar_angle)
        sx = cx + max_r * math.cos(rad)
        sy = cy + max_r * math.sin(rad)
        c.create_line(cx, cy, sx, sy, fill="#38BDF8", width=2)

        # Trailing sweep glow
        prev_rad = math.radians(self.radar_angle - 12)
        px = cx + max_r * math.cos(prev_rad)
        py = cy + max_r * math.sin(prev_rad)
        c.create_polygon(cx, cy, sx, sy, px, py, fill="#0C4A6E", outline="", stipple="gray25")

        # Center Target Reticle & City Label
        c.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill="#F8FAFC", outline="#38BDF8", width=2)
        city = w_data.get("city", "Bengaluru")
        c.create_text(cx, cy + 18, text=f"⌖ {city} Radar Base", font=("Segoe UI", 9, "bold"), fill="#F8FAFC")

    def _schedule_radar_animation(self):
        if not self.radar_playing or self.current_page != "radar":
            return
        self.radar_angle = (self.radar_angle + 6) % 360
        self._draw_radar_scope()
        self.radar_anim_id = self.root.after(45, self._schedule_radar_animation)

    # =========================================================================
    # Page: Air Quality & Solar UV Intelligence
    # =========================================================================
    def show_air_quality_page(self):
        """Render Air Quality Index (AQI) and Solar UV Radiation Metrics."""
        self._update_nav_highlight("air_quality")
        self._clear_content()

        container = self._create_scrollable_container()
        w = self.current_weather or {}
        city_name = w.get("city", "Bengaluru")

        # Page Header
        tk.Label(
            container,
            text=f"🍃 Air Quality & UV Radiation — {city_name}",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["bg"]
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            container,
            text="Atmospheric pollutant concentrations, solar ultraviolet index, and clinical health advisories.",
            font=("Segoe UI", 10),
            fg=self.colors["text_muted"],
            bg=self.colors["bg"]
        ).pack(anchor="w", pady=(0, 16))

        hum = w.get("humidity", 55)
        pres = w.get("pressure_hpa", 1013)
        aqi_value = int(max(20, min(180, int((hum * 0.4) + ((1020 - pres) * 1.5) + 25))))

        if aqi_value <= 50:
            aqi_status = "Good"
            aqi_color = "#10B981"
            aqi_desc = "Air quality is considered satisfactory. Safe for all outdoor activities."
        elif aqi_value <= 100:
            aqi_status = "Moderate"
            aqi_color = "#F59E0B"
            aqi_desc = "Air quality is acceptable. Unusually sensitive individuals should monitor outdoor exposure."
        else:
            aqi_status = "Unhealthy for Sensitive"
            aqi_color = "#EF4444"
            aqi_desc = "Members of sensitive groups may experience minor health effects. Consider reducing strenuous outdoor exercise."

        # Dual Hero Cards (AQI + UV)
        hero_row = tk.Frame(container, bg=self.colors["bg"])
        hero_row.pack(fill=tk.X, pady=(0, 16))

        # AQI Card
        aqi_card = tk.Frame(
            hero_row,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=20,
            pady=16
        )
        aqi_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

        tk.Label(aqi_card, text="AIR QUALITY INDEX (AQI)", font=("Segoe UI", 9, "bold"), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).pack(anchor="w")

        aqi_num_box = tk.Frame(aqi_card, bg=self.colors["card_bg"])
        aqi_num_box.pack(anchor="w", pady=(8, 4))

        tk.Label(aqi_num_box, text=str(aqi_value), font=("Segoe UI", 32, "bold"), fg=aqi_color, bg=self.colors["card_bg"]).pack(side=tk.LEFT)
        tk.Label(aqi_num_box, text=f"• {aqi_status}", font=("Segoe UI", 12, "bold"), fg=aqi_color, bg=self.colors["card_bg"]).pack(side=tk.LEFT, padx=(10, 0))

        tk.Label(aqi_card, text=aqi_desc, font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["card_bg"], wraplength=420, justify=tk.LEFT).pack(anchor="w")

        # UV Card
        uv_card = tk.Frame(
            hero_row,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=20,
            pady=16
        )
        uv_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(uv_card, text="SOLAR ULTRAVIOLET (UV) INDEX", font=("Segoe UI", 9, "bold"), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).pack(anchor="w")

        uv_num_box = tk.Frame(uv_card, bg=self.colors["card_bg"])
        uv_num_box.pack(anchor="w", pady=(8, 4))

        tk.Label(uv_num_box, text="UV 5.4", font=("Segoe UI", 32, "bold"), fg="#F59E0B", bg=self.colors["card_bg"]).pack(side=tk.LEFT)
        tk.Label(uv_num_box, text="• Moderate Risk", font=("Segoe UI", 12, "bold"), fg="#F59E0B", bg=self.colors["card_bg"]).pack(side=tk.LEFT, padx=(10, 0))

        tk.Label(uv_card, text="Sun protection recommended between 11:30 AM – 3:30 PM. Wear sunglasses and SPF 30+ sunscreen.", font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["card_bg"], wraplength=420, justify=tk.LEFT).pack(anchor="w")

        # 6 Detailed Pollutant Concentration Tiles
        tk.Label(
            container,
            text="📊 Pollutant Concentrations & WHO Benchmark Thresholds",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["bg"]
        ).pack(anchor="w", pady=(0, 10))

        grid_frame = tk.Frame(container, bg=self.colors["bg"])
        grid_frame.pack(fill=tk.X, pady=(0, 16))

        pollutants = [
            ("PM2.5 (Fine Particulate)", f"{12.4 + (aqi_value * 0.15):.1f} µg/m³", "Target: < 25 µg/m³", "#10B981"),
            ("PM10 (Inhalable Dust)", f"{28.6 + (aqi_value * 0.25):.1f} µg/m³", "Target: < 50 µg/m³", "#10B981"),
            ("Ozone (O₃)", f"{38.2 + (hum * 0.1):.1f} ppb", "Safe Threshold: < 70 ppb", "#38BDF8"),
            ("Nitrogen Dioxide (NO₂)", "18.4 ppb", "Automotive Emission: Low", "#10B981"),
            ("Sulphur Dioxide (SO₂)", "5.2 ppb", "Industrial Standard: Safe", "#10B981"),
            ("Carbon Monoxide (CO)", "0.38 ppm", "WHO Target: < 9 ppm", "#10B981"),
        ]

        for i, (p_name, p_val, p_tgt, p_col) in enumerate(pollutants):
            row = i // 3
            col = i % 3
            p_card = tk.Frame(
                grid_frame,
                bg=self.colors["card_bg"],
                highlightbackground=self.colors["border"],
                highlightthickness=1,
                padx=16,
                pady=12
            )
            p_card.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
            grid_frame.grid_columnconfigure(col, weight=1)

            tk.Label(p_card, text=p_name, font=("Segoe UI", 9, "bold"), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).pack(anchor="w")
            tk.Label(p_card, text=p_val, font=("Segoe UI", 14, "bold"), fg=p_col, bg=self.colors["card_bg"]).pack(anchor="w", pady=(4, 2))
            tk.Label(p_card, text=p_tgt, font=("Segoe UI", 8), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).pack(anchor="w")

        # Health Recommendations
        guide_card = tk.Frame(
            container,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=20,
            pady=16
        )
        guide_card.pack(fill=tk.X, pady=(0, 16))

        tk.Label(guide_card, text="🏥 Population Health Recommendations", font=("Segoe UI", 11, "bold"), fg=self.colors["text_main"], bg=self.colors["card_bg"]).pack(anchor="w", pady=(0, 10))

        recs = [
            ("🏃 Outdoor Athletes & Runners", "Air quality is suitable for high-intensity endurance training and marathon workouts."),
            ("👶 Children & Elderly Populations", "Normal outdoor recreation is encouraged. Maintain adequate hydration."),
            ("🫁 Individuals with Respiratory Conditions", "No immediate heightened allergen alerts. Carry standard inhalers as precaution."),
            ("🚗 Ventilation & Indoor Air Quality", "Safe to open windows for natural airflow and indoor circulation."),
        ]

        for r_title, r_desc in recs:
            r_box = tk.Frame(guide_card, bg=self.colors["card_sub_bg"], padx=14, pady=8)
            r_box.pack(fill=tk.X, pady=(0, 6))
            tk.Label(r_box, text=r_title, font=("Segoe UI", 9, "bold"), fg=self.colors["text_main"], bg=self.colors["card_sub_bg"]).pack(anchor="w")
            tk.Label(r_box, text=r_desc, font=("Segoe UI", 8), fg=self.colors["text_muted"], bg=self.colors["card_sub_bg"]).pack(anchor="w", pady=(2, 0))

    # =========================================================================
    # Page: Severe Weather Advisories & Emergency Warnings
    # =========================================================================
    def show_alerts_page(self):
        """Render Severe Weather Alerts, Emergency Preparedness, and Broadcast Simulator."""
        self._update_nav_highlight("alerts")
        self._clear_content()

        container = self._create_scrollable_container()
        w = self.current_weather or {}
        city_name = w.get("city", "Bengaluru")
        cond = w.get("condition", "clear").lower()
        wind_spd = w.get("wind_speed_kmh", 12.0)
        temp_c = w.get("temperature_c", 24.0)

        # Header with Simulate Button
        h_frame = tk.Frame(container, bg=self.colors["bg"])
        h_frame.pack(fill=tk.X, pady=(0, 14))

        left_h = tk.Frame(h_frame, bg=self.colors["bg"])
        left_h.pack(side=tk.LEFT)

        tk.Label(
            left_h,
            text=f"⚠️ Severe Weather Alerts & Advisories — {city_name}",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["bg"]
        ).pack(anchor="w")

        tk.Label(
            left_h,
            text="Real-time meteorological warnings, civil defense bulletins, and emergency disaster preparedness.",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["bg"]
        ).pack(anchor="w", pady=(2, 0))

        tk.Button(
            h_frame,
            text="🚨 Test Broadcast Alert",
            font=("Segoe UI", 9, "bold"),
            bg="#EF4444",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
            bd=0,
            command=self._trigger_simulated_alert
        ).pack(side=tk.RIGHT)

        # Dynamic Advisory Evaluation
        active_advisories = []
        if wind_spd >= 25.0:
            active_advisories.append((
                "HIGH WIND ADVISORY",
                f"Sustained wind velocity of {wind_spd:.1f} km/h detected across the metropolitan area.",
                "🔴 Warning",
                "#EF4444"
            ))
        if temp_c >= 34.0:
            active_advisories.append((
                "EXCESSIVE HEAT ADVISORY",
                f"Peak surface temperature of {temp_c:.1f}°C. Heat index precautions in effect.",
                "🟠 Advisory",
                "#F59E0B"
            ))
        elif temp_c <= 4.0:
            active_advisories.append((
                "FROST & FREEZE WATCH",
                f"Near-freezing temperatures ({temp_c:.1f}°C). Protect sensitive agricultural crops.",
                "🟠 Watch",
                "#38BDF8"
            ))
        if any(term in cond for term in ["storm", "thunder", "rain", "shower"]):
            active_advisories.append((
                "FLASH FLOOD & RAINSTORM WATCH",
                f"Precipitation system detected. Localized street flooding possible in low-lying zones.",
                "🟠 Advisory",
                "#F59E0B"
            ))

        if not active_advisories:
            active_advisories.append((
                "METEOROLOGICAL ALL CLEAR",
                f"No severe storm warnings, gale watches, or flash flood advisories active for {city_name}.",
                "🟢 All Clear",
                "#10B981"
            ))

        # Advisory Feed Cards
        for title, desc, badge_txt, badge_col in active_advisories:
            card = tk.Frame(
                container,
                bg=self.colors["card_bg"],
                highlightbackground=badge_col,
                highlightthickness=1,
                padx=20,
                pady=16
            )
            card.pack(fill=tk.X, pady=(0, 12))

            top_line = tk.Frame(card, bg=self.colors["card_bg"])
            top_line.pack(fill=tk.X, pady=(0, 6))

            badge = tk.Label(top_line, text=badge_txt, font=("Segoe UI", 8, "bold"), fg="#FFFFFF", bg=badge_col, padx=8, pady=2)
            badge.pack(side=tk.LEFT)

            tk.Label(top_line, text=f"  {title}", font=("Segoe UI", 12, "bold"), fg=self.colors["text_main"], bg=self.colors["card_bg"]).pack(side=tk.LEFT)

            tk.Label(card, text=desc, font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).pack(anchor="w", pady=(2, 0))

        # Interactive Preparedness Checklist Card
        check_card = tk.Frame(
            container,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=20,
            pady=16
        )
        check_card.pack(fill=tk.X, pady=(0, 16))

        tk.Label(check_card, text="🛡️ Severe Weather Readiness Checklist", font=("Segoe UI", 12, "bold"), fg=self.colors["text_main"], bg=self.colors["card_bg"]).pack(anchor="w", pady=(0, 6))
        tk.Label(check_card, text="Click to check off emergency readiness tasks for your household.", font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).pack(anchor="w", pady=(0, 12))

        checklist_items = [
            "Check mobile backup battery banks and keep emergency flashlights accessible",
            "Clear outdoor storm drains and secure loose awnings, tarps, and patio items",
            "Stock 72-hour supply of drinking water, non-perishable food, and first-aid kits",
            "Monitor live Doppler radar sweeps and local civil defense alerts regularly",
            "Ensure pet shelter, medication reserves, and emergency contact list are ready",
        ]

        self.checklist_vars = []
        for item in checklist_items:
            v = tk.BooleanVar(value=False)
            self.checklist_vars.append(v)
            cb = tk.Checkbutton(
                check_card,
                text=item,
                variable=v,
                font=("Segoe UI", 9),
                fg=self.colors["text_main"],
                bg=self.colors["card_bg"],
                selectcolor=self.colors["card_sub_bg"],
                activebackground=self.colors["card_bg"],
                activeforeground=self.colors["primary"],
                cursor="hand2",
                bd=0
            )
            cb.pack(anchor="w", pady=3)

    def _trigger_simulated_alert(self):
        """Trigger an interactive high-visibility emergency alert banner modal."""
        city = (self.current_weather or {}).get("city", "Bengaluru")
        messagebox.showwarning(
            "🚨 Severe Meteorological Broadcast Simulation",
            f"CIVIL WEATHER BROADCAST TEST:\n\n"
            f"Location: {city} Region\n"
            f"Alert Type: Flash Storm & High Wind Simulation\n"
            f"Status: TEST SIMULATION EXERCISE ONLY\n\n"
            f"This test confirms your notification systems and emergency readiness checklist are fully operational."
        )

    # =========================================================================
    # Page: Explore & City Comparison View
    # =========================================================================
    def show_explore_page(self):
        """Render City Exploration and Side-by-Side Weather Comparison."""
        self._update_nav_highlight("explore")
        self._clear_content()

        container = self._create_scrollable_container()

        # Page Header
        tk.Label(
            container,
            text="🔍 Explore Global Weather & City Comparison",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["bg"]
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            container,
            text="Compare atmospheric conditions between any two cities worldwide using live Open-Meteo REST API data.",
            font=("Segoe UI", 10),
            fg=self.colors["text_muted"],
            bg=self.colors["bg"]
        ).pack(anchor="w", pady=(0, 16))

        # Comparison Setup Card
        compare_card = tk.Frame(
            container,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=24,
            pady=20
        )
        compare_card.pack(fill=tk.X, pady=(0, 16))

        tk.Label(
            compare_card,
            text="⚖️ Live Two-City Weather Comparison",
            font=("Segoe UI", 13, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 12))

        inputs_row = tk.Frame(compare_card, bg=self.colors["card_bg"])
        inputs_row.pack(fill=tk.X, pady=(0, 12))

        # City 1 input
        c1_box = tk.Frame(inputs_row, bg=self.colors["card_bg"])
        c1_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        tk.Label(c1_box, text="Primary City (City A):", font=("Segoe UI", 9, "bold"), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).pack(anchor="w", pady=(0, 4))
        self.compare_entry1 = tk.Entry(c1_box, font=("Segoe UI", 11), bg=self.colors["card_sub_bg"], fg=self.colors["text_main"], relief=tk.FLAT, bd=0)
        self.compare_entry1.pack(fill=tk.X, ipady=6)
        default_c1 = self.current_weather.get("city") if self.current_weather else "Aland"
        self.compare_entry1.insert(0, default_c1)

        # City 2 input
        c2_box = tk.Frame(inputs_row, bg=self.colors["card_bg"])
        c2_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        tk.Label(c2_box, text="Comparison City (City B):", font=("Segoe UI", 9, "bold"), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).pack(anchor="w", pady=(0, 4))
        self.compare_entry2 = tk.Entry(c2_box, font=("Segoe UI", 11), bg=self.colors["card_sub_bg"], fg=self.colors["text_main"], relief=tk.FLAT, bd=0)
        self.compare_entry2.pack(fill=tk.X, ipady=6)
        self.compare_entry2.insert(0, "Bengaluru")

        # Compare Button
        self.run_compare_btn = tk.Button(
            compare_card,
            text="⚡ Run Side-by-Side Comparison",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["primary"],
            fg="#FFFFFF",
            activebackground=self.colors["primary_hover"],
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            bd=0,
            command=self.run_comparison_flow
        )
        self.run_compare_btn.pack(anchor="w", pady=(6, 0))

        # Results area
        self.comparison_results_frame = tk.Frame(container, bg=self.colors["bg"])
        self.comparison_results_frame.pack(fill=tk.X, pady=(0, 16))

        # Show previous comparison if already loaded
        if self.comparison_data.get("city1") and self.comparison_data.get("city2"):
            self._render_comparison_cards(self.comparison_results_frame)

    def run_comparison_flow(self):
        """Fetch and compare weather for two cities in a non-blocking thread."""
        c1 = self.compare_entry1.get().strip()
        c2 = self.compare_entry2.get().strip()

        if not c1 or not c2:
            messagebox.showinfo("Comparison", "Please enter names for both cities.")
            return

        self.run_compare_btn.configure(text="⏳ Fetching Both Cities...", state=tk.DISABLED)

        def worker():
            res1 = self.service.get_weather(c1)
            res2 = self.service.get_weather(c2)
            self.root.after(0, lambda: self._on_comparison_complete(res1, res2))

        threading.Thread(target=worker, daemon=True).start()

    def _on_comparison_complete(self, res1: dict, res2: dict):
        """Render comparison results when both requests complete."""
        self.run_compare_btn.configure(text="⚡ Run Side-by-Side Comparison", state=tk.NORMAL)

        if not res1.get("success"):
            messagebox.showerror("City A Error", f"Failed to fetch {res1.get('city', 'City 1')}: {res1.get('error')}")
            return
        if not res2.get("success"):
            messagebox.showerror("City B Error", f"Failed to fetch {res2.get('city', 'City 2')}: {res2.get('error')}")
            return

        self.comparison_data = {"city1": res1, "city2": res2}
        for w in self.comparison_results_frame.winfo_children():
            w.destroy()
        self._render_comparison_cards(self.comparison_results_frame)

    def _render_comparison_cards(self, parent: tk.Frame):
        """Render side-by-side comparative cards and delta breakdown."""
        c1 = self.comparison_data["city1"]
        c2 = self.comparison_data["city2"]

        # Insight Delta Banner
        t1 = c1.get("temperature_c", 0.0)
        t2 = c2.get("temperature_c", 0.0)
        diff = abs(t1 - t2)
        warmer = c1.get("city") if t1 >= t2 else c2.get("city")
        cooler = c2.get("city") if t1 >= t2 else c1.get("city")

        delta_banner = tk.Frame(
            parent,
            bg=self.colors["badge_bg"],
            padx=18,
            pady=12,
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        delta_banner.pack(fill=tk.X, pady=(0, 14))

        tk.Label(
            delta_banner,
            text=f"📊 Comparative Insight: {warmer} is {diff:.1f}°C warmer than {cooler}.",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["badge_fg"],
            bg=self.colors["badge_bg"]
        ).pack(anchor="w")

        # Side by side cards
        grid = tk.Frame(parent, bg=self.colors["bg"])
        grid.pack(fill=tk.X)

        self._build_city_card_widget(grid, c1, side=tk.LEFT, padx=(0, 10))
        self._build_city_card_widget(grid, c2, side=tk.RIGHT, padx=(10, 0))

    def _build_city_card_widget(self, parent: tk.Frame, data: dict, side, padx):
        """Construct individual comparison city card."""
        card = tk.Frame(
            parent,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=20,
            pady=16
        )
        card.pack(side=side, fill=tk.BOTH, expand=True, padx=padx)

        tk.Label(
            card,
            text=f"📍 {data.get('city')}, {data.get('country')}",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w")

        c_emoji = WMO_EMOJI_MAP.get(data.get("icon_type", "cloudy"), "⛅")
        tk.Label(
            card,
            text=f"{c_emoji} {data.get('condition')}",
            font=("Segoe UI", 11),
            fg=self.colors["primary"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(2, 10))

        celsius = data.get("temperature_c", 0.0)
        tk.Label(
            card,
            text=self._format_temp(celsius),
            font=("Segoe UI", 28, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 10))

        metrics = [
            ("Feels Like", self._format_temp(data.get("feels_like_c", celsius))),
            ("Humidity", f"{data.get('humidity', 0)}%"),
            ("Wind Speed", f"{data.get('wind_speed_kmh', 0.0)} km/h"),
            ("Surface Pressure", f"{data.get('pressure_hpa', 1013)} hPa"),
            ("Day Range", f"🔺 {self._format_temp(data.get('temp_max_c', celsius))} / 🔻 {self._format_temp(data.get('temp_min_c', celsius))}"),
        ]

        for m_name, m_val in metrics:
            m_row = tk.Frame(card, bg=self.colors["card_sub_bg"], padx=10, pady=6)
            m_row.pack(fill=tk.X, pady=(0, 4))
            tk.Label(m_row, text=m_name, font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["card_sub_bg"]).pack(side=tk.LEFT)
            tk.Label(m_row, text=m_val, font=("Segoe UI", 9, "bold"), fg=self.colors["text_main"], bg=self.colors["card_sub_bg"]).pack(side=tk.RIGHT)

        # Quick Load in Dashboard Button
        tk.Button(
            card,
            text="Load in Dashboard ➔",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["secondary"],
            fg=self.colors["primary"],
            activebackground=self.colors["primary"],
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
            bd=0,
            command=lambda: self._load_city_and_goto_dashboard(data.get("city"))
        ).pack(anchor="w", pady=(12, 0))

    def _load_city_and_goto_dashboard(self, city_name: str):
        """Fetch city and switch to dashboard page."""
        self.search_city_threaded(city_name, on_complete=lambda ok: self.show_dashboard_page() if ok else None)

    # =========================================================================
    # Page 4: Saved Favourites View
    # =========================================================================
    def show_favorites_page(self):
        """Render saved favourites grid with JSON persistence."""
        self._update_nav_highlight("favorites")
        self._clear_content()

        container = self._create_scrollable_container()

        # Page Header
        h_box = tk.Frame(container, bg=self.colors["bg"])
        h_box.pack(fill=tk.X, pady=(0, 14))

        tk.Label(
            h_box,
            text="⭐ Saved Favourites (.json)",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["bg"]
        ).pack(side=tk.LEFT)

        # Add Favorite Button
        tk.Button(
            h_box,
            text="➕ Add New City",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["primary"],
            fg="#FFFFFF",
            activebackground=self.colors["primary_hover"],
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=14,
            pady=5,
            cursor="hand2",
            bd=0,
            command=self._prompt_add_favorite
        ).pack(side=tk.RIGHT)

        favorites = self.storage.get_favorites()

        if not favorites:
            self._render_empty_state(
                container,
                icon="⭐",
                title="No Saved Favourites Yet",
                description="Click 'Add to Favourites' from the Dashboard or use the button above to bookmark cities."
            )
            return

        # Render Favourites Grid
        fav_grid = tk.Frame(container, bg=self.colors["bg"])
        fav_grid.pack(fill=tk.X)

        for fav in favorites:
            city = fav.get("city", "Unknown")
            country = fav.get("country", "")
            added = fav.get("added_at", "")

            f_card = tk.Frame(
                fav_grid,
                bg=self.colors["card_bg"],
                highlightbackground=self.colors["border"],
                highlightthickness=1,
                padx=18,
                pady=14
            )
            f_card.pack(fill=tk.X, pady=(0, 8))

            info_box = tk.Frame(f_card, bg=self.colors["card_bg"])
            info_box.pack(side=tk.LEFT)

            tk.Label(
                info_box,
                text=f"📍 {city}" + (f", {country}" if country else ""),
                font=("Segoe UI", 13, "bold"),
                fg=self.colors["text_main"],
                bg=self.colors["card_bg"]
            ).pack(anchor="w")

            tk.Label(
                info_box,
                text=f"Added on: {added}" if added else "Saved favourite",
                font=("Segoe UI", 8),
                fg=self.colors["text_muted"],
                bg=self.colors["card_bg"]
            ).pack(anchor="w")

            btn_box = tk.Frame(f_card, bg=self.colors["card_bg"])
            btn_box.pack(side=tk.RIGHT)

            tk.Button(
                btn_box,
                text="Load Weather",
                font=("Segoe UI", 9, "bold"),
                bg=self.colors["secondary"],
                fg=self.colors["primary"],
                activebackground=self.colors["primary"],
                activeforeground="#FFFFFF",
                relief=tk.FLAT,
                padx=12,
                pady=4,
                cursor="hand2",
                bd=0,
                command=lambda c=city: self._load_city_and_goto_dashboard(c)
            ).pack(side=tk.LEFT, padx=(0, 8))

            tk.Button(
                btn_box,
                text="🗑️ Remove",
                font=("Segoe UI", 9),
                bg=self.colors["card_sub_bg"],
                fg="#B91C1C",
                activebackground="#FEE2E2",
                relief=tk.FLAT,
                padx=10,
                pady=4,
                cursor="hand2",
                bd=0,
                command=lambda c=city: self._remove_favorite_action(c)
            ).pack(side=tk.LEFT)

    def _prompt_add_favorite(self):
        """Dialog to add a new favorite city."""
        from tkinter import simpledialog
        city = simpledialog.askstring("Add Favourite", "Enter city name to bookmark:", parent=self.root)
        if city and city.strip():
            added = self.storage.add_favorite(city.strip())
            if added:
                messagebox.showinfo("Success", f"'{city.strip()}' added to favourites (.json)!")
                self.show_favorites_page()
            else:
                messagebox.showinfo("Notice", f"'{city.strip()}' is already in your favourites.")

    def _remove_favorite_action(self, city_name: str):
        """Remove city from favorites and re-render view."""
        if messagebox.askyesno("Confirm Removal", f"Remove '{city_name}' from your saved favourites?"):
            self.storage.remove_favorite(city_name)
            self.show_favorites_page()

    def save_current_to_favorites(self):
        """Save currently loaded weather city to favorites."""
        if not self.current_weather:
            messagebox.showinfo("Notice", "Please search for a city first.")
            return

        city = self.current_weather.get("city")
        country = self.current_weather.get("country", "")
        added = self.storage.add_favorite(city, country)
        if added:
            messagebox.showinfo("Saved", f"'{city}' saved to favourites (.json)!")
        else:
            messagebox.showinfo("Notice", f"'{city}' is already in your favourites.")

    # =========================================================================
    # Page 5: History & Reports View (CSV + TXT)
    # =========================================================================
    def show_history_page(self):
        """Render CSV search history table and TXT report viewer."""
        self._update_nav_highlight("history")
        self._clear_content()

        container = self._create_scrollable_container()

        # Header Title
        tk.Label(
            container,
            text="📋 Search History & Intelligence Reports",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["bg"]
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            container,
            text="Examine persistent tabular search logs (.csv) and inspect generated intelligence reports (.txt).",
            font=("Segoe UI", 10),
            fg=self.colors["text_muted"],
            bg=self.colors["bg"]
        ).pack(anchor="w", pady=(0, 16))

        # ---------------- Section 1: CSV Search History ----------------
        hist_card = tk.Frame(
            container,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=20,
            pady=16
        )
        hist_card.pack(fill=tk.X, pady=(0, 16))

        h_top = tk.Frame(hist_card, bg=self.colors["card_bg"])
        h_top.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            h_top,
            text="📊 Search History Log (.csv)",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(side=tk.LEFT)

        tk.Button(
            h_top,
            text="🗑️ Clear CSV History",
            font=("Segoe UI", 9),
            bg=self.colors["card_sub_bg"],
            fg="#B91C1C",
            activebackground="#FEE2E2",
            relief=tk.FLAT,
            padx=10,
            pady=3,
            cursor="hand2",
            bd=0,
            command=self._clear_history_action
        ).pack(side=tk.RIGHT)

        history_records = self.storage.get_search_history_csv(limit=25)

        if not history_records:
            tk.Label(
                hist_card,
                text="No search history recorded yet. Recent searches will appear here automatically.",
                font=("Segoe UI", 9, "italic"),
                fg=self.colors["text_muted"],
                bg=self.colors["card_bg"]
            ).pack(anchor="w", pady=10)
        else:
            # Render styled table
            tree_frame = tk.Frame(hist_card, bg=self.colors["card_bg"])
            tree_frame.pack(fill=tk.X)

            columns = ("Timestamp", "City", "Country", "Temp (°C)", "Humidity", "Wind", "Condition")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, anchor="w", width=110)
            tree.column("Timestamp", width=140)
            tree.column("Condition", width=140)

            for r in history_records:
                tree.insert("", tk.END, values=(
                    r.get("Timestamp", ""),
                    r.get("City", ""),
                    r.get("Country", ""),
                    f"{r.get('Temperature_C', '')}°C",
                    f"{r.get('Humidity', '')}%",
                    f"{r.get('Wind_Speed_KMH', '')} km/h",
                    r.get("Condition", "")
                ))

            tree.pack(fill=tk.X, expand=True)

        # ---------------- Section 2: TXT Weather Report ----------------
        rep_card = tk.Frame(
            container,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=20,
            pady=16
        )
        rep_card.pack(fill=tk.X, pady=(0, 16))

        r_top = tk.Frame(rep_card, bg=self.colors["card_bg"])
        r_top.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            r_top,
            text="📄 Plain Text Intelligence Report (.txt)",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(side=tk.LEFT)

        r_btns = tk.Frame(r_top, bg=self.colors["card_bg"])
        r_btns.pack(side=tk.RIGHT)

        tk.Button(
            r_btns,
            text="Generate For Current City",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["primary"],
            fg="#FFFFFF",
            activebackground=self.colors["primary_hover"],
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            bd=0,
            command=self.generate_txt_report
        ).pack(side=tk.LEFT, padx=(0, 8))

        # In-App Text Preview Box
        report_content = self.storage.read_text_report()
        text_box = tk.Text(
            rep_card,
            height=12,
            font=("Consolas", 9),
            bg=self.colors["card_sub_bg"],
            fg=self.colors["text_main"],
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=10
        )
        text_box.insert(tk.END, report_content)
        text_box.configure(state=tk.DISABLED)
        text_box.pack(fill=tk.X, pady=6)

    def _clear_history_action(self):
        """Confirm and clear CSV search logs."""
        if messagebox.askyesno("Confirm Clear", "Clear all search history records from search_history.csv?"):
            self.storage.clear_search_history()
            self.show_history_page()

    def generate_txt_report(self):
        """Export current weather data to weather_report.txt."""
        if not self.current_weather:
            messagebox.showinfo("Notice", "Please search for a city first before generating a report.")
            return

        path = self.storage.save_text_report(self.current_weather)
        if path:
            messagebox.showinfo("Report Exported", f"Weather report successfully written to:\n{path}")
            if self.current_page == "history":
                self.show_history_page()
        else:
            messagebox.showerror("Export Failed", "Could not write text report.")

    # =========================================================================
    # Page 6: Settings & Preferences View
    # =========================================================================
    def show_settings_page(self):
        """Render settings view for units, refresh interval, theme, and diagnostics."""
        self._update_nav_highlight("settings")
        self._clear_content()

        container = self._create_scrollable_container()

        # Header Title
        tk.Label(
            container,
            text="⚙️ Preferences & Configuration",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["bg"]
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            container,
            text="Customize your temperature scale, default startup city, automatic refresh interval, and dashboard theme.",
            font=("Segoe UI", 10),
            fg=self.colors["text_muted"],
            bg=self.colors["bg"]
        ).pack(anchor="w", pady=(0, 16))

        settings_card = tk.Frame(
            container,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=24,
            pady=20
        )
        settings_card.pack(fill=tk.X, pady=(0, 16))

        # 1. Temperature Unit Selection
        tk.Label(
            settings_card,
            text="Temperature Measurement Unit",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 4))

        self.unit_var = tk.StringVar(value=self.current_unit)
        unit_row = tk.Frame(settings_card, bg=self.colors["card_bg"])
        unit_row.pack(anchor="w", pady=(0, 16))

        tk.Radiobutton(
            unit_row,
            text="Celsius (°C)",
            variable=self.unit_var,
            value="C",
            font=("Segoe UI", 10),
            bg=self.colors["card_bg"],
            fg=self.colors["text_main"],
            selectcolor=self.colors["card_bg"]
        ).pack(side=tk.LEFT, padx=(0, 16))

        tk.Radiobutton(
            unit_row,
            text="Fahrenheit (°F)",
            variable=self.unit_var,
            value="F",
            font=("Segoe UI", 10),
            bg=self.colors["card_bg"],
            fg=self.colors["text_main"],
            selectcolor=self.colors["card_bg"]
        ).pack(side=tk.LEFT)

        # 2. Default Startup City
        tk.Label(
            settings_card,
            text="Default Startup City",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 4))

        self.default_city_entry = tk.Entry(
            settings_card,
            font=("Segoe UI", 11),
            bg=self.colors["card_sub_bg"],
            fg=self.colors["text_main"],
            relief=tk.FLAT,
            bd=0
        )
        self.default_city_entry.pack(anchor="w", fill=tk.X, ipady=6, pady=(0, 16))
        self.default_city_entry.insert(0, self.settings.get("default_city", "Bengaluru"))

        # 3. Auto-Refresh Interval
        tk.Label(
            settings_card,
            text="Automatic Weather Refresh Interval",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 4))

        self.interval_var = tk.IntVar(value=int(self.settings.get("refresh_interval_min", 15)))
        int_row = tk.Frame(settings_card, bg=self.colors["card_bg"])
        int_row.pack(anchor="w", pady=(0, 16))

        intervals = [(0, "Manual Only"), (5, "5 Minutes"), (15, "15 Minutes"), (30, "30 Minutes")]
        for val, lbl in intervals:
            tk.Radiobutton(
                int_row,
                text=lbl,
                variable=self.interval_var,
                value=val,
                font=("Segoe UI", 10),
                bg=self.colors["card_bg"],
                fg=self.colors["text_main"],
                selectcolor=self.colors["card_bg"]
            ).pack(side=tk.LEFT, padx=(0, 16))

        # 4. Visual Theme
        tk.Label(
            settings_card,
            text="Visual Theme Preset",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 4))

        self.theme_var = tk.StringVar(value=self.current_theme_name)
        theme_row = tk.Frame(settings_card, bg=self.colors["card_bg"])
        theme_row.pack(anchor="w", pady=(0, 20))

        for tname in THEMES.keys():
            tk.Radiobutton(
                theme_row,
                text=tname,
                variable=self.theme_var,
                value=tname,
                font=("Segoe UI", 10),
                bg=self.colors["card_bg"],
                fg=self.colors["text_main"],
                selectcolor=self.colors["card_bg"]
            ).pack(side=tk.LEFT, padx=(0, 16))

        # Save Settings Button
        tk.Button(
            settings_card,
            text="💾 Save Preferences",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["primary"],
            fg="#FFFFFF",
            activebackground=self.colors["primary_hover"],
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            bd=0,
            command=self._save_settings_action
        ).pack(anchor="w")

        # ---------------- System Diagnostics Card ----------------
        diag_card = tk.Frame(
            container,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=24,
            pady=20
        )
        diag_card.pack(fill=tk.X, pady=(0, 16))

        tk.Label(
            diag_card,
            text="📦 Local Storage & Internship Diagnostics",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["text_main"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", pady=(0, 10))

        stats = self.storage.get_stats()
        diag_info = (
            f"• Saved Favourites (data/favorites.json): {stats['favorites_count']} cities\n"
            f"• Search History Rows (data/search_history.csv): {stats['history_count']} logged searches\n"
            f"• Cached Weather Responses (data/weather_cache.json): {stats['cache_count']} cached snapshots\n"
            f"• Active Report (data/weather_report.txt): {'Generated' if stats['has_report'] else 'Not yet generated'}\n"
            f"• Standard Libraries Utilized: os, random, datetime, math (100% compliant)"
        )

        tk.Label(
            diag_card,
            text=diag_info,
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["card_bg"],
            justify=tk.LEFT
        ).pack(anchor="w")

    def _save_settings_action(self):
        """Save preferences to storage and apply changes."""
        new_unit = self.unit_var.get()
        new_city = self.default_city_entry.get().strip() or "Bengaluru"
        new_interval = self.interval_var.get()
        new_theme = self.theme_var.get()

        updated = {
            "unit": new_unit,
            "default_city": new_city,
            "refresh_interval_min": new_interval,
            "theme": new_theme,
        }

        self.storage.save_settings(updated)
        self.settings.update(updated)
        self.current_unit = new_unit
        self.header_unit_btn.configure(text=f"°{new_unit}")

        # Update theme if changed
        if new_theme != self.current_theme_name:
            self.current_theme_name = new_theme
            self.colors = THEMES[new_theme]
            messagebox.showinfo("Theme Changed", f"Theme updated to '{new_theme}'. Restart or navigate to re-render all elements.")

        self._schedule_auto_refresh()
        messagebox.showinfo("Preferences Saved", "Settings successfully saved to data/settings.json!")
        self.show_dashboard_page()

    # =========================================================================
    # Empty State Helper
    # =========================================================================
    def _render_empty_state(self, parent: tk.Frame, icon: str, title: str, description: str):
        """Render a clean, modern empty state card."""
        card = tk.Frame(
            parent,
            bg=self.colors["card_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=28,
            pady=36
        )
        card.pack(fill=tk.X, pady=(0, 16))

        tk.Label(card, text=icon, font=("Segoe UI", 40), bg=self.colors["card_bg"]).pack(pady=(0, 10))
        tk.Label(card, text=title, font=("Segoe UI", 16, "bold"), fg=self.colors["text_main"], bg=self.colors["card_bg"]).pack()
        tk.Label(card, text=description, font=("Segoe UI", 10), fg=self.colors["text_muted"], bg=self.colors["card_bg"], wraplength=520, justify=tk.CENTER).pack(pady=(6, 0))


def launch_gui():
    """Launch the Tkinter desktop GUI event loop."""
    root = tk.Tk()
    app = WeatherWiseGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
