"""
Unit tests for Speed Limit Test, Multi-Threaded Engine, and Mode Selection Window.
"""

import sys
import unittest
import numpy as np
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtWidgets import QApplication

from wifi_analyzer.speed_test_engine import SpeedTestEngine, TestPhase
from wifi_analyzer.ui.benchmark_graph import (
    BenchmarkGraphWidget,
    DownloadBenchmarkGraph,
    UploadBenchmarkGraph,
)
from wifi_analyzer.ui.selection_window import SelectionWindow
from wifi_analyzer.ui.speed_limit_window import SpeedLimitWindow

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestSpeedTestEngine(unittest.TestCase):
    """Tests for SpeedTestEngine phases and saturation progression."""

    def setUp(self):
        self.engine = SpeedTestEngine(simulate=True, concurrency=4)

    def test_engine_initial_state(self):
        """Verify engine begins in IDLE phase with 0 counters."""
        self.assertEqual(self.engine.phase, TestPhase.IDLE)
        self.assertEqual(self.engine.current_second, 0)
        self.assertEqual(self.engine.peak_download_mbps, 0.0)
        self.assertEqual(self.engine.peak_upload_mbps, 0.0)

    def test_20_second_phase_progression(self):
        """Verify 1-10s is Download phase, 11-20s is Upload phase, and completion at 20s."""
        self.engine.start_test()

        # Seconds 1 to 10: Download phase
        for sec in range(1, 11):
            sample = self.engine.tick_second()
            self.assertEqual(sample.second, sec)
            self.assertEqual(sample.phase, TestPhase.DOWNLOAD)
            self.assertGreater(sample.download_mbps, 0.0)
            self.assertEqual(sample.upload_mbps, 0.0)

        self.assertGreater(self.engine.peak_download_mbps, 0.0)

        # Seconds 11 to 20: Upload phase
        for sec in range(11, 21):
            sample = self.engine.tick_second()
            self.assertEqual(sample.second, sec)
            self.assertIn(sample.phase, [TestPhase.UPLOAD, TestPhase.COMPLETED])
            self.assertEqual(sample.download_mbps, 0.0)
            self.assertGreater(sample.upload_mbps, 0.0)

        self.assertGreater(self.engine.peak_upload_mbps, 0.0)
        self.assertEqual(self.engine.phase, TestPhase.COMPLETED)

    def test_engine_reset(self):
        """Verify reset returns engine to initial state."""
        self.engine.start_test()
        self.engine.tick_second()
        self.engine.tick_second()
        self.engine.reset()

        self.assertEqual(self.engine.phase, TestPhase.IDLE)
        self.assertEqual(self.engine.current_second, 0)
        self.assertEqual(self.engine.peak_download_mbps, 0.0)
        self.assertEqual(self.engine.peak_upload_mbps, 0.0)


class TestBenchmarkGraphs(unittest.TestCase):
    """Tests for DownloadBenchmarkGraph and UploadBenchmarkGraph."""

    def test_graph_initial_range_and_axis_connection(self):
        """Verify graphs enforce fixed 0..10s X-axis and connected axes at (0, 0)."""
        dl_graph = DownloadBenchmarkGraph()
        ul_graph = UploadBenchmarkGraph()

        dl_graph.resize(800, 300)
        ul_graph.resize(800, 300)
        dl_graph.show()
        ul_graph.show()
        app.processEvents()

        # Check view ranges
        dl_vb = dl_graph.plot_widget.getPlotItem().getViewBox()
        ul_vb = ul_graph.plot_widget.getPlotItem().getViewBox()

        dl_range = dl_vb.viewRange()
        ul_range = ul_vb.viewRange()

        self.assertEqual(dl_range[0][0], 0.0)
        self.assertEqual(dl_range[0][1], 10.0)
        self.assertEqual(dl_range[1][0], 0.0)

        self.assertEqual(ul_range[0][0], 0.0)
        self.assertEqual(ul_range[0][1], 10.0)
        self.assertEqual(ul_range[1][0], 0.0)

        dl_graph.close()
        ul_graph.close()

    def test_graph_data_update_within_10s(self):
        """Verify graph updates plot curve within 10s timeline."""
        graph = DownloadBenchmarkGraph()
        times = np.array([1, 2, 3, 4, 5])
        speeds = np.array([50.0, 75.0, 95.0, 88.0, 92.0])
        graph.update_data(times, speeds)
        app.processEvents()

        vb = graph.plot_widget.getPlotItem().getViewBox()
        x_range = vb.viewRange()[0]
        self.assertEqual(x_range[0], 0.0)
        self.assertEqual(x_range[1], 10.0)
        graph.close()


