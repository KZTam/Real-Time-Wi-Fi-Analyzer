"""
Mode Selection Launcher Window.
Provides a modern landing dashboard enabling the user to choose between:
1. Real-Time Wi-Fi Analyzer 
2. Speed Limit Test 
"""

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from wifi_analyzer.ui.main_window import MainWindow
from wifi_analyzer.ui.speed_limit_window import SpeedLimitWindow
from wifi_analyzer.ui.styles import MAIN_STYLE_SHEET, PALETTE


class SelectionWindow(QMainWindow):
    """
    Mode Selection Window allowing the user to select between
    Real-Time Wi-Fi Analyzer and Speed Limit Test.
    """

    def __init__(self, simulate: bool = False, parent=None):
        super().__init__(parent)
        self.simulate = simulate
        self.analyzer_window = None
        self.speed_limit_window = None

        self.setWindowTitle("Real-Time Wi-Fi Suite - Mode Selection")
        self.resize(920, 560)
        self.setMinimumSize(820, 500)
        self.setStyleSheet(MAIN_STYLE_SHEET)

        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(30, 26, 30, 26)
        root_layout.setSpacing(20)

        # Header Title and Subtitle
        header_box = QVBoxLayout()
        header_box.setSpacing(6)
        header_box.setAlignment(Qt.AlignCenter)

        title = QLabel("REAL-TIME WI-FI SUITE")
        title.setStyleSheet("color: #38bdf8; font-size: 26px; font-weight: 900; letter-spacing: 1.2px;")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Select an operating mode to analyze and benchmark your Wi-Fi connection")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 500;")
        subtitle.setAlignment(Qt.AlignCenter)

        header_box.addWidget(title)
        header_box.addWidget(subtitle)
        root_layout.addLayout(header_box)

        # Mode Selection Cards (Horizontal Layout)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(24)

        # Mode 1 Card: Real-Time Wi-Fi Analyzer
        card_analyzer = self._create_mode_card(
            badge_text="PASSIVE 1Hz MONITORING",
            badge_color="#38bdf8",
            title="Real-Time Wi-Fi Analyzer",
            description=(
                "Continuous real-time network consumption monitoring updated at 1Hz:<br><br>"
                "• <b>Live Throughput Graph</b>: Real-time Download & Upload speed in Mbps.<br>"
                "• <b>Router Ping Latency Graph</b>: Round-trip latency and jitter (RFC 1889).<br>"
                "• <b>Passive Monitoring</b>: Zero network overhead; measures actual device traffic.<br>"
                "• <b>Wi-Fi Lock</b>: Requires active Wi-Fi connection to run."
            ),
            button_text="Launch Real-Time Analyzer →",
            button_style=(
                "QPushButton { background-color: #0284c7; color: #ffffff; font-weight: 700; "
                "font-size: 13px; border-radius: 6px; padding: 10px 18px; border: none; } "
                "QPushButton:hover { background-color: #0369a1; } "
                "QPushButton:pressed { background-color: #075985; }"
            ),
            on_click=self._launch_analyzer
        )

        # Mode 2 Card: Speed Limit Test
        card_speed_test = self._create_mode_card(
            badge_text="ACTIVE SATURATION BENCHMARK",
            badge_color="#a855f7",
            title="Speed Limit Test",
            description=(
                "Active multi-threaded pipeline saturation test to measure true capacity:<br><br>"
                "• <b>10-Second Timed Burst</b>: Fixed timeline measuring maximum limits.<br>"
                "• <b>Separated Graphs</b>: Dedicated Download (Top) & Upload (Bottom) graphs.<br>"
            ),
            button_text="Launch Speed Limit Test →",
            button_style=(
                "QPushButton { background-color: #7c3aed; color: #ffffff; font-weight: 700; "
                "font-size: 13px; border-radius: 6px; padding: 10px 18px; border: none; } "
                "QPushButton:hover { background-color: #6d28d9; } "
                "QPushButton:pressed { background-color: #5b21b6; }"
            ),
            on_click=self._launch_speed_test
        )

        cards_layout.addWidget(card_analyzer)
        cards_layout.addWidget(card_speed_test)
        root_layout.addLayout(cards_layout, stretch=1)

        # Footer Status Bar
        sim_text = "Simulation Mode: ON" if self.simulate else "Physical Wi-Fi Interface Detection: Active"
        sim_color = "#34d399" if self.simulate else "#64748b"
        footer = QLabel(f"● {sim_text}")
        footer.setStyleSheet(f"color: {sim_color}; font-size: 11px; font-weight: 600;")
        footer.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(footer)

    def _create_mode_card(
        self,
        badge_text: str,
        badge_color: str,
        title: str,
        description: str,
        button_text: str,
        button_style: str,
        on_click
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("modeCard")
        card.setStyleSheet(
            f"#modeCard {{ background-color: {PALETTE['bg_panel']}; border: 1px solid {PALETTE['border']}; "
            "border-radius: 10px; } "
            "#modeCard:hover { border: 1px solid #475569; }"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Mode Badge
        badge = QLabel(badge_text)
        badge.setStyleSheet(
            f"color: {badge_color}; background-color: #1e293b; border-radius: 4px; "
            "font-size: 10px; font-weight: 800; padding: 4px 8px; border: 1px solid #334155;"
        )
        badge.setSizePolicy(badge.sizePolicy().horizontalPolicy(), badge.sizePolicy().verticalPolicy())
        layout.addWidget(badge, alignment=Qt.AlignLeft)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #f8fafc; font-size: 18px; font-weight: 800;")
        layout.addWidget(title_lbl)

        # Description
        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.5;")
        desc_lbl.setWordWrap(True)
        desc_lbl.setTextFormat(Qt.RichText)
        layout.addWidget(desc_lbl)

        layout.addStretch()

        # Action Button
        btn = QPushButton(button_text)
        btn.setStyleSheet(button_style)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(on_click)
        layout.addWidget(btn)

        return card

    def _launch_analyzer(self):
        """Opens Window 1: Real-Time Wi-Fi Analyzer."""
        if self.analyzer_window is None:
            self.analyzer_window = MainWindow(
                simulate=self.simulate,
                on_back_callback=self._on_child_back
            )
            # Add a back button callback or close handler to return to launcher
            self.analyzer_window.closeEvent = self._create_child_close_event(self.analyzer_window)

        self.analyzer_window.show()
        self.analyzer_window.raise_()
        self.analyzer_window.activateWindow()
        self.hide()

    def _launch_speed_test(self):
        """Opens Window 2: Speed Limit Test."""
        if self.speed_limit_window is None:
            self.speed_limit_window = SpeedLimitWindow(
                simulate=self.simulate,
                on_back_callback=self._on_child_back
            )
            self.speed_limit_window.closeEvent = self._create_child_close_event(self.speed_limit_window)

        self.speed_limit_window.show()
        self.speed_limit_window.raise_()
        self.speed_limit_window.activateWindow()
        self.hide()

    def _on_child_back(self):
        """Returns to the selection launcher."""
        if self.speed_limit_window:
            self.speed_limit_window.hide()
        if self.analyzer_window:
            self.analyzer_window.hide()
        self.show()
        self.raise_()
        self.activateWindow()

    def _create_child_close_event(self, child_win):
        original_close = child_win.closeEvent

        def custom_close(event):
            original_close(event)
            # When child window is closed, restore launcher
            self.show()
            self.raise_()
            self.activateWindow()

        return custom_close
