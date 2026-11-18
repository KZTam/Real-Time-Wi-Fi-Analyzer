"""
Real-time Network Speed Monitor.
Calculates instantaneous Upload and Download speeds (in Mbps) at 1Hz intervals.
"""

from dataclasses import dataclass
import random
import time
from typing import Optional
import psutil


@dataclass
class SpeedSample:
    """Snapshot of upload and download speeds at a specific time."""
    download_mbps: float
    upload_mbps: float
    timestamp: float
    interface_name: str


class SpeedMonitor:
    """
    Monitors Wi-Fi interface I/O counters and computes exact 1Hz speed in Mbps.
    """

    def __init__(self, interface_name: Optional[str] = None, simulate: bool = False):
        self.interface_name = interface_name
        self.simulate = simulate

        self._last_time: Optional[float] = None
        self._last_bytes_recv: int = 0
        self._last_bytes_sent: int = 0

        # Aggregated session statistics
        self.peak_download_mbps: float = 0.0
        self.peak_upload_mbps: float = 0.0
        self.total_bytes_recv: int = 0
        self.total_bytes_sent: int = 0
        self._samples_count: int = 0
        self._sum_download_mbps: float = 0.0
        self._sum_upload_mbps: float = 0.0

        self._init_counters()

    def set_interface(self, name: str):
        """Updates the target network interface."""
        if name and name != self.interface_name:
            self.interface_name = name
            self.reset_counters()

    def reset_counters(self):
        """Resets baseline counters and stats."""
        self._last_time = None
        self._last_bytes_recv = 0
        self._last_bytes_sent = 0
        self.peak_download_mbps = 0.0
        self.peak_upload_mbps = 0.0
        self.total_bytes_recv = 0
        self.total_bytes_sent = 0
        self._samples_count = 0
        self._sum_download_mbps = 0.0
        self._sum_upload_mbps = 0.0
        self._init_counters()

    def _resolve_interface(self) -> str:
        """Finds the most suitable Wi-Fi interface name among available adapters."""
        counters = psutil.net_io_counters(pernic=True)
        if not counters:
            return "Wi-Fi"

        # Explicit interface if present
        if self.interface_name and self.interface_name in counters:
            return self.interface_name

        # Look for Wi-Fi / WLAN keywords
        for name in counters.keys():
            lower = name.lower()
            if "wi-fi" in lower or "wlan" in lower or "wireless" in lower:
                self.interface_name = name
                return name

        # Fallback to the first adapter with received bytes
        for name, stat in counters.items():
            if stat.bytes_recv > 0 and "loopback" not in name.lower():
                self.interface_name = name
                return name

        first_key = list(counters.keys())[0]
        self.interface_name = first_key
        return first_key

    def _init_counters(self):
        """Records initial baseline byte counters."""
        if self.simulate:
            self._last_time = time.time()
            return

        target_iface = self._resolve_interface()
        counters = psutil.net_io_counters(pernic=True)
        if target_iface in counters:
            stat = counters[target_iface]
            self._last_bytes_recv = stat.bytes_recv
            self._last_bytes_sent = stat.bytes_sent
            self._last_time = time.time()

    def sample(self) -> SpeedSample:
        """
        Calculates instantaneous Upload and Download speeds in Mbps since last sample.
        Typically invoked once per second (1Hz).
        """
        now = time.time()

        if self.simulate:
            return self._simulate_sample(now)

        target_iface = self._resolve_interface()
        counters = psutil.net_io_counters(pernic=True)

        if target_iface not in counters:
            return SpeedSample(download_mbps=0.0, upload_mbps=0.0, timestamp=now, interface_name=target_iface)

        stat = counters[target_iface]
        curr_recv = stat.bytes_recv
        curr_sent = stat.bytes_sent

        if self._last_time is None:
            self._last_time = now
            self._last_bytes_recv = curr_recv
            self._last_bytes_sent = curr_sent
            return SpeedSample(download_mbps=0.0, upload_mbps=0.0, timestamp=now, interface_name=target_iface)

        dt = now - self._last_time
        if dt <= 0:
            dt = 1.0

        # Handle counter rollover or reset
        delta_recv = curr_recv - self._last_bytes_recv
        delta_sent = curr_sent - self._last_bytes_sent
        if delta_recv < 0:
            delta_recv = 0
        if delta_sent < 0:
            delta_sent = 0

        # Convert Bytes/s to Megabits/s: (Bytes * 8) / (1_000_000 * dt)
        download_mbps = (delta_recv * 8.0) / (dt * 1_000_000.0)
        upload_mbps = (delta_sent * 8.0) / (dt * 1_000_000.0)

        # Update running stats
        self._last_time = now
        self._last_bytes_recv = curr_recv
        self._last_bytes_sent = curr_sent
        self.total_bytes_recv += delta_recv
        self.total_bytes_sent += delta_sent

        self.peak_download_mbps = max(self.peak_download_mbps, download_mbps)
        self.peak_upload_mbps = max(self.peak_upload_mbps, upload_mbps)

        self._samples_count += 1
        self._sum_download_mbps += download_mbps
        self._sum_upload_mbps += upload_mbps

        return SpeedSample(
            download_mbps=round(download_mbps, 2),
            upload_mbps=round(upload_mbps, 2),
            timestamp=now,
            interface_name=target_iface
        )

    def _simulate_sample(self, now: float) -> SpeedSample:
        """Generates dynamic simulated speeds with realistic Wi-Fi fluctuations."""
        # Simulated base traffic
        dl = max(0.2, random.gauss(45.0, 15.0))
        ul = max(0.1, random.gauss(18.0, 6.0))

        # Occasional burst
        if random.random() < 0.15:
            dl += random.uniform(20.0, 50.0)
            ul += random.uniform(10.0, 25.0)

        dl = round(dl, 2)
        ul = round(ul, 2)

        self.peak_download_mbps = max(self.peak_download_mbps, dl)
        self.peak_upload_mbps = max(self.peak_upload_mbps, ul)
        self._samples_count += 1
        self._sum_download_mbps += dl
        self._sum_upload_mbps += ul

        return SpeedSample(
            download_mbps=dl,
            upload_mbps=ul,
            timestamp=now,
            interface_name="Wi-Fi (Simulated)"
        )

    def get_stats(self) -> dict:
        """Returns statistical summary of speeds and data volume."""
        avg_dl = (self._sum_download_mbps / self._samples_count) if self._samples_count > 0 else 0.0
        avg_ul = (self._sum_upload_mbps / self._samples_count) if self._samples_count > 0 else 0.0
        total_dl_mb = (self.total_bytes_recv / 1_000_000.0)
        total_ul_mb = (self.total_bytes_sent / 1_000_000.0)

        return {
            "peak_download_mbps": round(self.peak_download_mbps, 2),
            "peak_upload_mbps": round(self.peak_upload_mbps, 2),
            "avg_download_mbps": round(avg_dl, 2),
            "avg_upload_mbps": round(avg_ul, 2),
            "total_download_mb": round(total_dl_mb, 2),
            "total_upload_mb": round(total_ul_mb, 2),
            "samples_count": self._samples_count
        }
