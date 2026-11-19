"""
Dedicated 10-Second Benchmark Graph Widget.
Visualizes single-metric throughput (in Mbps) over a fixed 10-second timeline.
Uses ConnectedAxisItem to guarantee axes stay firmly connected at (0, 0)
with no corner gaps or missing origin tick labels.
"""

from typing import Optional
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout
import pyqtgraph as pg

from wifi_analyzer.ui.connected_axis import ConnectedAxisItem


class BenchmarkGraphWidget(QFrame):
    """
    Real-time 1Hz benchmark plot widget with a fixed 10-second X-axis timeline.
    Separates Download and Upload into dedicated full-height visualization panels.
    """

    def __init__(
        self,
        title: str,
        metric_name: str,
        color_hex: str,
        units: str = "Mbps",
        parent=None
    ):
        super().__init__(parent)
        self.metric_name = metric_name
        self.color_hex = color_hex
        self.units = units
        self.window_seconds = 10

        self.current_x_min = 0.0
        self.current_x_max = 10.0
        self.current_y_max = 50.0

        self.setStyleSheet("background-color: #171c26; border-radius: 8px; border: 1px solid #283347;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Header title with current and peak readouts
        header_layout = QHBoxLayout()
        title_label = QLabel(title.upper())
        title_label.setStyleSheet("color: #94a3b8; font-weight: 700; font-size: 12px; letter-spacing: 0.5px;")

        self.legend_current = QLabel(f"● {metric_name}: 0.00 {units}")
        self.legend_current.setStyleSheet(f"color: {color_hex}; font-weight: 600; font-size: 12px;")

        self.legend_peak = QLabel(f"Peak: 0.00 {units}")
        self.legend_peak.setStyleSheet("color: #64748b; font-weight: 600; font-size: 12px; margin-left: 12px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.legend_current)
        header_layout.addWidget(self.legend_peak)

        # PyQtGraph PlotWidget with ConnectedAxisItem on both bottom and left
        pg.setConfigOptions(antialias=True)
        self.plot_widget = pg.PlotWidget(
            axisItems={
                'bottom': ConnectedAxisItem('bottom'),
                'left': ConnectedAxisItem('left')
            }
        )
        self.plot_widget.setBackground('#11151f')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.25)
        self.plot_widget.setLabel('left', metric_name, units=units, color=color_hex, size='11pt')
        self.plot_widget.setLabel('bottom', 'Test Timeline', units='s', color='#94a3b8', size='11pt')

        # Lock ViewBox to prevent accidental mouse dragging/zooming off-axis
        pi = self.plot_widget.getPlotItem()
        vb = pi.getViewBox()
        vb.disableAutoRange()
        vb.setMouseEnabled(x=False, y=False)
        vb.setLimits(xMin=0.0, yMin=0.0)
        vb.setMenuEnabled(False)
        vb.setBorder(pg.mkPen('#283347', width=1))
        pi.hideButtons()

        # Throughput curve with translucent area fill
        curve_color = QColor(color_hex)
        pen = QPen(curve_color, 2.4)
        brush = QColor(curve_color.red(), curve_color.green(), curve_color.blue(), 40)
        self.curve = self.plot_widget.plot(
            pen=pen,
            fillLevel=0.0,
            fillBrush=brush,
            name=metric_name
        )

        # Strict initial range: exactly 0 to 10 seconds with padding=0.0
        self.plot_widget.setXRange(self.current_x_min, self.current_x_max, padding=0.0)
        self.plot_widget.setYRange(0.0, self.current_y_max, padding=0.0)

        layout.addLayout(header_layout)
        layout.addWidget(self.plot_widget)

    def realign_axes(self):
        """Re-enforces exact ranges with zero padding to keep axes firmly attached."""
        vb = self.plot_widget.getPlotItem().getViewBox()
        vb.disableAutoRange()
        self.plot_widget.setXRange(self.current_x_min, self.current_x_max, padding=0.0)
        self.plot_widget.setYRange(0.0, self.current_y_max, padding=0.0)

    def resizeEvent(self, event):
        """Re-enforces exact ranges with zero padding on resize/maximize."""
        super().resizeEvent(event)
        self.realign_axes()

    def update_data(self, times: np.ndarray, values: np.ndarray):
        """Updates the graph curve with time-series data up to 10 seconds."""
        if len(times) == 0:
            self.clear()
            return

        self.curve.setData(times, values)

        latest_val = float(values[-1]) if len(values) > 0 else 0.0
        peak_val = float(np.max(values)) if len(values) > 0 else 0.0

        self.legend_current.setText(f"● {self.metric_name}: {latest_val:.2f} {self.units}")
        self.legend_peak.setText(f"Peak: {peak_val:.2f} {self.units}")

        # Dynamic scale for Y axis with clean integer ceilings
        if peak_val <= 20.0:
            self.current_y_max = 25.0
        elif peak_val <= 40.0:
            self.current_y_max = 50.0
        elif peak_val <= 80.0:
            self.current_y_max = 100.0
        elif peak_val <= 120.0:
            self.current_y_max = 150.0
        elif peak_val <= 180.0:
            self.current_y_max = 200.0
        elif peak_val <= 270.0:
            self.current_y_max = 300.0
        elif peak_val <= 450.0:
            self.current_y_max = 500.0
        else:
            self.current_y_max = float(int(np.ceil(peak_val * 1.25 / 100.0)) * 100)

        self.current_x_min = 0.0
        self.current_x_max = 10.0

        vb = self.plot_widget.getPlotItem().getViewBox()
        vb.disableAutoRange()
        self.plot_widget.setXRange(self.current_x_min, self.current_x_max, padding=0.0)
        self.plot_widget.setYRange(0.0, self.current_y_max, padding=0.0)

    def clear(self):
        """Clears curves and resets graph to initial 10-second view."""
        self.curve.setData([], [])
        self.legend_current.setText(f"● {self.metric_name}: 0.00 {self.units}")
        self.legend_peak.setText(f"Peak: 0.00 {self.units}")
        self.current_x_min = 0.0
        self.current_x_max = 10.0
        self.current_y_max = 50.0
        self.realign_axes()


class DownloadBenchmarkGraph(BenchmarkGraphWidget):
    """Specialized Download speed benchmark graph (Electric Cyan)."""
    def __init__(self, parent=None):
        super().__init__(
            title="DOWNLOAD BANDWIDTH",
            metric_name="Download",
            color_hex="#00e5ff",
            units="Mbps",
            parent=parent
        )


class UploadBenchmarkGraph(BenchmarkGraphWidget):
    """Specialized Upload speed benchmark graph (Emerald Green)."""
    def __init__(self, parent=None):
        super().__init__(
            title="UPLOAD BANDWIDTH",
            metric_name="Upload",
            color_hex="#00e676",
            units="Mbps",
            parent=parent
        )
