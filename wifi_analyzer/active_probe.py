"""
Lightweight active network speed prober.
Generates small HTTP burst traffic to test maximum real-time Wi-Fi throughput on demand.
"""

import threading
import time
from typing import Optional
import urllib.request


class ActiveSpeedProber:
    """
    Runs lightweight continuous burst download and upload probes in a background worker
    to benchmark actual available bandwidth while the analyzer is active.
    """

    DOWNLOAD_ENDPOINTS = [
        "https://speed.cloudflare.com/__down?bytes=2000000",
        "https://proof.ovh.net/files/1Mb.dat",
        "https://speedtest.tele2.net/1MB.zip",
    ]

    UPLOAD_ENDPOINTS = [
        "https://speed.cloudflare.com/__up",
    ]

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self._is_probing = False
        self._lock = threading.Lock()
        self._dummy_payload = b'X' * 262144  # 256 KB chunk for upload burst

    def set_enabled(self, enabled: bool):
        with self._lock:
            self.enabled = enabled

    def is_enabled(self) -> bool:
        with self._lock:
            return self.enabled

    def trigger_burst(self):
        """Triggers a 1-second download and upload probe if enabled and not currently busy."""
        with self._lock:
            if not self.enabled or self._is_probing:
                return
            self._is_probing = True

        thread = threading.Thread(target=self._run_burst_worker, daemon=True)
        thread.start()

    def _run_burst_worker(self):
        try:
            # 1. Download probe
            self._probe_download()
            # 2. Upload probe
            self._probe_upload()
        except Exception:
            pass
        finally:
            with self._lock:
                self._is_probing = False

    def _probe_download(self):
        for url in self.DOWNLOAD_ENDPOINTS:
            try:
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'RealTimeWiFiAnalyzer/1.0'}
                )
                with urllib.request.urlopen(req, timeout=1.2) as response:
                    # Stream read up to 2MB or until 0.5s elapsed
                    start = time.time()
                    while time.time() - start < 0.6:
                        chunk = response.read(65536)
                        if not chunk:
                            break
                return
            except Exception:
                continue

    def _probe_upload(self):
        for url in self.UPLOAD_ENDPOINTS:
            try:
                req = urllib.request.Request(
                    url,
                    data=self._dummy_payload,
                    headers={'User-Agent': 'RealTimeWiFiAnalyzer/1.0', 'Content-Type': 'application/octet-stream'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=1.2):
                    pass
                return
            except Exception:
                continue
