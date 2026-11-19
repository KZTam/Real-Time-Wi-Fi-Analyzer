"""
Active Multi-Threaded Speed Test Saturation Engine.
Executes a 20-second multi-threaded saturation burst:
- Seconds 1 to 10: Multi-threaded Download saturation test
- Seconds 11 to 20: Multi-threaded Upload saturation test
Measures peak achievable bandwidth without excessive memory accumulation.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
import random
import threading
import time
from typing import Callable, List, Optional
import urllib.request
import psutil


class TestPhase(Enum):
    IDLE = "IDLE"
    DOWNLOAD = "DOWNLOAD"
    UPLOAD = "UPLOAD"
    COMPLETED = "COMPLETED"


@dataclass
class SpeedBenchmarkSample:
    """Telemetry sample recorded at 1Hz during the speed limit benchmark."""
    second: int                     # 1 to 20
    phase: TestPhase
    download_mbps: float
    upload_mbps: float
    timestamp: float


class SpeedTestEngine:
    """
    Orchestrates the 20-second active speed limit saturation test.
    Phase 1 (Seconds 1-10): Multi-threaded Download Saturation
    Phase 2 (Seconds 11-20): Multi-threaded Upload Saturation
    """

    DOWNLOAD_ENDPOINTS = [
        "https://speed.cloudflare.com/__down?bytes=50000000",
        "https://proof.ovh.net/files/100Mb.dat",
        "https://speedtest.tele2.net/100MB.zip",
        "https://speed.cloudflare.com/__down?bytes=25000000",
    ]

    UPLOAD_ENDPOINTS = [
        "https://speed.cloudflare.com/__up",
        "https://httpbin.org/post",
    ]

    def __init__(
        self,
        interface_name: Optional[str] = None,
        simulate: bool = False,
        concurrency: int = 8
    ):
        self.interface_name = interface_name
        self.simulate = simulate
        self.concurrency = concurrency

        self.phase = TestPhase.IDLE
        self.current_second = 0
        self.total_seconds = 20
        self.download_phase_duration = 10
        self.upload_phase_duration = 10

        self.peak_download_mbps = 0.0
        self.peak_upload_mbps = 0.0
        self.avg_download_mbps = 0.0
        self.avg_upload_mbps = 0.0

        self._sum_download = 0.0
        self._count_download = 0
        self._sum_upload = 0.0
        self._count_upload = 0

        self._stop_workers = threading.Event()
        self._worker_threads: List[threading.Thread] = []
        self._lock = threading.Lock()

        # Dummy buffer for uploads (1MB reusable buffer)
        self._upload_dummy_buffer = b'X' * (1024 * 1024)

        # Baseline network byte tracking
        self._last_sample_time: Optional[float] = None
        self._last_bytes_recv = 0
        self._last_bytes_sent = 0

        # Internal byte counters from workers (fallback if pernic not resolved)
        self._worker_bytes_recv = 0
        self._worker_bytes_sent = 0
        self._last_worker_recv = 0
        self._last_worker_sent = 0

        self._init_baseline()

    def _resolve_interface(self) -> str:
        """Finds the most suitable active Wi-Fi interface."""
        counters = psutil.net_io_counters(pernic=True)
        if not counters:
            return "Wi-Fi"

        if self.interface_name and self.interface_name in counters:
            return self.interface_name

        for name in counters.keys():
            lower = name.lower()
            if "wi-fi" in lower or "wlan" in lower or "wireless" in lower:
                self.interface_name = name
                return name

        for name, stat in counters.items():
            if stat.bytes_recv > 0 and "loopback" not in name.lower():
                self.interface_name = name
                return name

        first = list(counters.keys())[0]
        self.interface_name = first
        return first

    def _init_baseline(self):
        """Initializes baseline network interface counters."""
        self._last_sample_time = time.time()
        if not self.simulate:
            iface = self._resolve_interface()
            counters = psutil.net_io_counters(pernic=True)
            if iface in counters:
                stat = counters[iface]
                self._last_bytes_recv = stat.bytes_recv
                self._last_bytes_sent = stat.bytes_sent

    def start_test(self):
        """Starts the 20-second benchmark sequence."""
        self.reset()
        self.current_second = 0
        self._start_download_phase()

    def reset(self):
        """Stops any active workers and resets test state."""
        self._stop_all_workers()
        with self._lock:
            self.phase = TestPhase.IDLE
            self.current_second = 0
            self.peak_download_mbps = 0.0
            self.peak_upload_mbps = 0.0
            self.avg_download_mbps = 0.0
            self.avg_upload_mbps = 0.0
            self._sum_download = 0.0
            self._count_download = 0
            self._sum_upload = 0.0
            self._count_upload = 0
            self._worker_bytes_recv = 0
            self._worker_bytes_sent = 0
            self._last_worker_recv = 0
            self._last_worker_sent = 0
        self._init_baseline()

    def stop_test(self):
        """Prematurely stops the test."""
        self._stop_all_workers()
        self.phase = TestPhase.IDLE

    def _stop_all_workers(self):
        """Signals worker threads to exit immediately."""
        self._stop_workers.set()
        for t in self._worker_threads:
            t.join(timeout=0.2)
        self._worker_threads.clear()
        self._stop_workers.clear()

    def _start_download_phase(self):
        """Launches multi-threaded download saturation workers."""
        self._stop_all_workers()
        self.phase = TestPhase.DOWNLOAD
        self._init_baseline()

        if self.simulate:
            return

        for i in range(self.concurrency):
            t = threading.Thread(target=self._download_worker, args=(i,), daemon=True)
            self._worker_threads.append(t)
            t.start()

    def _start_upload_phase(self):
        """Launches multi-threaded upload saturation workers."""
        self._stop_all_workers()
        self.phase = TestPhase.UPLOAD
        self._init_baseline()

        if self.simulate:
            return

        for i in range(self.concurrency):
            t = threading.Thread(target=self._upload_worker, args=(i,), daemon=True)
            self._worker_threads.append(t)
            t.start()

    def _download_worker(self, worker_id: int):
        """Worker thread continuously downloading chunks from high-speed CDNs."""
        endpoint = self.DOWNLOAD_ENDPOINTS[worker_id % len(self.DOWNLOAD_ENDPOINTS)]
        while not self._stop_workers.is_set():
            try:
                req = urllib.request.Request(
                    endpoint,
                    headers={'User-Agent': 'RealTimeWiFiSpeedTest/1.0'}
                )
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    while not self._stop_workers.is_set():
                        chunk = resp.read(65536)  # 64 KB chunk
                        if not chunk:
                            break
                        with self._lock:
                            self._worker_bytes_recv += len(chunk)
            except Exception:
                time.sleep(0.1)

    def _upload_worker(self, worker_id: int):
        """Worker thread continuously uploading dummy payload chunks."""
        endpoint = self.UPLOAD_ENDPOINTS[worker_id % len(self.UPLOAD_ENDPOINTS)]
        while not self._stop_workers.is_set():
            try:
                req = urllib.request.Request(
                    endpoint,
                    data=self._upload_dummy_buffer,
                    headers={
                        'User-Agent': 'RealTimeWiFiSpeedTest/1.0',
                        'Content-Type': 'application/octet-stream'
                    },
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=3.0):
                    with self._lock:
                        self._worker_bytes_sent += len(self._upload_dummy_buffer)
            except Exception:
                time.sleep(0.1)

    def tick_second(self) -> SpeedBenchmarkSample:
        """
        Advances the benchmark by 1 second (invoked at 1Hz).
        Calculates instantaneous saturation throughput and controls phase transitions.
        """
        self.current_second += 1
        now = time.time()
        dt = now - self._last_sample_time if self._last_sample_time else 1.0
        if dt <= 0:
            dt = 1.0

        download_mbps = 0.0
        upload_mbps = 0.0

        # Phase State Machine
        if self.current_second == 1:
            self._start_download_phase()

        elif self.current_second == 11:
            self._start_upload_phase()

        elif self.current_second > 20:
            self._stop_all_workers()
            self.phase = TestPhase.COMPLETED
            return SpeedBenchmarkSample(
                second=20,
                phase=TestPhase.COMPLETED,
                download_mbps=0.0,
                upload_mbps=0.0,
                timestamp=now
            )

        # Measure 1Hz Throughput
        if self.simulate:
            download_mbps, upload_mbps = self._simulate_step(self.current_second)
        else:
            download_mbps, upload_mbps = self._measure_actual_step(dt)

        # Update Aggregates
        if self.phase == TestPhase.DOWNLOAD:
            upload_mbps = 0.0  # Upload is inactive in Phase 1
            self.peak_download_mbps = max(self.peak_download_mbps, download_mbps)
            self._sum_download += download_mbps
            self._count_download += 1
            self.avg_download_mbps = self._sum_download / self._count_download
        elif self.phase == TestPhase.UPLOAD:
            download_mbps = 0.0  # Download is inactive in Phase 2
            self.peak_upload_mbps = max(self.peak_upload_mbps, upload_mbps)
            self._sum_upload += upload_mbps
            self._count_upload += 1
            self.avg_upload_mbps = self._sum_upload / self._count_upload

        # If at second 20, wrap up
        if self.current_second >= 20:
            self._stop_all_workers()
            self.phase = TestPhase.COMPLETED

        return SpeedBenchmarkSample(
            second=min(20, self.current_second),
            phase=self.phase,
            download_mbps=download_mbps,
            upload_mbps=upload_mbps,
            timestamp=now
        )

    def _measure_actual_step(self, dt: float) -> tuple:
        """Measures actual NIC transfer bytes over dt."""
        iface = self._resolve_interface()
        counters = psutil.net_io_counters(pernic=True)

        download_mbps = 0.0
        upload_mbps = 0.0

        if iface in counters:
            stat = counters[iface]
            delta_recv = max(0, stat.bytes_recv - self._last_bytes_recv)
            delta_sent = max(0, stat.bytes_sent - self._last_bytes_sent)
            self._last_bytes_recv = stat.bytes_recv
            self._last_bytes_sent = stat.bytes_sent
            download_mbps = (delta_recv * 8.0) / (dt * 1e6)
            upload_mbps = (delta_sent * 8.0) / (dt * 1e6)
        else:
            # Fallback to worker counters
            with self._lock:
                delta_w_recv = max(0, self._worker_bytes_recv - self._last_worker_recv)
                delta_w_sent = max(0, self._worker_bytes_sent - self._last_worker_sent)
                self._last_worker_recv = self._worker_bytes_recv
                self._last_worker_sent = self._worker_bytes_sent
            download_mbps = (delta_w_recv * 8.0) / (dt * 1e6)
            upload_mbps = (delta_w_sent * 8.0) / (dt * 1e6)

        self._last_sample_time = time.time()
        return round(download_mbps, 2), round(upload_mbps, 2)

    def _simulate_step(self, sec: int) -> tuple:
        """Simulates realistic high-speed saturation bursts for testing/demo."""
        if sec <= 10:
            # Phase 1: Download Saturation (ramp up to ~85-115 Mbps)
            base = 80.0 + (sec / 10.0) * 20.0
            noise = random.uniform(-6.0, 8.0)
            dl = max(30.0, base + noise)
            ul = 0.0
        else:
            # Phase 2: Upload Saturation (ramp up to ~35-55 Mbps)
            rel_sec = sec - 10
            base = 35.0 + (rel_sec / 10.0) * 15.0
            noise = random.uniform(-4.0, 5.0)
            dl = 0.0
            ul = max(15.0, base + noise)
        self._last_sample_time = time.time()
        return round(dl, 2), round(ul, 2)
