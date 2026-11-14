"""
Online Library Management System - Unified Project Launcher
Enables one-click execution of the Tkinter Desktop GUI, the Flask Web Portal,
the Automated Test Suite, or the Interactive Plotly Analytics Dashboard.
"""

import sys
import os
import subprocess
import webbrowser
import time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def launch_gui():
    """Launches the Tkinter Desktop Application (CO2)."""
    print("\n[+] Launching Tkinter Desktop Application...")
    gui_script = os.path.join(PROJECT_DIR, 'app_gui.py')
    subprocess.run([sys.executable, gui_script], cwd=PROJECT_DIR)


def launch_web():
    """Launches the Flask Web Application and opens browser."""
    print("\n[+] Starting Flask Web Portal on http://127.0.0.1:5000 ...")
    web_script = os.path.join(PROJECT_DIR, 'app_web.py')

    # Give a brief pause then open browser
    def open_browser():
        time.sleep(1.2)
        webbrowser.open("http://127.0.0.1:5000")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    subprocess.run([sys.executable, web_script], cwd=PROJECT_DIR)


def launch_tests():
    """Executes the complete automated test suite."""
    print("\n[+] Running Automated Test Suite (Unit & Integration Tests)...")
    test_script = os.path.join(PROJECT_DIR, 'test_system.py')
    subprocess.run([sys.executable, test_script], cwd=PROJECT_DIR)


def launch_dashboard():
    """Opens the standalone interactive Plotly analytics dashboard."""
    print("\n[+] Opening Interactive Plotly Analytics Dashboard in default browser...")
    dashboard_file = os.path.join(PROJECT_DIR, 'static', 'interactive_dashboard.html')
    if not os.path.exists(dashboard_file):
        from analytics import LibraryAnalytics
        analytics = LibraryAnalytics()
        analytics.generate_plotly_dashboard_html(save_path=dashboard_file)
    webbrowser.open(f"file://{dashboard_file}")


def interactive_menu():
    """Displays terminal interactive selection menu."""
    while True:
        print("\n" + "=" * 65)
        print("  ONLINE LIBRARY MANAGEMENT SYSTEM - UNIFIED LAUNCHER")
        print("=" * 65)
        print("  1. Launch Desktop Application (Tkinter GUI - CO2)")
        print("  2. Launch Web Application (Flask Portal - 11 Interfaces)")
        print("  3. Run Automated Test Suite (Unit & Integration Tests)")
        print("  4. Open Interactive Plotly Analytics Dashboard")
        print("  5. Exit")
        print("=" * 65)

        choice = input("Enter option [1-5] (default is 1): ").strip()
        if not choice or choice == '1':
            launch_gui()
            break
        elif choice == '2':
            launch_web()
            break
        elif choice == '3':
            launch_tests()
            input("\nPress Enter to return to menu...")
        elif choice == '4':
            launch_dashboard()
            input("\nPress Enter to return to menu...")
        elif choice == '5':
            print("Exiting launcher. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid selection. Please choose an option from 1 to 5.")


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ('--gui', '-g', 'gui'):
            launch_gui()
        elif arg in ('--web', '-w', 'web'):
            launch_web()
        elif arg in ('--test', '-t', 'test'):
            launch_tests()
        elif arg in ('--dashboard', '-d', 'dashboard'):
            launch_dashboard()
        else:
            interactive_menu()
    else:
        interactive_menu()


if __name__ == '__main__':
    main()
