"""
Real-time Network Speed (Upload and Download in Mbps) Graph Widget.
Updated at 1Hz using PyQtGraph with antialiased rendering, translucent area fills,
and strict connected axis alignment preventing data from exceeding the graph boundaries
or detaching during window resize and maximize.
"""

from typing import Optional
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout
import pyqtgraph as pg

from wifi_analyzer.ui.connected_axis import ConnectedAxisItem


class SpeedGraphWidget(QFrame):
    """
    Real-time 1Hz plot widget displaying Download and Upload throughput in Mbps.
    Uses custom ConnectedAxisItem to keep X and Y axes firmly attached at (0, 0)
    with no corner gaps or missing origin tick labels during window resizing.
    """

    def __init__(self, parent=None, window_seconds: int = 60):
        super().__init__(parent)
        self.window_seconds = window_seconds
        self.current_x_min = 0.0
        self.current_x_max = float(self.window_seconds)
        self.current_y_max = 5.0

        self.setStyleSheet("background-color: #171c26; border-radius: 8px; border: 1px solid #283347;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Header title with current speed indicators
        header_layout = QHBoxLayout()
        title_label = QLabel("REAL-TIME THROUGHPUT")
        title_label.setStyleSheet("color: #94a3b8; font-weight: 700; font-size: 12px; letter-spacing: 0.5px;")

        self.legend_dl = QLabel("● Download: 0.00 Mbps")
        self.legend_dl.setStyleSheet("color: #00e5ff; font-weight: 600; font-size: 12px;")

        self.legend_ul = QLabel("● Upload: 0.00 Mbps")
        self.legend_ul.setStyleSheet("color: #00e676; font-weight: 600; font-size: 12px; margin-left: 12px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.legend_dl)
        header_layout.addWidget(self.legend_ul)

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
        self.plot_widget.setLabel('left', 'Speed', units='Mbps', color='#94a3b8', size='11pt')
        self.plot_widget.setLabel('bottom', 'Elapsed Time', units='s', color='#94a3b8', size='11pt')

        # Lock ViewBox to prevent accidental mouse dragging/zooming off-axis
        pi = self.plot_widget.getPlotItem()
        vb = pi.getViewBox()
        vb.disableAutoRange()
        vb.setMouseEnabled(x=False, y=False)
        vb.setLimits(xMin=0.0, yMin=0.0)
        vb.setMenuEnabled(False)
        vb.setBorder(pg.mkPen('#283347', width=1))
        pi.hideButtons()

        # Download curve (Cyan)
        dl_pen = QPen(QColor("#00e5ff"), 2.2)
        dl_brush = QColor(0, 229, 255, 35)
        self.curve_download = self.plot_widget.plot(
            pen=dl_pen,
            fillLevel=0.0,
            fillBrush=dl_brush,
            name="Download"
        )

        # Upload curve (Green)
        ul_pen = QPen(QColor("#00e676"), 2.2)
        ul_brush = QColor(0, 230, 118, 35)
        self.curve_upload = self.plot_widget.plot(
            pen=ul_pen,
            fillLevel=0.0,
            fillBrush=ul_brush,
            name="Upload"
        )

        # Strict initial range with padding=0.0 to guarantee unbroken corner connection
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

    def set_window_seconds(self, window_seconds: int):
        """Updates the time window length."""
        self.window_seconds = max(10, window_seconds)
        self.current_x_max = float(self.window_seconds)

    def update_data(
        self,
        times: np.ndarray,
        downloads: np.ndarray,
        uploads: np.ndarray,
        window_seconds: Optional[int] = None
    ):
        """Updates the graph curves with new 1Hz time-series data."""
        if window_seconds is not None:
            self.window_seconds = max(10, window_seconds)

        if len(times) == 0:
            self.curve_download.setData([], [])
            self.curve_upload.setData([], [])
            self.legend_dl.setText("● Download: 0.00 Mbps")
            self.legend_ul.setText("● Upload: 0.00 Mbps")
            self.current_x_min = 0.0
            self.current_x_max = float(self.window_seconds)
            self.current_y_max = 5.0
            vb = self.plot_widget.getPlotItem().getViewBox()
            vb.disableAutoRange()
            self.plot_widget.setXRange(self.current_x_min, self.current_x_max, padding=0.0)
            self.plot_widget.setYRange(0.0, self.current_y_max, padding=0.0)
            return

        self.curve_download.setData(times, downloads)
        self.curve_upload.setData(times, uploads)

        # Update header quick readouts
        latest_dl = downloads[-1] if len(downloads) > 0 else 0.0
        latest_ul = uploads[-1] if len(uploads) > 0 else 0.0
        self.legend_dl.setText(f"● Download: {latest_dl:.2f} Mbps")
        self.legend_ul.setText(f"● Upload: {latest_ul:.2f} Mbps")

        # Dynamically scale Y axis to clean integer ceilings, strictly starting at y=0.0
        max_speed = max(
            np.max(downloads) if len(downloads) > 0 else 0.0,
            np.max(uploads) if len(uploads) > 0 else 0.0
        )
        if max_speed <= 4.0:
            self.current_y_max = 5.0
        elif max_speed <= 8.0:
            self.current_y_max = 10.0
        elif max_speed <= 18.0:
            self.current_y_max = 20.0
        elif max_speed <= 45.0:
            self.current_y_max = 50.0
        elif max_speed <= 90.0:
            self.current_y_max = 100.0
        else:
            self.current_y_max = float(int(np.ceil(max_speed * 1.25 / 50.0)) * 50)

        # Compute strictly bounded X-axis range to prevent data from exceeding axes
        latest_t = times[-1]
        if latest_t <= self.window_seconds:
            self.current_x_min = 0.0
            self.current_x_max = float(self.window_seconds)
        else:
            self.current_x_max = float(latest_t)
            self.current_x_min = float(latest_t - self.window_seconds)

        vb = self.plot_widget.getPlotItem().getViewBox()
        vb.disableAutoRange()
        self.plot_widget.setXRange(self.current_x_min, self.current_x_max, padding=0.0)
        self.plot_widget.setYRange(0.0, self.current_y_max, padding=0.0)

    def clear(self):
        """Clears curves and resets graph."""
        self.curve_download.setData([], [])
        self.curve_upload.setData([], [])
        self.legend_dl.setText("● Download: 0.00 Mbps")
        self.legend_ul.setText("● Upload: 0.00 Mbps")
        self.current_x_min = 0.0
        self.current_x_max = float(self.window_seconds)
        self.current_y_max = 5.0
        vb = self.plot_widget.getPlotItem().getViewBox()
        vb.disableAutoRange()
        self.plot_widget.setXRange(self.current_x_min, self.current_x_max, padding=0.0)
        self.plot_widget.setYRange(0.0, self.current_y_max, padding=0.0)
