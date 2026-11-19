"""
Main entry point for Real-Time Wi-Fi Suite.
Usage:
    python main.py                  # Opens Mode Selection window
    python main.py --simulate       # Opens with simulated Wi-Fi telemetry
    python main.py --analyzer       # Launches directly into Real-Time Wi-Fi Analyzer
    python main.py --speed-test     # Launches directly into Speed Limit Test
"""

import argparse
import os
import platform
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from wifi_analyzer.ui.main_window import MainWindow
from wifi_analyzer.ui.selection_window import SelectionWindow
from wifi_analyzer.ui.speed_limit_window import SpeedLimitWindow
from wifi_analyzer.ui.styles import MAIN_STYLE_SHEET


def parse_args():
    parser = argparse.ArgumentParser(
        description="Real-Time Wi-Fi Suite - Wi-Fi Analyzer & Speed Limit Saturation Benchmark"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run in simulation mode (generates simulated Wi-Fi telemetry for testing/demo)"
    )
    parser.add_argument(
        "--analyzer",
        action="store_true",
        help="Directly launch Window 1: Real-Time Wi-Fi Analyzer"
    )
    parser.add_argument(
        "--speed-test",
        action="store_true",
        help="Directly launch Window 2: Speed Limit Test"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Enable High-DPI scaling on Windows
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Windows App ID for proper taskbar grouping
    if platform.system() == "Windows":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "Antigravity.RealTimeWiFiAnalyzer.1.0"
            )
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("Real-Time Wi-Fi Suite")
    app.setOrganizationName("Antigravity")
    app.setStyleSheet(MAIN_STYLE_SHEET)

    # Route according to command-line flag or default to Selection Window
    if args.analyzer:
        window = MainWindow(simulate=args.simulate)
    elif args.speed_test:
        window = SpeedLimitWindow(simulate=args.simulate)
    else:
        window = SelectionWindow(simulate=args.simulate)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
