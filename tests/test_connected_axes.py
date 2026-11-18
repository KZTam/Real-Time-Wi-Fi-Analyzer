"""
Unit tests for ConnectedAxisItem and graph axis alignment during window resizing.
"""

import unittest
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPainter, QImage
import pyqtgraph as pg

from wifi_analyzer.ui.connected_axis import ConnectedAxisItem
from wifi_analyzer.ui.speed_graph import SpeedGraphWidget
from wifi_analyzer.ui.signal_graph import SignalGraphWidget
from wifi_analyzer.ui.main_window import MainWindow

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestConnectedAxisItem(unittest.TestCase):
    """Tests for custom ConnectedAxisItem."""

    def test_bounding_rect_expansion(self):
        """Verify boundingRect is expanded to prevent clipping boundary labels like '0'."""
        axis_b = ConnectedAxisItem('bottom')
        axis_l = ConnectedAxisItem('left')
        
        # Test bottom expansion
        rect_b = axis_b.boundingRect()
        self.assertGreaterEqual(rect_b.width(), 0.0)
        
        # Test left expansion
        rect_l = axis_l.boundingRect()
        self.assertGreaterEqual(rect_l.height(), 0.0)

    def test_picture_invalidation_on_geometry_change(self):
        """Verify setGeometry immediately sets self.picture to None to avoid stale rendering."""
        axis = ConnectedAxisItem('left')
        axis.picture = "dummy_cached_picture"
        axis.setGeometry(QRectF(0, 0, 50, 200))
        self.assertIsNone(axis.picture)

    def test_zero_labels_preserved_and_not_clipped(self):
        """Verify both bottom and left axes preserve '0' tick label."""
        pw = pg.PlotWidget(
            axisItems={
                'bottom': ConnectedAxisItem('bottom'),
                'left': ConnectedAxisItem('left')
            }
        )
        pw.showGrid(x=True, y=True, alpha=0.25)
        pw.setXRange(0.0, 60.0, padding=0.0)
        pw.setYRange(0.0, 5.0, padding=0.0)
        pw.resize(800, 400)
        pw.show()
        app.processEvents()

        img = QImage(800, 400, QImage.Format_ARGB32)
        p = QPainter(img)
        pw.render(p)

        axis_b = pw.getAxis('bottom')
        axis_l = pw.getAxis('left')

        specs_b = axis_b.generateDrawSpecs(p)
        specs_l = axis_l.generateDrawSpecs(p)
        p.end()

        self.assertIsNotNone(specs_b)
        self.assertIsNotNone(specs_l)

        bottom_labels = [item[2] for item in specs_b[2]]
        left_labels = [item[2] for item in specs_l[2]]

        self.assertIn('0', bottom_labels)
        self.assertIn('0', left_labels)

    def test_axes_connect_at_origin(self):
        """Verify the bottom end of the left axis connects to the start of the bottom axis."""
        pw = pg.PlotWidget(
            axisItems={
                'bottom': ConnectedAxisItem('bottom'),
                'left': ConnectedAxisItem('left')
            }
        )
        pw.showGrid(x=True, y=True, alpha=0.25)
        pw.setXRange(0.0, 60.0, padding=0.0)
        pw.setYRange(0.0, 5.0, padding=0.0)
        pw.resize(1000, 500)
        pw.show()
        app.processEvents()

        img = QImage(1000, 500, QImage.Format_ARGB32)
        p = QPainter(img)
        pw.render(p)

        axis_b = pw.getAxis('bottom')
        axis_l = pw.getAxis('left')

        specs_b = axis_b.generateDrawSpecs(p)
        specs_l = axis_l.generateDrawSpecs(p)
        p.end()

        p_left_end = axis_l.mapToParent(specs_l[0][2])
        p_bottom_start = axis_b.mapToParent(specs_b[0][1])

        # They should meet at the same point in PlotItem coordinate space
        self.assertAlmostEqual(p_left_end.x(), p_bottom_start.x(), delta=1.0)
        self.assertAlmostEqual(p_left_end.y(), p_bottom_start.y(), delta=1.0)


class TestGraphWidgetsResize(unittest.TestCase):
    """Tests for SpeedGraphWidget and SignalGraphWidget resizing."""

    def test_speed_graph_resize_maintains_range(self):
        """Verify SpeedGraphWidget preserves 0 padding on resize."""
        widget = SpeedGraphWidget(window_seconds=60)
        widget.resize(1200, 600)
        widget.show()
        app.processEvents()

        # Update data
        times = np.array([0, 1, 2, 3])
        dl = np.array([1.0, 2.0, 3.0, 2.5])
        ul = np.array([0.5, 1.0, 1.2, 0.8])
        widget.update_data(times, dl, ul)
        app.processEvents()

        # Simulate resize/maximize
        widget.resize(2762, 450)
        app.processEvents()

        vb = widget.plot_widget.getPlotItem().getViewBox()
        view_range = vb.viewRange()

        self.assertEqual(view_range[0][0], 0.0)
        self.assertEqual(view_range[0][1], 60.0)
        self.assertEqual(view_range[1][0], 0.0)
        self.assertEqual(view_range[1][1], 5.0)

    def test_signal_graph_resize_maintains_range(self):
        """Verify SignalGraphWidget preserves 0 padding on resize."""
        widget = SignalGraphWidget(window_seconds=60)
        widget.resize(1200, 600)
        widget.show()
        app.processEvents()

        times = np.array([0, 1, 2, 3])
        pings = np.array([12.0, 15.0, 11.0, 14.0])
        widget.update_data(times, pings)
        app.processEvents()

        # Simulate resize/maximize
        widget.resize(2762, 450)
        app.processEvents()

        vb = widget.plot_widget.getPlotItem().getViewBox()
        view_range = vb.viewRange()

        self.assertEqual(view_range[0][0], 0.0)
        self.assertEqual(view_range[0][1], 60.0)
        self.assertEqual(view_range[1][0], 0.0)
        self.assertEqual(view_range[1][1], 25.0)


class TestMainWindowMaximize(unittest.TestCase):
    """Tests for MainWindow maximize/resize."""

    def test_main_window_maximize_axes_connection(self):
        """Verify MainWindow when maximized maintains connected axes without gap."""
        win = MainWindow(simulate=True)
        win.resize(1180, 840)
        win.show()
        app.processEvents()

        # Resize to maximized dimensions
        win.resize(2762, 933)
        app.processEvents()

        # Test showMaximized and showNormal triggering changeEvent
        win.showMaximized()
        app.processEvents()
        win.showNormal()
        app.processEvents()
        win.showMaximized()
        app.processEvents()

        speed_vb = win.speed_graph_widget.plot_widget.getPlotItem().getViewBox()
        ping_vb = win.signal_graph_widget.plot_widget.getPlotItem().getViewBox()

        self.assertEqual(speed_vb.viewRange()[0][0], 0.0)
        self.assertEqual(speed_vb.viewRange()[1][0], 0.0)
        self.assertEqual(ping_vb.viewRange()[0][0], 0.0)
        self.assertEqual(ping_vb.viewRange()[1][0], 0.0)

        win.close()


if __name__ == '__main__':
    unittest.main()
