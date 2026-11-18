"""
Telemetry Metric Card Widget.
Displays high-visibility real-time metrics with units and sub-statistics.
"""

from typing import Optional
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class MetricCard(QFrame):
    """
    Card displaying an individual telemetry metric with title, primary value,
    unit, and auxiliary statistics.
    """

    def __init__(
        self,
        title: str,
        initial_value: str = "--",
        unit: str = "",
        accent_color: str = "#00e5ff",
        sub_text: str = "--",
        parent=None
    ):
        super().__init__(parent)
        self.setProperty("class", "metricCard")
        self.accent_color = accent_color

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(4)

        # Header: Title + Dot Indicator
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        self.dot = QLabel("●")
        self.dot.setStyleSheet(f"color: {accent_color}; font-size: 14px;")
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")

        header_layout.addWidget(self.dot)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        # Value Row: Main Value + Unit
        value_layout = QHBoxLayout()
        value_layout.setSpacing(4)
        value_layout.setAlignment(Qt.AlignLeft | Qt.AlignBaseline)

        self.val_label = QLabel(initial_value)
        self.val_label.setStyleSheet(
            f"color: {accent_color}; font-size: 26px; font-weight: 800; font-family: 'Segoe UI', monospace;"
        )

        self.unit_label = QLabel(unit)
        self.unit_label.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600; margin-left: 2px;")

        value_layout.addWidget(self.val_label)
        value_layout.addWidget(self.unit_label)
        value_layout.addStretch()

        # Footer: Sub-statistics
        self.sub_label = QLabel(sub_text)
        self.sub_label.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 500;")

        main_layout.addLayout(header_layout)
        main_layout.addLayout(value_layout)
        main_layout.addWidget(self.sub_label)

    def update_metric(self, value: str, sub_text: Optional[str] = None, unit: Optional[str] = None):
        """Updates the metric display."""
        self.val_label.setText(value)
        if sub_text is not None:
            self.sub_label.setText(sub_text)
        if unit is not None:
            self.unit_label.setText(unit)
