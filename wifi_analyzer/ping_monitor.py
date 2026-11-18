"""
Asynchronous and non-blocking Ping Monitor.
Measures real-time latency (in ms) to the Wi-Fi default gateway or Internet host.
"""

from collections import deque
from dataclasses import dataclass
import os
import platform
import random
import re
import subprocess
import threading
import time
from typing import Deque, Optional


@dataclass
class PingResult:
    """Represents a single ping measurement result."""
    target: str
    latency_ms: Optional[float]  # None if timed out / failed
    timestamp: float
    success: bool
    error: str = ""


class PingMonitor:
    """
    Executes ping probes in the background without blocking the UI.
    Computes real-time latency, jitter, and packet loss.
    """

    def __init__(self, target: str = "192.168.100.1", timeout_ms: int = 800, max_history: int = 300, simulate: bool = False):
        self.target = target
        self.timeout_ms = timeout_ms
        self.simulate = simulate
        self.max_history = max_history

        self._lock = threading.Lock()
        self._history: Deque[PingResult] = deque(maxlen=max_history)
        self._last_result: Optional[PingResult] = None
        self._is_probing = False

        # Jitter calculation state (RFC 1889)
        self._jitter: float = 0.0
        self._last_latency: Optional[float] = None

        self._packets_sent = 0
        self._packets_lost = 0

    def set_target(self, new_target: str):
        """Updates the ping destination target."""
        with self._lock:
            if new_target != self.target:
                self.target = new_target
                self._packets_sent = 0
                self._packets_lost = 0
                self._last_latency = None
                self._jitter = 0.0

    def get_latest(self) -> Optional[PingResult]:
        """Returns the most recent ping result in a thread-safe manner."""
        with self._lock:
            return self._last_result

    def trigger_probe(self, target: Optional[str] = None):
        """
        Launches an asynchronous probe in a daemon worker thread if not already running.
        """
        if self._is_probing:
            return  # Previous probe still in flight; avoids thread pile-up

        host = target or self.target
        self._is_probing = True
        thread = threading.Thread(target=self._run_probe_thread, args=(host,), daemon=True)
        thread.start()

    def _run_probe_thread(self, host: str):
        try:
            if self.simulate:
                res = self._simulate_ping(host)
            else:
                res = self._execute_ping(host)

            with self._lock:
                self._last_result = res
                self._history.append(res)
                self._packets_sent += 1

                if res.success and res.latency_ms is not None:
                    # Update jitter (RFC 1889 / 3550): J = J + (|D(i-1, i)| - J) / 16
                    if self._last_latency is not None:
                        diff = abs(res.latency_ms - self._last_latency)
                        self._jitter += (diff - self._jitter) / 16.0
                    self._last_latency = res.latency_ms
                else:
                    self._packets_lost += 1

        finally:
            self._is_probing = False

    def _execute_ping(self, host: str) -> PingResult:
        """Executes native OS ping command."""
        ts = time.time()
        if platform.system() == "Windows":
            cmd = ['ping', '-n', '1', '-w', str(self.timeout_ms), host]
        else:
            cmd = ['ping', '-c', '1', '-W', str(max(1, int(self.timeout_ms / 1000))), host]

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=max(1.5, (self.timeout_ms / 1000.0) + 0.5),
                startupinfo=startupinfo
            )
            stdout = proc.stdout

            # Match Windows time=<number>ms or time=<number> ms
            match = re.search(r'time[=<](\d+(?:\.\d+)?)ms', stdout, re.IGNORECASE)
            if match:
                lat = float(match.group(1))
                return PingResult(target=host, latency_ms=lat, timestamp=ts, success=True)

            # Match Windows "time<1ms"
            if 'time<1ms' in stdout.lower() or 'time<1 ms' in stdout.lower():
                return PingResult(target=host, latency_ms=0.5, timestamp=ts, success=True)

            # Linux/Unix "time=12.3 ms"
            match_unix = re.search(r'time=([\d\.]+)\s*ms', stdout, re.IGNORECASE)
            if match_unix:
                return PingResult(target=host, latency_ms=float(match_unix.group(1)), timestamp=ts, success=True)

            # Timed out or unreachable
            err = "Request timed out" if "timed out" in stdout.lower() else "Destination unreachable"
            return PingResult(target=host, latency_ms=None, timestamp=ts, success=False, error=err)

        except subprocess.TimeoutExpired:
            return PingResult(target=host, latency_ms=None, timestamp=ts, success=False, error="Probe timed out")
        except Exception as e:
            return PingResult(target=host, latency_ms=None, timestamp=ts, success=False, error=str(e))

    def _simulate_ping(self, host: str) -> PingResult:
        """Simulates latency with realistic jitter and occasional spike."""
        time.sleep(0.02)
        base = 4.0 if ("192.168" in host or "10." in host) else 15.0
        # 2% packet loss simulation
        if random.random() < 0.02:
            return PingResult(target=host, latency_ms=None, timestamp=time.time(), success=False, error="Simulated drop")

        # Jitter variance
        spike = random.uniform(5.0, 20.0) if random.random() < 0.05 else 0.0
        lat = round(max(0.5, base + random.uniform(-1.5, 2.5) + spike), 1)
        return PingResult(target=host, latency_ms=lat, timestamp=time.time(), success=True)

    def get_stats(self) -> dict:
        """Computes statistical summary across the current ping session."""
        with self._lock:
            valid_latencies = [r.latency_ms for r in self._history if r.success and r.latency_ms is not None]
            loss_pct = (self._packets_lost / self._packets_sent * 100.0) if self._packets_sent > 0 else 0.0

            if valid_latencies:
                min_lat = min(valid_latencies)
                max_lat = max(valid_latencies)
                avg_lat = sum(valid_latencies) / len(valid_latencies)
            else:
                min_lat = 0.0
                max_lat = 0.0
                avg_lat = 0.0

            current_lat = self._last_result.latency_ms if (self._last_result and self._last_result.success) else None

            return {
                "current_ms": current_lat,
                "min_ms": round(min_lat, 1),
                "max_ms": round(max_lat, 1),
                "avg_ms": round(avg_lat, 1),
                "jitter_ms": round(self._jitter, 1),
                "packets_sent": self._packets_sent,
                "packets_lost": self._packets_lost,
                "loss_percent": round(loss_pct, 1)
            }
