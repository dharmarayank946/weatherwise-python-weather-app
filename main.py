"""WeatherWise V3 — Main Unified Entry Point.
=============================================
Launches the WeatherWise Desktop GUI application directly.

Usage:
    python main.py            # Launch the Tkinter Desktop GUI (Default)
    python main.py --cli      # Launch the interactive terminal menu
    python main.py --test     # Run automated test suite
"""

import sys
import os

# Add local directory to module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Main routing entry point."""
    args = sys.argv[1:]

    if "--cli" in args or "-c" in args:
        import weather_app
        weather_app.main()
    elif "--test" in args or "-t" in args:
        import unittest
        loader = unittest.TestLoader()
        suite = loader.discover("tests")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
    elif "--help" in args or "-h" in args:
        print(__doc__)
    else:
        # Launch graphical application directly
        print("=" * 60)
        print("WeatherWise V3 -- Launching Desktop Meteorological GUI...")
        print("(Window will center and pop up directly in front)")
        print("=" * 60)
        from gui import launch_gui
        launch_gui()


if __name__ == "__main__":
    main()
