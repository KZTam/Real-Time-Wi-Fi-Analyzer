"""
Speed Limit Test Window.
Executes an active 20-second multi-threaded saturation benchmark:
- 10 seconds of multi-threaded Download saturation
- 10 seconds of multi-threaded Upload saturation
Features separated real-time graphs for Download and Upload over a 20-second timeline.
"""

import os
import time
from typing import Optional
import numpy as np

from PyQt5.QtCore import QEvent, QTimer, Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from wifi_analyzer.data_buffer import DataBuffer
from wifi_analyzer.speed_test_engine import SpeedTestEngine, TestPhase
from wifi_analyzer.ui.benchmark_graph import DownloadBenchmarkGraph, UploadBenchmarkGraph
from wifi_analyzer.ui.stats_card import MetricCard
from wifi_analyzer.ui.styles import MAIN_STYLE_SHEET, PALETTE
from wifi_analyzer.wifi_monitor import WiFiInterfaceInfo, WiFiMonitor


class SpeedLimitWindow(QMainWindow):
    """
    Dedicated Speed Limit Test Window.
    Measures maximum achievable bandwidth using active multi-threaded saturation.
    Separates Download and Upload onto distinct 20-second graphs without RSSI or ping sections.
    """

    def __init__(self, simulate: bool = False, parent=None, on_back_callback=None):
        super().__init__(parent)
        self.simulate = simulate
        self.on_back_callback = on_back_callback

        # Engines and Monitors
        self.wifi_monitor = WiFiMonitor(simulate=self.simulate)
        self.engine = SpeedTestEngine(simulate=self.simulate, concurrency=8)
        self.data_buffer = DataBuffer(max_points=120)

        # Connection info state
        self.current_wifi_info = WiFiInterfaceInfo()

        # Data series for 10-second separated phase graphs
        self.download_times = []
        self.download_values = []
        self.upload_times = []
        self.upload_values = []

        # Session history series (kept for backwards compatibility & export)
        self.test_times = []
        self.test_downloads = []
        self.test_uploads = []

        # Timers
        self.timer_1hz = QTimer(self)
        self.timer_1hz.setInterval(1000)
        self.timer_1hz.timeout.connect(self._on_1hz_tick)

        self.timer_conn = QTimer(self)
        self.timer_conn.setInterval(5000)
        self.timer_conn.timeout.connect(self._check_wifi_connection_status)

        self._setup_ui()
        self.setStyleSheet(MAIN_STYLE_SHEET)

        # Initial connection check
        self._check_wifi_connection_status()
        self.timer_conn.start()

    def _setup_ui(self):
        self.setWindowTitle("Speed Limit Test - Active Multi-Threaded Saturation Benchmark")
        self.resize(1180, 840)
        self.setMinimumSize(900, 680)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(14, 12, 14, 12)
        root_layout.setSpacing(10)

        # 1. Connection Status Banner
        banner_frame = self._create_banner_frame()
        root_layout.addWidget(banner_frame)

        # 2. Controls Toolbar
        toolbar_frame = self._create_toolbar_frame()
        root_layout.addWidget(toolbar_frame)

        # 3. Telemetry Metric Cards Row (RSSI removed)
        cards_layout = self._create_metric_cards()
        root_layout.addLayout(cards_layout)

        # 4. Graphs Splitter (Top: Download Graph, Bottom: Upload Graph - separated!)
        splitter = QSplitter(Qt.Vertical)
        self.download_graph = DownloadBenchmarkGraph(self)
        self.upload_graph = UploadBenchmarkGraph(self)

        splitter.addWidget(self.download_graph)
        splitter.addWidget(self.upload_graph)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        root_layout.addWidget(splitter, stretch=1)

        # 5. Wi-Fi Details Strip
        details_bar = self._create_details_strip()
        root_layout.addWidget(details_bar)

        # 6. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Press 'Run Speed Test' to begin 20-second active saturation benchmark.")

    def _create_banner_frame(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("bannerFrame")
        frame.setStyleSheet(
            f"background-color: {PALETTE['bg_panel']}; border: 1px solid {PALETTE['border']}; "
            "border-radius: 8px; padding: 8px 14px;"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        app_title = QLabel("SPEED LIMIT TEST")
        app_title.setStyleSheet("color: #00e5ff; font-size: 20px; font-weight: 800; letter-spacing: 0.8px;")
        app_sub = QLabel("Active Multi-Threaded Saturation Benchmark")
        app_sub.setStyleSheet("color: #64748b; font-size: 11px;")
        title_box.addWidget(app_title)
        title_box.addWidget(app_sub)

        self.conn_badge = QLabel("● Checking Wi-Fi...")
        self.conn_badge.setStyleSheet(
            "background-color: #1e293b; color: #94a3b8; border-radius: 6px; "
            "padding: 6px 14px; font-weight: 700; font-size: 13px;"
        )

        layout.addLayout(title_box)
        layout.addStretch()
        layout.addWidget(self.conn_badge)
        return frame

    def _create_toolbar_frame(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("controlToolbar")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        # Run Button
        self.btn_run = QPushButton("▶  Run")
        self.btn_run.setObjectName("btnRun")
        self.btn_run.setToolTip("Start 20-second multi-threaded saturation test (Requires Wi-Fi)")
        self.btn_run.clicked.connect(self._start_test)
        self.btn_run.setEnabled(False)

        # Stop Button
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_test)

        # Reset Button
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setObjectName("btnReset")
        self.btn_reset.clicked.connect(self._reset_test)

        # Export Button
        self.btn_export = QPushButton("📁  Export Results")
        self.btn_export.setObjectName("btnExport")
        self.btn_export.clicked.connect(self._export_results)

        # Mode Selection Button
        self.btn_back = QPushButton("←  Mode Selection")
        self.btn_back.setStyleSheet(
            "QPushButton { background-color: #1e293b; color: #94a3b8; border: 1px solid #334155; "
            "border-radius: 6px; font-weight: 600; padding: 6px 14px; } "
            "QPushButton:hover { background-color: #334155; color: #f8fafc; }"
        )
        self.btn_back.clicked.connect(self._go_back_to_selection)

        layout.addWidget(self.btn_run)
        layout.addWidget(self.btn_stop)
        layout.addWidget(self.btn_reset)
        layout.addWidget(self.btn_export)
        layout.addStretch()
        layout.addWidget(self.btn_back)
        return frame

    def _create_metric_cards(self) -> QHBoxLayout:
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        # 1. Download Card
        self.card_download = MetricCard(
            title="Download Speed",
            initial_value="0.00",
            unit="Mbps",
            accent_color="#00e5ff",
            sub_text="Peak: 0.00 | Avg: 0.00"
        )

        # 2. Upload Card
        self.card_upload = MetricCard(
            title="Upload Speed",
            initial_value="0.00",
            unit="Mbps",
            accent_color="#00e676",
            sub_text="Peak: 0.00 | Avg: 0.00"
        )

        cards_layout.addWidget(self.card_download)
        cards_layout.addWidget(self.card_upload)
        return cards_layout

    def _create_details_strip(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("detailsStrip")
        frame.setStyleSheet(
            f"background-color: {PALETTE['bg_panel']}; border: 1px solid {PALETTE['border']}; "
            "border-radius: 6px; padding: 4px 12px;"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(18)

        self.lbl_ssid = QLabel("SSID: --")
        self.lbl_bssid = QLabel("BSSID: --")
        self.lbl_protocol = QLabel("Standard: --")
        self.lbl_rates = QLabel("Link Rate: --")
        self.lbl_local_ip = QLabel("Local IP: --")
        self.lbl_gateway = QLabel("Gateway: --")

        for lbl in [self.lbl_ssid, self.lbl_bssid, self.lbl_protocol, self.lbl_rates, self.lbl_local_ip, self.lbl_gateway]:
            lbl.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 500;")
            layout.addWidget(lbl)

        layout.addStretch()
        return frame

    def _check_wifi_connection_status(self):
        """Polls Wi-Fi connection and locks/unlocks the Run button."""
        info = self.wifi_monitor.query()
        self.current_wifi_info = info
        is_connected = info.connected or self.simulate

        if is_connected:
            ssid_name = info.ssid if info.ssid else ("Simulated-WiFi-6" if self.simulate else "Connected")
            self.conn_badge.setText(f"● Connected: {ssid_name}")
            self.conn_badge.setStyleSheet(
                "background-color: #064e3b; color: #34d399; border-radius: 6px; "
                "padding: 6px 14px; font-weight: 700; font-size: 13px; border: 1px solid #059669;"
            )
            # Unlock Run button if test is not currently running
            if not self.timer_1hz.isActive():
                self.btn_run.setEnabled(True)
                self.btn_run.setText("▶  Run")
        else:
            self.conn_badge.setText("● Wi-Fi Disconnected")
            self.conn_badge.setStyleSheet(
                "background-color: #450a0a; color: #f87171; border-radius: 6px; "
                "padding: 6px 14px; font-weight: 700; font-size: 13px; border: 1px solid #dc2626;"
            )
            if self.timer_1hz.isActive():
                self._stop_test()
                QMessageBox.warning(
                    self,
                    "Wi-Fi Disconnected",
                    "Wi-Fi connection dropped! The speed limit test has been paused.\n"
                    "Please reconnect to Wi-Fi to run the test."
                )
            self.btn_run.setEnabled(False)
            self.btn_run.setText("🔒  Wi-Fi Required")

        self._update_details_strip(info)

    def _update_details_strip(self, info: WiFiInterfaceInfo):
        """Updates hardware details strip."""
        if info.connected or self.simulate:
            ssid = info.ssid if info.ssid else "Demo-WiFi-5G"
            bssid = info.bssid if info.bssid else "34:60:F9:8A:1B:2C"
            proto = info.radio_type if info.radio_type else "802.11ax (Wi-Fi 6)"
            tx = info.tx_rate_mbps if info.tx_rate_mbps > 0 else 866.7
            rx = info.rx_rate_mbps if info.rx_rate_mbps > 0 else 866.7
            lip = info.ip_address if info.ip_address else "192.168.1.105"
            gw = info.gateway_ip if info.gateway_ip else "192.168.1.1"

            self.lbl_ssid.setText(f"SSID: <b>{ssid}</b>")
            self.lbl_bssid.setText(f"BSSID: <b>{bssid}</b>")
            self.lbl_protocol.setText(f"Protocol: <b>{proto}</b>")
            self.lbl_rates.setText(f"Link: <b>↓{rx:.0f} / ↑{tx:.0f} Mbps</b>")
            self.lbl_local_ip.setText(f"IP: <b>{lip}</b>")
            self.lbl_gateway.setText(f"Gateway: <b>{gw}</b>")
        else:
            self.lbl_ssid.setText("SSID: <span style='color:#ef4444;'>Disconnected</span>")
            self.lbl_bssid.setText("BSSID: --")
            self.lbl_protocol.setText("Protocol: --")
            self.lbl_rates.setText("Link: --")
            self.lbl_local_ip.setText("IP: --")
            self.lbl_gateway.setText("Gateway: --")

    def _start_test(self):
        """Initiates the 20-second active saturation test."""
        if not (self.current_wifi_info.connected or self.simulate):
            QMessageBox.critical(self, "Connection Error", "Cannot run speed test: No active Wi-Fi connection detected.")
            return

        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_reset.setEnabled(False)

        # Clear previous data
        self.download_times.clear()
        self.download_values.clear()
        self.upload_times.clear()
        self.upload_values.clear()
        self.test_times.clear()
        self.test_downloads.clear()
        self.test_uploads.clear()
        self.download_graph.clear()
        self.upload_graph.clear()
        self.data_buffer.clear()

        self.engine.start_test()
        self.timer_1hz.start()
        self.status_bar.showMessage("Speed Limit Test started: Phase 1/2 (Download Saturation Test)...")

    def _stop_test(self):
        """Halts test execution."""
        self.timer_1hz.stop()
        self.engine.stop_test()
        self.btn_run.setEnabled(self.current_wifi_info.connected or self.simulate)
        self.btn_stop.setEnabled(False)
        self.btn_reset.setEnabled(True)
        self.status_bar.showMessage(f"Test stopped. Tested {self.engine.current_second} seconds.")

    def _reset_test(self):
        """Clears all benchmark curves and resets counters."""
        self._stop_test()
        self.download_times.clear()
        self.download_values.clear()
        self.upload_times.clear()
        self.upload_values.clear()
        self.test_times.clear()
        self.test_downloads.clear()
        self.test_uploads.clear()
        self.download_graph.clear()
        self.upload_graph.clear()
        self.data_buffer.clear()
        self.engine.reset()

        self.card_download.update_metric("0.00", "Peak: 0.00 | Avg: 0.00")
        self.card_upload.update_metric("0.00", "Peak: 0.00 | Avg: 0.00")
        self.status_bar.showMessage("Ready. Press 'Run Speed Test' to begin 20-second active saturation benchmark.")

    def _on_1hz_tick(self):
        """1Hz step during active speed testing."""
        sample = self.engine.tick_second()

        sec = sample.second
        self.test_times.append(float(sec))
        self.test_downloads.append(sample.download_mbps)
        self.test_uploads.append(sample.upload_mbps)

        # Record to buffer for export
        self.data_buffer.append(
            download_mbps=sample.download_mbps,
            upload_mbps=sample.upload_mbps,
            ping_ms=0.0,
            rssi_dbm=-50,
            signal_percent=100
        )

        # Phase 1: Download (Seconds 1 to 10) - plots on 0..10s Download graph
        if sample.phase == TestPhase.DOWNLOAD or (1 <= sec <= 10):
            if not self.download_times:
                self.download_times.append(0.0)
                self.download_values.append(0.0)
            self.download_times.append(float(sec))
            self.download_values.append(sample.download_mbps)
            self.download_graph.update_data(
                np.array(self.download_times),
                np.array(self.download_values)
            )

        # Phase 2: Upload (Seconds 11 to 20) - plots on 0..10s Upload graph starting from 0s
        elif sample.phase == TestPhase.UPLOAD or (11 <= sec <= 20):
            upload_sec = sec - 10
            if not self.upload_times:
                self.upload_times.append(0.0)
                self.upload_values.append(0.0)
            self.upload_times.append(float(upload_sec))
            self.upload_values.append(sample.upload_mbps)
            self.upload_graph.update_data(
                np.array(self.upload_times),
                np.array(self.upload_values)
            )

        # Determine phase description & status bar text
        if sample.phase == TestPhase.DOWNLOAD or (1 <= sec <= 10):
            phase_str = f"Phase 1/2: Download ({sec}/10s)"
            status_text = f"Phase 1/2: Measuring Peak Download... [{sec}s / 10s] - Live: {sample.download_mbps:.2f} Mbps"
        elif sample.phase == TestPhase.UPLOAD or (11 <= sec <= 20):
            upload_sec = sec - 10
            phase_str = f"Phase 2/2: Upload ({upload_sec}/10s)"
            status_text = f"Phase 2/2: Measuring Peak Upload... [{upload_sec}s / 10s] - Live: {sample.upload_mbps:.2f} Mbps"
        else:
            phase_str = "Benchmark Complete"
            status_text = f"Test Complete! Peak Download: {self.engine.peak_download_mbps:.2f} Mbps | Peak Upload: {self.engine.peak_upload_mbps:.2f} Mbps"

        self.status_bar.showMessage(status_text)

        # Update Metric Cards
        if sample.phase == TestPhase.DOWNLOAD or (1 <= sec <= 10):
            self.card_download.update_metric(
                value=f"{sample.download_mbps:.2f}",
                sub_text=f"Peak: {self.engine.peak_download_mbps:.2f} | Avg: {self.engine.avg_download_mbps:.2f}"
            )
            self.card_upload.update_metric(
                value="--",
                sub_text="Awaiting Phase 2..."
            )
        elif sample.phase == TestPhase.UPLOAD or (11 <= sec <= 20):
            self.card_download.update_metric(
                value=f"{self.engine.peak_download_mbps:.2f}",
                sub_text=f"Peak: {self.engine.peak_download_mbps:.2f} | Avg: {self.engine.avg_download_mbps:.2f}"
            )
            self.card_upload.update_metric(
                value=f"{sample.upload_mbps:.2f}",
                sub_text=f"Peak: {self.engine.peak_upload_mbps:.2f} | Avg: {self.engine.avg_upload_mbps:.2f}"
            )
        else:
            self.card_download.update_metric(
                value=f"{self.engine.peak_download_mbps:.2f}",
                sub_text=f"Peak: {self.engine.peak_download_mbps:.2f} | Avg: {self.engine.avg_download_mbps:.2f}"
            )
            self.card_upload.update_metric(
                value=f"{self.engine.peak_upload_mbps:.2f}",
                sub_text=f"Peak: {self.engine.peak_upload_mbps:.2f} | Avg: {self.engine.avg_upload_mbps:.2f}"
            )

        # Check if 20-second test completed
        if sec >= 20 or sample.phase == TestPhase.COMPLETED:
            self._on_test_completed()

    def _on_test_completed(self):
        """Handles completion of the 20-second benchmark."""
        self.timer_1hz.stop()
        self.btn_run.setEnabled(self.current_wifi_info.connected or self.simulate)
        self.btn_stop.setEnabled(False)
        self.btn_reset.setEnabled(True)

        QMessageBox.information(
            self,
            "Speed Limit Benchmark Completed",
            f"<h3 style='color: #38bdf8; margin: 0 0 10px 0;'>Speed Limit Benchmark Finished!</h3>"
            f"<div style='font-size: 13px; line-height: 1.6; color: #f8fafc;'>"
            f"<b style='color: #00e5ff;'>Peak Download:</b> "
            f"<span style='color: #ffffff; font-weight: bold; font-size: 14px;'>{self.engine.peak_download_mbps:.2f} Mbps</span> "
            f"<span style='color: #94a3b8;'>(Avg: {self.engine.avg_download_mbps:.2f} Mbps)</span><br>"
            f"<b style='color: #00e676;'>Peak Upload:</b> "
            f"<span style='color: #ffffff; font-weight: bold; font-size: 14px;'>{self.engine.peak_upload_mbps:.2f} Mbps</span> "
            f"<span style='color: #94a3b8;'>(Avg: {self.engine.avg_upload_mbps:.2f} Mbps)</span><br><br>"
            f"<span style='color: #94a3b8;'>Data can now be exported using <b>Export Results</b>.</span>"
            f"</div>"
        )

    def _export_results(self):
        """Exports captured benchmark points to CSV or JSON."""
        if self.data_buffer.count() == 0:
            QMessageBox.information(self, "No Data", "There are no captured benchmark points to export.")
            return

        filepath, filter_selected = QFileDialog.getSaveFileName(
            self,
            "Export Speed Limit Benchmark",
            f"speed_limit_benchmark_{int(time.time())}.csv",
            "CSV Files (*.csv);;JSON Files (*.json)"
        )
        if not filepath:
            return

        try:
            if filepath.endswith(".json") or "JSON" in filter_selected:
                self.data_buffer.export_json(filepath)
            else:
                self.data_buffer.export_csv(filepath)

            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {self.data_buffer.count()} benchmark points to:\n{filepath}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {e}")

    def _go_back_to_selection(self):
        """Returns to the Mode Selection window."""
        self._stop_test()
        if self.on_back_callback:
            self.on_back_callback()
        else:
            self.close()

    def realign_axes(self):
        """Re-enforces exact ranges with zero padding on both graphs."""
        if hasattr(self, 'download_graph') and hasattr(self, 'upload_graph'):
            self.download_graph.realign_axes()
            self.upload_graph.realign_axes()

    def changeEvent(self, event):
        """Handles window state changes (such as maximize / restore) to re-align axes."""
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            self.realign_axes()

    def resizeEvent(self, event):
        """Handles window resize events to maintain connected axes."""
        super().resizeEvent(event)
        self.realign_axes()

    def closeEvent(self, event):
        """Cleanup timers and active background workers on exit."""
        self.timer_1hz.stop()
        self.timer_conn.stop()
        self.engine.stop_test()
        event.accept()