class TestSpeedLimitWindow(unittest.TestCase):
    """Tests for SpeedLimitWindow structure and behavior."""

    def setUp(self):
        self.window = SpeedLimitWindow(simulate=True)
        self.window.resize(1180, 840)
        self.window.show()
        app.processEvents()

    def tearDown(self):
        self.window.close()

    def test_ui_components_presence_and_absence(self):
        """Verify RSSI section, Active Prober, and Benchmark Phase widget are removed, and graphs are separated."""
        # Active prober should NOT be an attribute
        self.assertFalse(hasattr(self.window, 'chk_active_probe'))

        # RSSI card should NOT exist
        self.assertFalse(hasattr(self.window, 'card_rssi'))

        # Benchmark Phase card should NOT exist
        self.assertFalse(hasattr(self.window, 'card_progress'))

        # Download and Upload graphs are present and separated
        self.assertTrue(isinstance(self.window.download_graph, DownloadBenchmarkGraph))
        self.assertTrue(isinstance(self.window.upload_graph, UploadBenchmarkGraph))
        self.assertIsNot(self.window.download_graph, self.window.upload_graph)

    def test_full_20_second_test_execution(self):
        """Verify start_test executes 20-second burst and finishes with completion state."""
        from unittest.mock import patch
        with patch('PyQt5.QtWidgets.QMessageBox.information') as mock_info:
            self.window._start_test()
            self.assertTrue(self.window.timer_1hz.isActive())
            self.assertFalse(self.window.btn_run.isEnabled())
            self.assertTrue(self.window.btn_stop.isEnabled())

            # Simulate 20 ticks
            for _ in range(20):
                self.window._on_1hz_tick()
                app.processEvents()

            # At second 20, timer should have stopped and test finished
            self.assertFalse(self.window.timer_1hz.isActive())
            self.assertTrue(self.window.btn_run.isEnabled())
            self.assertFalse(self.window.btn_stop.isEnabled())
            self.assertGreater(self.window.engine.peak_download_mbps, 0.0)
            self.assertGreater(self.window.engine.peak_upload_mbps, 0.0)
            mock_info.assert_called_once()

            # Verify download times and upload times both span 0 to 10 seconds
            self.assertEqual(self.window.download_times[0], 0.0)
            self.assertEqual(self.window.download_times[-1], 10.0)
            self.assertEqual(self.window.upload_times[0], 0.0)
            self.assertEqual(self.window.upload_times[-1], 10.0)

            # Verify graphs have 10s timeline
            dl_vb = self.window.download_graph.plot_widget.getViewBox()
            ul_vb = self.window.upload_graph.plot_widget.getViewBox()
            self.assertEqual(dl_vb.viewRange()[0][1], 10.0)
            self.assertEqual(ul_vb.viewRange()[0][1], 10.0)


    def test_main_window_mode_selection_button(self):
        """Verify MainWindow has Mode Selection button that invokes callback."""
        from wifi_analyzer.ui.main_window import MainWindow

        called = []
        def on_back():
            called.append(True)

        win = MainWindow(simulate=True, on_back_callback=on_back)
        self.assertTrue(hasattr(win, 'btn_back'))
        self.assertIn("Mode Selection", win.btn_back.text())

        # Start analyzer, then click back
        win._start_analyzer()
        self.assertTrue(win.is_running)

        win.btn_back.click()
        app.processEvents()

        self.assertFalse(win.is_running)
        self.assertEqual(called, [True])
        win.close()


    def test_qmessagebox_dark_theme_styling(self):
        """Verify QMessageBox inherits dark theme with high-contrast text and dark background."""
        from PyQt5.QtWidgets import QLabel, QMessageBox
        msg = QMessageBox(self.window)
        msg.setText("Speed test completed")
        msg.show()
        app.processEvents()

        # Verify dark background and crisp bright text
        bg_color = msg.palette().color(msg.backgroundRole()).name()
        lbl = msg.findChild(QLabel, "qt_msgbox_label")
        fg_color = lbl.palette().color(lbl.foregroundRole()).name() if lbl else None

        self.assertEqual(bg_color, "#171c26")
        self.assertEqual(fg_color, "#f8fafc")
        msg.close()


class TestSelectionWindow(unittest.TestCase):
    """Tests for Mode Selection Window."""

    def test_selection_window_launching(self):
        """Verify SelectionWindow creates cards and can launch windows."""
        launcher = SelectionWindow(simulate=True)
        launcher.show()
        app.processEvents()

        # Launch analyzer
        launcher._launch_analyzer()
        self.assertIsNotNone(launcher.analyzer_window)
        self.assertTrue(launcher.analyzer_window.isVisible())
        self.assertFalse(launcher.isVisible())

        # Click mode selection button from analyzer window to return
        launcher.analyzer_window.btn_back.click()
        app.processEvents()
        self.assertTrue(launcher.isVisible())
        self.assertFalse(launcher.analyzer_window.isVisible())

        # Launch speed limit test
        launcher._launch_speed_test()
        self.assertIsNotNone(launcher.speed_limit_window)
        self.assertTrue(launcher.speed_limit_window.isVisible())
        self.assertFalse(launcher.isVisible())

        # Click mode selection button from speed limit window to return
        launcher.speed_limit_window.btn_back.click()
        app.processEvents()
        self.assertTrue(launcher.isVisible())
        self.assertFalse(launcher.speed_limit_window.isVisible())

        launcher.close()
        if launcher.analyzer_window:
            launcher.analyzer_window.close()
        if launcher.speed_limit_window:
            launcher.speed_limit_window.close()


if __name__ == '__main__':
    unittest.main()
