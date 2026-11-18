"""
Main entry point for Real-Time Wi-Fi Analyzer.
Usage:
    python main.py
    python main.py --simulate
"""

import argparse
import os
import platform
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from wifi_analyzer.ui.main_window import MainWindow


def parse_args():
    parser = argparse.ArgumentParser(
        description="Real-Time Wi-Fi Analyzer - Real-time Bandwidth, Ping & RSSI Analysis"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run in simulation mode (generates simulated Wi-Fi telemetry for testing/demo)"
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
    app.setApplicationName("Real-Time Wi-Fi Analyzer")
    app.setOrganizationName("Antigravity")

    window = MainWindow(simulate=args.simulate)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
