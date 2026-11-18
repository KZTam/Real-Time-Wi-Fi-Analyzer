"""
Time-series ring buffer for real-time Wi-Fi telemetry.
Stores data points, computes rolling metrics, and exports data.
"""

from collections import deque
import csv
from dataclasses import asdict, dataclass
import json
import time
from typing import List, Optional
import numpy as np


@dataclass
class TelemetryPoint:
    """Single 1Hz telemetry snapshot."""
    timestamp: float
    relative_time: float
    download_mbps: float
    upload_mbps: float
    ping_ms: Optional[float]
    rssi_dbm: int
    signal_percent: int
    ssid: str
    channel: int
    band: str


class DataBuffer:
    """
    Manages circular ring buffers for continuous 1Hz real-time graph plotting and export.
    """

    def __init__(self, max_points: int = 600):
        self.max_points = max_points
        self._points: deque[TelemetryPoint] = deque(maxlen=max_points)
        self._start_time: Optional[float] = None

    def reset(self):
        """Clears all stored telemetry history."""
        self._points.clear()
        self._start_time = None

    def append(
        self,
        download_mbps: float,
        upload_mbps: float,
        ping_ms: Optional[float],
        rssi_dbm: int,
        signal_percent: int,
        ssid: str = "",
        channel: int = 0,
        band: str = ""
    ):
        """Appends a new 1Hz telemetry snapshot to the circular buffer."""
        now = time.time()
        if self._start_time is None:
            self._start_time = now

        relative_t = now - self._start_time
        point = TelemetryPoint(
            timestamp=now,
            relative_time=round(relative_t, 1),
            download_mbps=download_mbps,
            upload_mbps=upload_mbps,
            ping_ms=ping_ms,
            rssi_dbm=rssi_dbm,
            signal_percent=signal_percent,
            ssid=ssid,
            channel=channel,
            band=band
        )
        self._points.append(point)

    def count(self) -> int:
        return len(self._points)

    def get_time_series(self, window_seconds: Optional[int] = None):
        """
        Extracts synchronized numpy arrays for pyqtgraph plotting.
        If window_seconds is provided, only the most recent N seconds are returned.
        """
        if not self._points:
            return {
                "time": np.array([], dtype=float),
                "download": np.array([], dtype=float),
                "upload": np.array([], dtype=float),
                "ping": np.array([], dtype=float),
                "rssi": np.array([], dtype=float),
                "signal": np.array([], dtype=float),
            }

        points = list(self._points)
        if window_seconds and len(points) > window_seconds:
            points = points[-window_seconds:]

        times = np.array([p.relative_time for p in points], dtype=float)
        downloads = np.array([p.download_mbps for p in points], dtype=float)
        uploads = np.array([p.upload_mbps for p in points], dtype=float)

        # Handle None pings by propagating last valid or 0.0 for graphing
        pings = []
        last_valid_ping = 0.0
        for p in points:
            if p.ping_ms is not None:
                last_valid_ping = p.ping_ms
                pings.append(p.ping_ms)
            else:
                pings.append(last_valid_ping)
        pings_arr = np.array(pings, dtype=float)

        rssis = np.array([p.rssi_dbm for p in points], dtype=float)
        signals = np.array([p.signal_percent for p in points], dtype=float)

        return {
            "time": times,
            "download": downloads,
            "upload": uploads,
            "ping": pings_arr,
            "rssi": rssis,
            "signal": signals,
        }

    def export_csv(self, filepath: str):
        """Exports the recorded telemetry session to a CSV file."""
        points = list(self._points)
        if not points:
            return

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Timestamp", "RelativeTime_s", "Download_Mbps", "Upload_Mbps",
                "Ping_ms", "RSSI_dBm", "Signal_Percent", "SSID", "Channel", "Band"
            ])
            for p in points:
                writer.writerow([
                    time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(p.timestamp)),
                    p.relative_time,
                    p.download_mbps,
                    p.upload_mbps,
                    p.ping_ms if p.ping_ms is not None else "TIMEOUT",
                    p.rssi_dbm,
                    p.signal_percent,
                    p.ssid,
                    p.channel,
                    p.band
                ])

    def export_json(self, filepath: str):
        """Exports the recorded telemetry session to a JSON file."""
        points = [asdict(p) for p in self._points]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(points, f, indent=2)
