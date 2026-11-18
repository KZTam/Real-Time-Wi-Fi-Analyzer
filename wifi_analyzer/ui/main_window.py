"""
Main Dashboard Window for Real-Time Wi-Fi Analyzer.
Coordinates 1Hz updates, Wi-Fi connection enforcement, telemetry graphs, and controls.
"""

# Standard Library imports
import os
import time
from typing import Optional

# PyQt5 imports
from PyQt5.QtCore import QEvent, QTimer, Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QAction,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

#custom python module imports
from wifi_analyzer.active_probe import ActiveSpeedProber
from wifi_analyzer.data_buffer import DataBuffer
from wifi_analyzer.ping_monitor import PingMonitor
from wifi_analyzer.speed_monitor import SpeedMonitor
from wifi_analyzer.ui.signal_graph import SignalGraphWidget
from wifi_analyzer.ui.speed_graph import SpeedGraphWidget
from wifi_analyzer.ui.stats_card import MetricCard
from wifi_analyzer.ui.styles import MAIN_STYLE_SHEET, PALETTE
from wifi_analyzer.wifi_monitor import WiFiInterfaceInfo, WiFiMonitor


class MainWindow(QMainWindow):
    """
    Primary Application Window.
    Enforces Wi-Fi connection requirement before allowing analysis.
    """

    def __init__(self, simulate: bool = False):
        super().__init__()
        self.simulate = simulate
        self.is_running = False
        self.start_timestamp: Optional[float] = None
        self.selected_window_seconds: int = 60

        # Core subsystems
        self.wifi_monitor = WiFiMonitor(simulate=self.simulate)
        self.speed_monitor = SpeedMonitor(simulate=self.simulate)
        self.ping_monitor = PingMonitor(simulate=self.simulate)
        self.active_prober = ActiveSpeedProber(enabled=False)
        self.data_buffer = DataBuffer(max_points=1200)

        # Current state snapshot
        self.current_wifi_info = WiFiInterfaceInfo()

        # Timers
        self.timer_1hz = QTimer(self)
        self.timer_1hz.setInterval(1000)  # Exactly 1Hz (1 update per second)
        self.timer_1hz.timeout.connect(self._on_1hz_tick)

        # Connection check (5 seconds)
        self.timer_conn_checker = QTimer(self)
        self.timer_conn_checker.setInterval(5000)
        self.timer_conn_checker.timeout.connect(self._check_wifi_connection_status)

        self._setup_ui()
        self.setStyleSheet(MAIN_STYLE_SHEET)

        # Initial check
        self._check_wifi_connection_status()
        self.timer_conn_checker.start()

    def _setup_ui(self):
        self.setWindowTitle("Real-Time Wi-Fi Analyzer")
        self.resize(1180, 840)
        self.setMinimumSize(900, 680)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(14, 12, 14, 12)
        root_layout.setSpacing(10)

        # 1. Connection Status Banner & Title
        banner_frame = self._create_banner_frame()
        root_layout.addWidget(banner_frame)

        # 2. Controls Toolbar
        toolbar_frame = self._create_toolbar_frame()
        root_layout.addWidget(toolbar_frame)

        # 3. Telemetry Metric Cards Row
        cards_layout = self._create_metric_cards()
        root_layout.addLayout(cards_layout)

        # 4. Graphs Splitter (Top: Speed Graph, Bottom: Ping Latency Graph)
        splitter = QSplitter(Qt.Vertical)
        self.speed_graph_widget = SpeedGraphWidget(self)
        self.signal_graph_widget = SignalGraphWidget(self)

        splitter.addWidget(self.speed_graph_widget)
        splitter.addWidget(self.signal_graph_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        root_layout.addWidget(splitter, stretch=1)

        # 5. Wi-Fi Details Strip
        details_bar = self._create_details_strip()
        root_layout.addWidget(details_bar)

        # 6. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Wi-Fi status checked.")

    def _create_banner_frame(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("bannerFrame")
        frame.setStyleSheet(
            f"background-color: {PALETTE['bg_panel']}; border: 1px solid {PALETTE['border']}; "
            "border-radius: 8px; padding: 8px 14px;"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)

        # Left: App Title
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        app_title = QLabel("REAL-TIME WI-FI ANALYZER")
        app_title.setStyleSheet("color: #38bdf8; font-size: 20px; font-weight: 800; letter-spacing: 0.8px;")
        app_sub = QLabel("Live Throughput, Ping & RSSI Signal Analyzer")
        app_sub.setStyleSheet("color: #64748b; font-size: 11px;")
        title_box.addWidget(app_title)
        title_box.addWidget(app_sub)

        # Right: Prominent Wi-Fi Connection Status Indicator
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
        self.btn_run.setToolTip("Start real-time 1Hz Wi-Fi analysis (Requires Wi-Fi connection)")
        self.btn_run.clicked.connect(self._toggle_run)
        self.btn_run.setEnabled(False)  # Disabled until Wi-Fi connection is confirmed!

        # Stop Button
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_analyzer)

        # Reset Button
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setToolTip("Clear real-time history and curves")
        self.btn_reset.clicked.connect(self._reset_analyzer)

        # Ping Target Dropdown
        lbl_target = QLabel("Ping Target:")
        lbl_target.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.combo_ping_target = QComboBox()
        self.combo_ping_target.addItem("Wi-Fi Gateway (Router)", "gateway")
        self.combo_ping_target.addItem("Cloudflare (1.1.1.1)", "1.1.1.1")
        self.combo_ping_target.addItem("Google DNS (8.8.8.8)", "8.8.8.8")
        self.combo_ping_target.currentIndexChanged.connect(self._on_ping_target_changed)

        # Active Probe Toggle
        self.chk_active_probe = QCheckBox("Active Speed Prober")
        self.chk_active_probe.setToolTip(
            "Burst small download/upload streams every second to test maximum available bandwidth."
        )
        self.chk_active_probe.toggled.connect(self._on_active_probe_toggled)

        # Window Size Dropdown
        lbl_window = QLabel("Window:")
        lbl_window.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.combo_window = QComboBox()
        self.combo_window.addItem("60 seconds", 60)
        self.combo_window.addItem("30 seconds", 30)
        self.combo_window.addItem("120 seconds", 120)
        self.combo_window.addItem("300 seconds", 300)
        self.combo_window.currentIndexChanged.connect(self._on_window_changed)

        # Simulation Mode Toggle
        self.chk_simulate = QCheckBox("Simulation Mode")
        self.chk_simulate.setChecked(self.simulate)
        self.chk_simulate.setToolTip("Simulate Wi-Fi telemetry for testing or demonstration")
        self.chk_simulate.toggled.connect(self._on_simulation_toggled)

        # Export Button
        self.btn_export = QPushButton("📥  Export Data")
        self.btn_export.setToolTip("Export captured session data to CSV or JSON")
        self.btn_export.clicked.connect(self._export_data)

        layout.addWidget(self.btn_run)
        layout.addWidget(self.btn_stop)
        layout.addWidget(self.btn_reset)
        layout.addSpacing(10)
        layout.addWidget(lbl_target)
        layout.addWidget(self.combo_ping_target)
        layout.addWidget(self.chk_active_probe)
        layout.addSpacing(10)
        layout.addWidget(lbl_window)
        layout.addWidget(self.combo_window)
        layout.addWidget(self.chk_simulate)
        layout.addStretch()
        layout.addWidget(self.btn_export)

        return frame

    def _create_metric_cards(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)

        # Card 1: Download Speed
        self.card_download = MetricCard(
            title="Download Speed",
            initial_value="0.00",
            unit="Mbps",
            accent_color=PALETTE["download_cyan"],
            sub_text="Peak: 0.00 | Avg: 0.00"
        )

        # Card 2: Upload Speed
        self.card_upload = MetricCard(
            title="Upload Speed",
            initial_value="0.00",
            unit="Mbps",
            accent_color=PALETTE["upload_green"],
            sub_text="Peak: 0.00 | Avg: 0.00"
        )

        # Card 3: Ping Latency
        self.card_ping = MetricCard(
            title="Ping Latency",
            initial_value="--",
            unit="ms",
            accent_color=PALETTE["ping_amber"],
            sub_text="Jitter: -- ms | Loss: 0%"
        )

        # Card 4: Signal RSSI
        self.card_rssi = MetricCard(
            title="Signal RSSI",
            initial_value="--",
            unit="dBm",
            accent_color=PALETTE["rssi_magenta"],
            sub_text="Quality: --% | Ch: --"
        )

        layout.addWidget(self.card_download)
        layout.addWidget(self.card_upload)
        layout.addWidget(self.card_ping)
        layout.addWidget(self.card_rssi)
        return layout

    def _create_details_strip(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {PALETTE['bg_panel']}; border: 1px solid {PALETTE['border']}; "
            "border-radius: 6px; padding: 6px 12px;"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(6, 4, 6, 4)

        self.lbl_details_ssid = QLabel("SSID: --")
        self.lbl_details_bssid = QLabel("BSSID: --")
        self.lbl_details_band = QLabel("Band: --")
        self.lbl_details_standard = QLabel("Standard: --")
        self.lbl_details_rates = QLabel("Link Rate: --")
        self.lbl_details_ip = QLabel("IP / GW: --")

        for lbl in [
            self.lbl_details_ssid,
            self.lbl_details_bssid,
            self.lbl_details_band,
            self.lbl_details_standard,
            self.lbl_details_rates,
            self.lbl_details_ip
        ]:
            lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            layout.addWidget(lbl)
            if lbl != self.lbl_details_ip:
                sep = QLabel("•")
                sep.setStyleSheet("color: #334155;")
                layout.addWidget(sep)

        layout.addStretch()
        return frame

    # =========================================================================
    # Wi-Fi Connection Checker & Enforcement
    # =========================================================================
    def _check_wifi_connection_status(self):
        """
        Polls Wi-Fi interface status.
        ENFORCEMENT: 'Run' analyzer is only permitted when connected to Wi-Fi.
        """
        info = self.wifi_monitor.query()
        self.current_wifi_info = info

        if info.connected:
            # Wi-Fi is connected
            self.conn_badge.setText(
                f"● Connected to: {info.ssid} ({info.band}, Ch {info.channel})"
            )
            self.conn_badge.setStyleSheet(
                "background-color: #064e3b; color: #34d399; border: 1px solid #059669; "
                "border-radius: 6px; padding: 6px 14px; font-weight: 700; font-size: 13px;"
            )
            if not self.is_running:
                self.btn_run.setEnabled(True)
                self.btn_run.setToolTip("Start real-time 1Hz Wi-Fi analysis")

            # Update interface details strip
            self.lbl_details_ssid.setText(f"SSID: <b style='color:#f1f5f9'>{info.ssid}</b>")
            self.lbl_details_bssid.setText(f"BSSID: {info.bssid}")
            self.lbl_details_band.setText(f"Band: {info.band} (Ch {info.channel})")
            self.lbl_details_standard.setText(f"Standard: {info.radio_type}")
            self.lbl_details_rates.setText(f"Link: {info.rx_rate_mbps} / {info.tx_rate_mbps} Mbps")
            self.lbl_details_ip.setText(f"IP: {info.ip_address} | GW: {info.gateway_ip}")

            # Keep speed monitor targeting the Wi-Fi interface
            if info.name:
                self.speed_monitor.set_interface(info.name)

        else:
            # Wi-Fi is DISCONNECTED
            self.conn_badge.setText("● Disconnected from Wi-Fi — Connect to Wi-Fi to Run")
            self.conn_badge.setStyleSheet(
                "background-color: #450a0a; color: #f87171; border: 1px solid #dc2626; "
                "border-radius: 6px; padding: 6px 14px; font-weight: 700; font-size: 13px;"
            )

            # If user was running and connection dropped, abort and warn!
            if self.is_running:
                self._stop_analyzer()
                QMessageBox.warning(
                    self,
                    "Wi-Fi Disconnected",
                    "Wi-Fi connection lost! The analyzer requires an active Wi-Fi connection and has been stopped."
                )

            self.btn_run.setEnabled(False)
            self.btn_run.setToolTip("Analyzer disabled: Laptop must be connected to Wi-Fi first.")

            self.lbl_details_ssid.setText("SSID: <span style='color:#ef4444'>Disconnected</span>")
            self.lbl_details_bssid.setText("BSSID: --")
            self.lbl_details_band.setText("Band: --")
            self.lbl_details_standard.setText("Standard: --")
            self.lbl_details_rates.setText("Link: --")
            self.lbl_details_ip.setText("IP / GW: --")

    # =========================================================================
    # Run / Stop / Reset Handlers
    # =========================================================================
    def _toggle_run(self):
        """Starts or pauses the analyzer."""
        if not self.current_wifi_info.connected and not self.simulate:
            QMessageBox.warning(
                self,
                "Cannot Run",
                "The Wi-Fi analyzer can only be run when the laptop is connected to Wi-Fi.\n"
                "Please connect to a Wi-Fi network and try again."
            )
            return

        if not self.is_running:
            self._start_analyzer()
        else:
            self._stop_analyzer()

    def _start_analyzer(self):
        """Begins 1Hz real-time analysis."""
        self.is_running = True
        self.start_timestamp = time.time()
        self.btn_run.setText("⏸  Pause")
        self.btn_run.setStyleSheet(
            "background-color: #d97706; border: 1px solid #f59e0b; color: #ffffff; font-weight: bold;"
        )
        self.btn_stop.setEnabled(True)

        # Configure ping target
        self._update_ping_target()

        # Trigger immediate first ping
        self.ping_monitor.trigger_probe()

        # Start 1Hz timer
        self.timer_1hz.start()
        self.status_bar.showMessage("Real-Time Wi-Fi Analyzer RUNNING (1Hz updates)...")

    def _stop_analyzer(self):
        """Pauses the 1Hz analysis."""
        self.is_running = False
        self.timer_1hz.stop()
        self.btn_run.setText("▶  Run")
        self.btn_run.setStyleSheet("")
        self.btn_stop.setEnabled(False)
        self.status_bar.showMessage("Real-Time Wi-Fi Analyzer STOPPED.")

    def _reset_analyzer(self):
        """Clears buffers, charts, and statistics."""
        was_running = self.is_running
        if was_running:
            self._stop_analyzer()

        self.data_buffer.reset()
        self.speed_monitor.reset_counters()
        self.speed_graph_widget.clear()
        self.signal_graph_widget.clear()

        self.card_download.update_metric("0.00", sub_text="Peak: 0.00 | Avg: 0.00")
        self.card_upload.update_metric("0.00", sub_text="Peak: 0.00 | Avg: 0.00")
        self.card_ping.update_metric("--", sub_text="Jitter: -- ms | Loss: 0%")
        self.card_rssi.update_metric("--", sub_text="Quality: --% | Ch: --")

        self.status_bar.showMessage("Analyzer reset. Ready.")

    # =========================================================================
    # 1Hz Real-Time Updater (Main Analysis Loop)
    # =========================================================================
    def _on_1hz_tick(self):
        """
        Executed exactly once per second (1Hz) when running.
        Queries speed, ping, and RSSI, appends to buffer, and updates graphs.
        """
        # 1. Verify Wi-Fi connection is still active
        wifi_info = self.wifi_monitor.query()
        self.current_wifi_info = wifi_info

        if not wifi_info.connected and not self.simulate:
            self._stop_analyzer()
            self._check_wifi_connection_status()
            QMessageBox.warning(
                self,
                "Connection Lost",
                "Wi-Fi connection dropped! The analyzer requires an active Wi-Fi connection and has been stopped."
            )
            return

        # 2. Sample Upload & Download Speed (in Mbps)
        speed_sample = self.speed_monitor.sample()

        # 3. Read Ping latency (ms) from background monitor
        ping_res = self.ping_monitor.get_latest()
        ping_ms = ping_res.latency_ms if (ping_res and ping_res.success) else None

        # 4. Read RSSI (dBm) and Signal Quality (%)
        rssi_dbm = wifi_info.rssi_dbm
        signal_pct = wifi_info.signal_percent

        # 5. Append to Circular Buffer
        self.data_buffer.append(
            download_mbps=speed_sample.download_mbps,
            upload_mbps=speed_sample.upload_mbps,
            ping_ms=ping_ms,
            rssi_dbm=rssi_dbm,
            signal_percent=signal_pct,
            ssid=wifi_info.ssid,
            channel=wifi_info.channel,
            band=wifi_info.band
        )

        # 6. Extract data series for graphs according to selected window
        ts_data = self.data_buffer.get_time_series(window_seconds=self.selected_window_seconds)

        # 7. Update Graph 1: Real-time Throughput (Mbps) at 1Hz
        self.speed_graph_widget.update_data(
            times=ts_data["time"],
            downloads=ts_data["download"],
            uploads=ts_data["upload"],
            window_seconds=self.selected_window_seconds
        )

        # 8. Update Graph 2: Real-time Ping Latency (ms) at 1Hz
        self.signal_graph_widget.update_data(
            times=ts_data["time"],
            pings=ts_data["ping"],
            window_seconds=self.selected_window_seconds
        )

        # 9. Update Telemetry Cards
        speed_stats = self.speed_monitor.get_stats()
        self.card_download.update_metric(
            f"{speed_sample.download_mbps:.2f}",
            sub_text=f"Peak: {speed_stats['peak_download_mbps']:.1f} | Avg: {speed_stats['avg_download_mbps']:.1f}"
        )
        self.card_upload.update_metric(
            f"{speed_sample.upload_mbps:.2f}",
            sub_text=f"Peak: {speed_stats['peak_upload_mbps']:.1f} | Avg: {speed_stats['avg_upload_mbps']:.1f}"
        )

        ping_stats = self.ping_monitor.get_stats()
        ping_disp = f"{ping_ms:.1f}" if ping_ms is not None else "TIMEOUT"
        self.card_ping.update_metric(
            ping_disp,
            sub_text=f"Jitter: {ping_stats['jitter_ms']:.1f} ms | Loss: {ping_stats['loss_percent']:.0f}%"
        )

        rssi_disp = f"{rssi_dbm}"
        self.card_rssi.update_metric(
            rssi_disp,
            sub_text=f"Quality: {signal_pct}%"
        )

        # 10. Update Status Bar
        elapsed = int(time.time() - self.start_timestamp) if self.start_timestamp else 0
        self.status_bar.showMessage(
            f"RUNNING | Elapsed: {elapsed}s | Samples: {self.data_buffer.count()} | "
            f"Total DL: {speed_stats['total_download_mb']:.1f} MB | Total UL: {speed_stats['total_upload_mb']:.1f} MB | "
            f"Interface: {speed_sample.interface_name}"
        )

        # 11. Trigger next asynchronous ping probe and active speed burst for the next 1Hz tick
        self.ping_monitor.trigger_probe()
        if self.active_prober.is_enabled():
            self.active_prober.trigger_burst()

    # =========================================================================
    # Settings & Export Controls
    # =========================================================================
    def _update_ping_target(self):
        target_mode = self.combo_ping_target.currentData()
        if target_mode == "gateway":
            gw = self.current_wifi_info.gateway_ip or "192.168.1.1"
            self.ping_monitor.set_target(gw)
        else:
            self.ping_monitor.set_target(target_mode)

    def _on_ping_target_changed(self):
        self._update_ping_target()

    def _on_active_probe_toggled(self, checked: bool):
        self.active_prober.set_enabled(checked)
        if checked:
            self.status_bar.showMessage("Active speed prober ENABLED (transmitting 1s test bursts).", 3000)
        else:
            self.status_bar.showMessage("Active speed prober DISABLED (passive traffic monitor only).", 3000)

    def _on_window_changed(self):
        self.selected_window_seconds = self.combo_window.currentData()
        self.speed_graph_widget.set_window_seconds(self.selected_window_seconds)
        self.signal_graph_widget.set_window_seconds(self.selected_window_seconds)
        if self.is_running:
            self._on_1hz_tick()
        else:
            ts_data = self.data_buffer.get_time_series(window_seconds=self.selected_window_seconds)
            self.speed_graph_widget.update_data(
                times=ts_data["time"],
                downloads=ts_data["download"],
                uploads=ts_data["upload"],
                window_seconds=self.selected_window_seconds
            )
            self.signal_graph_widget.update_data(
                times=ts_data["time"],
                pings=ts_data["ping"],
                window_seconds=self.selected_window_seconds
            )

    def _on_simulation_toggled(self, checked: bool):
        self.simulate = checked
        self.wifi_monitor.simulate = checked
        self.speed_monitor.simulate = checked
        self.ping_monitor.simulate = checked
        self._check_wifi_connection_status()

    def _export_data(self):
        """Exports captured points to CSV or JSON."""
        if self.data_buffer.count() == 0:
            QMessageBox.information(self, "No Data", "There are no captured telemetry points to export.")
            return

        filepath, filter_selected = QFileDialog.getSaveFileName(
            self,
            "Export Wi-Fi Telemetry",
            f"wifi_telemetry_{int(time.time())}.csv",
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
                f"Successfully exported {self.data_buffer.count()} telemetry records to:\n{filepath}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {e}")

    def changeEvent(self, event):
        """Handles window state changes (such as maximize / restore) to re-align axes."""
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            if hasattr(self, 'speed_graph_widget') and hasattr(self, 'signal_graph_widget'):
                self.speed_graph_widget.realign_axes()
                self.signal_graph_widget.realign_axes()

    def resizeEvent(self, event):
        """Handles window resize events to maintain connected axes."""
        super().resizeEvent(event)
        if hasattr(self, 'speed_graph_widget') and hasattr(self, 'signal_graph_widget'):
            self.speed_graph_widget.realign_axes()
            self.signal_graph_widget.realign_axes()

    def closeEvent(self, event):
        """Cleanup timers and active background workers on exit."""
        self.timer_1hz.stop()
        self.timer_conn_checker.stop()
        self.active_prober.set_enabled(False)
        event.accept()
